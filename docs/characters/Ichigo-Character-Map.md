# Ichigo Kurosaki - Complete Character Mapping

> **Map status:** COMPLETE — full move list with in-game verified damages for base and Bankai (2026-01-29); file-linkage sections pending independent re-verification.

Deep dive analysis mapping Ichigo through all data files to understand linkages.

---

## In-Game Verified Data (2026-01-29)

### Koma Sizes (CONFIRMED)

- **Base Ichigo:** 4, 5, 6 koma
- **Bankai Ichigo:** 7, 8 koma

### Base Ichigo Move List (CONFIRMED)

| Move      | Damage  | Type     | Notes                               |
| --------- | ------- | -------- | ----------------------------------- |
| Neutral B | 10      | Slashing | Single hit                          |
| Forward B | 10      | Slashing | Single hit                          |
| Up B      | 9       | Slashing | Single hit                          |
| Down B    | 10      | Impact   | Single hit                          |
| Y         | 2+2+2   | Slashing | 3 hits                              |
| YYYY      | 2×5 + 4 | Slashing | 6 hits, final applies knockback     |
| Fwd Y     | 15 / 18 | Slashing | Getsuga (unbuffed/buffed)           |
| Up Y      | 15 / 18 | Slashing | Getsuga upward                      |
| Air Y     | 15 / 18 | Slashing | Getsuga aerial                      |
| Down Y    | 18      | **???**  | NOT Impact! Immune to dmg reduction |

### Base Ichigo Specials (X Moves)

| Koma | X             | up X                                                |
| ---- | ------------- | --------------------------------------------------- |
| 4    | 30 dmg, 1 hit | 33 dmg, 1 hit                                       |
| 5    | 38 dmg, 1 hit | No damage - Deck Power buff + Character Seal debuff |
| 6    | 45 dmg, 1 hit | No damage - Attack Boost buff (1.2×)                |

### Bankai Ichigo Move List (CONFIRMED - Different Moveset!)

| Move   | Damage  | Type     | Notes                                    |
| ------ | ------- | -------- | ---------------------------------------- |
| B      | 9       | Slashing | Single hit                               |
| Fwd B  | 9       | Slashing | Single hit                               |
| Up B   | 9       | Slashing | Single hit                               |
| Down B | 9       | Impact   | Single hit                               |
| Air B  | 9       | Slashing | Single hit                               |
| Y      | 2+2+7   | Slashing | 3 hits, final applies knockback          |
| YY     | 2×4 + 7 | Slashing | Variable combo, more taps = more slashes |
| YYY    | 2×6 + 7 | Slashing | "                                        |
| YYYY   | 2×8 + 7 | Slashing | "                                        |
| Fwd Y  | 18      | Slashing | Teleport slash (appears behind enemy)    |
| Up Y   | 18      | Slashing | Teleport upward slash                    |
| Air Y  | 18      | Slashing | Teleport to ground, arc slash            |
| Down Y | 18      | **???**  | NOT Impact! Immune to dmg reduction      |

### Bankai Ichigo Specials (X Moves)

| Koma | X                                                  | up X                            |
| ---- | -------------------------------------------------- | ------------------------------- |
| 7    | 50 dmg, 1 hit (random 75 dmg empowered + SP drain) | 49 dmg, 21 hits (1 + 19×2 + 10) |
| 8    | 55 dmg, 1 hit                                      | 65 dmg, 26 hits (1 + 24×2 + 16) |

### Koma Size Damage Scaling (Specials)

| Koma | X Damage | Delta |
| ---- | -------- | ----- |
| 4    | 30       | -     |
| 5    | 38       | +8    |
| 6    | 45       | +7    |
| 7    | 50       | +5    |
| 8    | 55       | +5    |

Pattern: Diminishing returns at higher koma sizes. Not a simple linear formula.
May not even be formulaic at all.

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense
  passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense
  passive)
- **??? (Guard Break?)** - Third type immune to both defensive passives
  - Example: Bankai down Y does 18 damage even with both passives active

### Buff Mechanics (CONFIRMED)

#### Getsuga Buff (Y Spin / Taunt)

**Trigger methods:**

1. **Y Spin** - Tap Y 4 times quickly (sword spins overhead, extended animation)
2. **Taunt** - Press Select for "ultimate action"

**Buff effects on Getsuga (fwd Y, up Y, air Y):**

- Damage: 15 → 18 (1.2× multiplier)
- Hitbox: Larger
- Knockback: Increased
- Hitstun: Increased
- Behavior: Projectile pierces through targets instead of disappearing on hit

#### Attack Boost Buff (6-koma up X)

Applies **exactly 1.2× damage multiplier** with standard rounding:

| Move             | Base | Boosted | Calculation            |
| ---------------- | ---- | ------- | ---------------------- |
| B                | 10   | 12      | 10 × 1.2 = 12 ✓        |
| up B             | 9    | 11      | 9 × 1.2 = 10.8 → 11 ✓  |
| fwd/up/air Y     | 15   | 18      | 15 × 1.2 = 18 ✓        |
| Getsuga-buffed Y | 18   | 22      | 18 × 1.2 = 21.6 → 22 ✓ |
| down Y           | 18   | 22      | 18 × 1.2 = 21.6 → 22 ✓ |

**Y combo with Attack Boost:** 2,3,2,3,2,5 (alternating rounding pattern)

#### Other Buffs

- **5-koma up X:** "Deck Power" buff (damage scales with number of unique
  characters in deck) + "Character Seal" debuff (cannot switch characters)
- **7-koma X (random):** Empowered version (75 dmg vs 50) but causes SP drain

### Weight/Displacement Mechanics (CONFIRMED)

**Key findings:**

- Base Ichigo and Bankai Ichigo have **identical** displacement velocity
- Franky has **much lower** displacement velocity (heavier feel)
- HP affects displacement velocity (lower HP = more displacement)
- "Heavy" characters = slower walk speed + lower displacement velocity

**Universal constants (all characters):**

- Same jump height
- Same fall speed

**Variable per-character:**

- **Walk speed** - varies (Franky slow, Killua fast, etc.)
- **Dash distance/speed** - Dash sprite duration appears constant, but actual
  ground covered varies. Some characters slide further after returning to idle.
  - Fast dashers: Killua, Lenalee (quick, cover lots of ground)
  - Normal dashers: Goku, Gon, Nami (similar speed/distance to each other)
  - Flash dashers: Ichigo, Bankai Ichigo, Dio, Gear 2 Luffy (character vanishes
    and reappears slightly farther ahead. Variable distances)

---

## Koma/Deck Sprite Mapping

### koma.bin Structure

Each series gets consecutive entries. Bleach (bl) starts at entry 95:

| Entry   | Name     | KShape | Koma Size | Character             |
| ------- | -------- | ------ | --------- | --------------------- |
| 95-102  | bl_00-07 | 0-6    | 1-7 koma  | Ichigo Base (bl_b_01) |
| 103-109 | bl_08-14 | 0-5    | 1-6 koma  | Bankai (bl_b_02)      |
| 110-112 | bl_15-17 | 0-2    | 1-3 koma  | Support char          |
| ...     | ...      | ...    | ...       | ...                   |

**Key insight:** koma.bin defines deck portrait sprites (DTX files), while
`bl_b_XX_Yc.aar` are battle sprites - two separate systems.

### Available Komas (In-Game Verified)

| Character   | koma.bin Range | Sprite Archives | Available |
| ----------- | -------------- | --------------- | --------- |
| Base Ichigo | bl_00-07 (1-7) | bl_b_01_4/5/6c  | 4, 5, 6   |
| Bankai      | bl_08-14 (1-6) | bl_b_02_7/8c    | 7, 8      |

**Note:** Bankai's 7/8 koma sprites exist but aren't in koma.bin's 1-6 range for
that character. The deck system must have additional logic to include higher
koma sizes.

---

## File Data

### Collision Files (ChrBin.aar/chr/col/)

| File        | Size      | Entries | Character              |
| ----------- | --------- | ------- | ---------------------- |
| bl_b_01.bin | 400 bytes | 20      | Ichigo Kurosaki (base) |
| bl_b_02.bin | 520 bytes | 26      | Ichigo (Bankai)        |

### Sprite Archives (chr/)

| Archive        | Size  | Purpose               |
| -------------- | ----- | --------------------- |
| bl_b_01c.aar   | 107KB | Main sprites (base)   |
| bl_b_01_4c.aar | 16KB  | 4-koma portrait       |
| bl_b_01_5c.aar | 14KB  | 5-koma portrait       |
| bl_b_01_6c.aar | 14KB  | 6-koma portrait       |
| bl_b_02c.aar   | 104KB | Main sprites (Bankai) |
| bl_b_02_7c.aar | 20KB  | 7-koma portrait       |
| bl_b_02_8c.aar | 17KB  | 8-koma portrait       |

### ARM9 Collision File Table (offset 0x0924B0)

| ARM9 Index | Collision File | Character          |
| ---------- | -------------- | ------------------ |
| 39         | bl_b_01        | Ichigo Kurosaki    |
| 40         | bl_b_02        | Ichigo (Bankai)    |
| 41         | bl_b_03        | Rukia Kuchiki      |
| 42         | bl_b_04        | Renji Abarai       |
| 43         | bl_b_05        | Toushiro Hitsugaya |

---

## Collision File Analysis

### Critical Finding: damageFlags ≠ Actual Damage

The collision file `damageFlags` field does **NOT** represent actual damage
values!

| Collision damageFlags | Actual In-Game Damage |
| --------------------- | --------------------- |
| 2, 5, 3, 8, 10, 14... | 10, 10, 9, 10, 15, 18 |

The damageFlags likely encodes:

- A modifier type or index
- A reference to jpower.bin entries
- Some other effect parameter

### bl_b_01.bin Raw Data (20 Entries)

All of Ichigo's B attacks are **single hit**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- |
| 0   | 3    | 1       | 10    | 5     | 0      | 2        | 19  | 1    |
| 1   | 3    | 2       | 10    | 7     | 0      | 5        | 21  | 1    |
| 2   | 3    | 2       | 9     | 5     | 4      | 3        | 22  | 1    |
| 3   | 3    | 1       | 10    | 8     | 0      | 5        | 18  | 1    |
| 4   | 2    | 1       | 10    | 10    | 2      | 0        | 18  | 1    |
| 5   | 3    | 1       | 2     | 2     | 2      | 2        | 29  | 1    |
| 6   | 3    | 5       | 4     | 15    | 4      | 8        | 29  | 1    |
| 7   | 3    | 2       | 2     | -2    | 2      | 7        | 29  | 1    |
| 8   | 2    | 2       | 15    | 15    | 4      | 10       | 21  | 1    |
| 9   | 2    | 5       | 18    | 15    | 5      | 10       | 21  | 1    |
| 10  | 2    | 1       | 15    | 5     | 8      | 8        | 21  | 1    |
| 11  | 2    | 5       | 18    | 12    | 12     | 8        | 21  | 1    |
| 12  | 2    | 2       | 15    | 5     | -6     | 10       | 21  | 1    |
| 13  | 2    | 5       | 18    | 12    | -10    | 10       | 21  | 1    |
| 14  | 2    | 5       | 18    | 15    | 8      | 14       | 1   | 1    |
| 15  | 4    | 6       | 30    | 20    | 5      | 7        | 22  | 1    |
| 16  | 4    | 6       | 33    | 15    | 10     | 9        | 22  | 1    |
| 17  | 4    | 6       | 38    | 20    | 5      | 10       | 22  | 1    |
| 18  | 4    | 6       | 45    | 25    | 5      | 10       | 22  | 1    |
| 19  | 2    | 2       | 8     | 15    | 4      | 10       | 21  | 1    |

**Entries 15-18 (Type 4, SubType 6):** These 4 entries represent the Air Y
(Getsuga) attack, which is **single hit** in-game. The multiple entries likely
represent:

- Different koma size variants, OR
- Buffed vs unbuffed states, OR
- Hitbox shape over animation frames

### bl_b_02.bin (Bankai) - 26 Entries

Key differences from base:

- More entries (26 vs 20)
- Higher hitTier (3) on many attacks
- Type 5 (Summon) entries (8 total)
- Larger hitboxes (max width 30 vs 25)
- Two terminator entries (0xFF)

---

## chr_b.bin Analysis

### Index Mapping Complexity

**IMPORTANT:** chr_b.bin entry indices do NOT directly correspond to ARM9
collision file pointer table indices. The linkage requires further research.

### Entries with charId=3

| chr_b Index | formType    | tier | komaSize | classId | jpower Block |
| ----------- | ----------- | ---- | -------- | ------- | ------------ |
| 39          | 0 (Normal)  | 2    | 4        | 564     | 52           |
| 40          | 0 (Normal)  | 1    | 2        | 564     | 52           |
| 41          | 1 (Powered) | 2    | 3        | 565     | 53           |
| 42          | 0 (Normal)  | 2    | 6        | 310     | 54           |
| 43          | 1 (Powered) | 2    | 5        | 567     | 55           |
| 46          | 1 (Powered) | 1    | 2        | 577     | 65           |

### textIds Reference Wrong Characters

chr_b entries with charId=3 reference **One Piece (Robin)** text content, not
Bleach:

| chr_b Entry | textIds  | Actual Content                |
| ----------- | -------- | ----------------------------- |
| 40          | 419, 420 | Robin move: 六輪咲き クラッチ |
| 41          | 421-424  | Robin moves                   |
| 42          | 426-428  | Robin moves                   |
| 43          | 431-434  | Placeholders (◇)              |

Ichigo's actual name (黒崎一護) is at chr_b_t.bin index **1014**, Bankai at
**1040** - neither referenced by any chr_b entry.

---

## jpower.bin Analysis

### Structure

- **311 entries total**, organized into blocks separated by DATA entries
- **88 DATA entries** act as block markers
- **classId low byte** points to DATA entry indices

### Damage Formula (CONFIRMED - see Research-Status.md)

```
actual_damage = floor(jpower.damage1 / 5)
```

> **Correction note:** This was originally derived here as "jpower_total ÷ 5"
> (total = d1+d2+d3). Cross-character testing later confirmed the divisor
> applies to **damage1 alone**. Ichigo's relevant entries have damage2/3 = 0,
> so total == damage1 and the error was masked — but the total-based version
> is DEBUNKED (it created the fake "Goku ÷7 paradox").

| jpower damage1 | ÷5  | Matches                   |
| -------------- | --- | ------------------------- |
| 10             | 2   | Y combo hit ✓             |
| 20             | 4   | Y combo finisher (base) ✓ |
| 50             | 10  | Base Ichigo B moves ✓     |
| 100            | 20  | Modified/buffed?          |

**SOLVED:** The **tier** field in chr_b.bin applies a damage modifier!

| tier | Count      | Damage Modifier | Example                   |
| ---- | ---------- | --------------- | ------------------------- |
| 1    | 11 entries | -1 (9 dmg)      | Bankai Ichigo (chr_b[40]) |
| 2    | 56 entries | 0 (10 dmg)      | Base Ichigo (chr_b[39])   |
| 3    | 7 entries  | +1 (11 dmg)?    | Untested                  |

**Formula:**

```
base_damage = floor(jpower.damage1 ÷ 5) + (tier - 2)
```

- Base Ichigo (tier=2): 50 ÷ 5 + 0 = 10 ✓
- Bankai (tier=1): 50 ÷ 5 - 1 = 9 ✓

**Attack boost confirms formula:** Bankai 9 × 1.2 = 10.8 → 11 ✓

**NOTE:** Koma size does NOT affect B/Y move damage (tested 7 vs 8 koma Bankai).
Koma size only affects Special (X) move damage with diminishing returns scaling.

### Individual Damage Fields

All damage1/damage2/damage3 values are multiples of 5:

- damage1: 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 100, 150, 200, 400
- damage2: 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 90, 100, 150, 200, 400
- damage3: 0, 5, 10, 20, 25, 30, 35, 40, 45, 50, 70, 100, 150, 200

The three fields may represent:

- Different koma size damage, OR
- Base/modifier components, OR
- Damage distribution over combo hits

### Modifier Values

Most entries have MOD total = 2× base total (50 → 100). This likely represents
the "buffed" or "powered" state damage.

### Bleach classId Mapping Issue

chr_b entries with Bleach classIds (564, 565, 567) point to DATA indices that
have empty or minimal attack blocks:

- classId 564 (low=52) → Block 17: 0 ATK entries
- classId 565 (low=53) → Block 18: 0 ATK entries
- classId 567 (low=55) → Block 19: 1 ATK entry (type2=9, total=200)

This suggests either the mapping is incorrect, or move data is accessed via
nextId chains from these sparse blocks.

---

## Confirmed Mechanics

### NOW KNOWN

1. **Attack Boost = 1.2× multiplier** - Proven via 6-koma up X buff testing
2. **Koma size only affects Specials** - B/Y moves identical across koma sizes
3. **Special damage scales with diminishing returns** - Not linear per koma
4. **Multi-hit specials scale hits AND finisher damage** - 7-koma: 21 hits,
   8-koma: 26 hits
5. **Combo bonus system** - Hits after the first in a combo get bonus damage
   (observed +1 on second hit of B → fwd B combo)
6. **Three damage types exist** - Slashing, Impact, and a third type
   - Down Y is NOT Impact despite label - immune to both damage reduction
     passives
   - Third type may be "Guard Break" or "Special"
7. **chr_b tier field = damage modifier** - tier 1 = -1 dmg, tier 2 = normal,
   tier 3 = +1 dmg (explains Bankai's 9 damage mystery!)
8. **chr_b index = collision index** - ARM9 identity table at 0x8D4A0 confirms
   direct 1:1 mapping between chr_b entries and collision files

### ARM9.bin Key Offsets

| Offset   | Contents                                      |
| -------- | --------------------------------------------- |
| 0x0924B0 | Collision file pointer table (8-byte entries) |
| 0x08D4A0 | chr_b → collision identity mapping (74 bytes) |
| 0x09E780 | Koma name table                               |

**Collision table format:** `[4-byte ptr to filename][4-byte series+char ID]`

### Combo Bonus Analysis (Bankai with defensive passives)

```
B → fwd B: 6 + 7 (second hit got +1 from combo)

Y combo (YYYY): 1, 2, 1, 2, 1, 2, 1, 2, 5
- Odd hits: reduced only
- Even hits: reduced + combo bonus
- Pattern suggests +1 on alternating hits in multi-hit moves
```

### Damage Reduction Passive Formula

Each defensive passive (Slash Defense / Impact Defense) reduces damage by
approximately **33% (÷3)** with minimum reduction of 1:

| Original | Reduced | Reduction | Formula: floor(dmg÷3), min 1 |
| -------- | ------- | --------- | ---------------------------- |
| 2        | 1       | -1        | max(1, floor(2÷3)) = 1 ✓     |
| 7        | 5       | -2        | floor(7÷3) = 2 ✓             |
| 9        | 6       | -3        | floor(9÷3) = 3 ✓             |
| 18       | 13      | -5        | floor(18÷3) = 6 ✗ (off by 1) |

The 18→13 case is slightly off. Possible explanations:

- Maximum reduction cap at 5
- Different formula for projectiles
- Combo bonus affecting the test measurement

### Damage Type Immunity

| Move            | Original | With Both Passives | Result                      |
| --------------- | -------- | ------------------ | --------------------------- |
| B moves (slash) | 9        | 6                  | Reduced by Slash Defense    |
| Y moves (slash) | varies   | reduced            | Reduced by Slash Defense    |
| down Y (???)    | 18       | **18**             | **IMMUNE to both passives** |

Down Y uses a third damage type that bypasses all defensive passives.

## Confirmed Unknowns

### SOLVED (This Session)

1. ~~**chr_b ↔ Collision linkage**~~ → **SOLVED:** Direct 1:1 mapping confirmed
   via ARM9 identity table at 0x8D4A0

2. ~~**Damage formula for non-×5 values**~~ → **SOLVED:** chr_b `tier` field
   applies modifier: tier 1 = -1, tier 2 = 0, tier 3 = +1

3. ~~**battleParams bytes**~~ → **PARTIALLY SOLVED:** Structure decoded below

### battleParams Structure (12 bytes)

```
┌────────────────────────────────────────────────────────────────┐
│ Bytes 0-7: Four 16-bit parameter slots                         │
│   Each slot = [low_byte: value] + [high_byte: flags]          │
│                                                                 │
│   Slot 0 (bytes 0-1): flags = 0x00, 0x10, 0x20                │
│   Slot 1 (bytes 2-3): flags = 0x00, 0x01, 0x10, 0x20          │
│   Slot 2 (bytes 4-5): flags = 0x00, 0x02, 0x04, 0x08...       │
│   Slot 3 (bytes 6-7): flags = 0x00, 0x04, 0x10, 0x14...       │
│                                                                 │
│ Bytes 8-10: Stat distribution (sum to 75-100)                  │
│   Byte 8:  Attack weight (25-100)                              │
│   Byte 9:  Defense weight (0-40)                               │
│   Byte 10: Speed/Utility weight (0-30)                         │
│                                                                 │
│ Byte 11: Special flag (0 or 1)                                 │
└────────────────────────────────────────────────────────────────┘
```

**Ichigo battleParams decoded:**

| Entry            | Slots 0-3                      | Stats [8,9,10] | Profile  |
| ---------------- | ------------------------------ | -------------- | -------- |
| bl_b_01 (Base)   | [7,0], [27,0], [48,0], [0,0]   | [40, 40, 20]   | Balanced |
| bl_b_02 (Bankai) | [7,0], [34,0x20], [7,0], [0,0] | [50, 35, 15]   | Offense  |

Note: Bankai has flag 0x20 on slot 1, base does not. Bankai is more offense-
focused (50 attack vs 40), less defense (35 vs 40), less utility (15 vs 20).

### SOLVED (2026-01-30 Session)

4. ~~**Walk speed storage**~~ → **PARTIALLY SOLVED:** chr_b.bin `statC` field
   - Walk speed uses a **threshold system**, not linear scaling
   - statC < ~100 = SLOW tier (Franky=67, Zoro=33)
   - statC >= ~100 = Normal/Fast tier (Ichigo=225, Killua=300, Lenalee=153)
   - Lenalee (153) and Killua (300) have SAME walk speed despite different statC!

5. ~~**Displacement velocity storage**~~ → **PARTIALLY SOLVED:** Multiple factors!
   - HP affects displacement (lower HP = more knockback)
   - Some characters have "hard to knock back" passive (e.g., Edajima)
   - statC may still be a factor but is NOT the only one
   - Ichigo/Bankai similar displacement likely due to similar HP + no special passives

### Still Unknown

1. **komaSize meaning** - Values 2-6 don't match deck komas (4-8)

2. **battleParams slot meanings** - What do slots 0-3 actually control? (Not
   weight/speed - proven by op_b_04/op_b_08 having identical values)

3. **Special damage scaling formula** - Koma 4→5→6→7→8 gives +8/+7/+5/+5. Not
   linear, might be lookup table or diminishing formula.

4. **Combo Bonus** - Is this a flat damage boost? We only saw the increase in
   damage for Bankai Ichigo's B -> fwd B string against a character that had a
   damage reduction passive

5. **Dash type determination** - What makes Ichigo a "flash dasher" vs normal?

---

## Notes

- Collision file field names in code (`BattleCharacterEntry.cs`) contain
  speculative comments that are not validated
- The chr_b-Mapping.md document in this repo has different ordering than ARM9
  analysis reveals
- Actual damage comes from somewhere other than collision damageFlags field
