Here's the rewritten doc:

---

# Per-Size HP Candidate in chr_b.bin (Task K2d)

Loop-Atlas iteration 7, static analysis. Triggered after the harness session killed my `size × 36` guess — all 8 deck slots read as u16, every HP was a multiple of 64 raw / 8 displayed, making `180` (22.5 × 8) impossible.

**Bottom line: strong candidate for per-size HP inside `chr_b.bin`, with one sharp testable prediction — Naruto's size-5 panel should read `160`, not `152` or `180`.**

## My earlier prediction was wrong

`findings/koma-format-decoded.md` predicted HP = `size × 36`, giving size-5 = `180`. **REFUTED**: HP is quantized to 8 displayed units and `180 / 8 = 22.5`. The harness session's replacement guess was `HP = 8 × (14 + size)` → size-5 = `152`. The evidence below says that's also wrong, for a more interesting reason.

## The candidate

`chr_b.bin` has 74 entries × 60 bytes. Five u8 fields sit at offsets `0x10`, `0x14`, `0x18`, `0x1C`, `0x20` (stride 4):

- **All 370 bytes (74 × 5) are multiples of 8.** CONFIRMED. That's not coincidence — 8 is exactly the HP quantum the harness measured.
- `+16` is the most common step between adjacent slots (131 times, vs. 63 zeros and scattered others).

Battle `abilityId` (`koma.bin` byte `0x7`) has 74 distinct values in range `0..73`, matching `chr_b.bin`'s 74 entries exactly — so `abilityId` is the `chr_b` index. CONFIRMED by arithmetic.

### Naruto lines up perfectly

Naruto uses `abilityId 20` for sizes 4–6 and `abilityId 24` (ナルト（九尾）) for sizes 7–8:

| entry | slot values (`0x10`,`0x14`,`0x18`,`0x1C`,`0x20`) |
|---|---|
| `chr_b[20]` Naruto | `144, 160, 176, 144, 144` |
| `chr_b[24]` ナルト（九尾） | `80, 96, 112, 192, 208` |

Sizes 4/5/6 from entry 20 slots 0/1/2, sizes 7/8 from entry 24 slots 3/4:

**`144, 160, 176, 192, 208`** — a clean `+16` ladder across sizes 4→8.

Three things independently back this up:

1. `144` matches the harness session's RAM reading for Naruto's 4-koma **exactly**.
2. Sizes 7–8 coming from a *different* `chr_b` entry explains why `komatxt.bin` renames those panels ナルト（九尾）.
3. `208` at size 8 fits the owner's observation that 8-koma panels have the most HP.

Each entry holds five slots indexed by `size - 4`. Characters only populate slots for sizes they actually have — entry 20's slots 3–4 repeat `144` (filler), and entry 24's slots 0–2 hold unrelated values.

## Where this is weak

**Only 19 of 74 entries are non-decreasing across the five slots.** Examples:

```
chr_b[66]: [104, 64, 152, 64, 224]
chr_b[73]: [224,  64, 152,  64,  64]
chr_b[ 5]: [ 80, 152, 128, 128, 128]
```

If all five slots were per-size HP for every character, they should rise or plateau, not zig-zag. Two readings survive:

- **A**: The five slots *are* per-size HP, but only slots matching sizes the character actually owns are meaningful; the rest is filler. Naruto fits this.
- **B**: My stride-4 grouping is wrong — I'm grabbing one byte out of five *different* fields that happen to share the multiple-of-8 property.

Evidence for B: reading these as u16 gives high bytes of `1, 4, 5, 16, 20, 22`, not a constant. A real per-size HP array would more likely be u8 or consistent u16, so the field boundaries probably aren't exactly where I've drawn them, even if the `0x10`+`4n` positions are right.

Confidence: **PLAUSIBLE**, not confirmed. The multiple-of-8 property and the Naruto ladder are strong; the non-monotonic majority is a real problem I can't explain statically.

## The falsifiable prediction

Three hypotheses give three different answers for **Naruto's size-5 panel** (`koma.bin` record 502):

| Source | Rule | size-5 HP |
|---|---|---|
| Mine (iteration 4) | `size × 36` | `180` — already REFUTED (not a multiple of 8) |
| Harness session | `8 × (14 + size)` | `152` |
| **This doc** | `chr_b[20]` slot 1 | **`160`** |

`152` and `160` are one quantum apart, so this needs an exact read — raw `9728` vs `10240`. That's harness card F1, and it now cleanly discriminates between the two surviving hypotheses.

If `160`: the `chr_b` slot array is real, HP is **per-character-per-size table data** (not a formula), size ladders vary by character, and each character's HP curve can be read straight from `chr_b.bin` offline for all 74.

If `152`: reading B is likelier, and I'm pattern-matching noise that happens to fit Naruto.

## Note on the 8.0 / 0.0 slots

The harness session's slot table had one entry at `8.0` displayed (empty ability array) and one at `0.0`. If `8.0` is a real panel, it can't come from any `chr_b` slot — the minimum value in that column set is well above 8. So `8.0` is most likely an empty/placeholder slot, not a base-HP data point. Don't over-read it.
