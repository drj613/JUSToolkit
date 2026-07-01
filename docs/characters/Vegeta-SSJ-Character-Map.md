# Vegeta SSJ (db_b_05) - Complete Character Mapping

Deep dive analysis mapping Vegeta SSJ through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Vegeta SSJ         |
| Series          | Dragon Ball        |
| chr_b Index     | 4                  |
| Collision File  | db_b_05.bin        |
| charId          | 7                  |
| tier            | 2 (assumed)        |
| jpower Block    | 2                  |
| classId         | 258                |

---

## In-Game Verified Data

### Koma Sizes (NEEDS TESTING)

- **Vegeta SSJ:** TBD koma (expected higher than base Vegeta)

### Move List (NEEDS TESTING)

> **NOTE:** If pattern matches Goku/Goku SSJ, Vegeta SSJ may share moveset with base
> Vegeta. Needs verification.

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

### chr_b.bin Entry (Index 4)

| Field        | Value | Notes                                 |
| ------------ | ----- | ------------------------------------- |
| charId       | 7     | Same stat template as Goku family     |
| formType     | 1     | Powered form (SSJ)                    |
| tier         | 2     | Assumed, needs verification           |
| komaSize     | 3     | Internal size (not deck koma)         |
| classId      | 258   | Different from base Vegeta (257)      |
| jpower Block | 2     | classId & 0xFF, shared with Gohan SSJ |

**Note:** Unlike Goku/Goku SSJ who share classId 256, Vegeta/Vegeta SSJ have DIFFERENT
classIds (257 vs 258). This means they use different jpower blocks!

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

### Collision File (db_b_05.bin)

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

### jpower Block 2 Analysis

**Shared with Gohan SSJ.**

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Old ÷7 calc (DEBUNKED) | Notes |
| ----- | --------- | --- | --- | --- | ----- | ---------------------- | ----- |
|       |           |     |     |     |       |                        |       |

**From chr_b-Complete-Mapping.md:** Block 2 is used by both Vegeta SSJ and Gohan SSJ.

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)  # Confirmed formula (Research-Status.md)
# NOTE: earlier ÷7-of-total calculation in the table above is DEBUNKED
```

### Sprite Archives (chr/)

| Archive        | Size | Purpose         |
| -------------- | ---- | --------------- |
| db_b_05c.aar   |      | Main sprites    |
| db_b_05_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                             | This Character |
| -------- | ------------------------------------ | -------------- |
| 0x0924B0 | Collision file pointer table         | Index 4        |
| 0x08D4A0 | chr_b -> collision identity mapping  |                |
| 0x09E780 | Koma name table                      |                |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed)

**Observations:**

- Expected same weight as base Vegeta
- SSJ form typically same physics as base form

### Movement

| Property      | Value    | Notes                          |
| ------------- | -------- | ------------------------------ |
| Walk Speed    |          | Needs testing                  |
| Dash Type     |          | Standard or Flash?             |
| Dash Distance |          |                                |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**Super Saiyan Form:**
- Powered version of base Vegeta
- Uses DIFFERENT jpower block than base (258 vs 257)
- This differs from Goku pattern where SSJ shares block with base
- May indicate different moveset or damage values

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                      | Priority | Status    | Result |
| ----------- | ------------------------------------- | -------- | --------- | ------ |
| db_b_05-001 | Full moveset damage values            | P2       | PENDING   |        |
| db_b_05-002 | Available koma sizes                  | P2       | PENDING   |        |
| db_b_05-003 | X move damage at each koma            | P2       | PENDING   |        |
| db_b_05-004 | Compare moveset to base Vegeta        | P1       | PENDING   |        |
| db_b_05-005 | Movement speed and dash type          | P3       | PENDING   |        |

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
   - [ ] **IMPORTANT:** Verify if moveset matches base Vegeta

---

## Unknown / Needs Research

### Unverified Data

1. All move damage values
2. Available koma sizes
3. Exact battleParams values
4. Whether moveset matches base Vegeta

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Comparison to base Vegeta moveset
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Why does Vegeta SSJ use different jpower block (2) than base Vegeta (1)?
2. Does this mean Vegeta SSJ has different moveset/damage than base?
3. Why does Goku/Goku SSJ share block 0 but Vegeta variants don't?
4. How does Gohan SSJ factor in (also uses block 2)?

---

## Related Characters

| Character  | chr_b Index | Collision File | Relationship                       |
| ---------- | ----------- | -------------- | ---------------------------------- |
| Vegeta     | 3           | db_b_04.bin    | Base form, DIFFERENT jpower block! |
| Gohan SSJ  | 5           | db_b_06.bin    | SAME jpower block (2)              |
| Goku SSJ   | 1           | db_b_02.bin    | SSJ comparison                     |
| Goku       | 0           | db_b_01.bin    | Reference character                |

**Characters sharing jpower Block 2:**

- Vegeta SSJ (chr_b[4]) - THIS CHARACTER
- Gohan SSJ (chr_b[5])

**Note:** This is an interesting pattern - two SSJ characters sharing a block, distinct from their base forms.

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

- **KEY DISCOVERY:** Vegeta SSJ uses jpower Block 2, NOT Block 1 like base Vegeta
- This is different from Goku/Goku SSJ who share Block 0
- Shares Block 2 with Gohan SSJ - potential common SSJ damage template?
- Same charId (7) as all Dragon Ball characters = same stat template
- High priority to verify if moveset differs from base Vegeta
