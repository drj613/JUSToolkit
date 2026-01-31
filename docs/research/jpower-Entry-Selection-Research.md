# jpower Entry Selection Mechanism - Research Summary

**Date:** 2026-01-31  
**Status:** Partially Resolved - Two Distinct Systems Identified

---

## Executive Summary

Collision files use **two distinct systems** to select jpower entries for damage calculation:

1. **Direct Reference System** (Ichigo pattern): `damageFlags` = global jpower array index
2. **Indirect Lookup System** (Goku pattern): `damageFlags=0` triggers alternative lookup mechanism

The selection mechanism is **character-dependent** and not uniform across all characters.

---

## Key Findings

### 1. What is `damageFlags` and Where is it Located?

**Location:** `CollisionEntry` structure, byte offset 0x0E (14) in collision files

**Field Definition:**
- **Type:** `byte` (unsigned 8-bit integer)
- **Size:** 1 byte
- **Range:** 0-255 (0xFF = terminator entry)
- **Special Values:**
  - `0xFF` = Terminator entry (marks end of collision data)
  - `0x40` (64) = Buff trigger flag (Yusuke, Ichigo buff system)
  - `0` = Triggers indirect lookup mechanism (for some characters)

**Code Reference:** `src/JUS.Tool/Combat/Formats/CollisionEntry.cs` line 99

```csharp
/// <summary>
/// Gets or sets the damage flags.
/// WARNING: This is NOT raw damage! In-game testing shows collision damageFlags
/// values (2,5,3,8,10,14) do not match actual damage (10,10,9,10,15,18).
/// This field likely encodes a modifier type, index, or effect reference.
/// 0xFF = terminator entry.
/// </summary>
public byte DamageFlags { get; set; }
```

---

### 2. How Does damageFlags=0 Differ from damageFlags>0?

#### System 1: Direct jpower Reference (damageFlags > 0)

**Pattern:** Characters like Ichigo use `damageFlags` as a **direct global jpower array index**.

**Evidence:**
- **Ichigo (bl_b_01):** 19/20 collision entries have `damageFlags > 0`
- **Example:** `damageFlags=2` → `jpower[2]` (ID=6, damage1=50) → 50/5=10 damage ✓
- **Verified:** All Ichigo moves match jpower entries at the specified array indices

**How it works:**
```
damageFlags = 2
→ jpower array index = 2
→ jpower[2].damage1 = 50
→ damage = (50 / 5) + (tier - 2) = 10 + 0 = 10 ✓
```

**Characteristics:**
- `damageFlags` directly points to a jpower entry in the global array
- No additional lookup required
- Works independently of jpower block assignment

#### System 2: Indirect Lookup (damageFlags = 0)

**Pattern:** Characters like Goku use `damageFlags=0` to trigger an **alternative lookup mechanism**.

**Evidence:**
- **Goku (db_b_01):** Only 2/25 collision entries have `damageFlags > 0`
- **All B attacks:** `damageFlags=0`, `subType=1`, `hitTier=2`
- **Goku B=8** requires jpower with `damage1=40` (not in Block 0)
- **damageFlags=0 does NOT mean jpower[0]** (that would give 50/5=10, not 8)

**jpower Entries with damage1=40:**
| Array Index | jpower ID | linkCategory | Notes |
|-------------|-----------|--------------|-------|
| 146 | 379 | 1 | First entry with damage1=40 |
| 195 | 539 | 1 | Same linkCategory |
| 218 | 604 | 1 | Same linkCategory |

**Characteristics:**
- `damageFlags=0` triggers unknown lookup mechanism
- Likely uses `subType`, `hitTier`, `collisionType`, or ARM9 lookup table
- May involve character-specific offsets or mappings
- Accesses jpower entries outside the assigned block

**Hypothesis:** When `damageFlags=0`, the game:
1. Uses `classId` to get jpower block index
2. Combines with `subType`/`hitTier`/other fields to select entry within block
3. OR uses an ARM9 lookup table mapping collision properties → jpower index
4. OR uses character-specific offset calculations

---

### 3. What Determines Which jpower Entry a Move Uses?

The selection mechanism depends on which system the character uses:

#### For Direct Reference Characters (Ichigo pattern):
```
jpower_entry_index = damageFlags
```

**Simple and direct:** The `damageFlags` value IS the jpower array index.

#### For Indirect Lookup Characters (Goku pattern):
```
jpower_entry_index = lookup_function(
    classId,           // Points to jpower block
    subType,           // Move type (1=jab, 2=combo, etc.)
    hitTier,           // Attack strength (0-3)
    collisionType,     // Hitbox type (2-5)
    character_index    // Possibly chr_b index
)
```

**Unknown function:** The exact lookup mechanism is not yet discovered.

**Possible factors:**
1. **subType mapping:** `subType=1` (B attacks) might map to specific jpower entries
2. **hitTier selection:** Different tiers might select different entries
3. **linkCategory matching:** Goku's entries with `damage1=40` all have `linkCategory=1`
4. **ARM9 lookup table:** Character-specific table mapping collision properties → jpower index
5. **Block-relative indexing:** Entry index within the assigned jpower block

---

## Character Distribution

### Direct Reference System Users
- **Ichigo (bl_b_01):** 19/20 entries with `damageFlags > 0`
- **Bankai Ichigo (bl_b_02):** Likely similar pattern (needs verification)

### Indirect Lookup System Users
- **Goku (db_b_01):** 2/25 entries with `damageFlags > 0`
- **Naruto:** B=8 damage, likely uses same system as Goku
- **Luffy, Robin, Franky, Nami:** All B=8 damage, likely indirect system

### Indirect Lookup System Users (continued)
- **Majin Buu:** B=9 damage, uses jpower entry with `damage1=45` (confirmed, not anomaly)
  - Originally thought to be anomaly because no jpower entry has *total*=45
  - Resolution: Formula uses `damage1` only, and entries with `damage1=45` exist

---

## Critical Observations

### 1. jpower Blocks are Template Libraries

**Key Finding:** Characters sharing the same jpower block have **different movesets**.

**Examples:**
- Goku and Majin Buu both use Block 0, but completely different attacks
- Luffy and Robin both use Block 9, but different movesets
- Nami and Franky both use Block 12, but different movesets

**Implication:** jpower blocks contain a **library of potential moves**, and each character selects a subset. The selection mechanism determines which entries each character actually uses.

### 2. Block Assignment vs Entry Selection

**Block Assignment (CONFIRMED):**
```
jpower_block_index = classId & 0xFF
```

**Entry Selection (PARTIALLY UNKNOWN):**
- Direct system: `damageFlags` = global array index
- Indirect system: Unknown function of collision properties

### 3. damageFlags Special Values

| Value | Meaning | System |
|-------|---------|--------|
| `0xFF` | Terminator entry | Both |
| `0x40` (64) | Buff trigger | Both |
| `0` | Indirect lookup | Indirect system only |
| `> 0` | Direct jpower index | Direct system |

---

## Verified Examples

### Ichigo (Direct System)
| Collision Entry | damageFlags | jpower Index | jpower.damage1 | Calculated Damage | Actual Damage |
|----------------|-------------|--------------|----------------|-------------------|---------------|
| B attack | 2 | jpower[2] | 50 | 50/5+0=10 | 10 ✓ |
| Combo | 5 | jpower[5] | 50 | 50/5+0=10 | 10 ✓ |
| Combo | 3 | jpower[3] | 45 | 45/5+0=9 | 9 ✓ |

### Goku (Indirect System)
| Move | damageFlags | subType | hitTier | Required damage1 | Actual Damage | jpower Entry |
|------|-------------|---------|---------|------------------|---------------|--------------|
| B | 0 | 1 | 2 | 40 | 8 | Unknown (indices 146, 195, 218) |
| Combo | 0 | 2 | 2 | ? | ? | Unknown |
| Y attack | 14 | 7 | ? | ? | 14 | Unknown |

---

## Research Gaps

### High Priority Questions

1. **Indirect lookup function:** What is the exact formula/table for `damageFlags=0`?
   - Does it use `subType` + `hitTier`?
   - Is there an ARM9 lookup table?
   - Does it involve character-specific offsets?

2. ~~**Majin Buu anomaly:**~~ **SOLVED** - Buu uses entry with `damage1=45`
   - Original confusion: thought formula used total damage (no entry has *total*=45)
   - Resolution: Formula uses `damage1` only, entries with `damage1=45` exist
   - Now classified as indirect lookup system user like Goku

3. **Character classification:** Which characters use which system?
   - Need to analyze more collision files
   - Determine if system correlates with series, tier, or other factors

4. **Multi-hit moves:** How do combos (Y 4+4+6, up B 3+3) work?
   - Do they use `nextId` chains in jpower?
   - Multiple collision entries?
   - Special handling?

### Medium Priority Questions

5. **Block-relative indexing:** When `damageFlags=0`, does it select entries within the assigned block?
   - Goku uses Block 0 (indices 0-8), but needs entries at 146, 195, 218
   - Suggests global array access, not block-relative

6. **linkCategory role:** Do entries with same `linkCategory` get selected together?
   - Goku's `damage1=40` entries all have `linkCategory=1`
   - Coincidence or selection criteria?

---

## Next Research Steps

### Immediate Actions

1. **ARM9 code analysis:**
   - Search for collision entry processing code
   - Look for `damageFlags` checks (if `damageFlags == 0` branch)
   - Find jpower lookup functions

2. **Character pattern analysis:**
   - Extract collision data for all 74 characters
   - Classify each character by system (direct vs indirect)
   - Look for patterns (series, tier, block assignment)

3. **Goku B move deep dive:**
   - Identify which jpower entry Goku B actually uses
   - Check if it's always the same entry (index 146?)
   - Verify if other Goku moves use same entry

4. ~~**Majin Buu investigation:**~~ **RESOLVED**
   - Buu uses standard `damage1/5 + (tier-2)` formula
   - Uses jpower entry with `damage1=45` → 45/5+0=9 ✓
   - No character-specific exception needed

### Analysis Tools Needed

1. **Collision-to-jpower mapper:**
   - Script to extract collision entries with `damageFlags=0`
   - Match against jpower entries by `damage1` value
   - Identify selection patterns

2. **Character classification tool:**
   - Analyze all collision files
   - Count `damageFlags=0` vs `damageFlags>0` entries
   - Generate classification report

3. **ARM9 disassembler analysis:**
   - Search for collision entry processing
   - Find jpower lookup functions
   - Reverse engineer selection logic

---

## Related Documentation

- **Research Status:** `docs/research/Research-Status.md` - "jpower Entry-to-Move Mapping" section
- **jpower Mapping:** `docs/research/jpower-Mapping.md` - Block assignment and structure
- **Damage Formula:** `docs/research/Damage-Formula-Predictions.md` - Confirmed formula
- **Character Maps:** `docs/characters/*-Character-Map.md` - Individual character analysis
- **Format Definitions:** `src/JUS.Tool/Combat/Formats/CollisionEntry.cs` - Code structure

---

## Conclusion

The jpower entry selection mechanism uses **two distinct systems**:

1. **Direct Reference:** `damageFlags` = global jpower array index (Ichigo pattern)
2. **Indirect Lookup:** `damageFlags=0` triggers alternative mechanism (Goku pattern)

The indirect lookup system remains **partially unknown** and requires:
- ARM9 code analysis to find the lookup function
- More character pattern analysis to identify selection criteria
- Investigation of edge cases (Majin Buu anomaly)

**Key Insight:** The system is character-dependent, not uniform. Understanding which characters use which system is critical for accurate damage prediction and move analysis.

---

_Research compiled: 2026-01-31_