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


def writes(x: int, r: int) -> bool:
    """Guard 2: conservatively, does this instruction write register r?"""
    if (x & 0x0F000000) == 0x0B000000:                     # bl clobbers a1-a4, ip, lr
        return r in (0, 1, 2, 3, 12, 14)
    if (x & 0x0FFFFFF0) == 0x012FFF30:                     # blx Rm, same
        return r in (0, 1, 2, 3, 12, 14)
    if (x & 0x0E000000) == 0x04000000 and (x >> 20) & 1:   # ldr/ldrb
        return ((x >> 12) & 0xF) == r
    if (x & 0x0E400090) == 0x00400090 and (x & 0x60) and (x >> 20) & 1:
        return ((x >> 12) & 0xF) == r                      # ldrh/ldrsb/ldrsh
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


def access(x: int, reg: int):
    """An `[reg,#imm]` load or store. Guard 4: r15 is never a struct base."""
    if reg == 15:
        return None
    if (x & 0x0E000000) == 0x04000000 and ((x >> 16) & 0xF) == reg:
        kind = ("ldr" if (x >> 20) & 1 else "str") + ("b" if (x >> 22) & 1 else "")
        return kind, x & 0xFFF
    if (x & 0x0E400090) == 0x00400090 and (x & 0x60) and ((x >> 16) & 0xF) == reg:
        sh = (x >> 5) & 3
        ld = (x >> 20) & 1
        kind = {1: "ldrh" if ld else "strh", 2: "ldrsb", 3: "ldrsh"}[sh]
        return kind, ((x & 0xF00) >> 4) | (x & 0xF)
    return None


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


def walk(words: list[int], base: int, anchor: int, reg: int, starts: list[int]):
    """Yield (addr, kind, offset) for accesses off `reg` around `anchor`."""
    i = bisect.bisect_right(starts, anchor) - 1
    lo = starts[i] if i >= 0 else base
    hi = starts[i + 1] if i + 1 < len(starts) else base + len(words) * 4

    hit = access(words[(anchor - base) // 4], reg)
    if hit and not is_vtable_load(words, base, anchor, reg):
        yield anchor, hit[0], hit[1]

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
    print(f"selftest: {len(found)} offsets found: {[hex(o) for o in sorted(found)]}")
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
    for off in sorted(fields):
        hits = fields[off]
        kinds = ",".join(sorted({k for _, k in hits}))
        flag = ""
        if args.size is not None and off >= args.size:
            flag = "   <<< CONTAMINATED (>= struct size)"
            bad.append(off)
        print(f"  +0x{off:03X}  x{len(hits):<7}  {kinds:<20}  0x{min(a for a, _ in hits):08X}{flag}")

    total = sum(len(v) for v in fields.values())
    print(f"\n  {total} accesses total")
    if bad:
        print(f"  WARNING: {len(bad)} offset(s) exceed the declared size — an anchor register is "
              f"being reassigned in a way this tool did not catch, or an anchor is wrong.")
    if total > 200:
        print("  WARNING: too many hits to read by hand. Add more specific anchors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
