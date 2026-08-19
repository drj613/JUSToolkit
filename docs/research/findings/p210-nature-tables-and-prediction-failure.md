## P210 — prediction failed on every specific; base byte is `8`, nature tables found

### RETRACTED: the P209 prediction

Runtime measured it. Control fired twice, all five breakpoints fired exactly twice — these are the damage calls.

| Predicted | Measured |
|---|---|
| base byte = `2` | **`8`** |
| `r3` (base) = `512` | **`2048`** |
| one factor = `0x0C0` | **both `0x0100`** — no `0.75` in this chain |
| final `r5` = `384` | **`2048`** |

Wrong on all four. I'd also drafted a follow-up claiming the base was fixed at `512` with resistance subtracting `0x40` from the multiplier — the factor delta came out constant at `-0x40` across both moves, which felt like confirmation. **Draft discarded unpublished.** It was a clean derivation from a wrong base that reproduced the observed number — the most convincing kind of wrong. It only avoided becoming canon because the prediction was written down before the measurement.

### What survives: the campaign's oldest number

The prologue read was right: `r5` comes from `ldrsb [elem+0x10 + 4]`, which is why no base appeared in the `0x2C`-byte element dump. **It reads `8`.**

`8` is the doc's unresisted `8.000` — **measured directly for the first time.** It converges with the CONFIRMED static formula DJ pointed me at: `damage = (jpower.damage1 ÷ 5) + (tier − 2)`, where `damage1` stores displayed damage × 5, so B's `damage1 = 40` encodes `8.000`. The design-time number and the runtime byte agree, reached from a file format and from a breakpoint.

**`jus-f0v`'s premise is moot.** The `8.000` baseline needed no ability-free opponent, no target swap, no respawn variant, no custom deck — only the right breakpoint. Four workarounds were built to obtain a number that was one signed byte away.

### `r4` is the attacker's scratch

`r4 = 0x0220FC3C`, the player's. So `+0x184`/`+0x186` are **attacker-side** scales, both exactly `1.0` here — not the reduction. I was right to refuse to guess which side it was.

### CONFIRMED: nature multiplier tables

The tail resolves the third factor. `0x020824B8`/`0x020824D0` read a byte at `r7+0xD1` — since `r7 = scratch+0xA4`, that's **`scratch+0x175`**, one of the bytes the collision loop writes (P201). Two-bit fields are extracted by `lsl`/`lsr #0x1E` triples, choosing bits 0–1, 2–3, or 4–5 by flags. Then:

```
0x02082508: lsl   r2, r1, #1          ; attack category x 2
0x0208252C: ldr   r3, [pc, #0x164]    ; table base
0x02082534: add   r1, r3, r1, lsl #3  ; + defence category x 8
0x02082538: ldrsh r3, [r2, r1]        ; factor = s16 table[defence][attack]
```

A 2-D table of signed halfwords, row stride `8`, column stride `2`. Both tables read out of `arm9.bin`:

**Table B, `0x0209FEF4`** — path taken when `ColPrmMan+0x14D` bit 0 is clear:

| | atk0 | atk1 | atk2 | atk3 |
|---|---|---|---|---|
| def0 | 1.000 | 1.000 | **1.500** | 1.000 |
| def1 | **1.500** | 1.000 | 1.000 | 1.000 |
| def2 | 1.000 | **1.500** | 1.000 | 1.000 |
| def3 | 1.000 | 1.000 | 1.000 | 1.000 |

**Table A, `0x0209FF14`** — the other path:

| | atk0 | atk1 | atk2 | atk3 |
|---|---|---|---|---|
| def0 | 1.000 | **1.500** | 1.000 | 1.000 |
| def1 | 1.000 | 1.000 | **1.500** | 1.000 |
| def2 | **1.500** | 1.000 | 1.000 | 1.000 |
| def3 | 1.000 | 1.000 | 1.000 | 1.000 |

`CONFIRMED_STATIC`: these are the **nature multipliers**. Only `1.000` and `1.500` appear; the fourth row and column are all `1.000`; the two tables are **inverse 3-cycles**, selected by `ColPrmMan+0x14D` bit 0. That's the 力/知/笑/なし triangle with なし inert — and it independently reproduces the confirmed static formula's *"nature multiplier: 1.0x neutral, 1.5x advantage, 1.0x disadvantage (bonus-only system)"*. **No value below `1.0` in either table, which is why the doc called it bonus-only.** Two representations — a file format and arm9 code — agreeing.

Also: `0x020824E0`/`0x020824EC` test **bit 30** of `+0x40` on both sides, forcing the factor to `0x100` if either is set — bit 30 being the bit `0x021591F4` toggles. So that setter is a nature-immunity switch.

### Still open: the `2048 → 384` gap

Nature was `1.0` here, so it's not the reduction either. Runtime's reconciliation stands: `2048` is `8.0` in 8.8, `>>2` converts to raw/64 scale giving `512` = `8.000`, then `×0.75` gives `384` = `6.000`; overall `3/16`. A `0.75` exists but lives **after** `0x0208253C`, and I haven't read from there to the return. That's the next bounded read — and this time I'm predicting nothing about its shape.
