# Dio Brando (jj_b_02) - Complete Character Mapping

Deep dive analysis mapping Dio Brando through all data files to understand linkages.

---

## Basic Info

| Field           | Value                    |
| --------------- | ------------------------ |
| Character Name  | Dio Brando               |
| Series          | JoJo's Bizarre Adventure |
| chr_b Index     | 29                       |
| Collision File  | jj_b_02.bin              |
| charId          | 54                       |
| tier            | (needs extraction)       |
| jpower Block    | 26                       |
| classId         | 282                      |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Dio Brando:** (needs human testing)

### Move List (CONFIRMED)

| Move   | Damage | Type    | Notes                              |
| ------ | ------ | ------- | ---------------------------------- |
| B      | 8      | Impact? | Verified damage from research docs |
| fwd B  |        |         | **Knife throw** (projectile)       |
| up B   |        |         |                                    |
| down B |        |         | **Stand attack** (The World)       |
| air B  |        |         | **Stand attack** (The World)       |
| Y      |        |         |                                    |
| fwd Y  |        |         | **Stand attack** (The World)       |
| up Y   |        |         |                                    |
| down Y |        |         |                                    |
| air Y  |        |         |                                    |

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

### chr_b.bin Entry (Index 29)

| Field        | Value | Notes                        |
| ------------ | ----- | ---------------------------- |
| charId       | 54    | Shared with several chars    |
| formType     |       | 0=Normal, 1=Powered          |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg |
| komaSize     |       | Internal size (not deck koma)|
| classId      | 282   |                              |
| jpower Block | 26    | classId & 0xFF               |

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

### Collision File (jj_b_02.bin)

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

- 37 collision entries (same as Jotaro)
- Includes Stand (The World) attack entries
- damageFlags field does NOT represent actual damage values

### jpower Block 26 Analysis

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

| Archive          | Size | Purpose         |
| ---------------- | ---- | --------------- |
| jj_b_02c.aar     |      | Main sprites    |
| jj_b_02_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 29       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** STANDARD (confirmed in Research-Status.md)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: Standard (matches Goku, Gon, Momotaro)
- Walk speed: (needs testing)
- Comparison to reference characters: Standard weight confirmed

### Movement

| Property      | Value        | Notes                                              |
| ------------- | ------------ | -------------------------------------------------- |
| Walk Speed    |              | Slow / Normal / Fast                               |
| Dash Type     | **FLASH**    | **CONFIRMED** - Character vanishes and reappears   |
| Dash Distance |              |                                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, **Dio**, Gear 2 Luffy)

**CONFIRMED:** Dio is a **flash dasher** as documented in:
- Ichigo-Character-Map.md (line 142)
- Research-Status.md (Flash Dash Mechanics section)

This matches his Stand The World's time-stop abilities thematically.

### Unique Mechanics

- **The World (Stand)** - Performs attacks for Dio on specific moves
- **Stand attacks confirmed:** down B, fwd Y, air B (from Combat-Mechanics.md)
- **Knife throw:** fwd B is a projectile attack
- **Flash dash:** Unique movement style

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
| jj_b_02-001| Available koma sizes          | P2       | PENDING   |        |
| jj_b_02-002| Verify B=8 damage             | P2       | PENDING   |        |
| jj_b_02-003| Full moveset damage values    | P2       | PENDING   |        |
| jj_b_02-004| Knife throw (fwd B) mechanics | P2       | PENDING   |        |
| jj_b_02-005| Stand attack identification   | P2       | PENDING   |        |
| jj_b_02-006| Walk speed                    | P2       | PENDING   |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values**
   - [ ] Verify B = 8 damage (from frame-data-hitbox-notes.txt)
   - [ ] fwd B (knife throw) damage
   - [ ] up B damage
   - [ ] down B (Stand attack) damage
   - [ ] air B (Stand attack) damage
   - [ ] Y combo full damage breakdown (per hit)
   - [ ] fwd Y (Stand attack) damage
   - [ ] up Y / down Y damage
   - [ ] All X move damage at each koma size

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast, Franky=slow)
   - [x] Dash type = **FLASH** (confirmed in research docs)
   - [x] Weight = **STANDARD** (confirmed in research docs)

3. **Unique Mechanics**
   - [ ] Verify Stand attacks on down B, fwd Y, air B
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact tier value in chr_b.bin
2. battleParams byte values
3. All collision file entry details
4. Stand attack damage type (Impact?)

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Walk speed storage location

### Open Questions

1. Do Stand attacks deal different damage type than personal attacks?
2. How is knife throw projectile defined in collision/shot files?
3. Any time stop mechanics in specials (ZA WARUDO)?

---

## Related Characters

| Character    | chr_b Index | Collision File | Relationship        |
| ------------ | ----------- | -------------- | ------------------- |
| Jotaro Kujo  | 28          | jj_b_01.bin    | Same series, rival  |

**Characters sharing charId 54:**

- Gotenks SSJ
- Frieza
- Kakashi
- **Dio**
- Train
- Kazuki

**Characters sharing jpower Block 26:**

- jj_b_02 (Dio Brando) - only character on this block

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
- [Combat-Mechanics.md](../research/Combat-Mechanics.md) - Stand attack documentation

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- Dio is the main antagonist of JoJo Part 1 and Part 3
- **Flash dasher** - confirmed unique movement style
- **Stand user** with The World - attacks via down B, fwd Y, air B
- **Knife throw** projectile on fwd B
- B damage = 8 (from frame-data-hitbox-notes.txt, collision damageFlags=10)
- charId 54 shared with diverse group including Frieza and Kakashi
- Standard weight confirmed in research docs
