# Frieza (db_b_11) - Complete Character Mapping

Deep dive analysis mapping Frieza through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Frieza                 |
| Series          | Dragon Ball            |
| chr_b Index     | 10                     |
| Collision File  | db_b_11.bin            |
| charId          | 54                     |
| tier            | (needs verification)   |
| jpower Block    | 6                      |
| classId         | 262                    |

**IMPORTANT NOTE:** Frieza has charId=54, shared with Gotenks SSJ, Kakashi, Dio,
Train, and Kazuki. This is a cross-series stat template group.

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Frieza:** (needs human testing) koma

### Move List (NEEDS TESTING)

| Move   | Damage | Type       | Notes                     |
| ------ | ------ | ---------- | ------------------------- |
| B      |        | Punch/Kick |                           |
| fwd B  |        | Punch/Kick |                           |
| up B   |        | Energy     | Likely energy attack      |
| down B |        | Punch/Kick | Possible tail attack      |
| air B  |        | Energy     |                           |
| Y      |        | Punch/Kick |                           |
| fwd Y  |        | Energy     | Death Beam likely         |
| up Y   |        | Energy     |                           |
| down Y |        | Energy     |                           |
| air Y  |        | Energy     |                           |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks (Death Beam, Death Ball)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 10)

| Field        | Value            | Notes                                    |
| ------------ | ---------------- | ---------------------------------------- |
| charId       | 54               | Cross-series stat template               |
| formType     | (needs verify)   | 0=Normal, 1=Powered                      |
| tier         | (needs verify)   | 1=-1 dmg, 2=normal, 3=+1 dmg             |
| komaSize     | (needs verify)   | Internal size (not deck koma)            |
| classId      | 262              | Low byte = jpower block index            |
| jpower Block | 6                | classId & 0xFF                           |

### charId 54 Template Group

Frieza shares charId=54 with characters from different series:
- Gotenks SSJ (Dragon Ball)
- Kakashi (Naruto)
- Dio (JoJo)
- Train (Black Cat)
- Kazuki (Busou Renkin)

This cross-series grouping suggests charId represents a gameplay archetype
(possibly balanced offense/projectile-focused) rather than series or character type.

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

### Collision File (db_b_11.bin)

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

### jpower Block 6 Analysis

**Characters sharing Block 6:**

- db_b_11 (Frieza) - chr_b[10], classId=262 (ONLY character in this block)

**Note:** Frieza has his own unique jpower block (6), not shared with any other
character.

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

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| db_b_11c.aar         |      | Main sprites    |
| db_b_11_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 10                    |
| 0x08D4A0 | chr_b -> collision identity mapping   |                             |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** (needs testing - could be LIGHT due to smaller frame)

**Observations:**

- Frieza in final form is relatively small/compact
- May feel lighter and faster than Saiyans
- Displacement velocity: (needs comparison to Goku)
- Walk speed: (needs comparison)

### Movement

| Property      | Value              | Notes                                   |
| ------------- | ------------------ | --------------------------------------- |
| Walk Speed    | (needs testing)    | Possibly fast due to character design   |
| Dash Type     | Standard or Flash  | Could have Flash due to telekinesis     |
| Dash Distance |                    |                                         |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

**Note:** Frieza could potentially have Flash dash given his ability to move
extremely fast and his association with Dio (who also has Flash dash and shares charId).

### Unique Mechanics

Frieza's fighting style in the anime:
- **Death Beam** - Fast, precise energy attack (likely fwd Y)
- **Death Ball** - Large energy sphere (likely a special)
- **Tail attacks** - May have extended reach or unique hitboxes
- **Telekinesis** - Could manifest as unique movement or grabs

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
| db_b_11-001 | Full moveset damage values | P2 | PENDING | |
| db_b_11-002 | Available koma sizes | P2 | PENDING | |
| db_b_11-003 | Compare feel to Dio (same charId=54) | P2 | PENDING | |
| db_b_11-004 | Test dash type (standard or flash) | P2 | PENDING | |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] B move damage (neutral, no buffs)
   - [ ] fwd B damage
   - [ ] up B damage (count hits if multi-hit)
   - [ ] down B damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y / up Y / down Y damage (likely energy-heavy)
   - [ ] All X move damage at each koma size

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast, Franky=slow)
   - [ ] Dash type (standard or flash - important for charId=54 investigation)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)
   - [ ] Tail attack reach/hitbox
   - [ ] Death Beam properties

4. **charId Investigation**
   - [ ] Compare stat feel to other charId=54 characters
   - [ ] Note if Frieza feels similar to Dio in terms of movement/stats

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

1. Does Frieza have Flash dash like Dio (both charId=54)?
2. What is the common thread between charId=54 characters gameplay-wise?
3. Does Frieza have any projectile-centric mechanics (lots of Y attacks being energy)?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship              |
| ----------------- | ----------- | -------------- | ------------------------- |
| Gotenks SSJ       | 8           | db_b_09        | Same charId=54            |
| Dio (JoJo)        | 29          | jj_b_02        | Same charId=54            |
| Goku              | 0           | db_b_01        | Same series, different charId |

**Characters sharing jpower Block 6:**

- db_b_11 (Frieza) - ONLY character

**Characters sharing charId 54 (stat template):**

- Gotenks SSJ (Dragon Ball)
- Frieza (Dragon Ball)
- Kakashi (Naruto)
- Dio (JoJo)
- Train (Black Cat)
- Kazuki (Busou Renkin)

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

- Has charId=54, shared with diverse characters across series
- Has unique jpower Block 6 (not shared)
- Primary antagonist of Dragon Ball Z - likely strong energy-based moveset
- Comparing to Dio (same charId) could reveal what charId=54 represents
- Villain character - may have unique attack properties or mechanics
