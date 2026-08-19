#!/usr/bin/env python3
"""Map which struct offsets are accessed through a known base ADDRESS -- with register
liveness tracking, so a reassigned base does not misattribute later accesses.

Iteration 154 produced an offset histogram for the base 0x0214CCF8 by walking 8
instructions forward from each pc-relative load and matching any access using that
register. That scan did NOT track liveness, and it reported offsets up to +0xC40. Since
0x0214CCF8 sits only 0x28 bytes below ov6's load base, every offset >= 0x28 lands inside
another overlay's region -- so those figures could not be distinguished from register
reuse, and nothing beyond +0x00 could be claimed. This tool exists to settle that.

METHOD. Find every pc-relative load of the target value (ARM `ldr Rd,[pc,#imm]` and Thumb
`ldr Rd,[pc,#imm8]`). From each, walk forward recording load/store offsets that use the
loaded register as base, and STOP the walk as soon as the base could have changed.

CONSERVATIVE BY DESIGN. The walk stops on anything this decoder cannot prove is safe:
  * an instruction that writes the base register
  * any branch, call, or return (`bl`/`blx`/`bx`/`b`/`pop {..pc}`)
  * a call while the base is in r0-r3 or r12 -- AAPCS lets the callee clobber those
  * `ldm`/`pop` touching the base
  * any encoding not on the recognised list
This under-reports rather than over-reports. A missing offset is not evidence of absence;
a reported offset IS evidence of presence.

BLIND SPOTS, always printed:
  * a base rematerialised from a different register (`mov r5,r1`) is not followed
  * a base passed to a callee as an argument -- the callee's offsets are invisible here
  * a base stored to memory and reloaded later
  * conditional execution: an ARM predicated write stops the walk even if never taken
  * offsets reached via register-offset addressing (`ldr rD,[rN,rM]`) carry no immediate

Usage:
  base_offset_scan.py 0x0214CCF8
  base_offset_scan.py 0x0214CCF8 --regions ov7,ov10
  base_offset_scan.py --selftest
"""
import argparse
import collections
import glob
import json
import os
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AN = os.path.join(ROOT, 'jus_files', 'analysis')
MAX_WALK = 24


def regions():
    D = json.load(open(os.path.join(AN, 'functions.json')))
    return {r['provenance']: int(r['base'], 16) for r in D['regions']}


def image(prov):
    if prov == 'arm9':
        # Name the file. A `sorted(glob(...))[0]` here silently returned arm7.bin and the
        # scan reported zero hits for a base whose accessors were hand-read the wake
        # before -- caught by a positive control, iteration 155.
        p = os.path.join(ROOT, 'jus_files', 'arm9', 'arm9.bin')
        if not os.path.isfile(p):
            raise FileNotFoundError(p)
        return p
    n = int(prov[2:])
    for c in (f'ov{n:02d}.bin', f'ov{n}.bin'):
        p = os.path.join(ROOT, 'jus_files', 'overlays', c)
        if os.path.isfile(p):
            return p
    return None


class Img:
    def __init__(self, prov, base):
        self.prov, self.base = prov, base
        self.b = open(image(prov), 'rb').read()

    def w(self, a):
        o = a - self.base
        if o < 0 or o + 4 > len(self.b):
            raise IndexError
        return struct.unpack_from('<I', self.b, o)[0]

    def h(self, a):
        o = a - self.base
        if o < 0 or o + 2 > len(self.b):
            raise IndexError
        return struct.unpack_from('<H', self.b, o)[0]


def arm_step(v, base_reg):
    """(access_offset_or_None, is_store, stop) for one ARM word."""
    cond = v >> 28
    if cond == 0xF:
        return None, False, True
    op = (v >> 25) & 0x7
    # branch / bl
    if op == 0x5:
        return None, False, True
    # bx / blx register
    if (v & 0x0FFFFFF0) in (0x012FFF10, 0x012FFF30):
        return None, False, True
    # ldm / stm
    if op == 0x4:
        return None, False, True
    # load/store immediate offset
    if op == 0x2:
        rn, rt = (v >> 16) & 0xF, (v >> 12) & 0xF
        load = bool((v >> 20) & 1)
        up = bool((v >> 23) & 1)
        wb = bool((v >> 21) & 1)
        off = v & 0xFFF
        acc = off if (rn == base_reg and up and not wb) else None
        # writeback to base, or a load into the base, kills it
        stop = (rn == base_reg and wb) or (load and rt == base_reg)
        return acc, (not load), stop
    # load/store register offset -- no immediate to record
    if op == 0x3:
        rn, rt = (v >> 16) & 0xF, (v >> 12) & 0xF
        load = bool((v >> 20) & 1)
        return None, False, (load and rt == base_reg) or (rn == base_reg and ((v >> 21) & 1))
    # data processing immediate / register
    if op in (0x0, 0x1):
        # multiply and friends share op 0 -- be conservative
        if (v & 0x0FC000F0) == 0x00000090:
            return None, False, True
        opc = (v >> 21) & 0xF
        rd = (v >> 12) & 0xF
        setflags_only = opc in (0x8, 0x9, 0xA, 0xB)  # tst teq cmp cmn
        if setflags_only:
            return None, False, False
        return None, False, (rd == base_reg)
    return None, False, True


def thumb_step(v, base_reg):
    """(access_offset_or_None, is_store, stop) for one Thumb halfword."""
    top = v >> 12
    # ldr/str Rt,[Rn,#imm5*4]
    if top == 0x6:
        rn, rt = (v >> 3) & 7, v & 7
        off = ((v >> 6) & 0x1F) << 2
        load = v >= 0x6800
        acc = off if rn == base_reg else None
        return acc, (not load), (load and rt == base_reg)
    # strb/ldrb Rt,[Rn,#imm5]
    if top == 0x7:
        rn, rt = (v >> 3) & 7, v & 7
        off = (v >> 6) & 0x1F
        load = v >= 0x7800
        acc = off if rn == base_reg else None
        return acc, (not load), (load and rt == base_reg)
    # strh/ldrh Rt,[Rn,#imm5*2]
    if top == 0x8:
        rn, rt = (v >> 3) & 7, v & 7
        off = ((v >> 6) & 0x1F) << 1
        load = v >= 0x8800
        acc = off if rn == base_reg else None
        return acc, (not load), (load and rt == base_reg)
    # shifts / add-sub reg-imm (format 1-2): write Rd = bits 2-0
    if top in (0x0, 0x1):
        return None, False, ((v & 7) == base_reg)
    # mov/cmp/add/sub immediate (format 3): Rd = bits 10-8, cmp writes nothing
    if top in (0x2, 0x3):
        rd = (v >> 8) & 7
        is_cmp = (v >> 11) & 1 and top == 0x2
        return None, False, (not is_cmp and rd == base_reg)
    if top == 0x4:
        if v < 0x4400:                      # ALU ops, Rd = bits 2-0
            ops_no_write = (0x8, 0xA, 0xB)  # tst cmp cmn
            return None, False, (((v >> 6) & 0xF) not in ops_no_write and (v & 7) == base_reg)
        if v < 0x4800:                      # hi-reg ops / bx / blx
            return None, False, True
        return None, False, (((v >> 8) & 7) == base_reg)   # ldr Rd,[pc,#imm]
    # load/store register offset
    if top == 0x5:
        return None, False, (v >= 0x5800 and (v & 7) == base_reg)
    # sp-relative / pc-relative address forms
    if top in (0x9, 0xA):
        return None, False, (((v >> 8) & 7) == base_reg)
    if top == 0xB:
        return None, False, True            # push/pop/add-sp/cbz -- be conservative
    return None, False, True                # branches, BL halves, anything else


def scan(target, provs):
    per = {}
    for prov, base in sorted(regions().items()):
        if provs and prov not in provs:
            continue
        if prov not in provs and provs:
            continue
        try:
            im = Img(prov, base)
        except Exception:
            continue
        sites = []
        for o in range(0, len(im.b) - 3, 4):
            v = struct.unpack_from('<I', im.b, o)[0]
            if (v & 0x0FFF0000) != 0x059F0000:
                continue
            site = base + o
            try:
                if im.w(site + 8 + (v & 0xFFF)) != target:
                    continue
            except IndexError:
                continue
            sites.append((site, (v >> 12) & 0xF, 'arm'))
        for o in range(0, len(im.b) - 1, 2):
            hw = struct.unpack_from('<H', im.b, o)[0]
            if not (0x4800 <= hw <= 0x4FFF):
                continue
            site = base + o
            try:
                if im.w(((site + 4) & ~3) + ((hw & 0xFF) << 2)) != target:
                    continue
            except IndexError:
                continue
            sites.append((site, (hw >> 8) & 7, 'thumb'))
        offs = collections.Counter()
        stores = collections.Counter()
        detail = collections.defaultdict(list)
        walked = 0
        for site, rd, mode in sites:
            step, wide = (4, True) if mode == 'arm' else (2, False)
            a = site + step
            for _ in range(MAX_WALK):
                try:
                    v = im.w(a) if wide else im.h(a)
                except IndexError:
                    break
                acc, is_store, stop = (arm_step if wide else thumb_step)(v, rd)
                if acc is not None:
                    offs[acc] += 1
                    if is_store:
                        stores[acc] += 1
                        detail[acc].append(a)
                if stop:
                    break
                a += step
            walked += 1
        per[prov] = (len(sites), offs, stores, detail)
    return per


def selftest():
    """The two ov7 writers of 0x0214CCF8 +0x00, hand-read in iteration 154."""
    per = scan(0x0214CCF8, {'ov7'})
    n, offs, stores, detail = per['ov7']
    assert n > 0, 'selftest: no load sites found in ov7'
    assert stores[0] >= 2, f'selftest: expected >=2 stores to +0x00, got {stores[0]}'
    got = set(detail[0])
    for want in (0x021661C0, 0x02166372):
        assert want in got, f'selftest: known writer {want:#010x} not reported'
    # the naive scan claimed offsets this large; liveness tracking must not reach them
    assert 0xC40 not in offs, 'selftest: +0xC40 survived liveness tracking in ov7'
    # POSITIVE CONTROL. Without this the tool can report "nothing survived" for every
    # input and look like a clean negative. 0x0214CCF4's arm9 accessor cluster was
    # hand-read in iteration 153 and touches +0x00, +0x01 and +0x04.
    ctl = scan(0x0214CCF4, {'arm9'})['arm9']
    cn, coffs = ctl[0], ctl[1]
    assert cn > 0, 'selftest: positive control found no arm9 load sites (wrong image file?)'
    for want in (0x00, 0x01, 0x04):
        assert want in coffs, (f'selftest: positive control missing +{want:#x}; '
                               f'got {sorted(coffs)}')
    print(f'selftest OK: both hand-read writers of +0x00 found in ov7 '
          f'({stores[0]} stores), no offset >= 0xC40 survives, and the arm9 positive '
          f'control recovers +0x00/+0x01/+0x04 from {cn} sites')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('target', nargs='?', type=lambda s: int(s, 0))
    ap.add_argument('--regions')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.target is None:
        ap.error('need TARGET address or --selftest')
    provs = set(a.regions.split(',')) if a.regions else set(regions())
    per = scan(a.target, provs)
    print(f'# base-offset scan for 0x{a.target:08X}, liveness-tracked, '
          f'walk cap {MAX_WALK} instructions')
    for prov, (n, offs, stores, detail) in per.items():
        if not n:
            continue
        print(f'\n{prov}: {n} pc-relative load site(s)')
        if not offs:
            print('    no offsets survived liveness tracking')
        for o in sorted(offs):
            mark = f'  stores at {[hex(x) for x in detail[o][:4]]}' if stores[o] else ''
            print(f'    +0x{o:02X}: {offs[o]} access(es), {stores[o]} store(s){mark}')
    print('\n# BLIND SPOTS: base rematerialised from another register, base passed to a '
          'callee,\n# base spilled and reloaded, ARM predicated writes (walk stops), '
          'register-offset\n# addressing (no immediate). Missing offsets are NOT evidence '
          'of absence.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
