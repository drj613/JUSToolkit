# Findings: the collision pipeline's bucket dataflow

Loop-Atlas iteration 62. Static.

Scanned the four stages iteration 61 left unattributed, restricting each to its **provable register
lifetime** instead of the whole function.

**Every consumer stage reads exactly one bucket in its first few instructions.** 9 of 22 buckets are now
assigned.

---

## 1. The method that worked

Iteration 61 failed on stages 4–7 because `arg0` gets reassigned 3, 16, 10 and 24 times, making a
whole-function scan meaningless. Fix: scan from function entry **until the first write to that register**
— the window where the manager is still live.

The windows are tiny — 4, 7, 2 and 14 instructions — each with exactly one bucket access:

| stage | address | window | bucket access |
|---|---|---|---|
| 4 | `0x020801FC` | 4 instrs | `0x02080208 ldr r1,[r0,#0x50]` → bucket 5 |
| 5 | `0x02080510` | 7 instrs | `0x02080514 ldr sb,[r0,#0xa8]` → bucket 16 |
| 6 | `0x020805E8` | 2 instrs | `0x020805E8 ldr ip,[r0,#0xd0]` → bucket 21 |
| 7 | `0x020802D0` | 14 instrs | `0x020802DC ldr r6,[r0,#0x80]` → bucket 11 |

Each stage grabs its list then immediately reuses the register for the walk. **The bucket access is always
in the first four instructions** — whole-function scanning didn't just add noise, it pointed the wrong way.

Stage 7 also saves the manager (`str r0,[sp]` at `0x020802D8`) and reloads it at `0x020803B4` and
`0x020803C4`. Neither reload is followed by a bucket access, so bucket 11 is its only input.

### A scan bug of my own

My first pass started the walk at `f+4`, assuming a `push` prologue. **Stage 6 has no prologue** — it
opens with `ldr ip,[r0,#0xd0]` — so the scan skipped the only bucket access. Off-by-one from assuming a
calling convention instead of reading the actual first instruction.

### What iteration 61's contaminated scan got wrong

| stage | contaminated claim | verified |
|---|---|---|
| 5 | buckets 7, 16, 21 | **16 only** |
| 6 | buckets 7, 21 | **21 only** |
| 7 | bucket 11 | **11** ✓ |

Partly right by luck. Bucket 7 was spurious in both — exactly why iteration 61 held them back.

## 2. The dataflow

| bucket | filled by | consumed by |
|---|---|---|
| 1 | ? | stage 8's callee `0x02080F14` (iteration 60) |
| **5** | stage 1 (`0x0207FF98`) | stage 4 |
| **6** | the **driver itself** at `0x0207F6B4` *(iteration 63 — not external as stated here)* | stage 1, as its **source list** |
| **7** | stage 1 (`0x0207FD94`) | stage 2 |
| 8 | ? | stage 3 |
| 11 | ? | stage 7 |
| **15** | stage 1 (`0x02080118`) | *no consumer found* |
| **16** | stage 1 (`0x02080008`) | stage 5 |
| 21 | ? | stage 6 |

Three complete producer→consumer chains: **5 → stage 4**, **7 → stage 2**, **16 → stage 5**.

Bucket 6 is the pipeline's entry point — stage 1 drains it, nothing in the eight stages fills it, so
entities arrive from outside the per-frame driver.

Bucket 15 is filled by stage 1 but no stage reads it. Its consumer is outside the pipeline, or the
remaining gaps (15 with no consumer; 8/11/21 with no producer) pair up somewhere I haven't looked.

## 3. Shape of the whole thing

```
external code inserts into bucket 6
  stage 1  drains bucket 6, classifies each entry -> buckets 5, 7, 15, 16
  stage 2  reads bucket 7
  stage 3  reads bucket 8
  stage 4  reads bucket 5
  stage 5  reads bucket 16
  stage 6  reads bucket 21
  stage 7  reads bucket 11
  stage 8  -> 0x02080C28 -> 0x02080F14, reads bucket 1,
             runs the narrowphase pair test and fills the contact matrix at +0x154
```

Stage addresses: 1 `0x0207FBD0`, 2 `0x02080C70`, 3 `0x02080E5C`, 4 `0x020801FC`, 5 `0x02080510`,
6 `0x020805E8`, 7 `0x020802D0`, 8 `0x02080C28`.

One classifier, seven per-category workers. The buckets are **categories**, not spatial cells — a spatial
hash would compute an index, but stage 1 branches to four fixed destinations.

## Predictions status

| Claim | Verdict |
|---|---|
| Stages 4–7 can be attributed by restricting to a register lifetime | **CONFIRMED** — windows of 4, 7, 2 and 14 instructions |
| Stage 4 reads bucket 5 | **CONFIRMED_STATIC** — `0x02080208` |
| Stage 5 reads bucket 16 | **CONFIRMED_STATIC** — `0x02080514` |
| Stage 6 reads bucket 21 | **CONFIRMED_STATIC** — `0x020805E8`, the function's first instruction |
| Stage 7 reads bucket 11, and only that | **CONFIRMED_STATIC** — two `[sp]` reloads, no further bucket |
| Each consumer stage reads exactly one bucket | **CONFIRMED_STATIC** — all four, in the first 4 instructions |
| Iteration 61's contaminated attributions | **REFUTED** — bucket 7 spurious for stages 5 and 6 |
| Stage 6 has no bucket access | **REFUTED** *(my own, this wake)* — scan started at `f+4`; stage 6 has no prologue |
| The buckets are spatial-hash cells | **not claimed** — stage 1 branches to four fixed destinations, which looks categorical |

## Next angles, ranked

1. **Find what inserts into bucket 6.** The pipeline's sole input — producer is outside the eight stages,
   likely where entities register each frame.
2. **Identify stage 1's four branch conditions** that sort entries into buckets 5, 7, 15 and 16.
3. **Find bucket 15's consumer** and the producers for buckets 8, 11 and 21.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
