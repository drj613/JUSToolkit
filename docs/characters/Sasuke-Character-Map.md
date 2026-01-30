# Sasuke Uchiha (na_b_03) - Complete Character Mapping

Deep dive analysis mapping Sasuke Uchiha through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Sasuke Uchiha          |
| Series          | Naruto                 |
| chr_b Index     | 22                     |
| Collision File  | na_b_03.bin            |
| charId          | 8                      |
| tier            | TBD                    |
| jpower Block    | 19                     |
| classId         | 275                    |

---

## In-Game Verified Data

### Koma Sizes (NEEDS VERIFICATION)

- **Sasuke:** TBD koma

### Move List (NEEDS TESTING)

| Move   | Damage | Type       | Notes                        |
| ------ | ------ | ---------- | ---------------------------- |
| B      |        | Slashing   | Likely sword attacks         |
| fwd B  |        | Slashing   |                              |
| up B   |        | Slashing   |                              |
| down B |        | Impact     | May be blunt attack          |
| air B  |        | Slashing   |                              |
| Y      |        | Mixed      | Slash + blunt per research   |
| fwd Y  |        | Energy     | Lightning specials           |
| up Y   |        | Energy     | Lightning specials           |
| down Y |        | Energy     | Lightning specials           |
| air Y  |        | Energy     | Lightning specials           |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks (Chidori/Lightning)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 22)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 8     | Unique stat template           |
| formType     | 0     | Normal form                    |
| tier         | TBD   | Check for damage modifier      |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 275   | Low byte = jpower block index  |
| jpower Block | 19    | classId & 0xFF = 19            |

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

### Collision File (na_b_03.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | TBD                      |
| Entry Count | 22                       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

- Mixed damage types: slash + blunt per Character-Mapping.md
- Lightning specials suggest energy-type attacks

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      | NEEDS EXTRACTION |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries
- Lightning specials may interact with lightning damage reduction passives

### jpower Block 19 Analysis

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

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| na_b_03c.aar         |      | Main sprites    |
| na_b_03_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 22                    |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 22                    |
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

**Lightning/Chidori Attacks:**
- Lightning specials noted in Character-Mapping.md
- May interact with "Decreased lightning damage" passive
- Lightning damage may be subtype of damage2 (energy)

**Mixed Damage Profile:**
- Uses both slash and blunt attacks
- Sword user but may have some hitProperties overrides

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
| na_b_03-001 | Document all move damage values | P2 | PENDING | |
| na_b_03-002 | Verify damage types (slash vs impact) | P2 | PENDING | |
| na_b_03-003 | Test lightning damage with defensive passive | P2 | PENDING | |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y / up Y / down Y damage (Chidori variants)
   - [ ] All X move damage at each koma size

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast, Franky=slow)
   - [ ] Dash type (standard or flash - may teleport like Ichigo)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Lightning damage type verification (test vs lightning resistance passive)
   - [ ] Which moves are slash vs blunt
   - [ ] Any buffs or special states (Sharingan activation?)
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact koma sizes available
2. tier value
3. battleParams byte values
4. Lightning damage interaction with passives

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Is lightning damage a subtype of energy (damage2) or its own type?
2. Does Sasuke have any Sharingan-based buff mechanics?
3. Which specific moves are slash vs blunt?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship           |
| ----------------- | ----------- | -------------- | ---------------------- |
| Naruto Uzumaki    | 20          | na_b_01.bin    | Same series, rival     |
| Kyuubi Naruto     | 21          | na_b_02.bin    | Same series            |
| Sakura Haruno     | 23          | na_b_04.bin    | Same series, teammate  |
| Kakashi Hatake    | 24          | na_b_05.bin    | Same series, teacher   |

**Characters sharing charId=8:**

- Only Sasuke uses charId=8 (unique stat template)

**Characters sharing jpower Block 19:**

- Only Sasuke uses Block 19 (classId=275)

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

- Sasuke has a unique charId (8) - not shared with any other character
- Mixed damage profile (slash + blunt) makes damage type testing important
- Lightning specials may be key to understanding lightning damage subtype
- 22 collision entries is relatively low, suggesting straightforward moveset
- May have flash dash like other ninja/speed characters
