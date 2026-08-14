#!/usr/bin/env python3
"""Cross-binary caller scan — ARM BL *and* Thumb BL/BLX.

Fixes the connectivity blind spot documented in docs/research/Overlay-Map.md:
`functions.json` records zero cross-binary call edges, so it cannot answer "which
mode calls this function?". This decodes branch-with-link encodings directly out of
arm9.bin plus every extracted overlay.

Handling Thumb is not optional. This ROM calls ARM functions from Thumb code via
BLX, and an ARM-only scan produced a confident false "zero callers in ov06" for the
nature predicate earlier in this effort. Two separate wrong conclusions in this
project came from tools that silently only handled ARM.

Validated: the known pair 0x021540AA -> 0x02078CB8 decodes correctly, and the
Thumb site 0x02150DD8 reproduces the lr = 0x02150DDD captured by a live GDB
breakpoint (odd lr => Thumb caller).

    python3 scripts/decomp/find_callers.py 0x020783CC 0x02078CB8

Read-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ARM9 = Path("jus_files/arm9/arm9.bin")
ARM9_BASE = 0x02000000
OVERLAY_DIR = Path("jus_files/overlays")


def binaries() -> list[tuple[str, Path, int]]:
    out: list[tuple[str, Path, int]] = []
    if ARM9.exists():
        out.append(("arm9", ARM9, ARM9_BASE))
    man = OVERLAY_DIR / "overlays.json"
    if man.exists():
        for e in json.loads(man.read_text()):
            p = OVERLAY_DIR / f"ov{e['id']:02d}.bin"
            if p.exists() and p.stat().st_size > 1000:
                out.append((f"ov{e['id']}", p, e["ram_address"]))
    return out


def scan(buf: bytes, base: int, targets: set[int]) -> list[tuple[int, int, str]]:
    hits = []
    n = len(buf)

    # Thumb BL / BLX: halfword pair. First hw 11110 S imm10, second 11111 (BL) or
    # 11101 (BLX) imm11. offset = (S:imm10 << 12) | (imm11 << 1), sign-extended
    # from bit 22. BLX forces the target word-aligned.
    for o in range(0, n - 3, 2):
        hw1 = int.from_bytes(buf[o:o + 2], "little")
        if not (0xF000 <= hw1 <= 0xF7FF):
            continue
        hw2 = int.from_bytes(buf[o + 2:o + 4], "little")
        blx = 0xE800 <= hw2 <= 0xEFFF
        bl = 0xF800 <= hw2 <= 0xFFFF
        if not (bl or blx):
            continue
        off = ((hw1 & 0x7FF) << 12) | ((hw2 & 0x7FF) << 1)
        if off & 0x400000:
            off -= 0x800000
        t = base + o + 4 + off
        if blx:
            t &= ~3
        if t in targets:
            hits.append((base + o, t, "thumb-blx" if blx else "thumb-bl"))

    # ARM BL (0xEB) and BLX immediate (0xFA/0xFB).
    for o in range(0, n - 3, 4):
        w = int.from_bytes(buf[o:o + 4], "little")
        if (w >> 24) & 0xFF not in (0xEB, 0xFA, 0xFB):
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        t = base + o + 8 + imm * 4
        if t in targets:
            hits.append((base + o, t, "arm-bl"))

    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="+", help="target addresses, e.g. 0x020783CC")
    ap.add_argument("--quiet-empty", action="store_true",
                    help="don't print binaries with no hits")
    args = ap.parse_args()

    targets = {int(t, 16) for t in args.targets}
    bins = binaries()
    if not bins:
        print("no binaries found — run scripts/analysis/extract_overlays.py first",
              file=sys.stderr)
        return 1

    total = 0
    per_target: dict[int, int] = {t: 0 for t in targets}
    for name, p, base in bins:
        hits = scan(p.read_bytes(), base, targets)
        if not hits and args.quiet_empty:
            continue
        for a, t, kind in sorted(hits):
            print(f"  {name:<5} 0x{a:08X}  {kind:<9} -> 0x{t:08X}")
            per_target[t] += 1
            total += 1

    print(f"\n{total} call site(s) across {len(bins)} binaries")
    for t in sorted(per_target):
        print(f"  0x{t:08X}: {per_target[t]}")
    if any(v == 0 for v in per_target.values()):
        print("\nNote: a zero here means no *direct* BL/BLX. The function could still be "
              "reached through a pointer table; this tool does not find indirect calls.")

    # Overlays sharing a load address are mutually exclusive, so a "caller" in one
    # overlay cannot really be calling code that lives in a different overlay at the
    # same address -- it is calling its own code at that address. Flag those rows.
    shared = {}
    man = OVERLAY_DIR / "overlays.json"
    if man.exists():
        for e in json.loads(man.read_text()):
            shared.setdefault(e["ram_address"], []).append(f"ov{e['id']}")
    ambiguous = [addr for addr, names in shared.items() if len(names) > 1]
    if ambiguous:
        print("\nWARNING: overlays share load addresses "
              + ", ".join(f"0x{a:08X} ({len(shared[a])} overlays)" for a in sorted(ambiguous))
              + ".")
        print("  If a target address falls in a shared window, only callers from the SAME")
        print("  overlay are real. A caller reported in a different overlay at that address")
        print("  is resolving to its own code, not to the target you named.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
