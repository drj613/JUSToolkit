#!/usr/bin/env python3
"""Scan for POOL-LOADED index and mask registers -- the residual recall gap named at P195.

Two classes, both invisible to every scanner built so far:

  A. index pool-loaded:  ldr rN,[pc,#k] where *pool == off (or off/4), then
                         str rX,[rBase, rN, lsl #s]        -- no offset in the store
  B. mask pool-loaded:   ldr rN,[pc,#k] where *pool == mask, then
                         orr rX,rY,rN  ...  str rX,[rBase,#field]

Class B is why this exists: the bit-11 damage-pending mask (0x800) cannot be a single
Thumb data-processing immediate, so a Thumb/ARM setter would pool-load it.

Scope: arm9 AND every overlay, same regions() as regoff_store_scan.py.
"""
import json, os, struct, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

def regions():
    out = [("arm9", os.path.join(ROOT, "jus_files/arm9/arm9.bin"), 0x02000000)]
    ov = json.load(open(os.path.join(ROOT, "jus_files/overlays/overlays.json")))
    for o in ov:
        out.append((f"ov{o['id']:02d}",
                    os.path.join(ROOT, "jus_files/overlays", o["file"]),
                    o["ram_address"]))
    return out

def arm_ldr_lit(w):
    """ldr rD,[pc,#imm] -> (rD, signed_imm) or None. cond must be AL."""
    if (w >> 28) != 0xE: return None
    if (w & 0x0F7F0000) != 0x051F0000: return None
    rd = (w >> 12) & 0xF
    imm = w & 0xFFF
    up = (w >> 23) & 1
    return (rd, imm if up else -imm)

def arm_str_reg(w, rm):
    """str rX,[rN, rm, lsl #s] -- word store, register offset, immediate LSL."""
    if (w >> 28) != 0xE: return None
    if (w & 0x0E500010) != 0x06000000: return None
    if ((w >> 5) & 3) != 0: return None
    if (w & 0xF) != rm: return None
    return (w >> 7) & 0x1F

def arm_orr_reg(w, rm):
    """orr rD,rN,rm (register form, immediate shift) -> rD or None."""
    if (w >> 28) != 0xE: return None
    if (w & 0x0FE00010) != 0x01800000: return None
    if (w & 0xF) != rm: return None
    return (w >> 12) & 0xF

def arm_str_imm(w, rd):
    """str rd,[rN,#imm] -> (rN, imm) or None."""
    if (w >> 28) != 0xE: return None
    if (w & 0x0E500000) != 0x04000000: return None
    if ((w >> 12) & 0xF) != rd: return None
    return ((w >> 16) & 0xF, w & 0xFFF)

def selftest():
    ok = True
    def chk(cond, msg):
        nonlocal ok
        if not cond: print(f"# SELFTEST FAIL: {msg}"); ok = False
    chk(arm_ldr_lit(0xE59F1024) == (1, 0x24), "ldr r1,[pc,#0x24] not matched")
    chk(arm_ldr_lit(0xE51F1024) == (1, -0x24), "ldr with U=0 not matched")
    chk(arm_ldr_lit(0xE5841024) is None, "matched a non-pc-relative ldr")
    chk(arm_str_reg(0xE7841102, 2) == 2, "str r1,[r4,r2,lsl #2] not matched")
    chk(arm_str_reg(0xE7941102, 2) is None, "matched a LOAD as a store")
    chk(arm_str_reg(0xE7841102, 3) is None, "matched the wrong index register")
    chk(arm_orr_reg(0xE1810002, 2) == 0, "orr r0,r1,r2 not matched")
    chk(arm_orr_reg(0xE1810002, 5) is None, "orr matched the wrong source register")
    chk(arm_str_imm(0xE5840040, 0) == (4, 0x40), "str r0,[r4,#0x40] not matched")
    chk(arm_str_imm(0xE5840040, 1) is None, "str_imm matched the wrong data register")
    print(f"# matcher selftest: {'PASS' if ok else 'FAIL'}")
    return ok

def scan(path, base, wanted_idx, wanted_mask, field, window=10, wanted_direct=None):
    d = open(path, "rb").read()
    hits = []
    n = len(d)
    for o in range(0, n - 4, 4):
        w = struct.unpack_from("<I", d, o)[0]
        lit = arm_ldr_lit(w)
        if not lit: continue
        rd, off = lit
        tgt = o + 8 + off
        if tgt < 0 or tgt + 4 > n: continue
        val = struct.unpack_from("<I", d, tgt & ~3)[0]
        klass = None
        if val in wanted_idx: klass = "INDEX"
        elif val in wanted_mask: klass = "MASK"
        elif wanted_direct and val in wanted_direct: klass = "DIRECT"
        if not klass: continue
        ctx = []
        for k in range(1, window + 1):
            if o + k*4 + 4 > n: break
            m = struct.unpack_from("<I", d, o + k*4)[0]
            if klass == "INDEX":
                s = arm_str_reg(m, rd)
                if s is not None:
                    ctx.append((k, f"str [rN, r{rd}, lsl #{s}]"))
            elif klass == "DIRECT":
                si = arm_str_imm(m, rd)
                if si and (field is None or si[1] == field):
                    ctx.append((k, f"str r{rd},[r{si[0]},#{si[1]:#x}] -- pool value stored straight to the field"))
            else:
                dst = arm_orr_reg(m, rd)
                if dst is not None:
                    for j in range(k+1, min(k+1+window, window*2)):
                        if o + j*4 + 4 > n: break
                        m2 = struct.unpack_from("<I", d, o + j*4)[0]
                        si = arm_str_imm(m2, dst)
                        if si and (field is None or si[1] == field):
                            ctx.append((k, f"orr r{dst},..,r{rd} then str [r{si[0]},#{si[1]:#x}]"))
        if ctx:
            hits.append((klass, base + o, f"ldr r{rd},[pc] = {val:#x}", ctx))
    return hits

def main():
    if not selftest():
        print("# ABORTING: matcher failed its own control"); return
    off   = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0xE8
    mask  = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x800
    field = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x40
    idx = {off} | ({off // 4} if off % 4 == 0 else set())
    print(f"# pool-loaded INDEX for +{off:#x} (values {sorted(hex(v) for v in idx)}) "
          f"| pool-loaded MASK {mask:#x} feeding a store to +{field:#x}\n")
    # SCAN-LEVEL CONTROL WITH A KNOWN ANSWER: arm9 0x0207CB28 pool-loads 0x0207D9A0
    # and 0x0207CB38 stores it to +0x50. If the scan cannot find that, every null below
    # is worthless. This is a control whose expected hit is already established.
    ctrl = 0
    for name, path, base in regions():
        if name != "arm9" or not os.path.isfile(path): continue
        for klass, addr, txt, ctx in scan(path, base, set(), set(), 0x50,
                                          wanted_direct={0x0207D9A0}):
            if addr == 0x0207CB28: ctrl += 1
    print(f"# scan-level control (0x0207CB28 -> 0x0207D9A0 -> +0x50): "
          f"{'FOUND' if ctrl else 'NOT FOUND -- nulls below are worthless'}\n")
    if not ctrl:
        print("# ABORTING: scan-level control failed"); return
    tot = 0
    for name, path, base in regions():
        if not os.path.isfile(path): continue
        for klass, addr, txt, ctx in scan(path, base, idx, {mask}, field):
            tot += 1
            print(f"{addr:#010x} ({name}) {klass}: {txt}")
            for k, why in ctx:
                print(f"      +{k} instr: {why}")
    print(f"\n# {tot} candidate(s) across arm9 and all overlays")

if __name__ == "__main__":
    main()
