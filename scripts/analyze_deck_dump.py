#!/usr/bin/env python3
"""
Analyze binary memory dumps from JUS deck state.

Usage:
    python scripts/analyze_deck_dump.py --dir jus_files/analysis/
    python scripts/analyze_deck_dump.py --search 0x1DD4
    python scripts/analyze_deck_dump.py --diff dump1.bin dump2.bin
"""

import argparse
import os
from pathlib import Path

# Known koma IDs from cheat codes
KOMA_IDS = {
    0x1DD4: "Eve 4-koma",
    0x1DB0: "Eve 1-koma",
    0x1DBC: "Eve 2-koma",
    0x1DC8: "Eve 3-koma",
    0x1DE0: "Eve 5-koma",
    0x1738: "Goku 1-koma",
    0x1744: "Goku 2-koma",
    0x1E70: "Ichigo 1-koma",
    0x196C: "Naruto 1-koma",
    0x2890: "Luffy 1-koma",
}

# Known addresses
KNOWN_ADDRESSES = {
    0x020a0c98: "Deck state flag",
    0x020a20f6: "Leader marker",
    0x020a2240: "Counter",
    0x020AFEB4: "Active deck index",
    0x020B0BAC: "Koma unlock flags",
}


def search_bytes(data: bytes, pattern: bytes, base_addr: int = 0) -> list:
    """Search for byte pattern in data."""
    results = []
    offset = 0
    while True:
        idx = data.find(pattern, offset)
        if idx == -1:
            break
        results.append(base_addr + idx)
        offset = idx + 1
    return results


def search_word(data: bytes, value: int, base_addr: int = 0) -> list:
    """Search for 16-bit word (little-endian) in data."""
    pattern = value.to_bytes(2, 'little')
    return search_bytes(data, pattern, base_addr)


def diff_binary(data1: bytes, data2: bytes, base_addr: int = 0) -> list:
    """Find differences between two binary dumps."""
    diffs = []
    min_len = min(len(data1), len(data2))

    i = 0
    while i < min_len:
        if data1[i] != data2[i]:
            # Find extent of difference
            start = i
            while i < min_len and data1[i] != data2[i]:
                i += 1
            diffs.append({
                'addr': base_addr + start,
                'size': i - start,
                'old': data1[start:i],
                'new': data2[start:i],
            })
        else:
            i += 1

    return diffs


def analyze_dump(filepath: str, base_addr: int = None) -> dict:
    """Analyze a single binary dump."""
    path = Path(filepath)
    data = path.read_bytes()

    # Try to infer base address from filename
    if base_addr is None:
        name = path.stem
        for part in name.split('_'):
            try:
                base_addr = int(part, 16)
                break
            except ValueError:
                continue
        if base_addr is None:
            base_addr = 0

    results = {
        'file': str(path),
        'size': len(data),
        'base_addr': base_addr,
        'koma_ids_found': [],
        'known_addresses': [],
    }

    # Search for known koma IDs
    for koma_id, name in KOMA_IDS.items():
        addrs = search_word(data, koma_id, base_addr)
        if addrs:
            results['koma_ids_found'].append({
                'id': koma_id,
                'name': name,
                'addresses': addrs,
            })

    # Check for known addresses within this dump
    end_addr = base_addr + len(data)
    for addr, name in KNOWN_ADDRESSES.items():
        if base_addr <= addr < end_addr:
            offset = addr - base_addr
            value = data[offset:offset+4]
            results['known_addresses'].append({
                'addr': addr,
                'name': name,
                'value': value.hex(),
            })

    return results


def print_analysis(results: dict):
    """Print analysis results."""
    print(f"\n=== {results['file']} ===")
    print(f"Size: {results['size']} bytes")
    print(f"Base: 0x{results['base_addr']:08X}")

    if results['koma_ids_found']:
        print("\nKoma IDs found:")
        for koma in results['koma_ids_found']:
            addrs = ', '.join(f"0x{a:08X}" for a in koma['addresses'][:5])
            if len(koma['addresses']) > 5:
                addrs += f" ... (+{len(koma['addresses'])-5} more)"
            print(f"  {koma['name']} (0x{koma['id']:04X}): {addrs}")

    if results['known_addresses']:
        print("\nKnown addresses in this dump:")
        for ka in results['known_addresses']:
            print(f"  0x{ka['addr']:08X} ({ka['name']}): {ka['value']}")


def print_diff(diffs: list, noise_addrs: set = None):
    """Print diff results, filtering noise."""
    if noise_addrs is None:
        noise_addrs = set()

    # Known noise addresses (timers/counters)
    known_noise = {
        0x020a10d4, 0x020a10fc, 0x020aae90, 0x020ab008,
        0x020ab184, 0x020aeb6c, 0x020b770c,
    }
    noise_addrs = noise_addrs.union(known_noise)

    filtered = [d for d in diffs if d['addr'] not in noise_addrs]

    print(f"\nTotal differences: {len(diffs)} regions")
    print(f"After filtering noise: {len(filtered)} regions")

    for d in filtered[:30]:
        old_hex = d['old'][:8].hex(' ')
        new_hex = d['new'][:8].hex(' ')
        if len(d['old']) > 8:
            old_hex += ' ...'
            new_hex += ' ...'

        # Check if known address
        known = ""
        for addr, name in KNOWN_ADDRESSES.items():
            if d['addr'] <= addr < d['addr'] + d['size']:
                known = f" <- {name}"
                break

        # Check if contains koma ID
        for koma_id, name in KOMA_IDS.items():
            pattern = koma_id.to_bytes(2, 'little')
            if pattern in d['old'] or pattern in d['new']:
                known += f" [contains {name}]"
                break

        print(f"\n0x{d['addr']:08X} ({d['size']} bytes){known}")
        print(f"  Old: {old_hex}")
        print(f"  New: {new_hex}")

    if len(filtered) > 30:
        print(f"\n... and {len(filtered) - 30} more")


def main():
    parser = argparse.ArgumentParser(description="Analyze JUS memory dumps")
    parser.add_argument("--dir", help="Directory with dump files")
    parser.add_argument("--file", help="Single dump file to analyze")
    parser.add_argument("--search", help="Search for hex value (e.g., 0x1DD4)")
    parser.add_argument("--diff", nargs=2, help="Diff two binary files")
    parser.add_argument("--base", type=lambda x: int(x, 0), help="Base address for file")

    args = parser.parse_args()

    if args.diff:
        file1, file2 = args.diff
        data1 = Path(file1).read_bytes()
        data2 = Path(file2).read_bytes()
        base = args.base or 0

        print(f"Diffing {file1} vs {file2}")
        diffs = diff_binary(data1, data2, base)
        print_diff(diffs)
        return

    if args.dir:
        dump_dir = Path(args.dir)
        bin_files = list(dump_dir.glob("*.bin"))

        if not bin_files:
            print(f"No .bin files found in {dump_dir}")
            return

        for bf in sorted(bin_files):
            results = analyze_dump(str(bf))
            print_analysis(results)

        return

    if args.file:
        results = analyze_dump(args.file, args.base)
        print_analysis(results)
        return

    if args.search:
        value = int(args.search, 0)
        print(f"Searching for 0x{value:04X} in analysis directory...")

        dump_dir = Path("jus_files/analysis")
        for bf in dump_dir.glob("*.bin"):
            data = bf.read_bytes()
            # Infer base address
            base = 0
            for part in bf.stem.split('_'):
                try:
                    base = int(part, 16)
                    break
                except:
                    pass

            addrs = search_word(data, value, base)
            if addrs:
                print(f"\n{bf.name}:")
                for a in addrs[:10]:
                    print(f"  0x{a:08X}")
                if len(addrs) > 10:
                    print(f"  ... and {len(addrs) - 10} more")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
