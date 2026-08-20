`kshape.bin` holds the koma shape catalogue, indexed by cell count. Builds on [`jus-koma-shape-is-a-20bit-bitmap-423`]; tracked in [`jus-koma-shapes-come-from-kshape-bin-0j2`].

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

## The record base is `0x54`, settled by the header's own class table

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

