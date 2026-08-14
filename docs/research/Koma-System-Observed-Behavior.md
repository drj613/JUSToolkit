# Koma System — Observed Behavior

**Read this before any K2/K3/K4 task.** Source: live play session on melonDS 1.1, walked through by the project owner. 25 screenshots in `docs/research/assets/koma-ui/`.

## Evidence tier

Everything here was **OBSERVED** from a running game — it outranks disassembly-confirmed data because it's what the code actually does. But it tells you nothing about byte layout. Use it as the oracle to check decodes against, never as proof of where a field lives.

Designer-facing version: `docs/design/Koma-Deckbuilder-UX-Spec.md`.

## The nature system: 4 values

K1 flagged "nature/color system — zero evidence" as the biggest gap. Now filled at the behavior level.

**Natures: 力 Power, 知 Knowledge, 笑 Laughter, なし Neutral.**

Type triangle — each beats the next, wrapping around:

```
Power ──▶ Knowledge ──▶ Laughter ──▶ Power     (なし Neutral sits outside)
```

The filter UI shows exactly these four ([shot](assets/koma-ui/13-filter-nature.png)). So nature is a **2-bit / 4-value enum**, not a color index into something bigger.

This kills the old `Deck-System.md` guess that natures are per-character. They're **per-panel**: the same character at the same size can have different natures.

## Falsifiable predictions for K2

The whole point of this doc. Every decode must pass these checks.

1. **Nature is a 4-value enum.** Find a field with exactly 4 distinct values across all 890 records. Candidates from K1: bytes `0x6`, `0x7`, `0xA`, `0xB`, or low bits of the `0x2` u16.
2. **Every 1-cell panel is なし.** All observed helpers were Neutral. So for all records where size == 1, the nature field should hold one constant (probably 0 or 3). This joint constraint ties size and nature together and should identify both fields at once.
3. **Type is derived, not stored.** バトル = 4–8 cells, サポート = 2–3, ヘルプア = 1. Confirmed across every row observed. If a field has 3 values, suspect it's a cached type — check it against size first.
4. **Size range is 1–8.** The size filter shows exactly 1–8 ([shot](assets/koma-ui/10-filter-size.png)). A field with 8 distinct values is your size candidate. Size may not be stored at all — it's derivable from `kshape.bin` geometry.
5. **Shape count per size is small and curated.** The shape filter for size 5 showed **13** options ([shot](assets/koma-ui/11-filter-shape-size5.png)) — counted from a screenshot, so ±1. Free pentominoes number 12, so the game uses roughly the mathematical set, not all fixed orientations.

   This makes `kshape.bin` add up. At 1.6 KB and `0x14` (20) bytes per record, it holds ~**81 shapes total**. All free polyominoes for sizes 1–8 would be 533 — so 81 means a **hand-picked set**, which explains the `(group, element)` indexing (`KShapeGroupId` at `0x8`, `KShapeElementId` at `0x9`) instead of a flat ID. **Prediction: group ≈ size, element ≈ which shape within that size.** If true, size is recoverable from byte `0x8` and needs no separate field.
6. **The 43-entry name table is series, not characters.** `Koma.NameTable` has 43 entries; `nameIdx` is at `0x4`. The series filter shows ~40 emblems ([shot](assets/koma-ui/08-filter-series.png)). So `nameIdx` (the doc's "letters"/LKN) is a **series index**, and `nameNum` at `0x5` is the character's slot within that series. This retires the `letters=1` → "Eyeshield 21?" question from `Deck-System.md`: the observed series popup was labelled アイシールド２１.
7. **Battle panels need 3 relationship IDs.** Every battle panel shows exactly 3 related characters. That doesn't fit in the 6 unknown bytes of a 12-byte record alongside everything else. So relationships live in a **separate table** — `piece.bin` (35 KB, still unopened) is the prime suspect.

## The Naruto reference table

Read directly from the panel browser ([shot](assets/koma-ui/14-view1-grid-naruto-list.png)). **Any candidate decode must reproduce this exactly.** It's the best test case in the game because rows 4 and 5 hold size constant while varying nature and shape.

| Size | Type | Nature | Name | Notes |
|---|---|---|---|---|
| 1 | Helper | なし | ナルト | |
| 2 | Support | 笑 | ナルト | ability ハーレムの術 |
| 3 | Support | 力 | ナルト | |
| 4 | Battle | 力 | ナルト | vertical-bar shape; passive 忍道; specials 螺旋丸 / うずまきナルト連弾 |
| 4 | Battle | 笑 | ナルト | **same size, different shape + nature** |
| 5 | Battle | 力 | ナルト | |
| 6 | Battle | 力 | ナルト | |
| 7 | Battle | 力 | ナルト（九尾） | Nine-Tails — *different name string* |
| 8 | Battle | 力 | ナルト（九尾） | |

Two things to exploit:

- The **4力 / 4笑 pair** isolates nature from size. Find two records with identical size and `nameIdx`/`nameNum` but different values in one candidate byte — that byte is nature. This single query should crack it.
- **Sizes 7–8 carry a different name string** (ナルト（九尾）). So either `nameNum` differs, or names come from `komatxt.bin` per-panel rather than per-character. Either way it's a distinguishing test.

Naruto's 3 relationships: 自来也 Jiraiya, 我愛羅 Gaara, サクラ Sakura. All same-series here, but cross-series pairings exist based on shared theme/archetype.

## Deck rules and structure (for K3)

- Grid is **4 rows × 5 columns = 20 cells**. Panels cost their own area; no separate currency.
- **A legal deck needs ≥1 battle, ≥1 support, and ≥1 helper.** Expect a validator in the deckmake overlay that counts by type.
- The deck-select screen shows per-deck **B / S / H** counters ([shot](assets/koma-ui/02-deck-select-existing.png)), so those counts are stored per deck or recomputed on entry. Existing RAM notes give 8 deck slots (index 0–7 at `0x020AFEB4`), matching the 7 rows + `NEW` observed.
- **Stickers**: Leader (battle panels only), plus L and R (battle or support). L/R bind a panel to a shoulder button — character swap for battle, assist call for support. Existing notes have leader state at `0x020A2289`, `0x020A20F6`, and `0x020A4368`; **L and R bindings are two more per-deck fields nobody has located yet.**
- **Helper facing**: most 1-cell helpers need a direction (up/down/left/right) after placement ([shot](assets/koma-ui/24-helper-awaiting-direction.png)). That's a **2-bit per-placed-panel field in deck save data**, separate from the koma ID. Worth hunting in `0x020A0C00`–`0x020A1000`. Note "most", not all — so there's a per-koma flag for whether facing is required.
- **Relationship adjacency**: placing a related character next to a battle panel triggers a chime + sparkle and grants **extra HP**. The deck validator also runs a neighbour check. The owner recalls the internal term being something like **"j soul"** — worth a `strings` sweep, but treat the name as unverified.

## Open questions

- What helper **direction** mechanically does.
- Nature triangle **magnitude** — the damage/defence numbers behind Power-beats-Knowledge.
- Whether the relationship HP bonus stacks across all 3.
- The HP readout showed `144` for 4-koma Naruto alone, then `144/152` with an L sticker ([shot](assets/koma-ui/22-sticker-l-placed-hp-144-152.png)). Two numbers, meaning unknown — possibly current total vs. maximum.
- Deck-level nature bonuses. `Deck-System.md` mentions "+1 SP helpers affect the whole deck" and nature-driven bonuses; no formula found, nothing observed this session.
- Whether unlocks gate shapes as well as characters and sizes.

## Revised K2 plan

1. **Do prediction 5 first.** Read `DtxCommands.KShapeSprites` and settle `kshape.bin`. If group ≈ size, you get size and shape for free and the search shrinks.
2. Dump all 890 records to JSON (no tool for this yet — K1 confirmed the CLI only emits PNGs). Histogram every byte.
3. Run the **4力/4笑 Naruto query** — same size, same character, differing byte = nature.
4. Verify prediction 2 (all size-1 panels share one nature value) as cross-check.
5. Open `piece.bin` looking for the 3-relationships-per-battle-panel table.
