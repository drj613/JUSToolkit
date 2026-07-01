# Caramelman (ds_b_03) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Caramelman through all data files to understand
linkages.

---

## Basic Info

| Field          | Value       |
| -------------- | ----------- |
| Character Name | Caramelman  |
| Series         | Dr. Slump   |
| chr_b Index    | 58          |
| Collision File | ds_b_03.bin |
| charId         | 45          |
| tier           | 3           |
| jpower Block   | 105         |
| classId        | 361         |

---

## In-Game Verified Data

### Koma Sizes (VERIFIED)

- **Caramelman:** 8 koma only (confirmed - alternate form of Dr. Mashirito)

**Character Description:** Caramelman rides in a robotic head (like Dr. Robotnik
from Sonic). He is the 8-koma version of Dr. Mashirito with a completely
different moveset.

### Move List (VERIFIED 2026-02-02)

| Move   | Damage   | d1    | Type       | Notes                                                   |
| ------ | -------- | ----- | ---------- | ------------------------------------------------------- |
| B      | 13       | 60    | Punch/Kick | Robot punches once                                      |
| fwd B  | 5/hit    | 20    | Punch/Kick | Rocket fist extends out and back, hits both ways        |
| up B   | 15       | 70    | Punch/Kick | Bat swing upward, slight knockup                        |
| down B | 10       | 45    | Punch/Kick | Dramatic lick with giant tongue                         |
| air B  | 15+5     | 70,20 | Punch/Kick | Spiked ball wraps around robot; ball=15, body contact=5 |
| Y      | 2×N+9    | 5,40  | Punch/Kick | Drill tank; 4-12 hits of 2 dmg, final hit 9             |
| fwd Y  | 2-3/tick | 5,10  | Energy     | Mouth beam; 3 dmg close, 2 dmg far; max ~22             |
| up Y   | 3×6+10   | 10,45 | Punch/Kick | Tornado, 6 hits of 3 + final 10 with huge knockup       |
| down Y | 20       | 95    | Energy     | Big electrical shock                                    |
| air Y  | 9×3      | 40    | Energy     | Up to 3 homing rockets, 9 each                          |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense
  passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense
  passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes                                         | up X Damage | up X Notes                                                    |
| ---- | -------- | ----------------------------------------------- | ----------- | ------------------------------------------------------------- |
| 8    | 80 + 3   | Laser explosions (80) + small area near him (3) | 65/hit      | Robot grows legs and runs around, damaging anyone in its path |

---

## File Data

### chr_b.bin Entry (Index 58)

| Field        | Value | Notes                           |
| ------------ | ----- | ------------------------------- |
| charId       | 45    | Shared with Mashirito           |
| formType     | 2     | Special/combo character         |
| tier         | 3     | +1 damage modifier (IMPORTANT!) |
| komaSize     | 4     | Internal size (not deck koma)   |
| classId      | 361   | Low byte = jpower block index   |
| jpower Block | 105   | classId & 0xFF                  |

**IMPORTANT:** Caramelman has tier=3, which means +1 damage modifier if the
standard formula (damage = jpower/5 + tier-2) applies. This is one of only ~7
characters in the game with tier=3.

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

| Property    | Value               |
| ----------- | ------------------- |
| Size        | 460 bytes           |
| Entry Count | 23                  |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes                |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | -------------------- |
| 0   | 3    | 1       | 13    | 8     | 0      | 0        | 1   | 1    | Basic attack         |
| 5   | 3    | 5       | 9     | 16    | 3      | 1        | 29  | 3    | Knockdown move       |
| 9   | 2    | 6       | 10    | 30    | 25     | 1        | 0   | 3    | Large hitbox move    |
| 16  | 4    | 6       | 80    | 12    | 30     | 13       | 16  | 3    | X move (high damage) |
| 17  | 5    | 6       | 65    | 30    | 10     | 1        | 0   | 3    | Summon finisher      |

**Notes:**

- 23 collision entries total
- Entry 16 has damageFlags=13, one of the higher values seen
- Has Type 5 (Summon) entries like Mashirito
- Large hitbox moves (30x25, 30x10) suggest area attacks
- damageFlags field does NOT represent actual damage values

### damageFlags Mapping (WIP)

**Source:** `jus_files/exported_combat/ds_b_03_collision.json`

**Non-zero `damageFlags` entries (index in JSON array):**

| idx | dmgFlags | type | subType | frame | dur | offX | offY | width | height |
| --- | -------- | ---- | ------- | ----- | --- | ---- | ---- | ----- | ------ |
| 5   | 1        | 3    | 5       | 9     | 0   | 0    | 0    | 16    | 3      |
| 9   | 1        | 2    | 6       | 10    | 0   | 0    | 0    | 30    | 25     |
| 10  | 2        | 0    | 0       | 0     | 0   | 12   | 0    | 0     | 4      |
| 12  | 13       | 2    | 1       | 9     | 0   | 32   | 2    | 8     | 0      |
| 14  | 14       | 2    | 1       | 20    | 0   | 1    | 0    | 10    | 0      |
| 16  | 13       | 4    | 6       | 80    | 0   | 0    | 4    | 12    | 30     |
| 17  | 1        | 5    | 6       | 65    | 0   | 1    | 10   | 30    | 10     |

**Attempt A — Global jpower index (Ichigo-style):**

| dmgFlags | jpower Index | jpower.id | type1 | d1  | d2  | d3  |
| -------- | ------------ | --------- | ----- | --- | --- | --- |
| 1        | 1            | 3         | 1     | 10  | 40  | 0   |
| 2        | 2            | 6         | 1     | 50  | 0   | 0   |
| 13       | 13           | 29        | 0     | 0   | 0   | 0   |
| 14       | 14           | 30        | 0     | 0   | 0   | 0   |

**Attempt B — Attack-only index (skip type1=0 entries):**

| dmgFlags | Attack Index | global idx | jpower.id | d1  | d2  | d3  |
| -------- | ------------ | ---------- | --------- | --- | --- | --- |
| 1        | 1            | 1          | 3         | 10  | 40  | 0   |
| 2        | 2            | 2          | 6         | 50  | 0   | 0   |
| 13       | 13           | 23         | 47        | 0   | 30  | 20  |
| 14       | 14           | 24         | 50        | 0   | 20  | 30  |

**Observations:**

- `damageFlags=1` → `damage1=10`, which matches Caramelman’s **3 damage ticks**
  (tier=3 → 10/5+1=3). This likely corresponds to beam close-zone or multi-hit
  tick damage (e.g., up Y or drill).
- `damageFlags=2` → `damage1=50` (11 damage at tier=3), which does **not** match
  any observed Caramelman hit. This suggests the lookup is **not** a simple
  array index for all entries.
- `damageFlags=13/14` map to entries with `damage1=0` but non-zero `damage2/3`,
  hinting **energy moves might read damage2/3** or a different lookup path.
- Several observed Caramelman damage components (`d1` = 20, 40, 45, 60, 70, 95)
  do not align with any direct-index mapping, reinforcing that Caramelman is
  **not purely Ichigo-style**.

**Working Hypothesis:**

Caramelman likely uses a hybrid lookup:

1. Some hits use direct indices (e.g., `damageFlags=1` for 3-damage ticks).
2. Other hits use an alternate table or interpret `damage2/3`, possibly gated by
   attack type (Energy vs Punch/Kick) or `formType=2`.

### Special Moves: Collision + Shot Correlation (WIP)

**Observed special damage values (tier=3):**

| Move           | Damage | Required damage1 (if standard formula) |
| -------------- | ------ | -------------------------------------- |
| X (explosion)  | 80     | 395                                    |
| X (near-body)  | 3      | 10                                     |
| up X (run hit) | 65     | 320                                    |

**Collision entries likely tied to X / up X:**

| idx | type | subType | frame | dmgFlags | width | height | Notes                               |
| --- | ---- | ------- | ----- | -------- | ----- | ------ | ----------------------------------- |
| 16  | 4    | 6       | 80    | 13       | 12    | 30     | Projectile-type; likely X explosion |
| 17  | 5    | 6       | 65    | 1        | 30    | 10     | Summon-type; likely up X run hit    |

**Projectile/Summon file:**

- File: `jus_files/extracted_chrbin/ChrBin.aar/chr/shot/ds_b_03.bin`
- Size: 288 bytes (9 records × 32 bytes)

**Notes:**

- Collision entries in `ds_b_03` have `projectileId=0` across the board, so the
  shot record index is **not** directly exposed in collision data.
- The `shot/*.bin` format is 32-byte records (per
  `docs/formats/Combat-Formats.md`), but field meanings remain unknown. This
  blocks direct mapping of shot record → X/up X at the moment.

**Next steps to disambiguate (specials):**

1. Reverse the `shot/*.bin` record layout to identify a per-record damage field.
2. Compare shot records across characters with known projectile damage to locate
   the damage component.
3. Check ARM9 for projectile spawn code that selects a shot record (indexing
   logic).

**Next steps to disambiguate:**

1. Correlate these collision entries to specific move animations and hit timing.
2. Check projectile/summon data (`chr/shot/*.bin`) for related damage
   references.
3. Search ARM9 for a Caramelman-specific lookup path or type-based routing.

### jpower Block 105 Analysis

**Note:** jpower block 105 is beyond the standard 88 DATA blocks in jpower.bin.
The jpower entry selection mechanism for Caramelman may work differently or use
a different formula than low-tier characters.

**Status:** jpower entries for this block need further investigation.

### Sprite Archives (chr/)

| Archive        | Size  | Purpose         |
| -------------- | ----- | --------------- |
| ds_b_03c.aar   | 254KB | Main sprites    |
| ds_b_03_8c.aar | 60KB  | 8-koma portrait |

**Note:** Only 8-koma portrait exists, suggesting Caramelman is an 8-koma only
character (high cost, powerful). This is typical for boss/powerful characters.

### ARM9 References

| Offset   | Contents                            | This Character |
| -------- | ----------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table        | Index 58       |
| 0x08D4A0 | chr_b -> collision identity mapping |                |
| 0x09E780 | Koma name table                     |                |

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

| Property      | Value       | Notes                        |
| ------------- | ----------- | ---------------------------- |
| Walk Speed    | LIKELY SLOW | Big character = usually slow |
| Dash Type     | UNKNOWN     | Standard / Flash             |
| Dash Distance |             |                              |

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

> **AGENTS**: When you need in-game verification, add items here AND to the
> central queue at `docs/research/Human-Testing-Queue.md`. Format:
> `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                                | Priority | Status  | Result |
| ----------- | ----------------------------------------------- | -------- | ------- | ------ |
| ds_b_03-001 | All B move damage values (neutral)              | P2       | PENDING |        |
| ds_b_03-002 | All Y move damage values (neutral)              | P2       | PENDING |        |
| ds_b_03-003 | X move damage (8-koma)                          | P2       | PENDING |        |
| ds_b_03-004 | up X move damage (8-koma)                       | P2       | PENDING |        |
| ds_b_03-005 | Walk speed comparison (vs Goku standard)        | P2       | PENDING |        |
| ds_b_03-006 | Dash type (standard vs flash)                   | P2       | PENDING |        |
| ds_b_03-007 | Weight feel (compare knockback received)        | P2       | PENDING |        |
| ds_b_03-008 | Damage type verification (use defense passives) | P2       | PENDING |        |
| ds_b_03-009 | Verify 8-koma only availability                 | P1       | PENDING |        |
| ds_b_03-010 | Tier 3 damage bonus verification                | P1       | PENDING |        |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice
to have

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
   - [ ] Walk speed observation (compare to Goku=standard, Nami=fast,
         Franky=slow)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Verify tier=3 gives +1 damage (compare to tier=2 character with same
         jpower)
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

| Character | chr_b Index | Collision File | Relationship            |
| --------- | ----------- | -------------- | ----------------------- |
| Arale     | 56          | ds_b_01.bin    | Same series (Dr. Slump) |
| Mashirito | 57          | ds_b_02.bin    | Creator of Caramelman   |

**Characters sharing charId 45:**

- ds_b_02 (Mashirito)
- ds_b_03 (Caramelman) - both share charId 45

**Characters with tier=3:**

Caramelman is one of approximately 7 characters with tier=3 in the entire game.
This makes him valuable for testing the tier damage formula.

---

## References

### ARM9.bin Key Offsets

| Offset   | Contents                            |
| -------- | ----------------------------------- |
| 0x0924B0 | Collision file pointer table        |
| 0x08D4A0 | chr_b -> collision identity mapping |
| 0x09E780 | Koma name table                     |

### Related Documentation

- [chr_b-Mapping.md](../formats/chr_b-Mapping.md)
- [jpower-Analysis.md](../formats/jpower-Analysis.md)
- [Collision-Format.md](../formats/Collision-Format.md)

---

## Session Log

| Date       | Session      | Verified | Notes                                   |
| ---------- | ------------ | -------- | --------------------------------------- |
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
