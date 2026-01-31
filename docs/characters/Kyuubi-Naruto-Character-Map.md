# Kyuubi Naruto (na_b_02) - Complete Character Mapping

Deep dive analysis mapping Kyuubi Naruto through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Kyuubi Naruto          |
| Series          | Naruto                 |
| chr_b Index     | 21                     |
| Collision File  | na_b_02.bin            |
| charId          | 13                     |
| tier            | TBD                    |
| jpower Block    | 18                     |
| classId         | 274                    |

---

## In-Game Verified Data

### Koma Sizes (EXPECTED)

- **Kyuubi Naruto:** 7, 8 koma (powered form pattern, like Bankai Ichigo)

### Move List (NEEDS TESTING)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      | **8**  | Punch/Kick | tier=1 verified (d1=45, 45/5-1=8) |
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
| 7    |          |         |             |            |
| 8    |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 21)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 13    | Stat template (shared with Sakura, Jotaro, Kenshiro, Raoh, Seiya) |
| formType     | TBD   | Likely 1 (Powered)             |
| tier         | TBD   | Check if tier=1 like Bankai    |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 274   | Low byte = jpower block index  |
| jpower Block | 18    | classId & 0xFF = 18            |

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

### Collision File (na_b_02.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | TBD                      |
| Entry Count | 30                       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

- Fewer entries than base Naruto (30 vs 46)
- Different moveset from base form

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      | NEEDS EXTRACTION |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 18 Analysis

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       | NEEDS EXTRACTION  |       |

**Damage Formula:**

```
base_damage = (jpower_total / 5) + (tier - 2)
```

- If tier=1 (like Bankai): -1 damage modifier
- If tier=2: No modifier (+0)
- Check tier value to determine expected damage

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| na_b_02c.aar         |      | Main sprites    |
| na_b_02_7c.aar       |      | 7-koma portrait |
| na_b_02_8c.aar       |      | 8-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 21                    |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 21                    |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** STANDARD (expected, may differ from base)

**Observations:**

- Displacement velocity: NEEDS TESTING
- Walk speed: NEEDS TESTING
- Compare to base Naruto for any differences

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

**Kyuubi Transformation:**
- Different moveset from base Naruto (30 vs 46 collision entries)
- Likely more aggressive/raw power focused compared to clone-heavy base
- Pattern matches other powered forms (Bankai Ichigo, Gear 2 Luffy)

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
| na_b_02-001 | Verify tier value and damage modifier | P2 | PENDING | |
| na_b_02-002 | Document all move damage values | P2 | PENDING | |
| na_b_02-003 | Compare moveset to base Naruto | P2 | PENDING | |

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
   - [ ] All X move damage at each koma size (7, 8)

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, base Naruto)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs base Naruto)

3. **Unique Mechanics**
   - [ ] Document how moveset differs from base Naruto
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact tier value (may be 1 like Bankai for -1 damage)
2. formType value (expected 1 for Powered)
3. battleParams byte values

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Kyuubi Naruto have tier=1 like Bankai Ichigo?
2. How much moveset overlap exists with base Naruto?
3. Does the Kyuubi form have any unique buff mechanics?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship           |
| ----------------- | ----------- | -------------- | ---------------------- |
| Naruto Uzumaki    | 20          | na_b_01.bin    | Base form              |
| Sasuke Uchiha     | 22          | na_b_03.bin    | Same series            |
| Sakura Haruno     | 23          | na_b_04.bin    | Shares charId=13       |
| Kakashi Hatake    | 24          | na_b_05.bin    | Same series            |

**Characters sharing charId=13:**

- Kyuubi Naruto (na_b_02)
- Sakura Haruno (na_b_04)
- Jotaro Kujo (jj_b_01)
- Kenshiro (hk_b_01)
- Raoh (hk_b_02)
- Seiya (ss_b_01)
- Gold Seiya (ss_b_02)

**Characters sharing jpower Block 18:**

- Only Kyuubi Naruto uses Block 18 (classId=274)

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
- [Naruto-Character-Map.md](./Naruto-Character-Map.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
| 2026-01-29 | Initial creation | chr_b mapping | Created from template with extracted data |

---

## Notes

- Powered form of base Naruto (7-8 koma variant)
- Fewer collision entries (30) than base (46), suggesting simpler but more powerful moveset
- Shares charId=13 with several heavy hitters (Kenshiro, Raoh, Jotaro)
- Pattern matches other powered forms: different moveset, higher koma sizes
- Need to verify tier value - if tier=1, expect -1 damage like Bankai Ichigo
