# Koma System — Design Brief

Decoded from the shipped game and cross-checked against live play. Where something's still unknown, it says so.

See also: `../research/Koma-System-Observed-Behavior.md` (evidence + confidence), `Koma-Deckbuilder-UX-Spec.md` (screen-by-screen UI), `../research/Helper-Passives-Catalog.md` (all 42 helper passives).

## One-sentence pitch

You don't pick a fighter — you build a **manga page**, and the page *is* your team.

## Core loop

A deck is a **4-row × 5-column grid = 20 cells**. You fill it with comic panels ("koma"). Each panel is one character at one size, and **size decides role**:

| Size | Type | Role |
|---|---|---|
| 1 cell | **Helper** | Not playable. Emits one passive buff to a fighter you aim it at. |
| 2–3 cells | **Support** | Called in for a single assist action. |
| 4–8 cells | **Battle** | A fully playable fighter. |

A 1-cell Naruto is a passive. A 4-cell Naruto is a fighter. An 8-cell Naruto is a stronger fighter eating 8 of your 20 cells.

**Grid space is the only currency.** No mana, no deck points, no cost stat. A panel costs exactly its area. Every tradeoff is spatial — packing puzzle, not arithmetic.

**A legal deck needs at least one Battle, one Support, one Helper.** Players get 8 deck slots.

## What's in the game

| Thing | Count |
|---|---|
| Characters | **312** |
| Panels total | **890** |
| Playable (Battle) panels | 206 |
| Support panels | 372 |
| Helper panels | **312** — exactly one per character |
| Manga series represented | 42 |
| Distinct panel shapes | 66 |
| Helper passive effects | 42 |
| Total named abilities | 57 |

Every character has exactly one Helper panel. Only some grow into Support and Battle sizes. 120 characters are Helper-only; the biggest movesets run to 10 panels.

## Shapes

Shapes are a **hand-picked set of 66**, not every possible polyomino (533 exist for sizes 1–8). Per size:

| Size | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Shapes | 1 | 2 | 6 | 12 | 14 | 14 | 13 | 4 |

Two things worth noting:

- **Variety peaks at sizes 5–6 and collapses at 8** (only 4 shapes). Big panels are deliberately hard to place.
- **The same character at the same size can come in two different shapes** — a real choice, not cosmetic. See natures below.

Full visual catalog in the appendix.

## Natures and the type triangle

Four values: **力 Power**, **知 Knowledge**, **笑 Laughter**, **なし Neutral**.

The three real natures form a rock-paper-scissors loop:

```
Power ──beats──▶ Knowledge ──beats──▶ Laughter ──beats──▶ Power
```

Neutral sits outside. **Every Helper is Neutral** — natures start at size 2.

Distribution across all 890 panels: **Power 226, Knowledge 183, Laughter 169, Neutral 312.** Balanced on purpose.

### The interesting part

A character's nature is normally fixed, but **32 Battle panels override it.** These alternate-nature variants have the same character and size but a *different shape* and *different nature*.

Naruto has two 4-cell panels: one Power (vertical bar) and one Laughter (squarer shape). Same fighter, same moves, same HP — different nature, different footprint. The player trades **grid geometry against type matchup**: a genuine two-axis decision and the sharpest lever in the system.

For balance: the alternate panel's **special attacks still use the character's base nature**. Only the panel's own nature changes for matchups and deck bonuses.

**Unknown:** the damage multiplier for a favourable matchup. Estimated around ×1.5, unconfirmed — hardcoded in the damage path, not in any data file.

## Health

HP is called **Ｊ魂 ("J-soul")**. The SP gauge is **必殺魂**.

`max HP = base HP for that character at that size + 8 per active bonus source`

- **Base HP is a per-character, per-size table**, not a formula. Naruto runs 144 / 160 / 176 / 192 / 208 across sizes 4→8.
- HP is quantised to **multiples of 8**.
- Bigger panels always have more HP — size buys durability and power.
- Full curves for all 74 playable characters: `../research/findings/hp-all-74-characters.md`.

### Bonuses

| Source | Effect | Stacks? |
|---|---|---|
| **Leader** sticker | +8 HP | yes |
| **Relationship** adjacency | +8 HP each, up to 3 | yes |
| **L / R** stickers | **no bonus** | — |

Four sources max → **+32 HP** cap. The game marks this `※複数有効` ("multiple instances are effective"), so stacking is intentional.

The engine clamps max HP at **256**. Highest base HP is 224, and `224 + 32 = 256` exactly — the ceiling matches what the data can produce, suggesting it was derived, not guessed.

### Relationships

Every Battle character has exactly **3 related characters** — sometimes same-series, sometimes cross-series by shared theme or archetype. Place one **adjacent** to the fighter: chime, sparkle, **+8 HP**.

This is a third optimisation axis on top of size and shape: area, legality, *and* neighbour pairs. It's also the mechanic rewarding series knowledge — exactly right for a Jump crossover game.

**Unknown:** the full relationship table hasn't been decoded. We can't list every trio yet.

## Stickers

- **Leader** — Battle panels only. Who you start as. Grants +8 HP.
- **L / R** — Battle or Support. Binds a panel to a shoulder button for quick swaps, dream attacks, or support calls. **No stat bonus** — pure convenience.

## Helpers: the aiming mechanic

Each of the 312 Helper panels carries exactly **one** of 42 passive effects. When placed, you set a **facing** (up/down/left/right) that picks **which fighter receives the buff**.

Helpers are directional emitters. Placement is a real spatial puzzle, not a leftover-cell dump. This is the most underrated mechanic in the system — handle with care in any redesign.

The 42 effects group into families:

| Family | Count | Examples |
|---|---|---|
| Mobility | 3 | Triple Jump, Wall Jump, Air Dash |
| Status immunity | 10 | one per status effect |
| Damage resistance | 3 | resist blunt / slash / special |
| Damage weakness | 2 | **take more** blunt / slash — negative passives exist |
| Guarding | 3 | auto-guard using SP, guard strength up |
| Health | 5 | max HP up, regen, more HP from food |
| SP gain triggers | 15 | on multi-hit, on just-guard, on KO, on low HP, … |
| Perception / misc | 1+ | see invisible characters |

Two surprises:

- **Negative passives ship in the game.** Two Helpers make their target *more* vulnerable, and one drains SP. Real, deliberate downsides on otherwise good characters.
- **SP-gain is by far the largest family** (15 of 42). Build identity lives in how you generate special meter, not in raw stats.

**Unknown:** whether facing hits one adjacent fighter or a whole row/column, and how two Helpers aimed at the same fighter interact.

## Status effects

Ten total, each with a dedicated immunity Helper:

Shock · Freeze · Burn · Confusion · Poison · Judgment · Paralysis · Blindness · Speed-Down · Battle/Support Seal

Damage is also typed by **attack class** — blunt (punches/kicks), slash (blades), special — with separate resistances and weaknesses per class.

## File map

All paths under `jus_files/ripped_jus_files/bin/`.

| File | Contents |
|---|---|
| `koma.bin` | The panel table. 890 records × 12 bytes: character, series, ordinal, type, ability id, shape, flags |
| `komatxt.bin` | Panel display names, 890 entries — **per panel**, so a character can rename at larger sizes (Naruto becomes ナルト（九尾） at sizes 7–8) |
| `kshape.bin` | The 66 shapes. Each is a 20-byte occupancy map over the 4×5 grid — literally the panel's footprint |
| `chr_b.bin` | 74 playable characters × 60 bytes: base nature, the per-size HP array, low-HP threshold percentages |
| `chr_s.bin` | 193 support entries × 20 bytes, including per-size nature slots |
| `ability.bin` | 57 abilities × 4 bytes, with magnitudes (`+8` HP, `+1` SP, …) |
| `ability_t.bin` | Ability names and descriptions (Japanese, Shift-JIS) |
| `koma.aar` | Panel artwork, one entry per panel |
| `piece.bin` | Not yet decoded — grouped by series |

Panel **size** isn't stored as a number — it's the count of occupied cells in the shape. `kshape` groups are ordered so group *g* holds all size *g+1* shapes.

Panel **nature** isn't stored directly. A nibble in the panel record holds an override; a sentinel value means "use the character's base nature."

`scripts/analysis/dump_koma.py` dumps every panel with size, type, shape and resolved nature.

## Still unknown

Ranked by design impact:

1. **The nature matchup multiplier.** Estimated ×1.5, unconfirmed, hardcoded in the damage path.
2. **What Helper facing actually covers** — one neighbour or a line.
3. **Deck-level nature bonuses.** Older notes mention a whole-deck effect; three suggestively named abilities (友情 Friendship / 努力 Effort / 勝利 Victory — Jump's three principles) exist, but no formula found.
4. **The relationship table** — we know each fighter has 3, not yet which 3 for everyone.
5. **Whether unlocks gate shapes** as well as characters and sizes.
6. How Helper passives stack when aimed at the same fighter.

## If you're redesigning this, keep these

The four load-bearing pieces:

1. **Area is the only cost.** Any other cost model turns this into a spreadsheet.
2. **Size changes role, not just power** — 1 cell is a passive, 4 is a fighter. That's what makes spending 8 cells feel dramatic.
3. **Same character, same size, different shape *and* nature.** Two axes in one choice.
4. **Helper facing.** Directional buffs turn leftover cells into a placement problem.

Things you could change safely: the specific 66 shapes, the 42 passive list, the exact HP curves, and the 8 deck slots.

---

## Appendix: all 66 shapes

`#` = occupied cell, shown top-left-aligned in the 5-wide grid. `#N` is the shape id within its size group; the number in brackets is how many panels in the game use that shape.

**Size 1** — 1 shapes defined, 1 used

```
#0 (312)
#....   
```

**Size 2** — 2 shapes defined, 2 used

```
#0 (136)  #1 ( 52)
##...     #....   
          #....   
```

**Size 3** — 6 shapes defined, 6 used

```
#0 ( 41)  #1 ( 35)  #2 ( 35)  #3 ( 17)  #4 ( 15)
###..     #....     ##...     .#...     #....   
          #....     .#...     ##...     ##...   
          #....                                 
```
```
#5 ( 41)
##...   
#....   
```

**Size 4** — 12 shapes defined, 12 used

```
#0 ( 34)  #1 (  3)  #2 (  9)  #3 (  2)  #4 (  5)
##...     ###..     #....     ##...     ###..   
##...     #....     #....     .#...     .#...   
                    #....     .#...             
                    #....                       
```
```
#5 (  1)  #6 (  1)  #7 (  1)  #8 (  2)  #9 (  2)
#....     ##...     .##..     #....     .#...   
#....     #....     ##...     ##...     ###..   
##...     #....               #....             
```
```
#10(  1)  #11(  1)
##...     ####.   
.##..             
```

**Size 5** — 14 shapes defined, 13 used

```
#0 ( 10)  #1 ( 14)  #2 ( 12)  #3 (  8)  #4 (  1)
##...     ###..     ###..     .##..     ###..   
##...     ##...     .##..     ###..     #.#..   
.#...                                           
```
```
#5 (  4)  #6 (  2)  #7 (  3)  #8 (  0)  #9 (  3)
##...     #.#..     .#...     .##..     #....   
##...     ###..     ##...     .#...     ##...   
#....               ##...     ##...     ##...   
```
```
#10(  1)  #11(  1)  #12(  1)  #13(  1)
##...     #####     .#...     ##...   
.#...               .#...     ###..   
.#...               ###..             
.#...                                 
```

**Size 6** — 14 shapes defined, 14 used

```
#0 ( 25)  #1 ( 17)  #2 (  1)  #3 (  1)  #4 (  1)
###..     ##...     ##...     #....     .##..   
###..     ##...     ##...     ##...     .#...   
          ##...     #....     ###..     ###..   
                    #....                       
```
```
#5 (  1)  #6 (  1)  #7 (  1)  #8 (  1)  #9 (  1)
###..     .###.     ##...     ...#.     .#...   
.###.     ###..     ###..     #####     ##...   
                    .#...               ##...   
                                        .#...   
```
```
#10(  1)  #11(  2)  #12(  1)  #13(  1)
.#...     ###..     ###..     ..#..   
###..     .##..     .##..     .##..   
##...     ..#..     .#...     ###..   
```

**Size 7** — 13 shapes defined, 12 used

```
#0 (  2)  #1 (  2)  #2 (  0)  #3 (  1)  #4 (  1)
.#...     ###..     ##...     ####.     #....   
###..     ###..     ###..     ###..     ##...   
###..     ..#..     .##..               ####.   
```
```
#5 (  1)  #6 (  2)  #7 (  1)  #8 (  1)  #9 (  2)
###..     ####.     .###.     #....     ##...   
.##..     .###.     ####.     ###..     ##...   
.##..                         ###..     ##...   
                                        #....   
```
```
#10(  1)  #11(  1)  #12(  1)
##...     ###..     ###..   
##...     ###..     ###..   
##...     #....     .#...   
.#...                       
```

**Size 8** — 4 shapes defined, 4 used

```
#0 (  6)  #1 (  1)  #2 (  4)  #3 (  1)
##...     ###..     ####.     ##...   
##...     ###..     ####.     ###..   
##...     #.#..               ###..   
##...                                 
```
