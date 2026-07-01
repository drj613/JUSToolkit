# Gear 2 Luffy (op_b_02) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Gear 2 Luffy through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Gear 2 Luffy           |
| Series          | One Piece              |
| chr_b Index     | 13                     |
| Collision File  | op_b_02.bin            |
| charId          | 14                     |
| tier            | 2 (assumed)            |
| jpower Block    | 10                     |
| classId         | 522                    |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED from file analysis)

- **Gear 2 Luffy:** 7, 8 koma (powered-up form, higher koma requirement)

### Move List (NEEDS HUMAN TESTING)

| Move   | Damage | Type       | Notes                                   |
| ------ | ------ | ---------- | --------------------------------------- |
| B      |        | Punch/Kick | Jet Pistol - faster version             |
| fwd B  |        | Punch/Kick | Jet attack                              |
| up B   |        | Punch/Kick | Jet attack                              |
| down B |        | Punch/Kick | Jet attack                              |
| air B  |        | Punch/Kick | Aerial jet attack                       |
| Y      |        | Punch/Kick | Jet combo                               |
| fwd Y  |        | Punch/Kick | Jet attack                              |
| up Y   |        | Punch/Kick | Jet attack                              |
| down Y |        | Punch/Kick | Jet attack                              |
| air Y  |        | Punch/Kick | Aerial jet attack                       |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks (Gear 2's main type)

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
| 7    |          |         |             |            |
| 8    |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 13)

| Field        | Value  | Notes                                     |
| ------------ | ------ | ----------------------------------------- |
| charId       | 14     | Shared with Bo-bobo, Kinnikuman, etc.     |
| formType     | 1      | Powered-up form (Gear 2 is enhanced)      |
| tier         | 2      | Standard damage (+0 modifier) - assumed   |
| komaSize     |        | Internal size (not deck koma)             |
| classId      | 522    | Low byte = jpower block index             |
| jpower Block | 10     | classId & 0xFF                            |

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

Profile: UNKNOWN (likely offensive due to powered form)
```

### Collision File (op_b_02.bin)

| Property    | Value             |
| ----------- | ----------------- |
| Size        |                   |
| Entry Count | 28                |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- 11 type4 entries (jet attacks/projectiles) - unique to Gear 2
- Different moveset from base Luffy despite being same character
- damageFlags field does NOT represent actual damage values

### jpower Block 10 Analysis

**Block 10 contents:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
| 0     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 1     |           | ?   | ?   | ?   | 7     | ~1-2              |       |
| 2     |           | ?   | ?   | ?   | 7     | ~1-2              |       |

**Block 10 Damage totals:** [7, 7, 7]

**Note:** Only 3 entries in Block 10. This suggests:
1. Most damage comes from collision files directly
2. The block is a minimal template
3. Selection mechanism accesses other entries somehow

**Damage Formula:**

```
base_damage = floor(jpower.damage1 / 5) + (tier - 2)
```

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| op_b_02c.aar         |      | Main sprites    |
| op_b_02_7c.aar       |      | 7-koma portrait |
| op_b_02_8c.aar       |      | 8-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character      |
| -------- | ------------------------------------- | ------------------- |
| 0x0924B0 | Collision file pointer table          | Index 13            |
| 0x08D4A0 | chr_b -> collision identity mapping   | Entry 13            |
| 0x09E780 | Koma name table                       |                     |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed)

**Observations:**

- Displacement velocity: Unknown
- Walk speed: Unknown, but Gear 2 is canonically faster
- Comparison to reference characters: Needs testing

### Movement

| Property      | Value          | Notes                                  |
| ------------- | -------------- | -------------------------------------- |
| Walk Speed    | Unknown        | Likely faster than base Luffy          |
| Dash Type     | **Flash**      | Confirmed flash dasher (like Ichigo)   |
| Dash Distance |                |                                        |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, **Gear 2 Luffy**)

**CONFIRMED:** Gear 2 Luffy uses flash dash (documented in Ichigo research).

### Unique Mechanics

**Gear Second (Second Gear):**
- Powered-up form of base Luffy
- Uses blood pump acceleration technique from the anime/manga
- Grants faster movement and attacks
- 11 type4 collision entries suggest jet/speed-based attacks
- Flash dash matches the "Gear 2 speed" theme

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
| op_b_02-001 | Full B move damage values (neutral)       | P2       | PENDING   |        |
| op_b_02-002 | Full Y combo damage breakdown             | P2       | PENDING   |        |
| op_b_02-003 | Special (X) damage at each koma size      | P2       | PENDING   |        |
| op_b_02-004 | Walk speed comparison vs Goku/base Luffy  | P2       | PENDING   |        |
| op_b_02-005 | Weight comparison vs Goku                 | P2       | PENDING   |        |
| op_b_02-006 | Confirm flash dash type                   | P3       | PENDING   |        |

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
   - [ ] All X move damage at 7-koma and 8-koma

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast)
   - [ ] Confirm flash dash type
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Speed comparison vs base Luffy
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Exact damage values for all moves
2. battleParams byte values
3. Whether Gear 2 inherits any stats from base Luffy

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Is Gear 2's speed increase reflected in walk speed data somewhere?
2. Why does Block 10 only have 3 entries when Gear 2 has 28 collision entries?
3. Does the type4 (jet) mechanic affect damage calculation?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship                      |
| ----------------- | ----------- | -------------- | --------------------------------- |
| Luffy (Base)      | 12          | op_b_01        | Base form, different moveset      |

**Characters sharing charId 14:**

- Gear 2 Luffy (chr_b[13])
- Bo-bobo (chr_b[47])
- Shinsetsu Bo-bobo (chr_b[48])
- Don Patch (chr_b[49])
- Super Patch (chr_b[50])
- Kinnikuman (chr_b[65])

**Note:** These characters share stat templates but have completely different movesets.

**Characters sharing jpower Block 10:**

- op_b_02 (Gear 2 Luffy) only

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
| 2026-01-29 | Initial | Partial  | Created from research docs           |

---

## Notes

- Gear 2 (Gear Second) is Luffy's first power-up technique
- Requires higher koma investment (7-8) compared to base Luffy (4-6)
- Uses flash dash like Ichigo and Dio - matches thematic "speed boost"
- Has completely different moveset from base Luffy (28 vs 38 collision entries)
- 11 type4 entries suggest jet/projectile-style attacks unique to this form
- formType=1 indicates this is a powered-up character variant
