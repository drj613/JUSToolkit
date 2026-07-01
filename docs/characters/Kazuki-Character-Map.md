# Kazuki Mutou (bu_b_01) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Kazuki Mutou through all data files to understand linkages.

---

## Basic Info

| Field           | Value               |
| --------------- | ------------------- |
| Character Name  | Kazuki Mutou        |
| Series          | Busou Renkin        |
| chr_b Index     | 44                  |
| Collision File  | bu_b_01.bin         |
| charId          | 54                  |
| classId         | 575                 |
| jpower Block    | 63                  |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Kazuki Mutou:** TBD koma

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

### chr_b.bin Entry (Index 44)

| Field        | Value | Notes                                   |
| ------------ | ----- | --------------------------------------- |
| charId       | 54    | Unique to Busou Renkin series           |
| formType     | TBD   | 0=Normal, 1=Powered                     |
| tier         | TBD   | 1=-1 dmg, 2=normal, 3=+1 dmg            |
| komaSize     | TBD   | Internal size (not deck koma)           |
| classId      | 575   | Low byte = jpower block index           |
| jpower Block | 63    | classId & 0xFF                          |

### battleParams (12 bytes)

```
Raw: [TBD]

Parsed:
  Slot 0: value=TBD, flags=0xTBD
  Slot 1: value=TBD, flags=0xTBD
  Slot 2: value=TBD, flags=0xTBD
  Slot 3: value=TBD, flags=0xTBD

Stats [8,9,10]: [TBD, TBD, TBD] = TBD total
  Attack weight:  TBD
  Defense weight: TBD
  Speed/Utility:  TBD

Byte 11: TBD (special flag)

Profile: TBD
```

### Collision File (bu_b_01.bin)

| Property    | Value              |
| ----------- | ------------------ |
| Size        | TBD bytes          |
| Entry Count | TBD                |
| Location    | ChrBin.aar/chr/col/|

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 63 Analysis

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

| Archive        | Size | Purpose         |
| -------------- | ---- | --------------- |
| bu_b_01c.aar   |      | Main sprites    |
| bu_b_01_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                            | This Character        |
| -------- | ----------------------------------- | --------------------- |
| 0x0924B0 | Collision file pointer table        | Index 44              |
| 0x08D4A0 | chr_b -> collision identity mapping |                       |
| 0x09E780 | Koma name table                     |                       |

---

## Mechanics

### Weight Category

**Category:** TBD

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: TBD
- Walk speed: TBD
- Comparison to reference characters: TBD

### Movement

| Property      | Value | Notes                    |
| ------------- | ----- | ------------------------ |
| Walk Speed    | TBD   | Slow / Normal / Fast     |
| Dash Type     | TBD   | Standard / Flash         |
| Dash Distance |       |                          |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

TBD - Kazuki uses the Sunlight Heart kakugane (alchemical weapon). May have lance-based attacks with extended reach.

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID    | Test Description           | Priority | Status    | Result |
| ---------- | -------------------------- | -------- | --------- | ------ |
| bu_b_01-001| Verify available koma sizes| P2       | PENDING   |        |
| bu_b_01-002| Test all B move damage     | P2       | PENDING   |        |

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

---

## Unknown / Needs Research

### Unverified Data

1. Exact koma sizes available in deck builder
2. All move damage values
3. Sprite archive sizes

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Kazuki have any lance-specific mechanics (extended reach)?
2. Are there any Busou Renkin-themed buffs or transformations?

---

## Related Characters

| Character  | chr_b Index | Collision File | Relationship      |
| ---------- | ----------- | -------------- | ----------------- |
| N/A        |             |                | Solo series rep   |

**Characters sharing jpower Block 63:**

- TBD (requires further analysis)

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                             |
| -------- | ------------------------------------ |
| 0x0924B0 | Collision file pointer table         |
| 0x08D4A0 | chr_b -> collision identity mapping  |
| 0x09E780 | Koma name table                      |

### Related Documentation

- [chr_b-Mapping.md](../formats/chr_b-Mapping.md)
- [jpower-Analysis.md](../formats/jpower-Analysis.md)
- [Collision-Format.md](../formats/Collision-Format.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

Kazuki Mutou is the sole representative from Busou Renkin in Jump Ultimate Stars. He wields the Sunlight Heart, an alchemical weapon created from a kakugane implanted in his chest. The weapon manifests as a lance with unique energy-based attacks.
