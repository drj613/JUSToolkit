# Loop-Atlas 216 — nature is read in the damage path, and the banner was the error

Claims in beads: [`jus-nature-is-read-in-damage-path-hbt`],
[`jus-nature-does-not-affect-damage-0c6`] (now `state:tainted`),
[`jus-nature-january-vs-august-9a6`].

The owner confirmed January's 1.5× came from live play, not derivation. A static check followed, and it settles the question.

## The tables contain exactly 1.5

Read from `arm9.bin`, 4×4 signed halfwords, index = `base + row*8 + col*2`:

| `0x0209FEF4` | | | | | `0x0209FF14` | | | |
|---|---|---|---|---|---|---|---|---|
| 1.0 | 1.0 | **1.5** | 1.0 | | 1.0 | **1.5** | 1.0 | 1.0 |
| **1.5** | 1.0 | 1.0 | 1.0 | | 1.0 | 1.0 | **1.5** | 1.0 |
| 1.0 | **1.5** | 1.0 | 1.0 | | **1.5** | 1.0 | 1.0 | 1.0 |
| 1.0 | 1.0 | 1.0 | 1.0 | | 1.0 | 1.0 | 1.0 | 1.0 |

`0x0180` is 1.5 in 8.8 fixed-point. Two opposite three-cycles with a neutral fourth row and column — rock-paper-scissors over three natures plus "none," matching the owner's known enum (力 / 知 / 笑 / なし). Table selection depends on `cmp sb, #0` at `0x020824FC`, where `sb` is `arg2`, the single bit from `[sl+0x14d]` at call site `0x02081264`.

## The arithmetic reproduces the owner's number

```
0x02082568  sub r1, r3, #0x100      ; r3 = 0x180 -> 0x80
0x0208256C  mul r1, r5, r1          ; 2048 * 128 = 262144
0x02082578  add r0, r0, r1, asr #8  ; r0 += 1024
0x02082678  add r0, r5, r0          ; 3072
0x0208267C  asr r1, r0, #2          ; 768
```

`768 / 64 = 12.000`, versus `512 / 64 = 8.000` when `r3 = 0x100`. The owner said to reproduce "B at 8 → 12." The table and the instructions give exactly that. Live play, ROM data, instruction arithmetic — three representations, none derived from the others.

## What August actually showed

Not "nature is never consulted." The path reads a **2-bit field**, not a byte. The column comes from `[r7+0xD1]` (= `r4+0x175`) — bits 1:0, 3:2, **or** 5:4 depending on flags at `0x020824A4` and `0x020824B4`; the row is `[r8+0x175] & 3`. Three candidate 2-bit fields packed in one byte, on a per-ColPrm-scratch copy. A bypass exists: if bit 30 of either `[r8+0x40]` or `[r4+0x40]` is set, `0x020824F4` forces `r3 = 0x100` and the tables are never read.

The null result had three innocent explanations. The bead picked the one that generalises furthest. Three bit-identical runs measure reproducibility, not scope. The experiment stands; the generalisation doesn't.

## The banner was the error

Five documents cited the tainted claim. Two — `Combat-Mechanics.md` and `Combat-Mechanics-Reference.md` — carried banners calling the correct January answer **wrong**. For part of a day, a reader landing on either was told the truth was false.

This is the thirty-iteration failure the project already paid for, recreated in the opposite direction within a week, by a process built to prevent it. Why it got through: the measurement was real, reproducible, and carefully written up. Nothing about it looked like a claim needing a scope audit. Clean evidence skipped the check. All five documents are corrected in the same wake as the bead.

## The formula headline changes shape

Nature and the class gates land in the **same accumulator** `r0` and are **additive**, not multiplicative. Codex, asked cold with the tables but no hypothesis, independently confirmed this and gave the same 768-versus-512. So "×0.75 per gate" is really *a sum of quarter-steps over the base, plus a half-step for nature advantage*. Advantage with one resist gate is 1.25×, not 1.5 × 0.75.

## Provenance

Static only. `jus_files/arm9/arm9.bin`, listing `jus_files/analysis/disasm/arm9.txt`; table bytes read from the binary at `addr − 0x02000000`, independent of the listing. Codex used cold — given two tables and the listing, no offset named, no hypothesis stated; it returned the `row*8 + col*2` index arithmetic, the three candidate 2-bit column fields, the `0x40000000` bypass, 768 versus 512, and "combined additively, not multiplicatively." Owner ground truth via [`jus-nature-january-vs-august-9a6`].

## The runtime number arrived — the 1.5 cell is observed live

Six stops read `r0 = 512` at `r5 = 1024`, unpoked [`jus-bit5-fired-and-nature-observed-w5n`]. The
term is `(r5 * (r3 - 0x100)) asr 8`, and **every** value in both nature tables is either `0x0100` or
`0x0180` — there is no third value. So at base 4 the term can only be 0 or 512, and 512 uniquely
implies a `0x180` = 1.5 cell. The bypass forces `r3 = 0x100`, which gives 0, so there's no other
route.

`jus-nature-1p5-never-observed-uh8` is retracted. And the composition lands as decoded: 4.000
unreduced, +2.000 nature, −1.000 quarter-step = 5.000 — both terms nonzero in one accumulator for the
first time.

**Why this observation counts where the earlier one didn't.** Two wakes earlier I offered the runtime
seat a cross-confirmation from a reading of `r0 = 0`, and they declined it. They were right: a
predicted value of **zero** is reachable by the tables returning 1.0, by the bypass firing, or by
nothing writing `r0`. A **nonzero** term at exactly the table value is reachable only by the tables
being read and indexed. Same field, same register, opposite epistemic weight — and the entire
difference is which value was predicted.

**Still open, narrowly:** the specific *cell* is inferred from the term's value, not read from the
inputs. 512 pins it to a 1.5 cell but not to which one, so whether the selector resolves as
[`jus-nature-column-selector-8gk`] predicts is untested.

