# Mashirito (ds_b_02) - Complete Character Mapping

Deep dive analysis mapping Dr. Mashirito through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Dr. Mashirito          |
| Series          | Dr. Slump              |
| chr_b Index     | 57                     |
| Collision File  | ds_b_02.bin            |
| charId          | 45                     |
| tier            | 2                      |
| jpower Block    | 104                    |
| classId         | 360                    |

---

## In-Game Verified Data

### Koma Sizes (UNVERIFIED)

- **Mashirito:** 4, 5, 6, 7 koma (based on sprite archives)

### Move List (UNVERIFIED)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        |            | Needs testing         |
| fwd B  |        |            | Needs testing         |
| up B   |        |            | Needs testing         |
| down B |        |            | Needs testing         |
| air B  |        |            | Needs testing         |
| Y      |        |            | Needs testing         |
| fwd Y  |        |            | Needs testing         |
| up Y   |        |            | Needs testing         |
| down Y |        |            | Needs testing         |
| air Y  |        |            | Needs testing         |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
| 4    |          |         |             |            |
| 5    |          |         |             |            |
| 6    |          |         |             |            |
| 7    |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 57)

| Field        | Value   | Notes                          |
| ------------ | ------- | ------------------------------ |
| charId       | 45      | Mashirito's stat template      |
| formType     | 2       | Special/combo character        |
| tier         | 2       | Normal damage modifier         |
| komaSize     | 3       | Internal size (not deck koma)  |
| classId      | 360     | Low byte = jpower block index  |
| jpower Block | 104     | classId & 0xFF                 |

### battleParams (12 bytes)

```
Raw: [49, 0, 13, 0, 11, 0, 0, 0, 40, 30, 30, 0]

Parsed:
  Slot 0: value=49, flags=0x00
  Slot 1: value=13, flags=0x00
  Slot 2: value=11, flags=0x00
  Slot 3: value=0, flags=0x00

Stats [8,9,10]: [40, 30, 30] = 100 total
  Attack weight:  40
  Defense weight: 30
  Speed/Utility:  30

Byte 11: 0 (no special flag)

Profile: Balanced (full 100 point allocation)
```

### Collision File (ds_b_02.bin)

| Property    | Value      |
| ----------- | ---------- |
| Size        | 660 bytes  |
| Entry Count | 33         |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
| 0   | 3    | 2       | 4     | 5     | 0      | 0        | 34  | 1    | Basic attack |
| 5   | 2    | 5       | 8     | 10    | 14     | 1        | 34  | 3    | Special attack |
| 12  | 4    | 5       | 36    | 30    | 5      | 1        | 2   | 3    | X move |
| 13  | 4    | 2       | 28    | 20    | 4      | 1        | 28  | 3    | X move |
| 18  | 4    | 4       | 8     | 10    | 3      | 1        | 16  | 3    | Special |
| 20  | 5    | 1       | 5     | 2     | 0      | 0        | 3   | 2    | Summon type |
| 22  | 5    | 5       | 20    | 12    | 24     | 1        | 16  | 3    | Summon attack |

**Notes:**

- 33 collision entries total (largest among Dr. Slump cast)
- Multiple Type 5 (Summon) entries - likely uses Caramelman robots
- damageFlags field does NOT represent actual damage values
- Variety of knockback values suggests diverse moveset

### jpower Block 104 Analysis

**Note:** jpower block 104 is beyond the standard 88 DATA blocks in jpower.bin.
The jpower entry selection mechanism for Mashirito may work differently or use a
different formula than low-tier characters.

**Status:** jpower entries for this block need further investigation.

### Sprite Archives (chr/)

| Archive          | Size  | Purpose         |
| ---------------- | ----- | --------------- |
| ds_b_02c.aar     | 73KB  | Main sprites    |
| ds_b_02_4c.aar   | 42KB  | 4-koma portrait |
| ds_b_02_5c.aar   | 42KB  | 5-koma portrait |
| ds_b_02_6c.aar   | 55KB  | 6-koma portrait |
| ds_b_02_7c.aar   | 77KB  | 7-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character  |
| -------- | ------------------------------------- | --------------- |
| 0x0924B0 | Collision file pointer table          | Index 57        |
| 0x08D4A0 | chr_b -> collision identity mapping   |                 |
| 0x09E780 | Koma name table                       |                 |

---

## Mechanics

### Weight Category

**Category:** UNKNOWN (needs testing)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: Needs testing
- Walk speed: Needs testing
- Comparison to reference characters: Needs testing

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    | UNKNOWN            | Slow / Normal / Fast               |
| Dash Type     | UNKNOWN            | Standard / Flash                   |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

Dr. Mashirito is the main antagonist of Dr. Slump, a mad scientist who creates
robots to defeat Arale. Based on collision file analysis:

- Type 5 (Summon) entries suggest he can summon Caramelman robots
- Variety of attack patterns indicates diverse moveset
- Likely plays as a technical/summoner character

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                              | Priority | Status    | Result |
| ----------- | --------------------------------------------- | -------- | --------- | ------ |
| ds_b_02-001 | All B move damage values (neutral)            | P2       | PENDING   |        |
| ds_b_02-002 | All Y move damage values (neutral)            | P2       | PENDING   |        |
| ds_b_02-003 | X move damage at each koma size (4,5,6,7)     | P2       | PENDING   |        |
| ds_b_02-004 | up X move damage at each koma size            | P2       | PENDING   |        |
| ds_b_02-005 | Walk speed comparison (vs Goku standard)      | P2       | PENDING   |        |
| ds_b_02-006 | Dash type (standard vs flash)                 | P2       | PENDING   |        |
| ds_b_02-007 | Weight feel (compare knockback received)      | P2       | PENDING   |        |
| ds_b_02-008 | Damage type verification (use defense passives)| P2      | PENDING   |        |
| ds_b_02-009 | Available koma sizes in deck building         | P2       | PENDING   |        |
| ds_b_02-010 | Summon mechanics (Type 5 collision entries)   | P2       | PENDING   |        |

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
   - [ ] Summon behavior (when do Caramelman appear?)
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. jpower block 104 entry structure (beyond standard DATA block range)
2. Actual damage formula for this character
3. Move damage values and types
4. Summon mechanic details

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers if any (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location
- [ ] Summon duration and behavior

### Open Questions

1. Does Mashirito use the standard damage = jpower/5 + (tier-2) formula?
2. What happens with jpower blocks > 88 (the number of DATA entries)?
3. How do the Type 5 (Summon) collision entries work?

---

## Related Characters

| Character     | chr_b Index | Collision File | Relationship           |
| ------------- | ----------- | -------------- | ---------------------- |
| Arale         | 56          | ds_b_01.bin    | Same series (Dr. Slump)|
| Caramelman    | 58          | ds_b_03.bin    | Same series, also summon|

**Characters sharing charId 45:**

- ds_b_02 (Mashirito)
- ds_b_03 (Caramelman) - both share charId 45

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                               |
| -------- | -------------------------------------- |
| 0x0924B0 | Collision file pointer table           |
| 0x08D4A0 | chr_b -> collision identity mapping    |
| 0x09E780 | Koma name table                        |

### Related Documentation

- [chr_b-Mapping.md](../formats/chr_b-Mapping.md)
- [jpower-Analysis.md](../formats/jpower-Analysis.md)
- [Collision-Format.md](../formats/Collision-Format.md)

---

## Session Log

| Date       | Session      | Verified | Notes                              |
| ---------- | ------------ | -------- | ---------------------------------- |
| 2026-01-29 | Initial scan | No       | Extracted file data, no in-game testing |

---

## Notes

- Dr. Mashirito is the villain from Dr. Slump who creates robots
- formType=2 suggests special/combo mechanics
- Type 5 (Summon) entries in collision file are unique to his moveset
- Largest sprite portrait files (7-koma = 77KB) among Dr. Slump cast
- Likely a technical character that uses summons
