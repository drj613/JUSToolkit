# Goku (db_b_01) - Complete Character Mapping

Deep dive analysis mapping Goku through all data files to understand linkages.

---

## ✓ CONFIRMED - In-Game Verified Data (2026-01-29)

### Damage Values (Tested vs Nature)

**Neutral damage (no nature advantage):** | Move | Damage | Type | Notes |
|------|--------|------|-------| | B | 8 | Punch/Kick | Single hit | | fwd B | 7
| Punch/Kick | Single hit | | up B | 3+3 | Punch/Kick | 2 hits | | down B | 7 |
Punch/Kick | Single hit | | Y | 4+4+6 | Punch/Kick | 3-hit combo | | fwd Y |
5+5+5 | Energy | Can shoot up to 3 projectiles | | up Y | 14 | Punch/Kick |
Single hit | | down Y | 14 | Punch/Kick | Single hit |

**Advantage damage (1.5× nature multiplier):** | Move | Damage | Calculation |
Verified | |------|--------|-------------|----------| | B | 12 | 8 × 1.5 = 12 |
✓ | | fwd B | 10 | 7 × 1.5 = 10.5 → 10 | ✓ | | up B | 4+5 | 3 × 1.5 = 4.5 → 4,
then 5 | ✓ | | down B | 10 | 7 × 1.5 = 10.5 → 10 | ✓ | | Y | 6+6+9 | 4 × 1.5 =
6, 6 × 1.5 = 9 | ✓ | | fwd Y | 7+8+7 | Variable per projectile | ✓ | | up Y | 21
| 14 × 1.5 = 21 | ✓ | | down Y | 21 | 14 × 1.5 = 21 | ✓ |

**Confirmed:**

- **Nature advantage = 1.5× multiplier** (verified across all moves)
- **No disadvantage penalty** (bonus-only system)
- **Rounding uses floor function**

### File Mapping (ARM9 Pointer Table)

**chr_b.bin entry 0:**

- File: db_b_01
- charId: 7
- tier: 2
- komaSize: 3
- classId: 256
- jpower block: 0 (classId & 0xFF)

**Collision file:**

- db_b_01.bin: 25 entries
- Contains hitbox data, knockback, frame timing
- 2/25 entries have damage>0 (most reference jpower)

**Deck komas:**

- Base Goku: 4, 5
- Goku SSJ: 6, 7 (db_b_02, different chr_b entry)
- Vegetto: 8 (db_b_03, different chr_b entry)

**Character variants:**

- db_b_01 (chr_b[0]): Base Goku
- db_b_02 (chr_b[1]): Goku SSJ - same moveset except specials
- db_b_03 (chr_b[2]): Vegetto - different character

---

## ⚠️ LIKELY TRUE - Evidence Exists But Incomplete

### jpower Block 0 Structure

**9 attack entries (indices 0-8):**

| Entry | jpower ID | d1  | d2  | d3  | Total | With ÷7 Formula | With ÷5 Formula | hitstun |
| ----- | --------- | --- | --- | --- | ----- | --------------- | --------------- | ------- |
| 0     | 0         | 30  | 20  | 0   | 50    | **7 damage**    | 10 damage       | 5       |
| 1     | 3         | 10  | 40  | 0   | 50    | **7 damage**    | 10 damage       | 0       |
| 2     | 6         | 50  | 0   | 0   | 50    | **7 damage**    | 10 damage       | 5       |
| 3     | 9         | 30  | 0   | 20  | 50    | **7 damage**    | 10 damage       | 5       |
| 4     | 12        | 25  | 25  | 0   | 50    | **7 damage**    | 10 damage       | 5       |
| 5     | 15        | 20  | 0   | 30  | 50    | **7 damage**    | 10 damage       | 5       |
| 6     | 18        | 25  | 25  | 0   | 50    | **7 damage**    | 10 damage       | 5       |
| 7     | 21        | 60  | 40  | 0   | 100   | **14 damage**   | 20 damage       | 10      |
| 8     | 23        | 100 | 0   | 0   | 100   | **14 damage**   | 20 damage       | 10      |

**With ÷7 formula:**

- 7 entries match tested 7-damage moves (fwd B, down B) ✓
- 2 entries match tested 14-damage moves (up Y, down Y) ✓
- Missing: B=8, multi-hits

**With ÷5 + tier formula:**

- All entries would give 10 damage (wrong for Goku's 7-damage moves)
- Doesn't match any of Goku's tested values

**Tentative conclusion:** Goku uses **÷7 formula**, conflicting with Ichigo
doc's ÷5 formula.

### Shared jpower Block

**Characters using Block 0:**

- db_b_01 (Goku) - chr_b[0], classId=256
- db_b_02 (Goku SSJ) - chr_b[1], classId=256
- db_b_12 (Majin Buu) - chr_b[11], classId=256

**Goku and SSJ share moveset** (user confirmed).

**Majin Buu has different moveset** but uses same block (selection mechanism
unknown).

---

## ❓ UNKNOWN - No Clear Evidence

### Missing Move Data

**Moves not found in jpower Block 0:**

1. **B (8 damage)**
   - Expected jpower total: 56 (with ÷7) or 40 (with ÷5)
   - NOT FOUND in Block 0 or anywhere in jpower.bin

2. **up B hits (3 damage each)**
   - Expected: total ≈ 21 each
   - NOT FOUND

3. **Y combo hits (4+4+6 damage)**
   - Expected: totals ≈ 28, 28, 42
   - NOT FOUND

4. **fwd Y projectiles (5 damage each)**
   - Expected: total ≈ 35 each
   - NOT FOUND

**Possible explanations:**

- These moves store damage in collision files directly
- Multi-hit moves use nextId chains from base values
- Different selection mechanism from jpower block
- Damage calculated with modifiers we don't understand

### Damage Formula Analysis

**CONFLICT RESOLUTION IN PROGRESS:**

| Formula   | Ichigo (tier=2)   | Bankai (tier=1)  | Goku (tier=2)  |
| --------- | ----------------- | ---------------- | -------------- |
| ÷5 + tier | 50÷5+0 = **10** ✓ | 50÷5-1 = **9** ✓ | 50÷5+0 = 10 ✗  |
| ÷7        | 50÷7 = 7 ✗        | 50÷7 = 7 ✗       | 50÷7 = **7** ✓ |

**Key observation from Ichigo session:**

- chr_b `tier` field IS a damage modifier (proven)
- tier 1 = -1 damage, tier 2 = 0, tier 3 = +1 (likely)
- Formula `damage = jpower/5 + (tier-2)` works for Ichigo/Bankai

**Goku paradox:**

- Goku B = 8 damage, tier = 2
- If ÷5 formula: needs jpower = 40 (exists at indices 146, 195, 218)
- BUT Goku uses Block 0, which has totals of 50 and 100, not 40

**Possible resolutions:**

1. **Block 0 entry mismatch:** The Block 0 entries with total=50 may not
   correspond to Goku's B move - the selection mechanism is unknown

2. **jpower total=40 exists:** Entries 146, 195, 218 have total=40
   - If Goku somehow accesses these, B=8 with ÷5 formula works
   - BUT these aren't in Block 0

3. **Collision file damage:** Some moves may store damage in collision files
   rather than jpower (needs investigation)

### Character Weight

**Observed:** Goku feels "standard" weight in-game.

**NOT stored in:**

- chr_b.bin battleParams
- Collision files
- jpower.bin

**Location:** Unknown

### Walk Speed

**Observed:** Goku appears average/standard walk speed.

**Location:** Unknown (same as weight)

### Collision-to-jpower Entry Mapping (Updated 2026-01-30)

**KEY DISCOVERY: damageFlags is a jpower array index for some characters**

Comparing Goku vs Ichigo collision files reveals different patterns:

| Character | damageFlags Pattern | Interpretation |
|-----------|---------------------|----------------|
| Ichigo | Non-zero values (2, 3, 5, 7, 8, etc.) | **Global jpower array indices** |
| Goku | Almost all 0 | Different lookup mechanism |

**Ichigo evidence (confirmed):**
- Ichigo B collision: damageFlags=2 → jpower[2] has total=50 → 50/5=10 ✓
- Ichigo uses damageFlags as **direct jpower array index**
- Most Ichigo collision entries have non-zero damageFlags

**Goku mystery (unresolved):**
- Goku B collision: damageFlags=0, hitTier=2
- All Goku subType=1 (B attacks) entries have damageFlags=0
- damageFlags=0 does NOT simply mean jpower[0]
- Goku B=8 requires jpower with total=40 (not in Block 0)

**collision subType distribution (Goku):**

- 0: 2 entries
- 1: 6 entries (B attacks, all damageFlags=0)
- 2: 13 entries (combo, mostly damageFlags=0, one has 14)
- 5: 2 entries (launcher)
- 6: 1 entry (aerial, damageFlags=1)
- 7: 1 entry (heavy/Y, projectile)

**jpower Block 0:** 9 entries (indices 0-8) with total=50 or 100

**Hypothesis:** When damageFlags=0, the game uses a different lookup mechanism
(possibly subType, hitTier, or an ARM9 table) to find the jpower entry.

### battleParams Field Meaning (Updated from Ichigo Session)

**Goku's battleParams:** `[37, 16, 15, 0, 49, 16, 32, 20, 40, 20, 20, 0]`

**CONFIRMED structure from ARM9 analysis:**

```
┌────────────────────────────────────────────────────────────────┐
│ Bytes 0-7: Four 16-bit parameter slots                         │
│   [low_byte: value] + [high_byte: flags]                       │
│                                                                 │
│ Bytes 8-10: Stat distribution (sum to ~80-100)                 │
│   Byte 8:  Attack weight (25-100)                              │
│   Byte 9:  Defense weight (0-40)                               │
│   Byte 10: Speed/Utility weight (0-30)                         │
│                                                                 │
│ Byte 11: Special flag (0 or 1)                                 │
└────────────────────────────────────────────────────────────────┘
```

**Goku parsed:**

| Slot | Value | Flags | Notes             |
| ---- | ----- | ----- | ----------------- |
| 0    | 37    | 0x10  | Flag bit 4 set    |
| 1    | 15    | 0x00  | No flags          |
| 2    | 49    | 0x10  | Flag bit 4 set    |
| 3    | 32    | 0x14  | Flags 0x10 + 0x04 |

**Stats:** [40, 20, 20] = 80 total (balanced profile)

**Comparison with Ichigo:**

| Character | Slots                                   | Stats      | Sum | Profile   |
| --------- | --------------------------------------- | ---------- | --- | --------- |
| Goku      | [37,0x10], [15,0], [49,0x10], [32,0x14] | [40,20,20] | 80  | Balanced  |
| Ichigo    | [7,0], [27,0], [48,0], [0,0]            | [40,40,20] | 100 | Defensive |
| Bankai    | [7,0], [34,0x20], [7,0], [0,0]          | [50,35,15] | 100 | Offensive |

**Note:** Bytes 0-7 (slot values/flags) do NOT encode weight or walk speed.
Nami/Franky have identical battleParams despite opposite gameplay feel. The stat
weights (bytes 8-10) likely affect AI or battle calculations.

---

## Comparison: Goku vs Ichigo (Updated)

| Property       | Goku (db_b_01) | Ichigo (bl_b_01) | Notes                     |
| -------------- | -------------- | ---------------- | ------------------------- |
| chr_b index    | 0              | 39               | Different series          |
| charId         | 7              | 3                | Stat template ID          |
| **tier**       | **2**          | **2**            | Same (no damage modifier) |
| jpower block   | 0              | 52               | Different blocks          |
| Base B damage  | 8              | 10               | **Different**             |
| Stats [8,9,10] | [40,20,20]=80  | [40,40,20]=100   | Goku lower total          |

**Damage formula status:**

- ÷5 + tier formula **CONFIRMED** for Ichigo/Bankai
- Goku B=8 requires jpower=40 with ÷5 formula
- jpower entries with total=40 exist (indices 146, 195, 218) but not in Block 0
- **Resolution needed:** Determine which jpower entry Goku's B actually uses

**ARM9 findings from Ichigo session:**

| Offset   | Contents                                                  |
| -------- | --------------------------------------------------------- |
| 0x0924B0 | Collision file pointer table (8-byte entries)             |
| 0x08D4A0 | chr_b → collision identity mapping (confirms index=index) |
| 0x09E780 | Koma name table                                           |

---

## Investigation Results (2026-01-30)

### Collision damageFlags = Global jpower Index (Partial Confirmation)

**For Ichigo (bl_b_01):** CONFIRMED
- damageFlags values (2, 3, 5, 7, 8, etc.) are **global jpower array indices**
- Example: damageFlags=2 → jpower array[2] → ID=6, total=50 → 50/5=10 damage ✓

**For Goku (db_b_01):** UNRESOLVED
- Most entries have damageFlags=0
- damageFlags=0 does NOT mean jpower array[0] (that would give 50/5=10, not 8)
- Goku B=8 requires jpower total=40, which exists at indices 146, 195, 218

**jpower entries with total=40:**

| Index | ID | linkCategory | Used By |
|-------|-----|--------------|---------|
| 146 | 379 | 1 | Unknown |
| 195 | 539 | 1 | Unknown |
| 218 | 604 | 1 | Unknown |

**Mystery remains:** How does Goku's collision (damageFlags=0) access index 146?

### Possible Explanations

1. **ARM9 lookup table:** A secondary table maps (chr_b_index, move_type) to jpower
2. **Formula with chr_b_index:** e.g., chr_b_index + offset = jpower_index
3. **damageFlags=0 special behavior:** Different lookup based on subType/hitTier
4. **Block 0 not used for B move:** Goku's B might bypass block system entirely

---

## Next Steps

1. **Search ARM9 for jpower lookup table:** Might find mapping between characters and entries with total=40

2. **Test more characters with damageFlags=0:** Find another character like Goku and verify their B damage

3. **Examine entries 146, 195, 218:** What makes them special? linkCategory=1 is common to all three

4. **Binary search ARM9 for values 146, 379, 40:** Might find the lookup mechanism

5. **Find weight/speed data:** Not in battleParams or collision - search ARM9 overlays
