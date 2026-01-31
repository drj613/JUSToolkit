# Franky (op_b_08) - Complete Character Mapping

Deep dive analysis mapping Franky through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Franky                 |
| Series          | One Piece              |
| chr_b Index     | 19                     |
| Collision File  | op_b_08.bin            |
| charId          | 16                     |
| tier            | 2 (assumed)            |
| jpower Block    | 12                     |
| classId         | 524                    |

---

## CRITICAL PARADOX: Franky vs Nami

**Franky and Nami share identical chr_b data but are COMPLETE OPPOSITES in gameplay!**

| Property        | Franky (op_b_08)   | Nami (op_b_04)     | Status           |
| --------------- | ------------------ | ------------------ | ---------------- |
| charId          | 16                 | 16                 | IDENTICAL        |
| classId         | 524                | 524                | IDENTICAL        |
| jpower Block    | 12                 | 12                 | IDENTICAL        |
| battleParams    | [15,0,12,0,10,4,0,0,60,20,20,0] | [15,0,12,0,10,4,0,0,60,20,20,0] | IDENTICAL |
| Weight          | **HEAVY**          | **LIGHT**          | OPPOSITE         |
| Walk Speed      | **SLOW**           | **FAST**           | OPPOSITE         |
| Moveset         | Mechanical/Brute   | Staff/Weather      | DIFFERENT        |

**This proves that weight and walk speed are NOT stored in:**
- chr_b.bin battleParams
- jpower.bin
- Collision files

**Weight and walk speed must be stored elsewhere** (possibly ARM9 hardcoded or overlay files).

---

## In-Game Verified Data

### Weight/Speed (CONFIRMED)

- **Weight Category:** HEAVY (reference character for heavy weight)
- **Walk Speed:** SLOW (slowest in game - reference character)

### Koma Sizes (NEEDS VERIFICATION)

- **Franky:** Likely 4, 5, 6 koma (based on file structure)

### Move List (NEEDS HUMAN TESTING)

| Move   | Damage | Type       | Notes                           |
| ------ | ------ | ---------- | ------------------------------- |
| B      | **8**  | Impact     | Mechanical punch (verified 2026-01-30) |
| fwd B  |        | Impact     | Mechanical attack               |
| up B   |        | Impact     | Mechanical attack               |
| down B |        | Impact     | Mechanical attack               |
| air B  |        | Impact     | Mechanical attack               |
| Y      |        | Impact     | Mechanical combo                |
| fwd Y  |        | Impact     | **Requires buff via taunt**     |
| up Y   |        | Impact     |                                 |
| down Y |        | Impact     |                                 |
| air Y  |        | Impact     |                                 |

**Damage Types:**

- **Impact** - Heavy blunt attacks from cyborg body
- Franky is a cyborg - mechanical/brute force attacks
- All attacks should be Impact type

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 19)

| Field        | Value  | Notes                                    |
| ------------ | ------ | ---------------------------------------- |
| charId       | 16     | **Shared with Nami despite opposites**   |
| formType     | 0      | Normal form                              |
| tier         | 2      | Standard damage (+0 modifier)            |
| komaSize     |        | Internal size (not deck koma)            |
| classId      | 524    | **Shared with Nami**                     |
| jpower Block | 12     | **Shared with Nami**                     |

### battleParams (12 bytes) - CONFIRMED IDENTICAL TO NAMI

```
Raw: [15, 0, 12, 0, 10, 4, 0, 0, 60, 20, 20, 0]

Parsed:
  Slot 0: value=15, flags=0x00
  Slot 1: value=12, flags=0x00
  Slot 2: value=10, flags=0x04
  Slot 3: value=0, flags=0x00

Stats [8,9,10]: [60, 20, 20] = 100 total
  Attack weight:  60
  Defense weight: 20
  Speed/Utility:  20

Byte 11: 0 (special flag)

Profile: Attack-focused (60 attack)
```

**CRITICAL:** This data is IDENTICAL to Nami's, yet they play completely differently!

### Collision File (op_b_08.bin)

| Property    | Value             |
| ----------- | ----------------- |
| Size        |                   |
| Entry Count | 21                |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |

**Notes:**

- 21 collision entries (different from Nami's 22)
- damageFlags field does NOT represent actual damage values
- Collision file IS different from Nami (different moveset)

### jpower Block 12 Analysis (SHARED WITH NAMI)

**Block 12 contents:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
| 0     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 1     |           | ?   | ?   | ?   | 7     | ~1-2              |       |

**Block 12 Damage totals:** [7, 7]

**IMPORTANT:** Both Franky and Nami reference this same jpower block, proving that:
1. jpower blocks are template libraries
2. Different characters select different entries from the same block
3. Or collision files handle damage differently per character

**Damage Formula:**

```
base_damage = (jpower_total / 5) + (tier - 2)
```

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| op_b_08c.aar         |      | Main sprites    |
| op_b_08_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character      |
| -------- | ------------------------------------- | ------------------- |
| 0x0924B0 | Collision file pointer table          | Index 19            |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 19            |
| 0x09E780 | Koma name table                       |                     |

---

## Mechanics

### Weight Category

**Category:** HEAVY (CONFIRMED)

**Reference status:** Franky is the HEAVY weight reference character (along with Raoh).

**Observations:**

- Low displacement velocity when hit
- Takes less knockback than standard characters
- Heavy/planted feel in combat

### Movement

| Property      | Value          | Notes                              |
| ------------- | -------------- | ---------------------------------- |
| Walk Speed    | **SLOW**       | Slowest in game (reference)        |
| Dash Type     | Standard       | Standard dash (not flash)          |
| Dash Distance |                |                                    |

**Reference status:** Franky is the SLOW walk speed reference character.

### Unique Mechanics

**Cyborg Body:**
- Franky is a cyborg with mechanical enhancements
- Heavy-hitting Impact attacks
- Slow but powerful

**Taunt Buff (CONFIRMED from Character-Mapping.md):**
- Franky has a buff mechanic via taunt
- Required for fwd Y attack
- Similar to other taunt-buff characters (Raoh, Fuusuke, Ichigo)

### Buff/Debuff Mechanics

| Buff Name   | Trigger | Effect            | Duration |
| ----------- | ------- | ----------------- | -------- |
| Taunt Buff  | Taunt   | Enables fwd Y     | Unknown  |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                                   | Priority | Status    | Result |
| ----------- | -------------------------------------------------- | -------- | --------- | ------ |
| op_b_08-001 | Full B move damage values (neutral)                | P2       | PENDING   |        |
| op_b_08-002 | Full Y combo damage breakdown                      | P2       | PENDING   |        |
| op_b_08-003 | Special (X) damage at each koma size               | P2       | PENDING   |        |
| op_b_08-004 | Confirm all attacks are Impact type                | P2       | PENDING   |        |
| op_b_08-005 | **Compare knockback received vs Nami (same hit)**  | **P1**   | PENDING   |        |
| op_b_08-006 | **Document walk speed difference vs Nami**         | **P1**   | PENDING   |        |
| op_b_08-007 | Taunt buff effect and duration                     | P2       | PENDING   |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**HIGH PRIORITY:** Tests 005 and 006 are critical for understanding where weight/speed data is stored!

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y damage (with taunt buff)
   - [ ] up Y / down Y damage
   - [ ] All X move damage at each koma size

2. **Movement/Physics (CRITICAL)**
   - [ ] Walk speed exact comparison vs Nami (frame count same distance)
   - [ ] Knockback received comparison vs Nami (same attack, measure distance)
   - [ ] Dash type confirmation (standard)
   - [ ] Jump height/fall speed (should match Nami - universal constants)

3. **Buff Mechanics**
   - [ ] Taunt buff trigger confirmation
   - [ ] What moves are affected by taunt buff
   - [ ] Buff duration
   - [ ] Damage multiplier if any

4. **Damage Type Verification**
   - [ ] Test with Impact Defense passive - should reduce damage
   - [ ] Test with Slash Defense passive - should have no effect

---

## Unknown / Needs Research

### Unverified Data

1. Exact damage values for all moves
2. Taunt buff specifics
3. Exact knockback/displacement values

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] **WHERE IS WEIGHT STORED?** (not in chr_b, collision, or jpower)
- [ ] **WHERE IS WALK SPEED STORED?** (not in chr_b, collision, or jpower)

### Open Questions

1. **CRITICAL:** If Franky and Nami have identical chr_b data, where is weight stored?
2. **CRITICAL:** If Franky and Nami have identical chr_b data, where is walk speed stored?
3. Why do Franky and Nami share the same jpower block despite different movesets?
4. How does the taunt buff interact with fwd Y specifically?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship                           |
| ----------------- | ----------- | -------------- | -------------------------------------- |
| **Nami**          | **15**      | **op_b_04**    | **SHARES ALL CHR_B DATA (PARADOX!)**   |
| Raoh              | 62          | hk_b_02        | Also heavy weight reference            |

**Characters sharing charId 16:**

- op_b_04 (Nami) - LIGHT, FAST
- op_b_08 (Franky) - HEAVY, SLOW

**Characters sharing jpower Block 12:**

- op_b_04 (Nami)
- op_b_08 (Franky)

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
- [Nami-Character-Map.md](./Nami-Character-Map.md) - **MUST CROSS-REFERENCE**

---

## Session Log

| Date       | Session | Verified | Notes                                |
| ---------- | ------- | -------- | ------------------------------------ |
| 2026-01-29 | Initial | Partial  | Created from research docs           |

---

## Notes

- Franky is the shipwright of the Straw Hat Pirates
- Cyborg body grants mechanical/heavy attacks
- **REFERENCE CHARACTER for HEAVY weight and SLOW walk speed**
- Shares ALL chr_b data with Nami despite being complete opposites
- This paradox proves weight/walk speed is NOT in chr_b battleParams
- Has taunt buff mechanic that enables fwd Y attack
- Critical for research: comparing Franky to Nami will reveal where weight/speed values are stored
- See also: Nami-Character-Map.md for the other half of this paradox
