#!/usr/bin/env python3
"""Extract the ARM9 (and ARM7) binary from a Nintendo DS ROM.

Reads the offsets straight out of the cartridge header, so it works on any
.nds file. Writes <out>/arm9.bin plus a small .json describing where the code
is mapped in memory -- you need the RAM base to turn a runtime address like
0x020784FC into a file offset.

Usage: python3 scripts/extract_arm9.py <rom.nds> <outdir>
"""
import json, os, struct, sys

# Header field offsets, per GBATEK.
FIELDS = {
    "arm9": {"rom_off": 0x020, "entry": 0x024, "ram_addr": 0x028, "size": 0x02C},
    "arm7": {"rom_off": 0x030, "entry": 0x034, "ram_addr": 0x038, "size": 0x03C},
}


def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    rom_path, outdir = argv[1], argv[2]
    with open(rom_path, "rb") as f:
        rom = f.read()
    os.makedirs(outdir, exist_ok=True)

    title = rom[0x00:0x0C].rstrip(b"\x00").decode("ascii", "replace")
    gamecode = rom[0x0C:0x10].decode("ascii", "replace")
    meta = {"rom": os.path.abspath(rom_path), "title": title,
            "gamecode": gamecode, "rom_bytes": len(rom), "binaries": {}}

    for name, fld in FIELDS.items():
        off = u32(rom, fld["rom_off"])
        size = u32(rom, fld["size"])
        ram = u32(rom, fld["ram_addr"])
        entry = u32(rom, fld["entry"])
        if off == 0 or size == 0 or off + size > len(rom):
            print("%s: bad/absent (off=0x%X size=0x%X)" % (name, off, size))
            continue
        blob = rom[off:off + size]
        out = os.path.join(outdir, name + ".bin")
        with open(out, "wb") as f:
            f.write(blob)
        # A BLZ-compressed binary is common on retail carts; the decompressor
        # stub address sits in the footer. Flag it rather than guess.
        meta["binaries"][name] = {
            "file": os.path.basename(out), "rom_offset": off, "size": size,
            "ram_address": ram, "entry_point": entry,
            "note": "file offset = runtime_addr - ram_address (if uncompressed)",
        }
        print("%s: 0x%X bytes -> %s  (maps to 0x%08X, entry 0x%08X)"
              % (name, size, out, ram, entry))

    with open(os.path.join(outdir, "binaries.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("wrote %s" % os.path.join(outdir, "binaries.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
