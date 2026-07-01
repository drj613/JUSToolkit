# Vegeta (db_b_04) - Complete Character Mapping

Deep dive analysis mapping Vegeta through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Vegeta             |
| Series          | Dragon Ball        |
| chr_b Index     | 3                  |
| Collision File  | db_b_04.bin        |
| charId          | 7                  |
| tier            | 2 (assumed)        |
| jpower Block    | 1                  |
| classId         | 257                |

---

## In-Game Verified Data

### Koma Sizes (NEEDS TESTING)

- **Vegeta:** TBD koma

### Move List (NEEDS TESTING)

| Move   | Damage | Type     | Notes         |
| ------ | ------ | -------- | ------------- |
| B      |        |          | Needs testing |
| fwd B  |        |          | Needs testing |
| up B   |        |          | Needs testing |
| down B |        |          | Needs testing |
| air B  |        |          | Needs testing |
| Y      |        |          | Needs testing |
| fwd Y  |        |          | Needs testing |
| up Y   |        |          | Needs testing |
| down Y |        |          | Needs testing |
| air Y  |        |          | Needs testing |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 3)

| Field        | Value | Notes                               |
| ------------ | ----- | ----------------------------------- |
| charId       | 7     | Same stat template as Goku family   |
| formType     | 0     | Normal form (base Vegeta)           |
| tier         | 2     | Assumed, needs verification         |
| komaSize     | 3     | Internal size (not deck koma)       |
| classId      | 257   | Same as Vegetto                     |
| jpower Block | 1     | classId & 0xFF, shared with Vegetto |

### battleParams (12 bytes)

```
Raw: [TBD - needs extraction]

Parsed:
  Slot 0: value=?, flags=?
  Slot 1: value=?, flags=?
  Slot 2: value=?, flags=?
  Slot 3: value=?, flags=?

Stats [8,9,10]: Expected similar profile to Goku family

Profile: TBD
```

### Collision File (db_b_04.bin)

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

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 1 Analysis

**Shared with Vegetto.**

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Old ÷7 calc (DEBUNKED) | Notes |
| ----- | --------- | --- | --- | --- | ----- | ---------------------- | ----- |
| 0     |           |     |     |     | 50    | 7                      |       |
| 1     |           |     |     |     | 50    | 7                      |       |

**From jpower-Mapping.md:** Block 1 has damages [7, 7] (2 entries)

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)  # Confirmed formula (Research-Status.md)
# NOTE: earlier ÷7-of-total calculation in the table above is DEBUNKED
```

### Sprite Archives (chr/)

| Archive        | Size | Purpose         |
| -------------- | ---- | --------------- |
| db_b_04c.aar   |      | Main sprites    |
| db_b_04_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                             | This Character |
| -------- | ------------------------------------ | -------------- |
| 0x0924B0 | Collision file pointer table         | Index 3        |
| 0x08D4A0 | chr_b -> collision identity mapping  |                |
| 0x09E780 | Koma name table                      |                |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed)

**Observations:**

- Vegeta is a Saiyan warrior like Goku
- Expected standard weight similar to Goku

### Movement

| Property      | Value    | Notes                     |
| ------------- | -------- | ------------------------- |
| Walk Speed    |          | Needs testing             |
| Dash Type     |          | Standard or Flash?        |
| Dash Distance |          |                           |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**Prince of Saiyans:**
- Rival to Goku, similar fighting style
- Has SSJ form as separate character (db_b_05)
- Likely punch/kick focused with energy attacks

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description              | Priority | Status    | Result |
| ----------- | ----------------------------- | -------- | --------- | ------ |
| db_b_04-001 | Full moveset damage values    | P2       | PENDING   |        |
| db_b_04-002 | Available koma sizes          | P2       | PENDING   |        |
| db_b_04-003 | X move damage at each koma    | P2       | PENDING   |        |
| db_b_04-004 | Movement speed and dash type  | P3       | PENDING   |        |
| db_b_04-005 | Compare moveset to Vegeta SSJ | P3       | PENDING   |        |

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
   - [ ] Walk speed observation (compare to Goku=standard)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)
   - [ ] Compare to Vegeta SSJ (shared moveset like Goku?)

---

## Unknown / Needs Research

### Unverified Data

1. All move damage values
2. Available koma sizes
3. Exact battleParams values
4. Collision file structure

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Any unique mechanics
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Vegeta share moveset with Vegeta SSJ (like Goku/Goku SSJ)?
2. How does Block 1 selection work with only 2 entries?
3. What are Vegeta's unique moves compared to Goku?

---

## Related Characters

| Character   | chr_b Index | Collision File | Relationship                  |
| ----------- | ----------- | -------------- | ----------------------------- |
| Vegeta SSJ  | 4           | db_b_05.bin    | Powered form, likely same moveset |
| Vegetto     | 2           | db_b_03.bin    | Same jpower block, fusion form    |
| Goku        | 0           | db_b_01.bin    | Rival, similar charId             |
| Goku SSJ    | 1           | db_b_02.bin    | SSJ comparison                    |

**Characters sharing jpower Block 1:**

- Vegetto (chr_b[2])
- Vegeta (chr_b[3]) - THIS CHARACTER

**Note:** Despite sharing Block 1, Vegetto and Vegeta have DIFFERENT movesets (common pattern in JUS).

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                            |
| -------- | ----------------------------------- |
| 0x0924B0 | Collision file pointer table        |
| 0x08D4A0 | chr_b -> collision identity mapping |
| 0x09E780 | Koma name table                     |

### Related Documentation

- [chr_b-Complete-Mapping.md](../research/chr_b-Complete-Mapping.md)
- [jpower-Mapping.md](../research/jpower-Mapping.md)
- [Goku-Character-Map.md](./Goku-Character-Map.md) - For comparison

---

## Session Log

| Date       | Session | Verified | Notes                      |
| ---------- | ------- | -------- | -------------------------- |
| 2026-01-29 | Initial | None     | Created from research docs |

---

## Notes

- Vegeta is Goku's rival and a core Dragon Ball character
- Has a SSJ form as separate entry (Vegeta SSJ, chr_b[4])
- Shares jpower Block 1 with Vegetto but different moveset
- Same charId (7) as all Dragon Ball characters = same stat template
- Need to verify if Vegeta/Vegeta SSJ share moveset like Goku/Goku SSJ
