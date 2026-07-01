# Gohan SSJ2 (db_b_07) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Gohan SSJ2 through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Gohan (SSJ2)           |
| Series          | Dragon Ball            |
| chr_b Index     | 6                      |
| Collision File  | db_b_07.bin            |
| charId          | 7                      |
| tier            | (needs verification)   |
| jpower Block    | 3                      |
| classId         | 259                    |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Gohan SSJ2:** (needs human testing) koma

### Move List (PARTIALLY VERIFIED 2026-01-31)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      | 8      | Punch/Kick | Verified in-game      |
| fwd B  |        | Punch/Kick |                       |
| up B   |        | Punch/Kick |                       |
| down B |        | Punch/Kick |                       |
| air B  |        | Punch/Kick |                       |
| Y      |        | Punch/Kick |                       |
| fwd Y  |        | Energy     |                       |
| up Y   |        | Punch/Kick |                       |
| down Y |        | Punch/Kick |                       |
| air Y  |        | Energy     |                       |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks (expected for Dragon Ball fighters)
- **Energy** - Projectile/energy attacks (ki blasts)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 6)

| Field        | Value            | Notes                          |
| ------------ | ---------------- | ------------------------------ |
| charId       | 7                | Shared with Goku family        |
| formType     | (needs verify)   | 0=Normal, 1=Powered            |
| tier         | (needs verify)   | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     | (needs verify)   | Internal size (not deck koma)  |
| classId      | 259              | Low byte = jpower block index  |
| jpower Block | 3                | classId & 0xFF                 |

### battleParams (12 bytes)

```
Raw: [(needs extraction)]

Parsed:
  Slot 0: value=?, flags=0x??
  Slot 1: value=?, flags=0x??
  Slot 2: value=?, flags=0x??
  Slot 3: value=?, flags=0x??

Stats [8,9,10]: [?, ?, ?] = ? total
  Attack weight:  ?
  Defense weight: ?
  Speed/Utility:  ?

Byte 11: ? (special flag)

Profile: (needs analysis)
```

### Collision File (db_b_07.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | (needs extraction) bytes |
| Entry Count | (needs extraction)       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 3 Analysis

**Characters sharing Block 3:**

- db_b_07 (Gohan SSJ2) - chr_b[6], classId=259
- db_b_08 (Gotenks) - chr_b[7], classId=259

**Note:** Gohan SSJ2 and base Gotenks share jpower block 3, but likely have
DIFFERENT movesets. This is consistent with the pattern seen in Block 0 (Goku
vs Majin Buu) where same block does NOT mean same moveset.

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       |                   |       |

**Damage Formula:**

```
base_damage = (jpower.damage1 / 5) + (tier - 2)
```

- tier 1: -1 modifier
- tier 2: no modifier
- tier 3: +1 modifier

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| db_b_07c.aar         |      | Main sprites    |
| db_b_07_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 6                     |
| 0x08D4A0 | chr_b -> collision identity mapping   |                             |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** (needs testing - likely STANDARD)

**Observations:**

- Dragon Ball fighters generally feel standard weight
- Displacement velocity: (needs comparison to Goku)
- Walk speed: (needs comparison)

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    | (needs testing)    | Slow / Normal / Fast               |
| Dash Type     | Standard           | Standard dash expected for DB char |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

As the first Saiyan to achieve SSJ2 form, Gohan may have form-specific mechanics.
Likely candidate for rage/power-up mechanics given his character arc.

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID | Test Description | Priority | Status | Result |
| ------- | ---------------- | -------- | ------ | ------ |
| db_b_07-001 | Full moveset damage values | P2 | PENDING | |
| db_b_07-002 | Available koma sizes | P2 | PENDING | |
| db_b_07-003 | Compare damage to Gotenks (same jpower block) | P1 | PENDING | |

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

4. **Block 3 Comparison**
   - [ ] Compare all moves to Gotenks (same jpower block) to understand entry selection

---

## Unknown / Needs Research

### Unverified Data

1. Tier value in chr_b.bin (affects base damage calculation)
2. formType value (0=Normal or 1=Powered)
3. Collision file entry count and structure

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. How do Gohan SSJ2 and Gotenks (both Block 3) select different moves from the same jpower block?
2. Does SSJ2 have any unique mechanics not present in other DB characters?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship              |
| ----------------- | ----------- | -------------- | ------------------------- |
| Gohan (SSJ)       | 5           | db_b_06        | Same character, lower form|
| Gotenks           | 7           | db_b_08        | Shares jpower Block 3     |
| Goku              | 0           | db_b_01        | Same charId=7 family      |

**Characters sharing jpower Block 3:**

- db_b_07 (Gohan SSJ2)
- db_b_08 (Gotenks)

**Characters sharing charId 7 (stat template):**

- Goku, Goku SSJ, Vegetto, Vegeta, Vegeta SSJ, Gohan SSJ, Gohan SSJ2, Gotenks, Majin Buu

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
- [Goku-Character-Map.md](./Goku-Character-Map.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
| 2026-01-29 | Initial Creation | File data from chr_b-Complete-Mapping.md | Needs human testing |

---

## Notes

- Shares jpower Block 3 with Gotenks - testing both characters will help understand
  entry selection mechanism
- Part of charId=7 family with Goku, suggesting similar stat template
- SSJ2 is Gohan's powered form - may have higher damage tier than base SSJ
