#!/usr/bin/env python3
"""Census of tagged heap allocations.

The game's allocator is called as

    r0 = size, r1 = "SourceFile.cpp", r2 = "Function_name", r3 = tag
    bl 0x0201A21C

so every allocation site names itself. That binding is at the CALL SITE, which
makes it far stronger evidence than extract_symbols.py's nearest-function
heuristic (which can only say "this string is near this code").

Method: scan the flat disassembly in jus_files/analysis/disasm/*.txt for calls to
the allocator, then back-scan up to WINDOW instructions for the last write to
r0/r1/r2. Only immediate `mov` and pc-relative `ldr` are resolved.

Guards (learned the hard way in earlier wakes):
  * a register written by anything other than mov-imm / ldr-pc is reported as
    COMPUTED, never guessed at;
  * the back-scan stops at a function boundary (push / bx lr / pop {..,pc}) so a
    size from the previous function is never attributed here;
  * a pc-relative literal must land on a `.word` line, else it is dropped;
  * a name string must be printable ASCII from the strings dump, else dropped.

Usage:
  alloc_census.py                     # every resolved site, sorted by size
  alloc_census.py --min-size 0x400    # only large objects
  alloc_census.py --name Chara        # substring filter on file or function
  alloc_census.py --selftest
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DISASM = os.path.join(ROOT, 'jus_files', 'analysis', 'disasm')
ALLOC = 0x0201A21C
WINDOW = 14
REGIONS = ['arm9'] + [f'ov{i}' for i in range(15)]

LINE = re.compile(r'^0x([0-9A-Fa-f]{8}): ([0-9a-f]{8})  (.*)$')
MOV_IMM = re.compile(r'^mov r([0-2]), #(-?(?:0x[0-9a-fA-F]+|\d+))$')
LDR_PC = re.compile(r'^ldr r([0-2]), \[pc, #(0x[0-9a-fA-F]+|\d+)\]$')
WORD = re.compile(r'^\.word (0x[0-9A-Fa-f]+)$')
BL_ALLOC = re.compile(r'^bl #(0x[0-9a-fA-F]+)$')
# a back-scan must not cross out of the function it started in
BOUNDARY = re.compile(r'^(push |bx lr$|pop \{.*pc\}$)')


def ensure_strings_cache():
    """Build (once) a per-region dump of every string, via query.py.

    Cached under jus_files/analysis/strings_cache/ so the census never depends on
    a scratch directory or an environment variable.
    """
    cache = os.path.join(ROOT, 'jus_files', 'analysis', 'strings_cache')
    os.makedirs(cache, exist_ok=True)
    query = os.path.join(ROOT, 'scripts', 'analysis', 'query.py')
    for region in REGIONS:
        dest = os.path.join(cache, region + '.txt')
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            continue
        res = subprocess.run([sys.executable, query, 'strings', region, '--all'],
                             capture_output=True, text=True)
        if res.returncode == 0:
            open(dest, 'w', encoding='utf-8').write(res.stdout)
    return cache


def load_strings(strdir):
    """addr -> string, from `query.py strings REGION --all` dumps."""
    out = {}
    if not strdir or not os.path.isdir(strdir):
        return out
    for name in sorted(os.listdir(strdir)):
        for line in open(os.path.join(strdir, name), encoding='utf-8', errors='replace'):
            m = re.match(r'^(0x[0-9A-Fa-f]{8}) \(\w+\): (.*)$', line.rstrip('\n'))
            if m:
                out[int(m.group(1), 16)] = m.group(2)
    return out


def load_region(region):
    """[(addr, word, text)] for one region, plus addr -> index."""
    path = os.path.join(DISASM, region + '.txt')
    if not os.path.exists(path):
        return [], {}
    rows, idx = [], {}
    for line in open(path, encoding='utf-8', errors='replace'):
        m = LINE.match(line.rstrip('\n'))
        if not m:
            continue
        addr = int(m.group(1), 16)
        idx[addr] = len(rows)
        rows.append((addr, int(m.group(2), 16), m.group(3).strip()))
    return rows, idx


def resolve(rows, idx, call_i):
    """Back-scan for the last write to r0/r1/r2 before rows[call_i]."""
    found = {}
    for j in range(call_i - 1, max(-1, call_i - 1 - WINDOW), -1):
        addr, _word, text = rows[j]
        if BOUNDARY.match(text):
            break                          # guard: do not cross a function edge
        m = MOV_IMM.match(text)
        if m:
            found.setdefault(int(m.group(1)), ('imm', int(m.group(2), 0)))
            continue
        m = LDR_PC.match(text)
        if m:
            reg = int(m.group(1))
            lit = addr + 8 + int(m.group(2), 0)
            k = idx.get(lit)
            val = None
            if k is not None:
                w = WORD.match(rows[k][2])
                if w:
                    val = int(w.group(1), 16)
            found.setdefault(reg, ('lit', val))
            continue
        # any other write to r0/r1/r2 makes it computed -- do not guess
        m = re.match(r'^\w+ r([0-2]),', text)
        if m and not text.startswith(('cmp', 'cmn', 'tst', 'teq', 'str')):
            found.setdefault(int(m.group(1)), ('computed', None))
    return found


def census():
    strings = load_strings(ensure_strings_cache())
    out = []
    for region in REGIONS:
        rows, idx = load_region(region)
        for i, (addr, _w, text) in enumerate(rows):
            m = BL_ALLOC.match(text)
            if not m or int(m.group(1), 16) != ALLOC:
                continue
            f = resolve(rows, idx, i)
            size = f.get(0, (None, None))
            cpp = f.get(1, (None, None))
            fn = f.get(2, (None, None))

            def name(entry):
                if entry[0] == 'lit' and entry[1] is not None:
                    return strings.get(entry[1], f'<{entry[1]:#010x}>')
                return {'imm': 'IMM', 'computed': 'COMPUTED'}.get(entry[0], 'NOT_FOUND')

            out.append({
                'region': region,
                'site': addr,
                'size': size[1] if size[0] == 'imm' else None,
                'size_note': 'COMPUTED' if size[0] == 'computed' else
                             ('NOT_FOUND' if size[0] is None else ''),
                'cpp': name(cpp),
                'func': name(fn),
            })
    return out


def selftest():
    """Anchor: Battle_CharaCreate. Verified by hand from the ov6 disassembly --
    0x02156A50 mov r0,#0x1f0 / 0x02156A48-4C ldr r1,r2 / 0x02156A58 bl."""
    rows = census()
    hit = [r for r in rows if r['site'] == 0x02156A58]
    assert hit, 'selftest: allocator call at 0x02156A58 not found'
    h = hit[0]
    assert h['size'] == 0x1F0, f"selftest: size {h['size']!r} != 0x1F0"
    assert h['region'] == 'ov6', f"selftest: region {h['region']}"
    if h['func'] != 'IMM':                 # only when the strings dump is present
        assert h['func'] == 'Battle_CharaCreate', f"selftest: func {h['func']!r}"
        assert h['cpp'] == 'BattleChara.cpp', f"selftest: cpp {h['cpp']!r}"
    named = [r for r in rows if r['func'] not in ('IMM', 'COMPUTED', 'NOT_FOUND')
             and not r['func'].startswith('<')]
    assert len(rows) > 400, f'selftest: only {len(rows)} sites'
    print(f'selftest OK: {len(rows)} sites, {len(named)} with a resolved name')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--min-size', type=lambda s: int(s, 0), default=0)
    ap.add_argument('--name', help='substring filter on the .cpp or function name')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    rows = census()
    total = len(rows)
    sized = [r for r in rows if r['size'] is not None]
    keep = [r for r in sized if r['size'] >= a.min_size]
    if a.name:
        keep = [r for r in keep if a.name.lower() in (r['cpp'] + ' ' + r['func']).lower()]
    keep.sort(key=lambda r: -r['size'])
    print(f'{total} allocator calls; {len(sized)} with an immediate size; '
          f'{total - len(sized)} computed or unresolved (NOT counted below)')
    print(f'{"size":>8}  {"site":<12} {"region":<6} {"function":<34} file')
    for r in keep:
        print(f'{r["size"]:#8x}  {r["site"]:#010x}  {r["region"]:<6} '
              f'{r["func"]:<34} {r["cpp"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
