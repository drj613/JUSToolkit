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
FAT_OFF, FAT_SIZE = 0x048, 0x04C
OVL9_OFF, OVL9_SIZE = 0x050, 0x054
OVL7_OFF, OVL7_SIZE = 0x058, 0x05C
OVL_ENTRY = 32


def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def extract_overlays(rom, outdir, which, tbl_off_field, tbl_size_field, meta):
    """Pull the ARM9/ARM7 overlays listed in the ROM's overlay table.

    Overlays matter for address work: several can share one RAM address and are
    swapped in as needed, so a given runtime address means different things
    depending on which overlay is resident. The manifest records `ram_address`
    per overlay precisely so that ambiguity is visible rather than assumed away.

    Table entry (32 bytes): id, ram_address, ram_size, bss_size,
    static_init_start, static_init_end, file_id, compressed_size|flags.
    File bytes come from the FAT: 8 bytes per file id (start, end).
    """
    tbl_off, tbl_size = u32(rom, tbl_off_field), u32(rom, tbl_size_field)
    fat_off = u32(rom, FAT_OFF)
    if tbl_off == 0 or tbl_size == 0:
        print("%s overlays: none declared" % which)
        return
    count = tbl_size // OVL_ENTRY
    sub = os.path.join(outdir, "overlays")
    os.makedirs(sub, exist_ok=True)
    by_addr = {}
    entries = []
    for i in range(count):
        e = tbl_off + i * OVL_ENTRY
        ovl_id = u32(rom, e + 0x00)
        ram_addr = u32(rom, e + 0x04)
        ram_size = u32(rom, e + 0x08)
        file_id = u32(rom, e + 0x18)
        flags = u32(rom, e + 0x1C)
        comp_size = flags & 0xFFFFFF
        compressed = bool(flags & (1 << 24))
        fe = fat_off + file_id * 8
        start, end = u32(rom, fe), u32(rom, fe + 4)
        if start == 0 or end <= start or end > len(rom):
            print("  ovl %02d: bad FAT entry, skipped" % ovl_id)
            continue
        blob = rom[start:end]
        name = "%s_ov%02d.bin" % (which, ovl_id)
        with open(os.path.join(sub, name), "wb") as f:
            f.write(blob)
        entries.append({
            "id": ovl_id, "file": name, "ram_address": ram_addr,
            "ram_size": ram_size, "file_id": file_id,
            "rom_start": start, "rom_end": end, "bytes": len(blob),
            "compressed": compressed, "compressed_size": comp_size,
        })
        by_addr.setdefault(ram_addr, []).append(ovl_id)
    meta["overlays_" + which] = entries
    print("%s overlays: %d extracted -> %s" % (which, len(entries), sub))
    for addr, ids in sorted(by_addr.items()):
        if len(ids) > 1:
            print("  !! 0x%08X shared by overlays %s -- an address in this "
                  "window means different things per resident overlay"
                  % (addr, ids))
    meta["overlay_shared_addresses_" + which] = {
        "0x%08X" % a: ids for a, ids in sorted(by_addr.items()) if len(ids) > 1}


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

    extract_overlays(rom, outdir, "arm9", OVL9_OFF, OVL9_SIZE, meta)
    extract_overlays(rom, outdir, "arm7", OVL7_OFF, OVL7_SIZE, meta)

    with open(os.path.join(outdir, "binaries.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("wrote %s" % os.path.join(outdir, "binaries.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
