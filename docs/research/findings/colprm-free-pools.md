# Findings: `+0x18` and `+0x20` are free pools, not ColObj lists

Loop-Atlas iteration 69. Static.

Iteration 68 guessed `ColPrm+0x18` and `+0x20` hold the ColObjs. **Refuted.** Both are **free pools** —
`0x2C`-byte nodes and `0x10`-byte nodes — while `Battle_ColObjCreate` allocates `0x40`.

A harder lesson: `+0x18` and `+0x20` are **conventional list-head offsets** shared across all three
collision modules. Offset matching alone is worthless without verifying the base register. Of 21
candidate sites, only **one** verified.

---

## 1. Both lists receive zeroed nodes

`+0x18`, at `0x0207D93C` — the only site with a verified base:

```
0x0207D914  add r0, r4, #8       ; a list head on r4
0x0207D918  bl  #0x2037c24       ; unlink(r4+8, r6)
0x0207D91C  mov r0, r6
0x0207D924  mov r2, #0x2c
0x0207D928  bl  #0x20517fc       ; memset(r6, 0, 0x2C)
0x0207D934  ldr r0, [r0]         ; r0 = *(0x0214BE10) = the manager
0x0207D938  add r0, r0, #0x18
0x0207D93C  bl  #0x2037b98       ; link(manager+0x18, r6)
```

`+0x20`, at `0x0207CBB8` (base verified in iteration 67):

```
0x0207CBA8  mov r2, #0x10
0x0207CBAC  bl  #0x20517fc       ; memset(r7, 0, 0x10)
0x0207CBB4  add r0, sb, #0x20    ; sb = the manager
0x0207CBB8  bl  #0x2037b98       ; link(manager+0x20, r7)
```

Both do the same thing: **unlink, zero, link into the manager's list.** Zeroing before linking is how you
return a node to a free pool — you don't wipe something you still need.

ColPrm has **three** free pools:

| head | node size | evidence |
|---|---|---|
| `+0x18` | `0x2C` bytes | `mov r2,#0x2c` at `0x0207D924` |
| `+0x20` | `0x10` bytes | `mov r2,#0x10` at `0x0207CBA8` |
| `+0xD8` | bucket nodes | 2 links vs **14 unlinks** (iteration 68) — the allocation-heavy one |

This also explains why they're "persistent across frames" — **free lists are never drained**, so the
per-frame drain starting at `+0x28` skips them.

## 2. REFUTED: they do not hold ColObjs

`Battle_ColObjCreate` (`0x0207AEDC`) allocates **`0x40`** bytes:

```
0x0207AF00  mov r0, #0x40
0x0207AF04  bl  #0x201a21c
0x0207AF08  movs r4, r0
0x0207AF10  strne r0, [r4, #8]    ; zero +0x08, +0x0C, +0x10
```

`0x40` matches neither pool. These lists are memory management, not registration.

Known collision record sizes: **ColObj `0x40`**, **ColWork `0x64`** (iteration 65), pool nodes `0x2C`
and `0x10`.

## 3. The limit: conventional offsets defeat attribution

Link/unlink calls at `manager+0x18` or `+0x20` turn up **21 sites**. Only **1** verified as ColPrm's
manager.

This isn't a verifier problem — it's a design problem. Eight of the 21 are *unlinks* (which would tell us
whether anything allocates from these pools), at `0x0207BE5C`, `0x0207BF2C`, `0x0207BFDC`, `0x0207C3C8`,
`0x0207CD0C`, `0x0207CD60`, `0x0207D488`, `0x02080860`, `0x02082D04`. Several sit **below**
`Battle_ColPrmManCreate` at `0x0207C4C0` — inside `BattleCol.cpp` and `BattleColJoint.cpp`, where
`+0x18`/`+0x20` on *those* modules' own objects is expected.

`+0x08`, `+0x10`, `+0x18` and `+0x20` are **conventional list-head offsets** in this codebase. The same
offsets recur on ColObj, ColWork, ColJoint nodes, and the ColPrm manager. An offset match alone carries
no information — these offsets are shared by design, not coincidence.

**Not claimed:** whether anything allocates out of `+0x18` or `+0x20`. Each of the eight unlink sites
needs its base traced individually.

## Predictions status

| Claim | Verdict |
|---|---|
| `+0x18` and `+0x20` hold the long-lived ColObjs | **REFUTED** *(iteration 68's guess)* — ColObj is `0x40`, pools take `0x2C` and `0x10` |
| `+0x18` is a free pool for `0x2C`-byte nodes | **CONFIRMED_STATIC** — unlink, `memset 0x2C`, link at `0x0207D93C` |
| `+0x20` is a free pool for `0x10`-byte nodes | **CONFIRMED_STATIC** — `memset 0x10`, link at `0x0207CBB8` |
| `Battle_ColObjCreate` allocates `0x40` bytes | **CONFIRMED_STATIC** — `0x0207AF00` |
| Being "persistent" implies long-lived registrations | **REFUTED** — free lists are simply never drained |
| The 21 `+0x18`/`+0x20` sites are all ColPrm's | **REFUTED** — several are in `BattleCol.cpp`/`BattleColJoint.cpp` |
| Anything allocates back out of `+0x18` or `+0x20` | **not claimed** — 8 unlink sites, none with a verified base |

## Next angles, ranked

1. **Trace each unlink site's base individually.** Only way to learn if these pools recycle or leak.
   Offset matching can't shortcut it.
2. **Map `BattleCol.cpp`** (carried) — three known record sizes (`0x40`, `0x64`, pool nodes) to match
   allocations against.
3. **Record the conventional-offset caveat** in the ColPrm field map, so `+0x08`/`+0x10`/`+0x18`/`+0x20`
   are never again treated as ColPrm-specific.
4. **Harness watchpoint** on `ColPrm+0x154` — bucket-1 contradiction, unresolvable statically.
