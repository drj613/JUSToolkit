# Kagura (gt_b_02) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Kagura through all data files to understand linkages.

---

## Basic Info

| Field           | Value               |
| --------------- | ------------------- |
| Character Name  | Kagura              |
| Series          | Gintama             |
| chr_b Index     | 53                  |
| Collision File  | gt_b_02.bin         |
| charId          | 2                   |
| classId         | 443                 |
| jpower Block    | 187                 |

---

## Notable Data Point: High jpower Block

Kagura's jpower Block 187 is significantly higher than most other characters:
- Compare to Gintoki (same series): Block 93
- Compare to other chars in this batch: Blocks 63-99

This suggests her damage data is stored in a later section of jpower.bin, possibly indicating she was added later in development or has unique damage scaling.

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Kagura:** TBD koma

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

**Note:** Kagura is a Yato clan member with superhuman strength. Her attacks are primarily punch/kick based and should be Impact type.

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 53)

| Field        | Value | Notes                                       |
| ------------ | ----- | ------------------------------------------- |
| charId       | 2     | Low ID suggests early/important character   |
| formType     | TBD   | 0=Normal, 1=Powered                         |
| tier         | TBD   | 1=-1 dmg, 2=normal, 3=+1 dmg                |
| komaSize     | TBD   | Internal size (not deck koma)               |
| classId      | 443   | Low byte = jpower block index               |
| jpower Block | 187   | classId & 0xFF - Notably high block number  |

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

Profile: TBD (likely Attack-heavy given Yato strength)
```

### Collision File (gt_b_02.bin)

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

### jpower Block 187 Analysis

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

**Note:** Block 187 is near the end of jpower.bin's 311 entries, suggesting either:
- Later development addition
- Unique damage scaling requirements
- Overflow from earlier series allocation

### Sprite Archives (chr/)

| Archive        | Size | Purpose         |
| -------------- | ---- | --------------- |
| gt_b_02c.aar   |      | Main sprites    |
| gt_b_02_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                            | This Character        |
| -------- | ----------------------------------- | --------------------- |
| 0x0924B0 | Collision file pointer table        | Index 53              |
| 0x08D4A0 | chr_b -> collision identity mapping |                       |
| 0x09E780 | Koma name table                     |                       |

---

## Mechanics

### Weight Category

**Category:** TBD (possibly LIGHT despite strength - she's small)

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

TBD - Kagura is a member of the Yato clan, one of the strongest warrior races in the Gintama universe. Despite her petite appearance, she possesses superhuman strength. She fights with her umbrella (which also functions as a gun) and raw physical power.

Expected mechanics:
- High damage output
- Umbrella-based attacks (possibly projectile)
- Pure Impact damage type

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
| gt_b_02-001| Verify available koma sizes| P2       | PENDING   |        |
| gt_b_02-002| Test all B move damage     | P2       | PENDING   |        |
| gt_b_02-003| Compare damage to Gintoki  | P2       | PENDING   |        |

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
   - [ ] Umbrella projectile mechanics (if any)

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
- [ ] Why jpower Block 187 is so different from Gintoki's Block 93

### Open Questions

1. Why is Kagura's jpower block (187) so much higher than Gintoki's (93)?
2. Does the high block number indicate different damage scaling?
3. Does she have umbrella gun projectile attacks?
4. Is her charId=2 related to One Piece characters (need to verify)?

---

## Related Characters

| Character | chr_b Index | Collision File | Relationship                  |
| --------- | ----------- | -------------- | ----------------------------- |
| Gintoki   | 52          | gt_b_01.bin    | Same series, different block  |

**Characters sharing jpower Block 187:**

- Kagura (gt_b_02) only (TBD - requires further analysis)

**Note:** Despite being from the same series, Gintoki and Kagura use completely different jpower blocks (93 vs 187), suggesting independently designed damage profiles.

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

Kagura is one of the main characters of Gintama and a member of the Yato clan, an alien warrior race known for their incredible strength and combat ability. Despite being a young girl, her physical power rivals or exceeds most adult fighters.

Her primary weapon is a special umbrella that functions both as a melee weapon and a gun, blocking sunlight (Yato weakness) while also serving as offense. In combat, she combines Yato-style martial arts with umbrella techniques.

The significant gap between her jpower block (187) and Gintoki's (93) is an interesting data point that warrants investigation - it suggests the developers may have designed her damage profile separately or added her character data later in development.
