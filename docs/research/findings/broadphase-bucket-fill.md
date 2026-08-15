# Findings: stage 1 fills the collision buckets

Loop-Atlas iteration 61. Static.

Scanned the seven unexamined collision-pipeline stages to find where the 22 buckets get filled.
**Stage 1 (`0x0207FBD0`) is the filler**: it reads bucket 6 as a source list and distributes entries
into buckets 5, 7, 15 and 16.

Stages 2 and 3 consume buckets 7 and 8. **Stages 4–7 are undetermined** — `arg0` is reassigned too
often for offset attribution to work, so they are left unattributed rather than guessed.

---

## 1. Stage 1 is the bucket filler

```
0x0207FBD0  push 0x4FF0
0x0207FBD8  mov r8, r0            ; r8 = the ColPrm manager — written EXACTLY ONCE in 395 instructions
0x0207FBDC  ldr r5, [r8, #0x58]   ; bucket 6 — the source list
...
0x0207FD94  bl 0x02037B98         ; link, r0 = r8+0x60   -> bucket 7
0x0207FF98  bl 0x02037B98         ; link, r0 = r8+0x50   -> bucket 5
0x02080008  bl 0x02037B98         ; link, r0 = r8+0xA8   -> bucket 16
0x02080118  bl 0x02037B98         ; link, r0 = r8+0xA0   -> bucket 15
```

`r8` receives `r0` and is **never written again** across the whole function — the single-write anchor
from iteration 60. Every `[r8,#imm]` is provably a manager field.

Bucket indices follow from the array base at `+0x28` with stride 8 (iteration 55): `0x50`→5, `0x58`→6,
`0x60`→7, `0xA0`→15, `0xA8`→16. All five offsets are 8-aligned, as bucket heads must be.

Stage 1 also makes **4 unlink calls** (`0x02037C24`) to match its 4 links — entries are removed from
the source before being filed.

Broadphase fill: **pending entries accumulate in bucket 6; stage 1 classifies each into one of four
destination buckets.**

## 2. Stages 2 and 3: same routine, adjacent buckets

Both are **46 instructions** and structurally identical:

| stage | address | bucket | accesses |
|---|---|---|---|
| 2 | `0x02080C70` | 7 | `0x02080C7C add r0,r4,#0x60`; `0x02080C84 ldr r6,[r4,#0x60]` |
| 3 | `0x02080E5C` | 8 | `0x02080E68 add r0,r4,#0x68`; `0x02080E70 ldr r6,[r4,#0x68]` |

Each has two writes to `r4`, but the second (`add r4,sp,#0x10`) occurs **after** the bucket accesses
(`0x02080C8C` and `0x02080E78`), so the attribution holds. Same routine, adjacent buckets.

## 3. Stages 4–7: not determined, and why

| stage | address | size | writes to `arg0`'s register |
|---|---|---|---|
| 4 | `0x020801FC` | 53 | 3 |
| 5 | `0x02080510` | 84 | **16** |
| 6 | `0x020805E8` | 30 | **10** |
| 7 | `0x020802D0` | 144 | **24** |

A first pass reported buckets for all four. With `r0` reassigned 16 or 24 times, any `[r0,#0x50]` in
the body could be another object's field, not the manager's — so those attributions are **not** recorded.
Determining them needs per-site anchored scans, one register-lifetime at a time.

Stage 8 touches no buckets (consistent with iteration 60) — it is the narrowphase driver.

## 4. A base-register count, again

First scan of stage 1 reported **22** accesses in the bucket byte range. Constrained to the verified
manager register, the real count is **5**. The other 17 used other base registers that happened to land
in the same numeric range.

22 looked right because the array has 22 buckets. A number matching expectation is not confirmation
when the measurement is unconstrained — the coincidence made a contaminated count look like a clean sweep.

## The bucket map so far

| bucket | role | evidence |
|---|---|---|
| 5 | filled by stage 1 | link at `0x0207FF98` |
| 6 | **source list** read by stage 1 | `ldr r5,[r8,#0x58]` |
| 7 | filled by stage 1, consumed by stage 2 | link at `0x0207FD94`; stage 2 reads it |
| 8 | consumed by stage 3 | stage 3 reads it |
| 15 | filled by stage 1 | link at `0x02080118` |
| 16 | filled by stage 1 | link at `0x02080008` |

6 of 22 buckets have a verified role. The remaining 16 have no trusted attribution yet.

## Predictions status

| Claim | Verdict |
|---|---|
| One of stages 1–7 fills the buckets | **CONFIRMED_STATIC** — stage 1, 4 link calls |
| Stage 1's `r8` is the manager | **CONFIRMED_STATIC** — `mov r8,r0`, written exactly once in 395 instructions |
| Stage 1 reads bucket 6 and fills 5, 7, 15, 16 | **CONFIRMED_STATIC** — all five offsets 8-aligned in the array |
| Stages 2 and 3 consume buckets 7 and 8 | **CONFIRMED_STATIC** — reassignment occurs after the accesses |
| Stages 2 and 3 are the same routine on different buckets | **PLAUSIBLE (strong)** — both 46 instructions, identical shape |
| Stages 4–7 touch buckets 5, 7, 11, 16, 21 | **not claimed** — `arg0` reassigned 3/16/10/24 times; attribution unreliable |
| Stage 1 touches 22 bucket-range offsets | **REFUTED** — 5 with a verified base; 22 was an unconstrained count |
| Stage 8 touches buckets | **REFUTED** — none, consistent with it being the narrowphase driver |

## Next angles, ranked

1. **Anchor-scan stages 5 and 7.** Largest unattributed stages (84 and 144 instructions); need
   per-register-lifetime anchors, not a whole-function scan.
2. **Identify what distinguishes buckets 5, 7, 15, 16** — branch conditions before each link define
   the classification.
3. **Trace `0x02081A58`** (packed nibbles → contact-matrix row index). Open.
4. Open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, the harness watchpoint recipe for the walker.
