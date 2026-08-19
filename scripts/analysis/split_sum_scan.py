#!/usr/bin/env python3
"""Close the COMPUTED-OFFSET sliver: a writer that holds an interior pointer.

  add rD, rN, #K        (or Thumb adds rD,#K)
  ...
  str rV, [rD, #S]      where K + S == TARGET

So TARGET never appears as an immediate, a pool word, or a store offset. This is the
last named materialisation route for the +0x134 write after P195/P196/P197 closed
immediate-offset, split-offset, shifted-register, pool-loaded-index and
offset-as-argument.

Scope: arm9 AND every overlay.
"""
import json, os, struct, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

def regions():
    out = [("arm9", os.path.join(ROOT, "jus_files/arm9/arm9.bin"), 0x02000000)]
    for o in json.load(open(os.path.join(ROOT, "jus_files/overlays/overlays.json"))):
        out.append((f"ov{o['id']:02d}",
                    os.path.join(ROOT, "jus_files/overlays", o["file"]),
                    o["ram_address"]))
    return out

def arm_add_imm(w):
    """add rD, rN, #imm (rotate 0, AL) -> (rD, rN, imm) or None."""
    if (w >> 28) != 0xE: return None
    if (w & 0x0FF00000) != 0x02800000: return None
    return ((w >> 12) & 0xF, (w >> 16) & 0xF, w & 0xFFF)

def arm_str_imm_on(w, rn):
    """str rV,[rn,#imm] word store, positive offset -> imm or None."""
    if (w >> 28) != 0xE: return None
    if (w & 0x0E500000) != 0x04000000: return None
    if not (w & 0x00800000): return None          # U bit: require +offset
    if ((w >> 16) & 0xF) != rn: return None
    return w & 0xFFF

def thumb_add_imm(h):
    """adds rD,#imm8 -> (rD, imm) or None."""
    if (h & 0xF800) != 0x3000: return None
    return ((h >> 8) & 7, h & 0xFF)

def thumb_str_on(h, rn):
    """str rV,[rn,#imm5*4] -> byte offset or None."""
    if (h & 0xF800) != 0x6000: return None
    if ((h >> 3) & 7) != rn: return None
    return ((h >> 6) & 0x1F) * 4

def selftest():
    ok = True
    def chk(c, m):
        nonlocal ok
        if not c: print(f"# SELFTEST FAIL: {m}"); ok = False
    chk(arm_add_imm(0xE2840100) == (0, 4, 0x100), "add r0,r4,#0x100 not matched")
    chk(arm_add_imm(0xE2440100) is None, "matched a SUB as an add")
    chk(arm_str_imm_on(0xE5800034, 0) == 0x34, "str r0,[r0,#0x34] not matched")
    chk(arm_str_imm_on(0xE5900034, 0) is None, "matched a LOAD as a store")
    chk(arm_str_imm_on(0xE5000034, 0) is None, "matched a negative-offset store")
    chk(arm_str_imm_on(0xE5800034, 3) is None, "matched the wrong base register")
    chk(thumb_add_imm(0x30E8) == (0, 0xE8), "adds r0,#0xe8 not matched")
    chk(thumb_str_on(0x6001, 0) == 0, "str r1,[r0,#0] not matched")
    chk(thumb_str_on(0x6841, 0) is None, "matched a Thumb LOAD as a store")
    print(f"# matcher selftest: {'PASS' if ok else 'FAIL'}")
    return ok

def scan(path, base, target, window=12):
    d = open(path, "rb").read(); n = len(d); hits = []
    for o in range(0, n - 4, 4):
        a = arm_add_imm(struct.unpack_from("<I", d, o)[0])
        if not a: continue
        rd, rn, k = a
        if k == 0 or k >= target: continue
        want = target - k
        if want > 0xFFF: continue
        for j in range(1, window + 1):
            if o + j*4 + 4 > n: break
            s = arm_str_imm_on(struct.unpack_from("<I", d, o + j*4)[0], rd)
            if s == want:
                hits.append(("ARM", base + o,
                             f"add r{rd},r{rn},#{k:#x} then +{j} str [r{rd},#{want:#x}] = {target:#x}"))
    for o in range(0, n - 2, 2):
        a = thumb_add_imm(int.from_bytes(d[o:o+2], "little"))
        if not a: continue
        rd, k = a
        if k == 0 or k >= target: continue
        want = target - k
        if want > 124 or want % 4: continue
        for j in range(1, window + 1):
            if o + j*2 + 2 > n: break
            s = thumb_str_on(int.from_bytes(d[o+j*2:o+j*2+2], "little"), rd)
            if s == want:
                hits.append(("Thumb", base + o,
                             f"adds r{rd},#{k:#x} then +{j} str [r{rd},#{want:#x}] = {target:#x}"))
    return hits

def main():
    if not selftest():
        print("# ABORTING: matcher failed its own control"); return
    target = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x134
    print(f"# two-step sums reaching +{target:#x}\n")
    tot = 0
    for name, path, b in regions():
        if not os.path.isfile(path): continue
        for kind, addr, txt in scan(path, b, target):
            tot += 1
            print(f"{addr:#010x} ({name}) {kind}: {txt}")
    print(f"\n# {tot} candidate(s) across arm9 and all overlays")

if __name__ == "__main__":
    main()
