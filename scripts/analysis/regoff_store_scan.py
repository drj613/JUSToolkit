#!/usr/bin/env python3
"""Find stores to a struct offset that `query.py search-imm` cannot see.

search-imm only matches load/store instructions whose offset is an immediate in
the instruction itself. Three shapes are invisible to it:

  1. ARM  `add rD, rN, #off` then `str rX, [rD]`      (split offset)
  2. Thumb `add rN, #off`     then `str rX, [rN]`      (split offset; and for
     off > 124 a Thumb word store CANNOT use an immediate at all, so any Thumb
     writer of a large offset must take this route or shape 3)
  3. either mode: `mov rM, #off` then `str rX, [rN, rM]` (register offset)

Read-only. Reports candidates with context; it does not resolve dataflow, so a
hit is a candidate to disassemble, not a confirmed writer.
"""
import json, struct, sys, os

ROOT = "/Users/djdjo/Documents/mine/JUSToolkit"

def regions():
    out = [("arm9", os.path.join(ROOT, "jus_files/arm9/arm9.bin"), 0x02000000)]
    ov = json.load(open(os.path.join(ROOT, "jus_files/overlays/overlays.json")))
    for o in ov:
        out.append((f"ov{o['id']:02d}",
                    os.path.join(ROOT, "jus_files/overlays", o["file"]),
                    o["ram_address"]))
    return out

def arm_add_imm(w, off):
    """add rD, rN, #off with rotate 0."""
    return (w & 0x0FFF00FFF) == 0x02800000 | off if False else \
           ((w & 0x0FF00FFF) == (0x02800000 | off) and (w >> 28) == 0xE)

def arm_mov_imm(w, val):
    """mov rD, #val with rotate 0, unconditional."""
    return (w >> 28) == 0xE and (w & 0x0FFF0000) == 0x03A00000 and (w & 0xFFF) == val

def arm_str_shifted(w, ridx, shift_imm):
    """str rX, [rN, rIdx, lsl #shift_imm] -- word store, immediate LSL shift.

    ARM register-offset store: cond 011 P U B W L | Rn | Rd | shift_imm(5) sh(2) 0 | Rm
    We require B=0 (word), L=0 (store), bit4=0 (immediate shift), sh=00 (LSL).
    """
    if (w >> 28) != 0xE:
        return False
    if (w & 0x0E500010) != 0x06000000:
        return False
    if ((w >> 5) & 3) != 0:
        return False
    if ((w >> 7) & 0x1F) != shift_imm:
        return False
    return (w & 0xF) == ridx

def scan_shifted(path, base, off, window=8):
    """The class P181 named as a genuine gap: str rX,[rBase, rIdx, lsl #2] where
    rIdx holds off/4. search-imm cannot see it (no offset in the store) and the
    add/mov scan cannot either (the constant is off/4, not off)."""
    d = open(path, "rb").read()
    hits = []
    cands = []
    if off % 4 == 0:
        cands.append((off // 4, 2))   # lsl #2 with the index scaled
    cands.append((off, 0))            # plain register offset, index holds off
    for idx_val, sh in cands:
        if idx_val > 0xFFF:
            continue
        for o in range(0, len(d) - 4, 4):
            w = struct.unpack_from("<I", d, o)[0]
            if not arm_mov_imm(w, idx_val):
                continue
            rd = (w >> 12) & 0xF
            ctx = []
            for k in range(1, window + 1):
                if o + k * 4 + 4 > len(d):
                    break
                n = struct.unpack_from("<I", d, o + k * 4)[0]
                if arm_str_shifted(n, rd, sh):
                    ctx.append((k, f"ARM str [rN, r{rd}, lsl #{sh}]"))
            if ctx:
                hits.append(("ARM shifted", base + o,
                             f"mov r{rd}, #{idx_val:#x} (index for +{off:#x}, lsl #{sh})", ctx))
    return hits

def selftest_shifted():
    """Control on the MATCHER itself, before trusting any scan result.
    Hand-encode str r1,[r4, r2, lsl #2] = 0xE7841102 and mov r2,#58 = 0xE3A0203A."""
    ok = True
    if not arm_str_shifted(0xE7841102, 2, 2):
        print("# SELFTEST FAIL: did not match str r1,[r4, r2, lsl #2]"); ok = False
    if arm_str_shifted(0xE7941102, 2, 2):
        print("# SELFTEST FAIL: matched a LOAD (bit20 set)"); ok = False
    if arm_str_shifted(0xE7841102, 3, 2):
        print("# SELFTEST FAIL: matched the wrong index register"); ok = False
    if not arm_mov_imm(0xE3A0203A, 58):
        print("# SELFTEST FAIL: did not match mov r2,#58"); ok = False
    print(f"# matcher selftest: {'PASS' if ok else 'FAIL'}")
    return ok

def scan(path, base, off, window=8):
    d = open(path, "rb").read()
    hits = []
    # --- ARM: add rD, rN, #off ---
    for o in range(0, len(d) - 4, 4):
        w = struct.unpack_from("<I", d, o)[0]
        if arm_add_imm(w, off):
            rn, rd = (w >> 16) & 0xF, (w >> 12) & 0xF
            ctx = []
            for k in range(1, window + 1):
                if o + k * 4 + 4 > len(d):
                    break
                n = struct.unpack_from("<I", d, o + k * 4)[0]
                # str rX, [rd, #imm]  (any immediate, incl. 0)
                if (n >> 28) == 0xE and (n & 0x0E500000) == 0x04000000 \
                   and ((n >> 16) & 0xF) == rd and not (n & 0x00100000):
                    ctx.append((k, "ARM str via that base"))
            hits.append(("ARM add", base + o, f"add r{rd}, r{rn}, #{off:#x}", ctx))
    # --- Thumb: add rN,#off / mov rN,#off, then a store ---
    for o in range(0, len(d) - 2, 2):
        h = int.from_bytes(d[o:o+2], "little")
        kind = None
        if 0x3000 <= h <= 0x37FF and (h & 0xFF) == off: kind = "add"
        if 0x2000 <= h <= 0x27FF and (h & 0xFF) == off: kind = "mov"
        if not kind:
            continue
        rn = (h >> 8) & 7
        ctx = []
        for k in range(1, window + 1):
            if o + k * 2 + 2 > len(d):
                break
            n = int.from_bytes(d[o + k*2:o + k*2 + 2], "little")
            if 0x6000 <= n <= 0x67FF and ((n >> 3) & 7) == rn:
                ctx.append((k, "Thumb str [that base, #imm]"))
            if 0x5000 <= n <= 0x51FF and (((n >> 6) & 7) == rn or ((n >> 3) & 7) == rn):
                ctx.append((k, "Thumb str reg-offset using it"))
        if ctx:
            hits.append((f"Thumb {kind}", base + o, f"{kind} r{rn}, #{off:#x}", ctx))
    return hits

def load_modes():
    """addr -> mode intervals per region, from functions.json."""
    import bisect
    fj = json.load(open(os.path.join(ROOT, "jus_files/analysis/functions.json")))
    per = {}
    for f in fj["functions"]:
        per.setdefault(f["provenance"], []).append(
            (int(f["addr"], 16), int(f["addr"], 16) + f["size"], f["mode"]))
    for k in per:
        per[k].sort()
    return per

def mode_at(modes, region, addr):
    """Return 'arm'/'thumb'/None for the function containing addr in region."""
    import bisect
    rows = modes.get(region)
    if not rows:
        return None
    starts = [r[0] for r in rows]
    i = bisect.bisect_right(starts, addr) - 1
    if i < 0:
        return None
    lo, hi, m = rows[i]
    return m if lo <= addr < hi else None

def main():
    off = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0xE8
    print(f"# scanning for split/register-offset stores to +{off:#x}\n")
    if not selftest_shifted():
        print("# ABORTING: the matcher failed its own control")
        return
    modes = load_modes()
    total = dropped = unknown = 0
    for name, path, base in regions():
        if not os.path.isfile(path):
            continue
        for kind, addr, txt, ctx in scan(path, base, off) + scan_shifted(path, base, off):
            if not ctx:
                continue          # only report ones with a plausible store nearby
            # MODE FILTER: ARM bytes can coincidentally match Thumb patterns and
            # vice versa. Drop any hit whose containing function is the other mode.
            m = mode_at(modes, name, addr)
            want = "thumb" if kind.startswith("Thumb") else "arm"
            if m is None:
                unknown += 1
                txt += "   [containing function unknown -- unverified mode]"
            elif m != want:
                dropped += 1
                continue
            total += 1
            print(f"{addr:#010x} ({name}) {kind}: {txt}")
            for k, why in ctx:
                print(f"      +{k} instr: {why}")
    print(f"\n# {total} candidate(s) with a store within 8 instructions"
          f"; {dropped} dropped by the mode filter; {unknown} in unbinned code")

if __name__ == "__main__":
    main()
