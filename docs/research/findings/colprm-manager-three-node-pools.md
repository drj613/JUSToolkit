# Findings: the ColPrm manager's `0xFB54` is three node pools

Loop-Atlas iteration 119. Static.

`+0x254` and `+0x354` are not fields — they are low halves of split immediates
reaching **three contiguous node pools** that tile the manager's back end exactly to
`0xFB54`.

Each pool links onto a free-list head already documented; the manager's size, its
three pools, and the node sizes from iterations 69–70 all reconcile.

---

## 1. The three pools

| base | nodes | size | total | linked to |
|---|---|---|---|---|
| `+0xC854` | `0x80` | `0x2C` | `0x1600` | `+0x18` |
| `+0xDE54` | 80 | `0x10` | `0x500` | `+0x20` |
| `+0xE354` | `0x200` | `0xC` | `0x1800` | `+0xD8` |

`0xC854 + 0x1600 = 0xDE54`. `0xDE54 + 0x500 = 0xE354`. `0xE354 + 0x1800 = 0xFB54` — the
allocation size. No gaps, no slack.

```
0x0207C7B8  add r0, r4, #0x54
0x0207C7BC  add r5, r0, #0xc800       ; 0xC854
0x0207C7C8  add r0, r4, #0x18         ; the 0x2C free pool
0x0207C7CC  bl  #0x2037b98
0x0207C7D4  cmp r6, #0x80
0x0207C7D8  add r5, r5, #0x2c

0x0207C7E0  add r0, r4, #0x354
0x0207C7E4  add r5, r0, #0xe000       ; 0xE354
0x0207C7F0  add r0, r4, #0xd8         ; the bucket free list
0x0207C7FC  cmp r6, #0x200
0x0207C800  add r5, r5, #0xc

0x0207C808  add r0, r4, #0x254
0x0207C80C  add r5, r0, #0xdc00       ; 0xDE54
0x0207C818  add r0, r4, #0x20         ; the 0x10 free pool
```

`0x80` and `0x200` counts come from `cmp` guards. The 80 for the `0x10` pool is derived
from tiling, not from a `cmp`.

## 2. Nodes are pre-cleared before linking

```
0x0207C58C  add r0, r4, #0x354
0x0207C590  add r2, r0, #0xe000       ; 0xE354
0x0207C594  add r0, r0, #0xf800       ; 0xFB4C
0x0207C598  mov r1, #0
0x0207C59C  str r1, [r2, #8]
0x0207C5A0  add r2, r2, #0xc
0x0207C5A4  cmp r2, r0
0x0207C5A8  blo #0x207c59c
```

A separate pass zeroes `+0x8` of every bucket node, bounded at `0xFB4C` (the last
node's `+0x8`).

## 3. `+0x254` and `+0x354` are guard-8 false positives

Iteration 118's map reported both as address-taken fields. Neither is: the real targets
are `0x354 + 0xE000` and `0x254 + 0xDC00`. `+0x54` is the same — it pairs with `0xC800`.

Second instance after `+0x21C` at iteration 104 (low half of a `0x61C` stride). **A
guard-8 hit followed within a few instructions by another `add` on the same register is
an address computation, not a field**, and the map should say so.

## Predictions status

| Claim | Verdict |
|---|---|
| Three node pools tile `+0xC854`–`+0xFB54` | **CONFIRMED_STATIC** — `0xC854+0x1600 = 0xDE54`, `+0x500 = 0xE354`, `+0x1800 = 0xFB54` |
| The `0x2C` pool has `0x80` nodes at `+0xC854`, linked to `+0x18` | **CONFIRMED_STATIC** — `cmp r6,#0x80`; `add r0,r4,#0x18`; `bl #0x2037b98` |
| The `0xC` pool has `0x200` nodes at `+0xE354`, linked to `+0xD8` | **CONFIRMED_STATIC** — `cmp r6,#0x200`; `add r0,r4,#0xd8` |
| The `0x10` pool sits at `+0xDE54`, linked to `+0x20` | **CONFIRMED_STATIC** — `add r5,r0,#0xdc00`; `add r0,r4,#0x20` |
| Its count of 80 was read from a `cmp` | **REFUTED** — derived from the tiling |
| Bucket nodes are cleared before linking | **CONFIRMED_STATIC** — `str r1,[r2,#8]` loop to `0xFB4C` |
| `+0x054`, `+0x254`, `+0x354` are manager fields | **REFUTED** — low halves of split immediates for `0xC854`, `0xDE54`, `0xE354` |
| The `0xFB54` size is now fully accounted for | **CONFIRMED_STATIC** — header to `+0xC854`, then the three pools |
| The header below `+0xC854` is mapped | **REFUTED** — 43 offsets known, all below `+0x360`; `+0x360`–`+0xC853` is unexamined |

## Next angles, ranked

1. **Teach guard 8 to suppress a hit that feeds another `add` on the same register** —
   two false fields in two structs, both from this shape.
2. **Map `+0x360`–`+0xC853`**, the manager's unexamined middle — `0xC4F4` bytes between the
   known header and the first pool.
3. **Read `+0x0EC`, `+0x0F0`, `+0x0F4`** (carried).
4. **Read `Battle_MoveManCreate` `0x02082A50`** (carried).
