# Yoh Asakura - White Swan (sk_b_02) - Complete Character Mapping

Deep dive analysis mapping Yoh (White Swan) through all data files to understand linkages.

---

## Basic Info

| Field           | Value                    |
| --------------- | ------------------------ |
| Character Name  | Yoh Asakura (White Swan) |
| Series          | Shaman King              |
| chr_b Index     | 26                       |
| Collision File  | sk_b_02.bin              |
| charId          | 6                        |
| tier            | (needs extraction)       |
| jpower Block    | 22                       |
| classId         | 534                      |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Yoh (White Swan):** 6 koma (from Character-Mapping.md)

### Move List (CONFIRMED)

| Move   | Damage | Type | Notes |
| ------ | ------ | ---- | ----- |
| B      |        |      |       |
| fwd B  |        |      |       |
| up B   |        |      |       |
| down B |        |      |       |
| air B  |        |      |       |
| Y      |        |      |       |
| fwd Y  |        |      |       |
| up Y   |        |      |       |
| down Y |        |      |       |
| air Y  |        |      |       |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
| 6    |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 26)

| Field        | Value | Notes                        |
| ------------ | ----- | ---------------------------- |
| charId       | 6     | Shared with base Yoh         |
| formType     |       | 0=Normal, 1=Powered          |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg |
| komaSize     |       | Internal size (not deck koma)|
| classId      | 534   | Same as base Yoh             |
| jpower Block | 22    | Shared with base Yoh         |

### battleParams (12 bytes)

```
Raw: [needs extraction]

Parsed:
  Slot 0: value=, flags=0x
  Slot 1: value=, flags=0x
  Slot 2: value=, flags=0x
  Slot 3: value=, flags=0x

Stats [8,9,10]: [, , ] =  total
  Attack weight:
  Defense weight:
  Speed/Utility:

Byte 11:  (special flag)

Profile:
```

### Collision File (sk_b_02.bin)

| Property    | Value                 |
| ----------- | --------------------- |
| Size        | (needs extraction)    |
| Entry Count | 19                    |
| Location    | ChrBin.aar/chr/col/   |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- White Swan has **5 more entries** than base Yoh (19 vs 14)
- Extended range noted in Character-Mapping.md
- damageFlags field does NOT represent actual damage values

### jpower Block 22 Analysis

**Shared block with:**
- sk_b_01 (Yoh) - classId=534
- sk_b_02 (Yoh White Swan) - classId=534

Both Yoh forms share the same jpower block, similar to Goku/Goku SSJ and Ichigo/Bankai patterns.

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

| Archive          | Size | Purpose         |
| ---------------- | ---- | --------------- |
| sk_b_02c.aar     |      | Main sprites    |
| sk_b_02_6c.aar   |      | 6-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 26       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed, same as base Yoh)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: (needs testing)
- Walk speed: (needs testing)
- Comparison to reference characters: (needs testing)

### Movement

| Property      | Value     | Notes                    |
| ------------- | --------- | ------------------------ |
| Walk Speed    |           | Slow / Normal / Fast     |
| Dash Type     |           | Standard / Flash         |
| Dash Distance |           |                          |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

- **Extended range** compared to base Yoh (documented in Character-Mapping.md)
- White Swan is Yoh's Spirit of Sword form with Amidamaru fully integrated
- Uses same jpower block as base Yoh but with different collision entries
- Pattern similar to Goku/SSJ and Ichigo/Bankai relationships

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID    | Test Description                   | Priority | Status    | Result |
| ---------- | ---------------------------------- | -------- | --------- | ------ |
| sk_b_02-001| Confirm 6-koma only availability   | P2       | PENDING   |        |
| sk_b_02-002| B move damage (neutral)            | P2       | PENDING   |        |
| sk_b_02-003| Full moveset damage values         | P2       | PENDING   |        |
| sk_b_02-004| Compare range to base Yoh          | P2       | PENDING   |        |
| sk_b_02-005| Damage type (slash vs impact)      | P2       | PENDING   |        |

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
   - [ ] Verify extended range vs base Yoh
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact tier value in chr_b.bin
2. battleParams byte values
3. All collision file entry details
4. How range extension is encoded (hitbox width in collision?)

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] Exact range difference vs base Yoh
- [ ] Buff multipliers if any (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does White Swan have any unique buff mechanics?
2. Is the "extended range" in collision file width values or separate system?
3. Why 5 more collision entries than base Yoh - what moves are enhanced?

---

## Related Characters

| Character        | chr_b Index | Collision File | Relationship              |
| ---------------- | ----------- | -------------- | ------------------------- |
| Yoh Asakura      | 25          | sk_b_01.bin    | Base form, same charId    |
| Anna Kyoyama     | 27          | sk_b_03.bin    | Same series               |

**Characters sharing jpower Block 22:**

- sk_b_01 (Yoh Asakura)
- sk_b_02 (Yoh White Swan)

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                               |
| -------- | -------------------------------------- |
| 0x0924B0 | Collision file pointer table           |
| 0x08D4A0 | chr_b -> collision identity mapping    |
| 0x09E780 | Koma name table                        |

### Related Documentation

- [chr_b-Mapping.md](../formats/chr_b-Mapping.md)
- [jpower-Analysis.md](../formats/jpower-Analysis.md)
- [Collision-Format.md](../formats/Collision-Format.md)
- [Character-Mapping.md](../research/Character-Mapping.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- White Swan is the powered/transformed version of Yoh Asakura
- Higher collision entry count (19 vs 14) suggests enhanced moveset
- Same jpower block and charId as base Yoh - form variant pattern
- "Extended range" documented in Character-Mapping.md - likely larger hitbox widths
