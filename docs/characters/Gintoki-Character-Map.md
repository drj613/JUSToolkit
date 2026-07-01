# Gintoki Sakata (gt_b_01) - Complete Character Mapping

Deep dive analysis mapping Gintoki Sakata through all data files to understand linkages.

---

## Basic Info

| Field           | Value               |
| --------------- | ------------------- |
| Character Name  | Gintoki Sakata      |
| Series          | Gintama             |
| chr_b Index     | 52                  |
| Collision File  | gt_b_01.bin         |
| charId          | 5                   |
| classId         | 349                 |
| jpower Block    | 93                  |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Gintoki Sakata:** TBD koma

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

**Note:** Gintoki uses a wooden sword (bokuto), so attacks may be Impact type despite being sword-based.

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 52)

| Field        | Value | Notes                         |
| ------------ | ----- | ----------------------------- |
| charId       | 5     | Gintama series ID             |
| formType     | TBD   | 0=Normal, 1=Powered           |
| tier         | TBD   | 1=-1 dmg, 2=normal, 3=+1 dmg  |
| komaSize     | TBD   | Internal size (not deck koma) |
| classId      | 349   | Low byte = jpower block index |
| jpower Block | 93    | classId & 0xFF                |

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

### Collision File (gt_b_01.bin)

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

### jpower Block 93 Analysis

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
| gt_b_01c.aar   |      | Main sprites    |
| gt_b_01_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                            | This Character        |
| -------- | ----------------------------------- | --------------------- |
| 0x0924B0 | Collision file pointer table        | Index 52              |
| 0x08D4A0 | chr_b -> collision identity mapping |                       |
| 0x09E780 | Koma name table                     |                       |

---

## Mechanics

### Weight Category

**Category:** TBD (likely STANDARD)

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

TBD - Gintoki is a former samurai who wields a wooden sword (Lake Toya bokuto). Despite being a comedic character, he's an extremely skilled swordsman. His moveset likely combines competent sword techniques with occasional gag elements.

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
| gt_b_01-001| Verify available koma sizes| P2       | PENDING   |        |
| gt_b_01-002| Test all B move damage     | P2       | PENDING   |        |
| gt_b_01-003| Verify damage type (slash vs impact for bokuto) | P2 | PENDING | |

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
   - [ ] Bokuto attacks: Slashing or Impact?

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

1. Are Gintoki's bokuto attacks classified as Slashing or Impact?
2. Does Gintoki have any comedic/gag special moves?
3. How does his damage compare to Kagura (same series)?

---

## Related Characters

| Character | chr_b Index | Collision File | Relationship                |
| --------- | ----------- | -------------- | --------------------------- |
| Kagura    | 53          | gt_b_02.bin    | Same series, different block|

**Characters sharing jpower Block 93:**

- Gintoki Sakata (gt_b_01) only (TBD - requires further analysis)

**Note:** Kagura uses jpower Block 187, not 93. The Gintama characters have separate damage data despite being from the same series.

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

Gintoki Sakata is the main protagonist of Gintama, a comedy/action series set in an alternate Edo period invaded by aliens. Despite the series' comedic nature, Gintoki is a highly skilled samurai known as the "White Demon" (Shiroyasha) from the Joui War.

His weapon of choice is a wooden sword (bokuto) purchased from a TV shopping channel, supposedly made from a tree that grew by Lake Toya. This creates an interesting classification question for the damage system - wooden swords could logically be either Slashing (sword technique) or Impact (blunt weapon).

Gintoki and Kagura represent Gintama's two battle characters, with notably different jpower blocks (93 vs 187) suggesting distinct damage scaling.
