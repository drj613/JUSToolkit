#!/usr/bin/env python3
"""What do we already know about X? Run this BEFORE investigating anything.

Why this exists, stated bluntly: over ~25 wakes this campaign hand-rolled
caller scans, literal-pool resolution, immediate-offset searches and word-reference
censuses — all of which `scripts/analysis/query.py` already provided, built by an
earlier phase of the same campaign. Five collision symbol names sat unread in
`jus_files/analysis/symbols.json` for 24 wakes while the same module structure was
re-derived by hand.

The loose-ends rule said "grep docs/ before opening a binary". That was too narrow.
It missed the generated artefacts, and it missed the query CLI entirely. This tool
searches everything at once so the gap cannot recur.

    python3 scripts/analysis/prior_art.py ColJoint
    python3 scripts/analysis/prior_art.py 0x0214BE0C
    python3 scripts/analysis/prior_art.py --inventory

Read-only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DOCS = Path("docs")
ANALYSIS = Path("jus_files/analysis")
STATE = Path("scripts/analysis/loop-state-atlas.json")
QUERY = Path("scripts/analysis/query.py")

# Everything a subsystem investigation should consult first.
ARTEFACTS = {
    "symbols.json": "assert-string symbol names -> function addresses (275 named functions)",
    "modules.json": "per-function (name, source .cpp) pairs; module boundaries",
    "functions.json": "function inventory with caller/callee edges per region",
    "xrefs.json": "prebuilt literal_loads (16648), imm_offsets (60259), branches (69034)",
    "arm9_tables.json": "detected pointer tables, index tables, struct arrays, string refs",
    "arm9_tables_ram.json": "the same, with RAM addresses",
    "arm9_regions.json": "region map (18 regions)",
    "cheat_addresses.json": "known cheat-code addresses by category",
}

QUERY_CMDS = [
    ("func ADDR", "the function containing ADDR: start, provenance, size, mode"),
    ("callers ADDR", "callers of the function at ADDR — includes functions.json edges a BL scan misses"),
    ("callees ADDR", "callees of the function at ADDR"),
    ("xrefs-to ADDR", "every literal_load / branch / caller reference to ADDR"),
    ("search-imm N", "load/store instructions with immediate offset N"),
    ("search-op-imm N", "data-processing instructions with #immediate N"),
    ("pool-values LO HI", "literal_load values inside [LO, HI] — finds globals you did not know about"),
    ("disasm ADDR N", "N verbatim disassembly lines from ADDR"),
    ("strings REGION", "printable ASCII / Shift-JIS strings in a region"),
]


def inventory() -> int:
    print("=== generated artefacts under jus_files/analysis/ ===")
    for name, desc in ARTEFACTS.items():
        p = ANALYSIS / name
        mark = "ok " if p.exists() else "MISSING"
        size = f"{p.stat().st_size:>9,}" if p.exists() else " " * 9
        print(f"  [{mark}] {name:<22} {size}  {desc}")
    print("\n=== query.py subcommands (READ-ONLY, prefer these over hand-rolled scans) ===")
    for cmd, desc in QUERY_CMDS:
        print(f"  query.py {cmd:<20} {desc}")
    print("\n=== scripts/decomp/ tools built by this phase ===")
    d = Path("scripts/decomp")
    if d.exists():
        for f in sorted(d.glob("*.py")):
            doc = ""
            for line in f.read_text().splitlines()[:4]:
                if line.startswith('"""'):
                    doc = line.strip('"').strip()
                    break
            print(f"  {f.name:<24} {doc[:70]}")
    print("\nNOTE: several scripts/decomp tools duplicate query.py subcommands. "
          "Check query.py first.")
    return 0


def search(term: str) -> int:
    is_addr = bool(re.fullmatch(r"0x[0-9A-Fa-f]+", term))
    print(f"=== prior art for {term!r} ===\n")

    print("--- docs/ ---")
    r = subprocess.run(["grep", "-rniE", term, str(DOCS)], capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.strip()][:12]
    print("\n".join("  " + l[:150] for l in lines) if lines else "  (nothing)")
    if len(r.stdout.splitlines()) > 12:
        print(f"  ... {len(r.stdout.splitlines()) - 12} more")

    for name in ("symbols.json", "modules.json"):
        p = ANALYSIS / name
        if not p.exists():
            continue
        print(f"\n--- {name} ---")
        d = json.loads(p.read_text())
        hits = []
        for binname, rows in d.items():
            for row in rows:
                blob = json.dumps(row)
                if term.lower() in blob.lower():
                    hits.append((binname, row))
        for binname, row in hits[:12]:
            addr = row.get("func", row.get("addr"))
            label = row.get("name") or row.get("cpp")
            print(f"  {binname:<5} 0x{addr:08X}  {label}  {row.get('cpp','') if row.get('name') else ''}")
        if not hits:
            print("  (nothing)")
        elif len(hits) > 12:
            print(f"  ... {len(hits) - 12} more")

    if STATE.exists():
        print("\n--- loop state: confirmed_constants + lessons ---")
        st = json.loads(STATE.read_text())
        n = 0
        for k, v in (st.get("confirmed_constants") or {}).items():
            if term.lower() in f"{k} {v}".lower():
                print(f"  [{k}] {str(v)[:170]}")
                n += 1
        for l in st.get("lessons", []):
            if term.lower() in l.lower():
                print(f"  [lesson] {l[:170]}")
                n += 1
        if not n:
            print("  (nothing)")

    if is_addr and QUERY.exists():
        print(f"\n--- query.py xrefs-to {term} ---")
        r = subprocess.run([sys.executable, str(QUERY), "xrefs-to", term],
                           capture_output=True, text=True)
        out = (r.stdout or r.stderr).splitlines()[:14]
        print("\n".join("  " + l for l in out) if out else "  (nothing)")
        print(f"\n  also worth running: query.py func {term} | callers {term} | callees {term}")
    elif not is_addr:
        print("\n  (term is not an address; for an address you also get query.py xrefs-to)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("term", nargs="?", help="a symbol fragment, subsystem word, or 0xADDRESS")
    ap.add_argument("--inventory", action="store_true",
                    help="list every artefact and query.py subcommand available")
    a = ap.parse_args()
    if a.inventory or not a.term:
        return inventory()
    return search(a.term)


if __name__ == "__main__":
    sys.exit(main())
