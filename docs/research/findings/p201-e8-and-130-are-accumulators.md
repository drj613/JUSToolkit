## P201 — `+0xE8` and `+0x130` are accumulators too, and there is a `-2.0`-shaped subtraction

Every store in `0x02081DDC`'s loop body goes through one `+0xA4` interior pointer. `r8` is set once at `0x02081EC8` (`add r8, r2, #0xa4`) and never reassigned, so every `[r8, #N]` store hits `object + 0xA4 + N`.

| Store | Offset via `r8` | Real field |
|---|---|---|
| `0x02081F68` `str r1,[r8,#0x44]` | `0xA4 + 0x44` | **`+0xE8`** — the pending HP delta |
| `0x02081F74` `str r1,[r8,#0x8c]` | `0xA4 + 0x8C` | **`+0x130`** — the pending gauge amount |
| `0x02081F88` `str r1,[r8,#0xac]` | `0xA4 + 0xAC` | `+0x150` |
| `0x02081F98` `str r1,[r8,#0xb0]` | `0xA4 + 0xB0` | `+0x154` |
| `0x02081FF0`/`0x02082004` `strh r0,[r8,#0xc4]` | `0xA4 + 0xC4` | `+0x168` |
| `0x02082028`/`0x0208203C` `strh r0,[r8,#0xc6]` | `0xA4 + 0xC6` | `+0x16A` |
| `0x02082164` `strh r1,[r8,#0xc8]` | `0xA4 + 0xC8` | `+0x16C` |
| `0x02081FE4`/`0x02081FF8` `strb r1,[r8,#0xce]` | `0xA4 + 0xCE` | **`+0x172`** |
| `0x0208201C`/`0x02082030` `strb r1,[r8,#0xcf]` | `0xA4 + 0xCF` | **`+0x173`** |

### `+0xE8` is an accumulator, not an assignment

```
0x02081F50: ldr  r1, [r7, #0xc]
0x02081F54: ldr  r1, [r1, #0x38]
0x02081F58: tst  r1, #0x8000            ; a flag bit
0x02081F5C: subne sb, sb, r2, lsl #7    ; CONDITIONAL: sb -= r2 * 128
0x02081F60: ldr  r1, [r8, #0x44]        ; load +0xE8
0x02081F64: add  r1, r1, r3, asr #2     ; += r3 / 4
0x02081F68: str  r1, [r8, #0x44]        ; store +0xE8
0x02081F6C: ldr  r1, [r8, #0x8c]        ; load +0x130
0x02081F70: add  r1, r1, sb             ; += sb
0x02081F74: str  r1, [r8, #0x8c]        ; store +0x130
```

`CONFIRMED_STATIC`: `+0xE8` accumulates `r3 >> 2`; `+0x130` accumulates `sb`. Both are `+=`, not `=`. This explains why twenty iterations of searching for a `+0xE8` writer turned up nothing — the offset never appears as a literal, same as `+0x134` (`0xA4 + 0x90`). Three of four damage-related fields are now known to accumulate through one interior pointer.

### The `-2.0`-shaped subtraction — `SPECULATIVE`

`0x02081F5C`: `subne sb, sb, r2, lsl #7` — subtracts `r2 × 128`, conditional on bit 15 of `[[r7+0xc]+0x38]`.

HP scale is raw/64 (max `0x4000` = 16384 = 256.0 displayed), so 128 raw = 2.0 displayed. With `r2 = 1` this subtracts exactly 2.0. That's the right shape: a flat reduction, gated on a flag, inside the collision loop.

Two reasons not to call it found:

1. It subtracts from `sb`, which flows into **`+0x130`** — the pending gauge amount, not the HP delta at `+0xE8`. If that label is right, the -2.0 lands on the wrong channel. The label came only from the flush reading `+0x130` alongside `+0xE8`, so it deserves re-examination rather than trust.
2. `r2` is unverified. `r2 × 128` is only 2.0 when `r2 = 1`.

### What this wake did NOT find

**No store to `+0xA4` slot 0** — no `str [r8]` or `str [r8,#0]` in the body. The loop writes the other fields through the array base but never writes the term itself. The `384` still arrives from elsewhere; the `+0xA4` writer remains open. `UNCHECKED, NOT CLEAR` for the six unread pipeline stages, all of which take the same object.

### `+0x172` and `+0x173` are real scratch fields

Both are written here as bytes, in the scratch struct, by the collision loop. At P171 I retracted the claim that ov12 code supported the runtime loop's two-channel model — those ov12 hits were `ALTextDS` / `CommonWindow` text-widget fields. That retraction was correct and stands. What's new: fields at these offsets genuinely exist in the right struct, reached by the right code. That doesn't confirm the two-channel model — it means the model's offsets now have a plausible home, which is weaker.
