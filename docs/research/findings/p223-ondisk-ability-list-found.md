> ## ⚠️ RETRACTED, THEN UN-RETRACTED THE SAME DAY — read this first
>
> I retracted this entry on finding that the exporter labels record `+0x03` as `charId` and the
> u32 at `+0x04` as `flags` (both true, 74/74). That was an over-correction and it is withdrawn.
> **The loader settles it: `arm9 0x02077768` walks five slots from record `+0x03` — `cmp sb, #5`
> at `0x02077818` — and dispatches all five identically.** Slot 0 is an ability slot whatever the
> exporter calls it. Claim: [`jus-ondisk-ability-list-at-chrb-0x03-kfc`].
>
> Everything below stands, and five of its claims are now confirmed from **instructions** rather
> than from data patterns: five slots, zeros as empty slots (the append primitive at `0x02077A74`
> returns early on `0`), `+0x1A` as the count, `+0x1B..` as the ids, and a capacity of 15.
>
> One claim below is incomplete rather than wrong: "the loader compacts non-zero slots". Some
> slots are **kind 2**, dispatched through a different table, and never become abilities at all.
>
> The mistake worth carrying: reclassifying a field's *name* and reclassifying its *function* are
> different moves. I established the first and asserted the second, with live ability lists
> sitting there to check the second against.

# Loop-Atlas 223 — the on-disk ability list is five sparse bytes at chr_b + 0x03

Claim in beads: [`jus-ondisk-ability-list-at-chrb-0x03-kfc`]. Related:
[`jus-one-routine-assembles-both-u24`], [`jus-base-2-is-jpower-damage1-10-mse`].

The ability list has been missing on disk for the whole campaign. `chr_b.json` doesn't export an ability field, and searching the 60-byte records for Luffy's known `09 19 0C` triple turned up nothing. Both facts are real. The list is still there.

## Where it is

**`chr_b` record + `0x03`, five bytes, sparse.** Zeros are empty slots, not terminators.

```
Luffy is chr_b record 12
record 12 + 0x03 .. + 0x07  =  09 19 00 00 0C   ->  ids 9, 25, 12
runtime's live list          =  [9, 25, 12, 14]
```

## Why the search missed it

Luffy's on-disk bytes read `09 19 00 00 0C` — a two-byte zero gap splits the triple. A contiguous search for `09 19 0C` can't match that. 25 of 74 records have a zero inside their non-zero span, so contiguous matching fails on a third of the file.

This also re-confirms the standing "no terminator convention" note from a new angle: a reader must scan all five slots, not stop at the first zero.

## Six checks (one decisive)

1. Luffy's window holds exactly his known triple, in order.
2. Only **2 of 74** records contain all three of `09`/`19`/`0C` anywhere in their `0x3C` bytes. One is record 12.
3. Every non-zero byte in the window is a valid ability id. `ability.bin` is 228 bytes of 4-byte entries — 57 abilities, ids `0..56`. Across all 74 records, **0 of 370** window bytes are non-zero and out of range. Control window `+0x08..+0x0C`: **154 of 370** out of range, max byte 255.
4. Slot occupancy is 0, 2, 3, or 4 — **never 1, never 5**. A field of small incidental values would produce both.
5. **Decisive.** Exactly four records have no abilities: **70, 71, 72, 73**. The handoff independently identifies `chr_b` records 70–73 as the unselectable **Debug series** — established from deck-building selectability, not bytes. The window predicts which records aren't real characters and gets all four right.
6. The distribution looks like a catalogue, not noise: 45 of 57 ids appear, the most common showing up 7–10 times across the roster.

## What the loader does

Luffy has three abilities on disk but four at runtime. The extra is `0x0E` (14). The loader compacts non-zero slots into `char+0x1B`, writes the count at `char+0x1A`, and appends `0x0E` at runtime.

This explains the id the handoff flagged as present in Luffy's live list but absent from his record. It's a runtime addition, not a data field. What triggers the addition is still unknown.

## One thing worth its own look

**Id 11 is carried by no character on disk.** The Japanese bitset names give `11` = 打撃弱点, blunt weakness — the add-side counterpart of `9` = 打撃耐性ＵＰ. A weakness ability exists in the catalogue, is wired into the damage path as bit 12 [`jus-bit5-is-ability-10-rxl`], and nobody has it. Ids 22, 33, 34, 36, 37, and 49–53 are also unused.

## No codex pass, deliberately

The strongest check is already cross-representational: a byte window predicting which four records are the Debug series, where "Debug series" was established from selectability. Running codex on the same bytes would be one artifact read twice — the thing I keep telling the runtime seat doesn't count.

## Provenance

Static only. `jus_files/ripped_jus_files/bin/chr_b.bin` (4440 bytes = 74 × `0x3C`) and `ability.bin` (228 bytes = 57 × 4); `docs/confirmed-facts/characters/character-index.md` for Luffy's record number; the shutdown handoff for the Debug series and for Luffy's known ids.
