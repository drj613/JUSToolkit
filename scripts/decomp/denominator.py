#!/usr/bin/env python3
"""Tier-2 task D0.2 — the function denominator for decomp progress.

Counts functions per binary and how much of each binary they account for.

One deviation from the plan, deliberately: the plan suggested bucketing functions
by ADDRESS RANGE. That cannot work here. Ten of the fourteen overlays load at
0x0214CD20, so an address in that window is ambiguous across ten binaries and
range-bucketing would multiply-count every overlay function.

`jus_files/analysis/functions.json` already carries a `provenance` field naming the
binary each function was disassembled from, so this attributes by provenance and
uses the address ranges only as a CONSISTENCY CHECK — any function whose address
falls outside its claimed binary's window is reported as a discrepancy.

Coverage % is the useful number: bytes claimed by identified functions divided by
the binary's size. It's the denominator a decomp effort measures progress against.

Read-only.
"""

from __future__ import annotations

import argparse
import collections
import json
import struct
import sys
from pathlib import Path

FUNCTIONS = Path("jus_files/analysis/functions.json")
OVERLAY_MANIFEST = Path("jus_files/overlays/overlays.json")
ARM9 = Path("jus_files/arm9/arm9.bin")
ARM9_BASE = 0x02000000
OUT = Path("docs/research/Overlay-Map.md")

# Mode labels from scripts/decomp/overlay_map.py (task D0.1).
MODES = {
    "arm9": "always-resident, mode-agnostic",
    "ov0": "boot / title / opening / ending / options",
    "ov1": "deck select list + results",
    "ov2": "J Galaxy story + demos",
    "ov3": "J Arena",
    "ov4": "J Quiz",
    "ov5": "deck make (editor) + koma browser",
    "ov6": "battle",
    "ov7": "local wireless",
    "ov8": "Nintendo WFC online",
    "ov10": "online, larger",
    "ov11": "battle AI",
    "ov12": "shared support (battle + deck)",
}


def load_extents() -> dict[str, tuple[int, int]]:
    """provenance -> (ram_base, size)."""
    ext: dict[str, tuple[int, int]] = {}
    if ARM9.exists():
        ext["arm9"] = (ARM9_BASE, ARM9.stat().st_size)
    if OVERLAY_MANIFEST.exists():
        for e in json.loads(OVERLAY_MANIFEST.read_text()):
            ext[f"ov{e['id']}"] = (e["ram_address"], e["ram_size"])
    return ext


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--functions", type=Path, default=FUNCTIONS)
    ap.add_argument("--write-doc", action="store_true",
                    help=f"append/replace the Denominator section in {OUT}")
    args = ap.parse_args()

    db = json.loads(args.functions.read_text())
    funcs = db["functions"]
    ext = load_extents()

    per = collections.defaultdict(lambda: {"n": 0, "bytes": 0, "thumb": 0,
                                           "no_callers": 0, "leaf": 0, "outside": 0})
    for f in funcs:
        p = f.get("provenance", "?")
        addr = int(f["addr"], 16)
        d = per[p]
        d["n"] += 1
        d["bytes"] += f.get("size", 0)
        if f.get("mode") == "thumb":
            d["thumb"] += 1
        if not f.get("callers"):
            d["no_callers"] += 1
        if not f.get("callees"):
            d["leaf"] += 1
        if p in ext:
            base, size = ext[p]
            if not (base <= addr < base + size):
                d["outside"] += 1

    total = len(funcs)
    print(f"total functions:        {total}")
    order = ["arm9"] + sorted((k for k in per if k != "arm9"),
                              key=lambda k: -per[k]["n"])
    rows = []
    for p in order:
        d = per[p]
        base, size = ext.get(p, (None, None))
        cov = (100.0 * d["bytes"] / size) if size else None
        rows.append((p, d, base, size, cov))
        covs = f"{cov:5.1f}%" if cov is not None else "   n/a"
        print(f"  {p:<6} {d['n']:>5} funcs  {d['bytes']:>7} bytes  cov {covs}"
              f"  thumb {d['thumb']:>3}  no-callers {d['no_callers']:>4}"
              + (f"  OUTSIDE {d['outside']}" if d["outside"] else ""))

    # Diagnostic: does the call graph cross binary boundaries at all?
    byaddr = collections.defaultdict(set)
    for f in funcs:
        byaddr[int(f["addr"], 16)].add(f.get("provenance", "?"))
    same = cross = 0
    for f in funcs:
        p = f.get("provenance", "?")
        for c in f.get("callers", []):
            ps = byaddr.get(int(c, 16))
            if ps is None:
                continue
            if p in ps:
                same += 1
            else:
                cross += 1
    print(f"\ncaller edges: same-binary {same}, cross-binary {cross}")
    if cross == 0:
        print("  WARNING: the call graph is INTRA-BINARY ONLY. Cross-binary calls are not")
        print("  recorded, so caller/callee data cannot establish which mode uses an arm9")
        print("  function. Ground truth: 0x020783CC has 8 callers in ov6 (verified by decoding")
        print("  BL across all binaries) and functions.json records none of them.")

    missing = [k for k in ext if k not in per]
    if missing:
        print(f"  binaries with zero attributed functions: {', '.join(sorted(missing))}")

    if args.write_doc:
        lines = []
        lines.append("## Denominator (task D0.2)")
        lines.append("")
        lines.append(f"Generated by `scripts/decomp/denominator.py`. **{total} functions** "
                     "identified across arm9 and 13 overlays.")
        lines.append("")
        lines.append("Attributed by the `provenance` field in "
                     "`jus_files/analysis/functions.json`, **not** by address range — ten "
                     "overlays share load address `0x0214CD20`, so range-bucketing would "
                     "multiply-count every overlay function. Address ranges are used only as a "
                     "consistency check.")
        lines.append("")
        lines.append("`coverage` = bytes claimed by identified functions / binary size. That is "
                     "the progress denominator: it says how much of each binary is accounted for "
                     "at all, before any of it is understood.")
        lines.append("")
        lines.append("| binary | mode | functions | bytes | coverage | thumb | no callers |")
        lines.append("|---|---|---|---|---|---|---|")
        for p, d, base, size, cov in rows:
            covs = f"{cov:.1f}%" if cov is not None else "n/a"
            lines.append(f"| `{p}` | {MODES.get(p,'?')} | {d['n']:,} | {d['bytes']:,} | "
                         f"{covs} | {d['thumb']} | {d['no_callers']} |")
        lines.append(f"| **total** | | **{total:,}** | | | | |")
        lines.append("")
        if missing:
            lines.append(f"Binaries with zero attributed functions: "
                         f"{', '.join('`'+m+'`' for m in sorted(missing))} — the 32-byte stubs "
                         "were never disassembled.")
            lines.append("")
        disc = {p: d["outside"] for p, d in per.items() if d["outside"]}
        lines.append(f"Consistency check: "
                     + ("no function falls outside its claimed binary's address window."
                        if not disc else f"**discrepancies** {disc}"))
        lines.append("")
        lines.append("### Limitation: the call graph is intra-binary only")
        lines.append("")
        lines.append(f"Of {same + cross:,} caller edges in `functions.json`, **{cross} cross a "
                     "binary boundary**. The disassembler built each binary's call graph in "
                     "isolation, so caller/callee data **cannot** tell you which mode uses an "
                     "`arm9` function.")
        lines.append("")
        lines.append("Ground truth for the gap: `0x020783CC` (the HP-delta apply entry) has "
                     "**8 callers, all in ov6**, found by decoding `BL` encodings across every "
                     "binary. `functions.json` records none of them — and does not list that "
                     "address as a function at all.")
        lines.append("")
        lines.append("Consequences worth planning around:")
        lines.append("")
        lines.append("1. The **battle-specific surface is at least 1,622 functions** "
                     "(ov6 + ov11 + ov12, ~19% of all identified functions). How much of arm9's "
                     "4,043 belongs to battle is *unknown* from this data.")
        lines.append("2. Any \"which mode calls this?\" question needs a cross-binary call graph. "
                     "Decode `BL` directly out of the binaries; do not grep the text disassembly, "
                     "which only covers the files someone happened to dump.")
        lines.append("3. This is the same blind spot that produced a wrong conclusion earlier in "
                     "this effort — \"the function is in `arm9.bin`, so it runs in this mode\" — "
                     "see `findings/nature-SOLVED.md`. Being in arm9 means mode-agnostic, not "
                     "mode-relevant.")
        lines.append("")
        lines.append("Reading the numbers: `no callers` counts functions nothing calls, which is "
                     "a mix of genuine entry points, indirectly-called handlers, and dead code. "
                     "It is an upper bound on entry points, not a count of them.")
        lines.append("")

        text = OUT.read_text() if OUT.exists() else ""
        marker = "## Denominator (task D0.2)"
        if marker in text:
            head, _, rest = text.partition(marker)
            # drop the old section up to the next H2
            after = rest.split("\n## ", 1)
            tail = ("\n## " + after[1]) if len(after) > 1 else ""
            text = head + "\n".join(lines) + tail
        else:
            text = text.rstrip() + "\n\n" + "\n".join(lines)
        OUT.write_text(text)
        print(f"\nwrote Denominator section to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
