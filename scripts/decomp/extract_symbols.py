#!/usr/bin/env python3
"""Recover developer symbol names from assert strings, and bind them to functions.

The retail ROM still contains the debug strings the developers compiled in:
function names (`Battle_ObjShotManCreate`) paired with source filenames
(`BattleObjShot.cpp`). `Battle-Engine-Map.md` used this once, in passing, to
confirm ov11 is the battle-AI overlay via `BattleAI_*` strings. Nothing
systematic was ever extracted, so most of the engine stayed anonymous while this
campaign referred to functions purely by address.

Method, and its limits:

  --names    List `Foo_Bar`-style identifiers and `*.cpp` filenames per binary.

  --bind     For each name string, find the 32-bit literal that points at it,
             then walk BACK to the nearest preceding `stmfd sp!,{..,lr}`. That
             push is the start of the function which references the string, so
             the binding is a real name for a real function.

  --nearest A  Report which named function is the closest one *below* address A.
             **This is a neighborhood, not containment.** Unnamed functions sit
             in between, so a result of `Battle_ObjShotManCreate + 0x219C` means
             "somewhere after that function", NOT "inside it". Because ARM
             toolchains lay code out per translation unit, a near neighbour is
             usually the same `.cpp` — which is useful, and still only PLAUSIBLE.

Only functions that reference an assert string get a name. Everything else stays
anonymous; this widens the named set, it does not produce a full symbol table.

    python3 scripts/decomp/extract_symbols.py --names
    python3 scripts/decomp/extract_symbols.py --bind --binary ov6
    python3 scripts/decomp/extract_symbols.py --nearest 0x0216C958 --binary ov6

Read-only.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from pathlib import Path

ARM9 = Path("jus_files/arm9/arm9.bin")
ARM9_BASE = 0x02000000
OVERLAY_DIR = Path("jus_files/overlays")

# An identifier plausible as a C/C++ symbol: starts with a letter, has an
# underscore or an interior capital, NUL-terminated, not a path or a filename.
IDENT = re.compile(rb"[A-Za-z][A-Za-z0-9_]{5,60}\x00")
CPP = re.compile(rb"[A-Za-z0-9_]{3,48}\.cpp")


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


def looks_like_symbol(s: str) -> bool:
    if s.endswith(".cpp") or "/" in s or "." in s or " " in s:
        return False
    return "_" in s or any(c.isupper() for c in s[1:])


def name_strings(buf: bytes, base: int) -> dict[int, str]:
    out = {}
    for m in IDENT.finditer(buf):
        s = m.group(0)[:-1].decode("ascii", "replace")
        if looks_like_symbol(s):
            out[base + m.start()] = s
    return out


def func_starts(buf: bytes, base: int) -> list[int]:
    """Addresses of `stmfd sp!,{...,lr}` — ARM function prologues."""
    starts = []
    for o in range(0, len(buf) - 3, 4):
        w = int.from_bytes(buf[o:o + 4], "little")
        if (w & 0x0FFF0000) == 0x092D0000 and (w & 0x4000):
            starts.append(base + o)
    return starts


def bind(buf: bytes, base: int) -> list[tuple[str, int, int, int]]:
    """(name, function_start, literal_addr, string_addr), for resolvable names."""
    names = name_strings(buf, base)
    starts = func_starts(buf, base)
    out = []
    for o in range(0, len(buf) - 3, 4):
        w = int.from_bytes(buf[o:o + 4], "little")
        if w not in names:
            continue
        lit = base + o
        i = bisect.bisect_right(starts, lit) - 1
        # a function referencing its own assert string is normally within a few
        # hundred bytes of its prologue; beyond that the attribution is noise
        if i >= 0 and lit - starts[i] < 0x800:
            out.append((names[w], starts[i], lit, w))
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--binary")
    ap.add_argument("--names", action="store_true")
    ap.add_argument("--bind", action="store_true")
    ap.add_argument("--nearest", type=lambda s: int(s, 0))
    ap.add_argument("--json", type=Path, help="write bindings to this file")
    args = ap.parse_args()
    if not (args.names or args.bind or args.nearest is not None):
        ap.error("pick --names, --bind or --nearest")

    bins = binaries(args.binary)
    if not bins:
        print("no binaries found", file=sys.stderr)
        return 1

    if args.names:
        total_cpp = set()
        for name, buf, base in bins:
            cpp = sorted({m.group(0).decode() for m in CPP.finditer(buf)})
            syms = name_strings(buf, base)
            total_cpp |= set(cpp)
            print(f"{name}: {len(syms)} symbol strings, {len(cpp)} .cpp files")
            if cpp:
                print(f"   {', '.join(cpp)}")
        print(f"\n{len(total_cpp)} distinct .cpp source files across all binaries")

    allb = {}
    if args.bind or args.json:
        for name, buf, base in bins:
            rows = bind(buf, base)
            allb[name] = [dict(name=n, func=f, literal=l, string=s) for n, f, l, s in rows]
            if args.bind:
                print(f"\n{name}: {len(rows)} name -> function bindings")
                for n, f, l, s in sorted(rows, key=lambda r: r[1]):
                    print(f"   0x{f:08X}  {n:<34} (literal 0x{l:08X})")
        if args.json:
            args.json.write_text(json.dumps(allb, indent=1))
            print(f"\nwrote {args.json}")

    if args.nearest is not None:
        a = args.nearest
        for name, buf, base in bins:
            if not (base <= a < base + len(buf)):
                continue
            rows = bind(buf, base)
            fs = sorted({f for _, f, _, _ in rows})
            lbl = {f: n for n, f, _, _ in rows}
            i = bisect.bisect_right(fs, a) - 1
            if i < 0:
                print(f"0x{a:08X} in {name}: before the first named function")
            else:
                print(f"0x{a:08X} in {name}: {lbl[fs[i]]} + 0x{a - fs[i]:X}")
                print("   NEIGHBOURHOOD, NOT CONTAINMENT — unnamed functions lie between. "
                      "Same-.cpp is likely but only PLAUSIBLE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
