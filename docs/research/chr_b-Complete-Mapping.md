# chr_b.bin Complete Reference

> ### Cross-check 2026-08-14 (Loop-Atlas)
>
> **Series column validated: 74/74.** An independent derivation — `koma.bin` `abilityId` → `chr_b`
> index, names from `komatxt.bin`, series from `Koma.NameTable` — agrees with this table's series code
> on every one of the 74 rows. Strong mutual validation for both.
>
> **One narrow correction: `chr_b[24]` is Kyuubi Naruto, not Kakashi.** Three independent lines:
> `koma.bin` records 504/505 (sizes 7 and 8) carry `abilityId = 24`; `komatxt.bin` names those panels
> **ナルト（九尾）**; and `chr_b[24]`'s per-size HP slots 3/4 are **192, 208**, exactly the owner's
> observed Naruto size-7/8 HP, where `chr_b[21]` gives `176, 192`. So the *name-within-series* ordering
> is off for these rows while the series column is right.
>
> Likely cause: this table assumes the `0x020924B0` string-table index equals the `chr_b` index, and
> `Battle-Engine-Map.md` **demoted** that assumption (its claim that the table's 6-bit id equals
> `classId` was refuted on a range mismatch). The alignment was never verified.
>
> **Also: the tier field is located.** The tier table below (`1`→−1, `2`→+0, `3`→+1) is
> `chr_b` byte **`+0x01`**, copied to battle-struct `+0x11` by the init function `0x02077C0C`. Its
> distribution is `{1:11, 2:56, 3:7}`. See `findings/docs-coverage-sweep.md`.


Complete mapping extracted from ARM9.bin pointer table at offset 0x0924B0.

## chr_b.bin → Collision File Mapping

| chr_b | File    | Character        | Series          | charId | classId | jpower Block |
| ----- | ------- | ---------------- | --------------- | ------ | ------- | ------------ |
| 0     | db_b_01 | Goku             | Dragon Ball     | 7      | 256     | 0            |
| 1     | db_b_02 | Goku (SSJ)       | Dragon Ball     | 7      | 256     | 0            |
| 2     | db_b_03 | Vegetto          | Dragon Ball     | 7      | 257     | 1            |
| 3     | db_b_04 | Vegeta           | Dragon Ball     | 7      | 257     | 1            |
| 4     | db_b_05 | Vegeta (SSJ)     | Dragon Ball     | 7      | 258     | 2            |
| 5     | db_b_06 | Gohan (SSJ)      | Dragon Ball     | 7      | 258     | 2            |
| 6     | db_b_07 | Gohan (SSJ2)     | Dragon Ball     | 7      | 259     | 3            |
| 7     | db_b_08 | Gotenks          | Dragon Ball     | 7      | 259     | 3            |
| 8     | db_b_09 | Gotenks (SSJ)    | Dragon Ball     | 54     | 516     | 4            |
| 9     | db_b_10 | Piccolo          | Dragon Ball     | 41     | 261     | 5            |
| 10    | db_b_11 | Frieza           | Dragon Ball     | 54     | 262     | 6            |
| 11    | db_b_12 | Majin Buu        | Dragon Ball     | 7      | 256     | 0            |
| 12    | op_b_01 | Luffy            | One Piece       | 9      | 521     | 9            |
| 13    | op_b_02 | Gear 2 Luffy     | One Piece       | 14     | 522     | 10           |
| 14    | op_b_03 | Zoro             | One Piece       | 18     | 523     | 11           |
| 15    | op_b_04 | Nami             | One Piece       | 16     | 524     | 12           |
| 16    | op_b_05 | PCT Nami         | One Piece       | 4      | 525     | 13           |
| 17    | op_b_06 | Sanji            | One Piece       | 10     | 270     | 14           |
| 18    | op_b_07 | Robin            | One Piece       | 9      | 521     | 9            |
| 19    | op_b_08 | Franky           | One Piece       | 16     | 524     | 12           |
| 20    | na_b_01 | Naruto           | Naruto          | 2      | 529     | 17           |
| 21    | na_b_02 | Kyuubi Naruto    | Naruto          | 13     | 274     | 18           |
| 22    | na_b_03 | Sasuke           | Naruto          | 8      | 275     | 19           |
| 23    | na_b_04 | Sakura           | Naruto          | 13     | 532     | 20           |
| 24    | na_b_05 | Kakashi          | Naruto          | 54     | 278     | 22           |
| 25    | sk_b_01 | Yoh              | Shaman King     | 6      | 534     | 22           |
| 26    | sk_b_02 | Yoh (White Swan) | Shaman King     | 6      | 534     | 22           |
| 27    | sk_b_03 | Anna             | Shaman King     | 6      | 535     | 23           |
| 28    | jj_b_01 | Jotaro           | JoJo            | 13     | 281     | 25           |
| 29    | jj_b_02 | Dio              | JoJo            | 54     | 282     | 26           |
| 30    | hh_b_01 | Gon              | Hunter x Hunter | 42     | 545     | 33           |
| 31    | hh_b_02 | Killua           | Hunter x Hunter | 23     | 290     | 34           |
| 32    | yh_b_01 | Yusuke           | Yu Yu Hakusho   | 45     | 549     | 37           |
| 33    | yh_b_02 | Kurama           | Yu Yu Hakusho   | 28     | 295     | 39           |
| 34    | yh_b_03 | Hiei             | Yu Yu Hakusho   | 47     | 298     | 42           |
| 35    | yo_b_01 | Yugi             | Yu-Gi-Oh!       | 47     | 303     | 47           |
| 36    | rk_b_01 | Kenshin          | Rurouni Kenshin | 1      | 304     | 48           |
| 37    | bc_b_01 | Train            | Black Cat       | 3      | 564     | 52           |
| 38    | bc_b_02 | Eve              | Black Cat       | 16     | 310     | 54           |
| 39    | bl_b_01 | Ichigo           | Bleach          | 3      | 564     | 52           |
| 40    | bl_b_02 | Bankai Ichigo    | Bleach          | 3      | 564     | 52           |
| 41    | bl_b_03 | Rukia            | Bleach          | 3      | 312     | 56           |
| 42    | bl_b_04 | Renji            | Bleach          | 3      | 310     | 54           |
| 43    | bl_b_05 | Hitsugaya        | Bleach          | 3      | 577     | 65           |
| 44    | bu_b_01 | Kazuki           | Busou Renkin    | 54     | 575     | 63           |
| 45    | dg_b_01 | Allen            | D.Gray-man      | 32     | 321     | 65           |
| 46    | dg_b_02 | Lenalee          | D.Gray-man      | 3      | 577     | 65           |
| 47    | bb_b_01 | Bo-bobo          | Bobobo          | 14     | 582     | 70           |
| 48    | bb_b_02 | Shinsetsu        | Bobobo          | 14     | 327     | 71           |
| 49    | bb_b_03 | Don Patch        | Bobobo          | 14     | 582     | 70           |
| 50    | bb_b_04 | Super Patch      | Bobobo          | 14     | 582     | 70           |
| 51    | kk_b_01 | Ryotsu           | KochiKame       | 55     | 348     | 92           |
| 52    | gt_b_01 | Gintoki          | Gintama         | 5      | 349     | 93           |
| 53    | gt_b_02 | Kagura           | Gintama         | 2      | 443     | 187          |
| 54    | tr_b_01 | Tsuna            | Reborn          | 4      | 354     | 98           |
| 55    | pj_b_01 | Jaguar           | Jaguar          | 28     | 355     | 99           |
| 56    | ds_b_01 | Arale            | Dr. Slump       | 30     | 356     | 100          |
| 57    | ds_b_02 | Mashirito        | Dr. Slump       | 45     | 357     | 101          |
| 58    | ds_b_03 | Caramelman       | Dr. Slump       | 45     | 358     | 102          |
| 59    | mr_b_01 | Muhyo            | Muhyo           | 47     | 652     | 140          |
| 60    | nn_b_01 | Neuro            | Neuro           | 31     | 669     | 157          |
| 61    | hk_b_01 | Kenshiro         | Hokuto no Ken   | 13     | 658     | 146          |
| 62    | hk_b_02 | Raoh             | Hokuto no Ken   | 13     | 403     | 147          |
| 63    | ss_b_01 | Seiya            | Saint Seiya     | 13     | 662     | 150          |
| 64    | ss_b_02 | Gold Seiya       | Saint Seiya     | 13     | 662     | 150          |
| 65    | kn_b_01 | Kinnikuman       | Kinnikuman      | 14     | 422     | 166          |
| 66    | oj_b_01 | Momotaro         | Otokojuku       | 5      | 428     | 172          |
| 67    | oj_b_02 | Edajima          | Otokojuku       | 9      | 420     | 164          |
| 68    | hs_b_01 | Taikoubou        | Houshin Engi    | 47     | 684     | 172          |
| 69    | nk_b_01 | Fuusuke          | Ninku           | 2      | 435     | 179          |
| 70    | dt_b_01 | Komaman Red      | Debug           | 0      | 446     | 190          |
| 71    | dt_b_02 | Komaman Yellow   | Debug           | 0      | 447     | 191          |
| 72    | dt_b_03 | Komaman Green    | Debug           | 0      | 448     | 192          |
| 73    | dt_b_04 | Taizo            | Debug           | 0      | 446     | 190          |

## Key Discoveries

### Shared jpower Blocks (≠ Shared Movesets!)

Characters sharing the same `classId & 0xFF` reference the same jpower block,
but **DO NOT necessarily share movesets**.

**Confirmed shared movesets:**

- db_b_01 + db_b_02 (Goku + Goku SSJ) - Block 0
- bb_b_03 + bb_b_04 (Don Patch + Super Patch) - Block 70

**Same jpower block, DIFFERENT movesets:**

- **Block 0:** db_b_12 (Majin Buu) ≠ Goku
- **Block 9:** op_b_01 (Luffy) ≠ op_b_07 (Robin)
- **Block 12:** op_b_04 (Nami) ≠ op_b_08 (Franky)
- **Block 52:** bl_b_01 (Ichigo) ≠ bl_b_02 (Bankai Ichigo)
- **Block 70:** bb_b_01 (Bo-bobo) ≠ bb_b_03/04 (Don Patch variants)

**Conclusion:** jpower blocks are **template libraries**, not complete movesets.
Characters select specific entries from their assigned block via unknown
mechanism (possibly collision subType, type2, linkCategory, or other selection
logic).

### Damage Formula (SOLVED - see Research-Status.md)

**Confirmed for all tested characters:**

```
damage = floor(jpower.damage1 / 5) + (tier - 2)
```

- Uses `damage1` (first component) ONLY - NOT the d1+d2+d3 total
- tier 1: -1 modifier (Bankai B = 9)
- tier 2: +0 modifier (Ichigo B = 10)
- tier 3: +1 modifier (Caramelman B = 13)
- Nature multiplier: 1.5x on advantage only

**Former "Goku paradox" (DEBUNKED):** An earlier total-based version of the
formula could not explain Goku B=8 and spawned a bogus ÷7 alternative. With
`damage1` alone there is no paradox: B=8 comes from `damage1=40` entries
(global indices 146, 195, 218, outside Block 0).

**Collision damage difference:**

- Goku: 2/25 collision entries have damageFlags (values: 1, 14)
- Ichigo: 19/20 collision entries have damageFlags (values: 2-14)
- Characters with more collision damage may bypass jpower entirely

### Block 52 Mystery

Block 52 (Ichigo+Bankai) points to **empty jpower entries** (all zeros at index
52-53). This suggests jpower block index may not directly map to jpower array
index.

**Possible interpretations:**

1. Block index counts DATA entries, not array index
2. Block index is multiplied/offset before lookup
3. Characters with collision damage don't need jpower

### Stat Template Groups (charId)

29 unique charIds for 74 characters:

- **charId=7**: Goku family (9 chars)
- **charId=3**: Bleach + Lenalee (6 chars)
- **charId=13**: Mixed group (7 chars including Raoh)
- **charId=16**: Nami + Franky (opposites!)

## Weight (UNKNOWN) & Walk Speed (SOLVED)

**Weight is NOT stored in:**

- chr_b.bin battleParams
- Collision files
- ARM9 near file name table

**Known weight from gameplay:**

- HEAVY: Raoh, Edajima, Franky
- LIGHT: Lenalee, Nami
- STANDARD: Goku, Dio, Gon, Momotaro

**Walk speed IS in chr_b.bin** (`statC` field, threshold/tier-based):

The earlier conclusion that walk speed was "not in chr_b" was wrong — it was
confounded by **Edajima**, who has a normal statC value but is slowed by an
innate character passive (he is the heaviest/slowest character). See
Research-Status.md for the confirmed tier data; exact thresholds are tracked
in JUS-n3p.

Weight location remains unknown. Walk speed is solved (statC).
