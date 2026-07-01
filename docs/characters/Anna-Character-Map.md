# Anna Kyoyama (sk_b_03) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Anna Kyoyama through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Anna Kyoyama       |
| Series          | Shaman King        |
| chr_b Index     | 27                 |
| Collision File  | sk_b_03.bin        |
| charId          | 6                  |
| tier            | (needs extraction) |
| jpower Block    | 23                 |
| classId         | 535                |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Anna Kyoyama:** (needs human testing)

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

### chr_b.bin Entry (Index 27)

| Field        | Value | Notes                        |
| ------------ | ----- | ---------------------------- |
| charId       | 6     | Shared with Yoh variants     |
| formType     |       | 0=Normal, 1=Powered          |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg |
| komaSize     |       | Internal size (not deck koma)|
| classId      | 535   | Different from Yoh (534)     |
| jpower Block | 23    | Different from Yoh (22)      |

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

### Collision File (sk_b_03.bin)

| Property    | Value                 |
| ----------- | --------------------- |
| Size        | (needs extraction)    |
| Entry Count | 23                    |
| Location    | ChrBin.aar/chr/col/   |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- Anna has more collision entries (23) than both Yoh forms (14, 19)
- Suggests a more complex moveset than the protagonist
- damageFlags field does NOT represent actual damage values

### jpower Block 23 Analysis

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
| sk_b_03c.aar     |      | Main sprites    |
| sk_b_03_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 27       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** (needs testing - may be LIGHT based on character)

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

- Anna is an itako (shaman medium) who uses spirit summoning
- May have summon-type attacks (collision type 5)
- Different jpower block from Yoh despite same series

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
| sk_b_03-001| Available koma sizes          | P2       | PENDING   |        |
| sk_b_03-002| B move damage (neutral)       | P2       | PENDING   |        |
| sk_b_03-003| Full moveset damage values    | P2       | PENDING   |        |
| sk_b_03-004| Dash type (standard/flash)    | P2       | PENDING   |        |
| sk_b_03-005| Weight category               | P2       | PENDING   |        |
| sk_b_03-006| Identify summon moves if any  | P2       | PENDING   |        |

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
   - [ ] Identify any summon attacks (type 5 collision)
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact tier value in chr_b.bin
2. battleParams byte values
3. All collision file entry details
4. Whether Anna uses summon mechanics

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Anna use summon-type attacks like Yugi or Dio?
2. Why more collision entries than Yoh despite being a supporting character?
3. Any unique mechanics related to her itako abilities?

---

## Related Characters

| Character        | chr_b Index | Collision File | Relationship  |
| ---------------- | ----------- | -------------- | ------------- |
| Yoh Asakura      | 25          | sk_b_01.bin    | Same series   |
| Yoh (White Swan) | 26          | sk_b_02.bin    | Same series   |

**Characters sharing jpower Block 23:**

- sk_b_03 (Anna Kyoyama) - only character on this block

**Characters sharing charId 6:**

- sk_b_01 (Yoh)
- sk_b_02 (Yoh White Swan)
- sk_b_03 (Anna)

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

- Anna shares charId=6 with both Yoh forms (stat template grouping)
- Has her own unique jpower block (23) unlike Yoh forms that share block 22
- More collision entries (23) suggests diverse moveset
- As an itako, may have unique summon or spiritual attack mechanics
