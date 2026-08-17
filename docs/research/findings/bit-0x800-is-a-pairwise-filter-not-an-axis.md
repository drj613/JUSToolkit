# Findings: category bit `0x800` is a pairwise control bit, not an axis selector

Loop-Atlas iteration 143. Static.

Iteration 142 mapped `+0x38` bits `0x4000` and `0x8000` to axes and noted that nothing tested `0x800`,
the third bit a real caller passes. Three consumer sites turned up. **`0x800` is not an axis bit** — it is a
control bit tested on *both members of a pair*, and its polarity flips between the two places that use it.

---

## 1. Finding the sites

`tst` against `#0x800` turns up 13 candidates across arm9. Keeping only those whose immediately preceding
instruction loads `+0x38` narrows the list to exactly three, all in the ColPrm module:

| site | containing function |
|---|---|
| `0x0207F7A0` | `0x0207F480` (1736 bytes, 0 callers) |
| `0x0207FFD4` | `0x0207FBD0` (1572 bytes, 1 caller) |
| `0x0207FFE4` | `0x0207FBD0` |

The "preceded by a `+0x38` load" filter is what made this manageable — most `tst #0x800` sites in this module
test the ColPrm record's `+0x40` flags, where `0x800` was already known to gate delta application.

## 2. Tested on both members of a pair

```
0x0207FFC8  bne #0x20801d4            ; an earlier test, same target
0x0207FFCC  ldr r0, [r5, #0xc]
0x0207FFD0  ldr r0, [r0, #0x38]       ; participant A's mask
0x0207FFD4  tst r0, #0x800
0x0207FFD8  bne #0x20801d4            ; set -> branch away
0x0207FFDC  ldr r0, [r6, #0xc]
0x0207FFE0  ldr r0, [r0, #0x38]       ; participant B's mask
0x0207FFE4  tst r0, #0x800
0x0207FFE8  bne #0x20801d4            ; set -> branch away
0x0207FFEC  ldr r5, [r8, #0xd8]       ; otherwise: the bucket free list
```

Two different bases, `r5` and `r6`, each reach a record through `+0xC` — the same indirection iteration
142 saw as `[r7+0xC]`. If **either** participant has `0x800` set, execution jumps to `0x020801D4`, a target
shared with at least one earlier test. Only when both are clear does it fall through to `[r8+0xD8]`, the
bucket free list from iterations 68–69.

This is a **pairwise pre-filter**: either party's bit can veto the operation.

## 3. The other site works the opposite way

```
0x0207F794  tst r1, r0
0x0207F798  bne #0x207f7a8            ; the mask test passed -> proceed
0x0207F79C  ldr r0, [r4, #0x38]
0x0207F7A0  tst r0, #0x800
0x0207F7A4  beq #0x207f7c8            ; CLEAR -> skip
0x0207F7A8  ldr r5, [r6, #0xd8]       ; proceed, again to the bucket free list
```

Here the flow is: proceed if `(r1 & r0) != 0` **or** `(+0x38 & 0x800)`. Bit `0x800` **set** lets the operation
through when the preceding test failed — an OR-bypass.

**The polarity is opposite between the two sites.** At `0x0207FFD4`/`0x0207FFE4`, set means *branch away*; at
`0x0207F7A0`, set means *proceed*. Both eventually reach the same `+0xD8` bucket free list.

Recorded as observed, **not reconciled**. The two are different operations — one is a pairwise pre-filter on
two participants, the other is a single-object bypass after a mask test — so a bit meaning "handle this
specially" could reasonably route to different paths in each case. But nothing here settles that, and
iteration 127 is the cautionary precedent: I labelled an asymmetry before reading the callee and got it wrong.

## 4. What this says about `+0x38`

The field packs two kinds of bit:

| bits | role |
|---|---|
| `0x4000`, `0x8000` | **axis selectors** — which accumulator an adjustment may move (iteration 142) |
| `0x800` | **a control bit** — tested per-participant, gating whether an operation happens at all |

So `+0x38` is not a pure "which layer am I" mask. It carries both geometry selectors and behavioural
control in one word — worth knowing before assuming any new bit is another axis.

## 5. One thing I am not claiming

`0x0207F794`'s `tst r1, r0` is a **mask-against-mask** test, exactly the shape of a
"do these two layers interact" check, and would strongly support the category reading. But
neither operand is traced — they are set before the window I read. **Not claimed.**

## Predictions status

| Claim | Verdict |
|---|---|
| Bit `0x800` of `+0x38` has a consumer | **CONFIRMED_STATIC** — three sites: `0x0207F7A0`, `0x0207FFD4`, `0x0207FFE4` |
| `0x800` is a third axis selector | **REFUTED** — it gates whether an operation proceeds, and no accumulator is tied to it |
| `0x800` is tested on both members of a pair | **CONFIRMED_STATIC** — `[r5+0xC]` and `[r6+0xC]` at `0x0207FFD0`/`0x0207FFE0`, both branching to `0x020801D4` |
| `0x800` has consistent polarity | **REFUTED** — set branches away at `0x0207FFD4`/`0x0207FFE4`, set proceeds at `0x0207F7A0` |
| Both paths lead to the bucket free list | **CONFIRMED_STATIC** — `[r8+0xD8]` at `0x0207FFEC`, `[r6+0xD8]` at `0x0207F7A8` |
| The record is reached via `+0xC` in both sites | **CONFIRMED_STATIC** — matches iteration 142's `[r7+0xC]` |
| `+0x38` holds only layer/category bits | **REFUTED** — it mixes axis selectors with behavioural control |
| `0x0207F794`'s `tst r1, r0` is a layer-versus-layer test | **not claimed** — neither operand traced |
| Why the polarity differs | **not claimed** — the two are different operations; nothing read decides it |

## Next angles, ranked

1. **Trace `0x0207F794`'s `r1` and `r0`.** If both come from `+0x38`, that is a mask-against-mask layer test
   and would explain the whole field in one stroke.
2. **Read `0x020801D4`**, the shared reject target in `0x0207FBD0`. Confirming it is "skip this pair and
   continue" would settle the polarity question from the other end.
3. **Identify `0x0207F480`** — 1736 bytes, **0 callers**, so it is installed as a function pointer; the
   largest unexamined function in the ColPrm module.
4. **Trace `0x02083624`'s caller** (carried) — decides whether the installer's `0x400000` branch is dead.
