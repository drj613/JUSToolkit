# Koma System — Observed Behavior

**Read before any K2/K3/K4 task.** Source: live play on melonDS 1.1, walked through by the project owner. 25 screenshots in `docs/research/assets/koma-ui/`.

## Evidence tier

Everything here comes from a running game — it beats disassembly because it's what the code actually does. But it says nothing about byte layout. Use it to verify decodes, not to locate fields.

Designer-facing version: `docs/design/Koma-Deckbuilder-UX-Spec.md`.

## The nature system: 4 values

K1's biggest gap was "nature/color system — zero evidence." Now filled at the behavior level.

**Natures: 力 Power, 知 Knowledge, 笑 Laughter, なし Neutral.**

Type triangle — each beats the next, wrapping:

```
Power ──▶ Knowledge ──▶ Laughter ──▶ Power     (なし Neutral sits outside)
```

The filter UI shows exactly these four ([shot](assets/koma-ui/13-filter-nature.png)). Nature is a **2-bit / 4-value enum**, not a color index into something bigger.

This kills the old `Deck-System.md` guess that natures are per-character. They're **per-panel**: the same character at the same size can have different natures.

## Falsifiable predictions for K2

Every decode must pass these checks.

1. **Nature is a 4-value enum.** Find a field with exactly 4 distinct values across all 890 records. Candidates from K1: bytes `0x6`, `0x7`, `0xA`, `0xB`, or low bits of the `0x2` u16.
2. **Every 1-cell panel is なし.** All observed helpers were Neutral. So for all records where size == 1, the nature field should hold one constant (probably 0 or 3). This joint constraint ties size and nature together and should identify both fields at once.
3. **Type is derived, not stored.** バトル = 4–8 cells, サポート = 2–3, ヘルプア = 1. Confirmed across every observed row. If a field has 3 values, suspect it's cached type — check it against size first.
4. **Size range is 1–8.** The size filter shows exactly 1–8 ([shot](assets/koma-ui/10-filter-size.png)). A field with 8 distinct values is your size candidate. Size may not be stored at all — it's derivable from `kshape.bin` geometry.
5. **Shape count per size is small and curated.** The shape filter for size 5 showed **13** options ([shot](assets/koma-ui/11-filter-shape-size5.png)) — counted from a screenshot, so ±1. Free pentominoes number 12, so the game uses roughly the mathematical set, not all fixed orientations.

   `kshape.bin` adds up: 1.6 KB at `0x14` (20) bytes per record = ~**81 shapes total**. All free polyominoes for sizes 1–8 would be 533, so 81 means a **hand-picked set**. That explains the `(group, element)` indexing (`KShapeGroupId` at `0x8`, `KShapeElementId` at `0x9`) instead of a flat ID. **Prediction: group ≈ size, element ≈ which shape within that size.** If true, size is recoverable from byte `0x8` with no separate field needed.
6. **The 43-entry name table is series, not characters.** `Koma.NameTable` has 43 entries; `nameIdx` is at `0x4`. The series filter shows ~40 emblems ([shot](assets/koma-ui/08-filter-series.png)). So `nameIdx` ("letters"/LKN) is a **series index**, and `nameNum` at `0x5` is the character's slot within that series. This retires the `letters=1` → "Eyeshield 21?" question from `Deck-System.md`: the observed series popup was labelled アイシールド２１.
7. **Battle panels need 3 relationship IDs.** Every battle panel shows exactly 3 related characters. That doesn't fit in the 6 unknown bytes of a 12-byte record alongside everything else, so relationships live in a **separate table** — `piece.bin` (35 KB, still unopened) is the prime suspect.

## The Naruto reference table

Read directly from the panel browser ([shot](assets/koma-ui/14-view1-grid-naruto-list.png)). **Any candidate decode must reproduce this exactly.** Rows 4 and 5 are especially useful — same size, different nature and shape.

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

- The **4力 / 4笑 pair** isolates nature from size. Find two records with identical size and `nameIdx`/`nameNum` but a different value in one byte — that byte is nature. This single query should crack it.
- **Sizes 7–8 use a different name string** (ナルト（九尾）). Either `nameNum` differs or names come from `komatxt.bin` per-panel rather than per-character. Either way it's a distinguishing test.

Naruto's 3 relationships: 自来也 Jiraiya, 我愛羅 Gaara, サクラ Sakura. All same-series here, but cross-series pairings exist based on shared theme/archetype.

## Deck rules and structure (for K3)

- Grid is **4 rows × 5 columns = 20 cells**. Panels cost their own area; no separate currency.
- **A legal deck needs ≥1 battle, ≥1 support, and ≥1 helper.** Expect a validator in the deckmake overlay that counts by type.
- The deck-select screen shows per-deck **B / S / H** counters ([shot](assets/koma-ui/02-deck-select-existing.png)), so those counts are stored or recomputed on entry. Existing RAM notes give 8 deck slots (index 0–7 at `0x020AFEB4`), matching the 7 rows + `NEW` observed.
- **Stickers**: Leader (battle panels only), plus L and R (battle or support). L/R bind a panel to a shoulder button — character swap for battle, assist call for support. Existing notes have leader state at `0x020A2289`, `0x020A20F6`, and `0x020A4368`; **L and R bindings are two more per-deck fields nobody has located yet.**
- **Helper facing**: most 1-cell helpers need a direction (up/down/left/right) after placement ([shot](assets/koma-ui/24-helper-awaiting-direction.png)). That's a **2-bit per-placed-panel field in deck save data**, separate from the koma ID. Worth hunting in `0x020A0C00`–`0x020A1000`. Note "most", not all — so there's a per-koma flag for whether facing is required.
- **Relationship adjacency**: placing a related character next to a battle panel triggers a chime + sparkle and grants **extra HP**. The deck validator also runs a neighbour check. The owner recalls the internal term being something like **"j soul"** — worth a `strings` sweep, but treat the name as unverified.

## Answered since first draft (owner-supplied, 2026-08-14)

- **Helper direction — ANSWERED.** Every 1-cell helper carries exactly one passive, and the facing picks **which battle character receives it**. Helpers are directional buff emitters. Full taxonomy of 42 passives and ~304 characters: `Helper-Passives-Catalog.md`.
- **`144/152` HP readout — ANSWERED and CONFIRMED.** Leader grants **+8 HP** and each relationship adjacency grants **+8 HP**. The readout is **base HP / effective HP after deck bonuses**. The owner has since stacked Leader plus all 3 relationships for **+32 total**, so the four sources are fully additive and this panel reads `144/176` at max. Formula: `effective = base + 8 × (active bonus sources)`, up to 4 sources.
- **Base HP scales with panel size — CONFIRMED (owner).** Bigger panels of the same character have progressively more HP; 8-koma panels have the most in the game. See the prediction below, because this constrains where HP is stored.
- **L/R stickers grant no bonus.** They only make a panel shoulder-callable: activate a battle character, fire its "dream attack" if already active, or summon a support. The earlier guess that the L sticker changed HP was wrong — the Leader sticker did.
- **Status-effect enum — 10 values, contiguous IDs `0x19`–`0x22`**, already in `Cheat-Code-Analysis.md`: Shock, Freeze, Burn, Confusion, Poison, Judgment, Paralysis, Blindness, Speed-Down, Battle/Support Seal. Directly useful for the combat phase.

## HP scaling — a second field the missing table must hold

Size-scaled HP has the **same structural signature as nature**, and that's the useful part.

From the decoded records (`findings/koma-format-decoded.md`), Naruto's size-4, size-5, and
size-6 panels all share `abilityId = 20` at byte `0x7`. If `abilityId` were the only pointer to
stat data, those three panels would have identical HP. They don't — HP rises with size. And
`koma.bin` has no HP field.

So either:

1. **HP is computed at runtime** as a function of base stats and size, or
2. **There's a per-panel stat table** keyed by koma index, which would also be the natural home
   for nature — the other per-panel value that `koma.bin` doesn't store.

Option 2 is the more interesting lead because it would resolve both gaps at once.

**Falsifiable prediction (SPECULATIVE):** 4-koma Naruto has base HP `144`, and `144 = 4 × 36`.
If HP is `size × k` with a per-character `k`, his size-5 panel reads `180`, size-6 reads `216`,
size-7 `252`, size-8 `288`. Reading any single one of those numbers off the panel-info screen
kills or confirms this in one observation. If the numbers don't fit a clean multiple, HP is
tabulated per panel and option 2 wins.

## Open questions

- Nature triangle **magnitude** — owner guesses ~1.5× damage but is **not** confident. Still SPECULATIVE; needs a damage-formula read or a controlled test.
- Whether the +8 relationship bonus stacks across all 3 relationships (expect `base/base+24` if it does, or `base/base+32` with Leader too).
- Whether passive **magnitudes** are per-passive constants or per-character.
- Whether a helper's facing hits one adjacent battle character or a whole row/column.
- Six ability IDs remain unidentified — see `Helper-Passives-Catalog.md`.
- Deck-level nature bonuses. `Deck-System.md` mentions "+1 SP helpers affect the whole deck" and nature-driven bonuses; no formula found, nothing observed. Ability `0x27`-family SP triggers and "Increase Max Special Gauge by 1" may be what that note was gesturing at.
- Whether unlocks gate shapes as well as characters and sizes.

## Spillover for the combat phase

Three things here are combat-engine leads, not koma leads. Feed them into `Battle-Engine-Map.md` when work flips to phase `combat`:

1. The **10-value status enum** at `0x19`–`0x22`, likely an immunity **bitmask** on the character state struct (one passive covers both Seal types, so they share a bit or a pair).
2. **Damage is classed by attack type** — punch/kick, special, blade — since three separate passives reduce damage per class. Tie to `DamageFlags-Character-Classification.md`.
3. **`+8` is a shared HP constant** used by both Leader and relationship bonuses. Applied twice near HP init — findable via `query.py search-imm 8` scoped to deck/HP setup.

## Revised K2 plan

1. **Do prediction 5 first.** Read `DtxCommands.KShapeSprites` and settle `kshape.bin`. If group ≈ size, you get size and shape for free and the search shrinks.
2. Dump all 890 records to JSON (no tool for this yet — K1 confirmed the CLI only emits PNGs). Histogram every byte.
3. Run the **4力/4笑 Naruto query** — same size, same character, differing byte = nature.
4. Verify prediction 2 (all size-1 panels share one nature value) as cross-check.
5. Open `piece.bin` looking for the 3-relationships-per-battle-panel table.
