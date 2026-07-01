# Gold Seiya (ss_b_02) - Complete Character Mapping

Deep dive analysis mapping Gold Seiya through all data files to understand linkages.

---

## Basic Info

| Field           | Value                           |
| --------------- | ------------------------------- |
| Character Name  | Gold Seiya (Sagittarius Seiya)  |
| Series          | Saint Seiya                     |
| chr_b Index     | 64                              |
| Collision File  | ss_b_02.bin                     |
| charId          | 13                              |
| tier            | 2 (assumed)                     |
| jpower Block    | 150                             |
| classId         | 662                             |

---

## In-Game Verified Data

### Koma Sizes (PENDING)

- **Gold Seiya:** TBD koma

### Move List (PENDING)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        |            |                       |
| fwd B  |        |            |                       |
| up B   |        |            |                       |
| down B |        |            |                       |
| air B  |        |            |                       |
| Y      |        |            |                       |
| fwd Y  |        |            |                       |
| up Y   |        |            |                       |
| down Y |        |            |                       |
| air Y  |        |            |                       |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks (expected for Cosmo-based attacks)
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 64)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 13    | Shared with Seiya, Kenshiro, Raoh, Jotaro, others |
| formType     | 1     | Powered (likely - Gold Cloth form) |
| tier         | 2     | Assumed - no modifier          |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 662   | Low byte = 150 (same as Seiya) |
| jpower Block | 150   | classId & 0xFF                 |

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

Profile: TBD
```

### Collision File (ss_b_02.bin)

| Property    | Value            |
| ----------- | ---------------- |
| Size        | TBD bytes        |
| Entry Count | TBD              |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 150 Analysis

**IMPORTANT:** Gold Seiya and Seiya SHARE the same jpower Block 150 and classId 662.

This is the same pattern as:
- Goku/Goku SSJ (Block 0, classId 256)
- Don Patch/Super Patch (Block 70, classId 582)

Shared block + classId typically indicates shared or nearly identical movesets.

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

| Archive           | Size | Purpose         |
| ----------------- | ---- | --------------- |
| ss_b_02c.aar      |      | Main sprites    |
| ss_b_02_Xc.aar    |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 64       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** STANDARD (assumed)

**Observations:**

- Displacement velocity: TBD
- Walk speed: TBD
- Comparison to reference characters: TBD

### Movement

| Property      | Value    | Notes                    |
| ------------- | -------- | ------------------------ |
| Walk Speed    | TBD      | Slow / Normal / Fast     |
| Dash Type     | TBD      | Standard / Flash         |
| Dash Distance | TBD      |                          |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

Gold Seiya represents Seiya wearing the Sagittarius Gold Cloth, a significant power-up in Saint Seiya. As a powered form of Seiya, he likely shares the base moveset but may have:
- Different tier value (affecting damage)
- Different specials (X moves)
- Higher koma sizes available
- Stat boosts reflected in battleParams

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID    | Test Description                          | Priority | Status    | Result |
| ---------- | ----------------------------------------- | -------- | --------- | ------ |
| ss_b_02-001 | Verify all B move damage values           | P2       | PENDING   |        |
| ss_b_02-002 | Verify all Y move damage values           | P2       | PENDING   |        |
| ss_b_02-003 | Verify X move damage at each koma size    | P2       | PENDING   |        |
| ss_b_02-004 | Compare moveset to base Seiya             | P1       | PENDING   |        |
| ss_b_02-005 | Verify if tier differs from Seiya         | P1       | PENDING   |        |

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

3. **Comparison to Base Seiya**
   - [ ] Document ANY differences in moves, damage, or properties
   - [ ] Test if damage values differ (would indicate tier difference)
   - [ ] Compare X move effects and damage

---

## Unknown / Needs Research

### Unverified Data

1. Actual tier value (if different from Seiya, explains damage differences)
2. formType value (likely 1 for Powered)
3. Whether movesets are truly identical or have differences

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Gold Seiya have the same or different damage values as base Seiya?
2. If different damage, is it due to tier value difference?
3. Are there any unique moves or properties for Gold Seiya?

---

## Related Characters

| Character  | chr_b Index | Collision File | Relationship                              |
| ---------- | ----------- | -------------- | ----------------------------------------- |
| Seiya      | 63          | ss_b_01.bin    | Same jpower block (150), base form        |
| Kenshiro   | 61          | hk_b_01.bin    | Same charId (13), different series        |
| Raoh       | 62          | hk_b_02.bin    | Same charId (13), different series        |

**Characters sharing charId=13:**

- Kyuubi Naruto, Sakura, Jotaro, Kenshiro, Raoh, Seiya, Gold Seiya

**Characters sharing jpower Block 150:**

- ss_b_01 (Seiya) - chr_b[63], classId=662
- ss_b_02 (Gold Seiya) - chr_b[64], classId=662

**Comparison to similar character pairs:**

| Base      | Powered        | Block  | classId | Same Moveset?         |
| --------- | -------------- | ------ | ------- | --------------------- |
| Goku      | Goku SSJ       | 0      | 256     | Yes (confirmed)       |
| Ichigo    | Bankai Ichigo  | 52     | 564     | No (different moves)  |
| Don Patch | Super Patch    | 70     | 582     | Yes (confirmed)       |
| Seiya     | Gold Seiya     | 150    | 662     | TBD (likely yes)      |

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

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- Gold Seiya and Seiya share identical jpower Block 150 and classId 662
- This pattern (same block + classId) typically indicates shared movesets
- Similar to Goku/Goku SSJ and Don Patch/Super Patch relationships
- Gold Seiya represents the Sagittarius Gold Cloth power-up from Saint Seiya
- charId=13 is shared with multiple characters including Kenshiro and Raoh
- Testing needed to confirm if movesets are truly identical or have differences
