# Toushiro Hitsugaya (bl_b_05) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Toushiro Hitsugaya through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | Toushiro Hitsugaya     |
| Series          | Bleach                 |
| chr_b Index     | 43                     |
| Collision File  | bl_b_05.bin            |
| charId          | 3                      |
| tier            | (needs extraction)     |
| jpower Block    | 65                     |
| classId         | 577                    |

---

## In-Game Verified Data

### Koma Sizes (UNVERIFIED)

- **Hitsugaya:** (needs human verification)

### Move List (UNVERIFIED)

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
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 43)

| Field        | Value            | Notes                          |
| ------------ | ---------------- | ------------------------------ |
| charId       | 3                | Shared with Ichigo, Rukia, Renji, Lenalee |
| formType     | (needs extraction) | 0=Normal, 1=Powered            |
| tier         | (needs extraction) | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     | (needs extraction) | Internal size (not deck koma)  |
| classId      | 577              | Low byte = jpower block index  |
| jpower Block | 65               | classId & 0xFF                 |

### battleParams (12 bytes)

```
Raw: [needs extraction]

Stats [8,9,10]: [?, ?, ?] = ? total
  Attack weight:  ?
  Defense weight: ?
  Speed/Utility:  ?

Byte 11: ? (special flag)

Profile: (needs extraction)
```

### Collision File (bl_b_05.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | (needs extraction)       |
| Entry Count | (needs extraction)       |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block 65 Analysis

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

**Note:** Hitsugaya shares jpower Block 65 with Allen Walker (dg_b_01) and Lenalee Lee (dg_b_02) from D.Gray-man.

### Sprite Archives (chr/)

| Archive              | Size | Purpose         |
| -------------------- | ---- | --------------- |
| bl_b_05c.aar         |      | Main sprites    |
| bl_b_05_Xc.aar       |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index 43                    |
| 0x08D4A0 | chr_b -> collision identity mapping   |                             |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** (UNKNOWN)

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity: (needs testing)
- Walk speed: (needs testing)
- Comparison to reference characters: (needs testing)

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    | (UNKNOWN)          | Slow / Normal / Fast               |
| Dash Type     | (UNKNOWN)          | Standard / Flash                   |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

Hitsugaya is a Shinigami Captain with ice-type Zanpakuto (Hyorinmaru). His fighting style likely features:
- Ice/frost attacks (potential freeze or slow effects)
- Slashing damage from sword attacks
- Potentially ranged ice projectiles

As one of the youngest captains in Soul Society, Hitsugaya may have:
- Lighter weight class
- Faster movement speed

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
| bl_b_05-001 | All koma sizes available | P2 | PENDING | |
| bl_b_05-002 | B move damage (neutral, no buffs) | P2 | PENDING | |
| bl_b_05-003 | Complete moveset damage values | P2 | PENDING | |
| bl_b_05-004 | Damage types (use defensive passives) | P2 | PENDING | |
| bl_b_05-005 | Walk speed (compare to Goku) | P3 | PENDING | |
| bl_b_05-006 | Weight class (compare knockback to Goku) | P3 | PENDING | |
| bl_b_05-007 | Dash type (standard or flash) | P3 | PENDING | |
| bl_b_05-008 | Ice attack effects (freeze? slow?) | P2 | PENDING | |

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
   - [ ] Ice ability effects (freeze? slow? unique damage type?)

---

## Unknown / Needs Research

### Unverified Data

1. Actual tier value from chr_b.bin extraction
2. Complete battleParams byte values
3. Collision file entry count and structure

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Does Hitsugaya have ice-specific mechanics (freeze, slow)?
2. Does he share any moveset properties with Allen/Lenalee (same jpower block)?
3. Does he have a buff/taunt system like Ichigo?
4. Is he lighter/faster than other Bleach characters due to his age/size?

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship           |
| ----------------- | ----------- | -------------- | ---------------------- |
| Ichigo Kurosaki   | 39          | bl_b_01.bin    | Same series, charId=3  |
| Bankai Ichigo     | 40          | bl_b_02.bin    | Same series, charId=3  |
| Rukia Kuchiki     | 41          | bl_b_03.bin    | Same series, charId=3  |
| Renji Abarai      | 42          | bl_b_04.bin    | Same series, charId=3  |
| Allen Walker      | 45          | dg_b_01.bin    | Same jpower block (65) |
| Lenalee Lee       | 46          | dg_b_02.bin    | Same jpower block (65), charId=3 |

**Characters sharing charId=3:**

All Bleach battle characters (Ichigo, Bankai, Rukia, Renji, Hitsugaya) plus Lenalee from D.Gray-man share the same stat template (charId=3).

**Characters sharing jpower Block 65:**

- Toushiro Hitsugaya (bl_b_05) - classId=577
- Allen Walker (dg_b_01) - classId=321
- Lenalee Lee (dg_b_02) - classId=577

All three characters use the same jpower block but likely have DIFFERENT movesets (jpower blocks are template libraries, not 1:1 movesets). Notably, Hitsugaya and Lenalee share the exact same classId (577).

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
- [Ichigo-Character-Map.md](./Ichigo-Character-Map.md)

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
| 2026-01-29 | Initial creation | Data from chr_b mapping | Extracted from research docs |

---

## Notes

- Hitsugaya shares charId=3 with all other Bleach characters, meaning they use the same stat template
- jpower block 65 is shared with Allen Walker and Lenalee Lee from D.Gray-man
- Hitsugaya and Lenalee share the exact same classId (577), which is notable
- As an ice-type sword user, attacks may have both Slashing damage and ice effects
- His small stature in canon may translate to lighter weight or faster movement in-game
