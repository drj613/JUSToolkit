#!/usr/bin/env python3
"""Find ARM jump-table dispatches, and signed-byte loads at a given struct offset.

Why: `findings/projectileid-is-a-selector-not-an-index.md` established that negative
`ProjectileId` (collision offset `0x03`, sbyte) is a per-character selector with 17
distinct values, and that no data table of 17 entries exists anywhere in
`ChrBin.aar`. The remaining hypothesis is that a `switch` in engine code dispatches
on it. This looks for that switch two ways:

  --tables   ARM jump-table idioms, with the case count recovered from the guarding
             `cmp Rm,#N`, so a ~17-case table is identifiable by arity alone.
  --ldrsb N  ARM LDRSB with immediate offset N — the instruction that would read a
             signed byte out of a collision record.

Both are deliberately narrow so that every hit can be read by hand. Four separate
offset-only scans in this campaign returned hundreds of unreadable hits; the lesson
recorded there was to constrain enough to read all of them.

KNOWN LIMIT, stated up front: **Thumb has no LDRSB immediate form** — only
`ldrsb Rd,[Rb,Ro]` with a register offset. A Thumb consumer of this field is
therefore invisible to `--ldrsb`, and silence from that scan is not evidence of
absence. Thumb switch dispatches are also not covered by `--tables`. Two wrong
conclusions earlier in this project came from tools that silently handled only ARM,
so this one says so out loud.

    python3 scripts/decomp/find_jump_tables.py --tables --min-cases 10 --max-cases 24
    python3 scripts/decomp/find_jump_tables.py --ldrsb 3

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

COND = ["eq", "ne", "cs", "cc", "mi", "pl", "vs", "vc",
        "hi", "ls", "ge", "lt", "gt", "le", "", "nv"]


def binaries(which: str | None) -> list[tuple[str, bytes, int]]:
    out = []
    if which in (None, "arm9") and ARM9.exists():
        out.append(("arm9", ARM9.read_bytes(), ARM9_BASE))
    man = OVERLAY_DIR / "overlays.json"
    if man.exists():
        for e in json.loads(man.read_text()):
            name = f"ov{e['id']}"
            if which not in (None, name):
                continue
            p = OVERLAY_DIR / f"ov{e['id']:02d}.bin"
            if p.exists() and p.stat().st_size > 1000:
                out.append((name, p.read_bytes(), e["ram_address"]))
    return out


def rot_imm(x: int) -> int:
    imm = x & 0xFF
    r = ((x >> 8) & 0xF) * 2
    return ((imm >> r) | (imm << (32 - r))) & 0xFFFFFFFF if r else imm


def words(buf: bytes) -> list[int]:
    return [int.from_bytes(buf[o:o + 4], "little") for o in range(0, len(buf) - 3, 4)]


def find_tables(ws: list[int], base: int) -> list[dict]:
    """ARM jump-table dispatch idioms, with case count from the guarding cmp."""
    hits = []
    for i, x in enumerate(ws):
        kind = None
        # add pc, pc, Rm, lsl #2   -> cond 000 0100 0 1111 1111 00010 00 Rm
        if (x & 0x0FFFFFF0) == 0x008FF100:
            kind = "add pc,pc,Rm,lsl#2"
        # ldr pc, [pc, Rm, lsl #2] -> cond 011 1100 1 1111 1111 00010 00 Rm
        elif (x & 0x0FFFFFF0) == 0x079FF100:
            kind = "ldr pc,[pc,Rm,lsl#2]"
        if kind is None:
            continue
        rm = x & 0xF
        cond = (x >> 28) & 0xF

        # walk back up to 6 instructions for `cmp Rm, #imm` on the same register
        cases = None
        cmp_at = None
        for j in range(i - 1, max(-1, i - 7), -1):
            y = ws[j]
            if (y & 0x0FF0F000) == 0x03500000 and ((y >> 16) & 0xF) == rm:
                cases = rot_imm(y)
                cmp_at = base + j * 4
                break
        hits.append(dict(addr=base + i * 4, kind=kind, rm=rm,
                         cond=COND[cond], cases=cases, cmp_at=cmp_at))
    return hits


def find_ldrsb(ws: list[int], base: int, off: int) -> list[dict]:
    """ARM LDRSB Rd,[Rn,#off] — immediate, pre-indexed, signed byte."""
    hits = []
    if not (0 <= off <= 0xFF):
        raise SystemExit("offset must fit in 8 bits (imm4H:imm4L)")
    want = ((off >> 4) << 8) | (off & 0xF)
    for i, x in enumerate(ws):
        # cond 000 P U 1 W 1 Rn Rd imm4H 1101 imm4L
        if (x & 0x0E1000F0) != 0x001000D0:
            continue                      # not a load with SH=10 (signed byte)
        if not (x >> 22) & 1:
            continue                      # register-offset form, no immediate
        if ((x & 0xF00) | (x & 0xF)) != want:
            continue
        up = (x >> 23) & 1
        hits.append(dict(addr=base + i * 4, rn=(x >> 16) & 0xF,
                         rd=(x >> 12) & 0xF, up=up,
                         cond=COND[(x >> 28) & 0xF]))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--binary", help="arm9 or ovN; default all")
    ap.add_argument("--tables", action="store_true")
    ap.add_argument("--ldrsb", type=lambda s: int(s, 0))
    ap.add_argument("--min-cases", type=int, default=0)
    ap.add_argument("--max-cases", type=int, default=10**9)
    args = ap.parse_args()
    if not args.tables and args.ldrsb is None:
        ap.error("pick --tables and/or --ldrsb N")

    bins = binaries(args.binary)
    if not bins:
        print("no binaries; run scripts/analysis/extract_overlays.py first", file=sys.stderr)
        return 1

    if args.tables:
        print("ARM jump-table dispatches (case count = guarding `cmp Rm,#N`, so N+1 cases)")
        total = shown = nocmp = 0
        filtering = bool(args.min_cases) or args.max_cases < 10**9
        for name, buf, base in bins:
            for h in find_tables(words(buf), base):
                total += 1
                n = h["cases"]
                if n is None:
                    # No guarding `cmp` -- the index is computed arithmetically.
                    # These used to be dropped silently, which hid two real
                    # unconditional dispatches at 0x0200D198 and 0x0200D38C
                    # (iteration 82). Report them unless a case filter is asked
                    # for, since an unknown count cannot satisfy a range.
                    nocmp += 1
                    if filtering:
                        continue
                    shown += 1
                    print(f"  {name:<5} 0x{h['addr']:08X}  {h['kind']:<22} r{h['rm']} "
                          f"cond={h['cond'] or 'al':<3} NO GUARDING CMP -> case count "
                          f"unknown (index computed)")
                    continue
                if not (args.min_cases <= n + 1 <= args.max_cases):
                    continue
                shown += 1
                print(f"  {name:<5} 0x{h['addr']:08X}  {h['kind']:<22} r{h['rm']} "
                      f"cond={h['cond'] or 'al':<3} cmp #{n} -> {n + 1} cases "
                      f"(cmp at 0x{h['cmp_at']:08X})")
        print(f"\n  {shown} shown / {total} total dispatch sites "
              f"({nocmp} with no guarding cmp)")
        if filtering:
            print(f"  (filtered to {args.min_cases}..{args.max_cases} cases; "
                  f"the {nocmp} sites with no recoverable cmp are hidden)")
        print("  NOTE: Thumb dispatches are NOT covered. Silence is not absence.")

    if args.ldrsb is not None:
        print(f"\nARM LDRSB Rd,[Rn,#{args.ldrsb}] (signed byte, immediate offset)")
        total = 0
        for name, buf, base in bins:
            for h in find_ldrsb(words(buf), base, args.ldrsb):
                total += 1
                sign = "+" if h["up"] else "-"
                print(f"  {name:<5} 0x{h['addr']:08X}  ldrsb{h['cond']} r{h['rd']},"
                      f"[r{h['rn']},#{sign}{args.ldrsb}]")
        print(f"\n  {total} site(s)")
        print("  NOTE: Thumb has no LDRSB immediate form — only register-offset.")
        print("  A Thumb reader of this field cannot appear here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
