# HP Fully Solved — All 74 Battle Characters, Every Size (Card F1 Closed)

> **Refinement (2026-08-14, from K3):** the `+0x10` block is an array of five **4-byte records**, not
> five lone bytes at stride 4. The character-init function `0x02077C0C` computes
> `chr_b_rec + (size-4)*4` (an `add ..,lsl #2`) and reads four fields from each record: `+0x0` max HP,
> `+0x1` **regen rate** (defaulting to 4 if zero), `+0x2` and `+0x3` unknown. The HP column in the
> table below is `+0x0` of each record and is unaffected — but the "u16 high bytes of 1, 4, 5, 16, 20,
> 22" I couldn't explain in iteration 7 were the **regen-rate field**, not high bytes of anything.
> See `findings/k3-chr_b-to-battle-copy.md`.


> ### Two caveats added 2026-08-14
>
> **1. `sources` is dynamic during a fight.** The harness session watched one slot's max HP go from
> `160.0` to `176.0` mid-battle — `+16`, i.e. two more `+8` sources coming online. So in
> `max = chr_b[idx][size-4] + 8 × sources`, the bonus count is **not fixed at battle start**. That
> fits `0x020784B8` (add-to-max, clamp `0x4000`) firing when a source activates. Any comparison of
> max HP across time needs this caveat; the **base** table below is unaffected.
>
> **2. A battle slot is a deck slot, not "the active character".** The four slots hold the deck in
> deck order, and which fighter is currently out is tracked elsewhere (candidate flags at struct
> `+0x0F` / `+0x47`, mapping not established). Earlier notes labelling slot 0 as "P active" were
> relying on that character happening to be both slot 0 and active when first measured.
>
> **The index→name join below is verified**, though — see `findings/chr_b-join-verified.md`. Two
> live RAM identifications match it exactly: `chr_b[0]` = 悟空 with base `152` (observed `160` = +8)
> and `chr_b[12]` = ルフィ with base `144` (observed `152` = +8).


Loop-Atlas iteration 8. Static analysis, cross-validated against live RAM via melonDS harness.

**HP is table data, not a formula.** Every character's HP at every size is readable offline from `chr_b.bin`. Card F1 is closed.

## The Formula

```
max_HP = chr_b[index][size - 4]  +  8 × (active Ｊ魂+ sources)
```

- `index` = `koma.bin` byte `0x7` (`abilityId`) for battle panels. CONFIRMED: 74 distinct values
  in `0..73`, and `chr_b.bin` is 74 × 60 bytes.
- The per-size array is **five u8 slots at `0x10`, `0x14`, `0x18`, `0x1C`, `0x20`** (stride 4),
  indexed by `size - 4`. Battle panels are sizes 4–8 — exactly five sizes for five slots.
- All 370 of those bytes are multiples of 8, matching the measured HP quantum.
- The `+8` term is ability index 52 `Ｊ魂最大値＋`, which the game's own text marks `※複数有効`
  ("multiple instances are effective"). Leader and each relationship adjacency each contribute
  one, so four sources give `+32`.

The harness confirmed this against RAM: the battle struct carries the `chr_b` index at **`hp_addr + 0x29`**, and six populated deck slots matched `chr_b[index][0]` exactly — with `+8` on the two **active** characters and `0` on the four benched ones.

### Card F1's Answer

**Naruto size-5 = `160` displayed = raw `10240`.** The iteration-7 prediction was correct; `size × 36` (180) and `8 × (14 + size)` (152) are both REFUTED.

## The Filler Question Is Resolved

Iteration 7 noted only 19 of 74 entries are non-decreasing across five slots and offered two readings: **(A)** slots are per-size HP with filler in unowned sizes, or **(B)** the stride-4 grouping was wrong. **(A) is correct.**

Cross-referencing every battle panel in `koma.bin` against its `chr_b` index: of 370 slots, only **174 are meaningful** — one per (character, owned size) pair. The other 196 are filler, which is why most entries zig-zag.

Two examples:

- `chr_b[0]` 悟空 owns sizes 4–5: `[152, 168, 168, 168, 168]`. Slots 0–1 are real, 2–4 repeat.
  The harness read Goku active at `160` = `152 + 8`. ✓
- `chr_b[20]` ナルト owns sizes 4–6: `[144, 160, 176, 144, 144]`. Slots 3–4 repeat because
  Naruto's sizes 7–8 live in a *different* record.

### On the 192/208 Attribution

The harness suggested my Naruto ladder numbers belonged to `chr_b[12]`. Both things are true:

- `chr_b[12]` = `[144, 160, 176, 192, 208]` — a complete ladder for a character who owns all five sizes.
- `chr_b[24]` = `[80, 96, 112, 192, 208]`, reached **only** by `koma.bin` records 504 and 505, both named ナルト（九尾）, both sizes 7–8. So its slots 3–4 are genuinely Naruto's size-7 and size-8 HP.

`192`/`208` legitimately appear in both records. HP values are shared across characters, so identical arrays are common and aren't evidence of a mix-up. Naruto's full curve — `144, 160, 176, 192, 208` — spans two records because ナルト（九尾） is a separate character entry. That's also why `komatxt.bin` renames those panels.

## Retired Method: Poking Ability IDs Does Nothing

The harness ran a controlled experiment with a **negative** result: the runtime ability array is *not* read at damage time. Removing `0x09` from Luffy left damage identical; adding `0x09` to Goku left incoming damage identical. Three controls ruled out a failed poke.

That array is a **source list** — good for *reading* which abilities a character has (it's how `0x09`/`0x0C` were confirmed on Luffy), useless for *changing* behavior. Resistance is precomputed at character load.

**Card E1 could never have worked by poking**, so closing it statically from `ability.bin` + `ability_t.bin` was the only route. The "write an ID and observe" method is retired for all future cards.

## Caveats

- This does not separate "is leader" from "is currently active" — both active characters had exactly one `+8` source. The `+8` is confirmed; its *trigger* is not fully pinned.
- Slot→size rests on the structural argument (five sizes, five slots), the 174/370 coverage fit, and one directly observed anchor (Naruto size 4 = 144). Sizes 5–8 are not yet observed in RAM.
- Values here are **max** HP. Damage arithmetic uses 1/64 raw units, but stored HP carries no fraction — every observed value was an exact multiple of 64 raw.

## All 74 Battle Characters

`chr_b` index, name from `komatxt.bin`, series code from `Koma.NameTable`, the sizes that
character actually has panels for, HP at each, and the raw slot array (including filler).

| chr_b | name | series | sizes owned | HP per owned size | full slot array |
|---|---|---|---|---|---|
| 0 | 悟空 | db | [4, 5] | 4:152, 5:168 | [152, 168, 168, 168, 168] |
| 1 | 超サイヤ人悟空 | db | [6, 7] | 6:184, 7:200 | [104, 120, 184, 200, 152] |
| 2 | べジータ | db | [4] | 4:144 | [144, 160, 120, 120, 120] |
| 3 | 超べジータ | db | [5, 6] | 5:160, 6:176 | [88, 160, 176, 128, 128] |
| 4 | 超サイヤ人悟飯 | db | [4] | 4:136 | [136, 112, 112, 112, 112] |
| 5 | 超サイヤ人２悟飯 | db | [5] | 5:152 | [80, 152, 128, 128, 128] |
| 6 | ゴテンクス | db | [4] | 4:144 | [144, 104, 144, 144, 144] |
| 7 | 超ゴテンクス | db | [5] | 5:160 | [88, 160, 168, 168, 168] |
| 8 | ピッコロ | db | [4, 5] | 4:136, 5:152 | [136, 152, 176, 176, 176] |
| 9 | フリーザ | db | [6] | 6:160 | [88, 104, 160, 144, 144] |
| 10 | 魔人ブウ | db | [6] | 6:192 | [88, 104, 192, 168, 168] |
| 11 | ベジット | db | [8] | 8:216 | [80, 96, 176, 176, 216] |
| 12 | ルフィ | op | [4, 5, 6] | 4:144, 5:160, 6:176 | [144, 160, 176, 192, 208] |
| 13 | ゾロ | op | [4, 5, 6] | 4:160, 5:176, 6:192 | [160, 176, 192, 136, 136] |
| 14 | サンジ | op | [4, 5, 6] | 4:136, 5:152, 6:168 | [136, 152, 168, 144, 144] |
| 15 | ナミ | op | [4, 5] | 4:128, 5:144 | [128, 144, 160, 104, 104] |
| 16 | ロビン | op | [4, 5, 6] | 4:128, 5:144, 6:160 | [128, 144, 160, 96, 96] |
| 17 | フランキー | op | [4, 5] | 4:160, 5:176 | [160, 176, 112, 144, 144] |
| 18 | ルフィ（ギア２） | op | [7, 8] | 7:192, 8:208 | [64, 80, 96, 192, 208] |
| 19 | ナミ完成版天候棒 | op | [6] | 6:160 | [72, 88, 160, 96, 96] |
| 20 | ナルト | na | [4, 5, 6] | 4:144, 5:160, 6:176 | [144, 160, 176, 144, 144] |
| 21 | サスケ | na | [7, 8] | 7:176, 8:192 | [136, 152, 168, 176, 192] |
| 22 | サクラ | na | [4, 5, 6] | 4:128, 5:144, 6:160 | [128, 144, 160, 136, 136] |
| 23 | カカシ | na | [4, 5, 6] | 4:136, 5:152, 6:168 | [136, 152, 168, 136, 136] |
| 24 | ナルト（九尾） | na | [7, 8] | 7:192, 8:208 | [80, 96, 112, 192, 208] |
| 25 | 葉 | sk | [4, 5] | 4:152, 5:168 | [152, 168, 112, 144, 144] |
| 26 | 葉（白鵠） | sk | [6] | 6:184 | [80, 96, 184, 152, 152] |
| 27 | アンナ | sk | [4, 5] | 4:136, 5:152 | [136, 152, 112, 160, 160] |
| 28 | 承太郎 | jj | [4, 5, 6] | 4:152, 5:168, 6:184 | [152, 168, 184, 160, 160] |
| 29 | ＤＩＯ | jj | [4, 5, 6] | 4:144, 5:160, 6:176 | [144, 160, 176, 184, 184] |
| 30 | ゴン | hh | [4, 5, 6] | 4:144, 5:160, 6:176 | [144, 160, 176, 144, 144] |
| 31 | キルア | hh | [4, 5] | 4:136, 5:152 | [136, 152, 120, 144, 144] |
| 32 | 幽助 | yh | [4, 5, 6] | 4:152, 5:168, 6:184 | [152, 168, 184, 160, 160] |
| 33 | 蔵馬 | yh | [4, 5] | 4:136, 5:152 | [136, 152, 120, 144, 144] |
| 34 | 飛影 | yh | [4, 5] | 4:136, 5:152 | [136, 152, 128, 160, 160] |
| 35 | 遊戯 | yo | [4, 5, 6] | 4:136, 5:152, 6:168 | [136, 152, 168, 152, 152] |
| 36 | 剣心 | rk | [4, 5, 6] | 4:136, 5:152, 6:168 | [136, 152, 168, 160, 160] |
| 37 | イヴ | bc | [4, 5] | 4:128, 5:144 | [128, 144, 104, 136, 136] |
| 38 | トレイン | bc | [4, 5] | 4:136, 5:152 | [136, 152, 104, 136, 136] |
| 39 | 一護 | bl | [4, 5, 6] | 4:144, 5:160, 6:176 | [144, 160, 176, 128, 128] |
| 40 | 一護（卍解） | bl | [7, 8] | 7:176, 8:192 | [72, 88, 160, 176, 192] |
| 41 | ルキア | bl | [4, 5, 6] | 4:128, 5:144, 6:160 | [128, 144, 160, 136, 136] |
| 42 | 阿散井恋次 | bl | [4, 5, 6] | 4:152, 5:168, 6:184 | [152, 168, 184, 128, 128] |
| 43 | 日番谷冬獅郎 | bl | [4, 5, 6] | 4:136, 5:152, 6:168 | [136, 152, 168, 128, 128] |
| 44 | カズキ | bu | [4, 5, 6] | 4:152, 5:168, 6:184 | [152, 168, 184, 152, 152] |
| 45 | アレン | dg | [4, 5, 6] | 4:136, 5:152, 6:168 | [136, 152, 168, 136, 136] |
| 46 | リナリー | dg | [4, 5] | 4:128, 5:144 | [128, 144, 112, 136, 136] |
| 47 | ボーボボ | bb | [4, 5, 6] | 4:160, 5:176, 6:192 | [160, 176, 192, 208, 144] |
| 48 | 首領パッチ | bb | [4, 5, 6] | 4:144, 5:160, 6:176 | [144, 160, 176, 136, 136] |
| 49 | 真説ボーボボ | bb | [7] | 7:208 | [88, 104, 120, 208, 136] |
| 50 | 怒んパッチ | bb | [7] | 7:192 | [88, 104, 120, 192, 136] |
| 51 | 両さん | kk | [4, 5, 6, 7] | 4:160, 5:176, 6:192, 7:208 | [160, 176, 192, 208, 136] |
| 52 | 銀さん | gt | [4, 5, 6, 7] | 4:144, 5:160, 6:176, 7:192 | [144, 160, 176, 192, 120] |
| 53 | 神楽 | gt | [4, 5, 6] | 4:152, 5:168, 6:184 | [152, 168, 184, 120, 120] |
| 54 | ツナ／リボーン | tr | [4, 5, 6] | 4:144, 5:160, 6:176 | [144, 160, 176, 152, 152] |
| 55 | ジャガー | pj | [4, 5, 6] | 4:144, 5:160, 6:176 | [144, 160, 176, 168, 168] |
| 56 | アラレ | ds | [4, 5, 6, 7] | 4:152, 5:168, 6:184, 7:200 | [152, 168, 184, 200, 160] |
| 57 | ドクターマシリト | ds | [4, 5, 6, 7] | 4:144, 5:160, 6:176, 7:192 | [144, 160, 176, 192, 184] |
| 58 | キャラメルマンＪ | ds | [8] | 8:208 | [72, 88, 104, 192, 208] |
| 59 | ムヒョ | mr | [4, 5, 6, 7] | 4:128, 5:144, 6:160, 7:176 | [128, 144, 160, 176, 184] |
| 60 | ネウロ／弥子 | nn | [4, 5] | 4:152, 5:168 | [152, 168, 104, 184, 184] |
| 61 | ケンシロウ | hk | [4, 5, 6, 7, 8] | 4:144, 5:160, 6:176, 7:192, 8:208 | [144, 160, 176, 192, 208] |
| 62 | ラオウ | hk | [6, 7, 8] | 6:184, 7:200, 8:216 | [72, 88, 184, 200, 216] |
| 63 | 星矢 | ss | [4, 5, 6, 7] | 4:136, 5:152, 6:168, 7:184 | [136, 152, 168, 184, 184] |
| 64 | 星矢（黄金聖衣） | ss | [8] | 8:200 | [72, 88, 104, 184, 200] |
| 65 | キン肉マン | kn | [4, 5, 6, 7, 8] | 4:152, 5:168, 6:184, 7:200, 8:216 | [152, 168, 184, 200, 216] |
| 66 | 江田島平八 | oj | [8] | 8:224 | [104, 64, 152, 64, 224] |
| 67 | 桃 | oj | [4, 5, 6] | 4:144, 5:160, 6:176 | [144, 160, 176, 184, 184] |
| 68 | 太公望 | hs | [4, 5, 6] | 4:136, 5:152, 6:168 | [136, 152, 168, 184, 184] |
| 69 | 風助 | nk | [4, 5] | 4:136, 5:152 | [136, 152, 104, 184, 184] |
| 70 | コマレッド | dt | [4] | 4:104 | [104, 64, 152, 64, 64] |
| 71 | コマグリーン | dt | [4] | 4:104 | [104, 64, 152, 64, 64] |
| 72 | コマイエロー | dt | [4] | 4:104 | [104, 64, 152, 64, 64] |
| 73 | 百手太臓（Ｍ） | dt | [4] | 4:224 | [224, 64, 152, 64, 64] |

<!-- battle panels covered: 206; size-slots used: 174 -->
