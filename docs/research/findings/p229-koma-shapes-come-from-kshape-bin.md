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
