# Jotaro Kujo (jj_b_01) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Jotaro Kujo through all data files to understand linkages.

---

## Basic Info

| Field           | Value                    |
| --------------- | ------------------------ |
| Character Name  | Jotaro Kujo              |
| Series          | JoJo's Bizarre Adventure |
| chr_b Index     | 28                       |
| Collision File  | jj_b_01.bin              |
| charId          | 13                       |
| tier            | (needs extraction)       |
| jpower Block    | 25                       |
| classId         | 281                      |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Jotaro Kujo:** (needs human testing)

### Move List (CONFIRMED)

| Move   | Damage | Type | Notes |
| ------ | ------ | ---- | ----- |
| B      |        |      |       |
| fwd B  |        |      |       |
| up B   |        |      |       |
| down B |        |      |       |
| air B  |        |      |       |
| Y      |        |      |       |
| fwd Y  |        |      |       |
| up Y   |        |      |       |
| down Y |        |      |       |
| air Y  |        |      |       |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 28)

| Field        | Value | Notes                        |
| ------------ | ----- | ---------------------------- |
| charId       | 13    | Shared with several chars    |
| formType     |       | 0=Normal, 1=Powered          |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg |
| komaSize     |       | Internal size (not deck koma)|
| classId      | 281   |                              |
| jpower Block | 25    | classId & 0xFF               |

### battleParams (12 bytes)

```
Raw: [needs extraction]

Parsed:
  Slot 0: value=, flags=0x
  Slot 1: value=, flags=0x
  Slot 2: value=, flags=0x
  Slot 3: value=, flags=0x

Stats [8,9,10]: [, , ] =  total
  Attack weight:
  Defense weight:
  Speed/Utility:

Byte 11:  (special flag)

Profile:
```

### Collision File (jj_b_01.bin)

| Property    | Value                 |
| ----------- | --------------------- |
| Size        | (needs extraction)    |
| Entry Count | 37                    |
| Location    | ChrBin.aar/chr/col/   |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- 37 collision entries (same as Dio)
- May include Stand (Star Platinum) attack entries
- damageFlags field does NOT represent actual damage values

### jpower Block 25 Analysis

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
| jj_b_01c.aar     |      | Main sprites    |
| jj_b_01_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 28       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: (needs testing)
- Walk speed: (needs testing)
- Comparison to reference characters: (needs testing)

### Movement

| Property      | Value     | Notes                    |
| ------------- | --------- | ------------------------ |
| Walk Speed    |           | Slow / Normal / Fast     |
| Dash Type     |           | Standard / Flash         |
| Dash Distance |           |                          |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

- **Star Platinum (Stand)** - Jotaro's Stand likely performs some attacks
- May have Stand-based attacks similar to Dio's Stand attacks
- Iconic "ORA ORA ORA" rush attacks

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID    | Test Description              | Priority | Status    | Result |
| ---------- | ----------------------------- | -------- | --------- | ------ |
| jj_b_01-001| Available koma sizes          | P2       | PENDING   |        |
| jj_b_01-002| B move damage (neutral)       | P2       | PENDING   |        |
| jj_b_01-003| Full moveset damage values    | P2       | PENDING   |        |
| jj_b_01-004| Dash type (standard/flash)    | P2       | PENDING   |        |
| jj_b_01-005| Weight category               | P2       | PENDING   |        |
| jj_b_01-006| Identify Stand attack moves   | P2       | PENDING   |        |

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
   - [ ] Identify which moves use Star Platinum
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact tier value in chr_b.bin
2. battleParams byte values
3. All collision file entry details
4. Which moves are Stand attacks vs personal attacks

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Jotaro have Stand-based attacks like Dio?
2. How are Stand attacks categorized in collision data?
3. Any time stop mechanics in specials?

---

## Related Characters

| Character   | chr_b Index | Collision File | Relationship |
| ----------- | ----------- | -------------- | ------------ |
| Dio Brando  | 29          | jj_b_02.bin    | Same series, rival |

**Characters sharing charId 13:**

- Kyuubi Naruto
- Sakura
- Jotaro
- Kenshiro
- Raoh
- Seiya
- Gold Seiya

**Characters sharing jpower Block 25:**

- jj_b_01 (Jotaro Kujo) - only character on this block

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                               |
| -------- | -------------------------------------- |
| 0x0924B0 | Collision file pointer table           |
| 0x08D4A0 | chr_b -> collision identity mapping    |
| 0x09E780 | Koma name table                        |

### Related Documentation

- [Character-Mapping.md](../research/Character-Mapping.md) (deck-builder order table)
- [jpower-Analysis.md](../formats/jpower-Analysis.md)
- [Collision-Format.md](../formats/Collision-Format.md)
- [Character-Mapping.md](../research/Character-Mapping.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- Jotaro is the protagonist of JoJo Part 3: Stardust Crusaders
- Stand user with Star Platinum - expect punch/impact damage type
- Same collision entry count as Dio (37) - likely similar complexity
- charId 13 shared with mixed group including Kenshiro and Raoh
