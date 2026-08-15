# Findings: the `+0x18` pool is recycled — a complete allocate/free pair

Loop-Atlas iteration 70. Static.

Traced all eight `+0x18`/`+0x20` unlink sites to their base registers. **One is the ColPrm manager**, and
its code contains the matching allocator — so the `+0x18` free pool is **recycled, not leaked**.

Two other `+0x18` unlinks belong to the **ColJoint** manager, confirming last wake's offset-collision hazard.

---

## 1. Eight sites, one manager

| site | offset | base traces to | ColPrm? |
|---|---|---|---|
| `0x0207D488` | `+0x18` | `*(0x0214BE10)` at `0x0207D46C` | **yes** |
| `0x0207BF2C` | `+0x18` | `*(0x0214BE0C)` — the **ColJoint** manager | no |
| `0x0207BFDC` | `+0x18` | `*(0x0214BE0C)` — ColJoint | no |
| `0x0207CD0C` | `+0x20` | `[r4,#0x68]` | no |
| `0x0207CD60` | `+0x18` | `[r4,#0x68]` | no |
| `0x0207C3C8` | `+0x20` | arg0 | unknown |
| `0x02082D04` | `+0x18` | arg0 | unknown |
| `0x02080860` | `+0x20` | not resolved | unknown |

Two sites resolve to `*(0x0214BE0C)`: **ColJoint keeps its own list at `+0x18`.** Matching on offset alone
would have miscounted them as ColPrm allocations, tripling the apparent pool traffic.

## 2. The allocator

```
0x0207D468  ldr r0, [pc, #0x3c8]   ; = &0x0214BE10
0x0207D46C  ldr r0, [r0]           ; r0 = the ColPrm manager
0x0207D470  ldr r5, [r0, #0x18]    ; r5 = head of the +0x18 pool
0x0207D474  cmp r5, #0
0x0207D478  moveq r0, #0
0x0207D47C  popeq {r3,r4,r5,r6,r7,pc}   ; pool empty -> return NULL
0x0207D480  mov r1, r5
0x0207D484  add r0, r0, #0x18
0x0207D488  bl  #0x2037c24         ; unlink(pool, node) — TAKE it
0x0207D48C  mov r1, r5
0x0207D490  add r0, r4, #8
0x0207D494  bl  #0x2037b98         ; link(owner+8, node) — attach to the owner
0x0207D498  ldr r0, [r4, #0x34]
0x0207D49C  str r0, [r5, #0x14]    ; initialise from the owner
0x0207D4A0  ldr r0, [r4, #0x38]
0x0207D4A4  str r0, [r5, #0x18]
```

Five steps: read the head, **return NULL if empty**, unlink from pool, attach to owner's `+0x8` list,
initialise node `+0x14`/`+0x18` from owner `+0x34`/`+0x38`.

## 3. The pair

| direction | site | what it does |
|---|---|---|
| allocate | `0x0207D468`–`0x0207D494` | manager`+0x18` → owner`+0x8`, fields initialised |
| free | `0x0207D914`–`0x0207D93C` (iteration 69) | owner`+0x8` → `memset 0x2C` → manager`+0x18` |

Symmetric pair, same pool, same module, both verified from the global. The `+0x18` pool is a
**fixed-capacity recycler with graceful exhaustion** — nodes cycle between pool and owner's `+0x8` list,
and allocation returns NULL instead of growing.

The free path memsets `0x2C` bytes; the allocate path writes `+0x14` and `+0x18`. Consistent: a `0x2C`-byte
node, wiped on release, partially re-initialised on acquisition.

## 4. `+0x20` remains open, and the `+0x08` sites are vindicated

No `+0x20` unlink resolves to the ColPrm manager. Whether that pool recycles is **still not established** —
the two candidates trace to `[r4,#0x68]` and arg0.

Last wake declined to claim `+0x08` and `+0x10` as manager list heads because their bases were "arg0 or
nodes". The allocator proves that right: `0x0207D494` links into **`r4+8`** where `r4` is the *owner*, not
the manager. `+0x08` is an owner-side list head.

## Predictions status

| Claim | Verdict |
|---|---|
| One of the eight unlink sites is ColPrm's | **CONFIRMED_STATIC** — `0x0207D488`, base from `0x0214BE10` at `0x0207D46C` |
| The `+0x18` pool is recycled, not leaked | **CONFIRMED_STATIC** — symmetric allocate/free pair |
| Allocation fails gracefully when the pool is empty | **CONFIRMED_STATIC** — `cmp r5,#0`; `moveq r0,#0`; `popeq` |
| Active nodes live on the owner's `+0x8` list | **CONFIRMED_STATIC** — `add r0,r4,#8` then link, at `0x0207D490` |
| All eight `+0x18`/`+0x20` unlinks are ColPrm's | **REFUTED** — 2 are ColJoint's (`*(0x0214BE0C)`), 5 are other objects or unresolved |
| The `+0x20` pool is recycled | **not claimed** — no candidate resolves to the ColPrm manager |
| `+0x08` is a ColPrm manager list head | **REFUTED** *(confirming iteration 69's caution)* — it is the **owner's** head |

## Next angles, ranked

1. **Identify the owner** — `r4` in the allocator, with fields `+0x08` (node list), `+0x34`, `+0x38`. It is
   the object these `0x2C`-byte nodes belong to, and naming it names the nodes.
2. **Find `+0x20`'s allocator** by the same route: search for `ldr rN,[mgr,#0x20]` followed by an unlink,
   with the base verified from the global.
3. **Map `BattleCol.cpp`** (carried) — now with four record sizes to match against (`0x40`, `0x64`, `0x2C`,
   `0x10`).
4. **Harness watchpoint** on `ColPrm+0x154` — the bucket-1 contradiction, unresolvable statically.
