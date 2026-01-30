# {{CHARACTER_NAME}} ({{FILE_PREFIX}}) - Complete Character Mapping

Deep dive analysis mapping {{CHARACTER_NAME}} through all data files to understand linkages.

---

## Basic Info

| Field           | Value                  |
| --------------- | ---------------------- |
| Character Name  | {{CHARACTER_NAME}}     |
| Series          | {{SERIES}}             |
| chr_b Index     | {{CHR_B_INDEX}}        |
| Collision File  | {{FILE_PREFIX}}.bin    |
| charId          | {{CHAR_ID}}            |
| tier            | {{TIER}}               |
| jpower Block    | {{JPOWER_BLOCK}}       |
| classId         | {{CLASS_ID}}           |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **{{CHARACTER_NAME}}:** {{KOMA_SIZES}} koma

### Move List (CONFIRMED)

| Move   | Damage | Type       | Notes                 |
| ------ | ------ | ---------- | --------------------- |
| B      |        | {{TYPE}}   |                       |
| fwd B  |        | {{TYPE}}   |                       |
| up B   |        | {{TYPE}}   |                       |
| down B |        | {{TYPE}}   |                       |
| air B  |        | {{TYPE}}   |                       |
| Y      |        | {{TYPE}}   |                       |
| fwd Y  |        | {{TYPE}}   |                       |
| up Y   |        | {{TYPE}}   |                       |
| down Y |        | {{TYPE}}   |                       |
| air Y  |        | {{TYPE}}   |                       |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks
- **??? (Guard Break?)** - Third type immune to both defensive passives

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index {{CHR_B_INDEX}})

| Field        | Value            | Notes                          |
| ------------ | ---------------- | ------------------------------ |
| charId       | {{CHAR_ID}}      |                                |
| formType     | {{FORM_TYPE}}    | 0=Normal, 1=Powered            |
| tier         | {{TIER}}         | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     | {{KOMA_SIZE}}    | Internal size (not deck koma)  |
| classId      | {{CLASS_ID}}     | Low byte = jpower block index  |
| jpower Block | {{JPOWER_BLOCK}} | classId & 0xFF                 |

### battleParams (12 bytes)

```
Raw: [{{BATTLE_PARAMS_RAW}}]

Parsed:
  Slot 0: value={{SLOT0_VAL}}, flags=0x{{SLOT0_FLAGS}}
  Slot 1: value={{SLOT1_VAL}}, flags=0x{{SLOT1_FLAGS}}
  Slot 2: value={{SLOT2_VAL}}, flags=0x{{SLOT2_FLAGS}}
  Slot 3: value={{SLOT3_VAL}}, flags=0x{{SLOT3_FLAGS}}

Stats [8,9,10]: [{{STAT_ATK}}, {{STAT_DEF}}, {{STAT_SPD}}] = {{STAT_TOTAL}} total
  Attack weight:  {{STAT_ATK}}
  Defense weight: {{STAT_DEF}}
  Speed/Utility:  {{STAT_SPD}}

Byte 11: {{BYTE11}} (special flag)

Profile: {{STAT_PROFILE}}
```

### Collision File ({{FILE_PREFIX}}.bin)

| Property    | Value                    |
| ----------- | ------------------------ |
| Size        | {{COL_SIZE}} bytes       |
| Entry Count | {{COL_ENTRIES}}          |
| Location    | ChrBin.aar/chr/col/      |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |
|     |      |         |       |       |        |          |     |      |       |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries

### jpower Block {{JPOWER_BLOCK}} Analysis

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----- |
|       |           |     |     |     |       |                   |       |

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
| {{FILE_PREFIX}}c.aar |      | Main sprites    |
| {{FILE_PREFIX}}_Xc.aar |    | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character              |
| -------- | ------------------------------------- | --------------------------- |
| 0x0924B0 | Collision file pointer table          | Index {{ARM9_COL_INDEX}}    |
| 0x08D4A0 | chr_b -> collision identity mapping   |                             |
| 0x09E780 | Koma name table                       |                             |

---

## Mechanics

### Weight Category

**Category:** {{WEIGHT_CATEGORY}}

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity:
- Walk speed:
- Comparison to reference characters:

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    | {{WALK_SPEED}}     | Slow / Normal / Fast               |
| Dash Type     | {{DASH_TYPE}}      | Standard / Flash                   |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

{{UNIQUE_MECHANICS}}

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## 🚨 Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID | Test Description | Priority | Status | Result |
| ------- | ---------------- | -------- | ------ | ------ |
| {{FILE_PREFIX}}-001 | | P2 | ⏳ PENDING | |
| {{FILE_PREFIX}}-002 | | P2 | ⏳ PENDING | |

**Priority Guide:** P0=Blocking other work, P1=High value, P2=Standard, P3=Nice to have

**Status:** ⏳ PENDING | 🔄 IN PROGRESS | ✅ DONE | ❌ NOT POSSIBLE

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

1. {{UNKNOWN_1}}
2. {{UNKNOWN_2}}
3. {{UNKNOWN_3}}

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Buff multipliers (needs human testing)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. {{QUESTION_1}}
2. {{QUESTION_2}}

---

## Related Characters

| Character         | chr_b Index | Collision File | Relationship           |
| ----------------- | ----------- | -------------- | ---------------------- |
| {{RELATED_CHAR1}} |             |                | {{RELATIONSHIP1}}      |
| {{RELATED_CHAR2}} |             |                | {{RELATIONSHIP2}}      |

**Characters sharing jpower Block {{JPOWER_BLOCK}}:**

-

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

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

{{ADDITIONAL_NOTES}}
