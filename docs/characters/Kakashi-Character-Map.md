# Kakashi Hatake (na_b_05) - Complete Character Mapping

Deep dive analysis mapping Kakashi Hatake through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Kakashi Hatake         |
| Series          | Naruto                 |
| chr_b Index     | 24                     |
| Collision File  | na_b_05.bin            |
| charId          | 54                     |
| tier            | TBD                    |
| jpower Block    | 22                     |
| classId         | 278                    |

---

## In-Game Verified Data

### Koma Sizes (NEEDS VERIFICATION)

- **Kakashi:** TBD koma

### Move List (NEEDS TESTING)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        | Slashing   | Shuriken (slash dmg)  |
| fwd B  |        | Slashing   |                       |
| up B   |        | Slashing   |                       |
| down B |        | Punch/Kick | Summons dogs          |
| air B  |        | Slashing   |                       |
| Y      |        | Punch/Kick |                       |
| fwd Y  |        | Punch/Kick | May summon dogs       |
| up Y   |        | Punch/Kick | May summon dogs       |
| down Y |        | Punch/Kick | May summon dogs       |
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
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 24)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 54    | Stat template (shared with Gotenks SSJ, Frieza, Dio, Train, Kazuki) |
| formType     | 0     | Normal form                    |
| tier         | TBD   | Check for damage modifier      |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 278   | Low byte = jpower block index  |
| jpower Block | 22    | classId & 0xFF = 22            |

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

### Collision File (na_b_05.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | TBD                      |
| Entry Count | 26                       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

- Summons dogs per Character-Mapping.md
- Slashing shuriken noted
- May have type5 (summon) entries for dog attacks

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      | NEEDS EXTRACTION |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries
- Dog summons should appear as type5 entries

### jpower Block 22 Analysis

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       | NEEDS EXTRACTION  |       |

**Damage Formula:**

```
base_damage = (jpower_total / 5) + (tier - 2)
```

- tier 1: -1 modifier
- tier 2: no modifier
- tier 3: +1 modifier

**Note:** Block 22 is also used by Yoh (sk_b_01) and Yoh White Swan (sk_b_02).

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| na_b_05c.aar         |      | Main sprites    |
| na_b_05_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 24                    |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 24                    |
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
| Dash Type     | NEEDS TESTING      | Standard / Flash (may flash)       |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**Dog Summoning:**
- Summons dogs for certain attacks
- Dogs are likely type5 (summon) collision entries
- May function similar to Yugi's monster summons or Dio's Stand

**Slashing Shuriken:**
- Shuriken attacks deal slash damage, not impact
- Unusual for thrown weapons (typically impact)
- Test with Slash Defense passive to confirm

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
| na_b_05-001 | Document all move damage values | P2 | PENDING | |
| na_b_05-002 | Verify shuriken = slash damage | P2 | PENDING | |
| na_b_05-003 | Catalog dog summon attacks | P2 | PENDING | |

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
   - [ ] Dash type (standard or flash - elite ninja may flash)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Which moves summon dogs
   - [ ] Dog summon behavior and damage
   - [ ] Confirm shuriken = slash damage (use Slash Defense passive)
   - [ ] Any Sharingan or copy mechanics
   - [ ] Any buffs or special states

---

## Unknown / Needs Research

### Unverified Data

1. Exact koma sizes available
2. tier value
3. battleParams byte values
4. Which specific moves summon dogs

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Do dog summons persist like Yugi's traps?
2. Can dogs be hit like Taikoubou's summon?
3. Does Kakashi have any Sharingan-based mechanics?
4. Why do Kakashi and Yoh share jpower Block 22?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship           |
| ----------------- | ----------- | -------------- | ---------------------- |
| Naruto Uzumaki    | 20          | na_b_01.bin    | Same series, student   |
| Kyuubi Naruto     | 21          | na_b_02.bin    | Same series            |
| Sasuke Uchiha     | 22          | na_b_03.bin    | Same series, student   |
| Sakura Haruno     | 23          | na_b_04.bin    | Same series, student   |
| Yoh Asakura       | 25          | sk_b_01.bin    | Shares jpower Block 22 |
| Yoh (White Swan)  | 26          | sk_b_02.bin    | Shares jpower Block 22 |

**Characters sharing charId=54:**

- Gotenks SSJ (db_b_09)
- Frieza (db_b_11)
- Kakashi Hatake (na_b_05)
- Dio Brando (jj_b_02)
- Train Heartnet (bc_b_01)
- Kazuki Mutou (bu_b_01)

**Characters sharing jpower Block 22:**

- Kakashi Hatake (na_b_05) - classId=278
- Yoh Asakura (sk_b_01) - classId=534
- Yoh White Swan (sk_b_02) - classId=534

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

- Shares charId=54 with other technical fighters (Dio, Frieza, Train)
- Shares jpower Block 22 with Yoh variants - interesting cross-series connection
- Dog summons and slashing shuriken are unique mechanics worth investigating
- 26 collision entries suggests moderate complexity
- Elite ninja may have flash dash like Dio and Ichigo
- Slashing shuriken is notable - thrown weapons usually deal impact damage
