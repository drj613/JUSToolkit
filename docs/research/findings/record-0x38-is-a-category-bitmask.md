# Findings: `record+0x38` is a single-bit category mask, traced from four real call sites

Loop-Atlas iteration 141. Static.

Iteration 140 named `record+0x34`/`+0x38` as the installer's `arg2`/`arg3` but not what they *mean*. Traced
the chain up two levels to four real call sites, three of them in ov6 with concrete constants.

1. `arg2`/`arg3` **pass straight through** the pooled-entity constructor unchanged.
2. The four observed `arg3` values are **`0`, `0x800`, `0x4000`, `0x8000`** — zero plus three single bits.
3. `arg2` is `0x100` at two sites and `r3 & ~0xF` at a third, so **`arg2 & 0xF` is zero everywhere I can
   see** — and the installer has a whole branch that only fires when it is non-zero.

---

## 1. The chain, and an ABI check that passed twice

```
ov6 caller  ->  0x020834D4 (pooled-entity constructor)  ->  0x0207C988 (ColObj installer)  ->  record
```

The constructor keeps `arg2`/`arg3` untouched:

```
0x020834F0  mov r7, r2      ; r7 = arg2
0x020834F8  mov r6, r3      ; r6 = arg3
   ...
0x02083554  mov r2, r7      ; installer arg2 = arg2
0x02083548  mov r3, r6      ; installer arg3 = arg3
0x02083560  bl  #0x207c988
```

and forwards its two stack arguments:

```
0x02083534  ldr r0, [sp, #0x20]   -> 0x0208353C  str r0, [sp]
0x02083540  ldrb r2, [sp, #0x24]  -> 0x0208354C  str r2, [sp, #4]
```

The frame arithmetic confirms the argument numbering both times. The installer pushes 7 registers (`0x1C`)
and subtracts `0x14`, so a caller's `[sp+0]` lands at its `[sp+0x30]` — exactly where iteration 140 saw it
read. The constructor pushes 6 (`0x18`) and subtracts `8`, so its caller's `[sp+0]` lands at `[sp+0x20]` —
exactly where it reads. Two independent frames, both consistent.

## 2. Four call sites, with values

| call site | region | `arg2` | `arg3` |
|---|---|---|---|
| `0x02164F0C` | ov6 | `0x100` | **`0x8000`** |
| `0x02164F48` | ov6 | `0x100` | **`0x4000`** |
| `0x02168E44` | ov6 | `r3 & ~0xF` | **`0x800`** |
| `0x0208363C` | arm9 | passed through | **`0`** |

`arg3` is zero or exactly one bit, every time. That is a **category or layer mask** — "which group is this" —
and it lands in `record+0x38`, which iteration 70 showed the pool allocator copying into `node+0x18`.

**PLAUSIBLE**, not confirmed: four data points, three distinct bits, and no consumer of `+0x38` read yet. A
size or an index would not be spread across bits `0x800`, `0x4000` and `0x8000`.

## 3. `arg2`'s low nibble is never set at any site I can see

The installer contains this branch (iteration 140):

```
0x0207CA58  ands r0, r7, #0xf
0x0207CA5C  lslne r0, r0, #4
0x0207CA60  orrne r0, r0, #0x400000
0x0207CA68  orrne r5, r5, r0
```

But:

- `0x02164F0C` and `0x02164F48` pass `0x100`, and `0x100 & 0xF == 0`.
- `0x02168E44` passes `bic r2, r3, #0xf` — it **deliberately clears** the low nibble.

So none of the three ov6 sites can reach the `orrne` path. **Not claimed as dead**, because `0x0208363C`'s
wrapper passes `r2` through untouched and I have not traced its caller — but it is a branch with no observed
live caller, worth flagging alongside the seven vestigial systems already found.

Conversely `0x100 & 0x00FCFFFF` is non-zero, so at the two `0x100` sites `record+0x3C` does receive
`0x30000`. Substituting into iteration 140's formula, those sites give
`record+0x3C = arg5 | 0x20C000 | 0x30000`.

## 4. `0x02083624` is a thin wrapper that defaults the category to zero

```
0x02083624  push {r3, lr}
0x02083628  sub sp, sp, #8
0x0208362C  ldrb ip, [sp, #0x10]
0x02083630  str r3, [sp]          ; its arg4 -> constructor arg5
0x02083634  mov r3, #0            ; constructor arg3 = 0
0x02083638  str ip, [sp, #4]      ; its stack arg -> constructor arg6
0x0208363C  bl  #0x20834d4
```

`r0`/`r1`/`r2` pass through untouched; `arg3` is forced to `0` and the remaining arguments shift down one.
So the subsystem has **two entry points**: the full six-argument constructor, and this convenience wrapper
that supplies no category.

## 5. `arg6` is zero at every ov6 site

`0x02164F08` and `0x02164F44` store `r5` after `mov r5, #0`; `0x02168E40` stores `r7` after `mov r7, #0`.

That argument becomes the installer's `[sp+0x34]`, which iteration 140 found packed as 2-bit fields into
`record+0x175`. With zero passed at all three battle call sites, **those packed fields are all zero in
practice** — which explains why the tail's elaborate bit-shuffling produces nothing interesting.

## Predictions status

| Claim | Verdict |
|---|---|
| `arg2`/`arg3` pass through the constructor unchanged | **CONFIRMED_STATIC** — `0x020834F0`/`0x020834F8` then `0x02083554`/`0x02083548` |
| The argument numbering is right | **CONFIRMED_STATIC** — both frames' arithmetic matches the offsets each function reads |
| `arg3` takes single-bit values | **CONFIRMED_STATIC** — `0x8000`, `0x4000`, `0x800`, and `0` |
| `record+0x38` is a category or layer mask | **CONFIRMED_STATIC** *(upgraded iteration 142)* — four consumer sites `tst` it against `0x4000`/`0x8000` in `0x02081DDC`; see `category-mask-confirmed-selects-an-axis.md` |
| Any ov6 site sets `arg2`'s low nibble | **REFUTED** — two pass `0x100`, the third `bic`s the nibble off |
| The installer's `orrne`/`0x400000` branch is dead | **not claimed** — `0x0208363C`'s `r2` is untraced |
| `record+0x3C` at the two `0x100` sites is `arg5 \| 0x20C000 \| 0x30000` | **CONFIRMED_STATIC** — `0x100 & 0x00FCFFFF` is non-zero |
| `0x02083624` forces `arg3` to zero | **CONFIRMED_STATIC** — `mov r3, #0` at `0x02083634` |
| `arg6` is zero at all three ov6 sites | **CONFIRMED_STATIC** — `0x02164F08`, `0x02164F44`, `0x02168E40` |
| `record+0x175`'s packed fields are zero in practice | **PLAUSIBLE** — follows from `arg6 = 0`, but only for the three sites checked |
| What `arg2 = 0x100` means | **not claimed** — a constant at two sites and computed at a third |

## Next angles, ranked

1. **Read a consumer of `record+0x38`** (or `node+0x18`). With three distinct bits in hand, one comparison
   site would turn the category-mask reading from PLAUSIBLE into confirmed.
2. **Trace `0x02083624`'s caller** to settle whether the installer's low-nibble branch is dead — it is the
   only remaining path to `arg2`'s low bits.
3. **Read `0x0201899C`** (carried) — the call whose output iteration 140 proved is discarded.
4. **Identify the three ov6 callers**, which are in the battle overlay and should have census names nearby.
