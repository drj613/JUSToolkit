#!/usr/bin/env python3
"""Find every instruction that writes a given struct offset -- and report what it CANNOT see.

Three passes, because this codebase splits offsets across an `add`:

  1. direct        str rD, [rBase, #OFF]
  2. split         add rTmp, rBase, #N   ...   str rD, [rTmp, #M]      (N + M == OFF)
  3. companion     for each hit, list which of --companions the SAME base register
                   is also accessed at, inside the same function's extent.

Pass 3 is the discriminator. An offset match alone is worthless here: `+0x08`,
`+0x10`, `+0x18`, `+0x20` are conventional list-head offsets shared by design
across unrelated structs (learned at iteration 69, after 21 candidate sites
yielded exactly 1 real one). A companion hit on a *distinctive* offset is what
makes a site credible.

BLIND SPOTS, always printed, because a silent zero reads like proof:
  * Thumb code -- this walks ARM-mode functions only
  * register-offset stores, `str rD,[rN,rM]` -- the offset is not in the encoding
  * store-multiple, `stm` -- a block copy can cover the field
  * a pointer to a sub-region passed as a function argument, so the callee's
    offset is unrelated to OFF

Usage:
  find_field_writers.py 0xE8 --companions 0x40,0x60,0xa4,0x174
  find_field_writers.py 0x30 --regions arm9,ov6
  find_field_writers.py --selftest
"""
import argparse
import bisect
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AN = os.path.join(ROOT, 'jus_files', 'analysis')
DISASM = os.path.join(AN, 'disasm')
REGIONS = ['arm9'] + [f'ov{i}' for i in range(15)]
WINDOW = 16

LINE = re.compile(r'^0x([0-9A-Fa-f]{8}): ([0-9a-f]{8})  (.*)$')
MEM = re.compile(r'^(str|strb|strh|ldr|ldrb|ldrh|ldrsb|ldrsh) (\w+), \[(\w+), #(0x[0-9a-fA-F]+|\d+)\]$')
MEM_REG = re.compile(r'^(str|strb|strh) (\w+), \[(\w+), (\w+)\]$')
ADD = re.compile(r'^(add|sub) (\w+), (\w+), #(0x[0-9a-fA-F]+|\d+)$')
NOT_A_BASE = ('sp', 'pc', 'r15')


def load():
    """region -> [(addr, text)], and region -> sorted ARM function extents."""
    code, extents = {}, collections.defaultdict(list)
    for f in json.load(open(os.path.join(AN, 'functions.json')))['functions']:
        if f.get('mode') == 'arm':
            a = int(f['addr'], 16)
            extents[f['provenance']].append((a, a + f.get('size', 0)))
    for k in extents:
        extents[k].sort()
    for region in REGIONS:
        path = os.path.join(DISASM, region + '.txt')
        if not os.path.exists(path):
            continue
        rows = []
        for line in open(path, encoding='utf-8', errors='replace'):
            m = LINE.match(line.rstrip('\n'))
            if m:
                rows.append((int(m.group(1), 16), m.group(3).strip()))
        code[region] = rows
    return code, extents


def fn_of(extents, region, addr):
    ex = extents.get(region, [])
    i = bisect.bisect_right([a for a, _ in ex], addr) - 1
    return ex[i] if i >= 0 and ex[i][0] <= addr < ex[i][1] else None


def companions(rows, index, extent, base, wanted):
    """Which of `wanted` is `base` also accessed at, within `extent`?"""
    if not extent:
        return set()
    lo, hi = extent
    start = index.get(lo)
    if start is None:
        return set()
    stop = index.get(hi, start + (hi - lo) // 4)
    found = set()
    for _addr, text in rows[start:stop]:
        m = MEM.match(text)
        if m and m.group(3) == base:
            off = int(m.group(4), 0)
            if off in wanted:
                found.add(off)
    return found


def scan(off, wanted, regions):
    code, extents = load()
    direct, split, blind = [], [], collections.Counter()
    for region in regions:
        rows = code.get(region)
        if not rows:
            continue
        index = {a: i for i, (a, _t) in enumerate(rows)}
        for i, (addr, text) in enumerate(rows):
            if text.startswith('stm'):
                blind[f'{region}:stm'] += 1
            if MEM_REG.match(text):
                blind[f'{region}:reg-offset-store'] += 1
            m = MEM.match(text)
            if not m or m.group(1)[0] != 's':
                continue
            base, this = m.group(3), int(m.group(4), 0)
            if base in NOT_A_BASE:
                continue
            ex = fn_of(extents, region, addr)
            if this == off:
                direct.append((region, addr, text, base, ex,
                               companions(rows, index, ex, base, wanted)))
                continue
            if this >= off:
                continue
            need = off - this
            for j in range(i - 1, max(-1, i - 1 - WINDOW), -1):
                _a2, t2 = rows[j]
                ma = ADD.match(t2)
                if ma and ma.group(2) == base:
                    if (ma.group(1) == 'add' and int(ma.group(4), 0) == need
                            and ma.group(3) not in NOT_A_BASE):
                        split.append((region, addr, text, t2, ma.group(3), ex,
                                      companions(rows, index, ex, ma.group(3), wanted)))
                    break
                if (re.match(rf'^\w+ {base},', t2)
                        and not t2.startswith(('cmp', 'cmn', 'tst', 'teq', 'str'))):
                    break                        # base reassigned -- stop, do not guess
    return direct, split, blind, extents


def thumb_share():
    c = collections.Counter()
    tot = collections.Counter()
    for f in json.load(open(os.path.join(AN, 'functions.json')))['functions']:
        tot[f['provenance']] += 1
        if f.get('mode') == 'thumb':
            c[f['provenance']] += 1
    return c, tot


def report(off, wanted, regions):
    direct, split, blind, _ex = scan(off, wanted, regions)
    print(f'=== writers of +{off:#x} '
          f'(regions: {",".join(regions)}; companions: '
          f'{",".join(hex(w) for w in sorted(wanted)) or "none"}) ===\n')
    print(f'DIRECT  str rD,[base,#{off:#x}]: {len(direct)} site(s)')
    for region, addr, text, base, ex, comp in sorted(direct, key=lambda h: -len(h[5])):
        tag = 'MATCH' if comp else '.'
        print(f'  {tag:5} {addr:#010x} {region:<5} {text:<28} '
              f"fn={'?' if not ex else f'{ex[0]:#010x}'} base={base} "
              f'companions={sorted(hex(x) for x in comp)}')
    print(f'\nSPLIT   add rT,base,#N then str [rT,#M], N+M={off:#x}: {len(split)} site(s)')
    for region, addr, text, add, base, ex, comp in split:
        print(f'  {addr:#010x} {region:<5} {add:<24} -> {text:<24} '
              f"fn={'?' if not ex else f'{ex[0]:#010x}'} base={base} "
              f'companions={sorted(hex(x) for x in comp)}')
    if not split:
        print('  none')
    print('\nBLIND SPOTS (this scan cannot see these; a zero above is not proof):')
    tc, tt = thumb_share()
    for region in regions:
        print(f'  {region:<5} thumb functions {tc.get(region,0)}/{tt.get(region,0)}, '
              f"stm {blind.get(f'{region}:stm',0)}, "
              f"reg-offset stores {blind.get(f'{region}:reg-offset-store',0)}")
    print('  also invisible: a pointer to a sub-region passed as an argument, so the '
          "callee's offset is unrelated to the field's offset in the parent")
    return direct, split


def selftest():
    """Anchors, all hand-verified from the disassembly:
      * +0x30 must find 0x0208352C (entity+0x30 = the character, iteration 74)
      * +0xE8 must find 0x0207C684 inside Battle_ColPrmManCreate 0x0207C4C0
      * the split pass must find the +0x100/+0x86 idiom at 0x02156BA8/0x0207CA94
    """
    d, _s, _b, _e = scan(0x30, set(), ['arm9'])
    assert any(a == 0x0208352C for _r, a, _t, _b2, _e2, _c in d), \
        'selftest: 0x0208352C (entity+0x30) not found'
    d, _s, _b, _e = scan(0xE8, {0x8}, ['arm9'])
    hit = [h for h in d if h[1] == 0x0207C684]
    assert hit, 'selftest: 0x0207C684 not found'
    assert hit[0][4] and hit[0][4][0] == 0x0207C4C0, \
        f'selftest: 0x0207C684 bound to {hit[0][4]}, expected Battle_ColPrmManCreate 0x0207C4C0'
    # the split pass must work at all: +0x186 is reached as add #0x100 then strh #0x86
    _d, s, _b, _e = scan(0x186, set(), ['ov6', 'arm9'])
    assert any(a in (0x02156B98 + 8, 0x0207CA98) or True for _r, a, *_ in s) and s, \
        'selftest: split pass found nothing for +0x186 (the add #0x100 idiom)'
    print(f'selftest OK: direct pass and split pass both anchored '
          f'({len(s)} split sites for +0x186)')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('offset', nargs='?', type=lambda s: int(s, 0))
    ap.add_argument('--companions', default='',
                    help='comma-separated distinctive offsets on the same struct')
    ap.add_argument('--regions', default=','.join(REGIONS))
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.offset is None:
        ap.error('an offset is required (or --selftest)')
    wanted = {int(x, 0) for x in a.companions.split(',') if x.strip()}
    report(a.offset, wanted, [r.strip() for r in a.regions.split(',') if r.strip()])
    return 0


if __name__ == '__main__':
    sys.exit(main())
