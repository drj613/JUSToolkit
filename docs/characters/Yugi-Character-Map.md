# Yugi Moto (yo_b_01) - Complete Character Mapping

> **Map status:** PARTIAL — file data (chr_b/collision/jpower IDs) extracted; most move damages and koma data unverified (needs in-game testing).

Deep dive analysis mapping Yugi Moto through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Yugi Moto          |
| Series          | Yu-Gi-Oh!          |
| chr_b Index     | 35                 |
| Collision File  | yo_b_01.bin        |
| charId          | 47                 |
| tier            | (needs extraction) |
| jpower Block    | 47                 |
| classId         | 303                |

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Yugi Moto:** (needs verification) koma

### Move List (CONFIRMED)

| Move   | Damage | Type   | Notes                           |
| ------ | ------ | ------ | ------------------------------- |
| B      |        | Summon | Card-based attacks              |
| fwd B  |        | Summon | Persistent/Trap - remains after switch-out |
| up B   |        | Summon |                                 |
| down B |        | Summon |                                 |
| air B  |        | Summon |                                 |
| Y      |        | Summon |                                 |
| fwd Y  |        | Summon |                                 |
| up Y   |        | Summon |                                 |
| down Y |        | Summon |                                 |
| air Y  |        | Summon |                                 |

**Damage Types:**

- **Slashing** - Blade attacks with distinct SFX (reduced by Slash Defense passive)
- **Impact** - Blunt attacks with distinct SFX (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks
- **Summon** - Separate entities summoned to attack

**Note:** Yugi uses Duel Monsters cards to summon creatures. These are classified as Summons per Research-Status.md.

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 35)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 47    | Shared with Hiei, Muhyo        |
| formType     |       | 0=Normal, 1=Powered            |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     |       | Internal size (not deck koma)  |
| classId      | 303   | Low byte = jpower block index  |
| jpower Block | 47    | classId & 0xFF                 |

### battleParams (12 bytes)

```
Raw: [needs extraction]

Parsed:
  Slot 0: value=, flags=0x
  Slot 1: value=, flags=0x
  Slot 2: value=, flags=0x
  Slot 3: value=, flags=0x

Stats [8,9,10]: [, , ] = total
  Attack weight:
  Defense weight:
  Speed/Utility:

Byte 11: (special flag)

Profile:
```

### Collision File (yo_b_01.bin)

| Property    | Value               |
| ----------- | ------------------- |
| Size        | (needs extraction)  |
| Entry Count | (needs extraction)  |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | Tier | Notes |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ---- | ----- |

**Notes:**

- damageFlags field does NOT represent actual damage values
- May encode modifier type/index or reference to jpower.bin entries
- Expect Type 5 (Summon) entries for card summons

### jpower Block 47 Analysis

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

| Archive          | Size | Purpose         |
| ---------------- | ---- | --------------- |
| yo_b_01c.aar     |      | Main sprites    |
| yo_b_01_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 35       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** (needs verification) - likely LIGHT or STANDARD

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity:
- Walk speed:
- Comparison to reference characters:

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    |                    | Slow / Normal / Fast               |
| Dash Type     |                    | Standard / Flash                   |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

### Unique Mechanics

**Summon/Trap System:**

Per Research-Status.md, Yugi has two projectile system categories:

1. **Summons** - Separate entities (Duel Monsters)
2. **Persistent/Traps** - Remain after switch-out (fwd B confirmed)

This makes Yugi a unique zoning/setup character who can maintain battlefield control even when switching out.

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                        | Priority | Status    | Result |
| ----------- | --------------------------------------- | -------- | --------- | ------ |
| yo_b_01-001 | B move damage (neutral)                 | P2       | PENDING   |        |
| yo_b_01-002 | fwd B trap persistence after switch-out | P1       | PENDING   |        |

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
   - [ ] fwd B trap persistence verification (switch out, confirm trap remains)
   - [ ] Summon behavior (independent targeting? duration?)
   - [ ] Damage type verification for summons

---

## Unknown / Needs Research

### Unverified Data

1. Complete collision file entry count and structure
2. battleParams byte values
3. Full jpower block 47 entry contents
4. Trap duration mechanics

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Summon damage type classification
- [ ] Trap persistence duration limits
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. How long do traps persist after switch-out?
2. Can multiple traps be active simultaneously?
3. Do summoned monsters have independent AI or fixed patterns?

---

## Related Characters

| Character  | chr_b Index | Collision File | Relationship             |
| ---------- | ----------- | -------------- | ------------------------ |
| Hiei       | 34          | yh_b_03.bin    | Same charId (47)         |
| Dio        | 29          | jj_b_02.bin    | Also uses Summons (Stand)|

**Characters sharing jpower Block 47:**

- (needs verification)

**Characters sharing charId 47:**

- Yugi (yo_b_01)
- Hiei (yh_b_03)
- Muhyo (mr_b_01)
- Taikoubou (hs_b_01)

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
- [Research-Status.md](../research/Research-Status.md) - mentions Yugi's trap system

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- Per Research-Status.md: "Persistent/Traps - Remain after switch-out (Yugi fwd B, Dr. Mashirito)"
- Yugi shares charId=47 with Hiei, Muhyo, and Taikoubou - all characters with summoning/special mechanics
- Unique zoning playstyle with trap persistence mechanics
- Collision file likely has Type 5 (Summon) entries similar to Dio's Stand
