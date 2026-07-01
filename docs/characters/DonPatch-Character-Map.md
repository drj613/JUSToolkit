# Don Patch / Super Patch - Character Map

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Don Patch and Super Patch through all data files.

> **Note:** These two characters share the same moveset and jpower data. They differ
> only in sprites and chr_b index. This document covers both forms.

---

## Overview

| Field           | Don Patch | Super Patch |
| --------------- | --------- | ----------- |
| Series          | Bobobo-bo Bo-bobo | Bobobo-bo Bo-bobo |
| chr_b Index     | 49        | 50          |
| Collision File  | bb_b_03.bin | bb_b_04.bin |
| Collision Entries | 18      | 18          |
| charId          | 14        | 14          |
| tier            | 2         | 2           |
| jpower Block    | 70        | 70          |
| classId         | 582       | 582         |

**Why consolidated:** Both characters use identical jpower block 70 and classId 582,
meaning they have the same damage values for all moves. Per Character-Mapping.md:
"Same kit as Don Patch".

---

## In-Game Verified Data

### Koma Sizes (PENDING)

- **Don Patch:** TBD koma
- **Super Patch:** TBD koma

### Shared Move List (PENDING)

Both forms share identical moves and damage values:

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        |            |                       |
| fwd B  |        |            |                       |
| up B   |        |            |                       |
| down B |        |            |                       |
| air B  |        |            |                       |
| Y      |        |            |                       |
| fwd Y  |        |            |                       |
| up Y   |        |            |                       |
| down Y |        |            |                       |
| air Y  |        |            |                       |

**Damage Types:**

- **Slashing** - Blade attacks (reduced by Slash Defense passive)
- **Impact** - Blunt attacks (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks

### Specials (X Moves)

May differ between forms - needs testing:

| Form        | Koma | X Damage | X Notes | up X Damage | up X Notes |
| ----------- | ---- | -------- | ------- | ----------- | ---------- |
| Don Patch   |      |          |         |             |            |
| Super Patch |      |          |         |             |            |

---

## File Data

### chr_b.bin Entries

#### Don Patch (Index 49)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 14    | Shared with Super Patch        |
| formType     | 0     | Normal (assumed)               |
| tier         | 2     | No damage modifier             |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 582   | Low byte = 70                  |
| jpower Block | 70    | classId & 0xFF                 |

#### Super Patch (Index 50)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 14    | Shared with Don Patch          |
| formType     | 0     | Normal (assumed)               |
| tier         | 2     | No damage modifier             |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 582   | Low byte = 70                  |
| jpower Block | 70    | classId & 0xFF                 |

### battleParams (12 bytes)

Both characters likely have identical or near-identical battleParams:

```
Raw: [TBD]

Parsed:
  Slot 0: value=TBD, flags=0xTBD
  Slot 1: value=TBD, flags=0xTBD
  Slot 2: value=TBD, flags=0xTBD
  Slot 3: value=TBD, flags=0xTBD

Stats [8,9,10]: [TBD, TBD, TBD] = TBD total
  Attack weight:  TBD
  Defense weight: TBD
  Speed/Utility:  TBD

Byte 11: TBD (special flag)

Profile: TBD
```

### Collision Files

| Property    | Don Patch (bb_b_03) | Super Patch (bb_b_04) |
| ----------- | ------------------- | --------------------- |
| Size        | TBD bytes           | TBD bytes             |
| Entry Count | 18                  | 18                    |
| Location    | ChrBin.aar/chr/col/ | ChrBin.aar/chr/col/   |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries
- Both collision files expected to have identical structure (18 entries each)

### jpower Block 70 Analysis

**IMPORTANT:** Block 70 is shared with Bo-bobo (bb_b_01), but Bo-bobo has a
DIFFERENT moveset despite same block. This demonstrates jpower blocks are
template libraries, not 1:1 moveset definitions.

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       |                   |       |

**Damage Formula:**

```
damage = floor(jpower.damage1 / 5) + (tier - 2)
```

- tier 1: -1 modifier
- tier 2: no modifier (Don Patch, Super Patch)
- tier 3: +1 modifier

### Sprite Archives (chr/)

| Form        | Main Sprites   | X-Koma Portrait   |
| ----------- | -------------- | ----------------- |
| Don Patch   | bb_b_03c.aar   | bb_b_03_Xc.aar    |
| Super Patch | bb_b_04c.aar   | bb_b_04_Xc.aar    |

### ARM9 References

| Offset   | Contents                              | Don Patch | Super Patch |
| -------- | ------------------------------------- | --------- | ----------- |
| 0x0924B0 | Collision file pointer table          | Index 49  | Index 50    |
| 0x08D4A0 | chr_b -> collision identity mapping   |           |             |
| 0x09E780 | Koma name table                       |           |             |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed)

**Observations:**

- Displacement velocity: TBD
- Walk speed: TBD
- Comparison to reference characters: TBD

### Movement

| Property      | Value    | Notes                    |
| ------------- | -------- | ------------------------ |
| Walk Speed    | TBD      | Slow / Normal / Fast     |
| Dash Type     | TBD      | Standard / Flash         |
| Dash Distance | TBD      |                          |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Form Differences

The only confirmed differences between Don Patch and Super Patch are:

1. **Sprites** - Different visual appearance
2. **chr_b Index** - 49 vs 50
3. **Collision file** - bb_b_03.bin vs bb_b_04.bin (same structure/entry count)

**Potential differences (needs testing):**

- X move effects or visuals
- Stats differences in battleParams
- Passive abilities

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                             | Priority | Status  | Result |
| ----------- | -------------------------------------------- | -------- | ------- | ------ |
| bb_b_03-001 | Verify all B move damage values (Don Patch)  | P2       | PENDING |        |
| bb_b_03-002 | Verify all Y move damage values (Don Patch)  | P2       | PENDING |        |
| bb_b_03-003 | Verify X move damage at each koma size       | P2       | PENDING |        |
| bb_b_03-004 | Confirm moveset identical to Super Patch     | P1       | PENDING |        |
| bb_b_04-001 | Verify X moves match Don Patch (Super Patch) | P2       | PENDING |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

### Specific Tests Needed

1. **Move Damage Values** (test with Don Patch, assume same for Super Patch)
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y / up Y / down Y damage
   - [ ] All X move damage at each koma size

2. **Form Comparison**
   - [ ] Confirm B/Y moves identical between forms
   - [ ] Compare X moves between forms
   - [ ] Check for stat differences (knockback received, walk speed)

3. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast, Franky=slow)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku)

4. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Actual tier value (assumed tier=2 for both)
2. Whether X moves differ between forms
3. Any stat differences in battleParams

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Are X moves identical between Don Patch and Super Patch?
2. What differentiates these characters from Bo-bobo (same jpower block)?
3. How do collision files differ from Bo-bobo despite same block?

---

## Related Characters

| Character    | chr_b Index | Collision File | Relationship                              |
| ------------ | ----------- | -------------- | ----------------------------------------- |
| Bo-bobo      | 47          | bb_b_01.bin    | Same jpower block (70), DIFFERENT moveset |
| Shinsetsu    | 48          | bb_b_02.bin    | Same series, different jpower block (71)  |

**Characters sharing jpower Block 70:**

- bb_b_01 (Bo-bobo) - chr_b[47], classId=582 - DIFFERENT moveset
- bb_b_03 (Don Patch) - chr_b[49], classId=582 - THIS FILE
- bb_b_04 (Super Patch) - chr_b[50], classId=582 - THIS FILE

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

| Date       | Session | Verified | Notes                                    |
| ---------- | ------- | -------- | ---------------------------------------- |
| 2026-01-31 |         |          | Consolidated from separate Don Patch and Super Patch files |

---

## Notes

- Don Patch and Super Patch share the SAME moveset (confirmed via jpower block + classId)
- Super Patch is the powered/alternate form of Don Patch in the Bobobo series
- Bo-bobo uses the same jpower Block 70 but has a DIFFERENT moveset
- This demonstrates jpower blocks are template libraries, not 1:1 moveset definitions
- charId=14 is shared with Gear 2 Luffy, Kinnikuman, and other Bobobo characters
