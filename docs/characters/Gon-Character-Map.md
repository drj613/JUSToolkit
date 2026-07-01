# Gon Freecss (hh_b_01) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Gon Freecss through all data files to understand linkages.

---

## Basic Info

| Field           | Value           |
| --------------- | --------------- |
| Character Name  | Gon Freecss     |
| Series          | Hunter x Hunter |
| chr_b Index     | 30              |
| Collision File  | hh_b_01.bin     |
| charId          | 42              |
| tier            | (needs extraction) |
| jpower Block    | 33              |
| classId         | 545             |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Gon Freecss:** (needs human testing)

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

### chr_b.bin Entry (Index 30)

| Field        | Value | Notes                        |
| ------------ | ----- | ---------------------------- |
| charId       | 42    |                              |
| formType     |       | 0=Normal, 1=Powered          |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg |
| komaSize     |       | Internal size (not deck koma)|
| classId      | 545   |                              |
| jpower Block | 33    | classId & 0xFF               |

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

### Collision File (hh_b_01.bin)

| Property    | Value                 |
| ----------- | --------------------- |
| Size        | (needs extraction)    |
| Entry Count | 21                    |
| Location    | ChrBin.aar/chr/col/   |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- 21 collision entries (relatively straightforward moveset)
- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 33 Analysis

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
| hh_b_01c.aar     |      | Main sprites    |
| hh_b_01_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 30       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** STANDARD (confirmed in Research-Status.md)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: Standard (matches Goku, Dio, Momotaro)
- Walk speed: (needs testing)
- Comparison to reference characters: Standard weight confirmed

### Movement

| Property      | Value        | Notes                                      |
| ------------- | ------------ | ------------------------------------------ |
| Walk Speed    |              | Slow / Normal / Fast                       |
| Dash Type     | **STANDARD** | **CONFIRMED** - Normal dasher (like Goku)  |
| Dash Distance |              |                                            |

**Dash types:**

- **Standard** - Character dashes forward visibly (**Goku, Gon**, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

**CONFIRMED:** Gon is a **normal dasher** as documented in Ichigo-Character-Map.md (line 141).

### Unique Mechanics

- Gon is a Nen user - likely uses Enhancement type attacks
- Jajanken (Rock-Paper-Scissors) technique for specials
- Straightforward fighter with Impact damage type expected

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
| hh_b_01-001| Available koma sizes          | P2       | PENDING   |        |
| hh_b_01-002| B move damage (neutral)       | P2       | PENDING   |        |
| hh_b_01-003| Full moveset damage values    | P2       | PENDING   |        |
| hh_b_01-004| Walk speed                    | P2       | PENDING   |        |
| hh_b_01-005| Jajanken mechanics            | P2       | PENDING   |        |

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
   - [x] Dash type = **STANDARD** (confirmed in research docs)
   - [x] Weight = **STANDARD** (confirmed in research docs)

3. **Unique Mechanics**
   - [ ] Jajanken (Rock-Paper-Scissors) special mechanics
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact tier value in chr_b.bin
2. battleParams byte values
3. All collision file entry details

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Walk speed storage location

### Open Questions

1. How does Jajanken work in this game?
2. Does Gon have any charge/buff mechanics?
3. What damage types do his attacks deal (likely Impact)?

---

## Related Characters

| Character      | chr_b Index | Collision File | Relationship |
| -------------- | ----------- | -------------- | ------------ |
| Killua Zoldyck | 31          | hh_b_02.bin    | Same series, partner |

**Characters sharing charId 42:**

- hh_b_01 (Gon Freecss) - unique charId

**Characters sharing jpower Block 33:**

- hh_b_01 (Gon Freecss) - only character on this block

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

- Gon is the protagonist of Hunter x Hunter
- **Standard dasher and standard weight** - confirmed in research docs
- Enhancement Nen user - expect Impact/Punch damage type
- Jajanken technique (Rock-Paper-Scissors) likely featured in specials
- Unique charId (42) - not shared with other characters
- 21 collision entries suggests straightforward moveset
