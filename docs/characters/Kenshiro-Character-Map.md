# Kenshiro (hk_b_01) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Kenshiro through all data files to understand linkages.

---

## Basic Info

| Field           | Value                    |
| --------------- | ------------------------ |
| Character Name  | Kenshiro                 |
| Series          | Hokuto no Ken            |
| chr_b Index     | 61                       |
| Collision File  | hk_b_01.bin              |
| charId          | 13                       |
| tier            | 2 (assumed)              |
| jpower Block    | 146                      |
| classId         | 658                      |

---

## In-Game Verified Data

### Koma Sizes (PENDING)

- **Kenshiro:** TBD koma

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
- **Punch/Kick** - Physical attacks (expected for Kenshiro's Hokuto Shinken style)
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 61)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 13    | Shared with Raoh, Seiya, Gold Seiya, Jotaro, others |
| formType     | 0     | Normal (assumed)               |
| tier         | 2     | Assumed - no modifier          |
| komaSize     | TBD   | Internal size (not deck koma)  |
| classId      | 658   | Low byte = 146                 |
| jpower Block | 146   | classId & 0xFF                 |

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

### Collision File (hk_b_01.bin)

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

### jpower Block 146 Analysis

**Note:** Kenshiro uses jpower Block 146, distinct from Raoh (Block 147).

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
| hk_b_01c.aar      |      | Main sprites    |
| hk_b_01_Xc.aar    |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 61       |
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

Kenshiro is the protagonist of Hokuto no Ken, using the Hokuto Shinken martial art style. His attacks are primarily punch/kick based with pressure point techniques that cause delayed explosive damage in the source material.

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
| hk_b_01-001 | Verify all B move damage values         | P2       | PENDING   |        |
| hk_b_01-002 | Verify all Y move damage values         | P2       | PENDING   |        |
| hk_b_01-003 | Verify X move damage at each koma size  | P2       | PENDING   |        |
| hk_b_01-004 | Compare weight/speed to Raoh            | P2       | PENDING   |        |

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

---

## Unknown / Needs Research

### Unverified Data

1. Actual tier value (assumed tier=2)
2. Damage types for each move
3. Movement characteristics compared to Raoh

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Kenshiro have any unique pressure point or delayed damage mechanics?
2. How does his playstyle differ from Raoh mechanically?
3. Is charId=13 significant for stat templates?

---

## Related Characters

| Character  | chr_b Index | Collision File | Relationship                              |
| ---------- | ----------- | -------------- | ----------------------------------------- |
| Raoh       | 62          | hk_b_02.bin    | Same series, different jpower block (147) |
| Seiya      | 63          | ss_b_01.bin    | Same charId (13), different series        |
| Gold Seiya | 64          | ss_b_02.bin    | Same charId (13), different series        |
| Jotaro     | 28          | jj_b_01.bin    | Same charId (13), different series        |

**Characters sharing charId=13:**

- Kyuubi Naruto, Sakura, Jotaro, Kenshiro, Raoh, Seiya, Gold Seiya

**Characters sharing jpower Block 146:**

- hk_b_01 (Kenshiro) - chr_b[61], classId=658

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

- Kenshiro and Raoh are the two Hokuto no Ken representatives in the game
- Both share charId=13 but have different jpower blocks (146 vs 147)
- Kenshiro uses Hokuto Shinken, a martial art focused on pressure point attacks
- Expected damage type is primarily Punch/Kick or Impact
