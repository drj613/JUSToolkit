# Monkey D. Luffy (op_b_01) - Complete Character Mapping

Deep dive analysis mapping Luffy through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Monkey D. Luffy        |
| Series          | One Piece              |
| chr_b Index     | 12                     |
| Collision File  | op_b_01.bin            |
| charId          | 9                      |
| tier            | 2 (assumed)            |
| jpower Block    | 9                      |
| classId         | 521                    |

---

## In-Game Verified Data

### Koma Sizes (NEEDS VERIFICATION)

- **Luffy:** 4, 5, 6 koma (based on file analysis)

### Move List (NEEDS HUMAN TESTING)

| Move   | Damage | Type       | Notes                        |
| ------ | ------ | ---------- | ---------------------------- |
| B      | **8**  | Punch/Kick | Stretching attack (verified 2026-01-30) |
| fwd B  |        | Punch/Kick | Gomu Gomu no Pistol          |
| up B   |        | Punch/Kick |                              |
| down B |        | Punch/Kick |                              |
| air B  |        | Punch/Kick |                              |
| Y      |        | Punch/Kick | Combo                        |
| fwd Y  |        | Punch/Kick |                              |
| up Y   |        | Punch/Kick |                              |
| down Y |        | Punch/Kick |                              |
| air Y  |        | Punch/Kick |                              |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks (likely Luffy's main type)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
| 4    |          |         |             |            |
| 5    |          |         |             |            |
| 6    |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 12)

| Field        | Value  | Notes                          |
| ------------ | ------ | ------------------------------ |
| charId       | 9      | Stat template shared with Robin |
| formType     | 0      | Normal (not powered-up form)   |
| tier         | 2      | Standard damage (+0 modifier)  |
| komaSize     |        | Internal size (not deck koma)  |
| classId      | 521    | Low byte = jpower block index  |
| jpower Block | 9      | classId & 0xFF                 |

### battleParams (12 bytes)

```
Raw: [NEEDS EXTRACTION]

Parsed:
  Slot 0: value=?, flags=0x??
  Slot 1: value=?, flags=0x??
  Slot 2: value=?, flags=0x??
  Slot 3: value=?, flags=0x??

Stats [8,9,10]: [?, ?, ?] = ? total
  Attack weight:  ?
  Defense weight: ?
  Speed/Utility:  ?

Byte 11: ? (special flag)

Profile: UNKNOWN
```

### Collision File (op_b_01.bin)

| Property    | Value             |
| ----------- | ----------------- |
| Size        |                   |
| Entry Count | 38                |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- 21 type5 entries (stretching attacks) - unique mechanic for Luffy
- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 9 Analysis

**Block 9 contents (shared with Robin):**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
| 0     |           | ?   | ?   | ?   | 57    | 11 (with /5+tier) |       |
| 1-9   |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 10    |           | ?   | ?   | ?   | 14    | ~3                |       |

**Block 9 Damage totals:** [57, 7, 7, 7, 7, 7, 7, 7, 7, 7, 14]

**IMPORTANT:** Luffy and Robin share this jpower block but have DIFFERENT movesets!
- Luffy: Stretching rubber attacks
- Robin: Arm-spawning attacks

This proves jpower blocks are **template libraries**, not 1:1 movesets.

**Damage Formula:**

```
base_damage = (jpower_total / 5) + (tier - 2)
```

- tier 1: -1 modifier
- tier 2: no modifier
- tier 3: +1 modifier

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| op_b_01c.aar         |      | Main sprites    |
| op_b_01_4c.aar       |      | 4-koma portrait |
| op_b_01_5c.aar       |      | 5-koma portrait |
| op_b_01_6c.aar       |      | 6-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character      |
| -------- | ------------------------------------- | ------------------- |
| 0x0924B0 | Collision file pointer table          | Index 12            |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 12            |
| 0x09E780 | Koma name table                       |                     |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed)

**Observations:**

- Displacement velocity: Unknown
- Walk speed: Unknown
- Comparison to reference characters: Needs testing vs Goku

### Movement

| Property      | Value          | Notes                              |
| ------------- | -------------- | ---------------------------------- |
| Walk Speed    | Unknown        | Slow / Normal / Fast               |
| Dash Type     | Standard       | Standard / Flash                   |
| Dash Distance |                |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**Rubber Stretching:**
- Luffy has 21 type5 collision entries representing stretching attacks
- Arms/legs extend beyond normal character hitbox range
- Likely grants superior range on many attacks

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                          | Priority | Status    | Result |
| ----------- | ----------------------------------------- | -------- | --------- | ------ |
| op_b_01-001 | Full B move damage values (neutral)       | P2       | PENDING   |        |
| op_b_01-002 | Full Y combo damage breakdown             | P2       | PENDING   |        |
| op_b_01-003 | Special (X) damage at each koma size      | P2       | PENDING   |        |
| op_b_01-004 | Walk speed comparison vs Goku             | P2       | PENDING   |        |
| op_b_01-005 | Weight/displacement comparison vs Goku    | P2       | PENDING   |        |
| op_b_01-006 | Damage type verification (slash/impact)   | P2       | PENDING   |        |

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
   - [ ] Stretching attack range comparison

---

## Unknown / Needs Research

### Unverified Data

1. Exact damage values for all moves
2. battleParams byte values
3. Koma size confirmation

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. How does Luffy select specific entries from jpower Block 9 that differ from Robin's selection?
2. Do the 21 type5 collision entries (stretching) have unique damage calculations?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship                      |
| ----------------- | ----------- | -------------- | --------------------------------- |
| Gear 2 Luffy      | 13          | op_b_02        | Powered form, different moveset   |
| Robin             | 18          | op_b_07        | Shares jpower Block 9 and charId  |

**Characters sharing jpower Block 9:**

- op_b_01 (Luffy) - Stretching attacks
- op_b_07 (Robin) - Arm spawning attacks

**Characters sharing charId 9:**

- Luffy (chr_b[12])
- Robin (chr_b[18])

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                               |
| -------- | -------------------------------------- |
| 0x0924B0 | Collision file pointer table           |
| 0x08D4A0 | chr_b -> collision identity mapping    |
| 0x09E780 | Koma name table                        |

### Related Documentation

- [chr_b-Complete-Mapping.md](../research/chr_b-Complete-Mapping.md)
- [jpower-Mapping.md](../research/jpower-Mapping.md)
- [Character-Mapping.md](../research/Character-Mapping.md)

---

## Session Log

| Date       | Session | Verified | Notes                                |
| ---------- | ------- | -------- | ------------------------------------ |
| 2026-01-29 | Initial | No       | Created from research docs, untested |

---

## Notes

- Luffy is the main protagonist of One Piece
- His rubber body grants extended range on attacks
- Shares jpower Block 9 with Robin despite completely different fighting styles
- This character demonstrates that jpower blocks are template libraries, not complete movesets
