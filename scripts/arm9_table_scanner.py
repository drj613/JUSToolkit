#!/usr/bin/env python3
"""
ARM9 Table Scanner for Jump Ultimate Stars.

Scans ARM9.bin to find:
- Pointer tables (arrays of ROM addresses 0x020xxxxx)
- Index tables (bounded byte arrays like character indices)
- String references (file names, series codes)
- Repeating struct patterns

Usage:
    python arm9_table_scanner.py --arm9 arm9.bin --output analysis/
    python arm9_table_scanner.py --arm9 arm9.bin --scan-range 0x80000 0xA0000
"""

import argparse
import json
import struct
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
from collections import Counter


# Known constants for JUS
ARM9_BASE = 0x02000000
NUM_BATTLE_CHARS = 74
NUM_JPOWER_ENTRIES = 311
NUM_KOMA_ENTRIES = 890

# Known table locations (for cross-reference)
KNOWN_TABLES = {
    0x0924B0: "Collision file pointer table",
    0x08D4A0: "chr_b → collision identity map",
    0x09E780: "Koma name table",
}

# Series prefixes to search for
SERIES_PREFIXES = [
    b"db_", b"op_", b"na_", b"bl_", b"sk_", b"jj_", b"hh_",
    b"yh_", b"yo_", b"rk_", b"bc_", b"bu_", b"dg_", b"bb_",
    b"kk_", b"gt_", b"tr_", b"pj_", b"ds_", b"mr_", b"nn_",
    b"hk_", b"ss_", b"kn_", b"oj_", b"hs_", b"nk_", b"dt_",
]


@dataclass
class TableCandidate:
    """A potential table found in ARM9."""
    offset: int
    table_type: str
    size: int
    entry_count: int
    confidence: str
    description: str
    sample_values: list
    hex_offset: str = ""

    def __post_init__(self):
        self.hex_offset = f"0x{self.offset:06X}"


@dataclass
class StringReference:
    """A string found in ARM9."""
    offset: int
    string: str
    context: str
    hex_offset: str = ""

    def __post_init__(self):
        self.hex_offset = f"0x{self.offset:06X}"


def read_arm9(filepath: str) -> bytes:
    """Read ARM9.bin file."""
    with open(filepath, 'rb') as f:
        return f.read()


def is_valid_rom_pointer(value: int) -> bool:
    """Check if value looks like a ROM pointer."""
    return 0x02000000 < value < 0x02200000


def scan_pointer_tables(arm9: bytes, start: int, end: int, min_entries: int = 4) -> List[TableCandidate]:
    """Find arrays of ROM pointers."""
    candidates = []

    offset = start
    while offset < end - 8:
        # Check if this looks like a pointer
        ptr = struct.unpack_from('<I', arm9, offset)[0]

        if is_valid_rom_pointer(ptr):
            # Count consecutive pointers
            count = 0
            entry_size = 4  # Try 4-byte entries first

            for i in range(100):  # Max 100 entries
                check_offset = offset + i * entry_size
                if check_offset + 4 > len(arm9):
                    break
                check_ptr = struct.unpack_from('<I', arm9, check_offset)[0]
                if is_valid_rom_pointer(check_ptr):
                    count += 1
                else:
                    break

            if count < min_entries:
                # Try 8-byte entries (pointer + data)
                entry_size = 8
                count = 0
                for i in range(100):
                    check_offset = offset + i * entry_size
                    if check_offset + 4 > len(arm9):
                        break
                    check_ptr = struct.unpack_from('<I', arm9, check_offset)[0]
                    if is_valid_rom_pointer(check_ptr):
                        count += 1
                    else:
                        break

            if count >= min_entries:
                # Calculate confidence
                if count == NUM_BATTLE_CHARS:
                    confidence = "HIGH (matches 74 battle chars)"
                elif count == NUM_JPOWER_ENTRIES:
                    confidence = "HIGH (matches 311 jpower entries)"
                elif count == NUM_KOMA_ENTRIES:
                    confidence = "HIGH (matches 890 koma entries)"
                elif count >= 50:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"

                # Get sample pointers
                samples = []
                for i in range(min(5, count)):
                    p = struct.unpack_from('<I', arm9, offset + i * entry_size)[0]
                    file_offset = p - ARM9_BASE
                    # Try to read string at pointer target
                    if file_offset < len(arm9):
                        end_idx = arm9.find(b'\x00', file_offset, file_offset + 20)
                        if end_idx > file_offset:
                            string = arm9[file_offset:end_idx].decode('ascii', errors='replace')
                            samples.append(f"0x{p:08X} -> \"{string}\"")
                        else:
                            samples.append(f"0x{p:08X}")
                    else:
                        samples.append(f"0x{p:08X}")

                # Check if known table
                desc = KNOWN_TABLES.get(offset, "Unknown pointer table")

                candidates.append(TableCandidate(
                    offset=offset,
                    table_type="pointer_table",
                    size=count * entry_size,
                    entry_count=count,
                    confidence=confidence,
                    description=desc,
                    sample_values=samples,
                ))

                # Skip past this table
                offset += count * entry_size
                continue

        offset += 4

    return candidates


def scan_index_tables(arm9: bytes, start: int, end: int,
                      max_value: int = 100, min_entries: int = 20) -> List[TableCandidate]:
    """Find arrays of bounded index values."""
    candidates = []

    offset = start
    while offset < end - min_entries:
        # Check if this region has bounded byte values
        values = list(arm9[offset:offset + 200])

        # Count how many are in valid range
        valid_count = 0
        for v in values:
            if v <= max_value:
                valid_count += 1
            else:
                break

        if valid_count >= min_entries:
            # Analyze the values
            subset = values[:valid_count]
            unique = len(set(subset))

            # Check for special patterns
            if valid_count == NUM_BATTLE_CHARS:
                confidence = "HIGH (matches 74 battle chars)"
                # Check if identity mapping
                if subset == list(range(74)):
                    desc = "Identity mapping (0,1,2...73)"
                else:
                    desc = f"Index table with {unique} unique values"
            elif valid_count in [70, 71, 72, 73, 75, 76]:
                confidence = "MEDIUM (near 74)"
                desc = f"Index table with {unique} unique values"
            else:
                confidence = "LOW"
                desc = f"Byte array with {unique} unique values in range 0-{max_value}"

            # Skip if known table
            if offset in KNOWN_TABLES:
                desc = KNOWN_TABLES[offset]

            candidates.append(TableCandidate(
                offset=offset,
                table_type="index_table",
                size=valid_count,
                entry_count=valid_count,
                confidence=confidence,
                description=desc,
                sample_values=subset[:20],
            ))

            offset += valid_count
            continue

        offset += 1

    return candidates


def scan_string_references(arm9: bytes, patterns: List[bytes]) -> List[StringReference]:
    """Find string patterns in ARM9."""
    references = []

    for pattern in patterns:
        idx = 0
        while True:
            idx = arm9.find(pattern, idx)
            if idx == -1:
                break

            # Read the full string
            end_idx = arm9.find(b'\x00', idx, idx + 50)
            if end_idx > idx:
                full_string = arm9[idx:end_idx].decode('ascii', errors='replace')

                # Determine context
                if b'_b_' in arm9[idx:end_idx]:
                    context = "Battle character file"
                elif b'_s_' in arm9[idx:end_idx]:
                    context = "Support character file"
                else:
                    context = "Unknown"

                references.append(StringReference(
                    offset=idx,
                    string=full_string,
                    context=context,
                ))

            idx += 1

    return references


def scan_struct_arrays(arm9: bytes, start: int, end: int,
                       struct_sizes: List[int] = [12, 20, 60, 304]) -> List[TableCandidate]:
    """Find arrays of repeating struct-like patterns."""
    candidates = []

    for struct_size in struct_sizes:
        offset = start
        while offset < end - struct_size * 3:
            # Check if this region has repeating patterns
            # Look for similar byte distributions across entries
            entries = []
            for i in range(10):  # Check up to 10 entries
                entry_offset = offset + i * struct_size
                if entry_offset + struct_size > len(arm9):
                    break
                entry = arm9[entry_offset:entry_offset + struct_size]
                entries.append(entry)

            if len(entries) < 3:
                offset += struct_size
                continue

            # Check for structural similarity
            # Look at first few bytes of each entry
            first_bytes = [e[:4] for e in entries]
            byte_patterns = Counter([b[0] for b in first_bytes])

            # If first bytes are similar (same byte appears often), might be struct array
            most_common_count = byte_patterns.most_common(1)[0][1]

            if most_common_count >= len(entries) // 2:
                # Count how many entries follow the pattern
                count = 0
                for i in range(200):
                    entry_offset = offset + i * struct_size
                    if entry_offset + struct_size > len(arm9):
                        break
                    # Simple heuristic: check if values are reasonable
                    entry = arm9[entry_offset:entry_offset + struct_size]
                    # Most game data has first bytes in reasonable range
                    if entry[0] < 20 or entry[0] in [0xFF]:
                        count += 1
                    else:
                        break

                if count >= 10:
                    if struct_size == 60 and count in range(70, 80):
                        confidence = "HIGH (likely chr_b format)"
                        desc = f"Possible character data array ({struct_size}B × {count})"
                    elif struct_size == 20 and count > 5:
                        confidence = "MEDIUM (collision format?)"
                        desc = f"Possible collision array ({struct_size}B × {count})"
                    elif struct_size == 12 and count > 100:
                        confidence = "MEDIUM (koma format?)"
                        desc = f"Possible koma array ({struct_size}B × {count})"
                    else:
                        confidence = "LOW"
                        desc = f"Repeating {struct_size}B structure × {count}"

                    candidates.append(TableCandidate(
                        offset=offset,
                        table_type="struct_array",
                        size=count * struct_size,
                        entry_count=count,
                        confidence=confidence,
                        description=desc,
                        sample_values=[list(entries[0][:16])],  # First 16 bytes of first entry
                    ))

                    offset += count * struct_size
                    continue

            offset += struct_size

    return candidates


def classify_region(arm9: bytes, offset: int, size: int = 1024) -> str:
    """Classify a region as code or data."""
    if offset + size > len(arm9):
        size = len(arm9) - offset

    chunk = arm9[offset:offset + size]

    # ARM instruction common prefixes in the 4th byte (big-endian position)
    arm_prefixes = {0xE3, 0xE5, 0xE1, 0xEB, 0x0A, 0x1A, 0x2A, 0x3A, 0xEA}

    instruction_count = 0
    for i in range(0, len(chunk) - 3, 4):
        # Check if 4th byte looks like ARM instruction
        if chunk[i + 3] in arm_prefixes:
            instruction_count += 1

    total_words = len(chunk) // 4
    if total_words == 0:
        return "unknown"

    ratio = instruction_count / total_words

    if ratio > 0.4:
        return "code"
    elif ratio < 0.1:
        return "data"
    else:
        return "mixed"


def map_arm9_regions(arm9: bytes, block_size: int = 0x1000) -> List[dict]:
    """Map ARM9 into code/data regions."""
    regions = []

    offset = 0
    while offset < len(arm9):
        region_type = classify_region(arm9, offset, block_size)

        # Extend region while type remains same
        end_offset = offset + block_size
        while end_offset < len(arm9):
            next_type = classify_region(arm9, end_offset, block_size)
            if next_type != region_type:
                break
            end_offset += block_size

        regions.append({
            "start": f"0x{offset:06X}",
            "end": f"0x{end_offset:06X}",
            "size": end_offset - offset,
            "type": region_type,
        })

        offset = end_offset

    return regions


def main():
    parser = argparse.ArgumentParser(description="Scan ARM9.bin for tables and patterns")
    parser.add_argument("--arm9", required=True, help="Path to ARM9.bin")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--scan-range", nargs=2, type=lambda x: int(x, 0),
                        default=[0x080000, 0x0B0000],
                        help="Hex range to scan (default: 0x80000 0xB0000)")
    parser.add_argument("--map-regions", action="store_true",
                        help="Map entire ARM9 into code/data regions")

    args = parser.parse_args()

    print(f"Loading ARM9 from {args.arm9}...")
    arm9 = read_arm9(args.arm9)
    print(f"  Size: {len(arm9):,} bytes (0x{len(arm9):X})")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    start, end = args.scan_range
    print(f"\nScanning range 0x{start:06X} - 0x{end:06X}...")

    # Scan for different table types
    print("\n[1/4] Scanning for pointer tables...")
    pointer_tables = scan_pointer_tables(arm9, start, end)
    print(f"  Found {len(pointer_tables)} pointer table candidates")

    print("\n[2/4] Scanning for index tables...")
    index_tables = scan_index_tables(arm9, start, end)
    print(f"  Found {len(index_tables)} index table candidates")

    print("\n[3/4] Scanning for string references...")
    strings = scan_string_references(arm9, SERIES_PREFIXES)
    print(f"  Found {len(strings)} string references")

    print("\n[4/4] Scanning for struct arrays...")
    struct_arrays = scan_struct_arrays(arm9, start, end)
    print(f"  Found {len(struct_arrays)} struct array candidates")

    # Combine and sort all findings
    all_tables = pointer_tables + index_tables + struct_arrays
    all_tables.sort(key=lambda t: t.offset)

    # Filter by confidence
    high_conf = [t for t in all_tables if "HIGH" in t.confidence]
    med_conf = [t for t in all_tables if "MEDIUM" in t.confidence]

    print(f"\n=== RESULTS ===")
    print(f"High confidence: {len(high_conf)}")
    print(f"Medium confidence: {len(med_conf)}")
    print(f"Total candidates: {len(all_tables)}")

    # Print high confidence findings
    if high_conf:
        print("\n--- HIGH CONFIDENCE TABLES ---")
        for t in high_conf:
            print(f"  {t.hex_offset}: {t.description}")
            print(f"    Type: {t.table_type}, Entries: {t.entry_count}, Size: {t.size}B")
            if t.sample_values:
                print(f"    Sample: {t.sample_values[:3]}")

    # Save results
    results = {
        "scan_range": {"start": f"0x{start:06X}", "end": f"0x{end:06X}"},
        "pointer_tables": [asdict(t) for t in pointer_tables],
        "index_tables": [asdict(t) for t in index_tables],
        "struct_arrays": [asdict(t) for t in struct_arrays],
        "string_references": [asdict(s) for s in strings],
        "summary": {
            "total_candidates": len(all_tables),
            "high_confidence": len(high_conf),
            "medium_confidence": len(med_conf),
        }
    }

    output_file = output_dir / "arm9_tables.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    # Optionally map regions
    if args.map_regions:
        print("\nMapping ARM9 regions...")
        regions = map_arm9_regions(arm9)
        regions_file = output_dir / "arm9_regions.json"
        with open(regions_file, 'w') as f:
            json.dump(regions, f, indent=2)
        print(f"Region map saved to: {regions_file}")

        # Summary
        code_size = sum(r['size'] for r in regions if r['type'] == 'code')
        data_size = sum(r['size'] for r in regions if r['type'] == 'data')
        print(f"  Code regions: {code_size:,} bytes ({code_size*100//len(arm9)}%)")
        print(f"  Data regions: {data_size:,} bytes ({data_size*100//len(arm9)}%)")


if __name__ == "__main__":
    main()
