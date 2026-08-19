## P208 — the damage formula is `0x020823E4`, reached by an out-parameter

The watchpoint named the term writer in one stop. The question was where `r3` gets `384` in the 28 bytes before the store. It doesn't — the value comes from outside.

### The PC is off by the ARM prefetch offset

Watchpoint-reported `pc` is the storing instruction **+ 8**:

| Reported | Actual | Instruction |
|---|---|---|
| `0x020812E4` | `0x020812DC` | `str r3, [r8, r0, lsl #2]` — the term store |
| `0x02051864` | `0x0205185C` | `str r1, [r0], #4` — a post-indexed memset loop, matching the 1133 zero writes |

`0x020812E4` itself is `str r0, [sp, #0x14]`, a masked flag going to the stack — unrelated. Same class as the `0x02156EB4` return-address error. "Subtract 8" belongs in reporting.

### The 28 bytes accumulate; they don't compute

```
0x020812C8: ldr ip, [r8, r0, lsl #2]   ; prior value at the destination
0x020812CC: ldr r3, [sp, #0x4c]        ; the contribution
0x020812D4: add r3, ip, r3             ; accumulate
0x020812DC: str r3, [r8, r0, lsl #2]
```

The array is cleared every frame, so the first accumulate equals the contribution — that's why `r3` reads exactly `384`. The origin is `[sp+0x4C]`.

### `[sp+0x4C]` is an out-parameter

`CONFIRMED_STATIC`: inside `0x02080F14`, that slot is **loaded eight times and stored zero times**. Control: 24 other sp-relative stores exist in the function, so the search reaches. Its address is taken once:

```
0x02081264: ldrb  r0, [sl, #0x14d]    ; sl = ColPrmMan; a flag byte
0x02081268: mov   r1, r6              ; the 0x2C-byte hit element
0x0208126C: add   r3, sp, #0x4c       ; &out
0x02081270: tst   r0, #1              ; bit 0 of ColPrmMan+0x14D
0x02081274: movne r2, #1
0x02081278: moveq r2, #0
0x0208127C: mov   r0, r5              ; the element list
0x02081280: bl    0x020823E4          ; the damage calculation
```

### `0x020823E4` is the damage formula

arm9, 680 bytes, 2 callers, 2 callees (`0x02031070`, `0x0207342C`). It runs a fixed-point multiplier chain **twice**:

```
0x02082490: sub r2, r2, #0x100        ; factor - 1.0
0x02082494: mul r2, r3, r2
0x02082498: add r2, r3, r2, asr #8    ; = base * factor / 256
0x0208249C: sub r0, r0, #0x100
0x020824A0: mul r0, r2, r0
0x020824A8: add r5, r2, r0, asr #8    ; scaled again by a second factor
```

`0x100` is `1.0` in 8.8 fixed point. `asr r2, r2, #6` at `0x02082450` is the raw/64 HP scale showing up directly in the arithmetic.

`SPECULATIVE`, stated narrowly: **this is not yet the flat `−2.0`.** A pure `base × factor / 256` gives a **constant** ratio, and the non-constant ratios from earlier — `0.750` and `0.714` across two moves — were why a flat subtraction was suspected instead of a scale. So the reduction is either elsewhere in these 680 bytes, or in the inputs. 680 bytes unread; that's the next task.

### The card

Break at `0x02081280` — **before** the `bl` — and dump `r0`, `r1`, `r2`, plus the `0x2C` bytes at `r1`. Confidence `PLAUSIBLE`, reachability `ESTABLISHED` (the watchpoint already caught this path twice).

- **Program point:** the call site, **upstream** of the accumulate at `0x020812DC`.
- **Why these:** captures the formula's whole input set — element list, hit element, and the `ColPrmMan+0x14D` bit 0 flag, which is a rule/mode input that would otherwise require guessing.
- **Expected:** if the base in the element already reads `384`, the reduction is upstream of the formula; if `512`, it's inside `0x020823E4` and findable statically.
- **Failure signature:** the element holds neither value — the base is derived, not stored, and the card is retracted.

### A note on the method

`0x020812E4` sits `0x10` past the `+0x48` accumulator I read at P205 for an unrelated reason. **I had this instruction in hand and read past it**, because I was looking for a list insert. The watchpoint didn't just find it faster — it found it in a function I had already disassembled. The structural reason: the destination lives in `r8`, so `0xA4` never appears in the instruction encoding. A watchpoint keys on the **address** and doesn't care how the code computed it. That's a class of write no offset-targeted search can reach — not a search run badly.
