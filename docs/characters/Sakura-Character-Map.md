# Sakura Haruno (na_b_04) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Sakura Haruno through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Sakura Haruno          |
| Series          | Naruto                 |
| chr_b Index     | 23                     |
| Collision File  | na_b_04.bin            |
| charId          | 13                     |
| tier            | TBD                    |
| jpower Block    | 20                     |
| classId         | 532                    |

---

## In-Game Verified Data

### Koma Sizes (NEEDS VERIFICATION)

- **Sakura:** TBD koma

### Move List (NEEDS TESTING)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        | Punch/Kick | Physical strikes      |
| fwd B  |        | Punch/Kick |                       |
| up B   |        | Punch/Kick |                       |
| down B |        | Punch/Kick |                       |
| air B  |        | Punch/Kick |                       |
| Y      |        | Punch/Kick |                       |
| fwd Y  |        | Energy     | Throws projectiles    |
| up Y   |        | Energy     | Throws projectiles    |
| down Y |        | Energy     | Throws projectiles    |
| air Y  |        | Energy     | Throws projectiles    |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 23)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 13    | Stat template (shared with Kyuubi Naruto, Jotaro, Kenshiro, etc.) |
| formType     | 0     | Normal form                    |
| tier         | TBD   | Check for damage modifier      |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 532   | Low byte = jpower block index  |
| jpower Block | 20    | classId & 0xFF = 20            |

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

### Collision File (na_b_04.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | TBD                      |
| Entry Count | 38                       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

- 38 entries suggests moderately complex moveset
- Throws projectiles per Character-Mapping.md notes
- May have type4 (projectile) entries

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      | NEEDS EXTRACTION |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries
- Projectile-throwing moves should have type4 collision entries

### jpower Block 20 Analysis

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       | NEEDS EXTRACTION  |       |

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
| na_b_04c.aar         |      | Main sprites    |
| na_b_04_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 23                    |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 23                    |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** LIGHT or STANDARD (need to verify)

**Observations:**

- Displacement velocity: NEEDS TESTING
- Walk speed: NEEDS TESTING
- Comparison to reference characters: Compare to Nami (light) or Goku (standard)

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

**Projectile Throwing:**
- Throws projectiles per documentation
- Kunai or shuriken likely
- May have multiple projectile variants

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
| na_b_04-001 | Document all move damage values | P2 | PENDING | |
| na_b_04-002 | Catalog projectile attacks | P2 | PENDING | |
| na_b_04-003 | Test weight class (light vs standard) | P3 | PENDING | |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y / up Y / down Y damage (projectile moves)
   - [ ] All X move damage at each koma size

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast, Franky=slow)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku, Nami)

3. **Unique Mechanics**
   - [ ] Projectile behavior documentation
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact koma sizes available
2. tier value
3. battleParams byte values
4. Projectile types and counts

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. What types of projectiles does Sakura throw?
2. Does she have any healing or support mechanics?
3. Weight class - female characters tend to be lighter?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship           |
| ----------------- | ----------- | -------------- | ---------------------- |
| Naruto Uzumaki    | 20          | na_b_01.bin    | Same series, teammate  |
| Kyuubi Naruto     | 21          | na_b_02.bin    | Shares charId=13       |
| Sasuke Uchiha     | 22          | na_b_03.bin    | Same series, teammate  |
| Kakashi Hatake    | 24          | na_b_05.bin    | Same series, teacher   |

**Characters sharing charId=13:**

- Kyuubi Naruto (na_b_02)
- Sakura Haruno (na_b_04)
- Jotaro Kujo (jj_b_01)
- Kenshiro (hk_b_01)
- Raoh (hk_b_02)
- Seiya (ss_b_01)
- Gold Seiya (ss_b_02)

**Characters sharing jpower Block 20:**

- Only Sakura uses Block 20 (classId=532)

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

- Shares charId=13 with several powerful characters (Kenshiro, Raoh, Jotaro)
- Interesting that a support-type character shares stat template with heavy hitters
- 38 collision entries indicates moderately complex moveset
- Projectile throwing noted as key mechanic
- May have unique support/healing abilities worth investigating
