#!/usr/bin/env python3
"""Resolve register-offset loads/stores by intra-block constant propagation.

Why this exists: `str rD,[rN,rM]` carries no offset in the instruction, so every
offset-based search is blind to it. In ov6 alone there are ~100 such stores, and
the writer of the pending-damage field `+0x134` is almost certainly one of them —
four separate offset searches came up empty (see
docs/research/findings/c6g-damage-writer-unreachable.md).

Tier-2 task D0.3 proposes headless Ghidra for this. Ghidra would do it properly,
but the specific capability needed is small: track which registers hold known
constants within a basic block, then read the offset off the register.

Scope, stated honestly:
  - Constants only, and only within a basic block (any branch, or being a branch
    target, clears the state). No cross-block or loop analysis.
  - Tracks mov #imm, mvn #imm, add/sub of a known reg and an immediate, lsl/lsr of
    a known reg, and PC-relative literal loads (which are always knowable).
  - Anything else makes the destination register unknown, conservatively.

So a hit is real, but silence is not proof of absence — the offset may be computed
across blocks or loaded from memory. That is the same limitation the whole static
approach has; this tool just moves the boundary.

KNOWN BUG — do not trust this tool's silence. On ov6 it reports **0** resolvable
offsets, while a cruder backward-scan (look 8 instructions back for `mov rm,#imm`)
finds 14. The state-clearing here is too aggressive, so it under-reports badly.
Measured on 2026-08-14 and left unfixed rather than shipped as if correct.

For the record, the cruder scan's 14 hits resolve to offset 0 (13x) and 0x10 (1x) —
none at 0x134/0x138 — and the 0-valued ones look like a stale producer being picked
up, so that scan is not trustworthy either. Both approaches fail on the question
they were built for.

    python3 scripts/decomp/resolve_reg_offsets.py ov6 --offset 0x134 0x138
    python3 scripts/decomp/resolve_reg_offsets.py ov6 --histogram

Read-only.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ARM9 = Path("jus_files/arm9/arm9.bin")
ARM9_BASE = 0x02000000
OVERLAY_DIR = Path("jus_files/overlays")


def load(which: str) -> tuple[bytes, int]:
    if which == "arm9":
        return ARM9.read_bytes(), ARM9_BASE
    n = int(which.replace("ov", ""))
    man = json.loads((OVERLAY_DIR / "overlays.json").read_text())
    for e in man:
        if e["id"] == n:
            return (OVERLAY_DIR / f"ov{n:02d}.bin").read_bytes(), e["ram_address"]
    raise SystemExit(f"unknown binary {which!r}")


def rot_imm(x: int) -> int:
    imm = x & 0xFF
    r = ((x >> 8) & 0xF) * 2
    return ((imm >> r) | (imm << (32 - r))) & 0xFFFFFFFF if r else imm


def branch_targets(words: list[int], base: int) -> set[int]:
    """Indices that are branch targets, so we can clear state there."""
    t = set()
    for i, x in enumerate(words):
        if (x & 0x0E000000) == 0x0A000000:
            imm = x & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            tgt = base + i * 4 + 8 + imm * 4
            idx = (tgt - base) // 4
            if 0 <= idx < len(words):
                t.add(idx)
    return t


def analyse(words: list[int], base: int):
    """Yield (addr, kind, rd, rn, rm, resolved_offset)."""
    targets = branch_targets(words, base)
    known: dict[int, int] = {}
    for i, x in enumerate(words):
        if i in targets:
            known.clear()

        cond = (x >> 28) & 0xF
        # register-offset word load/store: cond 011 P U B W L Rn Rd shift Rm
        if (x & 0x0E000010) == 0x06000000:
            rn, rd, rm = (x >> 16) & 0xF, (x >> 12) & 0xF, x & 0xF
            shift = (x >> 7) & 0x1F
            load_bit = (x >> 20) & 1
            if rm in known:
                off = known[rm] << shift
                yield (base + i * 4, "ldr" if load_bit else "str", rd, rn, rm, off)
            if not load_bit:
                pass
            else:
                known.pop(rd, None)
            continue

        # halfword register-offset
        if (x & 0x0E400090) == 0x00000090 and not ((x >> 22) & 1) and (x & 0x60):
            rn, rd, rm = (x >> 16) & 0xF, (x >> 12) & 0xF, x & 0xF
            load_bit = (x >> 20) & 1
            if rm in known:
                yield (base + i * 4, "ldrh" if load_bit else "strh", rd, rn, rm, known[rm])
            if load_bit:
                known.pop(rd, None)
            continue

        if cond != 0xE:            # conditional: don't trust the state afterwards
            rd = (x >> 12) & 0xF
            known.pop(rd, None)
            continue

        # constant producers
        if (x & 0x0FEF0000) == 0x03A00000:                    # mov rd,#imm
            known[(x >> 12) & 0xF] = rot_imm(x)
        elif (x & 0x0FEF0000) == 0x03E00000:                  # mvn rd,#imm
            known[(x >> 12) & 0xF] = (~rot_imm(x)) & 0xFFFFFFFF
        elif (x & 0x0FE00000) == 0x02800000:                  # add rd,rn,#imm
            rn = (x >> 16) & 0xF
            rd = (x >> 12) & 0xF
            if rn in known:
                known[rd] = (known[rn] + rot_imm(x)) & 0xFFFFFFFF
            else:
                known.pop(rd, None)
        elif (x & 0x0FE00000) == 0x02400000:                  # sub rd,rn,#imm
            rn, rd = (x >> 16) & 0xF, (x >> 12) & 0xF
            if rn in known:
                known[rd] = (known[rn] - rot_imm(x)) & 0xFFFFFFFF
            else:
                known.pop(rd, None)
        elif (x & 0x0FEF0070) == 0x01A00000:                  # mov/lsl rd,rm,#sh
            rd, rm, sh = (x >> 12) & 0xF, x & 0xF, (x >> 7) & 0x1F
            if rm in known:
                known[rd] = (known[rm] << sh) & 0xFFFFFFFF
            else:
                known.pop(rd, None)
        elif (x & 0x0FEF0070) == 0x01A00020:                  # lsr rd,rm,#sh
            rd, rm, sh = (x >> 12) & 0xF, x & 0xF, (x >> 7) & 0x1F
            if rm in known and sh:
                known[rd] = known[rm] >> sh
            else:
                known.pop(rd, None)
        elif (x & 0x0E5F0000) == 0x041F0000:                  # ldr rd,[pc,#imm]
            rd = (x >> 12) & 0xF
            pool = ((base + i * 4 + 8) & ~3) + (x & 0xFFF)
            idx = (pool - base) // 4
            if 0 <= idx < len(words):
                known[rd] = words[idx]
            else:
                known.pop(rd, None)
        elif (x & 0x0E000000) == 0x0A000000:                  # branch: end of block
            known.clear()
        else:
            rd = (x >> 12) & 0xF
            known.pop(rd, None)
            if (x & 0x0FFF0000) == 0x092D0000 or (x & 0x0FFF0000) == 0x08BD0000:
                known.clear()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("binary")
    ap.add_argument("--offset", nargs="*", default=[],
                    help="report only these resolved offsets, e.g. 0x134")
    ap.add_argument("--histogram", action="store_true",
                    help="show the distribution of resolved offsets")
    ap.add_argument("--stores-only", action="store_true")
    args = ap.parse_args()

    b, base = load(args.binary)
    words = [int.from_bytes(b[o:o + 4], "little") for o in range(0, len(b) - 3, 4)]
    wanted = {int(o, 16) for o in args.offset}

    rows = list(analyse(words, base))
    if args.stores_only:
        rows = [r for r in rows if r[1].startswith("str")]

    print(f"{args.binary}: {len(rows)} register-offset access(es) with a resolvable offset")
    if args.histogram:
        h = collections.Counter(r[5] for r in rows)
        print("\n  resolved offsets, most common first:")
        for off, n in h.most_common(24):
            print(f"    +0x{off:<6X} {n}")
    if wanted:
        hit = [r for r in rows if r[5] in wanted]
        print(f"\n  matching {', '.join(hex(w) for w in sorted(wanted))}: {len(hit)}")
        for a, kind, rd, rn, rm, off in hit:
            print(f"    0x{a:08X}  {kind:<5} r{rd},[r{rn},r{rm}]   resolved +0x{off:X}")
        if not hit:
            print("    none — offset may be computed across blocks or loaded from memory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
