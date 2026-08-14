# C5 — the damage field is +0x134, and it was in the queue all along

Loop-Atlas iteration 28. Static. **The stuck damage thread is unstuck** — thanks to a note the previous campaign left in `GDB-Validation-Queue.md`.

## Two trampolines, and I only ever traced one

Card 3 of the queue says:

> **Note (Phase-0): a sibling DRAIN trampoline exists at `0x020783B8`** (same `+0x56c` target, negates its delta)

Dead on, and I'd never read it. Static confirmation:

```asm
0x020783B8  ldr r12,[pc,#0x8]     ; = 0x02078488
0x020783BC  ldr r0,[r0,#0x56C]
0x020783C0  rsb r1,r1,#0x0        ; <-- NEGATES the delta
0x020783C4  bx  r12

0x020783CC  ldr r12,[pc,#0x4]     ; = 0x02078488
0x020783D0  ldr r0,[r0,#0x56C]
0x020783D4  bx  r12               ; no negation
```

A caller that wants to *subtract* HP passes a **positive magnitude** to `0x020783B8`. I found 14 callers of the plain trampoline and correctly classified them all as heals, status ticks, and dispatchers — because **damage doesn't use that trampoline.** It uses the drain one, which has only **2 callers**. I never looked at them.

## The damage field is +0x134, not +0x140

`0x0215AC70` (ov6, same state dispatcher) calls the drain trampoline. Its magnitude comes from:

```asm
0x0215AC00  ldr r1,[r5,#0x1A8]
0x0215AC04  ldr r1,[r1,#0x10]
0x0215AC08  ldr r4,[r1,#0x134]   ; <-- damage magnitude
...
0x0215AC68  ldr r0,[r5,#0x1B4]
0x0215AC6C  mov r1,r4
0x0215AC70  bl  0x020783B8       ; drain -> negated -> HP
```

Compare the accumulator flush I proposed earlier:

```asm
0x0215A300  ldr r0,[r6,#0x1A8]
0x0215A304  ldr r0,[r0,#0x10]
0x0215A308  ldr r1,[r0,#0x140]   ; heal delta
```

**Same chain** — `[char + 0x1A8] → +0x10` — but reading a different field. That object holds a family of pending deltas:

| offset | meaning | applied via |
|---|---|---|
| **`+0x134`** | **pending HP damage** (positive magnitude) | `0x020783B8` drain, negates |
| `+0x138` | pending SP drain | `rsb` then `0x020781E4` |
| `+0x140` | pending HP heal | `0x020783CC` plain |
| `+0x144` | pending SP add | `0x020781E4` |

My accumulator hypothesis was **right in shape, wrong by 12 bytes.** The harness watched `+0x140` and read 0 every frame — correctly, because that's the *heal* field. Damage was at `+0x134` the whole time.

The other drain caller, Thumb `0x021518D6`, passes `mov r1,#2; lsl r1,#10` = 2048 raw = **32.0 displayed** — a fixed scripted drain, not variable damage.

## The lesson

I spent five wakes enumerating callers, scanning offsets, and building tools. The pointer I needed was already written in the project's own validation queue by an earlier phase. **I never read the queue before starting the hunt.** I read `Battle-Engine-Map.md` (the conclusions) and skipped the document listing what was known-but-unverified.

The queue is where a prior campaign parked its loose ends — exactly what a later campaign needs. Reading conclusions and skipping loose ends is how you re-derive work that was already done.

## The card, now trivial

Watch `[character + 0x1A8] → +0x10 → +0x134` as a word per frame, or breakpoint `0x0215AC08` and log `r4`. On a landed 6.000 hit it should read **+384** (positive; the trampoline negates).

Single-value check, specific predicted number. As sharp as a card gets.

## Confidence

**CONFIRMED_STATIC** that `0x020783B8` negates its delta, that `0x0215AC70` calls it, and that its magnitude loads from `+0x134` off the same `[+0x1A8]→+0x10` chain as the `+0x140` heal field.

**PLAUSIBLE** that this is the melee path specifically. It's a pending-damage field in the battle state dispatcher — the right shape — but I've been wrong about shape being sufficient before, and the value hasn't been observed yet.
