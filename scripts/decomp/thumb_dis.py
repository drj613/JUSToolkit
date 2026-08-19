#!/usr/bin/env python3
"""Thumb-16 (+ BL/BLX pair) disassembler for the JUS binaries.

Why this exists: `jus_files/analysis/disasm/ov6.txt` decodes the whole battle
overlay as ARM. Large Thumb regions therefore come out as nonsense —
`0x02151300` reads as `stmvs sb, {r0, fp, sp, lr}` — and because ARM decoding
steps 4 bytes at a time, odd-halfword addresses are absent from the listing
entirely. Four of the five Thumb callers of the HP-apply function do not appear
in it at all.

That listing is what every prior hitbox-priority round searched, which is the
likely reason `Battle-Engine-Map.md` records the damage-formula site as "unfound
across 3 rounds" and no clash-resolution comparison found "anywhere in
ov0/ov3/ov4/ov5/ov6".

Usage:
    python3 scripts/decomp/thumb_dis.py ov6 0x02151380 0x02151420
    python3 scripts/decomp/thumb_dis.py arm9 0x02077C50 0x02077C80

Covers the Thumb-16 encodings ARMv4T actually emits, plus the 32-bit BL/BLX
pair. Unknown halfwords print as `.hw 0xXXXX` rather than guessing.

Read-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ARM9 = Path("jus_files/arm9/arm9.bin")
ARM9_BASE = 0x02000000
OVERLAY_DIR = Path("jus_files/overlays")

COND = ["eq", "ne", "cs", "cc", "mi", "pl", "vs", "vc",
        "hi", "ls", "ge", "lt", "gt", "le", "", "nv"]
ALU = ["and", "eor", "lsl", "lsr", "asr", "adc", "sbc", "ror",
       "tst", "neg", "cmp", "cmn", "orr", "mul", "bic", "mvn"]


def load(which: str) -> tuple[bytes, int]:
    if which == "arm9":
        return ARM9.read_bytes(), ARM9_BASE
    man = json.loads((OVERLAY_DIR / "overlays.json").read_text())
    num = int(which.replace("ov", ""))
    for e in man:
        if e["id"] == num:
            p = OVERLAY_DIR / f"ov{num:02d}.bin"
            return p.read_bytes(), e["ram_address"]
    raise SystemExit(f"unknown binary {which!r}")


def r(n: int) -> str:
    return {13: "sp", 14: "lr", 15: "pc"}.get(n, f"r{n}")


def dis1(hw: int, hw2: int | None, addr: int) -> tuple[str, int]:
    """Return (text, size_in_bytes)."""
    t = hw >> 12

    # 000xx — shift by immediate / add-sub register
    if hw >> 13 == 0b000:
        op = (hw >> 11) & 3
        if op != 3:
            imm, rs, rd = (hw >> 6) & 0x1F, (hw >> 3) & 7, hw & 7
            return f"{['lsl','lsr','asr'][op]} {r(rd)}, {r(rs)}, #{imm}", 2
        sub, is_imm = (hw >> 9) & 1, (hw >> 10) & 1
        rn, rs, rd = (hw >> 6) & 7, (hw >> 3) & 7, hw & 7
        opn = "sub" if sub else "add"
        src = f"#{rn}" if is_imm else r(rn)
        return f"{opn}s {r(rd)}, {r(rs)}, {src}", 2

    # 001xx — mov/cmp/add/sub immediate
    if hw >> 13 == 0b001:
        op, rd, imm = (hw >> 11) & 3, (hw >> 8) & 7, hw & 0xFF
        return f"{['mov','cmp','add','sub'][op]} {r(rd)}, #0x{imm:X}", 2

    # 010000 — ALU register
    if hw >> 10 == 0b010000:
        op, rs, rd = (hw >> 6) & 0xF, (hw >> 3) & 7, hw & 7
        return f"{ALU[op]} {r(rd)}, {r(rs)}", 2

    # 010001 — hi register ops / BX / BLX
    if hw >> 10 == 0b010001:
        op = (hw >> 8) & 3
        h1, h2 = (hw >> 7) & 1, (hw >> 6) & 1
        rs, rd = ((hw >> 3) & 7) | (h2 << 3), (hw & 7) | (h1 << 3)
        if op == 3:
            return f"{'blx' if h1 else 'bx'} {r(rs)}", 2
        return f"{['add','cmp','mov'][op]} {r(rd)}, {r(rs)}", 2

    # 01001 — LDR literal
    if hw >> 11 == 0b01001:
        rd, imm = (hw >> 8) & 7, (hw & 0xFF) * 4
        pool = ((addr + 4) & ~3) + imm
        return f"ldr {r(rd)}, [pc, #0x{imm:X}]   ; = 0x{pool:08X}", 2

    # 0101 — load/store register offset
    if hw >> 12 == 0b0101:
        if (hw >> 9) & 1:
            op = (hw >> 10) & 3
            names = ["strh", "ldrsb", "ldrh", "ldrsh"]
            rb, ro, rd = (hw >> 3) & 7, (hw >> 6) & 7, hw & 7
            return f"{names[op]} {r(rd)}, [{r(rb)}, {r(ro)}]", 2
        l, b = (hw >> 11) & 1, (hw >> 10) & 1
        rb, ro, rd = (hw >> 3) & 7, (hw >> 6) & 7, hw & 7
        return f"{'ldr' if l else 'str'}{'b' if b else ''} {r(rd)}, [{r(rb)}, {r(ro)}]", 2

    # 011 — load/store word/byte immediate
    if hw >> 13 == 0b011:
        b, l = (hw >> 12) & 1, (hw >> 11) & 1
        off, rb, rd = (hw >> 6) & 0x1F, (hw >> 3) & 7, hw & 7
        off = off if b else off * 4
        return f"{'ldr' if l else 'str'}{'b' if b else ''} {r(rd)}, [{r(rb)}, #0x{off:X}]", 2

    # 1000 — load/store halfword immediate
    if hw >> 12 == 0b1000:
        l, off, rb, rd = (hw >> 11) & 1, ((hw >> 6) & 0x1F) * 2, (hw >> 3) & 7, hw & 7
        return f"{'ldrh' if l else 'strh'} {r(rd)}, [{r(rb)}, #0x{off:X}]", 2

    # 1001 — SP-relative load/store
    if hw >> 12 == 0b1001:
        l, rd, off = (hw >> 11) & 1, (hw >> 8) & 7, (hw & 0xFF) * 4
        return f"{'ldr' if l else 'str'} {r(rd)}, [sp, #0x{off:X}]", 2

    # 1010 — ADD Rd, PC/SP, imm
    if hw >> 12 == 0b1010:
        sp, rd, off = (hw >> 11) & 1, (hw >> 8) & 7, (hw & 0xFF) * 4
        return f"add {r(rd)}, {'sp' if sp else 'pc'}, #0x{off:X}", 2

    # 1011 0000 — ADD/SUB SP
    if hw >> 8 == 0b10110000:
        sub, off = (hw >> 7) & 1, (hw & 0x7F) * 4
        return f"{'sub' if sub else 'add'} sp, #0x{off:X}", 2

    # 1011 x10x — PUSH/POP
    if (hw >> 12) == 0b1011 and ((hw >> 9) & 3) == 0b10:
        l, rl_bit, rlist = (hw >> 11) & 1, (hw >> 8) & 1, hw & 0xFF
        regs = [r(i) for i in range(8) if rlist & (1 << i)]
        if rl_bit:
            regs.append("pc" if l else "lr")
        return f"{'pop' if l else 'push'} {{{', '.join(regs)}}}", 2

    # 1100 — LDMIA/STMIA
    if hw >> 12 == 0b1100:
        l, rb, rlist = (hw >> 11) & 1, (hw >> 8) & 7, hw & 0xFF
        regs = [r(i) for i in range(8) if rlist & (1 << i)]
        return f"{'ldmia' if l else 'stmia'} {r(rb)}!, {{{', '.join(regs)}}}", 2

    # 1101 — conditional branch / SVC
    if hw >> 12 == 0b1101:
        c = (hw >> 8) & 0xF
        if c == 0xF:
            return f"svc #0x{hw & 0xFF:X}", 2
        off = hw & 0xFF
        if off & 0x80:
            off -= 0x100
        return f"b{COND[c]} 0x{addr + 4 + off * 2:08X}", 2

    # 11100 — unconditional branch
    if hw >> 11 == 0b11100:
        off = hw & 0x7FF
        if off & 0x400:
            off -= 0x800
        return f"b 0x{addr + 4 + off * 2:08X}", 2

    # 1111 0 / BL-BLX pair
    if 0xF000 <= hw <= 0xF7FF and hw2 is not None:
        blx = 0xE800 <= hw2 <= 0xEFFF
        bl = 0xF800 <= hw2 <= 0xFFFF
        if bl or blx:
            off = ((hw & 0x7FF) << 12) | ((hw2 & 0x7FF) << 1)
            if off & 0x400000:
                off -= 0x800000
            tgt = addr + 4 + off
            if blx:
                tgt &= ~3
            return f"{'blx' if blx else 'bl'} 0x{tgt:08X}", 4

    return f".hw 0x{hw:04X}", 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("binary", help="arm9 or ovN")
    ap.add_argument("start", help="start address, hex")
    ap.add_argument("end", help="end address, hex")
    ap.add_argument("--mark", nargs="*", default=[], help="addresses to flag")
    args = ap.parse_args()

    buf, base = load(args.binary)
    start, end = int(args.start, 16), int(args.end, 16)
    marks = {int(m, 16) for m in args.mark}

    a = start
    while a < end:
        o = a - base
        if o < 0 or o + 2 > len(buf):
            break
        hw = int.from_bytes(buf[o:o + 2], "little")
        hw2 = int.from_bytes(buf[o + 2:o + 4], "little") if o + 4 <= len(buf) else None
        text, size = dis1(hw, hw2, a)
        flag = "   <<<" if a in marks else ""
        print(f"0x{a:08X}: {text}{flag}")
        a += size
    return 0


if __name__ == "__main__":
    sys.exit(main())
