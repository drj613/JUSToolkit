# Findings: the ColPrm phase table's 19 handlers

Loop-Atlas iteration 123. Static.

All 19 phase-table entries recovered — function pointers from constructor literals.
Two pairs share a target; the first two slots are `bx lr` **no-op stubs** — **15 real handlers**.

`+0x0F4` holds the **ColJoint manager**. The `0x10`-node pool's 80-count, previously
derived by tiling (iteration 119), is now read directly from a `cmp`.

---

## 1. The table

| slot | handler | |
|---|---|---|
| `+0x0FC` | `0x0207D9A4` | **`bx lr`** — no-op |
| `+0x100` | `0x0207D9A8` | **`bx lr`** — no-op |
| `+0x104` | `0x0207D9AC` | `push {r3,r4,r5,r6,lr}`; `sub sp,#0x34` |
| `+0x108` | `0x0207DD40` | reads `[r0+0xB0]`, walks a list |
| `+0x10C` | `0x0207DDD4` | |
| `+0x110` | `0x0207DE08` | shared with `+0x120` |
| `+0x114` | `0x0207DE3C` | |
| `+0x118` | `0x0207DE44` | |
| `+0x11C` | `0x0207DE4C` | |
| `+0x120` | `0x0207DE08` | shared with `+0x110` |
| `+0x124` | `0x0207DF60` | |
| `+0x128` | `0x0207DFC0` | |
| `+0x12C` | `0x0207DFC8` | |
| `+0x134` | `0x0207DE80` | |
| `+0x138` | `0x0207DE88` | |
| `+0x13C` | `0x0207DFF4` | |
| `+0x140` | `0x0207DFD8` | shared with `+0x144` |
| `+0x144` | `0x0207DFD8` | shared with `+0x140` |
| `+0x148` | `0x0207E010` | |

19 slots, **17 unique** targets *(corrected iteration 124: these are NOT 15 separate handlers — seven are interior entry points inside `0x0207DD40`, one inside `0x0207DFF4`, three sit in an uncatalogued gap, and only two targets are substantial; see `phase-table-is-mostly-tiny-accessors.md`)* — contiguous in
`0x0207D9A4`–`0x0207E010`, none with an assert-string name.

`+0x130` absent, per iteration 118.

## 2. Two no-ops at the front

`0x0207D9A4` and `0x0207D9A8` are each a single `bx lr`, four bytes apart. `0x0207D9AC`
is the first real function — two do-nothing stubs placed immediately before it.

Third dispatch table in this ROM with dedicated no-op entries, after the view's 16-slot
table (indices 0–3 sharing one) and the 73-case dispatcher (40 of 73).

## 3. `+0x0F4` is the ColJoint manager

```
0x0207C830  ldr r0, [r4, #0xe0]        ; one of the three owned sub-objects
0x0207C834  bl  #0x207bd40             ; Battle_ColJointManCreate
0x0207C838  str r0, [r4, #0xf4]
```

ColPrm manager owns the ColJoint manager, also reachable via global `0x0214BE0C` — both
routes agree.

`+0x0EC` and `+0x0F0` hold two further objects; `+0x0EC`'s immediately receives
`[obj+0x98] = 0x50000000`.

## 4. The 80-count upgraded

```
0x0207C824  cmp r6, #0x50
0x0207C828  add r5, r5, #0x10
```

`0x50 = 80` with stride `0x10` — the middle node pool. Previously derived from tiling
(iteration 119); now read from the loop's own guard.

## Predictions status

| Claim | Verdict |
|---|---|
| All 19 phase-table slots hold function pointers from constructor literals | **CONFIRMED_STATIC** — 19 recovered by pairing each `ldr rD,[pc]` with its store |
| Two pairs of slots share a target | **CONFIRMED_STATIC** — `0x0207DE08` at `+0x110`/`+0x120`; `0x0207DFD8` at `+0x140`/`+0x144` |
| `+0x0FC` and `+0x100` are `bx lr` no-ops | **CONFIRMED_STATIC** — single-instruction stubs, four bytes apart |
| All 19 slots hold distinct real handlers | **REFUTED** — 17 unique; and per iteration 124 those are entry points across ~6 bodies, not 15 handlers |
| `+0x0F4` holds the ColJoint manager | **CONFIRMED_STATIC** — `bl #0x207bd40`; `str r0,[r4,#0xf4]` |
| `Battle_ColJointManCreate` receives `[manager+0xE0]` | **CONFIRMED_STATIC** — `ldr r0,[r4,#0xe0]` immediately before the call |
| The `0x10` pool's 80-node count was only derivable | **REFUTED** *(iteration 119)* — `cmp r6,#0x50` reads it directly |
| Any phase handler has an assert-string name | **REFUTED** — none of the 17 |
| `+0x0EC` and `+0x0F0` are identified | **not claimed** — two objects, origins untraced; `+0x0EC`'s gets `[+0x98] = 0x50000000` |

## Next angles, ranked

1. **Read the 15 real handlers as a set** — contiguous in `0x0207D9A4`–`0x0207E010`;
   the phase index selecting each is the collision pipeline's actual sequence.
2. **Trace `+0x0EC` and `+0x0F0`'s objects** — both set beside the ColJoint manager.
3. **Enumerate the other `record+0x40` bits** (carried).
4. **Read `Battle_MoveManCreate` `0x02082A50`** (carried).
