# ARM9 Disassembly Research Guide

A practical guide for reverse-engineering Jump Ultimate Stars data structures
using ARM9.bin analysis. This document captures the methodology developed during
the Ichigo character mapping deep-dive.

---

## Overview

Jump Ultimate Stars stores game data across multiple interconnected files:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   chr_b.bin ──────► jpower.bin ──────► Damage calculation                   │
│       │                 │                                                    │
│       │                 └──► nextId chains (multi-hit moves)                │
│       │                                                                      │
│       ▼                                                                      │
│   ARM9.bin ──────► Collision file table ──────► ChrBin.aar/chr/col/*.bin    │
│       │                                              │                       │
│       │                                              └──► damageFlags        │
│       │                                              └──► hitboxes           │
│       │                                                                      │
│       └──────► Koma name table ──────► Deck sprite construction             │
│                                                                              │
│   Sprite archives: bl_b_01c.aar, bl_b_01_4c.aar, etc.                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ARM9.bin Key Offsets

These offsets were discovered through pattern matching and cross-referencing
with known data:

| Offset   | Size       | Contents                           | Discovery Method              |
| -------- | ---------- | ---------------------------------- | ----------------------------- |
| 0x0924B0 | ~640 bytes | Collision file pointer table       | Searched for "bl_b_01" string |
| 0x08D4A0 | 74 bytes   | chr_b → collision identity map     | Found near collision table    |
| 0x09E780 | ~200 bytes | Koma name table ("bl", "db", etc.) | Referenced in koma.bin docs   |

### How to Find New Tables

**Step 1: Search for known strings**

```python
# Search ARM9 for character file prefixes
with open('arm9.bin', 'rb') as f:
    arm9 = f.read()

# Find where "bl_b_01" appears
idx = arm9.find(b'bl_b_01')
print(f"Found at offset 0x{idx:X}")
```

**Step 2: Trace pointers backwards**

ARM9 tables often have this structure:

```
[4-byte pointer to string][4-byte extra data]
[4-byte pointer to string][4-byte extra data]
...
```

The pointers are ROM addresses (0x02XXXXXX), convert to file offset:

```python
file_offset = rom_pointer - 0x02000000
```

**Step 3: Look for related data nearby**

Tables are often grouped. If you find the collision table, search ±0x500 bytes
for related index mappings, size tables, or flag arrays.

---

## Collision File Pointer Table (0x0924B0)

### Structure

Each entry is 8 bytes:

```
┌────────────────────────────────────────┐
│ Bytes 0-3: Pointer to filename string  │
│ Bytes 4-7: Extra data (series + index) │
└────────────────────────────────────────┘
```

### Parsing Example

```python
import struct

COLLISION_TABLE = 0x0924B0
ARM9_BASE = 0x02000000

for i in range(80):  # ~80 characters
    offset = COLLISION_TABLE + i * 8
    ptr = struct.unpack_from('<I', arm9, offset)[0]
    extra = struct.unpack_from('<I', arm9, offset + 4)[0]

    # Convert pointer to file offset
    if ptr > ARM9_BASE:
        file_offset = ptr - ARM9_BASE
        # Read null-terminated string
        string_end = arm9.find(b'\x00', file_offset)
        filename = arm9[file_offset:string_end].decode('ascii')
        print(f"[{i:2d}] {filename} - extra=0x{extra:08X}")
```

### Output Pattern

```
[ 0] db_b_01 - extra=0x0005C100   ← Dragon Ball, char 01
[ 1] db_b_02 - extra=0x0005C200
...
[39] bl_b_01 - extra=0x00078100   ← Bleach, char 01 (Ichigo)
[40] bl_b_02 - extra=0x00078200   ← Bleach, char 02 (Bankai)
```

The extra data encodes: `0x000SSCC00` where SS=series, CC=character within
series.

---

## chr_b.bin → Collision Mapping

### Discovery Process

1. **Hypothesis:** chr_b.bin entries map to collision files somehow
2. **Search:** Look for a table of 74 values (chr_b has 74 entries) near the
   collision pointer table
3. **Found:** Identity mapping at 0x08D4A0 - values 0,1,2,3...73

### Verification

```python
# Read 74 bytes starting at 0x8D4A0
identity_table = list(arm9[0x8D4A0:0x8D4A0+74])
print(identity_table)
# Output: [0, 1, 2, 3, 4, ... 73]
```

**Conclusion:** chr_b index = collision table index (direct 1:1 mapping)

This means:

- chr_b[39] → collision[39] → bl_b_01.bin (Ichigo)
- chr_b[40] → collision[40] → bl_b_02.bin (Bankai)

---

## Searching for Unknown Tables

### Pattern: Index Tables

When looking for lookup tables, search for:

1. **Sequential values:** [0, 1, 2, 3, ...] suggests identity or index mapping
2. **Bounded values:** All values in range 0-74 might be chr_b indices
3. **Repeated patterns:** Same value appearing multiple times = shared resource

```python
# Search for potential index tables
for offset in range(0x80000, 0xA0000, 4):
    values = list(arm9[offset:offset+74])

    # Check if all values are valid indices
    if all(0 <= v <= 80 for v in values):
        unique = len(set(values))
        if unique > 20:  # Has diversity
            print(f"Potential table at 0x{offset:X}")
```

### Pattern: Pointer Tables

```python
# Search for tables of ROM pointers
for offset in range(0x80000, 0xA0000, 8):
    ptr = struct.unpack_from('<I', arm9, offset)[0]

    if 0x02000000 < ptr < 0x02100000:
        # Valid ROM pointer, might be start of table
        # Check if next entries are also pointers
        next_ptr = struct.unpack_from('<I', arm9, offset + 8)[0]
        if 0x02000000 < next_ptr < 0x02100000:
            print(f"Pointer table at 0x{offset:X}")
```

---

## Tracing Damage Calculation

### The Ichigo Method

We traced damage by combining multiple data sources:

**Step 1: In-game testing**

```
Ichigo Base B = 10 damage
Bankai B = 9 damage
```

**Step 2: Check chr_b.bin differences**

```
chr_b[39] (Ichigo): tier=2, classId=564
chr_b[40] (Bankai): tier=1, classId=564
```

**Step 3: Check jpower.bin**

```
jpower_block = classId & 0xFF = 52
Block 52 entries have total=50
```

**Step 4: Derive formula**

```
If jpower_total=50 and damage=10: divisor = 5
If tier=1 reduces damage by 1: modifier = tier - 2

Formula: damage = (jpower_total / 5) + (tier - 2)
```

**Step 5: Verify with Bankai**

```
Bankai: 50/5 + (1-2) = 10 - 1 = 9 ✓
```

### Cross-Character Validation

The formula was tested but showed different behavior for Goku:

- Goku (tier=2): B=8, fwd B=7
- jpower Block 0 has total=50
- 50/5 = 10 ≠ 8, but 50/7 ≈ 7 ✓

**Conclusion:** Either different characters use different formulas, OR the
jpower entry selection mechanism varies by character.

---

## Analyzing battleParams (12 bytes)

### Statistical Approach

When a field's purpose is unknown, analyze patterns across all entries:

```python
import base64

# Decode all battleParams
all_params = []
for entry in chr_b_entries:
    bp = list(base64.b64decode(entry['battleParams']))
    all_params.append(bp)

# Analyze each byte position
for byte_idx in range(12):
    values = [bp[byte_idx] for bp in all_params]
    print(f"Byte {byte_idx}: min={min(values)} max={max(values)} "
          f"unique={len(set(values))}")
```

### Discovered Structure

```
┌────────────────────────────────────────────────────────────────┐
│ Bytes 0-7: Four 16-bit parameter slots                         │
│   [low_byte: value (0-50)] + [high_byte: flags (0x00/10/20)]  │
│                                                                 │
│ Bytes 8-10: Stat distribution (sum to ~80-100)                 │
│   Byte 8:  Attack weight (25-100)                              │
│   Byte 9:  Defense weight (0-40)                               │
│   Byte 10: Speed/Utility weight (0-30)                         │
│                                                                 │
│ Byte 11: Special flag (0 or 1)                                 │
└────────────────────────────────────────────────────────────────┘
```

### Key Insight: Comparing Known Characters

Comparing characters with known gameplay differences reveals field meanings:

| Character        | Stats [8,9,10] | Gameplay     |
| ---------------- | -------------- | ------------ |
| Ichigo           | [40,40,20]     | Balanced     |
| Bankai           | [50,35,15]     | Offensive    |
| Death Note chars | [100,0,0]      | Support only |

**Caveat:** Nami and Franky have IDENTICAL battleParams but opposite gameplay
(fast/light vs slow/heavy), proving bytes 0-7 are NOT weight or walk speed.

---

## Collision File Analysis

### Structure (20 bytes per entry)

```c
struct CollisionEntry {
    uint8_t  Type;        // 0: Movement category
    uint8_t  SubType;     // 1: Move variant
    uint8_t  HitTier;     // 2: Priority/tier
    uint8_t  Unknown03;   // 3: Flags?
    uint16_t FrameStart;  // 4-5: Animation frame
    int8_t   Width;       // 6: Hitbox width
    int8_t   Height;      // 7: Hitbox height
    int8_t   OffsetX;     // 8: X offset
    int8_t   OffsetY;     // 9: Y offset
    uint16_t Unknown0A;   // 10-11
    uint16_t Unknown0C;   // 12-13
    uint8_t  DamageFlags; // 14: NOT raw damage!
    uint8_t  Knockback;   // 15: Knockback value
    uint16_t Unknown10;   // 16-17
    uint16_t Unknown12;   // 18-19
};
```

### Critical Discovery: DamageFlags ≠ Damage

In-game testing proved that DamageFlags values do NOT equal actual damage:

| DamageFlags | In-Game Damage |
| ----------- | -------------- |
| 2           | 10             |
| 5           | 10             |
| 3           | 9              |
| 10          | 15             |

**Lesson:** Always validate assumptions with in-game testing!

### Character Collision Differences

Characters vary significantly in collision damage usage:

| Character | Entries with DamageFlags | jpower Reliance             |
| --------- | ------------------------ | --------------------------- |
| Goku      | 2/25                     | Heavy (most from jpower)    |
| Ichigo    | 19/20                    | Light (most from collision) |

This explains why damage formulas appear different - they may use different data
sources entirely.

---

## Searching for Code References

### Finding Field Access

When you know a structure offset (e.g., battleParams at offset 44 in chr_b
entries), search for code that loads from that offset:

```python
# Search for LDRB Rd, [Rn, #44]
for offset in range(0x80000, 0xA0000, 4):
    word = struct.unpack_from('<I', arm9, offset)[0]

    # LDRB with offset 44
    if (word & 0x0FF00FFF) == 0x05D0002C:
        rd = (word >> 12) & 0xF
        rn = (word >> 16) & 0xF
        print(f"0x{offset:X}: LDRB R{rd}, [R{rn}, #44]")
```

### ARM Instruction Patterns

Common patterns to search for:

| Pattern      | Instruction        | Use                    |
| ------------ | ------------------ | ---------------------- |
| `0x05D0002C` | LDRB Rx, [Ry, #44] | Load byte at offset 44 |
| `0x05900000` | LDR Rx, [Ry, #0]   | Load word at base      |
| `0x03A0003C` | MOV Rx, #60        | Entry size constant    |
| `0x0A000000` | B target           | Branch instruction     |

---

## Research Workflow

### Phase 1: Data Export

1. Extract all binary files using JUS CLI tools
2. Export to JSON for easy analysis
3. Create cross-reference maps (chr_b index → collision file → character name)

### Phase 2: Statistical Analysis

1. Analyze field distributions (min/max/unique values)
2. Look for patterns (sums to 100, powers of 2, sequential)
3. Group entries by shared values (charId, classId)

### Phase 3: In-Game Validation

1. Test specific values with known characters
2. Record exact damage numbers
3. Test edge cases (buffs, combos, type advantages)

### Phase 4: ARM9 Tracing

1. Find string references (file names)
2. Trace pointer tables backwards
3. Search for related lookup tables nearby
4. Verify with cross-references

### Phase 5: Documentation

1. Record all confirmed findings
2. Note hypotheses vs proven facts
3. Document what remains unknown
4. Create diagrams showing data flow

---

## Common Pitfalls

### 1. Assuming Direct Mappings

**Wrong:** "chr_b index 39 uses jpower entry 39" **Reality:** chr_b.classId &
0xFF determines jpower block, not chr_b index

### 2. Trusting Field Names in Code

**Wrong:** "DamageFlags contains the damage value" **Reality:** In-game testing
showed these values don't match actual damage

### 3. Universal Formulas

**Wrong:** "All characters use damage = jpower/5" **Reality:** Goku's damage
suggests ÷7, or different entry selection

### 4. jpower Block = Moveset

**Wrong:** "Characters sharing a jpower block share movesets" **Reality:** Majin
Buu uses Block 0 (Goku's block) but has different moves

---

## Tools and Techniques

### Python Analysis Template

```python
import struct
import json
import base64

def load_arm9(path):
    with open(path, 'rb') as f:
        return f.read()

def load_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('entries', data) if isinstance(data, dict) else data

def search_bytes(arm9, pattern, start=0, end=None):
    """Search for byte pattern in ARM9"""
    end = end or len(arm9)
    results = []
    idx = start
    while idx < end:
        idx = arm9.find(pattern, idx)
        if idx == -1 or idx >= end:
            break
        results.append(idx)
        idx += 1
    return results

def read_pointer_table(arm9, offset, count, entry_size=8):
    """Read a table of ROM pointers"""
    entries = []
    for i in range(count):
        ptr = struct.unpack_from('<I', arm9, offset + i * entry_size)[0]
        if ptr > 0x02000000:
            file_offset = ptr - 0x02000000
            # Read string at pointer
            end = arm9.find(b'\x00', file_offset)
            name = arm9[file_offset:end].decode('ascii', errors='replace')
            entries.append((i, name, ptr))
    return entries
```

### Useful CLI Commands

```bash
# Export chr_b.bin to JSON
dotnet run --project src/JUS.CLI -- jus combat export-chr \
    --bin jus_files/ripped_jus_files/bin/chr_b.bin \
    --output /tmp/chr_b.json

# Export jpower.bin to JSON
dotnet run --project src/JUS.CLI -- jus combat export-jpower \
    --bin jus_files/ripped_jus_files/bin/jpower.bin \
    --output /tmp/jpower.json

# Extract ALAR archive
dotnet run --project src/JUS.CLI -- jus containers export \
    --container jus_files/ripped_jus_files/chr/ChrBin.aar \
    --output /tmp/ChrBin_extracted
```

---

## Walk Speed (PARTIALLY SOLVED - 2026-01-30)

### Discovery: statC Controls Walk Speed via Threshold System

The `statC` field in chr_b.bin (offset 12, 2 bytes) determines walk speed,
but NOT linearly. It appears to be a **threshold-based system**:

- **statC < ~100**: SLOW walk speed tier
- **statC >= ~100**: Normal/Fast walk speed tier (same speed regardless of exact value)

### Verified Examples

| Character          | statC | Walk Speed | Notes                        |
| ------------------ | ----- | ---------- | ---------------------------- |
| Zoro (op_b_03)     | 33    | SLOW       | Confirmed very slow          |
| Kyuubi Naruto      | 48    | SLOW       | Confirmed slow               |
| Franky (op_b_08)   | 67    | SLOW       | Confirmed slow               |
| Lenalee (dg_b_02)  | 153   | FAST       | Same speed as Killua!        |
| Goku (db_b_01)     | 161   | Normal     |                              |
| Ichigo (bl_b_01)   | 225   | Normal     |                              |
| Killua (hh_b_02)   | 300   | FAST       | Confirmed fast               |

**Key finding:** Lenalee (statC=153) and Killua (statC=300) have the SAME walk
speed despite very different statC values. This proves statC is NOT linear.

### Slow Characters (statC < 100)

16 battle characters fall into the "slow" tier, including:
- Zoro, Franky (One Piece)
- Kyuubi Naruto (Naruto)
- Kinnikuman
- Kenshiro (Fist of the North Star)

### Important Notes

1. **Support characters** (flags=0, e.g., Death Note) have high statC values
   but don't move in battle - statC is only meaningful for battle characters.

2. **statA and statB are NOT gameplay stats** - they are series-grouped values
   (likely sprite/text offsets), not per-character physics parameters.

3. **battleParams bytes 0-7 are NOT weight** - characters with identical
   battleParams (e.g., op_b_04 and op_b_08) have different walk speeds.

---

## Knockback/Displacement (PARTIALLY UNDERSTOOD)

### Multiple Factors Affect Displacement

Displacement (how far a character is knocked back) is NOT simply statC. It's
affected by multiple factors:

1. **HP**: Lower HP = more displacement
2. **Character passives**: Some characters (e.g., Edajima) have a "hard to
   knock back" passive ability that reduces displacement
3. **Possibly statC**: May still affect base displacement, but not the only factor

### Edajima Example

Edajima (Sakigake!! Otokojuku) has:
- High health pool
- "Hard to knock back" passive ability
- This passive, not base stats, explains his displacement resistance

### What Remains Unknown

- Exact threshold value for walk speed tiers (somewhere around 95-100)
- Whether there are more than 2 speed tiers
- How passives like "hard to knock back" are stored/implemented
- The complete displacement formula

---

## koma.bin Structure (DISCOVERED 2026-01-30)

### Overview

koma.bin contains 890 entries × 12 bytes = 10,680 bytes total. Each entry
represents a "koma" (panel) that can be placed in a deck.

### Structure per Entry

```c
struct Koma {
    uint16_t ImageId;       // 0-1: Sprite/image reference
    uint16_t Unknown2;      // 2-3: Character/series ID (groups komas by character)
    uint8_t  nameIdx;       // 4: Text table index for series name
    uint8_t  nameNum;       // 5: Entry number within series
    uint8_t  KomaType;      // 6: 0=Help, 1=Support, 2=Battle (was Unknown6)
    uint8_t  PassiveIndex;  // 7: Passive ability index (was Unknown7)
    uint8_t  KShapeGroupId; // 8: Koma shape group
    uint8_t  KShapeElementId; // 9: Koma shape element
    uint8_t  UnknownA;      // 10: Unknown
    uint8_t  UnknownB;      // 11: Always 48 or 49 (flags?)
};
```

### Key Discoveries

**KomaType (byte 6):**
- 0 = Help koma (stat booster)
- 1 = Support koma (activatable assist)
- 2 = Battle koma (playable fighter)

**PassiveIndex (byte 7) - IMPORTANT:**
This field indexes into a passive ability table:
- Battle komas (type=2): Values 0-55 (47 unique values)
- Support komas (type=1): Values 92-192 (different ability set)

**NOTE:** Passives are per-form, not per-koma. All koma sizes of the same form
(e.g., 4-koma Goku and 5-koma Goku) share the same passive ability.

### Passive Abilities (Known Types)

From web research, battle passives include:
- Knockback resistance ("Principal" - Edajima)
- SP gain boost on KO (Edajima)
- 3-step jump (triple jump)
- Iron wall (reduced damage?)
- Status abnormality resistance
- Slash/Impact defense
- Auto guard

### Next Steps for Passive Research

1. Map PassiveIndex values to specific passive effects
2. Find the passive definition table in ARM9 (~50 entries for battle, ~100 for support)
3. Verify by testing characters with known passives (Edajima = knockback resist)

---

## What Remains Unknown

### High Priority

1. **jpower entry selection** - How does a move choose which jpower entry to
   use?
2. **Goku B=8 mystery** - No jpower total matches with any known formula
3. **Exact statC formula** - Linear scaling or lookup table for walk speed?

### Medium Priority

1. **komaSize field meaning** - Values 2-6 don't match deck koma sizes 4-8
2. **battleParams slots 0-3** - Low byte values (3-50 range) purpose unknown
3. **Collision subType → jpower mapping** - Does subType select jpower entries?
4. **Dash type determination** - What determines flash dash vs normal dash?

### Where to Look Next

1. **Overlay files** (overlay9_0 through overlay9_13) - May contain character-
   specific code
2. **Effect files** (ChrBin.aar/chr/effect/) - May contain physics parameters
3. **ARM9 code near known tables** - Disassemble functions that reference the
   collision or chr_b tables

---

## Quick Reference

### File Locations

| Data             | File                      | Format                  |
| ---------------- | ------------------------- | ----------------------- |
| Character stats  | bin/chr_b.bin             | 74 entries × 60 bytes   |
| Move power       | bin/jpower.bin            | 311 entries × 304 bytes |
| Collision/hitbox | ChrBin.aar/chr/col/\*.bin | 20 bytes/entry          |
| Koma definitions | bin/koma.bin              | 12 bytes/entry          |
| Character names  | bin/chr_b_t.bin           | Text file               |

### chr_b.bin Key Fields

| Offset | Size | Field    | Purpose                                    |
| ------ | ---- | -------- | ------------------------------------------ |
| 0      | 1    | formType | 0=base, 1=powered, 2=special               |
| 1      | 1    | tier     | Damage modifier: tier-2 added to base dmg  |
| 4      | 4    | flags    | 0=support char, >0=battle char             |
| 12     | 2    | statC    | **Walk speed + knockback resistance**      |
| 14     | 2    | classId  | Low byte = jpower block index              |
| 36     | 12   | battleParams | Character build profile (NOT physics)  |

### Key Formulas

```
jpower_block = chr_b.classId & 0xFF
damage = floor(jpower_total / 5) + (chr_b.tier - 2)  // For Ichigo
damage = floor(jpower_total / 5) + (tier - 2)        // Tentative - divisor 5 observed
attack_boost = 1.2×  // Universal multiplier
nature_advantage = 1.5×  // Type advantage multiplier

// Walk speed (statC field - threshold based, NOT linear)
if statC < ~100: walk_speed = SLOW
if statC >= ~100: walk_speed = NORMAL/FAST  // Same speed tier

// Knockback displacement (multiple factors)
displacement = f(attack_knockback, defender_HP, defender_passives, ...)
// Lower HP = more displacement
// "Hard to knock back" passive reduces displacement
```

### ARM9 Quick Reference

```
0x0924B0 - Collision file pointer table
0x08D4A0 - chr_b → collision identity mapping
0x09E780 - Koma name table
```

---

_Document created from Ichigo character mapping research session, 2026-01-29_
_Updated with walk speed/weight discovery, 2026-01-30_
