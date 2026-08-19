# Findings: the pool pair is two ColObj method slots

Loop-Atlas iteration 71. Static.

Goal: name the owner of the `0x2C`-byte pool nodes. Result: located it at `ColObj+0x28` but did not name
it. Along the way, confirmed that the allocate/free pair from iteration 70 is **two adjacent method slots
on a ColObj**.

---

## 1. The allocator is a ColObj method

`0x0207D440` has zero direct callers. Its only ROM reference is a literal load at `0x0207CA1C`, inside
`0x0207C988`:

```
0x0207CA18  bl  #0x207aedc      ; Battle_ColObjCreate -> a new ColObj in r0
0x0207CA1C  ldr r1, [pc, #0x120]
0x0207CA20  str r0, [r4, #0x60] ; keep the ColObj at r4+0x60
0x0207CA24  str r1, [r0, #0x1c] ; ColObj+0x1C = 0x0207D440
0x0207CA28  ldr r2, [pc, #0x118]
0x0207CA34  str r2, [r0, #0x20] ; ColObj+0x20 = 0x0207D858
0x0207CA30  ldr r1, [pc, #0x114]
0x0207CA40  str r1, [r0, #0x24] ; ColObj+0x24 = 0x0207D94C
```

Three method pointers are stored on the ColObj right after creation. **All three reference the ColPrm
global** `0x0214BE10` (two, three, and two literal loads respectively), making them the ColObj↔ColPrm
interface methods.

## 2. `+0x1C` and `+0x20` are acquire and release

Both start with the same owner dereference:

| slot | function | first instructions |
|---|---|---|
| `+0x1C` | `0x0207D440` | `ldr r4,[r0,#0x28]` at `0x0207D458` |
| `+0x20` | `0x0207D858` | `ldr r4,[r0,#0x28]` at `0x0207D870` |

Then they do exact opposites:

```
ColObj+0x1C  acquire:  ldr r5,[mgr,#0x18]  ; NULL if empty
                       unlink(mgr+0x18, r5)
                       link(r4+8, r5)
                       init r5+0x14/+0x18 from r4+0x34/+0x38

ColObj+0x20  release:  unlink(r4+8, node)
                       memset(node, 0, 0x2C)
                       link(mgr+0x18, node)
```

Iteration 70 established the pair by matching behavior. This confirms it structurally: same `arg0`, same
owner expression, adjacent slots on one object. The release path at `0x0207D914`–`0x0207D93C` falls inside
`0x0207D858` (size 236, ending `0x0207D944`).

## 3. What I did and did not achieve

**Located, not named.** The owner is `[ColObj+0x28]` — an object with a node list at `+0x8` and source
fields at `+0x34`/`+0x38`. That's a precise address expression, not an identity. Naming it requires
tracing whoever writes `ColObj+0x28`.

## 4. ColObj layout so far

```
ColObj — 0x40 bytes, Battle_ColObjCreate 0x0207AEDC
  +0x08   ColWork list head (0x64-byte records, iteration 65)
  +0x0C   zeroed at construction
  +0x10   zeroed at construction
  +0x1C   method -> 0x0207D440   acquire a 0x2C node from ColPrm+0x18
  +0x20   method -> 0x0207D858   release it back
  +0x24   method -> 0x0207D94C   (also touches the ColPrm global)
  +0x28   pointer to the owner of the 0x2C-node list
```

Two of the three collision layers are now connected: **ColObj** (`BattleCol.cpp`) holds methods that
allocate from the **ColPrm** manager's pool (`BattleColPrm.cpp`). First concrete link between the modules
iteration 65 separated.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x0207D440` is installed as a ColObj method at `+0x1C` | **CONFIRMED_STATIC** — `str r1,[r0,#0x1c]` at `0x0207CA24`, `r0` from `Battle_ColObjCreate` |
| Three method slots are installed together at `+0x1C`/`+0x20`/`+0x24` | **CONFIRMED_STATIC** — `0x0207CA24`, `0x0207CA34`, `0x0207CA40` |
| All three reference the ColPrm global | **CONFIRMED_STATIC** — 2, 3 and 2 literal loads of `0x0214BE10` |
| `+0x1C` and `+0x20` operate on the same owner | **CONFIRMED_STATIC** — both `ldr r4,[r0,#0x28]` |
| The release path is inside the `+0x20` method | **CONFIRMED_STATIC** — `0x0207D914` within `0x0207D858`+236 |
| The owner was identified | **REFUTED** *(my own task)* — located at `[ColObj+0x28]`, not named |
| `0x0207D440` is reached by a direct call | **REFUTED** — 0 callers; installed as a function pointer |

## Next angles, ranked

1. **Find what writes `ColObj+0x28`.** `search-imm 0x28` filtered to stores with a ColObj base, then trace
   the value. Names the owner and closes this thread.
2. **Read `ColObj+0x24`'s method** `0x0207D94C` — third interface method, unexamined.
3. **Map `BattleCol.cpp`** (carried) — `0x0207C988` is a good entry point: calls `Battle_ColObjCreate` and
   wires all three slots.
4. **Harness watchpoint** on `ColPrm+0x154` — bucket-1 contradiction, unresolvable statically.
