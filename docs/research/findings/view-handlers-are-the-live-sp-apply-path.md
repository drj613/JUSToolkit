# Findings: the view's handlers are a live path into SP-apply

Loop-Atlas iteration 90. Static.

The 16-slot table applies per-slot `int16` values to the character through
**`0x020781E4`**, the SP-apply function.

`0x020781E4` was previously known only through **dead** code — iteration 46 found
dispatcher cases 23/24 unreachable. The view gives it a **live** caller set from hit
resolution and the state dispatcher.

Also found: two `int16[16]` arrays and a capped counter.

---

## 1. Selectors 9 and 12 — apply an array value as SP

```
0x0215FF4C  ldr  ip, [pc, #0xc]        ; -> 0x020781E4
0x0215FF50  add  r1, r0, r1, lsl #1    ; view + N*2
0x0215FF54  ldrh r1, [r1, #0x16]       ; the slot's int16 parameter
0x0215FF58  ldr  r0, [r0]              ; view+0x00 = [char+0x1b4]
0x0215FF5C  bx   ip                    ; tail-call SP-apply(target, amount)
```

Takes the slot's `int16` from `+0x16`, tail-calls SP-apply with the character's data
block as target.

## 2. Selectors 13 and 14 — apply a scratch slot, if non-zero

```
0x0215FF64  ldr ip, [pc, #4]           ; -> 0x0215FFA0
0x0215FF68  add r1, r0, #0x64          ; &view+0x64
0x0215FF6C  bx  ip

0x0215FFA0  push {r4, lr}
0x0215FFA4  mov  r4, r1
0x0215FFA8  ldrh r1, [r4]
0x0215FFAC  cmp  r1, #0
0x0215FFB0  popeq {r4, pc}             ; zero -> nothing to apply
0x0215FFB4  ldr  r0, [r0]
0x0215FFB8  bl   #0x20781e4            ; SP-apply
```

Same destination, different source: the `+0x64` scratch halfword. `0x0215FCE4` writes
into `+0x64` from `view+0x16[N]` — one method stages, another applies.

## 3. Selector 11 — a capped counter and a second array

```
0x0215FF74  push {r3, lr}
0x0215FF78  ldrh r2, [r0, #0x14]
0x0215FF7C  cmp  r2, #0x2d0            ; 720
0x0215FF80  addls r1, r2, #1
0x0215FF84  strhls r1, [r0, #0x14]     ; below the cap -> just count
0x0215FF88  popls {r3, pc}
0x0215FF8C  add  r1, r0, r1, lsl #1
0x0215FF90  ldrh r1, [r1, #0x36]       ; a SECOND int16 array
0x0215FF94  ldr  r0, [r0]
```

`view+0x14` counts up to `0x2D0`, then falls through to the apply path. At 60 fps:
12 seconds.

## 4. The view's two parallel arrays

Selectors run 0–15, so each `int16` array occupies `0x20` bytes. `+0x16` ends at
`+0x35`; the second array at **`+0x36`** is exactly contiguous.

Layout:

| offset | contents |
|---|---|
| `+0x00` | `[char+0x1b4]`, the target passed to SP-apply |
| `+0x04` | `&char+0x7c` |
| `+0x08` | the character |
| `+0x0C` | 32-bit enable mask |
| `+0x14` | counter, capped at `0x2D0` |
| `+0x16` | `int16[16]`, indexed by selector |
| `+0x36` | `int16[16]`, indexed by selector |
| `+0x56`–`+0x59` | unaccounted |
| `+0x5A`–`+0x6A` | halfword slots, including the `+0x64` scratch |

Still inside the `0x70` bound from `char+0x1A0`.

## 5. A live path to a function known only as dead

`0x020781E4` is the SP-apply sibling of HP-delta `0x020783CC`. Iteration 46 marked
dispatcher cases 23/24 dead for both; the accumulator work found
`0x0215A334 bl 0x020781E4` on a path carrying zero at runtime.

The view reaches it from four selectors — 9, 12, 13, 14 — **all issued** (iteration 89).
Issuers: hit resolution `0x02158B20` (selector 9), state dispatcher (13, 14).

SP-apply is not a dead function; the *dispatcher's* route to it is dead. Distinct claims
that had been running together.

## Predictions status

| Claim | Verdict |
|---|---|
| Handler `0x0215FF4C` tail-calls `0x020781E4` with `view+0x16[N]` | **CONFIRMED_STATIC** — literal at `0x0215FF60`, `ldrh r1,[r1,#0x16]`, `bx ip` |
| Handler `0x0215FF64` applies `view+0x64` via `0x0215FFA0` | **CONFIRMED_STATIC** — `add r1,r0,#0x64`; `0x0215FFB8 bl #0x20781e4` |
| The `+0x64` apply is skipped when the slot is zero | **CONFIRMED_STATIC** — `cmp r1,#0`; `popeq` at `0x0215FFB0` |
| `view+0x14` is a counter capped at `0x2D0` | **CONFIRMED_STATIC** — `cmp r2,#0x2d0`; `addls`; `strhls`; `popls` |
| A second `int16` array exists at `view+0x36` | **CONFIRMED_STATIC** — `add r1,r0,r1,lsl#1`; `ldrh r1,[r1,#0x36]` |
| The two arrays are `int16[16]` and contiguous | **PLAUSIBLE** — selectors span 0–15, `+0x16` ends at `+0x35`, `+0x36` follows exactly; bounds not checked in code |
| `0x020781E4` is reachable only through dead code | **REFUTED** *(iteration 46's picture, now extended)* — four issued selectors reach it |
| Cases 23/24 are a dead entry point | **CONFIRMED_STATIC** *(unchanged)* — the dead route is the dispatcher's, not the function |
| All 9 unique handlers reach `0x020781E4` | **not claimed** — 3 read; the other 6 have no code-address literal nearby |

## Next angles, ranked

1. **Read the remaining 6 handlers** — `0x0215FD68`, `0x0215FD00`, `0x0215FD7C`,
   `0x0215FEAC`, `0x0215FEE8`, `0x0215FE14`. No code-address literals; they act on the
   view directly.
2. **Find who sets `view+0x0C`** — the mask gates all twelve.
3. **Find who fills the two `int16[16]` arrays** — the writer is the effect definition.
4. **Size `char+0x7c`** — damage-side users `0x02158B20`, `0x021586D0`.
