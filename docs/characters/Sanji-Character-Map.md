# Sanji (op_b_06) - Complete Character Mapping

Deep dive analysis mapping Sanji through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Sanji                  |
| Series          | One Piece              |
| chr_b Index     | 17                     |
| Collision File  | op_b_06.bin            |
| charId          | 10                     |
| tier            | 2 (assumed)            |
| jpower Block    | 14                     |
| classId         | 270                    |

---

## In-Game Verified Data

### Koma Sizes (NEEDS VERIFICATION)

- **Sanji:** Likely 4, 5, 6 koma (based on file structure)

### Move List (NEEDS HUMAN TESTING)

| Move   | Damage | Type       | Notes                           |
| ------ | ------ | ---------- | ------------------------------- |
| B      |        | Punch/Kick | Kick attack                     |
| fwd B  |        | Punch/Kick | Kick attack                     |
| up B   |        | Punch/Kick | Upward kick                     |
| down B |        | Punch/Kick | Low kick                        |
| air B  |        | Punch/Kick | Aerial kick                     |
| Y      |        | Punch/Kick | Kick combo                      |
| fwd Y  |        | Punch/Kick | Kick attack                     |
| up Y   |        | Punch/Kick | Kick attack                     |
| down Y |        | Punch/Kick | Kick attack                     |
| air Y  |        | Punch/Kick | Aerial kick                     |

**Damage Types:**

- **Punch/Kick** - Sanji only uses kicks (never punches due to character trait)
- All attacks should be Kick-type physical damage
- May register as Impact for damage reduction purposes

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 17)

| Field        | Value  | Notes                          |
| ------------ | ------ | ------------------------------ |
| charId       | 10     | Unique to Sanji                |
| formType     | 0      | Normal form                    |
| tier         | 2      | Standard damage (+0 modifier)  |
| komaSize     |        | Internal size (not deck koma)  |
| classId      | 270    | Low byte = jpower block index  |
| jpower Block | 14     | classId & 0xFF                 |

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

### Collision File (op_b_06.bin)

| Property    | Value             |
| ----------- | ----------------- |
| Size        |                   |
| Entry Count | 41                |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |

**Notes:**

- 41 collision entries - high count suggests complex kick combos
- One of the highest entry counts among One Piece characters
- All attacks should be kick-based (character never uses hands for combat)
- damageFlags field does NOT represent actual damage values

### jpower Block 14 Analysis

**Block 14 contents:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
| 0     |           | ?   | ?   | ?   | 57    | 11 (with /5+tier) |       |

**Block 14 Damage totals:** [57]

**Note:** Only 1 entry in Block 14 with total=57. This is unusual and suggests:
1. Most damage comes from collision files directly
2. The single entry is a base template multiplied
3. Selection mechanism works differently for this character

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)
```

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| op_b_06c.aar         |      | Main sprites    |
| op_b_06_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character      |
| -------- | ------------------------------------- | ------------------- |
| 0x0924B0 | Collision file pointer table          | Index 17            |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 17            |
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

**Kick-Only Combat:**
- Sanji NEVER uses his hands for attacks (protects them for cooking)
- All attacks are kicks
- 41 collision entries suggest many kick combo variants
- May have Diable Jambe (flaming leg) special moves

**Character Trait:**
- In One Piece, Sanji refuses to kick women
- Unknown if this affects gameplay (probably not)

### Buff/Debuff Mechanics

| Buff Name     | Trigger | Effect          | Duration |
| ------------- | ------- | --------------- | -------- |
| Diable Jambe? | Unknown | Fire damage?    | Unknown  |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                          | Priority | Status    | Result |
| ----------- | ----------------------------------------- | -------- | --------- | ------ |
| op_b_06-001 | Full B move damage values (neutral)       | P2       | PENDING   |        |
| op_b_06-002 | Full Y combo damage breakdown             | P2       | PENDING   |        |
| op_b_06-003 | Special (X) damage at each koma size      | P2       | PENDING   |        |
| op_b_06-004 | Confirm all attacks are Kick/Impact type  | P2       | PENDING   |        |
| op_b_06-005 | Walk speed comparison vs Goku             | P2       | PENDING   |        |
| op_b_06-006 | Weight comparison vs Goku                 | P2       | PENDING   |        |
| op_b_06-007 | Check for Diable Jambe mechanic           | P2       | PENDING   |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

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
   - [ ] Test with Impact Defense passive - should reduce kick damage
   - [ ] Test with Slash Defense passive - should have no effect
   - [ ] Any fire/special damage from Diable Jambe?

---

## Unknown / Needs Research

### Unverified Data

1. Exact damage values for all moves
2. battleParams byte values
3. Whether Diable Jambe exists as a mechanic

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Fire/special damage mechanics
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Why does jpower Block 14 only have 1 entry when Sanji has 41 collision entries?
2. Does Diable Jambe (flaming kick) exist as a buff or special mechanic?
3. Is there any damage type other than Impact/Kick in Sanji's moveset?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship                      |
| ----------------- | ----------- | -------------- | --------------------------------- |
|                   |             |                |                                   |

**Characters sharing charId 10:**

- op_b_06 (Sanji) only - unique charId

**Characters sharing jpower Block 14:**

- op_b_06 (Sanji) only - unique block

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

- Sanji is the cook of the Straw Hat Pirates
- Only uses kicks in combat (protects hands for cooking)
- Has 41 collision entries - one of the highest among One Piece characters
- Unique charId (10) and jpower block (14)
- jpower Block 14 has only 1 entry despite 41 collision entries - unusual
- May have Diable Jambe (flaming leg) special mechanic
- All damage should be Kick/Impact type
