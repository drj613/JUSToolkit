# Shinsetsu Bo-bobo (bb_b_02) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Shinsetsu Bo-bobo through all data files to understand linkages.

---

## Basic Info

| Field           | Value                    |
| --------------- | ------------------------ |
| Character Name  | Shinsetsu Bo-bobo        |
| Series          | Bobobo-bo Bo-bobo        |
| chr_b Index     | 48                       |
| Collision File  | bb_b_02.bin              |
| charId          | 14                       |
| tier            | 2 (assumed)              |
| jpower Block    | 71                       |
| classId         | 327                      |

---

## In-Game Verified Data

### Koma Sizes (PENDING)

- **Shinsetsu:** TBD koma

### Move List (PENDING)

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

### chr_b.bin Entry (Index 48)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 14    | Shared with Gear 2 Luffy, Kinnikuman, other Bobobo chars |
| formType     | 1     | Powered (likely - form change character) |
| tier         | 2     | Assumed - no modifier          |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 327   | Low byte = 71                  |
| jpower Block | 71    | classId & 0xFF                 |

### battleParams (12 bytes)

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

### Collision File (bb_b_02.bin)

| Property    | Value            |
| ----------- | ---------------- |
| Size        | TBD bytes        |
| Entry Count | TBD              |
| Location    | ChrBin.aar/chr/col/ |

**IMPORTANT - Form Change Mechanics:**

Shinsetsu has **form change** capability with **extra collision entries after the terminator**. This is a special structure where:
- Normal collision entries come first
- A terminator marker (0xFF) separates the normal and transformed states
- Additional collision entries follow for the transformed/powered state

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries
- Extra entries after terminator indicate form change character

### jpower Block 71 Analysis

**Note:** Shinsetsu uses jpower Block 71, distinct from the other Bobobo characters (Bo-bobo, Don Patch, Super Patch use Block 70).

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       |                   |       |

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)
```

- tier 1: -1 modifier
- tier 2: no modifier
- tier 3: +1 modifier

### Sprite Archives (chr/)

| Archive           | Size | Purpose         |
| ----------------- | ---- | --------------- |
| bb_b_02c.aar      |      | Main sprites    |
| bb_b_02_Xc.aar    |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 48       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

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

### Unique Mechanics

**Form Change Character:**

Shinsetsu Bo-bobo is a form change character with extra collision entries after the terminator. This likely represents a transformation mechanic where:
- Base state uses initial collision entries
- Transformed state uses post-terminator collision entries
- Transformation may be triggered by special move or condition

This is similar to other powered-up characters like Bankai Ichigo having separate collision data for their alternate forms.

### Buff/Debuff Mechanics

| Buff Name      | Trigger | Effect | Duration |
| -------------- | ------- | ------ | -------- |
| Form Change    | TBD     | TBD    | TBD      |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID    | Test Description                             | Priority | Status    | Result |
| ---------- | -------------------------------------------- | -------- | --------- | ------ |
| bb_b_02-001 | Verify all B move damage values              | P2       | PENDING   |        |
| bb_b_02-002 | Verify all Y move damage values              | P2       | PENDING   |        |
| bb_b_02-003 | Verify X move damage at each koma size       | P2       | PENDING   |        |
| bb_b_02-004 | Document form change trigger and effects     | P1       | PENDING   |        |
| bb_b_02-005 | Verify collision entries for both forms      | P1       | PENDING   |        |

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
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Form Change Mechanics**
   - [ ] How is form change triggered?
   - [ ] What moves/stats change in transformed state?
   - [ ] Duration of transformation
   - [ ] Visual/audio indicators

4. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Actual tier value (assumed tier=2)
2. Form change trigger mechanism
3. Complete collision structure with post-terminator entries

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Form change mechanics documentation
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. What triggers Shinsetsu's form change?
2. How many collision entries are in each form?
3. Are the post-terminator entries a full replacement or additions?

---

## Related Characters

| Character  | chr_b Index | Collision File | Relationship                              |
| ---------- | ----------- | -------------- | ----------------------------------------- |
| Bo-bobo    | 47          | bb_b_01.bin    | Same series, different jpower block (70)  |
| Don Patch  | 49          | bb_b_03.bin    | Same series, jpower block 70              |
| Super Patch| 50          | bb_b_04.bin    | Same series, jpower block 70              |

**Characters sharing jpower Block 71:**

- bb_b_02 (Shinsetsu) - chr_b[48], classId=327

**Note:** Shinsetsu is the only character using jpower Block 71, suggesting a unique moveset.

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

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- Shinsetsu is a **form change character** with extra collision entries after the terminator
- Uses unique jpower Block 71 (not shared with other Bobobo characters)
- charId=14 is shared with Gear 2 Luffy, Kinnikuman, and other Bobobo characters
- Form change mechanics need human testing to document trigger and effects
