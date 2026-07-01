# Hiei (yh_b_03) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Hiei through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Hiei               |
| Series          | Yu Yu Hakusho      |
| chr_b Index     | 34                 |
| Collision File  | yh_b_03.bin        |
| charId          | 47                 |
| tier            | (needs extraction) |
| jpower Block    | 42                 |
| classId         | 298                |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Hiei:** (needs verification) koma

### Move List (CONFIRMED)

| Move   | Damage | Type       | Notes                       |
| ------ | ------ | ---------- | --------------------------- |
| B      |        | Slashing   | Sword attacks               |
| fwd B  |        | Slashing   |                             |
| up B   |        | Slashing   |                             |
| down B |        | Slashing   |                             |
| air B  |        | Slashing   |                             |
| Y      |        | Slashing?  |                             |
| fwd Y  |        | Energy?    | Dragon of the Darkness Flame|
| up Y   |        | Energy?    |                             |
| down Y |        | Energy?    |                             |
| air Y  |        |            |                             |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

**Note:** Hiei uses a katana for physical attacks and Dragon of the Darkness Flame for special attacks. Need to verify damage types.

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 34)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 47    | Shared with Yugi, Muhyo        |
| formType     |       | 0=Normal, 1=Powered            |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     |       | Internal size (not deck koma)  |
| classId      | 298   | Low byte = jpower block index  |
| jpower Block | 42    | classId & 0xFF                 |

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

### Collision File (yh_b_03.bin)

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

### jpower Block 42 Analysis

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
| yh_b_03c.aar     |      | Main sprites    |
| yh_b_03_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 34       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** (needs verification)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity:
- Walk speed: Likely fast (Hiei is known for speed)
- Comparison to reference characters:

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    |                    | Slow / Normal / Fast               |
| Dash Type     |                    | Standard / Flash (likely Flash)    |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

**Note:** Given Hiei's character as the fastest of the Yu Yu Hakusho team, he likely has Flash dash and high walk speed.

### Unique Mechanics

**Dragon of the Darkness Flame:**

Hiei's signature ability - need to determine:
- Projectile type (True Projectile or Extended Hitbox)
- Damage type (likely Energy)
- Any special properties (burn, multi-hit, etc.)

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                | Priority | Status    | Result |
| ----------- | ------------------------------- | -------- | --------- | ------ |
| yh_b_03-001 | B move damage (neutral)         | P2       | PENDING   |        |
| yh_b_03-002 | Dash type verification (Flash?) | P2       | PENDING   |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y / up Y / down Y damage (Dragon attacks)
   - [ ] All X move damage at each koma size

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast, Franky=slow)
   - [ ] Dash type (standard or flash) - expected Flash
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Dragon of the Darkness Flame damage type (Energy?)
   - [ ] Any buffs or special states
   - [ ] Sword damage type verification (use Slash Defense passive)

---

## Unknown / Needs Research

### Unverified Data

1. Complete collision file entry count and structure
2. battleParams byte values
3. Full jpower block 42 entry contents

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Dragon attack damage type classification
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Is Hiei's dash type Flash (consistent with his speed characterization)?
2. Does Dragon of the Darkness Flame have special properties beyond Energy damage?

---

## Related Characters

| Character | chr_b Index | Collision File | Relationship     |
| --------- | ----------- | -------------- | ---------------- |
| Yusuke    | 32          | yh_b_01.bin    | Same series      |
| Kurama    | 33          | yh_b_02.bin    | Same series      |
| Yugi      | 35          | yo_b_01.bin    | Same charId (47) |

**Characters sharing jpower Block 42:**

- (needs verification)

**Characters sharing charId 47:**

- Hiei (yh_b_03)
- Yugi (yo_b_01)
- Muhyo (mr_b_01)
- Taikoubou (hs_b_01)

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

- Hiei shares charId=47 with Yugi, Muhyo, and Taikoubou - all summon/special type characters
- Known as the fastest member of Team Urameshi, likely has high walk speed and Flash dash
- Mix of sword (Slashing) and Dragon (Energy?) attacks
