# Caramelman (ds_b_03) - Complete Character Mapping

Deep dive analysis mapping Caramelman through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Caramelman             |
| Series          | Dr. Slump              |
| chr_b Index     | 58                     |
| Collision File  | ds_b_03.bin            |
| charId          | 45                     |
| tier            | 3                      |
| jpower Block    | 105                    |
| classId         | 361                    |

---

## In-Game Verified Data

### Koma Sizes (UNVERIFIED)

- **Caramelman:** 8 koma only (based on sprite archives - only ds_b_03_8c.aar exists)

### Move List (UNVERIFIED)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        |            | Needs testing         |
| fwd B  |        |            | Needs testing         |
| up B   |        |            | Needs testing         |
| down B |        |            | Needs testing         |
| air B  |        |            | Needs testing         |
| Y      |        |            | Needs testing         |
| fwd Y  |        |            | Needs testing         |
| up Y   |        |            | Needs testing         |
| down Y |        |            | Needs testing         |
| air Y  |        |            | Needs testing         |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
| 8    |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 58)

| Field        | Value   | Notes                              |
| ------------ | ------- | ---------------------------------- |
| charId       | 45      | Shared with Mashirito              |
| formType     | 2       | Special/combo character            |
| tier         | 3       | +1 damage modifier (IMPORTANT!)    |
| komaSize     | 4       | Internal size (not deck koma)      |
| classId      | 361     | Low byte = jpower block index      |
| jpower Block | 105     | classId & 0xFF                     |

**IMPORTANT:** Caramelman has tier=3, which means +1 damage modifier if the
standard formula (damage = jpower/5 + tier-2) applies. This is one of only
~7 characters in the game with tier=3.

### battleParams (12 bytes)

```
Raw: [14, 0, 48, 32, 51, 16, 8, 4, 35, 30, 20, 0]

Parsed:
  Slot 0: value=14, flags=0x00
  Slot 1: value=48, flags=0x20
  Slot 2: value=51, flags=0x10
  Slot 3: value=8, flags=0x04

Stats [8,9,10]: [35, 30, 20] = 85 total
  Attack weight:  35
  Defense weight: 30
  Speed/Utility:  20

Byte 11: 0 (no special flag)

Profile: Slightly offense-oriented
```

### Collision File (ds_b_03.bin)

| Property    | Value      |
| ----------- | ---------- |
| Size        | 460 bytes  |
| Entry Count | 23         |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
| 0   | 3    | 1       | 13    | 8     | 0      | 0        | 1   | 1    | Basic attack |
| 5   | 3    | 5       | 9     | 16    | 3      | 1        | 29  | 3    | Knockdown move |
| 9   | 2    | 6       | 10    | 30    | 25     | 1        | 0   | 3    | Large hitbox move |
| 16  | 4    | 6       | 80    | 12    | 30     | 13       | 16  | 3    | X move (high damage) |
| 17  | 5    | 6       | 65    | 30    | 10     | 1        | 0   | 3    | Summon finisher |

**Notes:**

- 23 collision entries total
- Entry 16 has damageFlags=13, one of the higher values seen
- Has Type 5 (Summon) entries like Mashirito
- Large hitbox moves (30x25, 30x10) suggest area attacks
- damageFlags field does NOT represent actual damage values

### jpower Block 105 Analysis

**Note:** jpower block 105 is beyond the standard 88 DATA blocks in jpower.bin.
The jpower entry selection mechanism for Caramelman may work differently or use a
different formula than low-tier characters.

**Status:** jpower entries for this block need further investigation.

### Sprite Archives (chr/)

| Archive          | Size   | Purpose         |
| ---------------- | ------ | --------------- |
| ds_b_03c.aar     | 254KB  | Main sprites    |
| ds_b_03_8c.aar   | 60KB   | 8-koma portrait |

**Note:** Only 8-koma portrait exists, suggesting Caramelman is an 8-koma only
character (high cost, powerful). This is typical for boss/powerful characters.

### ARM9 References

| Offset   | Contents                              | This Character  |
| -------- | ------------------------------------- | --------------- |
| 0x0924B0 | Collision file pointer table          | Index 58        |
| 0x08D4A0 | chr_b -> collision identity mapping   |                 |
| 0x09E780 | Koma name table                       |                 |

---

## Mechanics

### Weight Category

**Category:** LIKELY HEAVY (needs testing)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Large main sprite file (254KB) suggests big character model
- 8-koma only suggests powerful/boss-type character
- Displacement velocity: Needs testing
- Walk speed: Needs testing

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    | LIKELY SLOW        | Big character = usually slow       |
| Dash Type     | UNKNOWN            | Standard / Flash                   |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

Caramelman is one of Dr. Mashirito's robot creations in Dr. Slump. Based on
collision file analysis:

- tier=3 means +1 damage bonus on all attacks
- Type 5 (Summon) entries suggest summon-based attacks
- Large hitboxes (30x25, 30x10) indicate area control
- 8-koma only = high deck cost, powerful character
- Likely a tank/powerhouse character

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                              | Priority | Status    | Result |
| ----------- | --------------------------------------------- | -------- | --------- | ------ |
| ds_b_03-001 | All B move damage values (neutral)            | P2       | PENDING   |        |
| ds_b_03-002 | All Y move damage values (neutral)            | P2       | PENDING   |        |
| ds_b_03-003 | X move damage (8-koma)                        | P2       | PENDING   |        |
| ds_b_03-004 | up X move damage (8-koma)                     | P2       | PENDING   |        |
| ds_b_03-005 | Walk speed comparison (vs Goku standard)      | P2       | PENDING   |        |
| ds_b_03-006 | Dash type (standard vs flash)                 | P2       | PENDING   |        |
| ds_b_03-007 | Weight feel (compare knockback received)      | P2       | PENDING   |        |
| ds_b_03-008 | Damage type verification (use defense passives)| P2      | PENDING   |        |
| ds_b_03-009 | Verify 8-koma only availability               | P1       | PENDING   |        |
| ds_b_03-010 | Tier 3 damage bonus verification              | P1       | PENDING   |        |

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
   - [ ] X move damage at 8-koma

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast, Franky=slow)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Verify tier=3 gives +1 damage (compare to tier=2 character with same jpower)
   - [ ] Summon behavior if any
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

4. **Deck Testing**
   - [ ] Verify only 8-koma is available in deck building
   - [ ] Check if any other sizes are hidden/unlockable

---

## Unknown / Needs Research

### Unverified Data

1. jpower block 105 entry structure (beyond standard DATA block range)
2. Actual damage formula with tier=3 modifier
3. Move damage values and types
4. Whether 8-koma is truly the only option

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] Tier=3 damage formula verification
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Caramelman use the standard damage = jpower/5 + (tier-2) formula?
2. If so, his base damage should be +1 higher than tier=2 characters
3. Why only 8-koma? Is this character locked to high koma?
4. What happens with jpower blocks > 88 (the number of DATA entries)?

---

## Related Characters

| Character     | chr_b Index | Collision File | Relationship           |
| ------------- | ----------- | -------------- | ---------------------- |
| Arale         | 56          | ds_b_01.bin    | Same series (Dr. Slump)|
| Mashirito     | 57          | ds_b_02.bin    | Creator of Caramelman  |

**Characters sharing charId 45:**

- ds_b_02 (Mashirito)
- ds_b_03 (Caramelman) - both share charId 45

**Characters with tier=3:**

Caramelman is one of approximately 7 characters with tier=3 in the entire game.
This makes him valuable for testing the tier damage formula.

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

---

## Session Log

| Date       | Session      | Verified | Notes                              |
| ---------- | ------------ | -------- | ---------------------------------- |
| 2026-01-29 | Initial scan | No       | Extracted file data, no in-game testing |

---

## Notes

- Caramelman is Dr. Mashirito's robot creation from Dr. Slump
- tier=3 is rare and significant - +1 damage on all attacks
- formType=2 suggests special/combo mechanics
- 8-koma only = high cost, powerful character
- Largest main sprite file (254KB) in Dr. Slump cast
- Type 5 (Summon) entries shared with Mashirito
- Useful for testing tier=3 damage formula once jpower entries are mapped
