# Bo-bobo (bb_b_01) - Complete Character Mapping

Deep dive analysis mapping Bo-bobo through all data files to understand linkages.

---

## Basic Info

| Field           | Value                    |
| --------------- | ------------------------ |
| Character Name  | Bo-bobo                  |
| Series          | Bobobo-bo Bo-bobo        |
| chr_b Index     | 47                       |
| Collision File  | bb_b_01.bin              |
| charId          | 14                       |
| tier            | 2 (assumed)              |
| jpower Block    | 70                       |
| classId         | 582                      |

---

## In-Game Verified Data

### Koma Sizes (PENDING)

- **Bo-bobo:** TBD koma

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

### chr_b.bin Entry (Index 47)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 14    | Shared with Gear 2 Luffy, Kinnikuman, other Bobobo chars |
| formType     | 0     | Normal (assumed)               |
| tier         | 2     | Assumed - no modifier          |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 582   | Low byte = 70                  |
| jpower Block | 70    | classId & 0xFF                 |

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

### Collision File (bb_b_01.bin)

| Property    | Value            |
| ----------- | ---------------- |
| Size        | TBD bytes        |
| Entry Count | TBD              |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 70 Analysis

**IMPORTANT:** Bo-bobo shares jpower Block 70 with Don Patch and Super Patch, but Bo-bobo has a DIFFERENT moveset from Don Patch/Super Patch.

This is consistent with the finding that jpower blocks are **template libraries**, not complete movesets. Characters select specific entries from their assigned block.

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
| bb_b_01c.aar      |      | Main sprites    |
| bb_b_01_Xc.aar    |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 47       |
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

Bo-bobo's fighting style involves comedic and unpredictable attacks using his nose hair (Hanage Shinken). His moveset is distinct from Don Patch and Super Patch despite sharing the same jpower block.

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID    | Test Description                        | Priority | Status    | Result |
| ---------- | --------------------------------------- | -------- | --------- | ------ |
| bb_b_01-001 | Verify all B move damage values         | P2       | PENDING   |        |
| bb_b_01-002 | Verify all Y move damage values         | P2       | PENDING   |        |
| bb_b_01-003 | Verify X move damage at each koma size  | P2       | PENDING   |        |
| bb_b_01-004 | Confirm moveset differs from Don Patch  | P1       | PENDING   |        |

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

3. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Actual tier value (assumed tier=2)
2. Complete moveset differences from Don Patch/Super Patch
3. How moves select from jpower Block 70

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. How does Bo-bobo select different entries from Block 70 than Don Patch/Super Patch?
2. What collision file differences create the distinct moveset?

---

## Related Characters

| Character    | chr_b Index | Collision File | Relationship                                  |
| ------------ | ----------- | -------------- | --------------------------------------------- |
| Shinsetsu    | 48          | bb_b_02.bin    | Same series, different jpower block (71)      |
| Don Patch    | 49          | bb_b_03.bin    | Same jpower block (70), different moveset     |
| Super Patch  | 50          | bb_b_04.bin    | Same jpower block (70), different moveset     |

**Characters sharing jpower Block 70:**

- bb_b_01 (Bo-bobo) - chr_b[47], classId=582
- bb_b_03 (Don Patch) - chr_b[49], classId=582
- bb_b_04 (Super Patch) - chr_b[50], classId=582

**Note:** Don Patch and Super Patch share the same moveset (confirmed), but Bo-bobo has a different moveset despite using the same jpower block.

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

- Bo-bobo, Don Patch, and Super Patch all share jpower Block 70 but Bo-bobo has a distinctly different moveset
- This demonstrates that jpower blocks are template libraries, not 1:1 moveset definitions
- charId=14 is shared with Gear 2 Luffy, Kinnikuman, and other Bobobo characters
