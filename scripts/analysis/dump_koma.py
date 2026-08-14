#!/usr/bin/env python3
"""Dump and analyse bin/koma.bin records.

K1 established the record layout from the shipping C# parser
(src/JUS.Tool/Graphics/Converters/Binary2Koma.cs): 12 bytes per record,
little-endian, count = filesize / 12.

    0x0  u16  ImageId
    0x2  u16  Unknown2
    0x4  u8   nameIdx           index into Koma.NameTable (43 entries)
    0x5  u8   nameNum
    0x6  u8   Unknown6
    0x7  u8   Unknown7
    0x8  u8   KShapeGroupId
    0x9  u8   KShapeElementId
    0xA  u8   UnknownA
    0xB  u8   UnknownB

No existing tool dumps these fields (the CLI only renders PNGs), so this
script provides the raw field values plus per-field histograms that the
K2 predictions in docs/research/Koma-System-Observed-Behavior.md need.

Read-only. Never writes to jus_files/.
"""

from __future__ import annotations

import argparse
import collections
import json
import struct
import sys
from pathlib import Path

RECORD_SIZE = 12
DEFAULT_KOMA = Path("jus_files/ripped_jus_files/bin/koma.bin")

# Byte-level fields we histogram. u16 fields are also kept whole.
BYTE_FIELDS = [
    (0x4, "nameIdx"),
    (0x5, "nameNum"),
    (0x6, "unk6"),
    (0x7, "unk7"),
    (0x8, "kshapeGroup"),
    (0x9, "kshapeElem"),
    (0xA, "unkA"),
    (0xB, "unkB"),
]


# --- nature resolution -------------------------------------------------------
# Solved from the deck-editor overlay accessor at 0x0214E480 (ov05 disassembly).
# Nature is NOT a stored per-panel value; it is computed:
#
#   helper (panelType 2)          -> 3 (なし)
#   battle (panelType 0)          -> high nibble of flags(+0xB), unless that
#                                    nibble is 3 (the "no override" sentinel),
#                                    in which case chr_b[abilityId] + 0x00
#   support (panelType 1)         -> chr_s[abilityId*20 + (kshapeGroup-1)*8]
#
# Enum: 0 = 力 Power, 1 = 知 Knowledge, 2 = 笑 Laughter, 3 = なし Neutral.
# Verified: all 9 of Naruto's panels reproduce the owner's observed table.

NATURE_NAMES = {0: "Power", 1: "Knowledge", 2: "Laughter", 3: "Neutral"}
NATURE_JP = {0: "\u529b", 1: "\u77e5", 2: "\u7b11", 3: "\u306a\u3057"}

CHR_B = Path("jus_files/ripped_jus_files/bin/chr_b.bin")
CHR_S = Path("jus_files/ripped_jus_files/bin/chr_s.bin")


def resolve_natures(recs: list[dict], chr_b: Path = CHR_B, chr_s: Path = CHR_S) -> None:
    """Annotate each record in-place with 'nature' and 'natureName'."""
    cb = chr_b.read_bytes()
    cs = chr_s.read_bytes()
    for r in recs:
        ptype = r["unk6"]
        if ptype == 2:
            n = 3
        elif ptype == 0:
            nib = (r["unkB"] >> 4) & 0xF
            n = nib if nib != 3 else cb[r["unk7"] * 60 + 0x00]
        else:
            n = cs[r["unk7"] * 20 + (r["kshapeGroup"] - 1) * 8]
        r["nature"] = n
        r["natureName"] = NATURE_NAMES.get(n, f"?{n}")


def parse_records(raw: bytes) -> list[dict]:
    if len(raw) % RECORD_SIZE:
        print(
            f"warning: {len(raw)} bytes is not a multiple of {RECORD_SIZE}; "
            f"{len(raw) % RECORD_SIZE} trailing bytes ignored",
            file=sys.stderr,
        )
    out = []
    for i in range(len(raw) // RECORD_SIZE):
        b = raw[i * RECORD_SIZE : (i + 1) * RECORD_SIZE]
        image_id, unk2 = struct.unpack_from("<HH", b, 0)
        rec = {
            "idx": i,
            "imageId": image_id,
            "unk2": unk2,
            "raw": b.hex(),
        }
        for off, name in BYTE_FIELDS:
            rec[name] = b[off]
        out.append(rec)
    return out


def histogram(recs: list[dict], field: str) -> collections.Counter:
    return collections.Counter(r[field] for r in recs)


def summarise(recs: list[dict], field: str) -> dict:
    h = histogram(recs, field)
    vals = sorted(h)
    return {
        "field": field,
        "distinct": len(h),
        "min": vals[0] if vals else None,
        "max": vals[-1] if vals else None,
        "top": h.most_common(8),
        "all_values_if_few": vals if len(vals) <= 20 else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--koma", type=Path, default=DEFAULT_KOMA)
    ap.add_argument("--json", type=Path, help="write full per-record dump here")
    ap.add_argument(
        "--group-by-size",
        action="store_true",
        help="assume kshapeGroup is panel size and break histograms down by it",
    )
    args = ap.parse_args()

    raw = args.koma.read_bytes()
    recs = parse_records(raw)
    print(f"file      : {args.koma} ({len(raw)} bytes)")
    print(f"records   : {len(recs)}  (stride {RECORD_SIZE})")
    print(f"imageId   : min={min(r['imageId'] for r in recs)} "
          f"max={max(r['imageId'] for r in recs)} "
          f"distinct={len({r['imageId'] for r in recs})}")

    if CHR_B.exists() and CHR_S.exists():
        resolve_natures(recs)
        nh = collections.Counter(r["natureName"] for r in recs)
        print(f"nature    : {dict(nh)}")
    else:
        print("nature    : skipped (chr_b.bin / chr_s.bin not found)")

    print("\n=== per-field summary ===")
    fields = ["unk2"] + [n for _, n in BYTE_FIELDS]
    for f in fields:
        s = summarise(recs, f)
        line = f"{s['field']:<12} distinct={s['distinct']:<5} range={s['min']}..{s['max']}"
        if s["all_values_if_few"] is not None:
            line += f"  values={s['all_values_if_few']}"
        else:
            line += f"  top={s['top'][:5]}"
        print(line)

    if args.group_by_size:
        print("\n=== kshapeGroup breakdown (testing P5: group == panel size?) ===")
        by_group = collections.defaultdict(list)
        for r in recs:
            by_group[r["kshapeGroup"]].append(r)
        for g in sorted(by_group):
            rs = by_group[g]
            elems = sorted({r["kshapeElem"] for r in rs})
            print(f"  group {g:<3} n={len(rs):<5} distinct kshapeElem={len(elems):<4} "
                  f"elems={elems if len(elems) <= 16 else str(elems[:16]) + '...'}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(recs, indent=1))
        print(f"\nwrote {args.json} ({len(recs)} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
