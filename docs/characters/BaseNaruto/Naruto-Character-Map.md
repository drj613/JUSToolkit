# Naruto Uzumaki (na_b_01) - Complete Character Mapping

Deep dive analysis mapping Naruto Uzumaki through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Naruto Uzumaki         |
| Series          | Naruto                 |
| chr_b Index     | 20                     |
| Collision File  | na_b_01.bin            |
| charId          | 2                      |
| tier            | 2 (no damage modifier) |
| jpower Block    | 17                     |
| classId         | 529                    |

---

## In-Game Verified Data

### Koma Sizes (NEEDS VERIFICATION)

- **Naruto:** 4, 5, 6 koma (expected based on variant pattern)

### Move List (NEEDS TESTING)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      | **8**  | Punch/Kick | Shadow clone attacks (verified 2026-01-30) |
| fwd B  |        | Punch/Kick |                       |
| up B   |        | Punch/Kick |                       |
| down B |        | Punch/Kick |                       |
| air B  |        | Punch/Kick |                       |
| Y      |        | Punch/Kick |                       |
| fwd Y  |        | Punch/Kick |                       |
| up Y   |        | Punch/Kick |                       |
| down Y |        | Punch/Kick |                       |
| air Y  |        | Punch/Kick |                       |

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

---

## File Data

### chr_b.bin Entry (Index 20)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 2     | Stat template (shared with others) |
| formType     | 0     | Normal form                    |
| tier         | 2     | No damage modifier (+0)        |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 529   | Low byte = jpower block index  |
| jpower Block | 17    | classId & 0xFF = 17            |

### battleParams (12 bytes)

```
Raw: [NEEDS EXTRACTION]

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

Profile: NEEDS EXTRACTION
```

### Collision File (na_b_01.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | TBD                      |
| Entry Count | 46                       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

- 22 type5 entries (shadow clone summons)
- High entry count indicates complex moveset with clone mechanics

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      | NEEDS EXTRACTION |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries
- Shadow clone attacks (type5) make up nearly half of collision entries

### jpower Block 17 Analysis

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       | NEEDS EXTRACTION  |       |

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)
```

- Naruto tier=2: No modifier (+0)
- Example: If jpower.damage1=50, damage = 50/5 + 0 = 10

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| na_b_01c.aar         |      | Main sprites    |
| na_b_01_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 20                    |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 20                    |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** STANDARD (expected)

**Observations:**

- Displacement velocity: NEEDS TESTING
- Walk speed: NEEDS TESTING
- Comparison to reference characters: Compare to Goku (standard)

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    | NEEDS TESTING      | Slow / Normal / Fast               |
| Dash Type     | NEEDS TESTING      | Standard / Flash                   |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**Shadow Clone System:**
- 22 type5 collision entries indicate extensive shadow clone usage
- Clone attacks likely appear as separate summons performing attacks
- May have multi-hit potential through clone strikes

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
| NEEDS TESTING |     |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID | Test Description | Priority | Status | Result |
| ------- | ---------------- | -------- | ------ | ------ |
| na_b_01-001 | Verify B damage matches jpower/5+tier formula | P1 | PENDING | |
| na_b_01-002 | Document all move damage values | P2 | PENDING | |
| na_b_01-003 | Identify shadow clone attack patterns | P2 | PENDING | |
| na_b_01-004 | Test for any buff/powered states | P2 | PENDING | |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs) - **P1 PRIORITY: Use to verify damage formula**
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
   - [ ] Shadow clone behavior documentation
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact koma sizes available in deck builder
2. battleParams byte values
3. jpower Block 17 entry contents

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. How do shadow clones (type5 entries) interact with jpower damage?
2. Does Naruto have any buff/powered states like Ichigo or Yusuke?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship           |
| ----------------- | ----------- | -------------- | ---------------------- |
| Kyuubi Naruto     | 21          | na_b_02.bin    | Powered form (7-8 koma) |
| Sasuke Uchiha     | 22          | na_b_03.bin    | Same series            |
| Sakura Haruno     | 23          | na_b_04.bin    | Same series            |
| Kakashi Hatake    | 24          | na_b_05.bin    | Same series            |

**Characters sharing jpower Block 17:**

- Only Naruto uses Block 17 (classId=529)

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
- [Combat-Mechanics.md](../research/Combat-Mechanics.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
| 2026-01-29 | Initial creation | chr_b mapping | Created from template with extracted data |

---

## Notes

- Naruto has the 3rd highest collision entry count (46) among all characters
- High type5 (summon) usage indicates shadow clone-heavy playstyle
- Selected as test case for damage formula verification on non-Bleach character
- tier=2 means no damage modifier, so jpower/5 should equal actual damage directly
