# Renji Abarai (bl_b_04) - Complete Character Mapping

Deep dive analysis mapping Renji Abarai through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Renji Abarai           |
| Series          | Bleach                 |
| chr_b Index     | 42                     |
| Collision File  | bl_b_04.bin            |
| charId          | 3                      |
| tier            | (needs extraction)     |
| jpower Block    | 54                     |
| classId         | 310                    |

---

## In-Game Verified Data

### Koma Sizes (UNVERIFIED)

- **Renji:** (needs human verification)

### Move List (UNVERIFIED)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        |            |                       |
| fwd B  |        |            |                       |
| up B   |        |            |                       |
| down B |        |            |                       |
| air B  |        |            |                       |
| Y      |        |            |                       |
| fwd Y  |        |            |                       |
| up Y   |        |            |                       |
| down Y |        |            |                       |
| air Y  |        |            |                       |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 42)

| Field        | Value            | Notes                          |
| ------------ | ---------------- | ------------------------------ |
| charId       | 3                | Shared with Ichigo, Rukia, Hitsugaya, Lenalee |
| formType     | (needs extraction) | 0=Normal, 1=Powered            |
| tier         | (needs extraction) | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     | (needs extraction) | Internal size (not deck koma)  |
| classId      | 310              | Low byte = jpower block index  |
| jpower Block | 54               | classId & 0xFF                 |

### battleParams (12 bytes)

```
Raw: [needs extraction]

Stats [8,9,10]: [?, ?, ?] = ? total
  Attack weight:  ?
  Defense weight: ?
  Speed/Utility:  ?

Byte 11: ? (special flag)

Profile: (needs extraction)
```

### Collision File (bl_b_04.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | (needs extraction)       |
| Entry Count | (needs extraction)       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 54 Analysis

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       |                   |       |

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)
```

- tier 1: -1 modifier
- tier 2: no modifier
- tier 3: +1 modifier

**Note:** Renji shares jpower Block 54 with Eve (bc_b_02) from Black Cat.

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| bl_b_04c.aar         |      | Main sprites    |
| bl_b_04_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 42                    |
| 0x08D4A0 | chr_b -> collision identity mapping   |                             |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** (UNKNOWN)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: (needs testing)
- Walk speed: (needs testing)
- Comparison to reference characters: (needs testing)

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    | (UNKNOWN)          | Slow / Normal / Fast               |
| Dash Type     | (UNKNOWN)          | Standard / Flash                   |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

Renji is a Shinigami Lieutenant whose Zanpakuto (Zabimaru) has a unique extending/segmented blade. His fighting style likely features:
- Extended range sword attacks (Slashing damage)
- Zabimaru's whip-like segmented blade mechanics
- Potentially multi-hit attacks from the extending blade

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID | Test Description | Priority | Status | Result |
| ------- | ---------------- | -------- | ------ | ------ |
| bl_b_04-001 | All koma sizes available | P2 | PENDING | |
| bl_b_04-002 | B move damage (neutral, no buffs) | P2 | PENDING | |
| bl_b_04-003 | Complete moveset damage values | P2 | PENDING | |
| bl_b_04-004 | Damage types (use defensive passives) | P2 | PENDING | |
| bl_b_04-005 | Walk speed (compare to Goku) | P3 | PENDING | |
| bl_b_04-006 | Weight class (compare knockback to Goku) | P3 | PENDING | |
| bl_b_04-007 | Dash type (standard or flash) | P3 | PENDING | |
| bl_b_04-008 | Zabimaru extended range mechanics | P2 | PENDING | |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y / up Y / down Y damage
   - [ ] All X move damage at each koma size

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast, Franky=slow)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)
   - [ ] Zabimaru extending attack range and hit count

---

## Unknown / Needs Research

### Unverified Data

1. Actual tier value from chr_b.bin extraction
2. Complete battleParams byte values
3. Collision file entry count and structure

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Renji have extended range on certain attacks (Zabimaru mechanic)?
2. Does he share any moveset properties with Eve (same jpower block)?
3. Does he have a buff/taunt system like Ichigo?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship           |
| ----------------- | ----------- | -------------- | ---------------------- |
| Ichigo Kurosaki   | 39          | bl_b_01.bin    | Same series, charId=3  |
| Bankai Ichigo     | 40          | bl_b_02.bin    | Same series, charId=3  |
| Rukia Kuchiki     | 41          | bl_b_03.bin    | Same series, charId=3  |
| Hitsugaya         | 43          | bl_b_05.bin    | Same series, charId=3  |
| Eve (Black Cat)   | 38          | bc_b_02.bin    | Same jpower block (54) |
| Lenalee Lee       | 46          | dg_b_02.bin    | Different series, charId=3 |

**Characters sharing charId=3:**

All Bleach battle characters (Ichigo, Bankai, Rukia, Renji, Hitsugaya) plus Lenalee from D.Gray-man share the same stat template (charId=3).

**Characters sharing jpower Block 54:**

- Renji Abarai (bl_b_04) - classId=310
- Eve (bc_b_02) - classId=310

Both characters use the same jpower block but likely have DIFFERENT movesets (jpower blocks are template libraries, not 1:1 movesets).

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                               |
| -------- | -------------------------------------- |
| 0x0924B0 | Collision file pointer table           |
| 0x08D4A0 | chr_b -> collision identity mapping    |
| 0x09E780 | Koma name table                        |

### Related Documentation

- [chr_b-Complete-Mapping.md](../research/chr_b-Complete-Mapping.md)
- [jpower-Mapping.md](../research/jpower-Mapping.md)
- [Ichigo-Character-Map.md](./Ichigo-Character-Map.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
| 2026-01-29 | Initial creation | Data from chr_b mapping | Extracted from research docs |

---

## Notes

- Renji shares charId=3 with all other Bleach characters, meaning they use the same stat template
- jpower block 54 is shared with Eve from Black Cat (both have classId=310)
- As a sword user with Zabimaru, most attacks are expected to be Slashing damage type
- Zabimaru's extending mechanic may result in extended range or multi-hit attacks
