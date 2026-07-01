# Nami (op_b_04) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Nami through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Nami                   |
| Series          | One Piece              |
| chr_b Index     | 15                     |
| Collision File  | op_b_04.bin            |
| charId          | 16                     |
| tier            | 2 (assumed)            |
| jpower Block    | 12                     |
| classId         | 524                    |

---

## CRITICAL PARADOX: Nami vs Franky

**Nami and Franky share identical chr_b data but are COMPLETE OPPOSITES in gameplay!**

| Property        | Nami (op_b_04)     | Franky (op_b_08)   | Status           |
| --------------- | ------------------ | ------------------ | ---------------- |
| charId          | 16                 | 16                 | IDENTICAL        |
| classId         | 524                | 524                | IDENTICAL        |
| jpower Block    | 12                 | 12                 | IDENTICAL        |
| battleParams    | [15,0,12,0,10,4,0,0,60,20,20,0] | [15,0,12,0,10,4,0,0,60,20,20,0] | IDENTICAL |
| Weight          | **LIGHT**          | **HEAVY**          | OPPOSITE         |
| Walk Speed      | **FAST**           | **SLOW**           | OPPOSITE         |
| Moveset         | Staff/Weather      | Mechanical/Brute   | DIFFERENT        |

**This proves that weight is NOT stored in:**
- chr_b.bin battleParams
- jpower.bin
- Collision files

**Weight must be stored elsewhere** (possibly ARM9 hardcoded or overlay files).

> **Correction (walk speed SOLVED):** Walk speed IS in chr_b.bin — the `statC`
> field (threshold/tier-based), which DIFFERS between Nami and Franky even
> though charId/classId/battleParams are identical. The earlier "walk speed
> not in chr_b" conclusion was confounded by Edajima (normal statC, slowed by
> an innate passive). See docs/research/Research-Status.md; thresholds: JUS-n3p.

---

## In-Game Verified Data

### Weight/Speed (CONFIRMED)

- **Weight Category:** LIGHT
- **Walk Speed:** FAST (fastest in game - reference character)

### Koma Sizes (NEEDS VERIFICATION)

- **Nami:** Likely 4, 5, 6 koma (base form)

### Move List (NEEDS HUMAN TESTING)

| Move   | Damage | Type        | Notes                           |
| ------ | ------ | ----------- | ------------------------------- |
| B      | **6**  | Impact      | Staff attack (verified 2026-01-30) |
| fwd B  |        | Impact      | Staff attack                    |
| up B   |        | Impact      | Upward staff                    |
| down B |        | Impact      | Downward staff                  |
| air B  |        | Impact      | Aerial staff                    |
| Y      |        | Impact      | Staff combo                     |
| fwd Y  |        | Impact      |                                 |
| up Y   |        | Impact      |                                 |
| down Y |        | Impact      |                                 |
| air Y  |        | Impact      |                                 |

**Damage Types:**

- **Impact** - Blunt attacks (staff is not a blade)
- Nami uses Clima-Tact (weather staff) - blunt weapon

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 15)

| Field        | Value  | Notes                                    |
| ------------ | ------ | ---------------------------------------- |
| charId       | 16     | **Shared with Franky despite opposites** |
| formType     | 0      | Normal form                              |
| tier         | 2      | Standard damage (+0 modifier)            |
| komaSize     |        | Internal size (not deck koma)            |
| classId      | 524    | **Shared with Franky**                   |
| jpower Block | 12     | **Shared with Franky**                   |

### battleParams (12 bytes) - CONFIRMED IDENTICAL TO FRANKY

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

**CRITICAL:** This data is IDENTICAL to Franky's, yet they play completely differently!

### Collision File (op_b_04.bin)

| Property    | Value             |
| ----------- | ----------------- |
| Size        |                   |
| Entry Count | 22                |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |

**Notes:**

- 22 collision entries (different from Franky's 21)
- damageFlags field does NOT represent actual damage values
- Collision file IS different from Franky (different moveset)

### jpower Block 12 Analysis (SHARED WITH FRANKY)

**Block 12 contents:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
| 0     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 1     |           | ?   | ?   | ?   | 7     | ~1-2              |       |

**Block 12 Damage totals:** [7, 7]

**IMPORTANT:** Both Nami and Franky reference this same jpower block, proving that:
1. jpower blocks are template libraries
2. Different characters select different entries from the same block
3. Or collision files handle damage differently per character

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)
```

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| op_b_04c.aar         |      | Main sprites    |
| op_b_04_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character      |
| -------- | ------------------------------------- | ------------------- |
| 0x0924B0 | Collision file pointer table          | Index 15            |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 15            |
| 0x09E780 | Koma name table                       |                     |

---

## Mechanics

### Weight Category

**Category:** LIGHT (CONFIRMED)

**Reference status:** Nami is the LIGHT weight reference character.

**Observations:**

- High displacement velocity when hit
- Takes more knockback than standard characters
- Floaty feel in combat

### Movement

| Property      | Value          | Notes                              |
| ------------- | -------------- | ---------------------------------- |
| Walk Speed    | **FAST**       | Fastest in game (reference)        |
| Dash Type     | Standard       | Standard dash (not flash)          |
| Dash Distance |                |                                    |

**Reference status:** Nami is the FAST walk speed reference character.

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, **Nami**)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**Clima-Tact (Weather Staff):**
- Staff-based attacks (Impact damage type expected)
- May have weather-related special effects
- Light weight makes her evasive but vulnerable

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                                   | Priority | Status    | Result |
| ----------- | -------------------------------------------------- | -------- | --------- | ------ |
| op_b_04-001 | Full B move damage values (neutral)                | P2       | PENDING   |        |
| op_b_04-002 | Full Y combo damage breakdown                      | P2       | PENDING   |        |
| op_b_04-003 | Special (X) damage at each koma size               | P2       | PENDING   |        |
| op_b_04-004 | Confirm all attacks are Impact type                | P2       | PENDING   |        |
| op_b_04-005 | **Compare knockback received vs Franky (same hit)**| **P1**   | PENDING   |        |
| op_b_04-006 | **Document walk speed difference vs Franky**       | **P1**   | PENDING   |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**HIGH PRIORITY:** Tests 005 and 006 are critical for understanding where weight/speed data is stored!

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y / up Y / down Y damage
   - [ ] All X move damage at each koma size

2. **Movement/Physics (CRITICAL)**
   - [ ] Walk speed exact comparison vs Franky (frame count same distance)
   - [ ] Knockback received comparison vs Franky (same attack, measure distance)
   - [ ] Dash type confirmation (standard)
   - [ ] Jump height/fall speed (should match Franky - universal constants)

3. **Damage Type Verification**
   - [ ] Test with Impact Defense passive - should reduce damage
   - [ ] Test with Slash Defense passive - should have no effect

---

## Unknown / Needs Research

### Unverified Data

1. Exact damage values for all moves
2. Weather-related effects from specials
3. Exact knockback/displacement values

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] **WHERE IS WEIGHT STORED?** (not in chr_b, collision, or jpower)
- [x] ~~Where is walk speed stored?~~ SOLVED: chr_b `statC` (threshold-based)

### Open Questions

1. **CRITICAL:** If Nami and Franky have identical chr_b data, where is weight stored?
2. ~~Where is walk speed stored?~~ SOLVED: chr_b `statC` field (differs between Nami and Franky)
3. Why do Nami and Franky share the same jpower block despite different movesets?
4. Does Clima-Tact have any weather-based effects in-game?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship                           |
| ----------------- | ----------- | -------------- | -------------------------------------- |
| PCT Nami          | 16          | op_b_05        | Powered form (6 koma), weather attacks |
| **Franky**        | **19**      | **op_b_08**    | **SHARES ALL CHR_B DATA (PARADOX!)**   |

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
- [Franky-Character-Map.md](./Franky-Character-Map.md) - **MUST CROSS-REFERENCE**

---

## Session Log

| Date       | Session | Verified | Notes                                |
| ---------- | ------- | -------- | ------------------------------------ |
| 2026-01-29 | Initial | Partial  | Created from research docs           |

---

## Notes

- Nami is the navigator of the Straw Hat Pirates
- Uses Clima-Tact (weather staff) for attacks
- **REFERENCE CHARACTER for LIGHT weight and FAST walk speed**
- Shares ALL chr_b data with Franky despite being complete opposites
- This paradox proves weight is NOT in chr_b battleParams (walk speed is in statC - solved)
- Critical for research: comparing Nami to Franky will reveal where these values are stored
- See also: Franky-Character-Map.md for the other half of this paradox
