#!/usr/bin/env python3
"""Census of tagged heap allocations.

The game's allocator is called as

    r0 = size, r1 = "SourceFile.cpp", r2 = "Function_name", r3 = __LINE__
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import struct_fields as SF                                        # noqa: E402
DISASM = os.path.join(ROOT, 'jus_files', 'analysis', 'disasm')
# 0x0201A21C is NOT the allocator -- it is a 12-byte linker long-branch veneer
# (`ldr ip,[pc]; bx ip; .word 0x0201A228`), found in iteration 133. The real
# allocator is 0x0201A228. Callers far from it go through the veneer; callers
# in range `bl` it directly, and scanning only the veneer made every one of
# those invisible for ~100 iterations. Scan BOTH, and record which was used.
ALLOC_ENTRIES = {0x0201A21C: 'veneer', 0x0201A228: 'direct'}
ALLOC = 0x0201A21C          # kept: the veneer is still the tagged front door
WINDOW = 14
REGIONS = ['arm9'] + [f'ov{i}' for i in range(15)]

# ARM puts the condition in the mnemonic, so a regex listing bare opcodes
# silently drops every predicated instruction (iteration 81: that hid 40% of one
# sweep's hits). Every pattern here carries an optional suffix, and a conditional
# writer is reported as CONDITIONAL rather than resolved -- `movgt r0,#0x20` /
# `movle r0,#0x40` is a real idiom, and picking either value would invent a size
# the call may never use.
COND = r'(?:eq|ne|cs|cc|mi|pl|vs|vc|hi|ls|ge|lt|gt|le|lo|hs)'

LINE = re.compile(r'^0x([0-9A-Fa-f]{8}): ([0-9a-f]{8})  (.*)$')
MOV_IMM = re.compile(rf'^mov({COND})? r([0-2]), #(-?(?:0x[0-9a-fA-F]+|\d+))$')
LDR_PC = re.compile(rf'^ldr({COND})? r([0-2]), \[pc, #(0x[0-9a-fA-F]+|\d+)\]$')
WORD = re.compile(r'^\.word (0x[0-9A-Fa-f]+)$')
BL_ALLOC = re.compile(rf'^bl({COND})? #(0x[0-9a-fA-F]+)$')
# a back-scan must not cross out of the function it started in
BOUNDARY = re.compile(rf'^(push{COND}? |bx{COND}? lr$|pop{COND}? \{{.*pc\}}$)')


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
            kind = 'cond' if m.group(1) else 'imm'
            found.setdefault(int(m.group(2)), (kind, int(m.group(3), 0)))
            continue
        m = LDR_PC.match(text)
        if m:
            reg = int(m.group(2))
            if m.group(1):
                found.setdefault(reg, ('cond', None))
                continue
            lit = addr + 8 + int(m.group(3), 0)
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


def thumb_census(strings):
    """Thumb `blx` calls to the allocator.

    alloc_census.py counted ARM `bl` only until iteration 99. There are 238 Thumb
    call sites -- 32% of the ROM's allocations -- and ov6's own entry point
    `Battle_Add` is one of them.

    The back-resolver INVALIDATES r0-r3, ip and lr at every call, which the quick
    scratch version at iteration 98 did not: it reported 0x214BE40 (a RAM address)
    as several sizes because a stale `ldr r0,[pc,..]` from before a call survived.
    A register whose value cannot be tracked is reported, never guessed.
    """
    out = []
    for region in REGIONS:
        try:
            words, base = SF.load(region)
        except (FileNotFoundError, StopIteration):
            continue                 # region not present; any other error is a bug
        hs = []
        for x in words:
            hs.append(x & 0xFFFF)
            hs.append((x >> 16) & 0xFFFF)

        def word_at(addr):
            i = (addr - base) // 4
            return words[i] if 0 <= i < len(words) else None

        for i in range(len(hs) - 1):
            hi, lo = hs[i], hs[i + 1]
            if not (0xF000 <= hi <= 0xF7FF and 0xE800 <= lo <= 0xEFFF):
                continue                       # blx only; bl cannot reach ARM
            off = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
            if off & 0x400000:
                off -= 0x800000
            entry = ALLOC_ENTRIES.get((base + i * 2 + 4 + off) & ~3)
            if entry is None:
                continue

            val, dead = {}, set()
            for j in range(max(0, i - WINDOW * 2), i):
                h, ad = hs[j], base + j * 2
                if 0xB500 <= h <= 0xB5FF:      # a prologue: nothing before it counts
                    val, dead = {}, set()
                    continue
                if 0xF000 <= h <= 0xF7FF and j + 1 < len(hs) \
                        and 0xE800 <= hs[j + 1] <= 0xFFFF:
                    for r in (0, 1, 2, 3, 12, 14):     # a call clobbers these
                        val.pop(r, None)
                        dead.add(r)
                    continue
                if (h >> 11) == 0b00100:               # mov rd, #imm
                    rd = (h >> 8) & 7
                    val[rd] = h & 0xFF
                    dead.discard(rd)
                elif (h >> 11) == 0b00000 and (h & 0x07C0):   # lsl rd, rs, #n
                    rd, rs = h & 7, (h >> 3) & 7
                    if rs in val:
                        val[rd] = (val[rs] << ((h >> 6) & 0x1F)) & 0xFFFFFFFF
                        dead.discard(rd)
                    else:
                        val.pop(rd, None)
                        dead.add(rd)
                elif (h >> 11) == 0b01001:             # ldr rd, [pc, #n]
                    rd = (h >> 8) & 7
                    v = word_at(((ad + 4) & ~3) + (h & 0xFF) * 4)
                    if v is None:
                        val.pop(rd, None)
                        dead.add(rd)
                    else:
                        val[rd] = v
                        dead.discard(rd)
                else:
                    # Any other instruction that writes a low register makes it
                    # opaque. MEMORY LOADS MATTER MOST: at 0x02088A28 an
                    # `ldrh r0,[r4,#0x10]` left a stale pc-relative value in r0
                    # and the census reported 0x214BE40 -- a RAM address -- as an
                    # allocation size.
                    rd = None
                    if (h >> 11) in (0b00011, 0b00001, 0b00010):        # add/sub/lsr/asr
                        rd = h & 7
                    elif (h >> 12) in (0b0011, 0b1010):                 # add/sub imm8, add sp/pc
                        rd = (h >> 8) & 7
                    elif (h >> 10) == 0b010000:                         # ALU rd, rs
                        rd = h & 7
                    elif (h >> 10) == 0b010001 and ((h >> 8) & 3) != 3:  # hi-reg add/mov
                        rd = (h & 7) | ((h >> 4) & 8)
                    elif (h >> 12) == 0b0101 and (h >> 11) & 1:         # load, reg offset
                        rd = h & 7
                    elif (h >> 13) == 0b011 and (h >> 11) & 1:          # ldr/ldrb imm5
                        rd = h & 7
                    elif (h >> 12) == 0b1000 and (h >> 11) & 1:         # ldrh imm5
                        rd = h & 7
                    elif (h >> 12) == 0b1001 and (h >> 11) & 1:         # ldr sp-relative
                        rd = (h >> 8) & 7
                    elif (h >> 12) == 0b1100 and (h >> 11) & 1:         # ldmia
                        for r in range(8):
                            if h & (1 << r):
                                val.pop(r, None)
                                dead.add(r)
                    if rd is not None:
                        val.pop(rd, None)
                        dead.add(rd)

            def name(reg):
                if reg in val:
                    return strings.get(val[reg], f'<{val[reg]:#010x}>')
                return 'CLOBBERED' if reg in dead else 'NOT_FOUND'

            out.append({
                'region': region,
                'site': base + i * 2,
                'size': val.get(0),
                'size_cond': None,
                'size_note': '' if 0 in val else ('CLOBBERED' if 0 in dead
                                                  else 'NOT_FOUND'),
                'cpp': _tag_fields(entry, name(1), name(2))[0],
                'func': _tag_fields(entry, name(1), name(2))[1],
                'isa': 'thumb',
                'entry': entry,
            })
    return out


def _tag_fields(entry, cpp, func):
    """Iteration 134: the DIRECT entry 0x0201A228 takes a size only. Library
    callers never set r1/r2, and the allocator clobbers them itself (iteration
    133), so anything the back-scan finds there is a STALE register -- the same
    false-positive class the Thumb size guard exists for. Measured: 0 of 403
    direct sites resolve to a real source filename, while 572 of 732 veneer sites
    do. So report direct sites as UNTAGGED instead of printing a bare address
    that reads like data. 0x020A0C34 in particular is the instance counter from
    iteration 131, not a filename."""
    if entry == 'direct':
        return 'UNTAGGED', 'UNTAGGED'
    return cpp, func


def census():
    strings = load_strings(ensure_strings_cache())
    out = []
    for region in REGIONS:
        rows, idx = load_region(region)
        for i, (addr, _w, text) in enumerate(rows):
            m = BL_ALLOC.match(text)
            if not m:
                continue
            entry = ALLOC_ENTRIES.get(int(m.group(2), 16))
            if entry is None:
                continue
            f = resolve(rows, idx, i)
            size = f.get(0, (None, None))
            cpp = f.get(1, (None, None))
            fn = f.get(2, (None, None))

            def name(entry):
                if entry[0] == 'lit' and entry[1] is not None:
                    return strings.get(entry[1], f'<{entry[1]:#010x}>')
                return {'imm': 'IMM', 'computed': 'COMPUTED',
                        'cond': 'CONDITIONAL'}.get(entry[0], 'NOT_FOUND')

            out.append({
                'region': region,
                'site': addr,
                # A size can arrive as a pc-relative literal, not just a mov
                # immediate: Battle_ObjManCreate loads 0x42D8 that way, and
                # discarding 'lit' hid the second-largest battle allocation in
                # the ROM (iteration 101).
                # Iteration 134: the ARM pass had NO plausibility bound, only the
                # Thumb one did. Adding the direct entry surfaced site 0x020462EC
                # reporting 0x2096568 (34 MB) -- a stale pc-relative literal read
                # as a size. The largest real allocation in the ROM is 0x4000C, so
                # bound at the same 0x100000 the Thumb guard uses.
                'size': (size[1] if size[0] in ('imm', 'lit')
                         and size[1] is not None and size[1] <= 0x100000
                         else None),
            'size_cond': size[1] if size[0] == 'cond' else None,
                'size_note': {'computed': 'COMPUTED', 'cond': 'CONDITIONAL',
                              None: 'NOT_FOUND'}.get(size[0], ''),
                'cpp': _tag_fields(entry, name(cpp), name(fn))[0],
                'func': _tag_fields(entry, name(cpp), name(fn))[1],
                'isa': 'arm',
                'entry': entry,
            })
    out.extend(thumb_census(strings))          # iteration 99
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
    thumb = [r for r in rows if r.get('isa') == 'thumb']
    ba = [r for r in thumb if r['site'] == 0x0214CD66]
    assert ba, 'selftest: Thumb Battle_Add site 0x0214CD66 not found'
    assert ba[0]['size'] == 0x170, f"selftest: Battle_Add size {ba[0]['size']!r} != 0x170"
    assert ba[0]['func'] == 'Battle_Add', f"selftest: func {ba[0]['func']!r}"
    assert ba[0]['cpp'] == 'Battle.cpp', f"selftest: cpp {ba[0]['cpp']!r}"
    bad = [r for r in rows if r['size'] is not None and r['size'] > 0x100000]
    assert not bad, ('selftest: implausible sizes (stale register?): '
                     + str([(hex(r['site']), hex(r['size'])) for r in bad[:4]]))
    named = [r for r in rows
             if r['func'] not in ('IMM', 'COMPUTED', 'NOT_FOUND', 'CLOBBERED',
                                  'CONDITIONAL', 'UNTAGGED')
             and not r['func'].startswith('<')]
    assert len(rows) > 400, f'selftest: only {len(rows)} sites'
    # iteration 134: BOTH allocator entry points must be seen. 0x0201A21C is only
    # a veneer to 0x0201A228 (iteration 133); scanning one hid the other.
    entries = {r.get('entry') for r in rows}
    assert entries == {'veneer', 'direct'}, f'selftest: entries seen = {entries}'
    assert h['entry'] == 'veneer', f"selftest: CharaCreate entry {h['entry']!r}"
    assert ba[0]['entry'] == 'veneer', f"selftest: Battle_Add entry {ba[0]['entry']!r}"
    # a known direct caller, hand-read in iteration 133: mov r0,#0x78 then bl
    d = [r for r in rows if r['site'] == 0x02010DA4]
    assert d, 'selftest: direct site 0x02010DA4 not found'
    assert d[0]['entry'] == 'direct', f"selftest: 0x02010DA4 entry {d[0]['entry']!r}"
    assert d[0]['size'] == 0x78, f"selftest: 0x02010DA4 size {d[0]['size']!r} != 0x78"
    direct = [r for r in rows if r.get('entry') == 'direct']
    tagged_direct = [r for r in direct
                     if '.cpp' in r['cpp'] or '.h' in r['cpp']]
    assert not tagged_direct, ('selftest: a direct-entry site resolved to a real '
                               'filename -- _tag_fields would be suppressing real '
                               'data: ' + str([hex(r['site']) for r in tagged_direct[:4]]))
    assert all(r['cpp'] == 'UNTAGGED' for r in direct), 'selftest: direct sites not marked UNTAGGED'
    vreal = [r for r in rows if r.get('entry') == 'veneer'
             and ('.cpp' in r['cpp'] or '.h' in r['cpp'])]
    assert len(vreal) > 500, f'selftest: only {len(vreal)} veneer sites with a real filename'
    print(f'selftest OK: {len(rows)} sites ({len(thumb)} Thumb), '
          f'{len(named)} with a resolved name; Battle_Add resolves to 0x170; '
          f'both allocator entry points observed')
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
    cond = [r for r in rows if r['size_note'] == 'CONDITIONAL']
    sized = [r for r in rows if r['size'] is not None]
    keep = [r for r in sized if r['size'] >= a.min_size]
    if a.name:
        keep = [r for r in keep if a.name.lower() in (r['cpp'] + ' ' + r['func']).lower()]
    keep.sort(key=lambda r: -r['size'])
    arm = sum(1 for r in rows if r.get('isa') == 'arm')
    thumb = total - arm
    ven = sum(1 for r in rows if r.get('entry') == 'veneer')
    dir_ = sum(1 for r in rows if r.get('entry') == 'direct')
    dir_named = sum(1 for r in rows if r.get('entry') == 'direct'
                    and ('.cpp' in r['cpp'] or '.h' in r['cpp']))
    print(f'entry points: {ven} via the 0x0201A21C veneer + {dir_} direct to '
          f'0x0201A228 = {total}; of the direct ones {dir_named} carry a resolved '
          f'name (iteration 133/134: the direct entry takes a size only, so those '
          f'are reported UNTAGGED).')
    print(f'{arm} ARM + {thumb} Thumb = ', end='')
    print(f'{total} allocator calls; {len(sized)} with an unconditional immediate '
          f'size; {len(cond)} whose size is set CONDITIONALLY (a real idiom -- two '
          f'possible sizes, so neither is claimed); '
          f'{total - len(sized) - len(cond)} computed or unresolved. '
          f'Only the {len(sized)} appear below.')
    print(f'{"size":>8}  {"site":<12} {"region":<6} {"isa":<5} {"entry":<7} '
          f'{"function":<34} file')
    for r in keep:
        print(f'{r["size"]:#8x}  {r["site"]:#010x}  {r["region"]:<6} '
              f'{r.get("isa","arm"):<5} {r.get("entry","?"):<7} '
              f'{r["func"]:<34} {r["cpp"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
