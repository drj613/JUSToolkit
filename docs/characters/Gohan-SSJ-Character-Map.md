# Gohan SSJ (db_b_06) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Gohan SSJ through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Gohan SSJ          |
| Series          | Dragon Ball        |
| chr_b Index     | 5                  |
| Collision File  | db_b_06.bin        |
| charId          | 7                  |
| tier            | 2 (assumed)        |
| jpower Block    | 2                  |
| classId         | 258                |

---

## In-Game Verified Data

### Koma Sizes (NEEDS TESTING)

- **Gohan SSJ:** TBD koma

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

### chr_b.bin Entry (Index 5)

| Field        | Value | Notes                                   |
| ------------ | ----- | --------------------------------------- |
| charId       | 7     | Same stat template as Goku family       |
| formType     | 1     | Powered form (SSJ)                      |
| tier         | 2     | Assumed, needs verification             |
| komaSize     | 3     | Internal size (not deck koma)           |
| classId      | 258   | Same as Vegeta SSJ                      |
| jpower Block | 2     | classId & 0xFF, shared with Vegeta SSJ  |

**Note:** Gohan SSJ shares classId 258 with Vegeta SSJ, meaning they use the same
jpower block (2). This may be a "SSJ template" for damage values.

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

### Collision File (db_b_06.bin)

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

**Shared with Vegeta SSJ.**

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Old ÷7 calc (DEBUNKED) | Notes |
| ----- | --------- | --- | --- | --- | ----- | ---------------------- | ----- |
|       |           |     |     |     |       |                        |       |

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)  # Confirmed formula (Research-Status.md)
# NOTE: earlier ÷7-of-total calculation in the table above is DEBUNKED
```

### Sprite Archives (chr/)

| Archive        | Size | Purpose         |
| -------------- | ---- | --------------- |
| db_b_06c.aar   |      | Main sprites    |
| db_b_06_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                             | This Character |
| -------- | ------------------------------------ | -------------- |
| 0x0924B0 | Collision file pointer table         | Index 5        |
| 0x08D4A0 | chr_b -> collision identity mapping  |                |
| 0x09E780 | Koma name table                      |                |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed)

**Observations:**

- Gohan is Goku's son, similar build in SSJ form
- Expected standard weight like Goku family

### Movement

| Property      | Value    | Notes              |
| ------------- | -------- | ------------------ |
| Walk Speed    |          | Needs testing      |
| Dash Type     |          | Standard or Flash? |
| Dash Distance |          |                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**SSJ Gohan (Cell Saga version):**
- This is the Cell Saga SSJ1 Gohan (not SSJ2)
- SSJ2 Gohan is a separate character (db_b_07, chr_b[6])
- Shares jpower block with Vegeta SSJ

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                        | Priority | Status    | Result |
| ----------- | --------------------------------------- | -------- | --------- | ------ |
| db_b_06-001 | Full moveset damage values              | P2       | PENDING   |        |
| db_b_06-002 | Available koma sizes                    | P2       | PENDING   |        |
| db_b_06-003 | X move damage at each koma              | P2       | PENDING   |        |
| db_b_06-004 | Compare moveset to Vegeta SSJ (block 2) | P2       | PENDING   |        |
| db_b_06-005 | Movement speed and dash type            | P3       | PENDING   |        |

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
   - [ ] Compare to Gohan SSJ2 (different character)

---

## Unknown / Needs Research

### Unverified Data

1. All move damage values
2. Available koma sizes
3. Exact battleParams values
4. How block 2 differs from blocks 0 and 1

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Differences from Gohan SSJ2
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Why do Gohan SSJ and Vegeta SSJ share block 2?
2. Is there a "SSJ damage template" pattern?
3. How does moveset differ from Gohan SSJ2 (block 3)?
4. Does block sharing imply similar damage values?

---

## Related Characters

| Character   | chr_b Index | Collision File | Relationship                    |
| ----------- | ----------- | -------------- | ------------------------------- |
| Gohan SSJ2  | 6           | db_b_07.bin    | Powered form, different block   |
| Vegeta SSJ  | 4           | db_b_05.bin    | SAME jpower block (2)           |
| Goku        | 0           | db_b_01.bin    | Father, reference character     |
| Goku SSJ    | 1           | db_b_02.bin    | SSJ comparison (uses block 0)   |

**Characters sharing jpower Block 2:**

- Vegeta SSJ (chr_b[4])
- Gohan SSJ (chr_b[5]) - THIS CHARACTER

**Note:** This block appears to be a "SSJ template" distinct from base form blocks.

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

- Gohan SSJ is the Cell Saga version (before SSJ2 transformation)
- SSJ2 Gohan is a separate entry (chr_b[6], db_b_07)
- Shares jpower Block 2 with Vegeta SSJ - interesting SSJ grouping
- Same charId (7) as all Dragon Ball characters = same stat template
- Pattern suggests SSJ forms may share damage templates across characters
