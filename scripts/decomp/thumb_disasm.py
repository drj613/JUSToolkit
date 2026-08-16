#!/usr/bin/env python3
"""A minimal Thumb disassembler.

`query.py disasm` decodes ARM only. Iterations 95-96 found that ov6 contains
uncatalogued Thumb code -- including the sole caller of `Battle_CharaCreate` --
so reading it required something. This covers the ARMv4T encodings that actually
appear in this ROM's Thumb regions; anything else prints as `.hw <value>` rather
than being guessed at.

Usage:
  thumb_disasm.py ov6 0x0214D600 40
  thumb_disasm.py --selftest
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import struct_fields as SF                                        # noqa: E402

R = [f'r{i}' for i in range(13)] + ['sp', 'lr', 'pc']
COND = ['eq', 'ne', 'cs', 'cc', 'mi', 'pl', 'vs', 'vc',
        'hi', 'ls', 'ge', 'lt', 'gt', 'le', '', 'nv']


def reglist(mask, extra=None):
    rs = [R[i] for i in range(8) if mask & (1 << i)]
    if extra:
        rs.append(extra)
    return '{' + ', '.join(rs) + '}'


def decode(h, addr, nxt=None):
    """(text, size_in_halfwords). `nxt` allows the 32-bit BL/BLX pair."""
    # long branch with link -- two halfwords
    if 0xF000 <= h <= 0xF7FF and nxt is not None:
        if 0xF800 <= nxt <= 0xFFFF or 0xE800 <= nxt <= 0xEFFF:
            off = ((h & 0x7FF) << 12) | ((nxt & 0x7FF) << 1)
            if off & 0x400000:
                off -= 0x800000
            tgt = addr + 4 + off
            kind = 'bl'
            if 0xE800 <= nxt <= 0xEFFF:
                kind, tgt = 'blx', tgt & ~3
            return f'{kind} #{tgt:#010x}', 2
    top = h >> 12
    if h == 0x46C0:
        return 'nop', 1
    if (h >> 11) == 0b00000 and (h & 0x07C0):
        return f'lsl {R[h&7]}, {R[(h>>3)&7]}, #{(h>>6)&0x1f}', 1
    if (h >> 11) == 0b00001:
        return f'lsr {R[h&7]}, {R[(h>>3)&7]}, #{(h>>6)&0x1f}', 1
    if (h >> 11) == 0b00010:
        return f'asr {R[h&7]}, {R[(h>>3)&7]}, #{(h>>6)&0x1f}', 1
    if (h >> 11) == 0b00011:
        op = 'sub' if h & 0x200 else 'add'
        if h & 0x400:
            return f'{op} {R[h&7]}, {R[(h>>3)&7]}, #{(h>>6)&7}', 1
        return f'{op} {R[h&7]}, {R[(h>>3)&7]}, {R[(h>>6)&7]}', 1
    if top == 0b0010:
        return f'mov {R[(h>>8)&7]}, #{h&0xff:#x}', 1
    if top == 0b0011:
        return f'{"sub" if h & 0x800 else "add"} {R[(h>>8)&7]}, #{h&0xff:#x}', 1
    if top == 0b0010 | 1:
        return f'cmp {R[(h>>8)&7]}, #{h&0xff:#x}', 1
    if (h >> 11) == 0b00101:
        return f'cmp {R[(h>>8)&7]}, #{h&0xff:#x}', 1
    if (h >> 10) == 0b010000:
        ops = ['and', 'eor', 'lsl', 'lsr', 'asr', 'adc', 'sbc', 'ror',
               'tst', 'neg', 'cmp', 'cmn', 'orr', 'mul', 'bic', 'mvn']
        return f'{ops[(h>>6)&0xf]} {R[h&7]}, {R[(h>>3)&7]}', 1
    if (h >> 10) == 0b010001:                       # hi-register ops / bx
        op = (h >> 8) & 3
        rd = (h & 7) | ((h >> 4) & 8)
        rm = (h >> 3) & 0xF
        if op == 3:
            return f'{"blx" if h & 0x80 else "bx"} {R[rm]}', 1
        return f'{["add","cmp","mov"][op]} {R[rd]}, {R[rm]}', 1
    if (h >> 11) == 0b01001:
        return f'ldr {R[(h>>8)&7]}, [pc, #{(h&0xff)*4:#x}]  ; = {((addr+4) & ~3) + (h&0xff)*4:#010x}', 1
    if (h >> 12) == 0b0101:
        ops = ['str', 'strh', 'strb', 'ldrsb', 'ldr', 'ldrh', 'ldrb', 'ldrsh']
        return f'{ops[(h>>9)&7]} {R[h&7]}, [{R[(h>>3)&7]}, {R[(h>>6)&7]}]', 1
    if (h >> 13) == 0b011:
        b = (h >> 12) & 1
        l = (h >> 11) & 1
        off = ((h >> 6) & 0x1f) * (1 if b else 4)
        return f'{"ldr" if l else "str"}{"b" if b else ""} {R[h&7]}, [{R[(h>>3)&7]}, #{off:#x}]', 1
    if (h >> 12) == 0b1000:
        return (f'{"ldrh" if h & 0x800 else "strh"} {R[h&7]}, '
                f'[{R[(h>>3)&7]}, #{((h>>6)&0x1f)*2:#x}]'), 1
    if (h >> 12) == 0b1001:
        return f'{"ldr" if h & 0x800 else "str"} {R[(h>>8)&7]}, [sp, #{(h&0xff)*4:#x}]', 1
    if (h >> 12) == 0b1010:
        src = 'sp' if h & 0x800 else 'pc'
        return f'add {R[(h>>8)&7]}, {src}, #{(h&0xff)*4:#x}', 1
    if (h >> 8) == 0b10110000:
        return f'{"sub" if h & 0x80 else "add"} sp, #{(h&0x7f)*4:#x}', 1
    if (h >> 9) == 0b1011010:
        return f'push {reglist(h & 0xff, "lr" if h & 0x100 else None)}', 1
    if (h >> 9) == 0b1011110:
        return f'pop {reglist(h & 0xff, "pc" if h & 0x100 else None)}', 1
    if (h >> 12) == 0b1100:
        op = 'ldmia' if h & 0x800 else 'stmia'
        return f'{op} {R[(h>>8)&7]}!, {reglist(h & 0xff)}', 1
    if (h >> 12) == 0b1101:
        c = (h >> 8) & 0xF
        if c == 0xF:
            return f'swi #{h&0xff:#x}', 1
        off = h & 0xff
        if off & 0x80:
            off -= 0x100
        return f'b{COND[c]} #{addr + 4 + off*2:#010x}', 1
    if (h >> 11) == 0b11100:
        off = h & 0x7ff
        if off & 0x400:
            off -= 0x800
        return f'b #{addr + 4 + off*2:#010x}', 1
    return f'.hw {h:#06x}', 1


def disasm(region, start, count):
    words, base = SF.load(region)
    hs = []
    for x in words:
        hs.append(x & 0xFFFF)
        hs.append((x >> 16) & 0xFFFF)
    i = (start - base) // 2
    out = []
    n = 0
    while n < count and i < len(hs) - 1:
        addr = base + i * 2
        text, size = decode(hs[i], addr, hs[i + 1] if i + 1 < len(hs) else None)
        raw = f'{hs[i]:04x}' + (f' {hs[i+1]:04x}' if size == 2 else '     ')
        out.append(f'{addr:#010x}: {raw}  {text}')
        i += size
        n += 1
    return out


def selftest():
    """The hand-verified call sequence around iteration 95's anchor."""
    got = '\n'.join(disasm('ov6', 0x0214D658, 8))
    for want in ('add r1, sp, #0x48', 'blx #0x02156a38', 'nop'):
        assert want in got, f'selftest: missing {want!r} in\n{got}'
    print('selftest OK: the 0x0214D65E call site decodes as expected')
    print(got)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('region', nargs='?')
    ap.add_argument('start', nargs='?', type=lambda s: int(s, 0))
    ap.add_argument('count', nargs='?', type=int, default=32)
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.region or a.start is None:
        ap.error('need REGION and START, or --selftest')
    print('\n'.join(disasm(a.region, a.start, a.count)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
