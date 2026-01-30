# Piccolo (db_b_10) - Complete Character Mapping

Deep dive analysis mapping Piccolo through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Piccolo                |
| Series          | Dragon Ball            |
| chr_b Index     | 9                      |
| Collision File  | db_b_10.bin            |
| charId          | 41                     |
| tier            | (needs verification)   |
| jpower Block    | 5                      |
| classId         | 261                    |

**IMPORTANT NOTE:** Piccolo has charId=41, which is unique among Dragon Ball characters.
Most DB characters share charId=7 (Goku family), but Piccolo has his own stat template.

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Piccolo:** (needs human testing) koma

### Move List (NEEDS TESTING)

| Move   | Damage | Type       | Notes                     |
| ------ | ------ | ---------- | ------------------------- |
| B      |        | Punch/Kick |                           |
| fwd B  |        | Punch/Kick |                           |
| up B   |        | Punch/Kick | May have stretchy arms    |
| down B |        | Punch/Kick |                           |
| air B  |        | Punch/Kick |                           |
| Y      |        | Punch/Kick |                           |
| fwd Y  |        | Energy     | Likely Special Beam Cannon|
| up Y   |        | Energy     |                           |
| down Y |        | Punch/Kick |                           |
| air Y  |        | Energy     |                           |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks (ki blasts, Special Beam Cannon)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 9)

| Field        | Value            | Notes                                    |
| ------------ | ---------------- | ---------------------------------------- |
| charId       | 41               | UNIQUE to Piccolo (not charId=7 family)  |
| formType     | (needs verify)   | 0=Normal, 1=Powered                      |
| tier         | (needs verify)   | 1=-1 dmg, 2=normal, 3=+1 dmg             |
| komaSize     | (needs verify)   | Internal size (not deck koma)            |
| classId      | 261              | Low byte = jpower block index            |
| jpower Block | 5                | classId & 0xFF                           |

### charId Uniqueness

Piccolo's charId=41 is unique - he doesn't share it with any other character.
This suggests Piccolo has a completely custom stat template, possibly reflecting:
- His Namekian physiology (regeneration, stretchy limbs)
- His role as a technical/strategic fighter
- Different attack/defense ratios from Saiyans

### battleParams (12 bytes)

```
Raw: [(needs extraction)]

Parsed:
  Slot 0: value=?, flags=0x??
  Slot 1: value=?, flags=0x??
  Slot 2: value=?, flags=0x??
  Slot 3: value=?, flags=0x??

Stats [8,9,10]: [?, ?, ?] = ? total
  Attack weight:  ?
  Defense weight: ?
  Speed/Utility:  ?

Byte 11: ? (special flag)

Profile: (needs analysis)
```

### Collision File (db_b_10.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | (needs extraction) bytes |
| Entry Count | (needs extraction)       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 5 Analysis

From jpower-Mapping.md, Block 5 contains:
- Entries with damages: [7,3,2,1]
- This suggests multiple weak/multi-hit attacks

**Characters sharing Block 5:**

- db_b_10 (Piccolo) - chr_b[9], classId=261 (ONLY character in this block)

**Note:** Piccolo has his own unique jpower block (5), not shared with any other
character. Combined with unique charId, Piccolo is quite isolated in data terms.

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       |                   |       |

**Damage Formula:**

```
base_damage = (jpower_total / 5) + (tier - 2)
```

- tier 1: -1 modifier
- tier 2: no modifier
- tier 3: +1 modifier

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| db_b_10c.aar         |      | Main sprites    |
| db_b_10_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 9                     |
| 0x08D4A0 | chr_b -> collision identity mapping   |                             |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** (needs testing - likely STANDARD or HEAVY)

**Observations:**

- Piccolo is a tall, muscular Namekian
- May feel heavier than Goku
- Displacement velocity: (needs comparison to Goku)
- Walk speed: (needs comparison)

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    | (needs testing)    | Slow / Normal / Fast               |
| Dash Type     | Standard           | Standard dash expected for DB char |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

Piccolo's Namekian abilities may manifest as:
- **Stretchy Arms** - Extended reach on certain attacks
- **Regeneration** - Possible HP recovery mechanic (unlikely but possible)
- **Special Beam Cannon** - Signature charged attack
- **Hellzone Grenade** - Multi-projectile attack

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
| db_b_10-001 | Full moveset damage values | P2 | PENDING | |
| db_b_10-002 | Available koma sizes | P2 | PENDING | |
| db_b_10-003 | Test for stretchy arm reach mechanics | P2 | PENDING | |
| db_b_10-004 | Compare feel to Goku (different charId) | P2 | PENDING | |

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
   - [ ] Stretchy arm reach testing
   - [ ] Special Beam Cannon charging mechanic if present

4. **charId Investigation**
   - [ ] Compare stat feel (attack/defense ratio) to Goku (charId=7)
   - [ ] Note any obvious differences in combat feel

---

## Unknown / Needs Research

### Unverified Data

1. Tier value in chr_b.bin (affects base damage calculation)
2. formType value (0=Normal or 1=Powered)
3. Collision file entry count and structure
4. Why Piccolo has unique charId=41

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Why does Piccolo have a unique charId (41) while most DB characters share charId=7?
2. Does his unique charId manifest as noticeably different stats in-game?
3. Does Piccolo have any Namekian-specific mechanics (stretch, regen)?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship              |
| ----------------- | ----------- | -------------- | ------------------------- |
| Goku              | 0           | db_b_01        | Same series, different charId |
| Gon (HxH)         | 30          | hh_b_01        | charId=42 (close to Piccolo's 41) |

**Characters sharing jpower Block 5:**

- db_b_10 (Piccolo) - ONLY character

**Characters sharing charId 41:**

- db_b_10 (Piccolo) - ONLY character

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
- [Goku-Character-Map.md](./Goku-Character-Map.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
| 2026-01-29 | Initial Creation | File data from chr_b-Complete-Mapping.md | Needs human testing |

---

## Notes

- **UNIQUE:** Has charId=41 (no other character shares this template)
- **UNIQUE:** Has jpower Block 5 (not shared with any other character)
- Piccolo is completely isolated in terms of data sharing
- The Block 5 damage values [7,3,2,1] suggest multi-hit or varied attack strengths
- As a Namekian, may have reach/grapple mechanics different from Saiyans
