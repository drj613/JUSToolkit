# Nico Robin (op_b_07) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Robin through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Nico Robin             |
| Series          | One Piece              |
| chr_b Index     | 18                     |
| Collision File  | op_b_07.bin            |
| charId          | 9                      |
| tier            | 2 (assumed)            |
| jpower Block    | 9                      |
| classId         | 521                    |

---

## CRITICAL: Shared Data with Luffy

**Robin and Luffy share identical classId, charId, and jpower block but have COMPLETELY DIFFERENT MOVESETS!**

| Property        | Robin (op_b_07)    | Luffy (op_b_01)    | Status           |
| --------------- | ------------------ | ------------------ | ---------------- |
| charId          | 9                  | 9                  | IDENTICAL        |
| classId         | 521                | 521                | IDENTICAL        |
| jpower Block    | 9                  | 9                  | IDENTICAL        |
| Moveset         | Arm Spawning       | Rubber Stretching  | DIFFERENT        |
| Collision Count | 32                 | 38                 | DIFFERENT        |

**This proves that:**
1. jpower blocks are **template libraries**, not 1:1 movesets
2. Characters select specific entries from their assigned block
3. Selection mechanism is still unknown (collision subType? move index?)

---

## In-Game Verified Data

### Koma Sizes (NEEDS VERIFICATION)

- **Robin:** Likely 4, 5, 6 koma (based on file structure)

### Move List (NEEDS HUMAN TESTING)

| Move   | Damage | Type       | Notes                              |
| ------ | ------ | ---------- | ---------------------------------- |
| B      | **8**  | Impact     | Arm spawn attack (verified 2026-01-30) |
| fwd B  |        | Impact     | Arm spawn attack                   |
| up B   |        | Impact     | Arm spawn attack                   |
| down B |        | Impact     | Arm spawn attack                   |
| air B  |        | Impact     | Arm spawn attack                   |
| Y      |        | Impact     | Arm spawn combo                    |
| fwd Y  |        | Impact     | Arm spawn attack                   |
| up Y   |        | Impact     | Arm spawn attack                   |
| down Y |        | Impact     | Arm spawn attack                   |
| air Y  |        | Impact     | Arm spawn attack                   |

**Damage Types:**

- **Impact** - Blunt attacks from spawned arms (grappling, striking)
- Robin uses Hana Hana no Mi (Flower-Flower Fruit) to sprout arms
- All attacks should be Impact/grab type

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 18)

| Field        | Value  | Notes                                   |
| ------------ | ------ | --------------------------------------- |
| charId       | 9      | **Shared with Luffy**                   |
| formType     | 0      | Normal form                             |
| tier         | 2      | Standard damage (+0 modifier)           |
| komaSize     |        | Internal size (not deck koma)           |
| classId      | 521    | **Shared with Luffy**                   |
| jpower Block | 9      | **Shared with Luffy** - template block  |

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

### Collision File (op_b_07.bin)

| Property    | Value             |
| ----------- | ----------------- |
| Size        |                   |
| Entry Count | 32                |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |

**Notes:**

- 32 collision entries (vs Luffy's 38)
- Arm spawning attacks - unique hitbox placement
- May have grab/hold mechanics
- damageFlags field does NOT represent actual damage values

### jpower Block 9 Analysis (SHARED WITH LUFFY)

**Block 9 contents:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
| 0     |           | ?   | ?   | ?   | 57    | 11 (with /5+tier) |       |
| 1-9   |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 10    |           | ?   | ?   | ?   | 14    | ~3                |       |

**Block 9 Damage totals:** [57, 7, 7, 7, 7, 7, 7, 7, 7, 7, 14]

**CRITICAL:** This is the SAME block Luffy uses, but Robin's moves are completely different!
- Luffy: Rubber stretching (Gomu Gomu attacks)
- Robin: Arm spawning (Hana Hana attacks)

**This proves jpower blocks are SHARED TEMPLATE LIBRARIES.**

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)
```

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| op_b_07c.aar         |      | Main sprites    |
| op_b_07_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character      |
| -------- | ------------------------------------- | ------------------- |
| 0x0924B0 | Collision file pointer table          | Index 18            |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 18            |
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

**Hana Hana no Mi (Flower-Flower Fruit):**
- Robin can sprout arms (and other body parts) anywhere
- Attacks spawn from unexpected locations
- 32 collision entries suggest varied arm placement attacks
- May have grab/hold/clutch mechanics

**Arm Spawning:**
- Arms can appear on opponent's body
- May bypass normal hitbox interactions
- Likely has unique range/positioning compared to other characters

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                              | Priority | Status    | Result |
| ----------- | --------------------------------------------- | -------- | --------- | ------ |
| op_b_07-001 | Full B move damage values (neutral)           | P2       | PENDING   |        |
| op_b_07-002 | Full Y combo damage breakdown                 | P2       | PENDING   |        |
| op_b_07-003 | Special (X) damage at each koma size          | P2       | PENDING   |        |
| op_b_07-004 | Confirm all attacks are Impact type           | P2       | PENDING   |        |
| op_b_07-005 | Walk speed comparison vs Goku                 | P2       | PENDING   |        |
| op_b_07-006 | Weight comparison vs Goku                     | P2       | PENDING   |        |
| op_b_07-007 | **Compare damage to Luffy (same jpower block)**| **P1**  | PENDING   |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**HIGH PRIORITY:** Test 007 helps understand how different characters use the same jpower block.

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

3. **Damage Comparison (CRITICAL)**
   - [ ] Compare B damage to Luffy's B damage (same block, different moveset)
   - [ ] Note any similarities in damage values despite different animations

4. **Damage Type Verification**
   - [ ] Test with Impact Defense passive - should reduce arm grab damage
   - [ ] Test with Slash Defense passive - should have no effect

---

## Unknown / Needs Research

### Unverified Data

1. Exact damage values for all moves
2. battleParams byte values
3. How Robin selects different jpower entries than Luffy from same block

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Arm spawn mechanics details
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. **CRITICAL:** How does Robin select different jpower entries than Luffy from Block 9?
2. Do arm spawn attacks have unique hitbox behavior?
3. Are there any grab/hold mechanics with extended hitstun?
4. Why do Robin and Luffy share charId=9 despite different fighting styles?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship                          |
| ----------------- | ----------- | -------------- | ------------------------------------- |
| **Luffy**         | **12**      | **op_b_01**    | **Shares charId, classId, jpower Block** |

**Characters sharing charId 9:**

- op_b_01 (Luffy) - Stretching attacks
- op_b_07 (Robin) - Arm spawning attacks

**Characters sharing jpower Block 9:**

- op_b_01 (Luffy) - Stretching attacks
- op_b_07 (Robin) - Arm spawning attacks

**NOTE:** This pairing (like Nami/Franky) reveals important information about data storage:
- charId is a **stat template**, not a character identifier
- jpower blocks are **template libraries**, not 1:1 movesets
- Different characters can select different entries from the same block

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
- [Luffy-Character-Map.md](./Luffy-Character-Map.md) - **MUST CROSS-REFERENCE**

---

## Session Log

| Date       | Session | Verified | Notes                                |
| ---------- | ------- | -------- | ------------------------------------ |
| 2026-01-29 | Initial | No       | Created from research docs, untested |

---

## Notes

- Robin is the archaeologist of the Straw Hat Pirates
- Uses Hana Hana no Mi (Flower-Flower Fruit) to sprout arms anywhere
- Shares ALL chr_b linkage data with Luffy (charId, classId, jpower block)
- This pairing proves jpower blocks are shared template libraries
- Different movesets despite identical block reference - selection mechanism unknown
- 32 collision entries - arm spawning attacks
- Critical for research: comparing Robin to Luffy will reveal jpower entry selection
- See also: Luffy-Character-Map.md for the other half of this data-sharing pair
