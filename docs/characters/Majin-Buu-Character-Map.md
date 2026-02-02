# Majin Buu (db_b_12) - Complete Character Mapping

Deep dive analysis mapping Majin Buu through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Majin Buu              |
| Series          | Dragon Ball            |
| chr_b Index     | 11                     |
| Collision File  | db_b_12.bin            |
| charId          | 7                      |
| tier            | 2                      |
| jpower Block    | 0                      |
| classId         | 256                    |

---

## CRITICAL FINDING: The jpower Block 0 Paradox

**Majin Buu shares jpower Block 0 with Goku and Goku SSJ, but has a COMPLETELY
DIFFERENT MOVESET!**

This is one of the most important discoveries for understanding how the game's
damage system works.

### Block 0 Characters

| Character   | chr_b Index | classId | jpower Block | Moveset            |
| ----------- | ----------- | ------- | ------------ | ------------------ |
| Goku        | 0           | 256     | 0            | Kamehameha, kicks  |
| Goku SSJ    | 1           | 256     | 0            | Same as Goku       |
| Majin Buu   | 11          | 256     | 0            | Stretchy, candy    |

### What This Proves

1. **jpower blocks are TEMPLATE LIBRARIES, not movesets**
   - Multiple characters can share a block
   - Each character selects which entries to use via unknown mechanism

2. **Entry selection is NOT based on classId alone**
   - All three characters have classId=256
   - But Majin Buu uses different entries than Goku

3. **Selection mechanism candidates:**
   - Collision file subType field
   - Collision file type2 field
   - Collision file linkCategory field
   - Character-specific logic in game code
   - Another mapping table we haven't found

### Research Priority

Testing Majin Buu's damage values and comparing to Goku's jpower Block 0 entries
will help solve the entry selection mystery. This is **HIGH PRIORITY** research.

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Majin Buu:** (needs human testing) koma

### Move List (VERIFIED 2026-02-02)

| Move   | Damage | d1 | Type       | Notes                      |
| ------ | ------ | -- | ---------- | -------------------------- |
| B      | 9      | 45 | Punch/Kick | Single jab down/forward |
| fwd B  | 9      | 45 | Punch/Kick | Extends head tentacle forward, whips it |
| up B   | 9      | 45 | Punch/Kick | Kicks upward, launches opponent |
| down B | 9      | 45 | Punch/Kick | Shout attack - speech bubble deals damage |
| air B  | 9      | 45 | Punch/Kick | Slams hands downward, spikes opponent |
| Y      | 3+3+12 | 15,15,60 | Punch/Kick | Punch, punch, kick - extends limbs |
| fwd Y  | 6×4=24 | 30 | Punch/Kick | Foot stomp, appears ahead, repeatable |
| up Y   | 3+1×7+8=18 | 15,5,40 | Punch/Kick | Detached fist throw upward |
| down Y | 18     | 90 | Punch/Kick | Leans forward, pauses, extends both fists |
| air Y  | 4/tick | 20 | Punch/Kick | Rolling ball spin, potentially infinite |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks (stretchy attacks)
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 11)

| Field        | Value            | Notes                                    |
| ------------ | ---------------- | ---------------------------------------- |
| charId       | 7                | Same as Goku family                      |
| formType     | (needs verify)   | 0=Normal, 1=Powered                      |
| tier         | (needs verify)   | 1=-1 dmg, 2=normal, 3=+1 dmg             |
| komaSize     | (needs verify)   | Internal size (not deck koma)            |
| classId      | 256              | SAME as Goku!                            |
| jpower Block | 0                | SAME as Goku! (classId & 0xFF)           |

### The Goku/Buu Comparison

| Field        | Goku (chr_b[0])  | Majin Buu (chr_b[11]) | Match?    |
| ------------ | ---------------- | --------------------- | --------- |
| charId       | 7                | 7                     | SAME      |
| classId      | 256              | 256                   | SAME      |
| jpower Block | 0                | 0                     | SAME      |
| Moveset      | Kamehameha       | Stretchy/Candy        | DIFFERENT |

This is the core paradox that proves jpower blocks don't directly define movesets.

### battleParams (12 bytes)

```
Raw: [(needs extraction)]

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

Profile: (needs analysis)
```

### Collision File (db_b_12.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | (needs extraction) bytes |
| Entry Count | (needs extraction)       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**IMPORTANT:** Comparing Majin Buu's collision file to Goku's collision file
(especially subType and type2 fields) may reveal how entry selection works.

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 0 Analysis

**Goku's confirmed moves from Block 0:**

| Entry | jpower ID | Total | Goku Move       | Goku Damage |
| ----- | --------- | ----- | --------------- | ----------- |
| 0     | 0         | 50    | fwd B or down B | 7           |
| 1     | 3         | 50    | fwd B or down B | 7           |
| 7     | 21        | 100   | up Y            | 14          |
| 8     | 23        | 100   | down Y          | 14          |

**Question:** Which entries does Majin Buu use, and how does the game select them?

**Hypothesis:** If Majin Buu's B move does 7 damage, he may use the same entries
as Goku with ÷7 formula. If different, there's additional selection logic.

**Damage Formula:**

```
base_damage = (jpower_total / 5) + (tier - 2)   # Confirmed for Ichigo
base_damage = (jpower_total / 5) + (tier - 2)    # Tested - full kit minus specials
```

- tier 1: -1 modifier
- tier 2: no modifier
- tier 3: +1 modifier

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| db_b_12c.aar         |      | Main sprites    |
| db_b_12_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 11                    |
| 0x08D4A0 | chr_b -> collision identity mapping   |                             |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** (needs testing - likely HEAVY)

**Observations:**

- Majin Buu has a large, round body
- Should feel heavier than Goku
- Displacement velocity: (needs comparison to Goku - important!)
- Walk speed: (needs comparison)

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    | (needs testing)    | Likely slower than Goku            |
| Dash Type     | Standard           | Standard dash expected             |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

Majin Buu's signature abilities:
- **Stretchy Body** - Extended reach on punches
- **Candy Beam** - Transforms opponents (likely a special)
- **Regeneration** - May have HP recovery mechanic
- **Absorption** - Possibly manifests as buff/debuff

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID | Test Description | Priority | Status | Result |
| ------- | ---------------- | -------- | ------ | ------ |
| db_b_12-001 | Full moveset damage values | P1 | PENDING | Key to jpower mystery |
| db_b_12-002 | Available koma sizes | P2 | PENDING | |
| db_b_12-003 | Compare B damage to Goku's B (both Block 0) | P0 | PENDING | CRITICAL for entry selection |
| db_b_12-004 | Test if ÷7 or ÷5 formula applies | P1 | PENDING | |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** PENDING | IN PROGRESS | DONE | NOT POSSIBLE

### Specific Tests Needed

1. **Move Damage Values (HIGH PRIORITY)**
   - [ ] B move damage (CRITICAL - compare to Goku's 8)
   - [ ] fwd B damage (compare to Goku's 7)
   - [ ] up B damage (compare to Goku's 3+3)
   - [ ] down B damage (compare to Goku's 7)
   - [ ] Y combo full damage breakdown (compare to Goku's 4+4+6)
   - [ ] fwd Y / up Y / down Y damage (compare to Goku's 5+5+5, 14, 14)
   - [ ] All X move damage at each koma size

2. **Movement/Physics**
   - [ ] Walk speed observation (compare to Goku=standard)
   - [ ] Dash type (standard or flash)
   - [ ] Weight feel (compare knockback received vs Goku)

3. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)
   - [ ] Stretchy body attack reach
   - [ ] Candy beam mechanics

4. **Block 0 Investigation (CRITICAL)**
   - [ ] Does any Buu damage match a Goku damage? (proves shared entry)
   - [ ] Does any Buu damage match jpower total ÷5? (proves formula)
   - [ ] Does any Buu damage match jpower total ÷7? (proves alternative formula)

---

## Unknown / Needs Research

### Unverified Data

1. Tier value in chr_b.bin (affects base damage calculation)
2. formType value (0=Normal or 1=Powered)
3. Collision file entry count and structure
4. How Buu selects different entries from Block 0 than Goku

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. **CRITICAL:** How does Majin Buu select different jpower entries from Block 0 than Goku?
2. Does Buu share ANY damage values with Goku despite different moveset?
3. Is the selection based on collision file fields (subType, type2, linkCategory)?
4. Does Buu use ÷5 formula (like Ichigo) or ÷7 formula (like Goku)?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship              |
| ----------------- | ----------- | -------------- | ------------------------- |
| Goku              | 0           | db_b_01        | SAME jpower Block 0!      |
| Goku SSJ          | 1           | db_b_02        | SAME jpower Block 0!      |
| Luffy             | 12          | op_b_01        | Similar paradox (Block 9 with Robin) |

**Characters sharing jpower Block 0:**

- db_b_01 (Goku)
- db_b_02 (Goku SSJ)
- db_b_12 (Majin Buu) - **DIFFERENT MOVESET**

**Characters sharing charId 7 (stat template):**

- Goku, Goku SSJ, Vegetto, Vegeta, Vegeta SSJ, Gohan SSJ, Gohan SSJ2, Gotenks, Majin Buu

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
- [Goku-Character-Map.md](./Goku-Character-Map.md) - **COMPARE CAREFULLY**

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
| 2026-01-29 | Initial Creation | File data from chr_b-Complete-Mapping.md | High priority testing needed |

---

## Notes

- **KEY PARADOX:** Shares jpower Block 0 with Goku but has DIFFERENT moveset
- This proves jpower blocks are template libraries, not direct moveset definitions
- Testing Majin Buu is HIGH PRIORITY for understanding entry selection
- Comparing collision files between Goku and Buu may reveal selection mechanism
- Part of charId=7 family with Goku - same stat template, different character

## Comparison: Buu vs Goku (Both Block 0)

**VERIFIED 2026-02-02:** Despite sharing jpower Block 0, Buu and Goku have completely different damage values.

| Move   | Goku Damage | Buu Damage | Same? | Notes |
| ------ | ----------- | ---------- | ----- | ----- |
| B      | 8           | 9          | No    | Goku d1=40, Buu d1=45 |
| fwd B  | 7           | 9          | No    | Goku d1=35, Buu d1=45 |
| up B   | 3+3         | 9          | No    | Completely different |
| down B | 7           | 9          | No    | Goku d1=35, Buu d1=45 |
| air B  | ?           | 9          | ?     | |
| Y      | 4+4+6       | 3+3+12     | No    | Different structure |
| fwd Y  | 5+5+5       | 6×4=24     | No    | Different structure |
| up Y   | 14          | 18 (9 hits)| No    | Goku d1=70, Buu multi-hit |
| down Y | 14          | 18         | No    | Goku d1=70, Buu d1=90 |
| air Y  | ?           | 4/tick     | ?     | Buu has unique infinite |

**Conclusion:** Entry selection is per-character, not just per-block. Characters sharing a jpower block use completely different entries from that block.
