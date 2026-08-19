## P211 — damage formula end to end; the reduction is `r5/4`, not a flat `-512`

The runtime loop reported a flat `-512` — that's `2.0` in 8.8 fixed point, which is why every scan hunting for `128` (raw/64 magnitude) missed it for fourteen iterations. The unit mismatch is real and explains three sound-exhaustion results. But the term isn't constant.

### The instruction is proportional

```
0x02082644: lsleq r4, r5, #6          ; r4 = r5 << 6
0x0208264C: subeq r0, r0, r4, asr #8  ; r0 -= (r5 << 6) >> 8  ==  r5 >> 2  ==  r5 / 4
```

`r5` was `2048` on that run, so `r5/4` = `512` exactly. The measurement can't tell the two readings apart.

| move | base byte | base | flat `-512` | 25% of base | doc |
|---|---|---|---|---|---|
| B | 8 | 2048 | `384` = 6.000 | `384` = 6.000 | 6.000 |
| DOWN+B | 7 | 1792 | `320` = 5.000 | **`336` = 5.250** | 5.000 |

"Reproduces the other move without fitting" only holds under the flat reading. One certified DOWN+B measurement settles it, no deck needed. `5.000` means my decode is wrong or DOWN+B takes a different path; `5.250` means the doc's second row was heal-contaminated and the constant difference that started this hunt was an artifact of a single move.

### Two gates, one class table

```
gate 1  0x02082634: ldrb r3, [table, r1] ; cmp r3, #1              -> subtract r5/4
gate 2  0x02082650: tst  r2, #0x20       ; r2 = [r8+0x40], the flag word
        0x0208265C: ldrb r1, [table, r1] ; cmp r1, #2              -> subtract r5/4 again
```

Both pool loads resolve to `0x0208269C`, reading the same byte table at **`0x02092E68`**:

| index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| value | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |

The index maps to a damage **class**: class 1 loses 25% unconditionally; class 2 loses 25% only when **bit 5 of the flag word** is set. Total reduction: 0%, 25%, or 50%.

### The formula, end to end

```
base   = ldrsb [elem+0x10 + 4]           ; measured 8 -> the doc's unresisted 8.000
r3     = base << 8                       ; 2048 = 8.0 in 8.8 fixed point
      x= [attacker_scratch+0x184] / 256  ; measured 1.0
      x= [attacker_scratch+0x186] / 256  ; measured 1.0
      x= nature_table[defence][attack]   ; 0x0209FEF4 / 0x0209FF14, measured 1.0
r5     = that result
r0     = -(r5/4) per gate passed         ; 0, 1 or 2 gates
out    = (r5 + r0) >> 2                  ; 8.8 -> raw/64
0x02082684: str r1, [fp]                 ; the out-parameter
```

### A misread in their trace, corrected

They read `r3` going `4 → 262144` at `0x02082644` as "a value of 2 shifted into 8.8 and negated," concluding the source was per-target resistance. It isn't a damage value: `0x0208263C`/`0x02082640` are `orreq r3, r6, #4` then `lsleq r3, r3, #0x10` — the **result flag word** being built, with bit 2 meaning "resisted." It's handed back through `r6` at `0x02082648` and returned in `r0` at `0x02082680`. There's no literal 2 in the arithmetic.

### Why the ability pokes did nothing

This closes that loop. The reduction gates on **a flag bit and a class table**, not the ability bitset. An ability would have to feed those flags at **load** time — exactly the derived-value hypothesis both loops have been circling. Whatever sets **bit 5 of `[r8+0x40]`** is the next target, and a `JUS_WATCH` reaches it.

### Standing of the disagreement

Neither side has a certified answer: their control didn't fire on the tracing run, and my read is static. The only disagreement is flat versus proportional. This is the **fourth** derivation in this thread to reproduce the observed values — two of mine were wrong, one was discarded unpublished, and theirs fits B perfectly under an assumption the instruction contradicts. Their own rule applies to all four.
