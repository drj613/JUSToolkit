#!/usr/bin/env python3
"""Which ARM9 overlay is resident right now?

The 14 overlays SHARE load addresses, so an address in those windows means nothing
without naming the resident overlay:

    0x0214CD20  ov00-ov09
    0x02172A60  ov10, ov11
    0x021AC1C0  ov12, ov13

Overlays are stored uncompressed, so a resident one matches live RAM byte for byte.
Method: dump main RAM, compare each overlay image against its load address, report
the match percentage. ~100% over a large overlay is conclusive; a low percentage is
not evidence of anything except "not this one".

Two cautions carried from Overlay-Residency-By-Mode.md:
  * ov09 and ov13 are 32 bytes each. A tiny mostly-zero blob matches almost
    anything, so their percentages are meaningless.
  * Report which SCREEN was sampled, verified from pixels, not from where you think
    the navigation ended up. A previous residency run labelled its sample "the deck
    editor" when the navigation had actually landed on the deck select list -- the
    old route walked into デッキメイク by accident. A label is a claim and needs the
    same evidence as a number.

Usage:
    python3 overlay_residency.py [--label NAME] [--ram dump.bin]
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OVL_DIR = os.path.join(ROOT, "jus_files", "arm9", "overlays")
BASE = 0x02000000
RAM_END = 0x02400000
LOAD = {}
for i in range(0, 10):
    LOAD["ov%02d" % i] = 0x0214CD20
LOAD["ov10"] = LOAD["ov11"] = 0x02172A60
LOAD["ov12"] = LOAD["ov13"] = 0x021AC1C0
TINY = 1024   # below this, a match percentage is not informative


def dump_ram(path):
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "dump",
                        hex(BASE), hex(RAM_END), path],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("dump failed:\n%s%s" % (r.stdout, r.stderr))
    return path


def match_pct(ram, overlay, load_addr):
    off = load_addr - BASE
    n = min(len(overlay), len(ram) - off)
    if n <= 0:
        return 0.0, 0
    same = sum(1 for i in range(n) if ram[off + i] == overlay[i])
    return 100.0 * same / n, n


def main():
    label = "unlabelled"
    ram_path = "/tmp/jus_resid.bin"
    a = sys.argv[1:]
    for i, x in enumerate(a):
        if x == "--label":
            label = a[i + 1]
        elif x == "--ram":
            ram_path = a[i + 1]
    if "--ram" not in a:
        dump_ram(ram_path)
    with open(ram_path, "rb") as f:
        ram = f.read()

    print("overlay residency on screen %r" % label)
    print("%-6s %-12s %-9s %-7s %s" % ("ovl", "load", "size", "match", "note"))
    rows = []
    for name in sorted(LOAD):
        p = os.path.join(OVL_DIR, "arm9_%s.bin" % name)
        if not os.path.exists(p):
            continue
        with open(p, "rb") as f:
            ov = f.read()
        pct, n = match_pct(ram, ov, LOAD[name])
        note = "TOO SMALL to be meaningful" if len(ov) < TINY else (
            "<-- RESIDENT" if pct > 99.0 else "")
        print("%-6s 0x%08X   %-9d %6.1f%%  %s" % (name, LOAD[name], len(ov), pct, note))
        rows.append((name, pct, len(ov)))
    big = [r for r in rows if r[2] >= TINY]
    res = [r for r in big if r[1] > 99.0]
    print("\nresident (>99%%, excluding tiny overlays): %s"
          % (", ".join("%s %.1f%%" % (n, p) for n, p, _ in res) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
