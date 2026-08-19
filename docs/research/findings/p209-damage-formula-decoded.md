## P209 — the damage formula decoded: the flat `-2.0` is a `0.75` multiplier

`0x020823E4`, arm9, 680 bytes. `CONFIRMED_STATIC` for the shape.

### The formula

```
prologue:
0x020823E8: mov   sl, r1              ; sl = the 0x2C hit element
0x020823EC: ldr   r4, [sl, #0xc]      ; r4 = elem+0x0C = a scratch (the player's, per runtime's dump)
0x020823F8: add   r7, r4, #0xa4       ; that scratch's contribution array
            ; then a loop: while [r4+0x68] != 0 and bit 9 of [r4+0x40] is clear, walk r4 = [r4+0x68]
0x02082420: ldr   r1, [sl, #0x10]     ; elem+0x10
0x02082428: ldrsb r5, [r1, #4]        ; BASE, a SIGNED BYTE
0x0208242C: tst   r0, #0x2000000      ; bit 25 of the resolved scratch's +0x40

the chain:
0x0208247C: add   r0, r4, #0x100
0x02082480: ldrh  r2, [r0, #0x84]     ; f1 = halfword at scratch+0x184
0x02082484: ldrh  r0, [r0, #0x86]     ; f2 = halfword at scratch+0x186
0x0208248C: lsl   r3, r5, #8          ; base = r5 << 8
0x02082490: sub   r2, r2, #0x100
0x02082494: mul   r2, r3, r2
0x02082498: add   r2, r3, r2, asr #8  ; r2 = base * f1 / 256
0x0208249C: sub   r0, r0, #0x100
0x020824A0: mul   r0, r2, r0
0x020824A8: add   r5, r2, r0, asr #8  ; result = r2 * f2 / 256
```

`0x100` is `1.0` in 8.8 fixed point. The formula is **damage = (signed byte x 256) x f1/256 x f2/256**, where the two factors are halfwords at `scratch+0x184` and `+0x186`.

This also explains why no base damage showed up in the runtime loop's `0x2C`-byte element dump: the base isn't stored in the element. It's one signed byte behind `elem+0x10` — the element only carries the pointer.

### The arithmetic that closes fourteen iterations

| `r5` | base | factors | result | displayed |
|---|---|---|---|---|
| 2 | 512 | `0x100`, `0x100` | 512 | **8.000** |
| 2 | 512 | `0x100`, `0x0C0` | **384** | **6.000** |

`384` comes from base `512` times a single factor of `0xC0` — that's `0.75` in 8.8. The doc's `8.000` "unresisted" figure is just the unscaled base, not a separate measurement.

**The flat `-2.0` is a `0.75` multiplier. There is no subtraction anywhere.** The non-constant ratios that pointed toward a flat reduction were an artifact: `0.750` and `0.714` are raw `512->384` and `448->320`, but `448` isn't expressible as `r5 << 8` for integer `r5` (`448/256 = 1.75`), so that second move's `7.000` was already scaled. We were comparing two scaled numbers against each other instead of a base against a scaled result. Fourteen iterations found no subtraction because there is none.

### Pre-registered prediction, sent before the runtime loop's breakpoint

At `0x02082490` before it executes: `r3 = 512`, and `r2` is `0x0100` or `0x00C0`. At `0x0208249C`: whichever of the two halfwords the first was not — exactly one carries `0xC0`. After `0x020824A8`: `r5 = 384`. The signed byte at `[elem+0x10 + 4]` reads `2`.

Failure signatures, each killing a different part: `r3 != 512` means the base isn't `r5 << 8` and the prologue read is wrong. Neither halfword carrying `0xC0` while the result is still `384` means a third scaling step exists. The byte not reading `2` means `r5` loads from elsewhere on this path.

### Next watchpoint target

`scratch+0x184` and `+0x186` are the damage multipliers. Whatever writes them is where resistances, abilities, and rules land. A `JUS_WATCH` on those two halfwords names that writer the same way it named the term writer — and that writer is the natural home for the ability-derived value both loops have been looking for.

### Not claimed

**Which scratch supplies the factors.** `r4` starts as `elem+0x0C` and walks through `[r4+0x68]` while bit 9 of `[r4+0x40]` is clear, so the factors come from whatever that chain resolves to. Attacker vs. victim changes the interpretation completely; it needs `r4` read at `0x0208247C`.

Two smaller notes: `0x0208242C` tests **bit 25** of `[r4+0x40]`, the bit `0x02159210` toggles — so that setter feeds this formula. And `r7` holds `elem+0x0C`'s scratch `+0xA4`, putting the attacker's contribution array in hand here too.

A repo-wide record check for prior documentation of this formula is in flight; if earlier work already recorded these multipliers, this finding is a re-derivation and will be relabelled.
