#!/usr/bin/env python3
"""Find every ARM `BL` caller of a target address across arm9 + all overlays.

Why this exists: grepping a text disassembly for `bl #0xTARGET` only searches
the files someone happened to disassemble, and this ROM has 14 overlays of which
only 9 were ever dumped to text. Worse, several overlays share a load address,
so "which file is this address in?" is ambiguous. This decodes the BL encoding
directly out of every extracted binary, so the answer is complete.

It also answers the opposite question honestly: **zero callers** is a real
result. A function living inside `arm9.bin` does NOT mean it runs in battle --
arm9 is the always-resident image and holds code for every mode. Only the caller
tells you which mode uses it.

BL encoding: 0xEB<imm24>, target = pc + 8 + sign_extend(imm24) * 4.

Usage:
    python3 scripts/find_callers.py 0x02078CB8 [0x0214E480 ...]
    python3 scripts/find_callers.py --data 0x02078488   # also count pointer refs
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARM9_DIR = os.path.join(ROOT, "jus_files", "arm9")


def images():
    out = [("arm9", 0x02000000, os.path.join(ARM9_DIR, "arm9.bin"))]
    manifest = os.path.join(ARM9_DIR, "binaries.json")
    if not os.path.exists(manifest):
        print("no %s -- run scripts/extract_arm9.py first" % manifest)
        return out
    meta = json.load(open(manifest))
    for e in meta.get("overlays_arm9", []):
        out.append(("ov%02d" % e["id"], e["ram_address"],
                    os.path.join(ARM9_DIR, "overlays", e["file"])))
    return out


def window_of(target, imgs):
    """Which overlays' address windows contain `target`."""
    out = []
    for name, base, path in imgs:
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        if base <= target < base + size:
            out.append(name)
    return out


def bl_callers(target, imgs):
    hits = []
    for name, base, path in imgs:
        try:
            data = open(path, "rb").read()
        except OSError:
            continue
        for off in range(0, len(data) - 3, 4):
            word = struct.unpack_from("<I", data, off)[0]
            if (word >> 24) != 0xEB:          # unconditional BL
                continue
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            pc = base + off
            if pc + 8 + imm * 4 == target:
                hits.append((name, pc))
    return hits


def data_refs(target, imgs):
    word = target.to_bytes(4, "little")
    return [(name, open(path, "rb").read().count(word))
            for name, _, path in imgs if os.path.exists(path)]


def main(argv):
    want_data = "--data" in argv
    targets = [int(a, 16) for a in argv[1:] if a.startswith("0x")]
    if not targets:
        print(__doc__)
        return 2
    imgs = images()
    for t in targets:
        hits = bl_callers(t, imgs)
        owners = window_of(t, imgs)
        print("0x%08X: %d BL caller(s)   [address lives in: %s]"
              % (t, len(hits), ", ".join(owners) or "?"))
        # If the target address falls inside a window shared by several
        # overlays, the address alone does not identify code: in each overlay's
        # mode that address holds *that* overlay's bytes. So a BL found in
        # overlay A "targeting" it is only a real call if A is the overlay that
        # actually owns the target -- and we cannot tell which that is from the
        # files. Flag every such hit rather than presenting it as fact.
        shared = len([o for o in owners if o != "arm9"]) > 1
        if shared:
            print("    NOTE: %d overlays share this address window, so BL hits "
                  "below may be coincidences -- confirm the resident overlay."
                  % len([o for o in owners if o != "arm9"]))
        for name, pc in hits:
            note = "   <-- ambiguous (shared window)" if shared and name != "arm9" else ""
            print("    %-6s 0x%08X%s" % (name, pc, note))
        if not hits:
            print("    (none -- may be called indirectly, or unused)")
        if want_data:
            refs = [(n, c) for n, c in data_refs(t, imgs) if c]
            print("    pointer refs: %s" % (refs or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
