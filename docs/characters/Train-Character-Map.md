# Train Heartnet (bc_b_01) - Complete Character Mapping

Deep dive analysis mapping Train Heartnet through all data files to understand linkages.

---

## Basic Info

| Field           | Value              |
| --------------- | ------------------ |
| Character Name  | Train Heartnet     |
| Series          | Black Cat          |
| chr_b Index     | 37                 |
| Collision File  | bc_b_01.bin        |
| charId          | 3                  |
| tier            | (needs extraction) |
| jpower Block    | 52                 |
| classId         | 564                |

---

## IMPORTANT: Shared Data with Ichigo

**CRITICAL RELATIONSHIP:**

Train Heartnet shares both `classId=564` and `jpower Block 52` with Ichigo (bl_b_01) and Bankai Ichigo (bl_b_02)!

| Character     | chr_b Index | classId | jpower Block |
| ------------- | ----------- | ------- | ------------ |
| Train Heartnet| 37          | 564     | 52           |
| Ichigo        | 39          | 564     | 52           |
| Bankai Ichigo | 40          | 564     | 52           |

Per Research-Status.md:
> Characters sharing same `classId & 0xFF` reference the same jpower block, but **DO NOT necessarily share movesets**.
> **Block 52:** bl_b_01 (Ichigo) =/= bl_b_02 (Bankai Ichigo)

This means Train, Ichigo, and Bankai all pull damage values from the same jpower template library, but have completely different movesets.

---

## In-Game Verified Data

### Koma Sizes (CONFIRMED)

- **Train Heartnet:** (needs verification) koma

### Move List (CONFIRMED)

| Move   | Damage | Type       | Notes                            |
| ------ | ------ | ---------- | -------------------------------- |
| B      |        | Punch/Kick | Hades gun - blunt attacks?       |
| fwd B  |        | Energy?    | Gunshots - projectile            |
| up B   |        | Energy?    |                                  |
| down B |        | Punch/Kick |                                  |
| air B  |        | Energy?    |                                  |
| Y      |        | Energy?    | Railgun attacks?                 |
| fwd Y  |        | Energy     |                                  |
| up Y   |        | Energy     |                                  |
| down Y |        | Energy     |                                  |
| air Y  |        | Energy     |                                  |

**Damage Types:**

- **Slashing** - Blade attacks (reduced by Slash Defense passive)
- **Impact** - Blunt attacks (reduced by Impact Defense passive)
- **Punch/Kick** - Physical attacks
- **Energy** - Projectile/energy attacks - likely for Train's gun attacks

**Note:** Train uses the Hades gun - need to determine if melee attacks with the gun deal Punch/Kick or if all attacks are Energy (projectile).

### Specials (X Moves)

| Koma | X Damage | X Notes | up X Damage | up X Notes |
| ---- | -------- | ------- | ----------- | ---------- |
|      |          |         |             |            |

---

## File Data

### chr_b.bin Entry (Index 37)

| Field        | Value | Notes                                    |
| ------------ | ----- | ---------------------------------------- |
| charId       | 3     | Shared with Bleach characters + Lenalee  |
| formType     |       | 0=Normal, 1=Powered                      |
| tier         |       | 1=-1 dmg, 2=normal, 3=+1 dmg             |
| komaSize     |       | Internal size (not deck koma)            |
| classId      | 564   | **SHARED with Ichigo/Bankai!**           |
| jpower Block | 52    | **SHARED with Ichigo/Bankai!**           |

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

### Collision File (bc_b_01.bin)

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
- Collision file is DIFFERENT from Ichigo despite shared jpower block

### jpower Block 52 Analysis (SHARED)

**IMPORTANT:** This block is shared with Ichigo and Bankai Ichigo!

Per chr_b-Complete-Mapping.md:
> Block 52 (Ichigo+Bankai) points to **empty jpower entries** (all zeros at index 52-53). This suggests jpower block index may not directly map to jpower array index.

**Attack entries in this block:**

| Entry | jpower ID | d1  | d2  | d3  | Total | Calculated Damage | Notes       |
| ----- | --------- | --- | --- | --- | ----- | ----------------- | ----------- |
|       |           |     |     |     |       |                   | Empty/sparse|

**Damage Formula:**

```
base_damage = (jpower_total / 5) + (tier - 2)
```

- tier 1: -1 modifier
- tier 2: no modifier
- tier 3: +1 modifier

**Block 52 Mystery:**

The shared block may indicate:
1. Both characters use collision-based damage rather than jpower
2. Block index interpretation differs from array index
3. Selection mechanism chooses different entries within block

### Sprite Archives (chr/)

| Archive          | Size | Purpose         |
| ---------------- | ---- | --------------- |
| bc_b_01c.aar     |      | Main sprites    |
| bc_b_01_Xc.aar   |      | X-koma portrait |

### ARM9 References

| Offset   | Contents                              | This Character |
| -------- | ------------------------------------- | -------------- |
| 0x0924B0 | Collision file pointer table          | Index 37       |
| 0x08D4A0 | chr_b -> collision identity mapping   |                |
| 0x09E780 | Koma name table                       |                |

---

## Mechanics

### Weight Category

**Category:** (needs verification)

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

**Hades Gun:**

Train's signature weapon - need to determine:
- Projectile categories (True Projectile vs Extended Hitbox)
- Damage type classification (Energy for all, or mix with Punch/Kick for melee)
- Any special properties (Railgun charged attacks?)

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
| bc_b_01-001 | B move damage (neutral)             | P2       | PENDING   |        |
| bc_b_01-002 | Compare damage to Ichigo (same tier)| P1       | PENDING   |        |

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
   - [ ] Damage type verification (gun attacks - Energy?)
   - [ ] Compare to Ichigo damage values (shared jpower block)
   - [ ] Any buffs or special states

4. **jpower Block 52 Investigation**
   - [ ] Compare Train B damage to Ichigo B damage
   - [ ] If same tier, do they share base damage values?
   - [ ] This would help understand the jpower selection mechanism

---

## Unknown / Needs Research

### Unverified Data

1. Complete collision file entry count and structure
2. battleParams byte values
3. Full jpower block 52 entry contents
4. How Train selects different moves from same jpower block as Ichigo

### Missing Information

- [ ] Complete move damage values (needs human testing)
- [ ] All koma size special damage scaling (needs human testing)
- [ ] Gun attack damage type classification
- [ ] Weight/displacement velocity location in files
- [ ] Walk speed storage location
- [ ] jpower entry selection mechanism (critical!)

### Open Questions

1. How do Train and Ichigo have different movesets from the same jpower Block 52?
2. Is damage stored in collision files for characters with "empty" jpower blocks?
3. What determines which jpower entries each character uses?

---

## Related Characters

| Character     | chr_b Index | Collision File | Relationship                        |
| ------------- | ----------- | -------------- | ----------------------------------- |
| Eve           | 38          | bc_b_02.bin    | Same series                         |
| Ichigo        | 39          | bl_b_01.bin    | **SAME classId=564, jpower Block 52** |
| Bankai Ichigo | 40          | bl_b_02.bin    | **SAME classId=564, jpower Block 52** |

**Characters sharing jpower Block 52:**

- Train Heartnet (bc_b_01) - chr_b[37]
- Ichigo (bl_b_01) - chr_b[39]
- Bankai Ichigo (bl_b_02) - chr_b[40]

**Characters sharing charId 3:**

- All Bleach characters (Ichigo, Bankai, Rukia, Renji, Hitsugaya)
- Lenalee (D.Gray-man)
- Train Heartnet (Black Cat)

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
- [Research-Status.md](../research/Research-Status.md)
- [Ichigo-Character-Map.md](./Ichigo-Character-Map.md) - shares jpower block

---

## Session Log

| Date | Session | Verified | Notes |
| ---- | ------- | -------- | ----- |
|      |         |          |       |

---

## Notes

- **CRITICAL:** Train shares classId=564 and jpower Block 52 with Ichigo and Bankai Ichigo
- This is a key research opportunity to understand jpower entry selection mechanism
- Per chr_b-Complete-Mapping.md, Block 52 appears "empty" - may mean damage is collision-based
- Train also shares charId=3 with Bleach characters (stat template group)
- Comparing Train and Ichigo damage values could reveal how characters select from shared jpower blocks
