# Character index — identity fields only

Extracted 2026-08-19 from the 71 per-character map documents, which were then deleted.
This table is **all that survived**, because it was the only part of those files that was
real.

## What this is, and what it is not

These are **identity and file-linkage fields**: which `chr_b` entry a character is, which
collision file and `jpower` block belong to them, their `charId` / `classId`. That data was
extracted from the ROM and is generally reliable.

**Nothing here is a measurement.** No move damages, no koma data, no frame data, no
mechanics. Those existed in the deleted files as `TBD`, "NEEDS VERIFICATION", or plausible
guesses, and 489 literal `TBD`s across 70 files is what "PARTIAL" actually meant.

A `—` means the source file had nothing usable for that field — often literally `TBD` or
"(needs extraction)". `tier` is `—` for most characters because it was assumed rather than
read.

**Do not cite this table as evidence for anything except file linkage.** If you need a
number, measure it and put it in a bead.

## The two characters with real data

`Goku-Character-Map.md` and `Ichigo-Character-Map.md` are kept. They are the only two files
with an in-game-verified section:

- **Goku** — verified movement/physics, innate passive, helper boosts, damage values, file
  mapping. **Read its refutation banner first**: its nature-multiplier table contradicts the
  current understanding, which is an open question, not a settled error
  [`jus-nature-january-vs-august-9a6`].
- **Ichigo** — verified move lists for base and Bankai, buff mechanics, weight/displacement.
  Its own status line notes the file-linkage sections still want independent
  re-verification.

## Other survivors

- `TEMPLATE.md` — the template the deleted files were generated from. Useful if a character
  ever gets mapped properly.
- `BaseNaruto/sprites/` — 21 PNGs labelled by animation state (hitstun variants, dash,
  air-idle rising/falling). Real reference material for animation and hitstun work, kept
  even though Naruto's map itself was unverified and removed.
- `character-index.json` — this table, machine-readable.

## Recovering a deleted file

They are in git history, not gone:

```bash
git log --diff-filter=D --name-only -- 'docs/characters/*-Character-Map.md' | head
git show <commit>^:docs/characters/Zoro-Character-Map.md
```

## The index

| Character | Series | chr_b | charId | classId | tier | jpower | Collision file | Koma |
|---|---|---|---|---|---|---|---|---|
| Allen | D.Gray-man | 45 | 32 | 321 | — | 65 | dg_b_01.bin | — |
| Anna | Shaman King | 27 | 6 | 535 | — | 23 | sk_b_03.bin | — |
| Arale | Dr. Slump | 56 | 30 | 615 | 2 | 103 | ds_b_01.bin | — |
| Bobobo | Bobobo-bo Bo-bobo | 47 | 14 | 582 | 2 (assumed) | 70 | bb_b_01.bin | — |
| Caramelman | Dr. Slump | 58 | 45 | 361 | 3 | 105 | ds_b_03.bin | — |
| Dio | JoJo's Bizarre Adventure | 29 | 54 | 282 | — | 26 | jj_b_02.bin | — |
| DonPatch | Bobobo-bo Bo-bobo | 49 | 14 | 582 | 2 | 70 | bb_b_03.bin | — |
| Edajima | Sakigake!! Otokojuku (Charge!! Men's Private School) | 67 | 9 | 420 | — | 164 | oj_b_02.bin | — |
| Eve | Black Cat | 38 | 16 | 310 | — | 54 | bc_b_02.bin | — |
| Franky | One Piece | 19 | 16 | 524 | 2 (assumed) | 12 | op_b_08.bin | — |
| Frieza | Dragon Ball | 10 | 54 | 262 | — | 6 | db_b_11.bin | — |
| Fuusuke | Ninku | 69 | 2 | 435 | — | 179 | nk_b_01.bin | — |
| Gear2-Luffy | One Piece | 13 | 14 | 522 | 2 (assumed) | 10 | op_b_02.bin | — |
| Gintoki | Gintama | 52 | 5 | 349 | — | 93 | gt_b_01.bin | — |
| Gohan-SSJ | Dragon Ball | 5 | 7 | 258 | 2 (assumed) | 2 | db_b_06.bin | — |
| Gohan-SSJ2 | Dragon Ball | 6 | 7 | 259 | — | 3 | db_b_07.bin | — |
| Goku | Dragon Ball | 0 | 7 | 256 | 2 | 0 | db_b_01.bin | 4, 5 |
| GoldSeiya | Saint Seiya | 64 | 13 | 662 | 2 (assumed) | 150 | ss_b_02.bin | — |
| Gon | Hunter x Hunter | 30 | 42 | 545 | — | 33 | hh_b_01.bin | — |
| Gotenks | Dragon Ball | 7 | 7 | 259 | — | 3 | db_b_08.bin | — |
| Gotenks-SSJ | Dragon Ball | 8 | 54 | 516 | — | 4 | db_b_09.bin | — |
| Hiei | Yu Yu Hakusho | 34 | 47 | 298 | — | 42 | yh_b_03.bin | — |
| Hitsugaya | Bleach | 43 | 3 | 577 | — | 65 | bl_b_05.bin | — |
| Ichigo | — | formType | — | — | Count | — | — | — |
| Jaguar | Pyu to Fuku! Jaguar | 55 | 28 | 355 | — | 99 | pj_b_01.bin | — |
| Jotaro | JoJo's Bizarre Adventure | 28 | 13 | 281 | — | 25 | jj_b_01.bin | — |
| Kagura | Gintama | 53 | 2 | 443 | — | 187 | gt_b_02.bin | — |
| Kakashi | Naruto | 24 | 54 | 278 | — | 22 | na_b_05.bin | — |
| Kazuki | Busou Renkin | 44 | 54 | 575 | — | 63 | bu_b_01.bin | — |
| Kenshin | Rurouni Kenshin | 36 | 1 | 304 | — | 48 | rk_b_01.bin | — |
| Kenshiro | Hokuto no Ken | 61 | 13 | 658 | 2 (assumed) | 146 | hk_b_01.bin | — |
| Killua | Hunter x Hunter | 31 | 23 | 290 | — | 34 | hh_b_02.bin | — |
| Kinnikuman | Kinnikuman (Muscle Man) | 65 | 14 | 422 | — | 166 | kn_b_01.bin | — |
| KomamanGreen | — (Debug series, unselectable) | 72 | 0 | 448 | — | 192 | dt_b_03.bin | — |
| KomamanRed | — (Debug series, unselectable) | 70 | 0 | 446 | — | 190 | dt_b_01.bin | — |
| KomamanYellow | — (Debug series, unselectable) | 71 | 0 | 447 | — | 191 | dt_b_02.bin | — |
| Kurama | Yu Yu Hakusho | 33 | 28 | 295 | — | 39 | yh_b_02.bin | — |
| Kyuubi-Naruto | Naruto | 21 | 13 | 274 | — | 18 | na_b_02.bin | — |
| Lenalee | D.Gray-man | 46 | 3 | 577 | 1 | 65 | dg_b_02.bin | — |
| Luffy | One Piece | 12 | 9 | 521 | 2 (assumed) | 9 | op_b_01.bin | — |
| Majin-Buu | Dragon Ball | 11 | 7 | 256 | 2 | 0 | db_b_12.bin | — |
| Mashirito | Dr. Slump | 57 | 45 | 360 | 2 | 104 | ds_b_02.bin | — |
| Momotaro | Sakigake!! Otokojuku (Charge!! Men's Private School) | 66 | 5 | 428 | — | 172 | oj_b_01.bin | — |
| Muhyo | Muhyo to Rouji no Mahouritsu Soudan Jimusho | 59 | 47 | 652 | — | 140 | mr_b_01.bin | — |
| Nami | One Piece | 15 | 16 | 524 | 2 (assumed) | 12 | op_b_04.bin | — |
| Naruto | Naruto | 20 | 2 | 529 | 2 (no damage modifier) | 17 | na_b_01.bin | — |
| Neuro | Majin Tantei Nougami Neuro (Demon Detective Neuro) | 60 | 31 | 669 | — | 157 | nn_b_01.bin | — |
| PCT-Nami | One Piece | 16 | 4 | 525 | 2 (assumed) | 13 | op_b_05.bin | — |
| Piccolo | Dragon Ball | 9 | 41 | 261 | — | 5 | db_b_10.bin | — |
| Raoh | Hokuto no Ken | 62 | 13 | 403 | 2 (assumed) | 147 | hk_b_02.bin | — |
| Renji | Bleach | 42 | 3 | 310 | — | 54 | bl_b_04.bin | — |
| Robin | One Piece | 18 | 9 | 521 | 2 (assumed) | 9 | op_b_07.bin | — |
| Rukia | Bleach | 41 | 3 | 312 | — | 56 | bl_b_03.bin | — |
| Ryotsu | KochiKame | 51 | 55 | 348 | — | 92 | kk_b_01.bin | — |
| Sakura | Naruto | 23 | 13 | 532 | — | 20 | na_b_04.bin | — |
| Sanji | One Piece | 17 | 10 | 270 | 2 (assumed) | 14 | op_b_06.bin | — |
| Sasuke | Naruto | 22 | 8 | 275 | — | 19 | na_b_03.bin | — |
| Seiya | Saint Seiya | 63 | 13 | 662 | 2 (assumed) | 150 | ss_b_01.bin | — |
| Shinsetsu | Bobobo-bo Bo-bobo | 48 | 14 | 327 | 2 (assumed) | 71 | bb_b_02.bin | — |
| Taikoubou | Houshin Engi (Soul Hunter) | 68 | 47 | 684 | — | 172 | hs_b_01.bin | — |
| Taizo | — (Debug series, unselectable) | 73 | 0 | 446 | — | 190 | dt_b_04.bin | — |
| Train | Black Cat | 37 | 3 | 564 | — | 52 | bc_b_01.bin | — |
| Tsuna | Reborn! | 54 | 4 | 354 | — | 98 | tr_b_01.bin | — |
| Vegeta | Dragon Ball | 3 | 7 | 257 | 2 (assumed) | 1 | db_b_04.bin | — |
| Vegeta-SSJ | Dragon Ball | 4 | 7 | 258 | 2 (assumed) | 2 | db_b_05.bin | — |
| Vegetto | Dragon Ball | 2 | 7 | 257 | 2 (assumed) | 1 | db_b_03.bin | — |
| Yoh | Shaman King | 25 | 6 | 534 | — | 22 | sk_b_01.bin | — |
| Yoh-WhiteSwan | Shaman King | 26 | 6 | 534 | — | 22 | sk_b_02.bin | — |
| Yugi | Yu-Gi-Oh! | 35 | 47 | 303 | — | 47 | yo_b_01.bin | — |
| Yusuke | Yu Yu Hakusho | 32 | 45 | 549 | — | 37 | yh_b_01.bin | — |
| Zoro | One Piece | 14 | 18 | 523 | 2 (assumed) | 11 | op_b_03.bin | — |

## Eleven placeholder rows filled from git, 2026-08-19

Eleven rows in the table above were empty stubs — literally `| Edajima | — | File | — | — | — |
— | — | — |`, with the word `File` sitting in the `chr_b` column as extraction junk. The rows
existed, so a row count matched the prose's 71; but they carried **no data**, and any tool
reading the `chr_b` column numerically skipped them silently. Two of us independently
mis-diagnosed that as "eleven records are missing from the index" before checking the raw rows.

The data was recoverable in full from the deleted map files in git (`3330204^`) and is now in
place. `tier` is left `—` rather than guessed: those maps discuss a "tier-2 modifier" in prose
and I could not tell a real field from that phrase.

**The Debug series now has names.** `chr_b` 70–73 are KomamanRed, KomamanYellow, KomamanGreen
and Taizo, collision files `dt_b_01.bin` … `dt_b_04.bin`. These are exactly the four records with
an empty on-disk ability window [`jus-ondisk-ability-list-at-chrb-0x03-kfc`], which is how they
were independently identified as unselectable.

**Four records are still unidentified: `chr_b` 1, 39, 40 and 50.** They carry abilities, so they
are real characters, but no row here describes them and no deleted map named them. Ichigo's row
is also malformed (`formType` in the `chr_b` column); his real data is in
`Ichigo-Character-Map.md`, one of the two surviving verified maps.

## Caveat on the identity fields, added the same wake they were recovered

Trying to use this table as ground truth for mapping `chr_b.bin`'s fields immediately failed,
and the failure says something about the table rather than about the file.

`classId` sits at record offset `0x0E` as a little-endian u16 for **49 of the 70** rows with a
numeric `chr_b`. For the other 21 it does not — and for **13 of those 21 the `classId` value
does not appear at offset `0x0E` of any record in the file at all**: Allen 321, Fuusuke 435,
Gintoki 349, Kakashi 278, Kenshin 304, Kinnikuman 422, Momotaro 428, Neuro 669 among them.

A field is not 70% of a field. Either the `chr_b` numbers in those rows are wrong, or `classId`
in this table was derived from something other than `chr_b.bin`. Four of the thirteen are rows I
recovered above from deleted maps that carried the header **`Map status: STUB`** — so their
identity values may have been inferred rather than read, and they arrived in this table looking
exactly as solid as the other 59.

**So: treat the `charId` / `classId` / `jpower` columns as unverified until someone pins those
fields' offsets in `chr_b.bin` directly.** The `chr_b` index numbers themselves are better
supported — Edajima at 67 is confirmed three independent ways — and the on-disk ability window at
record `+0x03` is independent of this table entirely
[`jus-ondisk-ability-list-at-chrb-0x03-kfc`].

This is the third extraction artifact found in this one file today, after `File` in the `chr_b`
column and a regex that lifted "tier-2 modifier" out of prose as a `tier` value. All three read
as plausible data.
