# Yusuke Urameshi (yh_b_01) - Complete Character Mapping

Deep dive analysis mapping Yusuke Urameshi through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Yusuke Urameshi    |
| Series          | Yu Yu Hakusho      |
| chr_b Index     | 32                 |
| Collision File  | yh_b_01.bin        |
| charId          | 45                 |
| tier            | (needs extraction) |
| jpower Block    | 37                 |
| classId         | 549                |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Yusuke Urameshi:** (needs verification) koma

### Move List (CONFIRMED)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        | Punch/Kick |                       |
| fwd B  |        | Punch/Kick |                       |
| up B   |        | Punch/Kick |                       |
| down B |        | Punch/Kick |                       |
| air B  |        | Punch/Kick |                       |
| Y      |        | Energy     | Spirit Gun?           |
| fwd Y  |        | Energy     |                       |
| up Y   |        | Energy     |                       |
| down Y |        | Energy     |                       |
| air Y  |        | Energy     |                       |

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

### chr_b.bin Entry (Index 32)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 45    |                                |
| formType     |       | 0=Normal, 1=Powered            |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     |       | Internal size (not deck koma)  |
| classId      | 549   | Low byte = jpower block index  |
| jpower Block | 37    | classId & 0xFF                 |

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

### Collision File (yh_b_01.bin)

| Property    | Value               |
| ----------- | ------------------- |
| Size        | (needs extraction)  |
| Entry Count | (needs extraction)  |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 37 Analysis

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
| yh_b_01c.aar     |      | Main sprites    |
| yh_b_01_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 32       |
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

**Buff System:**

Yusuke is part of **Buff Group A** (along with Ichigo). This means:
- Yusuke can receive and share buffs with Ichigo
- Yusuke cannot share buffs with Group B characters (Fuusuke, Raoh)
- damageFlags=64 (0x40) triggers buff, modifier sub-records contain 2x damage

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description        | Priority | Status    | Result |
| ----------- | ----------------------- | -------- | --------- | ------ |
| yh_b_01-001 | B move damage (neutral) | P2       | PENDING   |        |
| yh_b_01-002 | All move damage values  | P2       | PENDING   |        |

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
   - [ ] Buff compatibility verification (Group A with Ichigo)
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Complete collision file entry count and structure
2. battleParams byte values
3. Full jpower block 37 entry contents

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. How does the buff sharing with Group A work mechanically?
2. Does Yusuke use Spirit Gun mechanics similar to Goku's energy attacks?

---

## Related Characters

| Character | chr_b Index | Collision File | Relationship                   |
| --------- | ----------- | -------------- | ------------------------------ |
| Kurama    | 33          | yh_b_02.bin    | Same series                    |
| Hiei      | 34          | yh_b_03.bin    | Same series                    |
| Ichigo    | 39          | bl_b_01.bin    | Buff Group A compatible        |

**Characters sharing jpower Block 37:**

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

- Yusuke is confirmed as part of Buff Group A (compatible with Ichigo) per Research-Status.md
- Spirit Detective abilities suggest mix of Punch/Kick and Energy damage types
