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


# ---------------------------------------------------------------------------
# Shared ARM encoding decoders.
#
# Four separate wakes lost time to a hand-written mask whose compare value
# disagreed with it about which bits matter -- the `bl` mask (iteration 46), the
# `ldr` Rd/Rn mask (47), the `mov` immediate mask (89) and the pc-relative load
# mask (111). Every one produced a clean zero instead of an error, so nothing
# looked wrong until a count came back implausible.
#
# These are the tested versions. Use them instead of writing a mask inline; the
# selftest hand-verifies each against a real instruction from this ROM.
# ---------------------------------------------------------------------------

def is_bl(x: int):
    """`bl #target` -> the absolute target, else None. Excludes `b`."""
    if (x >> 28) & 0xF == 0xF:
        return None                       # blx (immediate) has cond == 0xF
    if (x & 0x0F000000) != 0x0B000000:
        return None
    off = x & 0xFFFFFF
    if off & 0x800000:
        off -= 0x1000000
    return off * 4 + 8                    # caller adds the site address


def is_ldr_pc(x: int):
    """`ldr rD,[pc,#±imm]` -> (rD, signed displacement), else None.

    The mask must keep bit 23 (U) OUT of the comparison or fix it explicitly;
    masking it away while the compare value sets it can never match.
    """
    if (x & 0x0E5F0000) != 0x041F0000:
        return None
    imm = x & 0xFFF
    return (x >> 12) & 0xF, (imm if (x >> 23) & 1 else -imm)


def is_mov_imm(x: int):
    """`mov rD,#imm` (unconditional, S clear) -> (rD, value), else None."""
    if (x >> 28) & 0xF != 0xE:
        return None
    if (x & 0x0FFF0000) != 0x03A00000:
        return None
    v, r = x & 0xFF, (x >> 8) & 0xF
    val = ((v >> (2 * r)) | (v << (32 - 2 * r))) & 0xFFFFFFFF if r else v
    return (x >> 12) & 0xF, val


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


def strided_group(words: list[int], base: int, addr: int, dest: int, first: int,
                  starts: list[int]):
    """Guard 11: `add rD, base, #N` then a loop doing `add rD, rD, #K`.

    Adjacent list heads are walked with one pointer, not addressed individually:

        add r6, sl, #0x10       ; first head
      loop:
        ...                     ; work on [r6]
        add r8, r8, #1
        cmp r8, #3              ; three heads
        add r6, r6, #8          ; stride
        blt loop

    An anchor-register walk sees only `+0x10`, because `+0x18` and `+0x20` are
    never expressed relative to the anchor. Iteration 83 found them by reading the
    loop; iteration 85 confirmed the tool could not. This recovers the whole group.

    Returns the extra offsets (excluding `first`), or [] when the shape is absent
    or the trip count cannot be recovered -- a stride with an unknown bound is not
    guessed at.
    """
    i = bisect.bisect_right(starts, addr) - 1
    hi = starts[i + 1] if i + 1 < len(starts) else base + len(words) * 4
    stride = trips = None
    j = (addr - base) // 4
    end = min(len(words), (hi - base) // 4)
    while j + 1 < end:
        j += 1
        x = words[j]
        # self-increment of the walking pointer: add rD, rD, #K
        if ((x >> 28) & 0xF) == 0xE and (x & 0x0FF00000) == 0x02800000 \
                and ((x >> 12) & 0xF) == dest and ((x >> 16) & 0xF) == dest:
            v, r = x & 0xFF, (x >> 8) & 0xF
            stride = ((v >> (2 * r)) | (v << (32 - 2 * r))) & 0xFFFFFFFF if r else v
            continue
        # trip count: cmp rC, #M on any register, before the backward branch
        if (x & 0x0FF0F000) == 0x03500000:
            v, r = x & 0xFF, (x >> 8) & 0xF
            trips = ((v >> (2 * r)) | (v << (32 - 2 * r))) & 0xFFFFFFFF if r else v
            continue
        # a BACKWARD branch closes the loop; forward branches are just control
        # flow inside it (the real loop here opens with `b` to its condition test)
        if (x & 0x0E000000) == 0x0A000000 and not (x >> 24) & 1:
            # Only a back-edge that has both a stride and a trip count is the
            # walk's own loop. An inner loop closes first here -- the detach
            # routine drains each list before advancing to the next head -- so
            # keep scanning rather than giving up at the first backward branch.
            if (x & 0xFFFFFF) & 0x800000 and stride and trips and 1 < trips <= 64:
                return [first + k * stride for k in range(1, trips)]
            continue
        if writes(x, dest):                 # pointer reassigned -- not a strided walk
            return []
    return []


def emit_taken(words: list[int], base: int, addr: int, word: int, hit,
               starts: list[int] | None = None):
    """An address-taken field, with split bases and strided head groups resolved."""
    dest = (word >> 12) & 0xF
    parts = split_base(words, base, addr, dest)
    if parts:
        for kind, off in parts:
            yield addr, kind + "/split", hit[1] + off
    else:
        yield addr, hit[0], hit[1]
    if starts is not None:                                    # guard 11
        for off in strided_group(words, base, addr, dest, hit[1], starts):
            yield addr, "addr/strided", off


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
        yield from emit_taken(words, base, anchor, w0, hit, starts)

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
                yield from emit_taken(words, base, a, x, hit, starts)  # guards 9, 11


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
    # Encoding decoders, each against a hand-read instruction from this ROM.
    aw2, ab2 = load("arm9")

    def word_at(addr):
        return aw2[(addr - ab2) // 4]

    # 0x02076CB4: ldr r0, [pc, #0x20]  -> the deck global's pool word
    got = is_ldr_pc(word_at(0x02076CB4))
    if got != (0, 0x20):
        ok = False
        print(f"FAIL: is_ldr_pc(0x02076CB4) = {got!r}, expected (0, 0x20)")
    # 0x02076CD0: movlo r0, #0xc  -- conditional, must be rejected
    if is_mov_imm(word_at(0x02076CD0)) is not None:
        ok = False
        print("FAIL: is_mov_imm accepted a conditional mov")
    # 0x02076CC0 is `ldr r0,[r0,#0x8ec]`, not pc-relative
    if is_ldr_pc(word_at(0x02076CC0)) is not None:
        ok = False
        print("FAIL: is_ldr_pc accepted a non-pc load")
    # 0x02076EB4: bl #0x2076c98
    rel = is_bl(word_at(0x02076EB4))
    if rel is None or 0x02076EB4 + rel != 0x02076C98:
        ok = False
        print(f"FAIL: is_bl(0x02076EB4) -> {None if rel is None else hex(0x02076EB4 + rel)}, "
              f"expected 0x02076c98")
    # 0x02076CA4 is `bxeq lr`, not a bl
    if is_bl(word_at(0x02076CA4)) is not None:
        ok = False
        print("FAIL: is_bl accepted a non-bl")

    # guard 11 anchor: the detach routine walks three adjacent list heads with one
    # pointer (add r6,sl,#0x10 / add r6,r6,#8 / cmp r8,#3), so +0x18 and +0x20 are
    # never expressed off the anchor register (iterations 83, 85).
    aw1, ab1 = load("arm9")
    a1 = func_starts(aw1, ab1)
    heads = {off for _, _k, off in walk(aw1, ab1, 0x0207CB60, 10, a1)}
    for want in (0x10, 0x18, 0x20):
        if want not in heads:
            ok = False
            print(f"FAIL: strided list head +{want:#x} not recovered "
                  f"(got {[hex(o) for o in sorted(heads)]})")
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
