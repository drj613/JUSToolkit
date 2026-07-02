# DamageFlags Character Classification

Complete classification of all 74 battle characters by jpower entry selection
system.

**Issue:** JUS-9lp.1.1

---

## Classification System

| System               | Pattern                          | Count         |
| -------------------- | -------------------------------- | ------------- |
| **Indirect Lookup**  | damageFlags ≤ 1 for most entries | 64 characters |
| **Direct Reference** | damageFlags ≥ 2 for most entries | 10 characters |

### Key Discovery (2026-02-02)

**`damageFlags=1` is a FLAG, not a jpower index.**

Originally we classified based on `damageFlags > 0`, which incorrectly split
characters like Goku (Indirect) and Goku SSJ (Direct) despite them sharing the
same moveset.

Correct interpretation:

- `damageFlags=0` → Indirect lookup (unknown ARM9 mechanism)
- `damageFlags=1` → Indirect lookup (standard attack flag)
- `damageFlags≥2` → Direct jpower array index
- `damageFlags=64` → Buff trigger (0x40)

---

## Complete Classification

### Direct Reference System (10 characters)

These characters use `damageFlags` as direct jpower array indices.

| Character        | File    | Direct (≥2) | Total | Ratio |
| ---------------- | ------- | ----------- | ----- | ----- |
| Ichigo           | bl_b_01 | 19          | 20    | 95%   |
| Bankai Ichigo    | bl_b_02 | 5           | 5     | 100%  |
| Renji            | bl_b_04 | 28          | 33    | 85%   |
| Hitsugaya        | bl_b_05 | 2           | 2     | 100%  |
| Kazuki           | bu_b_01 | 29          | 31    | 94%   |
| Taikoubou        | hs_b_01 | 18          | 21    | 86%   |
| Gear 2 Luffy     | op_b_02 | 15          | 16    | 94%   |
| Yoh              | sk_b_01 | 13          | 14    | 93%   |
| Yoh (White Swan) | sk_b_02 | 16          | 19    | 84%   |
| Hiei             | yh_b_03 | 5           | 8     | 62%   |

### Indirect Lookup System (64 characters)

These characters use `damageFlags=0` or `damageFlags=1` for most attacks.

| Character      | File    | Indirect (≤1) | Total | Direct % |
| -------------- | ------- | ------------- | ----- | -------- |
| Bo-bobo        | bb_b_01 | 20            | 23    | 13%      |
| Shinsetsu      | bb_b_02 | 22            | 27    | 19%      |
| Don Patch      | bb_b_03 | 11            | 12    | 8%       |
| Super Patch    | bb_b_04 | 15            | 18    | 17%      |
| Train          | bc_b_01 | 3             | 4     | 25%      |
| Eve            | bc_b_02 | 15            | 18    | 17%      |
| Rukia          | bl_b_03 | 12            | 15    | 20%      |
| Goku           | db_b_01 | 24            | 25    | 4%       |
| Goku (SSJ)     | db_b_02 | 35            | 36    | 3%       |
| Vegetto        | db_b_03 | 14            | 15    | 7%       |
| Vegeta         | db_b_04 | 18            | 19    | 5%       |
| Vegeta (SSJ)   | db_b_05 | 15            | 15    | 0%       |
| Gohan (SSJ)    | db_b_06 | 14            | 14    | 0%       |
| Gohan (SSJ2)   | db_b_07 | 5             | 5     | 0%       |
| Gotenks        | db_b_08 | 5             | 5     | 0%       |
| Gotenks (SSJ)  | db_b_09 | 18            | 18    | 0%       |
| Piccolo        | db_b_10 | 2             | 2     | 0%       |
| Frieza         | db_b_11 | 17            | 18    | 6%       |
| Majin Buu      | db_b_12 | 16            | 18    | 11%      |
| Allen          | dg_b_01 | 15            | 22    | 32%      |
| Lenalee        | dg_b_02 | 27            | 28    | 4%       |
| Arale          | ds_b_01 | 15            | 15    | 0%       |
| Mashirito      | ds_b_02 | 1             | 1     | 0%       |
| Caramelman     | ds_b_03 | 19            | 23    | 17%      |
| Komaman Red    | dt_b_01 | 14            | 15    | 7%       |
| Komaman Yellow | dt_b_02 | 14            | 15    | 7%       |
| Komaman Green  | dt_b_03 | 14            | 15    | 7%       |
| Taizo          | dt_b_04 | 1             | 1     | 0%       |
| Gintoki        | gt_b_01 | 8             | 8     | 0%       |
| Kagura         | gt_b_02 | 3             | 3     | 0%       |
| Gon            | hh_b_01 | 4             | 5     | 20%      |
| Killua         | hh_b_02 | 13            | 15    | 13%      |
| Kenshiro       | hk_b_01 | 18            | 19    | 5%       |
| Raoh           | hk_b_02 | 18            | 19    | 5%       |
| Jotaro         | jj_b_01 | 15            | 18    | 17%      |
| Dio            | jj_b_02 | 6             | 6     | 0%       |
| Ryotsu         | kk_b_01 | 10            | 12    | 17%      |
| Kinnikuman     | kn_b_01 | 4             | 4     | 0%       |
| Muhyo          | mr_b_01 | 1             | 1     | 0%       |
| Naruto         | na_b_01 | 11            | 14    | 21%      |
| Kyuubi Naruto  | na_b_02 | 9             | 17    | 47%      |
| Sasuke         | na_b_03 | 18            | 22    | 18%      |
| Sakura         | na_b_04 | 8             | 15    | 47%      |
| Kakashi        | na_b_05 | 2             | 4     | 50%      |
| Fuusuke        | nk_b_01 | 18            | 22    | 18%      |
| Neuro          | nn_b_01 | 9             | 12    | 25%      |
| Momotaro       | oj_b_01 | 18            | 21    | 14%      |
| Edajima        | oj_b_02 | 8             | 15    | 47%      |
| Luffy          | op_b_01 | 35            | 38    | 8%       |
| Zoro           | op_b_03 | 48            | 51    | 6%       |
| Nami           | op_b_04 | 16            | 16    | 0%       |
| PCT Nami       | op_b_05 | 9             | 10    | 10%      |
| Sanji          | op_b_06 | 40            | 41    | 2%       |
| Robin          | op_b_07 | 32            | 32    | 0%       |
| Franky         | op_b_08 | 1             | 1     | 0%       |
| Jaguar         | pj_b_01 | 12            | 13    | 8%       |
| Kenshin        | rk_b_01 | 6             | 6     | 0%       |
| Anna           | sk_b_03 | 4             | 4     | 0%       |
| Seiya          | ss_b_01 | 31            | 31    | 0%       |
| Gold Seiya     | ss_b_02 | 20            | 21    | 5%       |
| Tsuna          | tr_b_01 | 34            | 35    | 3%       |
| Yusuke         | yh_b_01 | 31            | 32    | 3%       |
| Kurama         | yh_b_02 | 9             | 16    | 44%      |
| Yugi           | yo_b_01 | 2             | 4     | 50%      |

---

## DamageFlags Value Distribution

Analysis of all 1214 collision entries across 74 battle characters:

| Value | Count     | Interpretation                          |
| ----- | --------- | --------------------------------------- |
| 0     | 609 (50%) | Indirect lookup                         |
| 1     | 342 (28%) | Indirect lookup (standard attack flag)  |
| 2-13  | ~200      | Direct jpower indices                   |
| 14    | 43        | Special case (jpower[14] is DATA block) |
| 64    | 4         | Buff trigger (0x40)                     |
| 65-66 | 2         | Buff variants                           |

---

## Verified Examples (merged from jpower-Entry-Selection-Research.md)

### Ichigo (Direct System)

| Collision Entry | damageFlags | jpower Index | jpower.damage1 | Calculated Damage | Actual Damage |
| --------------- | ----------- | ------------ | -------------- | ----------------- | ------------- |
| B attack        | 2           | jpower[2]    | 50             | 50/5+0=10         | 10 ✓          |
| Combo           | 5           | jpower[5]    | 50             | 50/5+0=10         | 10 ✓          |
| Combo           | 3           | jpower[3]    | 45             | 45/5+0=9          | 9 ✓           |

### Goku (Indirect System)

| Move     | damageFlags | subType | hitTier | Required damage1 | Actual Damage | jpower Entry                    |
| -------- | ----------- | ------- | ------- | ---------------- | ------------- | ------------------------------- |
| B        | 0           | 1       | 2       | 40               | 8             | Unknown (indices 146, 195, 218) |
| Combo    | 0           | 2       | 2       | ?                | ?             | Unknown                         |
| Y attack | 14          | 7       | ?       | ?                | 14            | Unknown                         |

**Indirect lookup hypothesis:** when `damageFlags=0`, the game likely combines
`classId` (block), `subType`, `hitTier`, and/or an ARM9 lookup table to select
the entry; Goku's damage1=40 candidates all share `linkCategory=1`
(coincidence or criterion - unresolved).

---

## Patterns

### NOT Series-Based

Original hypothesis that series determines system is **disproven**:

| Series        | Direct | Indirect |
| ------------- | ------ | -------- |
| Bleach        | 4      | 1        |
| Dragon Ball   | 0      | 12       |
| One Piece     | 1      | 7        |
| Shaman King   | 2      | 1        |
| Yu Yu Hakusho | 1      | 2        |

### Form Variants Use Same System

When `damageFlags=1` is treated as Indirect:

- Goku (4% direct) ≈ Goku SSJ (3% direct) ✓
- Vegeta (5% direct) ≈ Vegeta SSJ (0% direct) ✓
- Gotenks (0% direct) ≈ Gotenks SSJ (0% direct) ✓

This confirms form variants share the same lookup system, as expected since they
share movesets.

---

## Next Steps

### Blocking Unknown

The **Indirect lookup mechanism** (damageFlags=0 or 1) is still unknown:

- How does the game select which jpower entry to use?
- Is there an ARM9 table mapping character+move → jpower index?
- Does collision `subType` or `hitTier` factor in?

### Required: GDB Experiment JUS-9lp.1.2

Trace ARM9 code when a character using Indirect system (e.g., Goku) deals
damage.

---

## Script

Classification generated by (script now archived - its full output is the
table above, committed in this document):

```bash
python scripts/archive/classify_damage_flags.py ./jus_files/extracted_chrbin/ChrBin.aar/chr/col/
```

---

_Last updated: 2026-02-02_
