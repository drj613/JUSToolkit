# Arale (ds_b_01) - Complete Character Mapping

Deep dive analysis mapping Arale through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Arale Norimaki         |
| Series          | Dr. Slump              |
| chr_b Index     | 56                     |
| Collision File  | ds_b_01.bin            |
| charId          | 30                     |
| tier            | 2                      |
| jpower Block    | 103                    |
| classId         | 615                    |

---

## In-Game Verified Data

### Koma Sizes (UNVERIFIED)

- **Arale:** 4, 5, 6, 7 koma (based on sprite archives)

### Move List (UNVERIFIED)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        | Punch/Kick | Needs testing         |
| fwd B  |        | Punch/Kick | Needs testing         |
| up B   |        | Punch/Kick | Needs testing         |
| down B |        | Punch/Kick | Needs testing         |
| air B  |        | Punch/Kick | Needs testing         |
| Y      |        | Punch/Kick | Needs testing         |
| fwd Y  |        | Punch/Kick | Needs testing         |
| up Y   |        | Punch/Kick | Needs testing         |
| down Y |        | Punch/Kick | Needs testing         |
| air Y  |        | Punch/Kick | Needs testing         |

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

### chr_b.bin Entry (Index 56)

| Field        | Value   | Notes                          |
| ------------ | ------- | ------------------------------ |
| charId       | 30      | Arale's stat template          |
| formType     | 2       | Special/combo character        |
| tier         | 2       | Normal damage modifier         |
| komaSize     | 5       | Internal size (not deck koma)  |
| classId      | 615     | Low byte = jpower block index  |
| jpower Block | 103     | classId & 0xFF                 |

### battleParams (12 bytes)

```
Raw: [13, 0, 33, 16, 16, 32, 8, 4, 30, 25, 25, 0]

Parsed:
  Slot 0: value=13, flags=0x00
  Slot 1: value=33, flags=0x10
  Slot 2: value=16, flags=0x20
  Slot 3: value=8, flags=0x04

Stats [8,9,10]: [30, 25, 25] = 80 total
  Attack weight:  30
  Defense weight: 25
  Speed/Utility:  25

Byte 11: 0 (no special flag)

Profile: Balanced (low total points suggests support-oriented)
```

### Collision File (ds_b_01.bin)

| Property    | Value      |
| ----------- | ---------- |
| Size        | 560 bytes  |
| Entry Count | 28         |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
| 0   | 3    | 1       | 10    | 10    | 1      | 0        | 6   | 1    | Basic attack |
| 1   | 3    | 7       | 17    | 12    | 1      | 1        | 34  | 2    | Knockback attack |
| 6   | 2    | 7       | 4     | 6     | 1      | 0        | 34  | 2    | Movement attack |
| 14  | 4    | 6       | 40    | 20    | 4      | 1        | 0   | 3    | Special move |
| 19  | 4    | 7       | 0     | 10    | 0      | 1        | 34  | 3    | Projectile |
| 22  | 4    | 6       | 40    | 20    | 11     | 1        | 0   | 3    | Special finisher |

**Notes:**

- 28 collision entries total
- Multiple Type 4 (Special) entries suggesting varied X moves
- Has projectile entries (Type 4, SubType 7)
- damageFlags field does NOT represent actual damage values

### jpower Block 103 Analysis

**Note:** jpower block 103 is beyond the standard 88 DATA blocks in jpower.bin.
The jpower entry selection mechanism for Arale may work differently or use a
different formula than low-tier characters.

**Status:** jpower entries for this block need further investigation.

### Sprite Archives (chr/)

| Archive          | Size | Purpose         |
| ---------------- | ---- | --------------- |
| ds_b_01c.aar     | 63KB | Main sprites    |
| ds_b_01_4c.aar   | 6.7KB| 4-koma portrait |
| ds_b_01_5c.aar   | 6.7KB| 5-koma portrait |
| ds_b_01_6c.aar   | 5.2KB| 6-koma portrait |
| ds_b_01_7c.aar   | 4.5KB| 7-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character  |
| -------- | ------------------------------------- | --------------- |
| 0x0924B0 | Collision file pointer table          | Index 56        |
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

Arale is a comedic character from Dr. Slump. She is known for her superhuman
strength despite her small android body. In-game mechanics may include:

- Potential for high knockback moves (robotic strength)
- Possible comedic attack animations

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
| ds_b_01-001 | All B move damage values (neutral)            | P2       | PENDING   |        |
| ds_b_01-002 | All Y move damage values (neutral)            | P2       | PENDING   |        |
| ds_b_01-003 | X move damage at each koma size (4,5,6,7)     | P2       | PENDING   |        |
| ds_b_01-004 | up X move damage at each koma size            | P2       | PENDING   |        |
| ds_b_01-005 | Walk speed comparison (vs Goku standard)      | P2       | PENDING   |        |
| ds_b_01-006 | Dash type (standard vs flash)                 | P2       | PENDING   |        |
| ds_b_01-007 | Weight feel (compare knockback received)      | P2       | PENDING   |        |
| ds_b_01-008 | Damage type verification (use defense passives)| P2      | PENDING   |        |
| ds_b_01-009 | Available koma sizes in deck building         | P2       | PENDING   |        |

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

---

## Unknown / Needs Research

### Unverified Data

1. jpower block 103 entry structure (beyond standard DATA block range)
2. Actual damage formula for this character
3. Move damage values and types

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers if any (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Arale use the standard damage = jpower/5 + (tier-2) formula?
2. What happens with jpower blocks > 88 (the number of DATA entries)?

---

## Related Characters

| Character     | chr_b Index | Collision File | Relationship           |
| ------------- | ----------- | -------------- | ---------------------- |
| Mashirito     | 57          | ds_b_02.bin    | Same series (Dr. Slump)|
| Caramelman    | 58          | ds_b_03.bin    | Same series (Dr. Slump)|

**Characters sharing charId 30:**

- Only Arale uses charId 30

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

- Arale is a robot girl with incredible strength from the Dr. Slump manga
- formType=2 suggests she may have special/combo mechanics
- Relatively small sprite files suggest simpler animation set
- jpower block 103 is unusual - may indicate special damage handling
