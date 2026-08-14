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
