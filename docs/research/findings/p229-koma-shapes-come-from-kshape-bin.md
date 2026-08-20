`kshape.bin` holds the koma shape catalogue, indexed by cell count. Builds on [`jus-koma-shape-is-a-20bit-bitmap-423`]; tracked in [`jus-koma-shapes-come-from-kshape-bin-0j2`].

> **Read the last three sections first.** The record base was wrong for most of this
> document's life. Current: base `0x40`, 20-byte cell map at `+0x00`, bitmap at `+0x14`, grid
> 5 columns x 4 rows. The superseded `0x54` reasoning is kept below for the error it illustrates.

## The file

`jus_files/ripped_jus_files/bin/kshape.bin`, 1648 bytes. It's the only file in `bin/` containing all nine observed masks, each once, at stride `0x18`, in the same order as the RAM array at `0x021AF1B4`:

| mask | file offset | | mask | file offset |
|---|---|---|---|---|
| `0x00421` | `0x0B4` | | `0x00063` | `0x12C` |
| `0x00043` | `0x0CC` | | `0x00027` | `0x144` |
| `0x00062` | `0x0E4` | | `0x08421` | `0x15C` |
| `0x00061` | `0x0FC` | | `0x00047` | `0x18C` |
| `0x00023` | `0x114` | | | |

RAM indices map directly — index 0 → `0x0B4`, 7 → `0x15C`, 9 → `0x18C` — so the RAM array at `0x021AF1B4` corresponds to file offset `0x0B4`, putting file offset 0 at RAM `0x021AF100`.

## Indexed by cell count

The header has two u32 tables:

```
cumulative starts   0, 1, 3, 9, 21, 35, 49, 62
per-class counts    1, 2, 6, 12, 14, 14, 13, 4     sum 66
```

That's 1 monomino, 2 dominoes, 6 trominoes, 12 tetrominoes, 14 pentominoes, 14 hexominoes, 13 heptominoes, 4 octominoes. Every cumulative step checks out. Walking stride `0x18` from base `0x3C` gives 66 records with histogram `{1:2, 2:2, 3:6, 4:12, 5:14, 6:14, 7:13, 8:3}` — exact match for 2–7 cells, off by one at each end.

## Curated subset

Fixed polyominoes run 1, 2, 6, 19, 63 for sizes 1–5. This file has 1, 2, 6, 12, 14. **Sizes 1–3 are complete; 4+ were hand-picked.** The game chose which shapes exist — a design decision, not a derivation, and the kind of fact the koma design brief needs.

## Not pinned

The exact record base isn't settled. It must be `≡ 0x0C mod 0x18` (since `0x0B4` is a known record), and `0x0C`, `0x24`, `0x3C` all produce plausible runs. `0x3C` is the only one giving exactly 66, with 4 trailing bytes — but the histogram being off by one at both ends suggests the true base is one record either side, or the header is 16 words and the stride gets interrupted. The eight-cell class is what to check: the design brief's "an 8-panel Naruto eats 8 of your 20 cells" says the largest class is real, and the header claims four of them.

The five other u32s per record are also unread.

## Why only wide masks discriminate

`0x00062`, `0x00061`, `0x00063`, `0x00023`, and `0x00047` are short values that collide by chance — they also hit `komatxt.bin`, `jpower.bin`, `chr_b.bin`, and `rulemess.bin`. Only `0x00421` and `0x08421` are wide enough to be meaningful, and `kshape.bin` is the sole file carrying both. Reporting the short hits would have looked like corroboration but been noise — the runtime seat made the same point about their overlay search and caught it before publishing.

## Provenance

Static only. `kshape.bin` read as aligned 32-bit words; header read as u32. Cross-checked against the RAM offsets and stride measured live by the runtime seat — two independent artifacts, neither derived from the other.

## WRONG, superseded — my `0x54` reading (kept for the error, not the claim)

> **The base is `0x40`, not `0x54`.** Everything in this section and the two that follow it is
> superseded by "Corrected again" below. `0x54` overruns the file by `0x14` and yields 65.167
> records. It is retained because the *way* it went wrong is the finding: the search space was
> constrained by the assumption under test, so `0x40` could never have been returned. See bead
> `jus-circular-search-constraint-ei5q`. Two words in the original heading did the damage —
> "settled by" — for a test that could not distinguish the candidates.

### The original reasoning, as written

Every record's **popcount must equal its class**, because the header fixes the class of every index:
counts `1,2,6,12,14,14,13,4` expand to classes `[1, 2,2, 3×6, 4×12, 5×14, 6×14, 7×13, 8×4]`. That
converts "which base" from a judgement about which run looks plausible into 65 independent tests.

```
base 0x3C : 7 MISMATCHES at indices 1, 3, 9, 21, 35, 49, 62 — every one a class boundary,
            every one exactly one class low. Those indices ARE the cumulative table.
base 0x54 : 65 of 65, zero mismatches.
```

**And the 66th record is truncated, not missing.** 65 full records end at `0x66C`, leaving 4 bytes
that read `0x00001CE3` — popcount 8, decoding to `##... / ###.. / ###..`. So the file is
`0x54 + 65*0x18 + 4 = 0x670`, exactly its size; the count really is 66; the header's class-8 count of
4 was right; and the `{8:3}` histogram above was the truncation rather than a bad base.

**Correction to the RAM mapping:** file offset 0 maps to **`0x021AF100`**. Mask `0x00421` sits at
file `0x0B4` and RAM `0x021AF1B4`, so the delta is `0x021AF1B4 − 0x0B4`. The mapping does *not* shift
with the record base — it's fixed by an anchor pair, not by where the records begin. With it, the
records from file `0x54` sit at RAM `0x021AF154` onward, `0x618` bytes for a full compare.

**Still open:** whether the RAM copy is the file verbatim or a transform. Four shape words and a
stride agree, and that is all that has been compared. The five trailing u32s per record are
unidentified in both.

## The compare closed it — and it corrected the ov12 boundary model

**1644 bytes identical**: file `0x000..0x66C` against RAM `0x021AF100..0x021AF76C`, header included.
So "the RAM array corresponds to kshape.bin" is the whole file rather than four shape words and a
stride, and the header is loaded rather than synthesised. The five trailing u32s per record are still
unidentified — now a question about the format, not the mapping.

### What sits immediately after it corrects a bigger claim

The runtime seat read 20 bytes past the end at RAM `0x021AF770` and nearly published "kshape.bin is
truncated in the rip" before noticing the bytes decode as ARM code rather than record fields. They're
**ov12's own code**: `arm9_ov12.bin` file offset `0x35B0` holds `E2840014 / E5902000 / E5922038 /
E12FFF32`, and ov12 file `0x35B0` maps to `0x021AC1C0 + 0x35B0 = 0x021AF770` exactly.

**So there is intact ov12 file content `0x11C40` below the `0x021C13B0` boundary.** The model on
[`jus-ov12-boundary-probably-moves-05o`] — 84.5 KB overwritten below, 79.4 KB intact above, one
contiguous split — can't be right as stated.

Better model, and it explains the 59.6% match cleanly: **the ov12 window holds ov12's code and
file-load buffers, interleaved.** kshape.bin loads at `0x021AF100` and ends at `0x021AF770` exactly
where ov12's code resumes — a buffer declared inside the overlay's own range, filled at load time.
The mismatching ~40% is loaded files, not a contiguous overwritten half.

It also explains why a 32-sample scan saw a clean split: samples every ~5 KB land mostly in the large
loaded-data regions and skip short intact code stretches. The scan wasn't wrong, it was
**under-resolved** — and a clean-looking split from sparse sampling is the same shape as the other
tidy-pattern failures in this campaign.

**Unresolved:** their fifth word read `E3A04D48` where the file has `E3A00000`, continuing
`E584003C / E8BD8010` — a coherent epilogue. Four words matching exactly isn't chance, so that range
is certainly ov12's code. Either a transcription slip, a patched word, or a read that started one
word later than recorded.

## `0x02076D00` identified — and it reconciles every reading above

Closed definitionally, from the function rather than from offsets
[`jus-kshape-lookup-identified-a1j`]:

```
0x02076D00  ldr   r1, [pc, #0x24]       -> 0x0214BD80, the chr_b table root global
0x02076D04  ldrsb r2, [r0, #8]          class selector
0x02076D0C  ldrsb r3, [r0, #9]          index within class
0x02076D10  ldr   ip, [r1, #0x38]       the kshape base
0x02076D18  ldr   r1, [ip, r2, lsl #2]  startTable[class] — the cumulative table
0x02076D20  add   r1, r3, r1            flat index = start + sub
0x02076D24  mla   r0, r1, #0x18, ip+0x40
```

A `(class, sub-index)` pair resolves through the cumulative table to a flat record index, records at
stride `0x18` from `ip+0x40`. So the table found by pattern above — `0, 1, 3, 9, 21, 35, 49, 62` — is
literally what `ldr r1,[ip, r2, lsl #2]` indexes.

**And it reconciles what looked like a contradiction.** The function returns a pointer `0x14` *short*
of a record, so the caller's `+0x14` lands on `record+0x00`:

```
index  0 -> returns 0x040, +0x14 = 0x054, mask 0x00001   the monomino
index  4 -> returns 0x0A0, +0x14 = 0x0B4, mask 0x00421
index 13 -> returns 0x178, +0x14 = 0x18C, mask 0x00047   Goku's T
```

**[WRONG — see "Corrected again" below. Base is `0x40`; bitmap is at `record+0x14`.]** So the record base **is** `0x54` (`= 0x40 + 0x14`), the bitmap **is** at `record+0x00`, and
`[fn+0x14]` **is** the bitmap. The header is `0x40` — eight cumulative words then eight count words —
followed by a `0x14` gap reading `1, 0, 0, 0, 0`.

**Why declining to name the object was right.** From the offsets alone I'd have placed the bitmap at
`+0x14` of a kshape record, among the trailing words. It's `+0x14` of a pointer *deliberately short*
of the record. Naming from offsets would have produced a confident, wrong field map.

**And a tidy idea of mine failed a cheap test:** I hypothesised `koma.bin` was the `0x18`-stride table
with bitmaps at `+0x14`. Checked all six word offsets of a `0x18` stride across its 445 records —
**zero** catalogue masks at any offset. koma.bin holds something else.

## Corrected again: the base is `0x40`, and the record is a cell map plus a bitmap

`0x40 + 66*0x18 = 0x670`, exactly the file size. `0x54` overruns by `0x14` and leaves 65.167 records —
a fractional record count is the tell. So **the bitmap is at `record+0x14`** and `0x02076D00` returns
the record exactly, not `0x14` short of it.

**Confirmed structurally, independent of the size argument.** The five leading words are a **20-byte
per-cell ordinal map** — one byte per grid cell, 5 columns × 4 rows, holding a 1-based traversal order
for occupied cells and 0 for empty:

```
record 59, cell map as the grid        its bitmap 0x10C63
   1  2  0  0  0                          ##...
   3  4  0  0  0                          ##...
   4  6  0  0  0                          ##...
   0  7  0  0  0                          .#...
```

Across all 66 records the cell map's occupied set equals the bitmap's set **66 of 66**, and popcount
equals the ordinal count **66 of 66**. The bitmap is a redundant summary derivable from the cell map,
which is why it comes last — and a 20-byte map can't start at `+0x14` of a `0x18` record, so the
layout settles the boundary on its own.

**One anomaly:** record 59's ordinals are `1,2,3,4,4,6,7` — a duplicate 4, no 5. Occupied set and
count are still right; only the permutation breaks. One of 66, so likelier a data bug than a feature.

### Two errors of mine worth keeping

**A circular constraint.** I restricted candidate bases to `≡ 0x0C mod 0x18` because `0x0B4` is "a known
record". It's a known *bitmap*. That assumed the bitmap sits at `record+0x00` — the thing in question —
and **excluded `0x40` from the search space**, so every candidate the search returned was wrong by
construction.

**A test that could not fail.** The bitmap addresses are identical under both readings, so the 65-test
popcount check was blind to the boundary. And I reported it as "settled by the header's own class
table", which made it sound as though the header had adjudicated — it adjudicated the class-to-index
mapping, which was never in dispute. An insensitive test, described as answering a harder question.

Twice now the strongest-feeling evidence here has been a test every candidate passes. The guard:
**name the rival and ask what byte it predicts differently, before running anything.** Here that was
one line — "under the other reading, where does the last record end?"


## The grid is 5 wide, and the ROM says so directly

The width question (5 columns x 4 rows vs the transpose) does not need the file layout or a
connectivity argument. `0x02076D30`, the placement validator, states it three times:

```
0x02076D6C  ldr r0, [r0, #0x14]      ; the bitmap, at record+0x14
0x02076D70  lsr r3, r0, #5           ; \
0x02076D74  lsr r2, r0, #0xa         ;  four slices, five bits apart
0x02076D78  lsr r1, r0, #0xf         ; /
0x02076D7C  and ip, r0, #0x1f        ; each masked to 5 bits, then OR'd
0x02076D98  lsl r1, r1, r5           ; shift the column profile by the column
0x02076D9C  bics r1, r1, #0x1f       ; anything past bit 4 -> reject
0x02076DA8  add r1, r4, r4, lsl #2   ; row*5
```

It folds the 20-bit map into a per-column profile by OR-ing FOUR slices of FIVE bits. Four rows of
five. The 5-bit overflow mask and the `row*5` index say the same thing from two other directions. A
width-4 reading would slice by 4.

Semantic cross-check, from the runtime seat: a koma piece must be one connected polyomino.
Width 5 gives 66/66 connected; width 4 gives 30/66, with 36 shapes coming apart (record 59 among
them). Agrees, and from a completely different representation -- but it was never the only
discriminator available.

## `[r0+0x14]` settles the base without the file size

`0x02076D6C` loads the bitmap at `record+0x14`, so a record begins 0x14 before any known bitmap.
File offset 0x0B4 is a known bitmap:

```
0x0B4 - 0x14 = 0x0A0 = 0x40 + 4*0x18      record 4 under base 0x40, exact
```

This is independent of the file-size fit (`0x40 + 66*0x18 = 0x670`, exact). Two representations,
one answer.

It also sharpens the circular-constraint error recorded above. The bad constraint was built FROM
"0x0B4 is a known bitmap" -- and that same fact yields 0x40 in one subtraction once paired with the
`+0x14` load, which sits in a function already read. The information needed to break the circle was
inside the circle. What kept it shut was converting an observation into a modular constraint instead
of asking what the code does with that address.

State: bead jus-koma-shapes-come-from-kshape-bin-0j2, bead jus-kshape-lookup-identified-a1j,
bead jus-circular-search-constraint-ei5q.
