# Eve (bc_b_02) - Complete Character Mapping

Deep dive analysis mapping Eve through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Eve                |
| Series          | Black Cat          |
| chr_b Index     | 38                 |
| Collision File  | bc_b_02.bin        |
| charId          | 16                 |
| tier            | (needs extraction) |
| jpower Block    | 54                 |
| classId         | 310                |

---

## IMPORTANT: charId Shared with Nami/Franky

**CRITICAL FINDING:**

Eve shares charId=16 with both Nami (op_b_04) and Franky (op_b_08)!

Per Research-Status.md:
> charId=16: **Nami and Franky** (completely opposite weight/speed but identical chr_b entry)
>
> **Conclusion:** charId groups characters by stat template, not individual identity.

This is significant because Nami and Franky have opposite physical properties:
- **Nami:** Fastest walk speed, lightest weight
- **Franky:** Slowest walk speed, heaviest weight

Yet they share the same charId! This proves charId is NOT related to weight or walk speed.

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Eve:** (needs verification) koma

### Move List (CONFIRMED)

| Move   | Damage | Type       | Notes                               |
| ------ | ------ | ---------- | ----------------------------------- |
| B      |        | Punch/Kick | Nanomachine transformation attacks  |
| fwd B  |        | Punch/Kick |                                     |
| up B   |        | Punch/Kick |                                     |
| down B |        | Punch/Kick |                                     |
| air B  |        | Punch/Kick |                                     |
| Y      |        | Slashing?  | Nanomachine blades?                 |
| fwd Y  |        | Slashing?  |                                     |
| up Y   |        | Slashing?  |                                     |
| down Y |        | Slashing?  |                                     |
| air Y  |        |            |                                     |

**Damage Types:**

- **Slashing** - Blade attacks (reduced by Slash Defense passive)
- **Impact** - Blunt attacks (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks

**Note:** Eve uses nanomachine transformations - need to verify if her transformed blade attacks deal Slashing or Punch/Kick damage.

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 38)

| Field        | Value | Notes                                       |
| ------------ | ----- | ------------------------------------------- |
| charId       | 16    | **SHARED with Nami/Franky** (opposites!)    |
| formType     |       | 0=Normal, 1=Powered                         |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg                |
| komaSize     |       | Internal size (not deck koma)               |
| classId      | 310   | Low byte = jpower block index               |
| jpower Block | 54    | classId & 0xFF                              |

### jpower Block 54 - Shared with Renji

Per chr_b-Complete-Mapping.md:
- Eve (bc_b_02): chr_b[38], classId=310, jpower Block 54
- Renji (bl_b_04): chr_b[42], classId=310, jpower Block 54

Both characters share the same jpower block and classId!

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

### Collision File (bc_b_02.bin)

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

### jpower Block 54 Analysis (SHARED with Renji)

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
| bc_b_02c.aar     |      | Main sprites    |
| bc_b_02_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 38       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** (needs verification)

Options: LIGHT / STANDARD / HEAVY

**Note:** charId=16 is shared with Nami (LIGHT/FAST) and Franky (HEAVY/SLOW), proving charId does NOT determine weight. Eve's weight must be determined through gameplay testing.

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

**Nanomachine Transformation:**

Eve's signature ability - her body can transform into various weapons and shapes:
- Need to determine if different transformations have different damage types
- Blade transformations may deal Slashing damage
- Blunt transformations may deal Punch/Kick damage
- Possible extended hitbox attacks (hair/arm extensions)

### Buff/Debuff Mechanics

| Buff Name | Trigger | Effect | Duration |
| --------- | ------- | ------ | -------- |
|           |         |        |          |

---

## Human Testing Required

> **AGENTS**: When you need in-game verification, add items here AND to the central
> queue at `docs/research/Human-Testing-Queue.md`. Format: `[CHARACTER] - [TEST]`

### Pending Tests

| Test ID     | Test Description                    | Priority | Status    | Result |
| ----------- | ----------------------------------- | -------- | --------- | ------ |
| bc_b_02-001 | B move damage (neutral)             | P2       | PENDING   |        |
| bc_b_02-002 | Weight/speed comparison             | P2       | PENDING   |        |
| bc_b_02-003 | Compare damage to Renji (same block)| P1       | PENDING   |        |

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
   - [ ] Damage type verification for different transformation attacks
   - [ ] Compare to Renji damage values (shared jpower block)
   - [ ] Any buffs or special states

4. **charId=16 Investigation**
   - [ ] Compare Eve's weight/speed to Nami and Franky
   - [ ] Document where Eve falls on the spectrum (closer to Nami or Franky?)

---

## Unknown / Needs Research

### Unverified Data

1. Complete collision file entry count and structure
2. battleParams byte values
3. Full jpower block 54 entry contents
4. Weight/speed characteristics (charId=16 doesn't determine these)

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Transformation attack damage types
- [ ] Weight/displacement velocity (NOT from charId!)
- [ ] Walk speed storage location

### Open Questions

1. Where is Eve on the weight/speed spectrum? (charId=16 includes both extremes)
2. Do different nanomachine transformations have different damage types?
3. How do Eve and Renji differ despite sharing jpower Block 54?

---

## Related Characters

| Character | chr_b Index | Collision File | Relationship                      |
| --------- | ----------- | -------------- | --------------------------------- |
| Train     | 37          | bc_b_01.bin    | Same series                       |
| Renji     | 42          | bl_b_04.bin    | **SAME classId=310, jpower Block 54** |
| Nami      | 15          | op_b_04.bin    | **SAME charId=16** (lightest/fastest) |
| Franky    | 19          | op_b_08.bin    | **SAME charId=16** (heaviest/slowest) |

**Characters sharing jpower Block 54:**

- Eve (bc_b_02) - chr_b[38]
- Renji (bl_b_04) - chr_b[42]

**Characters sharing charId 16:**

- Nami (op_b_04) - lightest, fastest
- Franky (op_b_08) - heaviest, slowest
- Eve (bc_b_02) - unknown position on spectrum

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
- [Research-Status.md](../research/Research-Status.md) - charId=16 proof

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- **charId=16 paradox:** Eve shares charId with both Nami (lightest/fastest) and Franky (heaviest/slowest)
- This PROVES charId is NOT related to weight or walk speed
- Eve shares jpower Block 54 with Renji (different series, different moveset)
- Nanomachine transformation mechanics may create variable damage types per move
- Key research character for understanding charId purpose and jpower selection
