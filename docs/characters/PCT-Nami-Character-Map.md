# Perfect Clima-Tact Nami (op_b_05) - Complete Character Mapping

Deep dive analysis mapping PCT Nami through all data files to understand linkages.

---

## Basic Info

| Field           | Value                       |
| --------------- | --------------------------- |
| Character Name  | Perfect Clima-Tact Nami     |
| Series          | One Piece                   |
| chr_b Index     | 16                          |
| Collision File  | op_b_05.bin                 |
| charId          | 4                           |
| tier            | 2 (assumed)                 |
| jpower Block    | 13                          |
| classId         | 525                         |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED from file analysis)

- **PCT Nami:** 6 koma only (powered-up form, single koma tier)

### Move List (NEEDS HUMAN TESTING)

| Move   | Damage | Type     | Notes                            |
| ------ | ------ | -------- | -------------------------------- |
| B      |        | Energy   | Weather attack                   |
| fwd B  |        | Energy   | Weather attack                   |
| up B   |        | Energy   | Weather attack                   |
| down B |        | Energy   | Weather attack                   |
| air B  |        | Energy   | Weather attack                   |
| Y      |        | Impact   | Staff combo                      |
| fwd Y  |        | Energy   | Weather projectile               |
| up Y   |        | Energy   | Weather projectile               |
| down Y |        | Energy   | Weather attack                   |
| air Y  |        | Energy   | Aerial weather attack            |

**Damage Types:**

- **Energy** - Weather-based projectile attacks (lightning, thunder, etc.)
- **Impact** - Staff physical attacks
- PCT Nami focuses on weather manipulation - likely more Energy attacks than base Nami

### Specials (X Moves)

| Koma | X Damage | X Notes           | up X Damage | up X Notes        |
| ---- | -------- | ----------------- | ----------- | ----------------- |
| 6    |          | Weather special   |             | Weather special   |

---

## File Data

### chr_b.bin Entry (Index 16)

| Field        | Value  | Notes                               |
| ------------ | ------ | ----------------------------------- |
| charId       | 4      | Different from base Nami (16)       |
| formType     | 1      | Powered-up form (enhanced weapon)   |
| tier         | 2      | Standard damage (+0 modifier)       |
| komaSize     |        | Internal size (not deck koma)       |
| classId      | 525    | Low byte = jpower block index       |
| jpower Block | 13     | Different from base Nami (12)       |

**Key Difference from Base Nami:**
- Different charId (4 vs 16)
- Different classId (525 vs 524)
- Different jpower block (13 vs 12)
- formType = 1 (powered vs 0 normal)

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

Profile: UNKNOWN
```

### Collision File (op_b_05.bin)

| Property    | Value             |
| ----------- | ----------------- |
| Size        |                   |
| Entry Count | 37                |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |

**Notes:**

- 37 collision entries (significantly more than base Nami's 22)
- Increased entry count likely due to weather attack complexity
- damageFlags field does NOT represent actual damage values

### jpower Block 13 Analysis

**Block 13 contents:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
| 0     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 1     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 2     |           | ?   | ?   | ?   | 7     | ~1-2              |       |

**Block 13 Damage totals:** [7, 7, 7]

**Note:** PCT Nami has her own jpower block (13), different from base Nami (12).

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)
```

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| op_b_05c.aar         |      | Main sprites    |
| op_b_05_6c.aar       |      | 6-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character      |
| -------- | ------------------------------------- | ------------------- |
| 0x0924B0 | Collision file pointer table          | Index 16            |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 16            |
| 0x09E780 | Koma name table                       |                     |

---

## Mechanics

### Weight Category

**Category:** LIGHT (assumed - same as base Nami)

**Observations:**

- Displacement velocity: Unknown (test vs base Nami)
- Walk speed: Unknown (likely same as base Nami)
- If weight/speed differs from base Nami, reveals per-form storage

### Movement

| Property      | Value          | Notes                              |
| ------------- | -------------- | ---------------------------------- |
| Walk Speed    | Unknown        | Likely FAST like base Nami         |
| Dash Type     | Unknown        | Likely Standard like base Nami     |
| Dash Distance |                |                                    |

### Unique Mechanics

**Perfect Clima-Tact:**
- Upgraded version of Nami's weapon
- Focuses on weather manipulation attacks
- More projectile/energy attacks than base form
- 37 collision entries vs base Nami's 22 - more complex moveset
- Single 6-koma tier (high investment required)

**Weather Attacks:**
- Lightning
- Thunder
- Possibly other weather phenomena

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                          | Priority | Status    | Result |
| ----------- | ----------------------------------------- | -------- | --------- | ------ |
| op_b_05-001 | Full B move damage values (neutral)       | P2       | PENDING   |        |
| op_b_05-002 | Full Y combo damage breakdown             | P2       | PENDING   |        |
| op_b_05-003 | Special (X) damage (6-koma only)          | P2       | PENDING   |        |
| op_b_05-004 | Damage type for weather attacks (Energy?) | P2       | PENDING   |        |
| op_b_05-005 | Walk speed comparison vs base Nami        | P2       | PENDING   |        |
| op_b_05-006 | Weight comparison vs base Nami            | P2       | PENDING   |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y / up Y / down Y damage
   - [ ] 6-koma X and up X damage

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to base Nami)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs base Nami)

3. **Damage Type Verification**
   - [ ] Weather attacks - Energy type?
   - [ ] Staff attacks - Impact type?
   - [ ] Test with both defensive passives

---

## Unknown / Needs Research

### Unverified Data

1. Exact damage values for all moves
2. battleParams byte values
3. Whether weight/speed differs from base Nami

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] 6-koma special damage (needs human testing)
- [ ] Exact weather attack mechanics
- [ ] Whether PCT Nami has same weight/speed as base Nami

### Open Questions

1. Does PCT Nami share weight/speed with base Nami, or does the powered form change these?
2. What damage type are weather attacks? (Energy, Special, or something else)
3. Why does PCT Nami have significantly more collision entries than base Nami (37 vs 22)?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship                      |
| ----------------- | ----------- | -------------- | --------------------------------- |
| Nami (Base)       | 15          | op_b_04        | Base form, different moveset      |
| Franky            | 19          | op_b_08        | Base Nami's chr_b paradox partner |

**Characters sharing charId 4:**

- op_b_05 (PCT Nami)
- (Others to be identified)

**Characters sharing jpower Block 13:**

- op_b_05 (PCT Nami) only

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
- [Character-Mapping.md](../research/Character-Mapping.md)
- [Nami-Character-Map.md](./Nami-Character-Map.md) - Base form

---

## Session Log

| Date       | Session | Verified | Notes                                |
| ---------- | ------- | -------- | ------------------------------------ |
| 2026-01-29 | Initial | No       | Created from research docs, untested |

---

## Notes

- PCT = Perfect Clima-Tact (upgraded weather weapon)
- Powered-up form of base Nami (formType=1)
- Only available as 6-koma (high deck investment)
- Weather-focused moveset with 37 collision entries (vs 22 for base)
- Has unique charId (4), different from base Nami (16)
- Has unique jpower block (13), different from base Nami (12)
- Unlike Luffy/Gear 2 or Ichigo/Bankai, PCT Nami has completely different chr_b linkages from base
