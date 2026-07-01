# Rukia Kuchiki (bl_b_03) - Complete Character Mapping

Deep dive analysis mapping Rukia Kuchiki through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Rukia Kuchiki          |
| Series          | Bleach                 |
| chr_b Index     | 41                     |
| Collision File  | bl_b_03.bin            |
| charId          | 3                      |
| tier            | (needs extraction)     |
| jpower Block    | 56                     |
| classId         | 312                    |

---

## In-Game Verified Data

### Koma Sizes (UNVERIFIED)

- **Rukia:** (needs human verification)

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

### chr_b.bin Entry (Index 41)

| Field        | Value            | Notes                          |
| ------------ | ---------------- | ------------------------------ |
| charId       | 3                | Shared with Ichigo, Renji, Hitsugaya, Lenalee |
| formType     | (needs extraction) | 0=Normal, 1=Powered            |
| tier         | (needs extraction) | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     | (needs extraction) | Internal size (not deck koma)  |
| classId      | 312              | Low byte = jpower block index  |
| jpower Block | 56               | classId & 0xFF                 |

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

### Collision File (bl_b_03.bin)

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

### jpower Block 56 Analysis

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

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| bl_b_03c.aar         |      | Main sprites    |
| bl_b_03_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 41                    |
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

Rukia is a Shinigami from the Soul Society. Her fighting style likely incorporates:
- Zanpakuto sword attacks (Slashing damage)
- Ice-type abilities from Sode no Shirayuki (her Zanpakuto)

Character uses ice-themed special attacks which may have unique properties.

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
| bl_b_03-001 | All koma sizes available | P2 | PENDING | |
| bl_b_03-002 | B move damage (neutral, no buffs) | P2 | PENDING | |
| bl_b_03-003 | Complete moveset damage values | P2 | PENDING | |
| bl_b_03-004 | Damage types (use defensive passives) | P2 | PENDING | |
| bl_b_03-005 | Walk speed (compare to Goku) | P3 | PENDING | |
| bl_b_03-006 | Weight class (compare knockback to Goku) | P3 | PENDING | |
| bl_b_03-007 | Dash type (standard or flash) | P3 | PENDING | |

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
   - [ ] Ice ability effects (freeze? slow?)

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

1. Does Rukia have ice-specific mechanics (freeze, slow)?
2. Does she have a buff/taunt system like Ichigo?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship           |
| ----------------- | ----------- | -------------- | ---------------------- |
| Ichigo Kurosaki   | 39          | bl_b_01.bin    | Same series, charId=3  |
| Bankai Ichigo     | 40          | bl_b_02.bin    | Same series, charId=3  |
| Renji Abarai      | 42          | bl_b_04.bin    | Same series, charId=3  |
| Hitsugaya         | 43          | bl_b_05.bin    | Same series, charId=3  |
| Lenalee Lee       | 46          | dg_b_02.bin    | Different series, charId=3 |

**Characters sharing charId=3:**

All Bleach battle characters (Ichigo, Bankai, Rukia, Renji, Hitsugaya) plus Lenalee from D.Gray-man share the same stat template (charId=3).

**Characters sharing jpower Block 56:**

- (needs research - may be unique to Rukia)

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

- Rukia shares charId=3 with all other Bleach characters, meaning they use the same stat template
- jpower block 56 is unique to Rukia (classId=312)
- As a sword user, most attacks are expected to be Slashing damage type
- Ice abilities may have unique properties not documented yet
