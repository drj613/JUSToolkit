#!/usr/bin/env python3
"""Extract ALAR (AL ARchive) containers — versions 2 and 3.

Why: `chr/ChrBin.aar` (322 KB) has never been unpacked, and per
`docs/articles/specs/summary.md` it contains `chr/col/*` (collision data),
`chr/ai/*`, `chr/shot/*` and `chr/effect/*`. The hitbox-priority subsystem in
`Battle-Engine-Map.md` has an open question — "where is the runtime CollisionEntry
parser... not located in this campaign at all" — and nobody had noticed the
collision *files* were sitting inside an unopened archive.

Format from `docs/articles/specs/alar.md`. An earlier hand-rolled attempt of mine
failed because it assumed a fixed-size entry table; V3 entries are variable-length
with the path embedded.

Header (both versions):
    0x00 char[4] "ALAR"
    0x04 byte    version
    0x05 byte    feature flags (bit0 = filenames, bit2 = folders/sub-containers)
    0x06 short   number of files

V3: 0x08 uint firstFileId, 0x0C uint lastFileId, 0x10 ushort dataOffset,
    0x12 ushort[numFiles] file-info offsets. Each file info:
    0x00 uint id, 0x04 uint data offset, 0x08 uint size, 0x0C uint flags,
    0x10 ushort path hash, 0x12 char[] NUL-terminated path.

Read-only on the input. Writes into the chosen output directory.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path


def parse_v3(b: bytes) -> list[dict]:
    n = struct.unpack_from("<H", b, 0x06)[0]
    offs = struct.unpack_from(f"<{n}H", b, 0x12)
    out = []
    for o in offs:
        fid, doff, size, flags = struct.unpack_from("<IIII", b, o)
        phash = struct.unpack_from("<H", b, o + 0x10)[0]
        end = b.find(b"\0", o + 0x12)
        path = b[o + 0x12:end].decode("ascii", "replace")
        out.append(dict(id=fid, offset=doff, size=size, flags=flags,
                        hash=phash, path=path))
    return out


def parse_v2(b: bytes) -> list[dict]:
    """V2: fixed 8-byte info entries after the extended header."""
    n = struct.unpack_from("<H", b, 0x06)[0]
    base = 0x0C
    out = []
    for i in range(n):
        doff, size = struct.unpack_from("<II", b, base + i * 8)
        out.append(dict(id=i, offset=doff, size=size, flags=0, hash=0,
                        path=f"file_{i:04d}.bin"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("archive", type=Path)
    ap.add_argument("--out", type=Path, help="extract into this directory")
    ap.add_argument("--list", action="store_true", help="list only")
    args = ap.parse_args()

    b = args.archive.read_bytes()
    if b[:4] != b"ALAR":
        print(f"not an ALAR container: {b[:4]!r}", file=sys.stderr)
        return 1
    ver, flags, n = b[4], b[5], struct.unpack_from("<H", b, 0x06)[0]
    print(f"{args.archive.name}: ALAR v{ver} flags 0x{flags:02X}, {n} files "
          f"({len(b)} bytes)")

    entries = parse_v3(b) if ver == 3 else parse_v2(b)

    # sanity: offsets and sizes must lie inside the file
    bad = [e for e in entries if e["offset"] + e["size"] > len(b)]
    if bad:
        print(f"  WARNING: {len(bad)} entries point outside the archive — "
              f"layout assumption may be wrong", file=sys.stderr)

    total = 0
    for e in entries:
        total += e["size"]
        if args.list:
            print(f"  id={e['id']:<5} 0x{e['offset']:06X} {e['size']:>7} B  "
                  f"flags=0x{e['flags']:08X}  {e['path']}")
    print(f"  total payload: {total} bytes "
          f"({100.0 * total / len(b):.1f}% of the container)")

    if args.out:
        for e in entries:
            dest = args.out / e["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b[e["offset"]:e["offset"] + e["size"]])
        print(f"  extracted {len(entries)} files to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
