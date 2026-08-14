# C6c — all 8 ARM callers classified; pending-damage accumulator found

Loop-Atlas iteration 22. Static analysis of raw `ov06.bin`.

All 14 callers of the HP-apply function are now classified. The likely melee path is an accumulator that stores pending damage until a per-frame flush consumes it.

## The eight ARM callers

| site | enclosing fn | what it is |
|---|---|---|
| `0x02157DC0` | `0x02157A44` (+0x37C) | large dispatcher; delta is a function argument (`mov r4,r3`) |
| `0x021582C4` | `0x0215807C` (+0x248) | same shape |
| `0x02158BC0` | `0x02158B20` (+0xA0) | mid-size handler, delta in `r4` |
| `0x02159274` | `0x02159260` (+0x14) | **thin script wrapper**, displayed units |
| `0x021592D0` | `0x021592C0` (+0x10) | **thin script wrapper**, raw units |
| `0x0215952C` | `0x02159500` (+0x2C) | status opcode `0x1D` — poison tick |
| `0x02159668` | `0x02159624` (+0x44) | status opcode `0x1B` — burn tick |
| `0x0215A318` | `0x02159EF8` (+0x420) | **accumulator flush** — see below |

## Thin script-wrapper family

Five siblings, all shaped `(context, node)` — they read a **signed halfword at `node->[4]->[4]`** and apply it:

| wrapper | scaling | target |
|---|---|---|
| `0x02159260` | `lsl r1,r1,#6` → **displayed units** | HP, one target |
| `0x02159280` | none → raw units | (target unresolved) |
| `0x021592A0` | `lsl #6` → displayed units | `0x020783DC` — the **all-living-characters** variant |
| `0x021592C0` | none → raw units | HP, one target |
| `0x021592DC` | none → raw units | **SP** |

The script VM uses separate opcodes for HP vs SP, displayed vs raw units, single-target vs everyone. The `lsl #6` converts "authored in displayed HP" to machine units. The value is **signed**, so one opcode handles both damage and healing.

## 0x020781E4 is the SP-apply sibling

Its 19 call sites appear **immediately after** HP-apply sites — `0x02157DD0` after `0x02157DC0`, `0x021582D4` after `0x021582C4`, `0x02158BCC` after `0x02158BC0`, `0x0215A334` after `0x0215A318`. Handlers apply HP and SP deltas as a pair.

## The likely melee path: a pending-damage accumulator

Inside per-character state dispatcher `0x02159EF8`:

```asm
0x0215A300  ldr r0,[r6,#0x1A8]
0x0215A304  ldr r0,[r0,#0x10]
0x0215A308  ldr r1,[r0,#0x140]   ; pending HP delta
0x0215A30C  cmp r1,#0
0x0215A310  beq 0x0215A31C       ; skip if nothing pending
0x0215A314  ldr r0,[r6,#0x1B4]   ; target
0x0215A318  bl  0x020783CC       ; apply

0x0215A31C  ldr r0,[r6,#0x1A8]
0x0215A320  ldr r0,[r0,#0x10]
0x0215A324  ldr r1,[r0,#0x144]   ; pending SP delta
0x0215A328  cmp r1,#0
0x0215A32C  beq …
0x0215A334  bl  0x020781E4       ; apply SP
```

`[r6+0x1A8] → +0x10 → +0x140` holds a **pending HP change**. It's flushed once per dispatcher pass and skipped when zero. `+0x144` is the SP equivalent.

This is the strongest melee-damage candidate so far, and it explains something the harness session kept running into: the delta always arrived **pre-computed** at the apply sites. Of course — it's read from an accumulator that something else already filled.

### Connection to hitbox-priority

`0x02159EF8` is the function `Battle-Engine-Map.md` claim 4 flagged as "architecturally the right neighborhood for clash resolution" (rated SPECULATIVE because no two-entity comparison was found inside it). The accumulator flush gives that claim a concrete mechanism to hang on. Whoever *writes* `+0x140` is the damage producer — and that write is where resistance (the flat −2) must be applied.

Still SPECULATIVE that this is the melee path. The writer hasn't been found yet.

## Harness watch target

Watch `[character + 0x1A8] → +0x10 → +0x140` as a **word**, per frame. On a landed melee hit it should go non-zero for one frame, then return to zero as the dispatcher consumes it. This isolates melee from the heal spam and script opcodes that clutter breakpoints on the shared apply function.

If it stays zero through a hit that visibly reduces HP, melee takes a different route and this theory is refuted.

## Caller tally (complete)

- **6 Thumb** — heals (regen `+128`, full heal `16384`)
- **2 ARM** — poison and burn status ticks, value from an effect record
- **2 ARM** — thin script wrappers (displayed / raw units)
- **3 ARM** — larger dispatchers receiving the delta as an argument
- **1 ARM** — the accumulator flush

None is melee-specific. The accumulator is what reconciles that with the fact that melee damage exists.

## Correction: which object owns +0x1A8 / +0x1B4 (added 2026-08-14)

The harness session tried to watch the accumulator and got null everywhere. The cause is a level
error in how I described the chain, so here it is precisely.

`0x020783CC` is a two-instruction thunk:

```asm
0x020783CC  ldr r12,[pc,#0x4]     ; r12 = 0x02078488
0x020783D0  ldr r0,[r0,#0x56C]    ; r0 = [entity + 0x56C] = char struct
0x020783D4  bx  r12
0x020783D8  .word 0x02078488
```

and `0x02078488` takes the **char struct** (`ldrsh r2,[r0,#0x18]` = current HP). So:

```
r6 --+0x1B4--> E (entity) --+0x56C--> char struct --+0x18--> current HP
r6 --+0x1A8--> obj --+0x10--> obj2 --+0x140--> pending HP delta
```

**`+0x1A8` and `+0x1B4` belong to `r6`, which is one level ABOVE the entity.** Their scan found `E`
candidates correctly (locations pointing at the char struct, minus `0x56C`) and then read `+0x1A8`
off `E` — the wrong object, which is why every read was `0`.

### How to reach r6

`r6` is simply the first argument: `0x02159EF8` opens `push {...}` / `mov r6,r0`.

But **`0x02159EF8` has zero direct `BL`/`BLX` callers** across arm9 and all 14 overlays, so it's
invoked through a function-pointer table — consistent with a state-machine dispatcher. There's no
call site to read the argument from.

So find `r6` by structure instead. Having located an `E`, scan RAM for words equal to `E` and take
`r6 = location − 0x1B4`. Confirm the candidate against `r6`'s other fields:

| offset | contents |
|---|---|
| `+0x14` | halfword flags; the function's first act is `ldrh r0,[r6,#0x14]` then `tst r0,#1` |
| `+0x1A0` | pointer |
| `+0x1A8` | pointer → `+0x10` → `+0x140` accumulator |
| `+0x1B4` | pointer to the entity `E` |

A candidate satisfying "`+0x1B4` equals a known `E`" **and** "`+0x1A8` is a plausible RAM pointer" is
almost certainly right — the two-field agreement is the check, in the same spirit as the
four-consecutive-slots signature that pinned the character array.

## The writer is still unfound — my scan hit an offset collision (2026-08-14)

The harness session located `r6` using the structural recipe above (player `0x022286E0`, opponent
`0x0224E1E0`, both with `+0x14` bit 0 set; accumulators `0x0220FBD4` / `0x0220FD5C`, sitting `0x188`
apart — regular per-entity spacing). The chain fully resolves. Watching the accumulator per frame
gave **0 on all 220 frames, including the exact frames HP dropped by 384 raw.**

Not refuted, for their reason: a once-per-frame sample cannot see a value written and consumed inside
the same frame. The reads returned `0` rather than `None`, so the watch was genuine.

I tried to settle it statically by finding the writer. **That failed, and the failure is instructive.**

Scanning every binary for ARM word stores to `+0x140`/`+0x144` gave 36 sites, with exactly two in
ov6: `0x02161C54` and `0x02161C60`, adjacent and mirroring the flush pair. That looked conclusive. It
isn't — the surrounding code writes to `+0x11C`, `+0x120`, `+0x124`, `+0x128`, `+0x12C`, `+0x134`,
`+0x138`, `+0x13C`, `+0x140`, `+0x144`, `+0x148` from a literal pool whose values are
`0x0207E664`, `0x0207F050`, `0x0207E864`, `0x0207F2CC`, `0x0207E018` — **all arm9 code addresses,
each starting with a `push` prologue.** It's a **vtable initialiser**, on a different object type
that happens to have a field at the same offset.

The flush genuinely reads *data*, confirmed independently: `0x02078488` does
`ldrsh r2,[r0,#0x18]` then `adds r1,r1,r2` then `strh r1,[r0,#0x18]`, so `r1` is a numeric delta and
cannot be a pointer.

**So: the accumulator holds a delta, and its writer is not findable by offset scan.** Same mistake I
made in C3 with `strh [Rn,#0x18]` — scanning by offset without constraining the object type. Twice
now, so it's worth stating as a rule: **an offset-only scan over these binaries is not evidence about
a specific struct.** `+0x140` and `+0x18` are both commonplace.

### The decisive experiment

Breakpoint **`0x0215A308`** (`ldr r1,[r0,#0x140]`) and log `r1`. That captures the value at the
moment of consumption, immune to sub-frame timing. `r1 == -384` during a landed punch confirms the
melee hypothesis; only-zero-or-positive refutes it.
