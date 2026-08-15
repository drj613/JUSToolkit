# Findings: buckets 1 and 8 are never filled — two dead read paths

Loop-Atlas iteration 64. Static.

Collision buckets 1 and 8 have consumers but no producer. Both are read every frame and written by
nothing in the ROM — stage 3's bucket-8 walk and `0x02080F14`'s bucket-1 walk always see an empty list.

Finding this required closing a **gap in iteration 63's census**: it resolved link-call targets only from
immediate adds, leaving six computed-base calls unexamined.

---

## 1. The gap in my own census

Iteration 63 concluded producers were known for 14 of 22 buckets, from a census that recovered `r0`'s origin only for `add r0,rN,#imm` — immediate offsets. A generic
bucket insert computes `manager + 0x28 + idx*8`, which the census couldn't see. **6 link calls use a
shifted-register base**, four with `lsl #3` — the bucket stride. Resolving all four:

| site | computed base | is it ColPrm's array? |
|---|---|---|
| `0x0207BF40` | `*(0x0214BE0C) + r5*8` | **no** — a different global |
| `0x0207BFF0` | `*(literal) + r6*8` | **no** — same shape, array at offset 0 |
| `0x02083BBC` | `*(r0) + 0x74 + r5*8` | **no** — array at `+0x74` |
| `0x02083D5C` | `r7 + 0x24 + r5*8` | **no** — array at `+0x24` |

All four index arrays at offset `0`, `+0x24`, or `+0x74` — none at ColPrm's `+0x28`. Iteration 63's
conclusion survived, but by luck, not by having been tested.

## 2. Four independent checks, all negative

| check | result |
|---|---|
| 145 immediate-offset link calls (`0x02037B98`) | none targets `+0x30` or `+0x68` |
| 6 computed-base link calls | none targets ColPrm's bucket array |
| 3 sibling list helpers — `0x02037B54` (5 callers), `0x02037BD8` (2), `0x02037C54` (1) | none targets them |
| direct stores at `+0x30`/`+0x68` off a verified manager register, across the driver, stages 1–3 and `0x02080F14` | **0** |

The last check covers all five regions where the manager register is known and single-write — no
immediate-offset store could hide. **Nothing writes bucket 1 or bucket 8.**

## 3. Consequence: two dead read paths

Both buckets have confirmed consumers:

- **bucket 1** — `0x02080F14` opens `ldr r5,[sl,#0x30]` (iteration 60), the narrowphase pair-test function
- **bucket 8** — stage 3 opens `ldr r6,[r4,#0x68]` (iteration 62)

Both read an empty list every frame. The driver's (`0x0207F480`) drain walks all 22 buckets; for these two it finds a null
head and the inner loop never runs.

Second dead region this campaign has found, after dispatcher cases 1–33 (iteration 48). Same pattern:
handler code present in the binary but not exercised in this build.

Static-reachability caveat: no *code* writes those heads. A value arriving outside the four checks remains
possible, though the checks now span immediate offsets, computed offsets, all sibling helpers, and direct
stores.

### What it means for `0x02080F14`

Iteration 60 showed this function walks bucket 1 and calls the narrowphase pair test. If bucket 1 is
always empty, **the pair test never runs** — yet iterations 56–57 confirmed real contact-array accumulators
on the chain behind it.

Does `0x02080F14` also walk a *live* bucket? **No.** All **6** bucket-range accesses off `r10` (the
single-write manager anchor from iteration 60) target `+0x30` — bucket 1. No computed bucket form
(`add rD,r10,rM,lsl #3`), no walk from `r10+0x28`. It reads bucket 1 and nothing else.

The contradiction is real, not a scanning gap. Real accumulators on a real chain, reached through a list
nothing fills. **This is the sharpest case yet for the harness watchpoint** — a read watchpoint on
`ColPrm+0x154` settles in one run whether the narrowphase output is ever written.

## 4. A fourth manager global

`0x0207BF40`'s base is `*(0x0214BE0C)`, not previously known. The globals block now holds four:

```
0x0214BD80  chr_b base pointer                                   (earlier campaign)
0x0214BE0C  a manager with an 8-stride list array AT OFFSET 0     (new)
0x0214BE10  BattleColPrm manager                                 (iteration 52)
0x0214BE14  BattleObj manager                                    (iteration 52)
```

Its array is indexed by a small register (`cmp r6,#2` after one insertion), so the index space is small.

## Predictions status

| Claim | Verdict |
|---|---|
| Buckets 1 and 8 have producers that bypass the link helper | **REFUTED** — they have no producer at all |
| Iteration 63's census covered all link calls | **REFUTED** *(my own)* — immediate offsets only; 6 computed-base calls unexamined |
| One of the computed-base link calls targets ColPrm's buckets | **REFUTED** — bases at offset `0`, `+0x24`, `+0x74` |
| A sibling list helper fills bucket 1 or 8 | **REFUTED** — 8 calls total across three helpers, none matching |
| A direct store fills bucket 1 or 8 | **REFUTED** — 0 across five verified-manager regions |
| Stage 3 and `0x02080F14`'s bucket walks are dead in this build | **CONFIRMED_STATIC** — consumers with no producer |
| `0x0214BE0C` is a manager global with an 8-stride list array | **CONFIRMED_STATIC** — `0x0207BF40` |
| The contact-array accumulators execute | **contradictory** — real chain (iterations 56–57) but reached via an always-empty bucket |
| `0x02080F14` also walks a live bucket, dissolving the contradiction | **REFUTED** — 6 of 6 bucket accesses are bucket 1; no computed form |

## Next angles, ranked

1. **Escalate the harness watchpoint.** The bucket-1 contradiction makes it decisive, not just useful:
   a read watchpoint on `ColPrm+0x154` answers in one run whether the narrowphase output is ever written.
   Recipe in iteration 45.
2. **Identify `*(0x0214BE0C)`** — a fourth manager next to two already named.
3. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values.
