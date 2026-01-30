# chr_b.bin Analysis

## Confirmed Discoveries

### chr_b.bin → Collision File Mapping (CONFIRMED)

Found in ARM9.bin at offset 0x0924B0 - pointer table to collision file names in
order:

| chr_b Index | File                      | Character                 |
| ----------- | ------------------------- | ------------------------- |
| 0-11        | db_b_01 through db_b_12   | Dragon Ball (12 chars)    |
| 12-19       | op_b_01 through op_b_08   | One Piece (8 chars)       |
| 20-24       | na_b_01 through na_b_05   | Naruto (5 chars)          |
| 25-27       | sk_b_01 through sk_b_03   | Shaman King (3 chars)     |
| 28-29       | jj_b_01, jj_b_02          | JoJo (2 chars)            |
| 30-31       | hh_b_01, hh_b_02          | Hunter x Hunter (2 chars) |
| 32-34       | yh_b_01, yh_b_02, yh_b_03 | Yu Yu Hakusho (3 chars)   |
| 35          | yo_b_01                   | Yu-Gi-Oh (1 char)         |
| 36          | rk_b_01                   | Rurouni Kenshin (1 char)  |
| 37-38       | bc_b_01, bc_b_02          | Black Cat (2 chars)       |
| 39-43       | bl_b_01 through bl_b_05   | Bleach (5 chars)          |
| 44          | bu_b_01                   | Busou Renkin (1 char)     |
| 45-46       | dg_b_01, dg_b_02          | D.Gray-man (2 chars)      |
| 47-50       | bb_b_01 through bb_b_04   | Bobobo (4 chars)          |
| 51          | kk_b_01                   | KochiKame (1 char)        |
| 52-53       | gt_b_01, gt_b_02          | Gintama (2 chars)         |
| 54          | tr_b_01                   | Reborn (1 char)           |
| 55          | pj_b_01                   | Jaguar (1 char)           |
| 56-58       | ds_b_01, ds_b_02, ds_b_03 | Dr. Slump (3 chars)       |
| 59          | mr_b_01                   | Muhyo (1 char)            |
| 60          | nn_b_01                   | Neuro (1 char)            |
| 61-62       | hk_b_01, hk_b_02          | Hokuto no Ken (2 chars)   |
| 63-64       | ss_b_01, ss_b_02          | Saint Seiya (2 chars)     |
| 65          | kn_b_01                   | Kinnikuman (1 char)       |
| 66-67       | oj_b_01, oj_b_02          | Otokojuku (2 chars)       |
| 68          | hs_b_01                   | Houshin Engi (1 char)     |
| 69          | nk_b_01                   | Ninku (1 char)            |
| 70-73       | dt_b_01 through dt_b_04   | Debug (4 chars)           |

**Verified with collision entry counts:**

- db_b_01 (Goku): 25 entries ✓
- dt_b_04 (Taizo): 1 entry ✓
- bl_b_01 (Ichigo): 20 entries ✓
- bl_b_02 (Bankai): 26 entries ✓

### charId Field = Stat Templates (NOT Character IDs)

chr_b.bin has only **29 unique charIds** for **74 characters**. Characters share
charIds as stat templates:

| charId | Characters Sharing This Template                                                       |
| ------ | -------------------------------------------------------------------------------------- |
| 3      | Ichigo, Bankai Ichigo, Rukia, Renji, Hitsugaya, **Lenalee**                            |
| 7      | Goku, Goku SSJ, Vegetto, Vegeta, Vegeta SSJ, Gohan SSJ, Gohan SSJ2, Gotenks, Majin Buu |
| 13     | Kyuubi Naruto, Sakura, Jotaro, **Kenshiro, Raoh**, Seiya, Gold Seiya                   |
| 14     | Gear 2 Luffy, Bo-bobo, Shinsetsu, Don Patch, Super Patch, Kinnikuman                   |
| 16     | **Nami, Franky** (complete opposites: light/fast vs heavy/slow!)                       |
| 54     | Gotenks SSJ, Frieza, Kakashi, **Dio**, Train, Kazuki                                   |

**Key Finding:** Nami and Franky share charId=16 and have **identical chr_b
entries**, but are opposite in weight and walk speed. This proves chr_b.bin
stores stat templates, not character-specific properties.

### battleParams Field - NOT Weight or Walk Speed

The 12-byte `battleParams` field does NOT encode:

- Character weight
- Walk speed

Evidence: Nami (light, fast) and Franky (heavy, slow) have identical
battleParams: `[15, 0, 12, 0, 10, 4, 0, 0, 60, 20, 20, 0]`

**What battleParams might encode:**

- Attack/defense stat modifiers
- Movement parameters (jump, air mobility)
- Hitstun resistance
- Unknown combat modifiers

### komaSize Field - Not Deck Koma Size

The `komaSize` field (values 2-6) does NOT match deck koma sizes (4-8).

Evidence from .aar filenames:

- Raoh has deck komas 6, 7, 8 (files: hk_b_02_6c.aar, hk_b_02_7c.aar,
  hk_b_02_8c.aar)
- But Raoh's chr_b entry has komaSize=6

The mapping is unclear - komaSize might be:

- Minimum deck koma
- A tier indicator
- Something else entirely

---

## Unknown / To Research

### Weight Storage

Weight is NOT in:

- chr_b.bin battleParams (proven via Nami/Franky test)
- Collision files (reserved fields all zero)
- ARM9 file name table region

Weight might be:

- Hardcoded in game executable by character index
- Stored in effect files (chr/effect/\*.bin)
- Calculated from other properties
- In overlays or other game code

### Walk Speed Storage

Same as weight - unknown location.

### Other battleParams Bytes

The meaning of battleParams bytes 0-11 is unclear. Needs further investigation.

### jpower.bin Linkage

How collision files link to jpower.bin entries for damage/hitstun values is
unknown.

Possible mechanisms:

- Implicit by entry order/grouping
- Via subType or hitTier mapping
- Via linkCategory in jpower matching collision patterns
- External lookup table

---

## Next Steps

1. **Examine effect files** - 66 files exist, might contain per-character
   physics properties
2. **jpower.bin mapping** - Trace how moves link to jpower entries
3. **Deep dive one character** - Fully map Goku through all data files to
   understand linkages
4. **ARM9 disassembly** - Search game code for hardcoded weight/speed tables
