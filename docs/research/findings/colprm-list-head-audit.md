# Findings: the ColPrm list-head audit — `+0x18` and `+0x20` are heads, not init data

Loop-Atlas iteration 68. Static. Used the prebuilt `branches` index.

Re-audited the ten words iteration 53 called an "init block" at `ColPrm+0x00`–`+0x24`. **Two of them —
`+0x18` and `+0x20` — are list heads taking real insertions.**

Iteration 53's map already showed it: `+0x18` was *the only word of the ten that was both read and
written*. That's exactly what a list head looks like — read to walk, written to link.

---

## 1. Complete list-head map, from the index

The `branches` index has **263** link/unlink sites ROM-wide. Filtered to those whose `r0` is
`manager + imm` off a **verified** manager register (driver's `r6`, stage 1's `r8`):

| offset | ops | role |
|---|---|---|
| `+0x020` | link ×1 | **list head — inside the old "init block"** |
| `+0x028` | link ×1 | bucket 0 |
| `+0x050` | link ×1 | bucket 5 |
| `+0x058` | link ×1 | bucket 6 |
| `+0x060` | link ×1 | bucket 7 |
| `+0x070` | link ×1 | bucket 9 |
| `+0x080` | link ×1 | bucket 11 |
| `+0x088` | link ×1 | bucket 12 |
| `+0x090` | link ×1 | bucket 13 |
| `+0x098` | link ×1 | bucket 14 |
| `+0x0A0` | link ×1 | bucket 15 |
| `+0x0A8` | link ×1 | bucket 16 |
| `+0x0B0` | link ×1 | bucket 17 |
| `+0x0C8` | link ×1 | bucket 20 |
| `+0x0D0` | link ×1 | bucket 21 |
| `+0x0D8` | link ×2, **unlink ×14** | free list |

Iteration 63 dismissed `+0x020` as "(not a bucket head)" — true, but it *is* a list head. Outside the
22-bucket array doesn't mean outside all lists.

## 2. Verifying the low offsets

Eighteen link/unlink sites in the constructor region use offset `≤ 0x24`, but most operate on other
objects. Each base register traced to its origin:

| site | offset | base origin | manager? |
|---|---|---|---|
| `0x0207D93C` | `+0x18` | `ldr r0,[r0]` where `r0 = 0x0214BE10` | **yes — directly from the global** |
| `0x0207CBB8` | `+0x20` | `ldr r9,[r4,#0x0]`, `r4 = &global` (iteration 67) | **yes** |
| `0x0207C9B8`, `0x0207C9C4` | `+0x08` | `mov r9,r0` — arg0 | no |
| `0x0207CDBC` | `+0x18` | `mov r5,r0` — arg0 | no |
| `0x0207D494` | `+0x08` | `ldr r4,[r0,#0x28]` — **a node out of bucket 0** | no |
| `0x0207C798`, `0x0207C7CC`, `0x0207C81C`, `0x0207CE64` | `+0x08`/`+0x18`/`+0x20` | not resolved | unknown |

`0x0207D494` is the key case: it reads `manager+0x28` (bucket 0) to get a **node**, then links into that
node's `+0x08`. So `+0x08` is a *node* field — without tracing the base, it would look like an eleventh
manager list head.

**Confirmed manager list heads outside the bucket array: `+0x18` and `+0x20`.** The `+0x08` and `+0x10`
candidates are **not claimed** — their bases are arg0 or nodes.

## 3. What the init block actually is

```
+0x00 .. +0x14   written once during construction (init data)
+0x18            LIST HEAD   (read+write in iteration 53's map — the clue I missed)
+0x1C            written once
+0x20            LIST HEAD   (linked by the driver at 0x0207F53C and at 0x0207CBB8)
+0x24            written once
+0x28 .. +0xD7   the 22 per-frame buckets
+0xD8            free list
```

The per-frame drain loop starts at `+0x28` and runs 22 iterations (iteration 55). It never touches
`+0x18` or `+0x20`. Those two are **persistent** lists that survive across frames; the buckets are rebuilt
every frame.

That's the structural distinction the "init block" label was hiding.

## Predictions status

| Claim | Verdict |
|---|---|
| `ColPrm+0x00`–`+0x24` is a uniform init block | **REFUTED** *(iteration 53)* — `+0x18` and `+0x20` are list heads |
| `+0x18` is a manager list head | **CONFIRMED_STATIC** — `0x0207D93C`, base loaded straight from `0x0214BE10` |
| `+0x20` is a manager list head | **CONFIRMED_STATIC** — `0x0207CBB8`, plus the driver's link at `0x0207F53C` |
| `+0x08` and `+0x10` are manager list heads | **not claimed** — bases are arg0 or nodes from bucket 0 |
| `+0x08` on a bucket-0 node is a list head | **CONFIRMED_STATIC** — `0x0207D494` reads `[r0,#0x28]` first |
| `+0x18`/`+0x20` are drained each frame like the buckets | **REFUTED** — the drain loop starts at `+0x28` |
| Iteration 53's map contained no signal about `+0x18` | **REFUTED** — it flagged `+0x18` as the only read-and-written word of the ten |

## Next angles, ranked

1. **What lives on the two persistent lists** (`+0x18`, `+0x20`). They outlive the per-frame buckets —
   likely the ColObjs themselves.
2. **Resolve the four unknown bases** (`0x0207C798`, `0x0207C7CC`, `0x0207C81C`, `0x0207CE64`) — any that
   trace to the manager means more heads.
3. **Map `BattleCol.cpp`** (carried), starting from `prior_art.py BattleCol`.
4. **Harness watchpoint** on `ColPrm+0x154` — the bucket-1 contradiction, unresolvable statically.
