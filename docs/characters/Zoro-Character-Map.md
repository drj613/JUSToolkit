# Roronoa Zoro (op_b_03) - Complete Character Mapping

Deep dive analysis mapping Zoro through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Roronoa Zoro           |
| Series          | One Piece              |
| chr_b Index     | 14                     |
| Collision File  | op_b_03.bin            |
| charId          | 18                     |
| tier            | 2 (assumed)            |
| jpower Block    | 11                     |
| classId         | 523                    |

---

## In-Game Verified Data

### Koma Sizes (NEEDS VERIFICATION)

- **Zoro:** Likely 4, 5, 6 koma (based on file structure)

### Move List (NEEDS HUMAN TESTING)

| Move   | Damage | Type     | Notes                           |
| ------ | ------ | -------- | ------------------------------- |
| B      |        | Slashing | Three-sword style               |
| fwd B  |        | Slashing | Sword attack                    |
| up B   |        | Slashing | Upward slash                    |
| down B |        | Slashing | Downward slash                  |
| air B  |        | Slashing | Aerial sword attack             |
| Y      |        | Slashing | Multi-hit combo                 |
| fwd Y  |        | Slashing |                                 |
| up Y   |        | Slashing |                                 |
| down Y |        | Slashing |                                 |
| air Y  |        | Slashing |                                 |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- Zoro is a swordsman - all attacks should be Slashing type
- **Impact** - Blunt attacks (Zoro may have some pommel/hilt attacks)

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 14)

| Field        | Value  | Notes                          |
| ------------ | ------ | ------------------------------ |
| charId       | 18     | Unique to Zoro                 |
| formType     | 0      | Normal form                    |
| tier         | 2      | Standard damage (+0 modifier)  |
| komaSize     |        | Internal size (not deck koma)  |
| classId      | 523    | Low byte = jpower block index  |
| jpower Block | 11     | classId & 0xFF                 |

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

### Collision File (op_b_03.bin)

| Property    | Value             |
| ----------- | ----------------- |
| Size        |                   |
| Entry Count | 51                |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |

**Notes:**

- **51 collision entries** - Second highest in the game (only Kinnikuman has more at 60)
- High entry count suggests many multi-hit combos and complex moveset
- Blade damage type expected on most attacks
- damageFlags field does NOT represent actual damage values

### jpower Block 11 Analysis

**Block 11 contents:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
| 0     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 1     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 2     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 3     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 4     |           | ?   | ?   | ?   | 7     | ~1-2              |       |

**Block 11 Damage totals:** [7, 7, 7, 7, 7]

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)
```

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| op_b_03c.aar         |      | Main sprites    |
| op_b_03_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character      |
| -------- | ------------------------------------- | ------------------- |
| 0x0924B0 | Collision file pointer table          | Index 14            |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 14            |
| 0x09E780 | Koma name table                       |                     |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed)

**Observations:**

- Displacement velocity: Unknown
- Walk speed: Unknown
- Comparison to reference characters: Needs testing

### Movement

| Property      | Value          | Notes                              |
| ------------- | -------------- | ---------------------------------- |
| Walk Speed    | Unknown        | Slow / Normal / Fast               |
| Dash Type     | Unknown        | Standard / Flash                   |
| Dash Distance |                |                                    |

### Unique Mechanics

**Three-Sword Style (Santoryu):**
- Zoro wields three swords (one in mouth, two in hands)
- High collision entry count (51) suggests complex multi-hit combos
- All attacks should deal Slashing damage type
- May have Slash Defense passive effectiveness against him reduced

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
| op_b_03-001 | Full B move damage values (neutral)       | P2       | PENDING   |        |
| op_b_03-002 | Full Y combo damage breakdown (multi-hit) | P2       | PENDING   |        |
| op_b_03-003 | Special (X) damage at each koma size      | P2       | PENDING   |        |
| op_b_03-004 | Confirm all attacks are Slashing type     | P2       | PENDING   |        |
| op_b_03-005 | Walk speed comparison vs Goku             | P2       | PENDING   |        |
| op_b_03-006 | Weight comparison vs Goku                 | P2       | PENDING   |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit) - expect many hits
   - [ ] fwd Y / up Y / down Y damage
   - [ ] All X move damage at each koma size

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast, Franky=slow)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Damage Type Verification**
   - [ ] Test with Slash Defense passive - all attacks should be reduced
   - [ ] Test with Impact Defense passive - should have no effect
   - [ ] Any exceptions (Guard Break type)?

---

## Unknown / Needs Research

### Unverified Data

1. Exact damage values for all moves
2. battleParams byte values
3. Whether any attacks are non-Slashing

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Exact hit count per combo
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. With 51 collision entries, how many unique attacks does Zoro have?
2. Do any attacks deal Impact or Guard Break damage instead of Slashing?
3. How do multi-hit combos interact with Slash Defense passive?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship                      |
| ----------------- | ----------- | -------------- | --------------------------------- |
|                   |             |                |                                   |

**Characters sharing charId 18:**

- op_b_03 (Zoro) only - unique charId

**Characters sharing jpower Block 11:**

- op_b_03 (Zoro) only - unique block

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

---

## Session Log

| Date       | Session | Verified | Notes                                |
| ---------- | ------- | -------- | ------------------------------------ |
| 2026-01-29 | Initial | No       | Created from research docs, untested |

---

## Notes

- Zoro is the swordsman of the Straw Hat Pirates
- Uses three-sword style (Santoryu) - unique fighting style
- Has the second-highest collision entry count in the game (51)
- Expected to be a primarily Slashing damage dealer
- Unique charId (18) and jpower block (11) - not shared with other characters
- High entry count suggests complex combo potential and multi-hit attacks
