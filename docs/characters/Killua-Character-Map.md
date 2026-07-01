# Killua Zoldyck (hh_b_02) - Complete Character Mapping

Deep dive analysis mapping Killua Zoldyck through all data files to understand linkages.

---

## Basic Info

| Field           | Value           |
| --------------- | --------------- |
| Character Name  | Killua Zoldyck  |
| Series          | Hunter x Hunter |
| chr_b Index     | 31              |
| Collision File  | hh_b_02.bin     |
| charId          | 23              |
| tier            | (needs extraction) |
| jpower Block    | 34              |
| classId         | 290             |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Killua Zoldyck:** (needs human testing)

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

### chr_b.bin Entry (Index 31)

| Field        | Value | Notes                        |
| ------------ | ----- | ---------------------------- |
| charId       | 23    |                              |
| formType     |       | 0=Normal, 1=Powered          |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg |
| komaSize     |       | Internal size (not deck koma)|
| classId      | 290   |                              |
| jpower Block | 34    | classId & 0xFF               |

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

### Collision File (hh_b_02.bin)

| Property    | Value                 |
| ----------- | --------------------- |
| Size        | (needs extraction)    |
| Entry Count | 26                    |
| Location    | ChrBin.aar/chr/col/   |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- 26 collision entries (more than Gon's 21)
- Likely includes lightning/Godspeed attacks
- damageFlags field does NOT represent actual damage values

### jpower Block 34 Analysis

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
| hh_b_02c.aar     |      | Main sprites    |
| hh_b_02_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 31       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** (needs testing - may be LIGHT based on character)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: (needs testing)
- Walk speed: **FAST** (documented as fast walker)
- Comparison to reference characters: (needs testing)

### Movement

| Property      | Value     | Notes                                       |
| ------------- | --------- | ------------------------------------------- |
| Walk Speed    | **FAST**  | **CONFIRMED** - Fast dasher (like Lenalee)  |
| Dash Type     | **FAST**  | Quick, covers lots of ground                |
| Dash Distance |           |                                             |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)
- **Fast** - Quick dash covering lots of ground (Killua, Lenalee)

**CONFIRMED:** Killua is a **fast dasher** as documented in Ichigo-Character-Map.md (line 140):
> "Fast dashers: Killua, Lenalee (quick, cover lots of ground)"

This matches his Godspeed ability and assassin training.

### Unique Mechanics

- Killua is a Nen user - Transmutation type (electricity)
- Lightning-based attacks - may have special damage type
- Assassin with fast movement
- "Decreased lightning damage" passive exists in game (from Combat-Mechanics.md)

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID    | Test Description                 | Priority | Status    | Result |
| ---------- | -------------------------------- | -------- | --------- | ------ |
| hh_b_02-001| Available koma sizes             | P2       | PENDING   |        |
| hh_b_02-002| B move damage (neutral)          | P2       | PENDING   |        |
| hh_b_02-003| Full moveset damage values       | P2       | PENDING   |        |
| hh_b_02-004| Weight category                  | P2       | PENDING   |        |
| hh_b_02-005| Lightning damage type testing    | P1       | PENDING   |        |
| hh_b_02-006| Godspeed/speed mechanics         | P2       | PENDING   |        |

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
   - [x] Walk speed = **FAST** (confirmed in research docs)
   - [x] Dash type = **FAST** (confirmed in research docs)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Lightning damage type testing (use "Decreased lightning damage" passive)
   - [ ] Any buffs or special states (Godspeed?)
   - [ ] Damage type verification vs Slash/Impact passives

---

## Unknown / Needs Research

### Unverified Data

1. Exact tier value in chr_b.bin
2. battleParams byte values
3. All collision file entry details
4. Lightning damage implementation

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight category (needs testing)
- [ ] Which attacks deal lightning damage

### Open Questions

1. Does Killua's lightning count as a separate damage type?
2. Does the "Decreased lightning damage" passive affect his attacks?
3. Any Godspeed mechanics in his specials?
4. Is his weight LIGHT like Lenalee (another fast character)?

---

## Related Characters

| Character   | chr_b Index | Collision File | Relationship         |
| ----------- | ----------- | -------------- | -------------------- |
| Gon Freecss | 30          | hh_b_01.bin    | Same series, partner |

**Characters sharing charId 23:**

- hh_b_02 (Killua Zoldyck) - unique charId

**Characters sharing jpower Block 34:**

- hh_b_02 (Killua Zoldyck) - only character on this block

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                               |
| -------- | -------------------------------------- |
| 0x0924B0 | Collision file pointer table           |
| 0x08D4A0 | chr_b -> collision identity mapping    |
| 0x09E780 | Koma name table                        |

### Related Documentation

- [chr_b-Mapping.md](../formats/chr_b-Mapping.md)
- [jpower-Analysis.md](../formats/jpower-Analysis.md)
- [Collision-Format.md](../formats/Collision-Format.md)
- [Character-Mapping.md](../research/Character-Mapping.md)
- [Combat-Mechanics.md](../research/Combat-Mechanics.md) - Lightning damage passive

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- Killua is the deuteragonist of Hunter x Hunter
- **Fast dasher** - confirmed unique movement style (like Lenalee)
- Transmutation Nen user - electricity/lightning attacks
- Unique charId (23) - not shared with other characters
- 26 collision entries (5 more than Gon) suggests more varied moveset
- Lightning damage may be a subtype of Energy (damage2) per Combat-Mechanics.md
- "Decreased lightning damage" passive exists - need to test if it affects Killua
