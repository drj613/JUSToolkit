#!/usr/bin/env python3
"""
Classify characters by damageFlags system (Direct vs Indirect).

Analyzes collision files and counts damageFlags=0 vs damageFlags>0 entries
to determine which jpower selection system each character uses.

Usage:
    python classify_damage_flags.py <collision_dir>
    python classify_damage_flags.py --single <collision_file>
    
Example:
    python classify_damage_flags.py ./extracted/collision/
    python classify_damage_flags.py --single ./extracted/collision/bl_b_01.bin
"""

import argparse
import os
import struct
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

# Entry size from CollisionEntry.cs
ENTRY_SIZE = 20
DAMAGE_FLAGS_OFFSET = 14  # byte offset within entry

# Character mapping (index, file_prefix, name, series)
CHARACTER_MAP = [
    (0, "db_b_01", "Goku", "Dragon Ball"),
    (1, "db_b_02", "Goku (SSJ)", "Dragon Ball"),
    (2, "db_b_03", "Vegetto", "Dragon Ball"),
    (3, "db_b_04", "Vegeta", "Dragon Ball"),
    (4, "db_b_05", "Vegeta (SSJ)", "Dragon Ball"),
    (5, "db_b_06", "Gohan (SSJ)", "Dragon Ball"),
    (6, "db_b_07", "Gohan (SSJ2)", "Dragon Ball"),
    (7, "db_b_08", "Gotenks", "Dragon Ball"),
    (8, "db_b_09", "Gotenks (SSJ)", "Dragon Ball"),
    (9, "db_b_10", "Piccolo", "Dragon Ball"),
    (10, "db_b_11", "Frieza", "Dragon Ball"),
    (11, "db_b_12", "Majin Buu", "Dragon Ball"),
    (12, "op_b_01", "Luffy", "One Piece"),
    (13, "op_b_02", "Gear 2 Luffy", "One Piece"),
    (14, "op_b_03", "Zoro", "One Piece"),
    (15, "op_b_04", "Nami", "One Piece"),
    (16, "op_b_05", "PCT Nami", "One Piece"),
    (17, "op_b_06", "Sanji", "One Piece"),
    (18, "op_b_07", "Robin", "One Piece"),
    (19, "op_b_08", "Franky", "One Piece"),
    (20, "na_b_01", "Naruto", "Naruto"),
    (21, "na_b_02", "Kyuubi Naruto", "Naruto"),
    (22, "na_b_03", "Sasuke", "Naruto"),
    (23, "na_b_04", "Sakura", "Naruto"),
    (24, "na_b_05", "Kakashi", "Naruto"),
    (25, "sk_b_01", "Yoh", "Shaman King"),
    (26, "sk_b_02", "Yoh (White Swan)", "Shaman King"),
    (27, "sk_b_03", "Anna", "Shaman King"),
    (28, "jj_b_01", "Jotaro", "JoJo"),
    (29, "jj_b_02", "Dio", "JoJo"),
    (30, "hh_b_01", "Gon", "Hunter x Hunter"),
    (31, "hh_b_02", "Killua", "Hunter x Hunter"),
    (32, "yh_b_01", "Yusuke", "Yu Yu Hakusho"),
    (33, "yh_b_02", "Kurama", "Yu Yu Hakusho"),
    (34, "yh_b_03", "Hiei", "Yu Yu Hakusho"),
    (35, "yo_b_01", "Yugi", "Yu-Gi-Oh!"),
    (36, "rk_b_01", "Kenshin", "Rurouni Kenshin"),
    (37, "bc_b_01", "Train", "Black Cat"),
    (38, "bc_b_02", "Eve", "Black Cat"),
    (39, "bl_b_01", "Ichigo", "Bleach"),
    (40, "bl_b_02", "Bankai Ichigo", "Bleach"),
    (41, "bl_b_03", "Rukia", "Bleach"),
    (42, "bl_b_04", "Renji", "Bleach"),
    (43, "bl_b_05", "Hitsugaya", "Bleach"),
    (44, "bu_b_01", "Kazuki", "Busou Renkin"),
    (45, "dg_b_01", "Allen", "D.Gray-man"),
    (46, "dg_b_02", "Lenalee", "D.Gray-man"),
    (47, "bb_b_01", "Bo-bobo", "Bobobo"),
    (48, "bb_b_02", "Shinsetsu", "Bobobo"),
    (49, "bb_b_03", "Don Patch", "Bobobo"),
    (50, "bb_b_04", "Super Patch", "Bobobo"),
    (51, "kk_b_01", "Ryotsu", "KochiKame"),
    (52, "gt_b_01", "Gintoki", "Gintama"),
    (53, "gt_b_02", "Kagura", "Gintama"),
    (54, "tr_b_01", "Tsuna", "Reborn"),
    (55, "pj_b_01", "Jaguar", "Jaguar"),
    (56, "ds_b_01", "Arale", "Dr. Slump"),
    (57, "ds_b_02", "Mashirito", "Dr. Slump"),
    (58, "ds_b_03", "Caramelman", "Dr. Slump"),
    (59, "my_b_01", "Muhyo", "Muhyo"),
    (60, "hn_b_01", "Kenshiro", "Hokuto no Ken"),
    (61, "hn_b_02", "Raoh", "Hokuto no Ken"),
    (62, "ss_b_01", "Seiya", "Saint Seiya"),
    (63, "ss_b_02", "Gold Seiya", "Saint Seiya"),
    (64, "nr_b_01", "Neuro", "Neuro"),
    (65, "ok_b_01", "Edajima", "Otokojuku"),
    (66, "ok_b_02", "Momotaro", "Otokojuku"),
    (67, "kn_b_01", "Kinnikuman", "Kinnikuman"),
    (68, "he_b_01", "Taikoubou", "Houshin Engi"),
    (69, "nk_b_01", "Fuusuke", "Ninku"),
    (70, "km_b_01", "Komaman Red", "Debug"),
    (71, "km_b_02", "Komaman Yellow", "Debug"),
    (72, "km_b_03", "Komaman Green", "Debug"),
    (73, "km_b_04", "Taizo", "Debug"),
]


@dataclass
class ClassificationResult:
    """Result of analyzing a character's collision file."""
    file_prefix: str
    name: str
    series: str
    total_entries: int
    entries_with_flags: int  # damageFlags > 0
    entries_without_flags: int  # damageFlags = 0
    system: str  # "Direct" or "Indirect"
    ratio: float  # percentage with flags > 0
    flag_values: List[int]  # unique damageFlags values seen


def analyze_collision_file(filepath: Path) -> Tuple[int, int, int, List[int]]:
    """
    Analyze a collision file and count damageFlags distribution.
    
    Returns: (total_entries, entries_with_flags, entries_without_flags, flag_values)
    """
    with open(filepath, 'rb') as f:
        data = f.read()
    
    total_entries = 0
    with_flags = 0
    without_flags = 0
    flag_values = []
    
    offset = 0
    while offset + ENTRY_SIZE <= len(data):
        # Read damageFlags byte
        damage_flags = data[offset + DAMAGE_FLAGS_OFFSET]
        
        # Check for terminator
        if damage_flags == 0xFF:
            break
            
        total_entries += 1
        
        if damage_flags > 0:
            with_flags += 1
            if damage_flags not in flag_values:
                flag_values.append(damage_flags)
        else:
            without_flags += 1
            
        offset += ENTRY_SIZE
    
    return total_entries, with_flags, without_flags, sorted(flag_values)


def classify_character(filepath: Path, char_info: Tuple) -> ClassificationResult:
    """Classify a single character based on collision file analysis."""
    idx, file_prefix, name, series = char_info
    
    total, with_flags, without_flags, flag_values = analyze_collision_file(filepath)
    
    if total == 0:
        ratio = 0.0
        system = "Unknown (no entries)"
    else:
        ratio = (with_flags / total) * 100
        # If more than 50% have flags > 0, it's Direct system
        system = "Direct" if ratio > 50 else "Indirect"
    
    return ClassificationResult(
        file_prefix=file_prefix,
        name=name,
        series=series,
        total_entries=total,
        entries_with_flags=with_flags,
        entries_without_flags=without_flags,
        system=system,
        ratio=ratio,
        flag_values=flag_values
    )


def find_character_info(filename: str) -> Tuple:
    """Find character info by filename prefix."""
    base = Path(filename).stem.lower()
    for char_info in CHARACTER_MAP:
        if char_info[1].lower() == base:
            return char_info
    return None


def main():
    parser = argparse.ArgumentParser(description="Classify characters by damageFlags system")
    parser.add_argument("collision_dir", nargs="?", help="Directory containing collision files")
    parser.add_argument("--single", help="Analyze a single collision file")
    parser.add_argument("--output", "-o", help="Output markdown file")
    args = parser.parse_args()
    
    results = []
    
    if args.single:
        filepath = Path(args.single)
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            return
        
        char_info = find_character_info(filepath.name)
        if not char_info:
            char_info = (0, filepath.stem, filepath.stem, "Unknown")
        
        result = classify_character(filepath, char_info)
        results.append(result)
        
    elif args.collision_dir:
        col_dir = Path(args.collision_dir)
        if not col_dir.exists():
            print(f"Error: Directory not found: {col_dir}")
            return
        
        for filepath in sorted(col_dir.glob("*.bin")):
            char_info = find_character_info(filepath.name)
            if char_info:
                result = classify_character(filepath, char_info)
                results.append(result)
                
    else:
        parser.print_help()
        return
    
    # Output results
    print("\n# DamageFlags Classification Results\n")
    print("| Character | Series | System | Ratio | With Flags | Total | Flag Values |")
    print("|-----------|--------|--------|-------|------------|-------|-------------|")
    
    for r in results:
        flags_str = ", ".join(str(v) for v in r.flag_values[:5])
        if len(r.flag_values) > 5:
            flags_str += "..."
        print(f"| {r.name} | {r.series} | **{r.system}** | {r.ratio:.0f}% | {r.entries_with_flags} | {r.total_entries} | {flags_str} |")
    
    # Summary by series
    print("\n## Summary by Series\n")
    series_data = {}
    for r in results:
        if r.series not in series_data:
            series_data[r.series] = {"direct": 0, "indirect": 0}
        if r.system == "Direct":
            series_data[r.series]["direct"] += 1
        else:
            series_data[r.series]["indirect"] += 1
    
    print("| Series | Direct | Indirect |")
    print("|--------|--------|----------|")
    for series, counts in sorted(series_data.items()):
        print(f"| {series} | {counts['direct']} | {counts['indirect']} |")


if __name__ == "__main__":
    main()
