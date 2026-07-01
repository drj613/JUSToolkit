# Jaguar Junichi (pj_b_01) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Jaguar Junichi through all data files to understand linkages.

---

## Basic Info

| Field           | Value               |
| --------------- | ------------------- |
| Character Name  | Jaguar Junichi      |
| Series          | Pyu to Fuku! Jaguar |
| chr_b Index     | 55                  |
| Collision File  | pj_b_01.bin         |
| charId          | 28                  |
| classId         | 355                 |
| jpower Block    | 99                  |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Jaguar Junichi:** TBD koma

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

**Note:** Jaguar is a comedic musician character. His attacks likely involve his recorder (flute) and bizarre gag moves.

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 55)

| Field        | Value | Notes                         |
| ------------ | ----- | ----------------------------- |
| charId       | 28    | Pyu to Fuku! Jaguar series ID |
| formType     | TBD   | 0=Normal, 1=Powered           |
| tier         | TBD   | 1=-1 dmg, 2=normal, 3=+1 dmg  |
| komaSize     | TBD   | Internal size (not deck koma) |
| classId      | 355   | Low byte = jpower block index |
| jpower Block | 99    | classId & 0xFF                |

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

### Collision File (pj_b_01.bin)

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

### jpower Block 99 Analysis

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
| pj_b_01c.aar   |      | Main sprites    |
| pj_b_01_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                            | This Character        |
| -------- | ----------------------------------- | --------------------- |
| 0x0924B0 | Collision file pointer table        | Index 55              |
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

TBD - Jaguar Junichi is a gag manga character known for his terrible recorder (flute) playing. His fighting style in Jump games typically involves:
- Weaponized recorder attacks
- Sound-based moves (possibly projectiles)
- Absurdist comedy animations

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
| pj_b_01-001| Verify available koma sizes| P2       | PENDING   |        |
| pj_b_01-002| Test all B move damage     | P2       | PENDING   |        |

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
   - [ ] Sound/music-based attack properties

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

1. Does Jaguar have any sound/music-based projectile attacks?
2. Are his attacks Impact type (blunt recorder hits) or something else?
3. What gag mechanics does he have?

---

## Related Characters

| Character | chr_b Index | Collision File | Relationship    |
| --------- | ----------- | -------------- | --------------- |
| N/A       |             |                | Solo series rep |

**Characters sharing jpower Block 99:**

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

- [Character-Mapping.md](../research/Character-Mapping.md) (deck-builder order table)
- [jpower-Analysis.md](../formats/jpower-Analysis.md)
- [Collision-Format.md](../formats/Collision-Format.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

Jaguar Junichi is the main character of "Pyu to Fuku! Jaguar" (Blow the Flute! Jaguar), a gag manga series that ran in Weekly Shonen Jump from 2000 to 2010. He is a self-proclaimed "recorder musician" who runs a music school, though his playing is notoriously terrible.

The series prefix "pj" in the file naming (pj_b_01) stands for "Pyu Jaguar" or similar. As a purely comedic character with no combat abilities in the source material, his fighting game moveset is entirely invented for Jump games, typically featuring recorder-based attacks and absurdist humor.

Jaguar represents one of the more obscure series in Jump Ultimate Stars, appealing primarily to Japanese audiences familiar with the gag manga.
