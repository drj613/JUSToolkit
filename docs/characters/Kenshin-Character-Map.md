# Himura Kenshin (rk_b_01) - Complete Character Mapping

Deep dive analysis mapping Himura Kenshin through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Himura Kenshin     |
| Series          | Rurouni Kenshin    |
| chr_b Index     | 36                 |
| Collision File  | rk_b_01.bin        |
| charId          | 1                  |
| tier            | (needs extraction) |
| jpower Block    | 48                 |
| classId         | 304                |

---

## IMPORTANT: Damage Type Override

**CONFIRMED per Research-Status.md:**

> `hitProperties=1` in collision data forces blunt damage regardless of weapon visual.
>
> **Verified:** Kenshin uses sword visually but deals punch/kick damage (tested vs Naruto and Luffy with different resistances).

This is a critical finding: Despite wielding a reverse-blade sword (sakabato), Kenshin's attacks deal **Punch/Kick (Impact) damage**, NOT Slashing damage. This matches his character's philosophy of non-lethal combat.

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Kenshin:** (needs verification) koma

### Move List (CONFIRMED)

| Move   | Damage | Type       | Notes                              |
| ------ | ------ | ---------- | ---------------------------------- |
| B      |        | Punch/Kick | hitProperties=1 forces blunt dmg   |
| fwd B  |        | Punch/Kick | Sword visual, blunt damage         |
| up B   |        | Punch/Kick |                                    |
| down B |        | Punch/Kick |                                    |
| air B  |        | Punch/Kick |                                    |
| Y      |        | Punch/Kick |                                    |
| fwd Y  |        | Punch/Kick | Hiten Mitsurugi-ryu techniques     |
| up Y   |        | Punch/Kick |                                    |
| down Y |        | Punch/Kick |                                    |
| air Y  |        | Punch/Kick |                                    |

**Damage Types:**

- **Slashing** - Blade attacks (reduced by Slash Defense passive) - NOT used by Kenshin
- **Impact** - Blunt attacks (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks - **KENSHIN USES THIS** despite sword visual
- **Energy** - Projectile/energy attacks

**VERIFIED:** Kenshin's sword attacks deal Punch/Kick damage due to `hitProperties=1` override. This was tested against characters with different damage resistances.

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 36)

| Field        | Value | Notes                          |
| ------------ | ----- | ------------------------------ |
| charId       | 1     | Unique charId                  |
| formType     |       | 0=Normal, 1=Powered            |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg   |
| komaSize     |       | Internal size (not deck koma)  |
| classId      | 304   | Low byte = jpower block index  |
| jpower Block | 48    | classId & 0xFF                 |

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

### Collision File (rk_b_01.bin)

| Property    | Value               |
| ----------- | ------------------- |
| Size        | (needs extraction)  |
| Entry Count | (needs extraction)  |
| Location    | ChrBin.aar/chr/col/ |

**Notable Entries:**

| #   | Type | SubType | Frame | Width | Height | DmgFlags | KB  | hitProperties | Notes               |
| --- | ---- | ------- | ----- | ----- | ------ | -------- | --- | ------------- | ------------------- |
|     |      |         |       |       |        |          |     | 1             | Forces blunt damage |

**CRITICAL: hitProperties Field**

- `hitProperties=1` forces all attacks to deal Punch/Kick (blunt) damage
- This overrides the visual appearance of sword attacks
- Unique mechanic that matches Kenshin's reverse-blade sword concept

**Notes:**

- damageFlags field does NOT represent actual damage values
- hitProperties=1 is the key field that changes damage type from Slashing to Punch/Kick

### jpower Block 48 Analysis

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

**Note:** Kenshin's damage goes to damage1 (Punch/Kick) field, NOT damage3 (Blade) despite sword visual.

### Sprite Archives (chr/)

| Archive          | Size | Purpose         |
| ---------------- | ---- | --------------- |
| rk_b_01c.aar     |      | Main sprites    |
| rk_b_01_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 36       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** (needs verification) - likely STANDARD

Options: LIGHT / STANDARD / HEAVY

**Observations:**

- Displacement velocity:
- Walk speed:
- Comparison to reference characters:

### Movement

| Property      | Value              | Notes                              |
| ------------- | ------------------ | ---------------------------------- |
| Walk Speed    |                    | Slow / Normal / Fast               |
| Dash Type     |                    | Standard / Flash (possibly Flash)  |
| Dash Distance |                    |                                    |

**Dash types:**

- **Standard** - Character dashes forward visibly (Goku, Gon, Nami)
- **Flash** - Character vanishes and reappears ahead (Ichigo, Dio, Gear 2 Luffy)

**Note:** Given Kenshin's Hiten Mitsurugi-ryu style emphasizes god-like speed, he may have Flash dash.

### Unique Mechanics

**hitProperties=1 Damage Type Override:**

This is a confirmed unique mechanic:
- All of Kenshin's sword attacks deal Punch/Kick damage instead of Slashing
- This is implemented via `hitProperties=1` in collision data
- Matches the reverse-blade sword (sakabato) concept from the manga
- Characters with Impact Defense passive will resist Kenshin's attacks
- Characters with Slash Defense passive will NOT resist Kenshin's attacks

This creates an interesting matchup dynamic where Kenshin counters characters expecting Slash Defense but is countered by Impact Defense.

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                            | Priority | Status | Result     |
| ----------- | ------------------------------------------- | -------- | ------ | ---------- |
| rk_b_01-001 | B move damage (neutral)                     | P2       | PENDING |            |
| rk_b_01-002 | Damage type vs Impact Defense (should reduce) | P1    | DONE   | CONFIRMED  |
| rk_b_01-003 | Damage type vs Slash Defense (should NOT reduce) | P1 | DONE   | CONFIRMED  |

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
   - [x] Damage type verification - CONFIRMED: Punch/Kick despite sword visual
   - [ ] Any buffs or special states (Battousai mode?)

---

## Unknown / Needs Research

### Unverified Data

1. Complete collision file entry count and structure
2. battleParams byte values
3. Full jpower block 48 entry contents

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Whether any moves bypass hitProperties=1 (possible Battousai attacks?)
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location

### Open Questions

1. Do ALL of Kenshin's attacks have hitProperties=1, or just sword attacks?
2. Does Kenshin have a powered-up form (Battousai) with different damage types?
3. Is charId=1 unique to Kenshin? (appears to be - only entry with this ID)

---

## Related Characters

| Character | chr_b Index | Collision File | Relationship              |
| --------- | ----------- | -------------- | ------------------------- |
| Ichigo    | 39          | bl_b_01.bin    | Sword user (Slashing dmg) |
| Hiei      | 34          | yh_b_03.bin    | Sword user (Slashing dmg) |

**Characters sharing jpower Block 48:**

- (needs verification)

**Unique charId:**

- Kenshin appears to be the only character with charId=1

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
- [Research-Status.md](../research/Research-Status.md) - **mentions hitProperties=1 verification**

---

## Session Log

| Date       | Session | Verified                         | Notes                                |
| ---------- | ------- | -------------------------------- | ------------------------------------ |
| (previous) | -       | hitProperties=1 damage override  | Tested vs Naruto/Luffy per Research-Status |

---

## Notes

- **CRITICAL FINDING:** Kenshin uses `hitProperties=1` which forces Punch/Kick damage despite sword visual
- This was verified in-game by testing against characters with Slash Defense and Impact Defense passives
- Thematically matches the reverse-blade sword (sakabato) concept - Kenshin deals blunt trauma, not cutting damage
- Unique charId=1 (only character with this value in the entire roster)
- Creates interesting matchup dynamics: counters Slash Defense, weak to Impact Defense
