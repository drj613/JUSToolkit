#!/usr/bin/env python3
"""Map a struct's fields from code, with every guard this campaign learned the hard way.

Six separate wakes were spent on wrong results from offset scans, each with a
different cause. The rules were written down each time and then not applied the
next time — iteration 49 recorded the reassignment-tracking guard and iteration 50
wrote a fresh scan without it. So the guards live here instead of in a note.

You give it an ANCHOR: an address plus a register that provably holds the struct
at that instruction (e.g. `ldr ip,[r5,#0x70]` proves r5 is a NoteTrack, because
+0x70 is a known NoteTrack field). It walks outward from the anchor and reports
`[reg,#imm]` accesses, applying:

  1. STOP AT FUNCTION BOUNDARIES. `bx lr`, `pop {..,pc}`, and unconditional
     branches end the walk. (iteration 44: a chain scan stepped over `bx lr` and
     invented a collision-array reader in ov11.)
  2. STOP AT REASSIGNMENT. Any write to the anchor register ends the walk in that
     direction — the register no longer holds the struct. (iterations 49 and 50:
     without this, four phantom fields appeared and two real ones were missed.)
  3. SKIP VTABLE LOADS. If the base was just loaded from `[Rm,#0]`, the offset is
     a vtable slot index, not a field. (iteration 48: ov6 makes 384 virtual calls
     across 33 slots, so this is common.)
  4. NEVER TREAT r15 AS A BASE. `ldr Rd,[pc,#imm]` is a literal-pool load.
     (iteration 47: 14 of 36 hits were these.)
  5. SIZE CHECK. With --size, any offset at or beyond the struct size is reported
     as CONTAMINATED rather than as a field. This is the cheap sanity check that
     caught iteration 50's error.
  6. COUNT THE HITS. Prints the total so you notice when a scan is too loose to
     read by hand.

`--selftest` reproduces the verified NoteTrack map and fails if any known-phantom
offset reappears. Run it after touching this file.

    python3 scripts/decomp/struct_fields.py --selftest
    python3 scripts/decomp/struct_fields.py ov6 --anchor 0x02156130:5 --size 0xA8
    python3 scripts/decomp/struct_fields.py ov6 --anchor 0x02156130:5 --anchor 0x02155E3C:5

Read-only.
"""

from __future__ import annotations

import argparse
import bisect
import json
import sys
from pathlib import Path

ARM9 = Path("jus_files/arm9/arm9.bin")
ARM9_BASE = 0x02000000
OVERLAY_DIR = Path("jus_files/overlays")

BX_LR = 0xE12FFF1E


def load(which: str) -> tuple[list[int], int]:
    if which == "arm9":
        buf = ARM9.read_bytes()
        base = ARM9_BASE
    else:
        n = int(which.replace("ov", ""))
        man = json.loads((OVERLAY_DIR / "overlays.json").read_text())
        ent = next(e for e in man if e["id"] == n)
        buf = (OVERLAY_DIR / f"ov{n:02d}.bin").read_bytes()
        base = ent["ram_address"]
    return [int.from_bytes(buf[o:o + 4], "little")
            for o in range(0, len(buf) - 3, 4)], base


def func_starts(words: list[int], base: int) -> list[int]:
    return [base + i * 4 for i, x in enumerate(words)
            if (x & 0x0FFF0000) == 0x092D0000 and (x & 0x4000)]


def ends_block(x: int) -> bool:
    """Guard 1: does this instruction end the straight-line region?

    Only *unconditional* control transfers end it. Conditional branches are
    ordinary in-block flow — treating them as boundaries makes the walk stop
    almost immediately and miss most of the struct.
    """
    uncond = (x >> 28) == 0xE
    if x == BX_LR:
        return True
    if (x & 0x0FFF0000) == 0x08BD0000 and (x & 0x8000):    # pop {..,pc}
        return True
    if (x & 0x0FFFFFF0) == 0x012FFF10:                     # bx Rm
        return True
    if uncond and (x & 0x0F000000) == 0x0A000000 and not ((x >> 24) & 1):
        return True                                        # b, not bl, not conditional
    return False


def writes_back(x: int) -> bool:
    """Does this transfer modify its own base register?

    Post-indexed (P = 0, bit 24) always writes back; pre-indexed does so when
    W = 1 (bit 21). Both forms were previously invisible to `writes()`, so
    guard 2 never fired on them and the walk carried on past a base that had
    already moved. `str r0,[r4],#4` was the worst case: a store, so the old
    load-only test skipped it entirely.
    """
    p_bit = (x >> 24) & 1
    w_bit = (x >> 21) & 1
    return p_bit == 0 or w_bit == 1


def writes(x: int, r: int) -> bool:
    """Guard 2: conservatively, does this instruction write register r?"""
    if (x & 0x0F000000) == 0x0B000000:                     # bl clobbers a1-a4, ip, lr
        return r in (0, 1, 2, 3, 12, 14)
    if (x & 0x0FFFFFF0) == 0x012FFF30:                     # blx Rm, same
        return r in (0, 1, 2, 3, 12, 14)
    if (x & 0x0E000000) == 0x04000000:                     # ldr/str/ldrb/strb
        if writes_back(x) and ((x >> 16) & 0xF) == r:
            return True                                    # base advances
        if (x >> 20) & 1:
            return ((x >> 12) & 0xF) == r
        return False
    if (x & 0x0E400090) == 0x00400090 and (x & 0x60):      # ldrh/strh/ldrsb/ldrsh
        if writes_back(x) and ((x >> 16) & 0xF) == r:
            return True                                    # base advances
        if (x >> 20) & 1:
            return ((x >> 12) & 0xF) == r
        return False
    if (x & 0x0E000000) == 0x08000000 and (x >> 20) & 1:   # ldm
        return bool((x >> r) & 1)
    if (x & 0x0FE000F0) in (0x00000090, 0x00200090):       # mul / mla
        return ((x >> 16) & 0xF) == r
    if (x & 0x0C000000) == 0x00000000:                     # data processing
        op = (x >> 21) & 0xF
        if op in (0x8, 0x9, 0xA, 0xB):                     # tst/teq/cmp/cmn write nothing
            return False
        return ((x >> 12) & 0xF) == r
    return False


def effective_offset(x: int, imm: int):
    """Guard 10: the offset the access actually uses, or None if unusable.

    Two encoding details the first version of this file ignored, both of which
    produce wrong field offsets rather than missing ones:

      * POST-INDEXED (P = 0). `ldrsh r2,[r6],#2` reads at offset **0** and then
        advances the base by 2. The immediate is a stride, not a field offset.
        Reporting it as `+2` invented `+0x9A` on the ColPrm record at iteration
        78, when the real second array element is written by the loop's next
        pass, not by that instruction.
      * DOWN (U = 0). `ldr r0,[r4,#-8]` subtracts. A negative offset from a
        struct base is not a field here, so it is dropped rather than reported
        as `+8`.
    """
    if not (x >> 23) & 1:                   # U = 0, offset subtracts
        return None
    if not (x >> 24) & 1:                   # P = 0, post-indexed
        return 0
    return imm


def access(x: int, reg: int):
    """An `[reg,#imm]` load or store. Guard 4: r15 is never a struct base."""
    if reg == 15:
        return None
    if (x & 0x0E000000) == 0x04000000 and ((x >> 16) & 0xF) == reg:
        kind = ("ldr" if (x >> 20) & 1 else "str") + ("b" if (x >> 22) & 1 else "")
        off = effective_offset(x, x & 0xFFF)
        return None if off is None else (kind, off)
    if (x & 0x0E400090) == 0x00400090 and (x & 0x60) and ((x >> 16) & 0xF) == reg:
        sh = (x >> 5) & 3
        ld = (x >> 20) & 1
        kind = {1: "ldrh" if ld else "strh", 2: "ldrsb", 3: "ldrsh"}[sh]
        off = effective_offset(x, ((x & 0xF00) >> 4) | (x & 0xF))
        return None if off is None else (kind, off)
    return None


def address_taken(x: int, reg: int):
    """Guard 8: `add Rd, reg, #imm` — a field whose ADDRESS is taken.

    Every list head and every embedded sub-region in this codebase is reached
    this way, never as `[reg,#imm]`: `add r0,r4,#8` then link(), or
    `add r0,r4,#0xa4` then memset(). A scan that only looks at load/store
    encodings therefore misses exactly the structural fields you most want —
    iteration 78 found 13 offsets on the ColPrm record and none of them were the
    node list at `+0x08` or the scratch region at `+0xA4`.

    Reported as kind `addr` so it is never confused with a read or a write.
    Requires an unconditional `add` with a rotate-encoded immediate and S clear.
    """
    if (x >> 28) & 0xF != 0xE:
        return None
    if (x & 0x0FF00000) != 0x02800000:      # add Rd, Rn, #imm, S clear
        return None
    if ((x >> 16) & 0xF) != reg:
        return None
    if ((x >> 12) & 0xF) == 15:             # add pc, ... is control flow
        return None
    v, r = x & 0xFF, (x >> 8) & 0xF
    imm = ((v >> (2 * r)) | (v << (32 - 2 * r))) & 0xFFFFFFFF if r else v
    if imm == 0:
        return None                         # `add Rd,reg,#0` is a move, not a field
    return "addr", imm


def split_base(words: list[int], base: int, addr: int, dest: int):
    """Guard 9: resolve `add rD, reg, #N` used as a base for `[rD, #M]`.

    `+0x100` is not a field. The code does `add r0,r4,#0x100` then
    `strh r2,[r0,#0x86]` to reach `+0x186` — ARM's 12-bit immediate covers it,
    so this is the compiler's choice, not a necessity, and it appears on this
    codebase's larger structs. Reporting `+0x100` as a field would be wrong.

    Looks ahead up to 6 instructions for an access off `dest`, stopping if
    `dest` is rewritten. Yields (kind, N + M) for each one found.
    """
    out = []
    for k in range(1, 7):
        j = (addr - base) // 4 + k
        if j >= len(words):
            break
        y = words[j]
        hit = access(y, dest)
        if hit:
            out.append(hit)
            continue
        if writes(y, dest) or ends_block(y):
            break
    return out


def is_vtable_load(words: list[int], base: int, addr: int, reg: int) -> bool:
    """Guard 5: is this `[reg,#imm]` a vtable slot rather than a struct field?

    A vtable call is `ldr Rv,[obj,#0]` then `ldr Rf,[Rv,#slot]` then `blx Rf`.
    The trap: `ldr Rd,[Rm,#0]` is byte-identical to dereferencing a
    pointer-to-pointer — which is exactly how every singleton global here is
    loaded (`ldr r0,[pc]=&g; ldr r0,[r0,#0]`). Suppressing on the preceding
    instruction alone therefore discards real fields: on the ColPrm manager it
    silently dropped 7 of 16 anchors' first access, including `+0x70`.

    The discriminator is what happens to the *loaded value*. A vtable slot's
    contents get called; a struct field's do not. So require both the preceding
    `[Rm,#0]` load AND a nearby `blx` on the value this access produces.
    """
    if addr - 4 < base:
        return False
    prev = words[(addr - 4 - base) // 4]
    if not ((prev & 0x0FFF0FFF) == 0x05900000 and ((prev >> 12) & 0xF) == reg):
        return False
    cur = words[(addr - base) // 4]
    if not ((cur & 0x0E000000) == 0x04000000 and (cur >> 20) & 1):
        return False                        # not a word load; cannot be a call target
    rd = (cur >> 12) & 0xF
    for k in range(1, 7):                   # is the loaded value called?
        j = (addr - base) // 4 + k
        if j >= len(words):
            break
        y = words[j]
        if (y & 0x0FFFFFF0) == 0x012FFF30 and (y & 0xF) == rd:
            return True
        if (y & 0x0FFFFFF0) == 0x012FFF10 and (y & 0xF) == rd:
            return True
    return False


def emit_taken(words: list[int], base: int, addr: int, word: int, hit):
    """An address-taken field, with split bases resolved to their real offset."""
    dest = (word >> 12) & 0xF
    parts = split_base(words, base, addr, dest)
    if parts:
        for kind, off in parts:
            yield addr, kind + "/split", hit[1] + off
        return
    yield addr, hit[0], hit[1]


def walk(words: list[int], base: int, anchor: int, reg: int, starts: list[int]):
    """Yield (addr, kind, offset) for accesses off `reg` around `anchor`."""
    i = bisect.bisect_right(starts, anchor) - 1
    lo = starts[i] if i >= 0 else base
    hi = starts[i + 1] if i + 1 < len(starts) else base + len(words) * 4

    w0 = words[(anchor - base) // 4]
    hit = access(w0, reg)
    if hit and not is_vtable_load(words, base, anchor, reg):
        yield anchor, hit[0], hit[1]
    hit = address_taken(w0, reg)
    if hit:
        yield from emit_taken(words, base, anchor, w0, hit)

    for step in (4, -4):
        a = anchor
        while True:
            a += step
            if not (lo <= a < hi):
                break
            x = words[(a - base) // 4]
            if writes(x, reg):                 # guard 2
                break
            if ends_block(x):                  # guard 1
                break
            hit = access(x, reg)
            if hit and not is_vtable_load(words, base, a, reg):   # guards 3, 4
                yield a, hit[0], hit[1]
            hit = address_taken(x, reg)                           # guard 8
            if hit:
                yield from emit_taken(words, base, a, x, hit)      # guard 9


# Verified NoteTrack facts, from iterations 49 and 50. The selftest asserts the
# tool reproduces the real fields and reports none of the known phantoms.
NT_ANCHORS = [(0x021554EC, 4), (0x02155E3C, 5), (0x02155E9C, 5), (0x02155F10, 5),
              (0x02155F4C, 5), (0x02155FC0, 5), (0x02155FFC, 5), (0x0215605C, 5),
              (0x02156130, 5), (0x02156420, 0), (0x021564BC, 0), (0x02156538, 0)]
NT_REAL = {0x70, 0x74, 0x7C, 0x88, 0x90, 0x98}
NT_PHANTOM = {0x10, 0x28, 0x40, 0x5C, 0xDF, 0xE0, 0x158}
NT_SIZE = 0xA8


def selftest() -> int:
    words, base = load("ov6")
    starts = func_starts(words, base)
    found = set()
    for anchor, reg in NT_ANCHORS:
        for _, _, off in walk(words, base, anchor, reg, starts):
            found.add(off)
    ok = True
    missing = NT_REAL - found
    if missing:
        ok = False
        print(f"FAIL: real NoteTrack fields not found: {[hex(o) for o in sorted(missing)]}")
    phantom = NT_PHANTOM & found
    if phantom:
        ok = False
        print(f"FAIL: known-phantom offsets reported: {[hex(o) for o in sorted(phantom)]}")
    over = {o for o in found if o >= NT_SIZE}
    if over:
        ok = False
        print(f"FAIL: offsets beyond the 0xA8 struct: {[hex(o) for o in sorted(over)]}")
    # guard 10 anchors: the ColPrm record's three int16[2] arrays at
    # +0x90/+0x94/+0x98 (iteration 79). `ldrsh r2,[r6],#2` at 0x0207CB0C is
    # post-indexed: it reads +0x98, not +0x9A. +0x9A must NOT be reported.
    aw0, ab0 = load("arm9")
    a0 = func_starts(aw0, ab0)
    # r6 holds record+0x98, so offsets here are relative to the array base:
    # `strh r3,[r6]` and `ldrsh r2,[r6],#2` both touch element 0. A stride of 2
    # reported as an offset would show up as {0, 2}.
    arr = {off for _, _k, off in walk(aw0, ab0, 0x0207CB08, 6, a0)}
    if 2 in arr:
        ok = False
        print("FAIL: post-indexed stride reported as a field offset (+2)")
    if arr != {0}:
        ok = False
        print(f"FAIL: expected only element 0 off the array base, got "
              f"{[hex(o) for o in sorted(arr)]}")
    # the whole-record scan must no longer invent +0x9A
    rec = {off for a, r in ((0x0207CCDC, 4), (0x0207CA20, 4))
           for _, _k, off in walk(aw0, ab0, a, r, a0)}
    if 0x9A in rec:
        ok = False
        print("FAIL: +0x9A still reported on the ColPrm record")
    # guard 8 anchors: the ColPrm record's node list and scratch region are
    # reached only by `add`, so a load/store-only scan cannot see them.
    aw, ab = load("arm9")
    astarts = func_starts(aw, ab)
    taken = {off for a, r in ((0x0207CA20, 4), (0x0207D498, 4))
             for _, k, off in walk(aw, ab, a, r, astarts) if k == "addr"}
    for want in (0x08, 0xA4):
        if want not in taken:
            ok = False
            print(f"FAIL: address-taken field +{want:#x} not found on the ColPrm record")
    print(f"selftest: {len(found)} offsets found: {[hex(o) for o in sorted(found)]}")
    print(f"selftest: address-taken fields on the ColPrm record: "
          f"{[hex(o) for o in sorted(taken)]}")
    print("selftest PASSED" if ok else "selftest FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary", nargs="?", help="arm9 or ovN")
    ap.add_argument("--anchor", action="append", default=[],
                    help="ADDR:REG — an address where REG provably holds the struct")
    ap.add_argument("--size", type=lambda s: int(s, 0),
                    help="struct size; offsets >= this are flagged CONTAMINATED")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.binary or not args.anchor:
        ap.error("need a binary and at least one --anchor ADDR:REG")

    words, base = load(args.binary)
    starts = func_starts(words, base)
    fields: dict[int, list] = {}
    for spec in args.anchor:
        astr, rstr = spec.split(":")
        for addr, kind, off in walk(words, base, int(astr, 0), int(rstr), starts):
            fields.setdefault(off, []).append((addr, kind))

    print(f"{len(fields)} distinct offsets from {len(args.anchor)} anchor(s)\n")
    print("  off     accesses  kinds                 first site")
    bad = []
    misaligned = []
    for off in sorted(fields):
        hits = fields[off]
        kinds = ",".join(sorted({k for _, k in hits}))
        flag = ""
        if args.size is not None and off >= args.size:
            flag = "   <<< CONTAMINATED (>= struct size)"
            bad.append(off)
        # Guard 7: alignment. A word access at an offset not divisible by 4, or a
        # halfword access at an odd offset, cannot be a real struct field — no
        # compiler emits one. It means the walk strayed onto a different object.
        # (iteration 58: an unguarded walk reported `ldr [rX,#1]` and `ldr [rX,#2]`,
        # which is what exposed the contamination.)
        for _, k in hits:
            if k in ("ldr", "str") and off % 4:
                flag += "   <<< MISALIGNED (word access at a non-4-aligned offset)"
                misaligned.append(off)
                break
            if k in ("ldrh", "strh", "ldrsh") and off % 2:
                flag += "   <<< MISALIGNED (halfword access at an odd offset)"
                misaligned.append(off)
                break
        print(f"  +0x{off:03X}  x{len(hits):<7}  {kinds:<20}  0x{min(a for a, _ in hits):08X}{flag}")

    total = sum(len(v) for v in fields.values())
    print(f"\n  {total} accesses total")
    if bad:
        print(f"  WARNING: {len(bad)} offset(s) exceed the declared size — an anchor register is "
              f"being reassigned in a way this tool did not catch, or an anchor is wrong.")
    if misaligned:
        print(f"  WARNING: {len(misaligned)} misaligned access(es). Real struct fields are aligned, "
              f"so the walk has strayed onto a different object. Treat the whole map as suspect.")
    if total > 200:
        print("  WARNING: too many hits to read by hand. Add more specific anchors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
