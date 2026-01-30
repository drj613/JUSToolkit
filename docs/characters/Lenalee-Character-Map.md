# Lenalee Lee (dg_b_02) - Complete Character Mapping

Deep dive analysis mapping Lenalee Lee through all data files to understand linkages.

---

## Basic Info

| Field           | Value               |
| --------------- | ------------------- |
| Character Name  | Lenalee Lee         |
| Series          | D.Gray-man          |
| chr_b Index     | 46                  |
| Collision File  | dg_b_02.bin         |
| charId          | 3                   |
| classId         | 577                 |
| jpower Block    | 65                  |

---

## CRITICAL: Cross-Series charId Sharing

**Lenalee uses charId=3, which is shared with ALL Bleach characters!**

This is a notable anomaly in the data structure:

| Character       | Series     | chr_b Index | charId | classId |
| --------------- | ---------- | ----------- | ------ | ------- |
| Ichigo (Base)   | Bleach     | 39          | 3      | 564     |
| Ichigo (Bankai) | Bleach     | 40          | 3      | 564     |
| Rukia           | Bleach     | 41          | 3      | 565     |
| Renji           | Bleach     | 42          | 3      | 310     |
| Toushiro        | Bleach     | 43          | 3      | 567     |
| **Lenalee Lee** | D.Gray-man | 46          | 3      | 577     |

**Implications:**

1. The `charId` field appears to define a **stat template** shared across characters
2. Lenalee inherits base stat parameters from the Bleach template
3. The `classId` field provides the differentiation (unique jpower block)
4. This may indicate that Lenalee was designed with Bleach-style combat balance

**Research needed:** Verify if Lenalee's battleParams bytes [8-10] match Bleach characters.

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Lenalee Lee:** TBD koma

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

**Note:** Lenalee's attacks are kick-based (Dark Boots Innocence), likely all Impact type.

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 46)

| Field        | Value | Notes                                          |
| ------------ | ----- | ---------------------------------------------- |
| charId       | 3     | **SHARED WITH BLEACH** - Cross-series template |
| formType     | 1     | Powered form (likely Dark Boots active)        |
| tier         | 1     | -1 damage modifier                             |
| komaSize     | 2     | Internal size                                  |
| classId      | 577   | Low byte = jpower block index                  |
| jpower Block | 65    | classId & 0xFF - Shared with Allen Walker      |

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

Profile: TBD (likely Speed-focused given her agile fighting style)
```

### Collision File (dg_b_02.bin)

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

### jpower Block 65 Analysis

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       |                   |       |

**Damage Formula:**

```
base_damage = (jpower_total / 5) + (tier - 2)
```

- tier 1: -1 modifier (Lenalee's tier)
- tier 2: no modifier
- tier 3: +1 modifier

**IMPORTANT:** Lenalee shares jpower Block 65 with Allen Walker (dg_b_01). Their damage entries in jpower.bin are identical, but tier differences affect final damage.

### Sprite Archives (chr/)

| Archive        | Size | Purpose         |
| -------------- | ---- | --------------- |
| dg_b_02c.aar   |      | Main sprites    |
| dg_b_02_Xc.aar |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                            | This Character        |
| -------- | ----------------------------------- | --------------------- |
| 0x0924B0 | Collision file pointer table        | Index 46              |
| 0x08D4A0 | chr_b -> collision identity mapping |                       |
| 0x09E780 | Koma name table                     |                       |

---

## Mechanics

### Weight Category

**Category:** LIGHT (expected)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: TBD (expected high - fast movement)
- Walk speed: TBD (expected Fast)
- Comparison to reference characters: Likely similar to Killua (fast dasher)

### Movement

| Property      | Value    | Notes                                    |
| ------------- | -------- | ---------------------------------------- |
| Walk Speed    | TBD      | Expected Fast (Dark Boots enhance speed) |
| Dash Type     | TBD      | Likely Standard but very fast            |
| Dash Distance |          |                                          |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

TBD - Lenalee uses the Dark Boots Innocence, equipment-type anti-Akuma weapons worn on her legs. Her fighting style is entirely kick-based with enhanced speed and aerial mobility.

Expected mechanics:
- Fast movement speed
- Aerial combo emphasis
- Impact-type damage on all attacks

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID    | Test Description                        | Priority | Status    | Result |
| ---------- | --------------------------------------- | -------- | --------- | ------ |
| dg_b_02-001| Verify available koma sizes             | P2       | PENDING   |        |
| dg_b_02-002| Test all B move damage                  | P2       | PENDING   |        |
| dg_b_02-003| Compare stats to Bleach chars (charId=3)| P1       | PENDING   |        |
| dg_b_02-004| Verify all moves are Impact type        | P2       | PENDING   |        |

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
   - [ ] Compare knockback received to Ichigo (same charId=3)

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
- [ ] Confirmation of battleParams similarity to Bleach characters

### Open Questions

1. Why does Lenalee share charId=3 with Bleach characters?
2. Does charId=3 confer any stat inheritance from Bleach template?
3. Are Lenalee's battleParams bytes [8-10] identical to any Bleach character?
4. Is this cross-series sharing intentional game design or data reuse?

---

## Related Characters

| Character    | chr_b Index | Collision File | Relationship                   |
| ------------ | ----------- | -------------- | ------------------------------ |
| Allen Walker | 45          | dg_b_01.bin    | Same series, same jpower block |
| Ichigo       | 39-40       | bl_b_01/02.bin | Same charId=3 (cross-series!)  |
| Rukia        | 41          | bl_b_03.bin    | Same charId=3 (cross-series!)  |
| Renji        | 42          | bl_b_04.bin    | Same charId=3 (cross-series!)  |
| Toushiro     | 43          | bl_b_05.bin    | Same charId=3 (cross-series!)  |

**Characters sharing jpower Block 65:**

- Allen Walker (dg_b_01) - charId=32
- Lenalee Lee (dg_b_02) - charId=3

**Characters sharing charId=3:**

- All Bleach battle characters (indices 39-43)
- Lenalee Lee (index 46) - D.Gray-man

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
- [Ichigo-Character-Map.md](./Ichigo-Character-Map.md) - For charId=3 comparison

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

Lenalee Lee is the second battle character from D.Gray-man and presents a unique case study in the game's data structure. Her charId=3 is shared with all Bleach characters, suggesting the developers may have used Bleach's stat template as a base for her balance.

The Dark Boots Innocence she wields are equipment-type weapons that enhance her leg strength and speed, making her an agile, kick-focused fighter. This contrasts with Allen's arm-based Innocence attacks.

**Key research priority:** Understanding why Lenalee shares charId with Bleach could reveal important insights about the game's character stat system and potential stat inheritance between characters.
