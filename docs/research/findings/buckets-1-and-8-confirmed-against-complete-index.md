# Findings: buckets 1 and 8 re-checked against the complete index

Loop-Atlas iteration 67. Static. Used `query.py search-imm` and `disasm`.

Re-ran the buckets-1-and-8 producer question against the **full 60,259-entry immediate-offset index** instead
of hand-picked scan windows. **Answer unchanged: no producer** — but now backed by complete ROM coverage.

By-products: a filter bug that briefly produced 159 false candidates, and a correction to the ColPrm field map.

---

## 1. Complete coverage, for comparison

| offset | total accesses | stores | store regions |
|---|---|---|---|
| `+0x30` (bucket 1) | 1054 | **352** | arm9 117, ov6 48, ov5 24, ov4 23, ov0 22, ov12 22, ov1 21, ov7 18, ov3 17, ov2 12, ov10 11, ov11 10, ov8 7 |
| `+0x68` (bucket 8) | 1059 | **147** | arm9 53, ov1 17, ov12 15, ov0 13, ov11 11, ov3 11, ov5 8, ov6 7, ov7 5, ov2 5, ov4 2 |

Earlier checks (iterations 63–65) covered the driver, stages 1–3, narrowphase, and the constructor — a few
hundred instructions out of **499 stores** ROM-wide at these two offsets. The conclusion was right, but its
evidence base was far narrower than stated.

## 2. The filter bug

First pass defined "in scope" as the span between the first and last global-load site — `0x0207C83C` to
`0x02157EC8`. That covers arm9 and every overlay, so it matched nearly everything: **159 candidate stores**,
almost all `[sp,#0x30]` stack writes.

The base register gave it away: a bucket head is a list head, and `str [sp,#0x30]` can't be one. Switching
to **per-function extents** for the 17 arm9 global-load sites (7 distinct functions), plus mapped regions
*with their known manager register*, and excluding `sp` bases, cut 159 to **1**.

`min(sites)..max(sites)` is not a scope — same class of error as iteration 61's "22 accesses in the bucket
range": an unconstrained window producing a plausible-looking count.

## 3. The one candidate, and why it fails

```
0x0207CB58: push {r3,r4,r5,r6,r7,r8,sb,sl,fp,lr}
0x0207CB5C: mov sl, r0            ; arg0 — NOT the manager
0x0207CB6C: ldr r4, [pc, #0x15c]  ; r4 = &0x0214BE10
0x0207CB70: add r6, sl, #0x10     ; a list head on arg0
0x0207CB80: ldr r7, [r6]          ; walk it
0x0207CB90: bl  #0x2037c24        ; unlink(r6, r7)
0x0207CB9C: ldr sb, [r4]          ; sb = the ColPrm manager
0x0207CBB4: add r0, sb, #0x20     ; manager + 0x20
0x0207CBB8: bl  #0x2037b98        ; link into manager+0x20
0x0207CBC0: ldr r0, [r7, #8]      ; r0 = node->[8]
0x0207CBC8: str r5, [r0, #0x68]   ; a field of node->[8], NOT the manager
```

At `0x0207CBC8`, `r0` came from `[r7+8]` where `r7` is a **list node**. The store hits that node's `+0x68`,
not the manager's. False positive.

**Seventh independent check, same answer: nothing fills bucket 1 or bucket 8.**

## 4. Correction: `ColPrm+0x20` is a list head

`0x0207CBB4`–`0x0207CBB8` links into **`manager+0x20`** — below the bucket array, which starts at `+0x28`.

Iteration 53's field map grouped `+0x00`–`+0x24` as "ten consecutive words written in order" and called it
init data. `+0x20` is actually a **list head** taking real insertions. The block is not uniform init data;
this function moves nodes from an `arg0+0x10` list into `manager+0x20`.

## Predictions status

| Claim | Verdict |
|---|---|
| The complete index changes the buckets-1-and-8 answer | **REFUTED** — still no producer, now on complete coverage |
| My earlier checks had complete coverage | **REFUTED** — a few hundred instructions against 499 ROM-wide stores |
| `min(sites)..max(sites)` defines a usable scope | **REFUTED** *(my own, this wake)* — spans arm9 + all overlays; 159 false candidates |
| `0x0207CBC8` fills bucket 8 | **REFUTED** — base is `[r7+8]`, a list node |
| `ColPrm+0x20` is init data | **REFUTED** *(iteration 53)* — it is a list head, linked at `0x0207CBB8` |
| Nothing fills bucket 1 or bucket 8 | **CONFIRMED_STATIC** — seventh check, first with complete coverage |

## Next angles, ranked

1. **Re-audit the other ColPrm "init block" offsets** (`+0x00`–`+0x24`) for list-head use. `+0x20` was wrong;
   `search-imm` over the complete index can settle each one cheaply.
2. **Run `prior_art.py` on remaining open questions** before touching a binary — NoteTrack
   `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at `0x02171FEC`, the 24 positive
   `ProjectileId` values.
3. **Map `BattleCol.cpp`** (carried), starting from `prior_art.py BattleCol`.
4. **Harness watchpoint** on `ColPrm+0x154` — the bucket-1 contradiction survives seven static checks. That's
   as far as static analysis goes.
