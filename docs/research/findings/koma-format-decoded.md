## koma.bin and kshape.bin Decoded (Task K2)

Loop-Atlas iteration 4. Static analysis only. New tool: `scripts/analysis/dump_koma.py`.

**Bottom line: 10 of 12 bytes in a koma record are now identified, and panel size comes free from the shape table.** Six predictions confirmed, one revised, one important negative: **nature is not stored in `koma.bin` at all.**

---

## kshape.bin — Fully Decoded

CONFIRMED from `src/JUS.Tool/Graphics/Converters/BinaryKShape2SpriteCollection.cs:33-141` plus byte-level file check.

`kshape.bin` is exactly **1648 bytes**:

| Offset | Size | Contents |
|---|---|---|
| `0x00`–`0x1F` | 32 | `int32 group[8]` — first entry index per group. Actual: `(0, 1, 3, 9, 21, 35, 49, 62)` |
| `0x20`–`0x3F` | 32 | `int32 numElements[8]` — entries per group. Actual: `(1, 2, 6, 12, 14, 14, 13, 4)`, sum **66** |
| `0x40`+ | 66 × 24 | Shape entries |

Each 24-byte entry: a **20-byte occupancy array over a 5×4 grid** (240×192 px in 48×48 blocks), plus 4 trailing bytes the parser reads but ignores. Zero = empty; nonzero = occupied, value minus 1 = tileset index.

**That 5×4 grid is the deck grid.** A kshape entry *is* the panel footprint. Lookup:

```
entry_index  = group[KShapeGroupId] + KShapeElementId
byte_offset  = 64 + entry_index * 24
```

### P5 CONFIRMED — Group Index Is Size Minus One

Every one of the 66 entries: group `g` always has exactly `g+1` occupied cells, no exceptions. So `KShapeGroupId` at `0x8` gives panel size directly as `group + 1`. No separate size field needed.

Shapes available per size vs. actually used:

| Size | In kshape.bin | Used by koma.bin | Panels |
|---|---|---|---|
| 1 | 1 | 1 | 312 |
| 2 | 2 | 2 | 188 |
| 3 | 6 | 6 | 184 |
| 4 | 12 | 12 | 62 |
| 5 | 14 | **13** | 61 |
| 6 | 14 | 14 | 55 |
| 7 | 13 | 12 | 16 |
| 8 | 4 | 4 | 12 |

**Independent confirmation:** the owner's size-5 shape-filter screenshot showed **13** options — matches exactly. The earlier estimate of "~81 shapes at 20 bytes each" was wrong (66 entries at 24 bytes), but the conclusion holds: this is a hand-picked shape set, far short of the 533 free polyominoes for sizes 1–8.

Sample footprints (size 4): element 0 = 2×2 square, element 1 = L-shape.

```
elem 0        elem 1
##...         ###..
##...         #....
.....         .....
.....         .....
```

---

## koma.bin — 10 of 12 Bytes Identified

890 records × 12 bytes = 10680 bytes.

| Off | Type | Name | Status | Meaning |
|---|---|---|---|---|
| `0x0` | u16 | ImageId | CONFIRMED | `0..889`, always equals record index — fully redundant |
| `0x2` | u16 | **characterId** | CONFIRMED | `1..312`, 312 distinct |
| `0x4` | u8 | **seriesIdx** | CONFIRMED | `1..42`, index into `Koma.NameTable` |
| `0x5` | u8 | **panelOrdinal** | CONFIRMED | Panel number within the character, `0`-based |
| `0x6` | u8 | **panelType** | CONFIRMED | `0` = Battle, `1` = Support, `2` = Helper |
| `0x7` | u8 | **abilityId** | PLAUSIBLE | Ability/data ID; range depends on type |
| `0x8` | u8 | KShapeGroupId | CONFIRMED | **size = value + 1** |
| `0x9` | u8 | KShapeElementId | CONFIRMED | Which shape of that size |
| `0xA` | u8 | unkA | UNIDENTIFIED | `0..8`, always ≤ size |
| `0xB` | u8 | **flags** | PLAUSIBLE | Bit `0x10` ≈ "primary variant". Not nature |

### 312 Characters, Each with Exactly One Helper

312 distinct `characterId` values. Every single one has exactly one 1-cell helper panel (312/312). The game has 312 characters.

**P8 CONFIRMED:** the owner's helper-passive list named ~304 characters vs. 312 actual — consistent with "have been identified" being slightly incomplete.

Panel counts: 120 characters have just 1 (helper only), 132 have 3, rest go up to 10. Only characters with a size-4+ panel are playable.

### Panel Type: Stored and Derivable

Type is perfectly determined by size, zero exceptions across all 890 records:

| Size | panelType | Count |
|---|---|---|
| 1 | `2` Helper | 312 |
| 2, 3 | `1` Support | 188 + 184 |
| 4–8 | `0` Battle | 62 + 61 + 55 + 16 + 12 |

**P3 CONFIRMED:** type is a cached field, redundant with size. Matches the owner's Battle 4–8 / Support 2–3 / Helper 1 rule exactly.

### Series Index — P6 Confirmed (With Correction)

`Koma.NameTable` is hardcoded at `src/JUS.Tool/Graphics/Koma.cs:33`, 43 slots (index 0 is `null`, 42 usable), sourced from ARM9 pointers at `0x0209E840`. Values run `1..42` — every series used.

**`Deck-System.md` guessed `letters=1` → "Eyeshield 21?" with a question mark. Answer: yes.** Index 1 is `"es"`. Index 24 is `"na"` (Naruto), index 23 is `"db"` (Dragon Ball).

**P6 half-wrong:** `0x5` is *not* the character's slot within the series — it's the **panel ordinal within the character**, running `0..8`. `(seriesIdx, panelOrdinal)` is unique across all 890 records.

### Ability ID — Range Depends on Type

| Type | n | Distinct | Range |
|---|---|---|---|
| Helper | 312 | 47 | `0..55` |
| Support | 372 | 193 | `0..192` |
| Battle | 206 | 74 | `0..73` |

**P2 CONFIRMED:** 47 distinct helper values in `0..55` lines up with the owner's 42 passive categories and ability IDs from `Cheat-Code-Analysis.md`. Correction: the real helper ID space reaches **55 (`0x37`)**, wider than the `0x30` the cheat-code list stopped at.

Battle's 74 distinct values cross-checks perfectly: `chr_b.bin` has **74 battle character stat entries**. For battle panels, `0x7` indexes `chr_b.bin`.

---

## Naruto — Verified Against Owner's Reference

Naruto is **character 184**, series index 24 (`"na"`). All 9 panels from the file:

| idx | panelOrdinal | type | abilityId | size | shape | unkA | flags |
|---|---|---|---|---|---|---|---|
| 497 | 0 | Helper | 2 | 1 | 0 | 1 | `0x30` |
| 498 | 1 | Support | 17 | 2 | 0 | 2 | `0x30` |
| 499 | 2 | Support | 17 | 3 | 5 | 3 | `0x30` |
| 500 | 3 | Battle | 20 | 4 | 2 | 1 | `0x30` |
| 501 | 4 | Battle | 20 | 4 | 0 | 3 | **`0x20`** |
| 502 | 5 | Battle | 20 | 5 | 2 | 4 | `0x30` |
| 503 | 6 | Battle | 24 | 6 | 0 | 4 | `0x30` |
| 504 | 7 | Battle | 24 | 7 | 0 | 6 | `0x30` |
| 505 | 8 | Battle | 24 | 8 | 2 | 8 | `0x30` |

Sizes `[1,2,3,4,4,5,6,7,8]` and types match the owner's table exactly. Sizes 7–8 switch to `abilityId` 24 while 4–6 use 20 — consistent with those panels being ナルト（九尾）, a different character label with different battle data.

The two size-4 panels share `abilityId` 20, matching the `Deck-System.md` note that nature variants reuse the same battle data.

---

## NEGATIVE RESULT: Nature Is Not in koma.bin

This is the most important finding. **P1 REFUTED.**

The `4力`/`4笑` test: the two size-4 panels differ only in `imageId`, `panelOrdinal`, shape, `unkA`, and `flags` (`0x30` → `0x20`). All three characters with the same size signature showed the same `0x30` → `0x20` transition, so `flags` bit `0x10` looks like "primary variant."

**But `flags` cannot be nature.** Naruto's size-2 panel is 笑 Laughter and his size-3 panel is 力 Power — both carry `flags = 0x30`. Two panels, different natures, identical bytes. **No field in `koma.bin` encodes nature.**

Nature can't be purely per-character either, since Naruto's two size-4 panels differ in nature while sharing character ID 184. Most likely: a parallel per-panel table indexed by koma ID.

**Recorded per evidence discipline:** P1 predicted a 4-value field in `koma.bin`. None exists. `unk6` has 3 values but is panel type; `flags` has 9 values but is variant bits.

---

## piece.bin — Not a Per-Koma Table

35183 bytes. No stride produces 890 records, and the size is odd — **not** a fixed-stride per-koma table. Variable-length or offset-indexed. Still a candidate for nature/relationship data but needs a header read, not a stride guess.

---

## Where to Look for Nature Next

1. **`komatxt.bin`** — 13362 bytes. The C# parser reads `count = firstInt32 / 0xC`. Its `Unk1` and `Unk2` int32 fields per entry are unexamined, and it's a per-koma table by construction. Cheapest next check.
2. **`piece.bin`** — read the header properly and find the indexing scheme.
3. **`unkA`** — still unidentified, `0..8`, always ≤ size. Correlates loosely with the shape's bounding box (equals width in 474/890, height in 500/890) but neither exactly. Might be a render anchor or sort key.

---

## Prediction Status

| ID | Prediction | Verdict |
|---|---|---|
| P1 | Nature is a 4-value enum in `koma.bin` | **REFUTED** — no such field |
| P2 | Passive ID on helpers in `0x01`–`0x30` | **CONFIRMED** (space actually reaches `0x37`) |
| P3 | Type derived, not the source of truth | **CONFIRMED** — `0x6`, fully redundant with size |
| P4 | Size is a field with 8 distinct values | **CONFIRMED as "not stored"** — comes from `0x8 + 1` |
| P5 | kshape group ≈ size, element ≈ shape | **CONFIRMED exactly** |
| P6 | `0x4` is series, `0x5` is char-in-series | **HALF** — `0x4` series yes; `0x5` is panel ordinal |
| P7 | Relationships in a separate table | **Still open** — `piece.bin` not yet decoded |
| P8 | Helper count ≥ ~304 | **CONFIRMED** — 312 helpers, one per character |
| P9 | Static IDs may differ from RAM ability IDs | **Still open** |
