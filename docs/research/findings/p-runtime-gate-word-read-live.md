# Runtime — the gate word read live: 0x00002010, predicted to the bit

Claims tracked in beads: [`jus-gate-word-read-live-0x2010-nbz`],
[`jus-formula-bp-not-a-hit-oracle-ve6`], [`jus-gate-word-is-r8-0x44-fnz`],
[`jus-bit5-is-ability-10-rxl`].

## What was predicted, before the emulator was launched

The static side published a mask table mapping ability ids to bits of the gate word. The
recorded target bitset for `fight_base` is `0x02005200`, i.e. ability ids 9, 12, 14, 25.
Two of those ids appear in the table: id 9 maps to subtract-bit 4, and id 12 maps to
**add**-bit 13. So the gate word had to read `0x00002010` — a prediction the static side had
not made, registered on the request bead before launch, one value out of 2^32.

## What the capture read

Breakpoint at arm9 `0x02082584`, eight stops, all identical:

| value | read | meaning |
|---|---|---|
| `r2` = `[r8+0x44]` | `0x00002010` | the gate word, exactly as predicted |
| `r8` | `0x0220FDC4` | the object the gates read |
| `r4` | `0x0220FC3C` | the other participant |
| `r5` | `2048` | the 8.8 base |
| `[r3+0x04]` | `8` | base damage byte — agrees with `r5` independently |
| `r1`, `[r3+0x0E]` | `0`, `0` | class index, and it agrees with itself |
| `[r8+0x40]` | `0x01000018` | dynamic; reads `0x00000008` at rest |

The breakpoint sits at `0x02082584` rather than `0x0208257C` because at the earlier address
`r1` is `r5 * (nature - 1.0)`, which is zero whenever nature is 1.0 — as it has been in every
measurement ever taken. A prediction of "`r1` in 0..15" would have passed there on a zero that
had nothing to do with the class index, and would have passed forever, for the same reason.

## The chain closes end to end

Read on `fight_base` before GDB was attached, so the derivation is independent of the capture:
`battleObj 0x02244020` → `+0x1a8` = `0x022069F8` → `+0x10` = `0x0220FDC4`, whose `+0x44` is
`0x00002010`. The damage routine's `r8` is the same `0x0220FDC4`. The object the ability
helper writes and the object the gates read are one object.

## The arithmetic, and the conditional that correctly declined to fire

Category is `table[0]` = 1. Bit 14, bit 6, bit 12 and bit 5 are not armed. Bit 4 is armed and
needs category 1, so it fires: −512. Bit 13 **is armed** and needs category 2, so it does not.

```
out = (2048 − 512) >> 2 = 384 raw = 6.000 displayed
```

which is the number measured independently, with real HP drops, in [`jus-jas`]. The armed
bit that declined to fire is the stronger half of this: it shows the category gating working,
rather than showing only that one bit has an effect.

## What this does not show

**No hit landed during the capture.** The target's HP held at max through all eight formula
evaluations with regen confirmed off. Every stop is a swing that did not connect, and the
formula runs anyway [`jus-formula-bp-not-a-hit-oracle-ve6`]. The gate word and the base byte
are properties of the target and the move rather than of contact, and the arithmetic they
imply matches an independent landed-hit measurement — but this capture does not itself
witness a landed hit.

**Bit 4's causality is untested.** A clear-bit-4 / restore intervention returned `+0.000` on
all three arms because the presses were out of range. Three identical nulls would have read
as "bit 4 does nothing" and refuted a correct decode; the unconditional stop counter staying
flat at 3 is what identified it as a stimulus that never arrived. The intervention needs no
GDB, so it is not bound by the one-session-per-launch limit and should be run outside one.
