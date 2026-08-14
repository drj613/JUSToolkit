# Findings: 14 Overlays Extracted; Nature Table Exhaustively Excluded (task K2f)

> ### ⚠️ CORRECTED — see `nature-SOLVED.md`
>
> This doc says the per-koma nature table model is "exhaustively REFUTED." That was **overstated.**
> The searches were sound and their literal conclusion holds — there is no *dedicated* nature table.
> But they only tested dedicated tables (whole-byte, nibble-packed, 2-bit-packed at every offset).
> They never tested **the high nibble of an existing koma field plus a sentinel-and-fallback
> scheme**, which is what the game actually does. Nature is now solved: it lives in the high nibble
> of `koma.bin` byte `+0xB`, with `3` meaning "no override, use the character's base nature."
> The word "exhaustive" claimed more coverage than the method had.

Loop-Atlas iteration 9. Static. New tool: `scripts/analysis/extract_overlays.py`.

**Two results.** Opened a new search space — 11 ARM9 overlays never previously examined. And nature is **not** a per-koma-indexed table anywhere in the ROM binaries. That's now exhaustive, not partial.

## The overlays were a blind spot

The ROM header declares **14 ARM9 overlays**, but only `ov0`, `ov1`, and `ov2` had been disassembled (`jus_files/analysis/disasm/`). The other 11 were never extracted. `scripts/extract_arm9.py` only pulls `arm9.bin` / `arm7.bin`, so every value search so far was blind to ~1.4 MB of code and data.

`scripts/analysis/extract_overlays.py` now extracts all 14. Read-only on the ROM; writes to `jus_files/overlays/` (never `ripped_jus_files/`).

| overlay | RAM address | size | overlay | RAM address | size |
|---|---|---|---|---|---|
| ov00 | `0x0214CD20` | 85760 | ov07 | `0x0214CD20` | 122816 |
| ov01 | `0x0214CD20` | 135456 | ov08 | `0x0214CD20` | 128160 |
| ov02 | `0x0214CD20` | 65152 | ov09 | `0x0214CD20` | 32 |
| ov03 | `0x0214CD20` | 73472 | ov10 | `0x02172A60` | 215264 |
| ov04 | `0x0214CD20` | 86208 | ov11 | `0x02172A60` | 61440 |
| ov05 | `0x0214CD20` | 152928 | ov12 | `0x021AC1C0` | 167776 |
| ov06 | `0x0214CD20` | 154688 | ov13 | `0x021AC1C0` | 32 |

All 14 are **uncompressed** (compress flag 0), so `file_offset = runtime_addr - ram_address` works the same as arm9.

ov00–ov09 all load at **`0x0214CD20`** — they're mutually exclusive, one per game mode. The deck editor lives in one of them, sharing an address with nine others. Any RAM watchpoint in that range only makes sense once you know which overlay is loaded. Full manifest with RAM/ROM offsets: `jus_files/overlays/overlays.json`.

ov10–ov13 load at two other addresses and can coexist with the first group.

## Nature: per-koma table model is exhaustively REFUTED

Built a search with a much tighter constraint than a value histogram. The owner's data gives a hard invariant: **every 1-cell helper panel is なし**, and there are exactly 312 of them at known `koma.bin` indices.

So any table indexed by koma index must satisfy:

1. All 312 helper indices hold one identical value.
2. The 578 non-helper indices hold ≥3 other values, **each appearing ≥50 times** (natures are roughly balanced across 578 support and battle panels).
3. ≥500 of the 578 differ from the helper value.

Searched every byte offset in three encodings (one byte per koma, nibble-packed, 2-bit-packed) across:

- `arm9.bin` (692568 bytes)
- all 26 files in `bin/`
- **all 14 overlays**

**Result: zero candidates.** REFUTED.

An earlier, weaker search using only Naruto's 9-panel nature *pattern* produced 224 matches — all noise. A 9-element equality pattern is far too weak in 2-bit-packed data where only four values exist and chance matches are common. The 312-way invariant is what made the search conclusive.

## Why nature probably doesn't live here at all

Re-reading `Deck-System.md` reframes the problem. Its long-standing note says nature variants **reuse the same battle data**, and special attacks still use the character's *base* nature even on an alternate-nature panel.

That means panel nature is **not a combat property** — it's a deck-building property, used for deck bonuses only. Two consequences:

1. No reason for it to sit near `chr_b` / `chr_s` battle data, where I'd assumed it would be.
2. It only needs to exist wherever the **deck editor and deck-bonus calculation** run — pointing at the deckmake overlay's own data, or at data inside the `.aar` archives that only that mode loads.

This also explains why natures are per-panel while every other per-panel property I've decoded (size, shape, type, ability, name) lives in `koma.bin` or `komatxt.bin`. Nature may simply not be part of the koma record set.

## Remaining candidate locations, ranked

1. **Inside the `.aar` archives.** `InfoDeck.aar` (570 KB, ~130 entries) is the koma-browser data with a working parser (`Binary2InfoDeckDeck`) that reads 10 string "pages" per entry. Its *non-string* fields have never been examined. `deckmake.aar` and `Deck.aar` likewise.
2. **The deckmake overlay's static data** — now extractable but not yet identified. The 578-entry compacted-table variant is the natural next scan.
3. **Computed at load time.** The harness session proved resistance is precomputed when a character loads rather than read at damage time; nature may work the same way, with no lookup table in any file — only disassembly of the load path would find it.

## Methodological note: the group is the signature

My first nature search used Naruto's 9-panel nature *pattern* (positions 1 and 4 equal, positions 2/3/5/6/7/8 equal, groups differ). It returned **224 candidates across all files** — all noise. In 2-bit-packed data with only four values, a 9-element equality pattern matches by chance constantly.

The 312-way invariant — *every* helper must hold the same value — dropped it to zero with no ambiguity. **A wide invariant beats a clever pattern.**

The harness session found the same thing scanning RAM for the battle struct: a single 0x50-byte slot matched **1167** times in 4 MB, but requiring four consecutive slots at stride 0x50 made the hit unique. Same principle, opposite direction.

## The compacted-table variant is refuted too

A follow-up scan tested a **compacted 578-entry table** (supports and battles only, in koma-index
order) — a model the base-offset scan above would miss, since that one assumes indices `0..889`.
Criteria: exactly 3–4 distinct values in a 578-byte window, each appearing ≥80 times. `u8`
encoding only, since nibble and 2-bit are noise-dominated for the reason given above.

Searched all 26 `bin/` files, all 14 overlays, and `arm9.bin`. **Zero candidates.** REFUTED.

Implementation note: the first attempt was O(offsets × 578) in Python and got killed before
finishing. A **rolling histogram** — add the entering byte, drop the leaving one — makes it O(n)
and it completes in seconds. Worth reaching for on any sliding-window scan over these files.


## Predictions status

| ID | Prediction | Verdict |
|---|---|---|
| P1 | Nature is a 4-value enum in `koma.bin` | **REFUTED** (iteration 4) |
| P1b | Nature is a per-koma-indexed table somewhere in the ROM binaries | **REFUTED** — exhaustive, 3 encodings × every offset × arm9 + 26 bin files + 14 overlays |
| P1c | Nature is a compacted 578-entry table (non-helpers only) | **REFUTED** — same corpus, `u8` encoding |

## Note for the harness session

The overlay extraction should be folded into `scripts/extract_arm9.py` so there's one tool. More importantly: **ov00–ov09 all load at `0x0214CD20`**, so a RAM address in that window means different things in different modes. Any watchpoint spec should say which overlay is expected to be resident, or it'll be ambiguous.
