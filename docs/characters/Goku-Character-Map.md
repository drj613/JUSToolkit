# Goku / Goku SSJ - Character Map

Deep dive analysis mapping Goku and Goku SSJ through all data files.

> **Note:** Base Goku and Goku SSJ share the same jpower block (0) and classId (256),
> meaning they have identical damage values for all B/Y moves. They differ only in
> sprites, koma costs, and X moves. This document covers both forms.

---

## Overview

| Field           | Base Goku | Goku SSJ |
| --------------- | --------- | -------- |
| Series          | Dragon Ball | Dragon Ball |
| chr_b Index     | 0         | 1        |
| Collision File  | db_b_01.bin | db_b_02.bin |
| Collision Entries | 25      | 36       |
| charId          | 7         | 7        |
| tier            | 2         | 2        |
| jpower Block    | 0         | 0        |
| classId         | 256       | 256      |
| Koma Sizes      | 4, 5      | 6, 7     |

**Why consolidated:** Both forms use identical jpower block 0 and classId 256,
meaning they have the same damage values for all B/Y moves. User confirmed same
moveset. SSJ differs in sprites, koma cost, and X moves.

---

## ✓ CONFIRMED - In-Game Verified Data (2026-01-29)

### Movement & Physics

| Property      | Value    | Notes                              |
| ------------- | -------- | ---------------------------------- |
| Walk Speed    | Normal   | statC=161 (above slow threshold)   |
| Dash Type     | Standard | Visible dash forward               |
| Dash Distance | TBD      | Short / Medium / Long              |
| Weight Class  | Normal   | Standard knockback received        |

**Dash Types:**
- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Innate Passive

| Form       | Passive Name | Effect                     |
| ---------- | ------------ | -------------------------- |
| Base Goku  | TBD          | Needs in-game verification |

**Note:** Passives are per-form (same for all koma sizes of that form). Stored in koma.bin PassiveIndex field.

### Helper Boosts (Ally Boosts)

Characters that give Goku an HP boost when placed adjacent in deck:

| Helper      | Boost | Series Connection              |
| ----------- | ----- | ------------------------------ |
| TBD         | TBD   | Needs in-game verification     |

**Note:** Ally boosts are typically same-series characters or characters with story connections.

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

- db_b_01 (chr_b[0]): Base Goku - THIS FILE
- db_b_02 (chr_b[1]): Goku SSJ - THIS FILE (same jpower block)
- db_b_03 (chr_b[2]): Vegetto - SEPARATE FILE (different jpower block 1)

### Form-Specific: Specials (X Moves)

| Form      | Koma | X Damage | X Notes | up X Damage | up X Notes |
| --------- | ---- | -------- | ------- | ----------- | ---------- |
| Base Goku | 4    |          |         |             |            |
| Base Goku | 5    |          |         |             |            |
| Goku SSJ  | 6    |          |         |             |            |
| Goku SSJ  | 7    |          |         |             |            |

### Form-Specific: Sprite Archives

| Form      | Main Sprites  | X-Koma Portrait  |
| --------- | ------------- | ---------------- |
| Base Goku | db_b_01c.aar  | db_b_01_Xc.aar   |
| Goku SSJ  | db_b_02c.aar  | db_b_02_Xc.aar   |

---

## ⚠️ LIKELY TRUE - Evidence Exists But Incomplete

### jpower Block 0 Structure

**9 attack entries (indices 0-8):**

| Entry | jpower ID | d1  | d2  | d3  | Total | floor(d1÷5)+(tier-2) | hitstun |
| ----- | --------- | --- | --- | --- | ----- | -------------------- | ------- |
| 0     | 0         | 30  | 20  | 0   | 50    | 6                    | 5       |
| 1     | 3         | 10  | 40  | 0   | 50    | 2                    | 0       |
| 2     | 6         | 50  | 0   | 0   | 50    | 10                   | 5       |
| 3     | 9         | 30  | 0   | 20  | 50    | 6                    | 5       |
| 4     | 12        | 25  | 25  | 0   | 50    | 5                    | 5       |
| 5     | 15        | 20  | 0   | 30  | 50    | 4                    | 5       |
| 6     | 18        | 25  | 25  | 0   | 50    | 5                    | 5       |
| 7     | 21        | 60  | 40  | 0   | 100   | 12                   | 10      |
| 8     | 23        | 100 | 0   | 0   | 100   | 20                   | 10      |

> **DEBUNKED (historical):** This table originally carried "÷7" and "÷5 of
> total" columns; both formulas summed d1+d2+d3 and were wrong. The confirmed
> formula is `floor(damage1 / 5) + (tier - 2)` (Research-Status.md). Note none
> of Goku's tested damages (B=8, fwd B=7, up Y=14) match Block 0 entries under
> the confirmed formula — Goku's moves resolve to jpower entries OUTSIDE
> Block 0 via the unknown Indirect (damageFlags=0) lookup, e.g. B=8 uses
> `damage1=40` at global indices 146/195/218.

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

**Moves not found in jpower Block 0** (required `damage1` per confirmed
formula `floor(d1/5) + (tier-2)`, tier=2):

1. **B (8 damage)**
   - Required damage1 = 40
   - **FOUND outside Block 0:** global indices 146, 195, 218

2. **up B hits (3 damage each)**
   - Required damage1 = 15 each
   - Not yet located

3. **Y combo hits (4+4+6 damage)**
   - Required damage1 = 20, 20, 30
   - Not yet located

4. **fwd Y projectiles (5 damage each)**
   - Required damage1 = 25 each
   - Not yet located

**Possible explanations:**

- These moves store damage in collision files directly
- Multi-hit moves use nextId chains from base values
- Different selection mechanism from jpower block
- Damage calculated with modifiers we don't understand

### Damage Formula Analysis (RESOLVED)

**Confirmed formula (Research-Status.md):**

```
damage = floor(jpower.damage1 / 5) + (tier - 2)
```

- Uses `damage1` (first component) only — NOT the d1+d2+d3 total
- tier 1 = -1 damage, tier 2 = 0, tier 3 = +1

**The former "Goku paradox" and ÷7 alternative are DEBUNKED.** Both arose
from summing all three damage components. With `damage1` alone:

- Ichigo (tier=2): damage1=50 → 50/5+0 = 10 ✓
- Bankai (tier=1): damage1=50 → 50/5-1 = 9 ✓
- Goku B (tier=2) = 8 → requires damage1=40, which exists at global indices
  146, 195, 218 (outside Block 0)

**Remaining open question (moved to entry-selection research):** how Goku's
damageFlags=0 collision entries select out-of-block jpower entries.

### Walk Speed (PARTIALLY SOLVED 2026-01-30)

**Location:** chr_b.bin `statC` field (offset 12, 2 bytes)

**Goku's statC:** 161 (above threshold = normal/fast tier)

Walk speed uses a **threshold system**, not linear scaling:

| Character | statC | Walk Speed |
|-----------|-------|------------|
| Zoro      | 33    | SLOW       |
| Franky    | 67    | SLOW       |
| Lenalee   | 153   | FAST       |
| Goku      | 161   | Normal     |
| Ichigo    | 225   | Normal     |
| Killua    | 300   | FAST       |

**Key finding:** Lenalee (153) and Killua (300) have the SAME walk speed!
- statC < ~100 = SLOW tier
- statC >= ~100 = Normal/Fast tier

### Knockback/Displacement

Displacement is affected by **multiple factors**:
- HP (lower HP = more knockback)
- Character passives (e.g., Edajima's "hard to knock back")
- Possibly statC as a base factor

Goku's statC=161 is above the slow threshold, giving normal walk speed.

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
- Goku B=8 requires jpower with damage1=40 (not in Block 0)

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

- `floor(damage1/5) + (tier-2)` **CONFIRMED** for all tested characters
- Goku B=8 requires damage1=40
- jpower entries with damage1=40 exist (indices 146, 195, 218) but not in Block 0
- **Resolution needed:** Determine which jpower entry Goku's B actually uses
  (entry selection mechanism, not formula)

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
- Goku B=8 requires jpower damage1=40, which exists at indices 146, 195, 218

**jpower entries with damage1=40:**

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

1. **Search ARM9 for jpower lookup table:** Might find mapping between characters and entries with damage1=40

2. **Test more characters with damageFlags=0:** Find another character like Goku and verify their B damage

3. **Examine entries 146, 195, 218:** What makes them special? linkCategory=1 is common to all three

4. **Binary search ARM9 for values 146, 379, 40:** Might find the lookup mechanism

~~5. **Find weight/speed data:**~~ **SOLVED** - statC field in chr_b.bin controls both
