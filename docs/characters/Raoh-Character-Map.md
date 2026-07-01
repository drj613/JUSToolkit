# Raoh (hk_b_02) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Raoh through all data files to understand linkages.

---

## Basic Info

| Field           | Value                    |
| --------------- | ------------------------ |
| Character Name  | Raoh                     |
| Series          | Hokuto no Ken            |
| chr_b Index     | 62                       |
| Collision File  | hk_b_02.bin              |
| charId          | 13                       |
| tier            | 2 (assumed)              |
| jpower Block    | 147                      |
| classId         | 403                      |

---

## In-Game Verified Data

### Koma Sizes (PENDING)

- **Raoh:** TBD koma (likely 6, 7, 8 based on sprite archives hk_b_02_6c/7c/8c.aar)

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
- **Punch/Kick** - Physical attacks (expected for Raoh's Hokuto Shinken style)
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 62)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 13    | Shared with Kenshiro, Seiya, Gold Seiya, Jotaro, others |
| formType     | 0     | Normal (assumed)               |
| tier         | 2     | Assumed - no modifier          |
| komaSize     | 6     | Based on sprite archives       |
| classId      | 403   | Low byte = 147                 |
| jpower Block | 147   | classId & 0xFF                 |

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

### Collision File (hk_b_02.bin)

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

### jpower Block 147 Analysis

**Note:** Raoh uses jpower Block 147, distinct from Kenshiro (Block 146).

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
| hk_b_02c.aar      |      | Main sprites    |
| hk_b_02_6c.aar    |      | 6-koma portrait |
| hk_b_02_7c.aar    |      | 7-koma portrait |
| hk_b_02_8c.aar    |      | 8-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 62       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** HEAVY (documented in research docs)

Raoh is documented as a HEAVY weight character, similar to Franky and Edajima.

**Observations:**

- Displacement velocity: Expected to be LOW (heavy characters have reduced knockback displacement)
- Walk speed: Expected to be SLOW
- Comparison to reference characters: Similar to Franky (heavy, slow)

### Movement

| Property      | Value    | Notes                              |
| ------------- | -------- | ---------------------------------- |
| Walk Speed    | SLOW     | Expected based on HEAVY weight     |
| Dash Type     | TBD      | Standard / Flash                   |
| Dash Distance | TBD      |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

Raoh is the main antagonist of Hokuto no Ken, using the same Hokuto Shinken style as Kenshiro but with a more aggressive and powerful approach. As a HEAVY character, he likely trades speed for power and knockback resistance.

Known HEAVY characters from research:
- Raoh
- Edajima
- Franky

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
| hk_b_02-001 | Verify all B move damage values           | P2       | PENDING   |        |
| hk_b_02-002 | Verify all Y move damage values           | P2       | PENDING   |        |
| hk_b_02-003 | Verify X move damage at each koma size    | P2       | PENDING   |        |
| hk_b_02-004 | Confirm HEAVY weight classification       | P1       | PENDING   |        |
| hk_b_02-005 | Compare displacement to Franky/Edajima    | P2       | PENDING   |        |

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
   - [ ] **Weight verification** - compare knockback received to Franky (known HEAVY)
   - [ ] Displacement velocity comparison to Kenshiro

3. **Unique Mechanics**
   - [ ] Any buffs or special states
   - [ ] Damage type verification (use Slash Defense / Impact Defense passives)

---

## Unknown / Needs Research

### Unverified Data

1. Actual tier value (assumed tier=2)
2. Exact weight value/category in game files
3. Walk speed comparison to other HEAVY characters

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] **Weight storage location in files** (NOT in chr_b.bin battleParams)
- [ ] Walk speed storage location

### Open Questions

1. Where is HEAVY weight actually stored in the game files?
2. Does Raoh have higher damage output than Kenshiro as a trade-off for speed?
3. Are all HEAVY characters (Raoh, Edajima, Franky) stored the same way?

---

## Related Characters

| Character  | chr_b Index | Collision File | Relationship                              |
| ---------- | ----------- | -------------- | ----------------------------------------- |
| Kenshiro   | 61          | hk_b_01.bin    | Same series, different jpower block (146) |
| Franky     | 19          | op_b_08.bin    | Same weight class (HEAVY)                 |
| Edajima    | 67          | oj_b_02.bin    | Same weight class (HEAVY)                 |

**Characters sharing charId=13:**

- Kyuubi Naruto, Sakura, Jotaro, Kenshiro, Raoh, Seiya, Gold Seiya

**Characters sharing jpower Block 147:**

- hk_b_02 (Raoh) - chr_b[62], classId=403

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

- **Raoh is documented as HEAVY weight** in research docs
- HEAVY weight characters have:
  - Lower displacement velocity (harder to knock back)
  - Slower walk speed
  - Potentially higher damage or different stat profile
- Raoh and Kenshiro are the two Hokuto no Ken representatives
- Both share charId=13 but have different jpower blocks (147 vs 146)
- Weight storage location is unknown (NOT in chr_b.bin battleParams)
- Sprite archives suggest 6, 7, 8 koma sizes available
