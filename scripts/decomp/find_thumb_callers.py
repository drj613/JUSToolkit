#!/usr/bin/env python3
"""Find Thumb `bl`/`blx` call sites — the campaign's ARM-only blind spot.

Every caller analysis in this repo decoded ARM only: `query.py callers`,
`functions.json` edges, and each inline `bl` sweep. Iteration 95 found that
`Battle_CharaCreate` has ZERO ARM callers and is reached from Thumb, so any
finding of the form "0 callers, therefore a callback" or "therefore unreachable"
was resting on an incomplete search.

A Thumb long call is two halfwords:
    hi:  1111 0 <offset[22:12]>          0xF000-0xF7FF
    lo:  1111 1 <offset[11:1]>   BL      0xF800-0xFFFF   (stays Thumb)
         1110 1 <offset[11:1]>   BLX     0xE800-0xEFFF   (switches to ARM)
Target = pc + sign_extend(offset), with BLX clearing the low 2 bits.

FALSE POSITIVES ARE EXPECTED. Scanning halfword pairs across ARM code and data
manufactures "calls" wherever the bit patterns line up. `--verify` checks each
hit for Thumb plausibility: a `46c0` nop, a `b5xx` push, a `bdxx` pop, or another
BL/BLX pair nearby. Iteration 95's real hit had `46c0` padding and a literal pool
around it; the ARM reading of those bytes was incoherent.

Usage:
  find_thumb_callers.py --to 0x02156A38          # who calls this, from Thumb?
  find_thumb_callers.py --audit                  # every ARM function with no ARM
                                                 # caller but a Thumb one
  find_thumb_callers.py --selftest
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import struct_fields as SF                                        # noqa: E402

REGIONS = ['arm9'] + [f'ov{i}' for i in range(15)]
ANCHOR = (0x0214D65E, 0x02156A38)     # iteration 95, hand-verified


def halfwords(region):
    words, base = SF.load(region)
    out = []
    for x in words:
        out.append(x & 0xFFFF)
        out.append((x >> 16) & 0xFFFF)
    return out, base


def scan(region):
    """[(site, target, kind)] for every Thumb bl/blx pair in `region`."""
    hs, base = halfwords(region)
    hits = []
    for i in range(len(hs) - 1):
        hi, lo = hs[i], hs[i + 1]
        if not (0xF000 <= hi <= 0xF7FF):
            continue
        if 0xE800 <= lo <= 0xEFFF:
            kind = 'blx'
        elif 0xF800 <= lo <= 0xFFFF:
            kind = 'bl'
        else:
            continue
        off = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
        if off & 0x400000:
            off -= 0x800000
        tgt = base + i * 2 + 4 + off
        if kind == 'blx':
            tgt &= ~3
        hits.append((base + i * 2, tgt, kind))
    return hits, hs, base


def plausible(hs, base, site):
    """Guard against byte-pattern coincidence: does this look like Thumb code?"""
    i = (site - base) // 2
    for j in range(max(0, i - 8), min(len(hs), i + 8)):
        h = hs[j]
        if h == 0x46C0:                       # nop (mov r8, r8), Thumb padding
            return 'nop'
        if 0xB500 <= h <= 0xB5FF:             # push {..., lr}
            return 'push'
        if 0xBD00 <= h <= 0xBDFF:             # pop {..., pc}
            return 'pop'
    for j in (i - 2, i + 2):                  # another call adjacent
        if 0 <= j < len(hs) - 1 and 0xF000 <= hs[j] <= 0xF7FF:
            if 0xE800 <= hs[j + 1] <= 0xFFFF:
                return 'call'
    return None


OVERLAP_BASE = 0x0214CD20        # ov0-ov9 all load here; see the campaign's
                                 # phantom-caller hazard


def invalid_edge(kind, target_mode, caller_region, target_region):
    """Reasons a decoded Thumb call cannot be a real edge.

    Two filters, both learned from this ROM:

    * A Thumb `bl` STAYS in Thumb. It cannot call an ARM function. Any decoded
      `bl` landing on an ARM-mode target is a byte-pattern coincidence, however
      plausible its neighbourhood looks.
    * Ten overlays share load address 0x0214CD20. A "caller" in ov8 whose target
      resolves into ov6's address range is the phantom-caller hazard, not a call:
      the two are never resident together.
    """
    if kind == 'bl' and target_mode == 'arm':
        return 'bl cannot target ARM'
    if (caller_region != target_region
            and caller_region.startswith('ov') and target_region.startswith('ov')
            and int(caller_region[2:]) <= 9 and int(target_region[2:]) <= 9):
        return f'phantom: {caller_region} and {target_region} share {OVERLAP_BASE:#x}'
    return None


def arm_callers(addr):
    """(ARM caller count, mode, provenance) from functions.json.

    Provenance matters: overlays overlap, so resolving a target address to a
    region by range is ambiguous by construction -- it returns whichever overlay
    is checked first. The declared provenance is the only reliable answer, and
    using the range instead made this tool reject its own verified anchor.
    """
    for f in json.load(open(os.path.join(ROOT, 'jus_files', 'analysis',
                                         'functions.json')))['functions']:
        if int(f['addr'], 16) == addr:
            return len(f.get('callers', [])), f.get('mode'), f.get('provenance')
    return None, None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--to', type=lambda s: int(s, 0), action='append', default=[])
    ap.add_argument('--audit', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()

    if a.selftest:
        hits, hs, base = scan('ov6')
        site, tgt = ANCHOR
        match = [h for h in hits if h[0] == site and h[1] == tgt]
        assert match, f'selftest: known Thumb blx {site:#x} -> {tgt:#x} not found'
        assert match[0][2] == 'blx', f'selftest: decoded as {match[0][2]}, expected blx'
        assert plausible(hs, base, site), 'selftest: verified hit failed the plausibility check'
        print(f'selftest OK: {len(hits)} Thumb call pairs in ov6; '
              f'the hand-verified {site:#010x} -> {tgt:#010x} blx is among them')
        return 0

    if a.to:
        want = set(a.to)
        for region in REGIONS:
            try:
                hits, hs, base = scan(region)
            except Exception:
                continue
            for site, tgt, kind in hits:
                if tgt in want:
                    _n, tmode, tprov = arm_callers(tgt)
                    bad = invalid_edge(kind, tmode, region, tprov or region)
                    print(f'  {region:<5} {site:#010x} thumb {kind} -> {tgt:#010x} '
                          f'[plausibility: {plausible(hs, base, site) or "NONE"}]'
                          + (f'  REJECTED: {bad}' if bad else '  ACCEPTED'))
        for t in sorted(want):
            n, mode, prov = arm_callers(t)
            print(f'  {t:#010x}: functions.json ARM callers = {n}, '
                  f'mode = {mode}, provenance = {prov}')
        return 0

    if a.audit:
        fns = json.load(open(os.path.join(ROOT, 'jus_files', 'analysis',
                                          'functions.json')))['functions']
        zero = {int(f['addr'], 16): f for f in fns
                if f.get('mode') == 'arm' and not f.get('callers')}
        found = {}
        rejected = 0
        for region in REGIONS:
            try:
                hits, hs, base = scan(region)
            except Exception:
                continue
            for site, tgt, kind in hits:
                if tgt in zero and plausible(hs, base, site):
                    if invalid_edge(kind, zero[tgt].get('mode'), region,
                                    zero[tgt]['provenance']):
                        rejected += 1
                        continue
                    found.setdefault(tgt, []).append((region, site, kind))
        print(f'{len(zero)} ARM functions have no ARM caller; '
              f'{len(found)} of them have an ACCEPTED Thumb caller '
              f'({rejected} edges rejected as bl-to-ARM or phantom-overlay)\n')
        for tgt in sorted(found):
            f = zero[tgt]
            print(f'  {tgt:#010x} ({f["provenance"]}, size {f.get("size")}):')
            for region, site, kind in found[tgt][:3]:
                print(f'       <- {region} {site:#010x} {kind}')
        return 0

    ap.error('pass --to ADDR, --audit, or --selftest')


if __name__ == '__main__':
    sys.exit(main())
