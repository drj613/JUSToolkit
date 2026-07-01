# Seiya (ss_b_01) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Seiya through all data files to understand linkages.

---

## Basic Info

| Field           | Value                    |
| --------------- | ------------------------ |
| Character Name  | Seiya (Pegasus Seiya)    |
| Series          | Saint Seiya              |
| chr_b Index     | 63                       |
| Collision File  | ss_b_01.bin              |
| charId          | 13                       |
| tier            | 2 (assumed)              |
| jpower Block    | 150                      |
| classId         | 662                      |

---

## In-Game Verified Data

### Koma Sizes (PENDING)

- **Seiya:** TBD koma

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

### chr_b.bin Entry (Index 63)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 13    | Shared with Gold Seiya, Kenshiro, Raoh, Jotaro, others |
| formType     | 0     | Normal (assumed)               |
| tier         | 2     | Assumed - no modifier          |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 662   | Low byte = 150                 |
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

### Collision File (ss_b_01.bin)

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

**IMPORTANT:** Seiya and Gold Seiya SHARE the same jpower Block 150.

This is similar to other character variants (Goku/Goku SSJ sharing Block 0). The shared block may indicate similar movesets with potential variations in stats or specials.

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
| ss_b_01c.aar      |      | Main sprites    |
| ss_b_01_Xc.aar    |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 63       |
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

Seiya is the protagonist of Saint Seiya, using Cosmo energy to power his attacks as a Bronze Saint (Pegasus). His signature move is the Pegasus Ryu Sei Ken (Pegasus Meteor Fist).

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
| ss_b_01-001 | Verify all B move damage values           | P2       | PENDING   |        |
| ss_b_01-002 | Verify all Y move damage values           | P2       | PENDING   |        |
| ss_b_01-003 | Verify X move damage at each koma size    | P2       | PENDING   |        |
| ss_b_01-004 | Compare moveset to Gold Seiya             | P1       | PENDING   |        |

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
   - [ ] Compare all moves to Gold Seiya for differences

---

## Unknown / Needs Research

### Unverified Data

1. Actual tier value (assumed tier=2)
2. Exact differences from Gold Seiya (if moveset is truly identical)
3. Whether Block 150 entries are used differently by each variant

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Do Seiya and Gold Seiya have identical movesets?
2. If same jpower block, what differentiates them mechanically?
3. Are stat differences encoded in tier or battleParams?

---

## Related Characters

| Character  | chr_b Index | Collision File | Relationship                              |
| ---------- | ----------- | -------------- | ----------------------------------------- |
| Gold Seiya | 64          | ss_b_02.bin    | Same jpower block (150), powered variant  |
| Kenshiro   | 61          | hk_b_01.bin    | Same charId (13), different series        |
| Raoh       | 62          | hk_b_02.bin    | Same charId (13), different series        |

**Characters sharing charId=13:**

- Kyuubi Naruto, Sakura, Jotaro, Kenshiro, Raoh, Seiya, Gold Seiya

**Characters sharing jpower Block 150:**

- ss_b_01 (Seiya) - chr_b[63], classId=662
- ss_b_02 (Gold Seiya) - chr_b[64], classId=662

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

- Seiya and Gold Seiya share the same jpower Block 150 and classId 662
- This is similar to Goku/Goku SSJ sharing Block 0 - likely indicates shared or very similar movesets
- charId=13 is shared with Kenshiro, Raoh, and other characters
- Gold Seiya represents Seiya wearing the Gold Cloth (Sagittarius Cloth) power-up
