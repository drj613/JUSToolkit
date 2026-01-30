#!/usr/bin/env python3
"""
Extract character data from JUS game files.

Reads chr_b.bin and outputs JSON files per character with all extracted data.
Optionally reads collision files from ChrBin.aar (if extracted) and jpower.bin.

Usage:
    python extract_character_data.py --chr-b bin/chr_b.bin --output ./output
    python extract_character_data.py --chr-b bin/chr_b.bin --col-dir col/ --jpower bin/jpower.bin --output ./output
"""

import argparse
import json
import os
import struct
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


# Character mapping from chr_b.bin index to file prefix, character name, and series
# Based on docs/research/chr_b-Complete-Mapping.md
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
    (59, "mr_b_01", "Muhyo", "Muhyo"),
    (60, "nn_b_01", "Neuro", "Neuro"),
    (61, "hk_b_01", "Kenshiro", "Hokuto no Ken"),
    (62, "hk_b_02", "Raoh", "Hokuto no Ken"),
    (63, "ss_b_01", "Seiya", "Saint Seiya"),
    (64, "ss_b_02", "Gold Seiya", "Saint Seiya"),
    (65, "kn_b_01", "Kinnikuman", "Kinnikuman"),
    (66, "oj_b_01", "Momotaro", "Otokojuku"),
    (67, "oj_b_02", "Edajima", "Otokojuku"),
    (68, "hs_b_01", "Taikoubou", "Houshin Engi"),
    (69, "nk_b_01", "Fuusuke", "Ninku"),
    (70, "dt_b_01", "Komaman Red", "Debug"),
    (71, "dt_b_02", "Komaman Yellow", "Debug"),
    (72, "dt_b_03", "Komaman Green", "Debug"),
    (73, "dt_b_04", "Taizo", "Debug"),
]


# Constants from C# code
BATTLE_CHARACTER_ENTRY_SIZE = 60
COLLISION_ENTRY_SIZE = 20
JPOWER_BLOCK_SIZE = 304
JPOWER_SUBRECORD_SIZE = 64


@dataclass
class BattleCharacterEntry:
    """Single battle character entry from chr_b.bin (60 bytes)."""
    form_type: int      # 0=Normal, 1=Powered, 2=Transformed
    tier: int           # Character power tier (1-3)
    koma_size: int      # Panel size in deck (2-6)
    char_id: int        # Character ID within series
    flags: int          # Battle modifier flags (4 bytes)
    stat_a: int         # Primary base stat
    stat_b: int         # Secondary base stat
    stat_c: int         # Tertiary base stat
    class_id: int       # Character class identifier
    combat_stat1_value: int
    combat_stat1_mod: int
    combat_stat2_value: int
    combat_stat2_mod: int
    combat_stat3_value: int
    combat_stat3_mod: int
    combat_stat4_value: int
    combat_stat4_mod: int
    combat_stat5_value: int
    combat_stat5_mod: int
    battle_params: list  # 12 bytes of battle parameters
    text_ids: list       # 6 u16 text IDs


@dataclass
class CollisionEntry:
    """Single collision/hitbox entry (20 bytes)."""
    collision_type: int   # 0-7; 3=standard, 4=strong, 5=special
    sub_type: int         # Move index: 1=jab, 2=combo, 5=launcher, 7=special
    ext_flags: int        # Extended flags (0-3)
    projectile_id: int    # Negative=projectile type, 0=melee
    frame_start: int      # Frame when hitbox activates
    duration_mult: int    # Duration multiplier
    reserved0: int
    hit_modifier: int     # Hit property modifier
    offset_x: int         # Hitbox X position (signed)
    offset_y: int         # Hitbox Y position
    position_flags: int   # 0x00=standard, 0x02=alternate, 0x20=aerial
    reserved1: int
    width: int            # Hitbox width (signed)
    height: int           # Hitbox height (signed)
    damage_flags: int     # Damage flags (0xFF = terminator)
    knockback: int        # Knockback force (0xFF = terminator)
    hit_tier: int         # 0=passive, 1=light, 2=medium, 3=heavy
    hit_properties: int   # Additional hit properties
    reserved2: int
    reserved3: int


@dataclass
class JPowerEntry:
    """Single jpower entry (304 byte block, parsed main record)."""
    id: int
    type1: int            # 0=data-only, 1=attack definition
    type2: int            # Attack subtype: 1=standard, 7=projectile, 8=heavy, 9=special, 10=super
    next_id: int          # Linked record ID
    damage1: int          # Punch/kick damage
    damage2: int          # Energy/ki damage
    damage3: int          # Blade damage
    hitstun: int          # Hitstun frames
    link_type: int        # Link category type
    link_category: int    # Category code
    link_flags: int       # Additional flags
    extended_data: list   # 16 bytes
    has_modifier: bool
    modifier_damage1: int
    modifier_damage2: int
    modifier_damage3: int
    modifier_effect: int
    raw_block: Optional[bytes] = None


def read_battle_character_entry(data: bytes, offset: int) -> BattleCharacterEntry:
    """Read a single BattleCharacterEntry from binary data."""
    # Unpack fields (little-endian)
    form_type = data[offset]
    tier = data[offset + 1]
    koma_size = data[offset + 2]
    char_id = data[offset + 3]
    flags = struct.unpack_from('<I', data, offset + 4)[0]
    stat_a = struct.unpack_from('<H', data, offset + 8)[0]
    stat_b = struct.unpack_from('<H', data, offset + 10)[0]
    stat_c = struct.unpack_from('<H', data, offset + 12)[0]
    class_id = struct.unpack_from('<H', data, offset + 14)[0]

    # Combat stats (5 pairs of value + modifier)
    combat_stat1_value = struct.unpack_from('<H', data, offset + 16)[0]
    combat_stat1_mod = struct.unpack_from('<H', data, offset + 18)[0]
    combat_stat2_value = struct.unpack_from('<H', data, offset + 20)[0]
    combat_stat2_mod = struct.unpack_from('<H', data, offset + 22)[0]
    combat_stat3_value = struct.unpack_from('<H', data, offset + 24)[0]
    combat_stat3_mod = struct.unpack_from('<H', data, offset + 26)[0]
    combat_stat4_value = struct.unpack_from('<H', data, offset + 28)[0]
    combat_stat4_mod = struct.unpack_from('<H', data, offset + 30)[0]
    combat_stat5_value = struct.unpack_from('<H', data, offset + 32)[0]
    combat_stat5_mod = struct.unpack_from('<H', data, offset + 34)[0]

    # Battle params (12 bytes)
    battle_params = list(data[offset + 36:offset + 48])

    # Text IDs (6 u16)
    text_ids = list(struct.unpack_from('<6H', data, offset + 48))

    return BattleCharacterEntry(
        form_type=form_type,
        tier=tier,
        koma_size=koma_size,
        char_id=char_id,
        flags=flags,
        stat_a=stat_a,
        stat_b=stat_b,
        stat_c=stat_c,
        class_id=class_id,
        combat_stat1_value=combat_stat1_value,
        combat_stat1_mod=combat_stat1_mod,
        combat_stat2_value=combat_stat2_value,
        combat_stat2_mod=combat_stat2_mod,
        combat_stat3_value=combat_stat3_value,
        combat_stat3_mod=combat_stat3_mod,
        combat_stat4_value=combat_stat4_value,
        combat_stat4_mod=combat_stat4_mod,
        combat_stat5_value=combat_stat5_value,
        combat_stat5_mod=combat_stat5_mod,
        battle_params=battle_params,
        text_ids=text_ids,
    )


def read_collision_entry(data: bytes, offset: int) -> CollisionEntry:
    """Read a single CollisionEntry from binary data."""
    collision_type = data[offset]
    sub_type = data[offset + 1]
    ext_flags = data[offset + 2]
    projectile_id = struct.unpack_from('<b', data, offset + 3)[0]  # signed byte
    frame_start = data[offset + 4]
    duration_mult = data[offset + 5]
    reserved0 = data[offset + 6]
    hit_modifier = data[offset + 7]
    offset_x = struct.unpack_from('<b', data, offset + 8)[0]  # signed byte
    offset_y = data[offset + 9]
    position_flags = data[offset + 10]
    reserved1 = data[offset + 11]
    width = struct.unpack_from('<b', data, offset + 12)[0]  # signed byte
    height = struct.unpack_from('<b', data, offset + 13)[0]  # signed byte
    damage_flags = data[offset + 14]
    knockback = data[offset + 15]
    hit_tier = data[offset + 16]
    hit_properties = data[offset + 17]
    reserved2 = data[offset + 18]
    reserved3 = data[offset + 19]

    return CollisionEntry(
        collision_type=collision_type,
        sub_type=sub_type,
        ext_flags=ext_flags,
        projectile_id=projectile_id,
        frame_start=frame_start,
        duration_mult=duration_mult,
        reserved0=reserved0,
        hit_modifier=hit_modifier,
        offset_x=offset_x,
        offset_y=offset_y,
        position_flags=position_flags,
        reserved1=reserved1,
        width=width,
        height=height,
        damage_flags=damage_flags,
        knockback=knockback,
        hit_tier=hit_tier,
        hit_properties=hit_properties,
        reserved2=reserved2,
        reserved3=reserved3,
    )


def read_jpower_entry(data: bytes, offset: int) -> JPowerEntry:
    """Read a single JPowerEntry from binary data (304-byte block)."""
    # Main record fields
    id_val = struct.unpack_from('<H', data, offset)[0]
    # offset + 2: reserved
    type1 = struct.unpack_from('<H', data, offset + 4)[0]
    type2 = struct.unpack_from('<H', data, offset + 6)[0]
    next_id = struct.unpack_from('<H', data, offset + 8)[0]
    # offset + 10: reserved
    damage1 = struct.unpack_from('<H', data, offset + 12)[0]
    damage2 = struct.unpack_from('<H', data, offset + 14)[0]
    damage3 = struct.unpack_from('<H', data, offset + 16)[0]
    # offset + 18-20: reserved
    hitstun = struct.unpack_from('<H', data, offset + 22)[0]
    link_type = struct.unpack_from('<H', data, offset + 24)[0]
    link_category = struct.unpack_from('<H', data, offset + 26)[0]
    link_flags = struct.unpack_from('<H', data, offset + 28)[0]
    # offset + 30: reserved
    extended_data = list(data[offset + 32:offset + 48])

    # Check for modifier sub-record at offset 0x40
    has_modifier = False
    modifier_damage1 = 0
    modifier_damage2 = 0
    modifier_damage3 = 0
    modifier_effect = 0

    if data[offset + 64] == 0x02 and data[offset + 65] == 0x00:
        has_modifier = True
        modifier_damage1 = struct.unpack_from('<H', data, offset + 64 + 8)[0]
        modifier_damage2 = struct.unpack_from('<H', data, offset + 64 + 10)[0]
        modifier_damage3 = struct.unpack_from('<H', data, offset + 64 + 12)[0]
        # offset + 78-80: reserved
        modifier_effect = struct.unpack_from('<H', data, offset + 64 + 18)[0]

    raw_block = bytes(data[offset:offset + JPOWER_BLOCK_SIZE])

    return JPowerEntry(
        id=id_val,
        type1=type1,
        type2=type2,
        next_id=next_id,
        damage1=damage1,
        damage2=damage2,
        damage3=damage3,
        hitstun=hitstun,
        link_type=link_type,
        link_category=link_category,
        link_flags=link_flags,
        extended_data=extended_data,
        has_modifier=has_modifier,
        modifier_damage1=modifier_damage1,
        modifier_damage2=modifier_damage2,
        modifier_damage3=modifier_damage3,
        modifier_effect=modifier_effect,
        raw_block=raw_block,
    )


def read_chr_b(filepath: str) -> list:
    """Read all entries from chr_b.bin."""
    with open(filepath, 'rb') as f:
        data = f.read()

    entry_count = len(data) // BATTLE_CHARACTER_ENTRY_SIZE
    entries = []

    for i in range(entry_count):
        offset = i * BATTLE_CHARACTER_ENTRY_SIZE
        entries.append(read_battle_character_entry(data, offset))

    return entries


def read_collision_file(filepath: str) -> list:
    """Read all entries from a collision .bin file."""
    with open(filepath, 'rb') as f:
        data = f.read()

    entry_count = len(data) // COLLISION_ENTRY_SIZE
    entries = []

    for i in range(entry_count):
        offset = i * COLLISION_ENTRY_SIZE
        entry = read_collision_entry(data, offset)
        entries.append(entry)
        # Check for terminator
        if entry.damage_flags == 0xFF or entry.knockback == 0xFF:
            break

    return entries


def read_jpower(filepath: str) -> list:
    """Read all entries from jpower.bin."""
    with open(filepath, 'rb') as f:
        data = f.read()

    block_count = len(data) // JPOWER_BLOCK_SIZE
    entries = []

    for i in range(block_count):
        offset = i * JPOWER_BLOCK_SIZE
        entries.append(read_jpower_entry(data, offset))

    return entries


def find_collision_file(col_dir: str, file_prefix: str) -> Optional[str]:
    """Find collision file for a character prefix."""
    # Try exact match first
    col_path = Path(col_dir) / f"{file_prefix}.bin"
    if col_path.exists():
        return str(col_path)

    # Try with col/ subdirectory
    col_path = Path(col_dir) / "col" / f"{file_prefix}.bin"
    if col_path.exists():
        return str(col_path)

    return None


def collision_entry_to_dict(entry: CollisionEntry) -> dict:
    """Convert CollisionEntry to dictionary."""
    return {
        "collision_type": entry.collision_type,
        "sub_type": entry.sub_type,
        "ext_flags": entry.ext_flags,
        "projectile_id": entry.projectile_id,
        "frame_start": entry.frame_start,
        "duration_mult": entry.duration_mult,
        "hit_modifier": entry.hit_modifier,
        "offset_x": entry.offset_x,
        "offset_y": entry.offset_y,
        "position_flags": entry.position_flags,
        "width": entry.width,
        "height": entry.height,
        "damage_flags": entry.damage_flags,
        "knockback": entry.knockback,
        "hit_tier": entry.hit_tier,
        "hit_properties": entry.hit_properties,
        "is_terminator": entry.damage_flags == 0xFF or entry.knockback == 0xFF,
    }


def jpower_entry_to_dict(entry: JPowerEntry) -> dict:
    """Convert JPowerEntry to dictionary (without raw_block)."""
    return {
        "id": entry.id,
        "type1": entry.type1,
        "type2": entry.type2,
        "next_id": entry.next_id,
        "damage1": entry.damage1,
        "damage2": entry.damage2,
        "damage3": entry.damage3,
        "total_damage": entry.damage1 + entry.damage2 + entry.damage3,
        "hitstun": entry.hitstun,
        "link_type": entry.link_type,
        "link_category": entry.link_category,
        "link_flags": entry.link_flags,
        "extended_data": entry.extended_data,
        "has_modifier": entry.has_modifier,
        "modifier_damage1": entry.modifier_damage1,
        "modifier_damage2": entry.modifier_damage2,
        "modifier_damage3": entry.modifier_damage3,
        "modifier_effect": entry.modifier_effect,
        "is_attack": entry.type1 == 1,
        "category_name": get_category_name(entry.type2),
    }


def get_category_name(type2: int) -> str:
    """Get attack category name from type2."""
    names = {
        0: "Data",
        1: "Standard",
        2: "Variation2",
        3: "Variation3",
        4: "Variation4",
        5: "Variation5",
        7: "Projectile",
        8: "Heavy",
        9: "Special",
        10: "Super",
    }
    return names.get(type2, f"Unknown({type2})")


def build_character_json(
    index: int,
    chr_b_entry: BattleCharacterEntry,
    collision_entries: Optional[list],
    jpower_entries: Optional[list],
) -> dict:
    """Build character JSON data structure."""
    file_prefix = CHARACTER_MAP[index][1]
    character_name = CHARACTER_MAP[index][2]
    series = CHARACTER_MAP[index][3]

    # Calculate jpower block index from classId
    jpower_block = chr_b_entry.class_id & 0xFF

    result = {
        "chr_b_index": index,
        "file_prefix": file_prefix,
        "character_name": character_name,
        "series": series,
        "charId": chr_b_entry.char_id,
        "formType": chr_b_entry.form_type,
        "tier": chr_b_entry.tier,
        "komaSize": chr_b_entry.koma_size,
        "classId": chr_b_entry.class_id,
        "jpower_block": jpower_block,
        "flags": chr_b_entry.flags,
        "stats": {
            "statA": chr_b_entry.stat_a,
            "statB": chr_b_entry.stat_b,
            "statC": chr_b_entry.stat_c,
        },
        "combatStats": {
            "stat1": {"value": chr_b_entry.combat_stat1_value, "modifier": chr_b_entry.combat_stat1_mod},
            "stat2": {"value": chr_b_entry.combat_stat2_value, "modifier": chr_b_entry.combat_stat2_mod},
            "stat3": {"value": chr_b_entry.combat_stat3_value, "modifier": chr_b_entry.combat_stat3_mod},
            "stat4": {"value": chr_b_entry.combat_stat4_value, "modifier": chr_b_entry.combat_stat4_mod},
            "stat5": {"value": chr_b_entry.combat_stat5_value, "modifier": chr_b_entry.combat_stat5_mod},
        },
        "battleParams": {
            "raw": chr_b_entry.battle_params,
            # Known interpretations from research
            "byte0": chr_b_entry.battle_params[0],  # Unknown
            "byte1": chr_b_entry.battle_params[1],  # Unknown
            "byte2": chr_b_entry.battle_params[2],  # Unknown
            "byte3": chr_b_entry.battle_params[3],  # Unknown
            "byte4": chr_b_entry.battle_params[4],  # Unknown
            "byte5": chr_b_entry.battle_params[5],  # Unknown
            "byte6": chr_b_entry.battle_params[6],  # Unknown
            "byte7": chr_b_entry.battle_params[7],  # Unknown
            "attack": chr_b_entry.battle_params[8],   # Attack weight
            "defense": chr_b_entry.battle_params[9],  # Defense weight
            "speed": chr_b_entry.battle_params[10],   # Speed modifier
            "byte11": chr_b_entry.battle_params[11],  # Unknown
        },
        "textIds": chr_b_entry.text_ids,
    }

    # Add collision data if available
    if collision_entries:
        result["collision"] = {
            "entry_count": len(collision_entries),
            "entries": [collision_entry_to_dict(e) for e in collision_entries],
        }
    else:
        result["collision"] = None

    # Add jpower data if available
    if jpower_entries and jpower_block < len(jpower_entries):
        jpower_entry = jpower_entries[jpower_block]
        result["jpower"] = jpower_entry_to_dict(jpower_entry)
    else:
        result["jpower"] = None

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Extract character data from JUS game files"
    )
    parser.add_argument(
        "--chr-b",
        required=True,
        help="Path to chr_b.bin file",
    )
    parser.add_argument(
        "--col-dir",
        help="Path to collision files directory (optional)",
    )
    parser.add_argument(
        "--jpower",
        help="Path to jpower.bin file (optional)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for JSON files",
    )
    parser.add_argument(
        "--single",
        type=int,
        help="Export only character at this chr_b index",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read chr_b.bin
    print(f"Reading chr_b.bin from {args.chr_b}...")
    chr_b_entries = read_chr_b(args.chr_b)
    print(f"  Found {len(chr_b_entries)} battle character entries")

    # Read jpower.bin if provided
    jpower_entries = None
    if args.jpower:
        print(f"Reading jpower.bin from {args.jpower}...")
        jpower_entries = read_jpower(args.jpower)
        print(f"  Found {len(jpower_entries)} jpower blocks")

    # Process each character
    indices = [args.single] if args.single is not None else range(len(chr_b_entries))

    for i in indices:
        if i >= len(CHARACTER_MAP):
            print(f"Warning: No mapping for chr_b index {i}, skipping")
            continue

        chr_b_entry = chr_b_entries[i]
        file_prefix = CHARACTER_MAP[i][1]
        character_name = CHARACTER_MAP[i][2]

        # Try to read collision file if col_dir provided
        collision_entries = None
        if args.col_dir:
            col_path = find_collision_file(args.col_dir, file_prefix)
            if col_path:
                collision_entries = read_collision_file(col_path)
                print(f"  Found collision file: {col_path} ({len(collision_entries)} entries)")

        # Build character JSON
        char_json = build_character_json(
            i,
            chr_b_entry,
            collision_entries,
            jpower_entries,
        )

        # Write output file
        output_path = output_dir / f"{file_prefix}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(char_json, f, indent=2, ensure_ascii=False)

        print(f"  [{i:02d}] {character_name:20s} -> {output_path}")

    print(f"\nExport complete! Files written to: {output_dir}")

    # Write summary file
    summary = {
        "total_characters": len(chr_b_entries),
        "exported_characters": len(list(indices)),
        "has_collision_data": args.col_dir is not None,
        "has_jpower_data": args.jpower is not None,
        "character_list": [
            {
                "index": i,
                "file_prefix": CHARACTER_MAP[i][1],
                "name": CHARACTER_MAP[i][2],
                "series": CHARACTER_MAP[i][3],
            }
            for i in range(min(len(chr_b_entries), len(CHARACTER_MAP)))
        ],
    }

    summary_path = output_dir / "_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Summary written to: {summary_path}")


if __name__ == "__main__":
    main()
