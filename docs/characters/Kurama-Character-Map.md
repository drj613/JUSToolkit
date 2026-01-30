# Kurama (yh_b_02) - Complete Character Mapping

Deep dive analysis mapping Kurama through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Kurama             |
| Series          | Yu Yu Hakusho      |
| chr_b Index     | 33                 |
| Collision File  | yh_b_02.bin        |
| charId          | 28                 |
| tier            | (needs extraction) |
| jpower Block    | 39                 |
| classId         | 295                |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Kurama:** (needs verification) koma

### Move List (CONFIRMED)

| Move   | Damage | Type       | Notes                    |
| ------ | ------ | ---------- | ------------------------ |
| B      |        | Slashing?  | Rose Whip attacks        |
| fwd B  |        | Slashing?  |                          |
| up B   |        | Slashing?  |                          |
| down B |        | Slashing?  |                          |
| air B  |        | Slashing?  |                          |
| Y      |        | Slashing?  |                          |
| fwd Y  |        | Slashing?  |                          |
| up Y   |        | Slashing?  |                          |
| down Y |        | Slashing?  |                          |
| air Y  |        | Slashing?  |                          |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

**Note:** Kurama uses Rose Whip - need to verify if this counts as Slashing or has its own damage type.

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 33)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 28    |                                |
| formType     |       | 0=Normal, 1=Powered            |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     |       | Internal size (not deck koma)  |
| classId      | 295   | Low byte = jpower block index  |
| jpower Block | 39    | classId & 0xFF                 |

### battleParams (12 bytes)

```
Raw: [needs extraction]

Parsed:
  Slot 0: value=, flags=0x
  Slot 1: value=, flags=0x
  Slot 2: value=, flags=0x
  Slot 3: value=, flags=0x

Stats [8,9,10]: [, , ] = total
  Attack weight:
  Defense weight:
  Speed/Utility:

Byte 11: (special flag)

Profile:
```

### Collision File (yh_b_02.bin)

| Property    | Value               |
| ----------- | ------------------- |
| Size        | (needs extraction)  |
| Entry Count | (needs extraction)  |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 39 Analysis

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       |                   |       |

**Damage Formula:**

```
base_damage = (jpower_total / 5) + (tier - 2)
```

- tier 1: -1 modifier
- tier 2: no modifier
- tier 3: +1 modifier

### Sprite Archives (chr/)

| Archive          | Size | Purpose         |
| ---------------- | ---- | --------------- |
| yh_b_02c.aar     |      | Main sprites    |
| yh_b_02_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 33       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** (needs verification)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity:
- Walk speed:
- Comparison to reference characters:

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    |                    | Slow / Normal / Fast               |
| Dash Type     |                    | Standard / Flash                   |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**Rose Whip:**

Kurama's signature weapon - need to determine:
- Whether it counts as Slashing damage type
- Range properties (extended hitbox vs projectile)
- Any special properties (multi-hit, piercing, etc.)

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                   | Priority | Status    | Result |
| ----------- | ---------------------------------- | -------- | --------- | ------ |
| yh_b_02-001 | B move damage (neutral)            | P2       | PENDING   |        |
| yh_b_02-002 | Rose Whip damage type verification | P2       | PENDING   |        |

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
   - [ ] Rose Whip damage type (test with Slash Defense passive)
   - [ ] Any buffs or special states
   - [ ] Range/hitbox properties of whip attacks

---

## Unknown / Needs Research

### Unverified Data

1. Complete collision file entry count and structure
2. battleParams byte values
3. Full jpower block 39 entry contents

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Rose Whip damage type classification
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Rose Whip count as Slashing damage or a unique type?
2. What is the effective range of whip attacks compared to sword characters?

---

## Related Characters

| Character | chr_b Index | Collision File | Relationship |
| --------- | ----------- | -------------- | ------------ |
| Yusuke    | 32          | yh_b_01.bin    | Same series  |
| Hiei      | 34          | yh_b_03.bin    | Same series  |

**Characters sharing jpower Block 39:**

- (needs verification)

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
- [Research-Status.md](../research/Research-Status.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- Kurama has unique charId=28, also shared by Jaguar (pj_b_01) per chr_b-Complete-Mapping.md
- Rose Whip mechanics may be similar to Zoro's sword but with different range properties
