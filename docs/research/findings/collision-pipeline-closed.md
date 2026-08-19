# Findings: the contact-array chain closed, and an 8-stage per-frame collision pipeline

Loop-Atlas iteration 57. Static.

Iteration 56 found the contact-array writer but left one link unproven: whether `r10` at `0x02081340`
holds the ColPrm manager. **It does.** The chain is verified end to end — writer and query 71 touch the
same array. Upgraded from PLAUSIBLE to **CONFIRMED_STATIC**, closing a four-wake search.

Tracing also showed `0x0207F480` is not what iteration 55 called it: it is a **440-instruction per-frame
collision driver running an 8-stage pipeline**, not a reset routine.

---

## 1. The chain, end to end

```
0x0207F480   callback registered on ColPrm+0xE0   (word ref at 0x0207C860, in the ctor)
0x0207F484     ldr r0, [r0, #0x4]
0x0207F48C     ldr r6, [r0, #0x10]      ; r6 = the ColPrm manager (back-pointer)
                 ... r6 written 0 times in the following 440 instructions ...
0x0207FA98     mov r0, r6               ; r0 = the manager
0x0207FA9C     bl 0x02080C28
0x02080C28   push {r4, lr} ; mov r4, r0 ; bl 0x02080F14      (thin forwarder)
0x02080F14   push {...}
0x02080F20     mov sl, r0               ; r10 = the manager
0x0208133C     add r2, sl, #0x154       ; the contact array
0x02081344     mla r1, r0, r1, r2       ; + row * 0xC0
0x0208134C     mla r2, fp, r0, r1       ; + column * 0x30
0x0208135C     str r0, [r2, #0x10]      ; element += value
```

Every step is direct, not inferred:

- `0x0207F480` is the `+0xE0` callback — its address is a word at `0x0207C860`, in the constructor's registration region (iteration 55).
- `r6` is the manager back-pointer via `[subobj+4]+0x10`, the same access both ColPrm callbacks use.
- **`r6` is written zero times** between load and call — no reassignment possible. Same guard that caught three phantom fields in iterations 49–50, used here as a positive check.
- `0x02080C28` is a four-instruction forwarder; `r0` passes straight through.
- `0x02080F14` does `mov sl, r0`, so `r10 = arg0 = the manager`.

## 2. The 8-stage per-frame pipeline

Every `mov r0,r6` + `bl` pair in `0x0207F480`'s body:

| stage | site | target |
|---|---|---|
| 1 | `0x0207FA60` | `0x0207FBD0` |
| 2 | `0x0207FA68` | `0x02080C70` |
| 3 | `0x0207FA70` | `0x02080E5C` |
| 4 | `0x0207FA78` | `0x020801FC` |
| 5 | `0x0207FA80` | `0x02080510` |
| 6 | `0x0207FA88` | `0x020805E8` |
| 7 | `0x0207FA90` | `0x020802D0` |
| 8 | `0x0207FA98` | `0x02080C28` → `0x02080F14` → the contact-array accumulators |

Eight consecutive calls, all passing the ColPrm manager as `arg0`. This is the collision system's per-frame sequence; the contact array is filled in its final stage.

## 3. Correction: `0x0207F480` is a driver, not a reset

Iteration 55 called it "the per-frame reset" that drains 22 buckets. The function is **440 instructions**
ending at `0x0207FB60`; the bucket drain is roughly its first 20. The drain is the opening phase of a much
larger routine that then runs the eight stages above.

Same mistake as iteration 54's "handler table" and iteration 53's "hot fields": I printed part of a
function and named the whole thing. Three wakes, same failure. Fix: establish a function's *extent* before
describing it — one instruction's work (find the next prologue).

## Predictions status

| Claim | Verdict |
|---|---|
| `r10` at `0x02081340` is the ColPrm manager | **CONFIRMED_STATIC** — chain verified, `r6` has 0 writes across 440 instructions |
| The writer's array is the one query 71 reads | **CONFIRMED_STATIC** *(was PLAUSIBLE, iteration 56)* |
| `0x0207F480` runs an 8-stage pipeline on the manager | **CONFIRMED_STATIC** — 8 `mov r0,r6`+`bl` pairs, `0x0207FA60`–`0x0207FA98` |
| The contact array is filled in the pipeline's last stage | **CONFIRMED_STATIC** — stage 8 reaches the accumulators |
| `0x0207F480` is a reset routine | **REFUTED** *(my own, iteration 55)* — 440 instructions; the drain is its first ~20 |
| `0x02080C28` does anything but forward | **REFUTED** — four instructions, passes `r0` through |

## The collision subsystem as it now stands

```
*(0x0214BE10) = BattleColPrm manager
  +0x28..+0xD7   22 bucket list heads      drained each frame by 0x0207F480's opening phase
  +0xD8          free list
  +0xE0          sub-object -> callback 0x0207F480  = the per-frame driver, 8 stages
  +0xE4          sub-object -> callback 0x0207FB60  = phase driver (2 stubs + 1 live)
  +0xE8          sub-object -> callback 0x0207FBB0  (bx lr stub)
  +0xFC..+0x148  19-entry phase table, all excluded as array writers
  +0x154         contact array: rows 0xC0, elements 0x30, 4 per row
                   element +0x04  written by 0x02081418   READ by ov6 query 71
                   element +0x08  written by 0x020813D0
                   element +0x0C  written by 0x02081388
                   element +0x10  written by 0x02081340
                   element +0x1C                          READ by ov6 query 71
                   element +0x28  written by 0x02081340
```

## Next angles, ranked

1. **Identify the accumulated values** — `[sp,#0x4c]` and `r7` at stage 8. If these are damage figures,
   the array is a per-pair damage ledger, connecting collision directly to the damage-pipeline questions
   open since early in the campaign.
2. **Read stages 1–7.** Seven unexamined functions, all taking the manager, once per frame. Stage ordering
   should reveal the broadphase/narrowphase split.
3. **Decode `0x02081A58`** (packed nibbles → row index) — defines what the array's rows represent.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
