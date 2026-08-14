#!/usr/bin/env python3
"""Extract the ARM9 overlays from the JUS ROM.

`scripts/extract_arm9.py` (from the emulator-harness session) pulls arm9.bin and
arm7.bin. It does not pull overlays, and the ROM header declares 14 of them --
only 3 of which have ever been disassembled. The deck-editor code and data almost
certainly live in one, which is why searches confined to arm9.bin come up empty.

Read-only on the ROM. Writes to jus_files/overlays/ (never to ripped_jus_files/).

NDS layout used here:
  header 0x50: arm9 overlay table offset, length   (32 bytes per entry)
  header 0x48: FAT offset, length                  (8 bytes per file: start, end)
  overlay entry: id, ram_addr, ram_size, bss_size, sinit_start, sinit_end,
                 file_id, (compressed_size:24 | compress_flag:8)

BLZ-compressed overlays are written out raw and flagged; decompression is only
attempted when the flag is set.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

DEFAULT_ROM = Path("/Users/djdjo/Documents/mine/rom/jus.nds")
DEFAULT_OUT = Path("jus_files/overlays")


def blz_decompress(data: bytes) -> bytes | None:
    """Decompress a BLZ (backwards-LZ) block as used by NDS overlays.

    Returns None if the footer doesn't look like BLZ, so callers can fall back
    to treating the payload as raw.
    """
    if len(data) < 8:
        return None
    footer = data[-8:]
    enc_len_and_hdr, dec_off = struct.unpack("<II", footer)
    hdr_len = enc_len_and_hdr >> 24
    enc_len = enc_len_and_hdr & 0xFFFFFF
    if not (8 <= hdr_len <= 0xB) or enc_len > len(data) or dec_off == 0:
        return None

    dst = bytearray(data)
    dst.extend(b"\0" * dec_off)
    # The compressed region ends where the footer begins.
    src = len(data) - hdr_len
    end = len(data) - enc_len
    out = len(data) + dec_off
    try:
        while src > end:
            src -= 1
            flags = dst[src]
            for bit in range(8):
                if src <= end:
                    break
                if flags & (0x80 >> bit):
                    src -= 2
                    pair = (dst[src] << 8) | dst[src + 1]
                    length = (pair >> 12) + 3
                    disp = (pair & 0xFFF) + 3
                    for _ in range(length):
                        out -= 1
                        dst[out] = dst[out + disp]
                else:
                    src -= 1
                    out -= 1
                    dst[out] = dst[src]
                if out <= 0:
                    break
    except IndexError:
        return None
    return bytes(dst[len(data) - enc_len + hdr_len :]) if False else bytes(dst)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--decompress", action="store_true",
                    help="attempt BLZ decompression when the compress flag is set")
    args = ap.parse_args()

    if not args.rom.exists():
        print(f"ROM not found: {args.rom}", file=sys.stderr)
        return 1

    rom = args.rom.read_bytes()
    ovt_off, ovt_len = struct.unpack_from("<II", rom, 0x50)
    fat_off, fat_len = struct.unpack_from("<II", rom, 0x48)
    count = ovt_len // 32
    print(f"rom      : {args.rom} ({len(rom)} bytes)")
    print(f"overlays : {count}  (table at 0x{ovt_off:X})")
    print(f"FAT      : 0x{fat_off:X}, {fat_len // 8} files\n")

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i in range(count):
        e = ovt_off + i * 32
        ov_id, ram_addr, ram_size, bss, si_s, si_e, file_id, packed = \
            struct.unpack_from("<IIIIIIII", rom, e)
        comp_size = packed & 0xFFFFFF
        comp_flag = packed >> 24

        fe = fat_off + file_id * 8
        start, end = struct.unpack_from("<II", rom, fe)
        payload = rom[start:end]

        name = f"ov{ov_id:02d}.bin"
        data = payload
        note = "raw"
        if comp_flag and args.decompress:
            dec = blz_decompress(payload)
            if dec:
                data = dec
                note = "blz-decompressed"
            else:
                note = "blz-flagged, decompression failed - written raw"
        elif comp_flag:
            note = "blz-flagged, written raw (use --decompress)"

        (args.out / name).write_bytes(data)
        manifest.append({
            "id": ov_id, "file": name,
            "ram_address": ram_addr, "ram_size": ram_size, "bss_size": bss,
            "rom_start": start, "rom_end": end,
            "file_bytes": len(payload), "written_bytes": len(data),
            "compress_flag": comp_flag, "compressed_size": comp_size,
            "note": note,
        })
        print(f"  ov{ov_id:02d}: ram 0x{ram_addr:08X} size {ram_size:>7} "
              f"file {len(payload):>7}B flag={comp_flag} -> {name} ({note})")

    (args.out / "overlays.json").write_text(json.dumps(manifest, indent=1))
    print(f"\nwrote {count} overlays + overlays.json to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
