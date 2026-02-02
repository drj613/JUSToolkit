# Gotenks SSJ (db_b_09) - Complete Character Mapping

Deep dive analysis mapping Gotenks SSJ through all data files to understand
linkages.

---

## Basic Info

| Field          | Value                |
| -------------- | -------------------- |
| Character Name | Gotenks (SSJ)        |
| Series         | Dragon Ball          |
| chr_b Index    | 8                    |
| Collision File | db_b_09.bin          |
| charId         | 54                   |
| tier           | (needs verification) |
| jpower Block   | 4                    |
| classId        | 516                  |

**IMPORTANT NOTE:** Gotenks SSJ has charId=54, which is DIFFERENT from base
Gotenks (charId=7). This suggests SSJ form uses a completely different stat
template.

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Gotenks SSJ:** (needs human testing) koma

### Move List (PARTIALLY VERIFIED 2026-01-31)

| Move   | Damage | Type       | Notes            |
| ------ | ------ | ---------- | ---------------- |
| B      | 10     | Punch/Kick | Verified in-game |
| fwd B  |        | Punch/Kick |                  |
| up B   |        | Punch/Kick |                  |
| down B |        | Punch/Kick |                  |
| air B  |        | Punch/Kick |                  |
| Y      |        | Punch/Kick |                  |
| fwd Y  |        | Energy     |                  |
| up Y   |        | Punch/Kick |                  |
| down Y |        | Punch/Kick |                  |
| air Y  |        | Energy     |                  |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense
  passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense
  passive)
- **Punch/Kick** - Physical attacks (expected for Dragon Ball fighters)
- **Energy** - Projectile/energy attacks (ki blasts, Kamikaze Ghosts)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 8)

| Field        | Value          | Notes                                   |
| ------------ | -------------- | --------------------------------------- |
| charId       | 54             | DIFFERENT from base Gotenks (charId=7)! |
| formType     | (needs verify) | 0=Normal, 1=Powered                     |
| tier         | (needs verify) | 1=-1 dmg, 2=normal, 3=+1 dmg            |
| komaSize     | (needs verify) | Internal size (not deck koma)           |
| classId      | 516            | Low byte = jpower block index           |
| jpower Block | 4              | classId & 0xFF                          |

### charId Anomaly

**This is significant!** Most Dragon Ball characters share charId=7:

- Goku, Goku SSJ, Vegetto, Vegeta, Vegeta SSJ, Gohan SSJ, Gohan SSJ2, Gotenks,
  Majin Buu

But Gotenks SSJ has charId=54, which is shared with:

- Frieza (chr_b[10])
- Kakashi (Naruto)
- Dio (JoJo)
- Train (Black Cat)
- Kazuki (Busou Renkin)

This suggests Gotenks SSJ uses a completely different stat template than his
base form, possibly to represent his powered-up state with different
attack/defense ratios.

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

### Collision File (db_b_09.bin)

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

### jpower Block 4 Analysis

From jpower-Mapping.md, Block 4 contains:

- Entries with damages: [7,7,7,28]
- This suggests 3 normal attacks (7 damage each) and one stronger attack (28
  damage)

**Characters sharing Block 4:**

- db_b_09 (Gotenks SSJ) - chr_b[8], classId=516 (ONLY character in this block)

**Note:** Gotenks SSJ has his own unique jpower block (4), not shared with any
other character. This is unusual compared to other Dragon Ball characters who
often share blocks.

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

| Archive        | Size | Purpose         |
| -------------- | ---- | --------------- |
| db_b_09c.aar   |      | Main sprites    |
| db_b_09_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                            | This Character |
| -------- | ----------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table        | Index 8        |
| 0x08D4A0 | chr_b -> collision identity mapping |                |
| 0x09E780 | Koma name table                     |                |

---

## Mechanics

### Weight Category

**Category:** (needs testing - likely LIGHT due to being a child character)

**Observations:**

- Gotenks SSJ is still a child fusion, likely lighter than adults
- May feel faster than base Gotenks due to SSJ transformation
- Displacement velocity: (needs comparison to Goku and base Gotenks)
- Walk speed: (needs comparison)

### Movement

| Property      | Value           | Notes                              |
| ------------- | --------------- | ---------------------------------- |
| Walk Speed    | (needs testing) | Likely faster than base Gotenks    |
| Dash Type     | Standard        | Standard dash expected for DB char |
| Dash Distance |                 |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

As the SSJ form of Gotenks:

- **Kamikaze Ghosts** - Signature attack (summon-type)
- **Super Ghost Kamikaze Attack** - Powered version of ghost attack
- **Galactic Donut** - Energy ring trap
- Higher damage output than base form expected

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the
> central queue at `docs/research/Human-Testing-Queue.md`. Format:
> `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                                   | Priority | Status  | Result |
| ----------- | -------------------------------------------------- | -------- | ------- | ------ |
| db_b_09-001 | Full moveset damage values                         | P2       | PENDING |        |
| db_b_09-002 | Available koma sizes                               | P2       | PENDING |        |
| db_b_09-003 | Compare damage to base Gotenks (different charId!) | P1       | PENDING |        |
| db_b_09-004 | Verify charId=54 stat differences vs charId=7      | P1       | PENDING |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice
to have

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
   - [ ] Walk speed observation (compare to Goku=standard, base Gotenks)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku and base Gotenks)

3. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)
   - [ ] Kamikaze Ghost mechanics

4. **charId Investigation**
   - [ ] Compare stat feel (attack/defense ratio) to base Gotenks
   - [ ] Compare to other charId=54 characters (Frieza, Dio) if possible

---

## Unknown / Needs Research

### Unverified Data

1. Tier value in chr_b.bin (affects base damage calculation)
2. formType value (0=Normal or 1=Powered)
3. Collision file entry count and structure
4. Why charId differs from base Gotenks

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Why does Gotenks SSJ have charId=54 while base Gotenks has charId=7?
2. Does the different charId result in noticeably different stat feel in-game?
3. Is Block 4 exclusively for Gotenks SSJ or are there other characters we
   haven't mapped?

---

## Related Characters

| Character | chr_b Index | Collision File | Relationship              |
| --------- | ----------- | -------------- | ------------------------- |
| Gotenks   | 7           | db_b_08        | Same character, base form |
| Frieza    | 10          | db_b_11        | Same charId=54            |
| Goku      | 0           | db_b_01        | Different charId (7)      |

**Characters sharing jpower Block 4:**

- db_b_09 (Gotenks SSJ) - ONLY character

**Characters sharing charId 54 (stat template):**

- Gotenks SSJ, Frieza, Kakashi, Dio, Train, Kazuki

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
- [Gotenks-Character-Map.md](./Gotenks-Character-Map.md)

---

## Session Log

| Date       | Session          | Verified                                 | Notes               |
| ---------- | ---------------- | ---------------------------------------- | ------------------- |
| 2026-01-29 | Initial Creation | File data from chr_b-Complete-Mapping.md | Needs human testing |

---

## Notes

- **ANOMALY:** Has charId=54 unlike other Dragon Ball characters (charId=7)
- Has unique jpower Block 4 (not shared with any other character)
- Comparing to base Gotenks will help understand how charId affects gameplay
- The charId=54 group includes diverse characters (Frieza, Dio, Kakashi) -
  likely represents a specific stat archetype rather than series grouping
