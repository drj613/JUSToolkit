# Goku SSJ (db_b_02) - Complete Character Mapping

Deep dive analysis mapping Goku SSJ through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Goku SSJ           |
| Series          | Dragon Ball        |
| chr_b Index     | 1                  |
| Collision File  | db_b_02.bin        |
| charId          | 7                  |
| tier            | 2 (assumed)        |
| jpower Block    | 0                  |
| classId         | 256                |

---

## In-Game Verified Data

### Koma Sizes (NEEDS TESTING)

- **Goku SSJ:** 6, 7 koma (from Goku-Character-Map.md references)

### Move List (INFERRED FROM GOKU)

> **NOTE:** User confirmed Goku and Goku SSJ share the same moveset. Values below are
> copied from Goku's verified data. SSJ specials (X moves) may differ.

| Move   | Damage | Type       | Notes                          |
| ------ | ------ | ---------- | ------------------------------ |
| B      | 8      | Punch/Kick | Shared with base Goku          |
| fwd B  | 7      | Punch/Kick | Shared with base Goku          |
| up B   | 3+3    | Punch/Kick | 2 hits, shared with base Goku  |
| down B | 7      | Punch/Kick | Shared with base Goku          |
| air B  |        |            | Needs testing                  |
| Y      | 4+4+6  | Punch/Kick | 3-hit combo, shared with Goku  |
| fwd Y  | 5+5+5  | Energy     | Up to 3 projectiles            |
| up Y   | 14     | Punch/Kick | Shared with base Goku          |
| down Y | 14     | Punch/Kick | Shared with base Goku          |
| air Y  |        |            | Needs testing                  |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
| 6    |          |         |             |            |
| 7    |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 1)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 7     | Same as base Goku              |
| formType     | 1     | Powered form (SSJ)             |
| tier         | 2     | Assumed, needs verification    |
| komaSize     | 3     | Internal size (not deck koma)  |
| classId      | 256   | Same as base Goku              |
| jpower Block | 0     | classId & 0xFF, same as Goku   |

### battleParams (12 bytes)

```
Raw: [TBD - needs extraction]

Parsed:
  Likely identical or similar to base Goku

Stats [8,9,10]: Expected similar to Goku [40, 20, 20] = 80 total

Profile: Balanced (assumed same as Goku)
```

### Collision File (db_b_02.bin)

| Property    | Value               |
| ----------- | ------------------- |
| Size        | TBD                 |
| Entry Count | TBD                 |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- Expected to be identical or very similar to db_b_01.bin (base Goku)
- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 0 Analysis

**Shared with base Goku and Majin Buu.**

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage (÷7) | Notes         |
| ----- | --------- | --- | --- | --- | ----- | ---------------------- | ------------- |
| 0     | 0         | 30  | 20  | 0   | 50    | 7                      | fwd B/down B? |
| 1     | 3         | 10  | 40  | 0   | 50    | 7                      |               |
| 2     | 6         | 50  | 0   | 0   | 50    | 7                      |               |
| 3     | 9         | 30  | 0   | 20  | 50    | 7                      |               |
| 4     | 12        | 25  | 25  | 0   | 50    | 7                      |               |
| 5     | 15        | 20  | 0   | 30  | 50    | 7                      |               |
| 6     | 18        | 25  | 25  | 0   | 50    | 7                      |               |
| 7     | 21        | 60  | 40  | 0   | 100   | 14                     | up Y          |
| 8     | 23        | 100 | 0   | 0   | 100   | 14                     | down Y        |

**Damage Formula:**

```
base_damage = (jpower_total / 7) for Goku family
```

- Goku uses ÷7 formula (different from Bleach ÷5)
- B = 8 damage NOT explained by Block 0 entries

### Sprite Archives (chr/)

| Archive        | Size | Purpose         |
| -------------- | ---- | --------------- |
| db_b_02c.aar   |      | Main sprites    |
| db_b_02_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                             | This Character |
| -------- | ------------------------------------ | -------------- |
| 0x0924B0 | Collision file pointer table         | Index 1        |
| 0x08D4A0 | chr_b -> collision identity mapping  |                |
| 0x09E780 | Koma name table                      |                |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed same as base Goku)

**Observations:**

- Should feel identical to base Goku
- Displacement velocity: Standard
- Comparison: Expected same as Goku

### Movement

| Property      | Value    | Notes                     |
| ------------- | -------- | ------------------------- |
| Walk Speed    | Normal   | Assumed same as base Goku |
| Dash Type     | Standard | Visible movement          |
| Dash Distance |          |                           |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**Super Saiyan Form:**
- Higher koma cost than base Goku (6-7 vs 4-5)
- Specials may have different effects/damage
- Visual effects (yellow aura, golden hair)

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                    | Priority | Status    | Result |
| ----------- | ----------------------------------- | -------- | --------- | ------ |
| db_b_02-001 | Verify moveset matches base Goku    | P2       | PENDING   |        |
| db_b_02-002 | X move damage at 6-koma             | P2       | PENDING   |        |
| db_b_02-003 | X move damage at 7-koma             | P2       | PENDING   |        |
| db_b_02-004 | Confirm tier value (expect 2)       | P3       | PENDING   |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values**
   - [x] B move damage - Expected 8 (same as Goku)
   - [x] fwd B damage - Expected 7
   - [x] up B damage - Expected 3+3
   - [x] down B damage - Expected 7
   - [ ] All X move damage at 6-koma and 7-koma sizes

2. **Movement/Physics**
   - [ ] Confirm walk speed matches base Goku
   - [ ] Confirm dash type (standard)
   - [ ] Confirm weight matches base Goku

3. **Unique Mechanics**
   - [ ] Any differences from base Goku besides specials
   - [ ] SSJ-specific buffs or effects

---

## Unknown / Needs Research

### Unverified Data

1. Exact battleParams values (need extraction)
2. Collision file entry count and differences from db_b_01
3. X move damage scaling

### Missing Information

- [ ] Complete X move damage values (needs human testing)
- [ ] Exact koma sizes available in-game
- [ ] Any SSJ-specific mechanics beyond visuals

### Open Questions

1. Are there ANY mechanical differences from base Goku besides specials?
2. Does SSJ have different hitstun or knockback values?

---

## Related Characters

| Character  | chr_b Index | Collision File | Relationship            |
| ---------- | ----------- | -------------- | ----------------------- |
| Goku       | 0           | db_b_01.bin    | Base form, same moveset |
| Majin Buu  | 11          | db_b_12.bin    | Same jpower block only  |
| Vegetto    | 2           | db_b_03.bin    | Same series, Block 1    |
| Vegeta     | 3           | db_b_04.bin    | Same series, Block 1    |

**Characters sharing jpower Block 0:**

- Goku (chr_b[0]) - SAME MOVESET
- Goku SSJ (chr_b[1]) - THIS CHARACTER
- Majin Buu (chr_b[11]) - Different moveset

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                            |
| -------- | ----------------------------------- |
| 0x0924B0 | Collision file pointer table        |
| 0x08D4A0 | chr_b -> collision identity mapping |
| 0x09E780 | Koma name table                     |

### Related Documentation

- [Goku-Character-Map.md](./Goku-Character-Map.md) - Base form with verified data
- [chr_b-Complete-Mapping.md](../research/chr_b-Complete-Mapping.md)
- [jpower-Mapping.md](../research/jpower-Mapping.md)

---

## Session Log

| Date       | Session | Verified                  | Notes                              |
| ---------- | ------- | ------------------------- | ---------------------------------- |
| 2026-01-29 | Initial | Inherited from base Goku  | Created based on Goku verified data |

---

## Notes

- **Key insight:** User confirmed Goku and Goku SSJ share the same moveset
- All basic move data inherited from base Goku's verified testing
- SSJ is a "powered form" (formType=1) with higher koma cost
- Focus testing should be on X moves which likely differ from base form
