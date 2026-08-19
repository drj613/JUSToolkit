# Findings: the deck's active list is never non-empty

Loop-Atlas iteration 115. Static.

The battle deck never gets populated.

Every `link`/`unlink` against the two list heads shows the active list at `+0x558` has
exactly **one** linker — add-entry, proved dead in iteration 113 — and **one** unlinker.
No node ever reaches it. The remove function and **both walkers** are unreachable too.

---

## 1. Every mutation of the two lists

`0x558` is not a valid ARM rotated immediate, so both heads use an `add` pair.
Searching for that shape plus a call to `0x02037B98` (link) or `0x02037C24` (unlink)
across all 16 regions:

| head | site | operation | function |
|---|---|---|---|
| **`+0x558`** | `0x02076EF4` | **link** | add-entry `0x02076E38` — **dead** |
| **`+0x558`** | `0x020770E4` | **unlink** | the remove function |
| `+0x560` | `0x02076958` | link | slot constructor, 16 nodes at init |
| `+0x560` | `0x02076C44` | link | a second 16-node rebuild loop |
| `+0x560` | `0x02076EE4` | unlink | add-entry taking a node |
| `+0x560` | `0x020770F0` | link | remove, returning the node |

Six sites total, all in `ComicDeck.cpp`.

## 2. The remove function

```
0x020770D0  ldr r5, [r4, #0x34]      ; the node's table entry
0x020770D8  add r0, r6, #0x158
0x020770E0  add r0, r0, #0x400       ; slot+0x558
0x020770E4  bl  #0x2037c24           ; unlink
0x020770EC  add r0, r6, #0x560
0x020770F0  bl  #0x2037b98           ; link back to free
```

Exact inverse of add-entry. Nothing is ever on the active list, so nothing to remove.

## 3. The second init loop

```
0x02076C34  mov r6, #0x10            ; 16 nodes
0x02076C38  mvn r4, #0               ; -1
0x02076C40  add r0, r7, #0x560
0x02076C44  bl  #0x2037b98           ; link to free
0x02076C48  sub r6, r6, #1
```

Returns all 16 nodes to the free list — same shape as the constructor loop from iteration 106.

## 4. What is dead

| component | why |
|---|---|
| add-entry `0x02076E38` | the ID lookup always fails (iteration 113) |
| the remove function | its only source is the active list |
| walker `0x0207871C` | reads `[slot+0x558]`, always null |
| walker `0x020785B8` | same |
| the `+0x016` → `+0x018` halving | inside walker one |
| the `+0x03C` flag manipulation | inside both walkers |
| the unique-by-ID rule | inside add-entry |

Still live: the constructor and rebuild loop (parking all 16 nodes on the free list), plus
fields outside the node system — the gauge pointer, `+0x5C8` SP, the guard bytes.

## Predictions status

| Claim | Verdict |
|---|---|
| Exactly one site links a node onto `slot+0x558` | **CONFIRMED_STATIC** — `0x02076EF4`, inside add-entry |
| Exactly one site unlinks from `slot+0x558` | **CONFIRMED_STATIC** — `0x020770E4` |
| Four sites touch the free list `+0x560` | **CONFIRMED_STATIC** — two init loops, add-entry's take, remove's return |
| The active list is ever non-empty | **REFUTED** — its only linker cannot succeed |
| The remove function is reachable | **REFUTED** — nothing is ever on the list it drains |
| Both active-list walkers do work at runtime | **REFUTED** — both read a permanently null head |
| The battle deck is populated by some other route | **REFUTED** — the node lists are the only storage, and only the free one is ever filled |
| Nodes are still initialised | **CONFIRMED_STATIC** — two loops park all 16 on the free list with `+0x0C = -1` |
| The whole ComicDeck object is dead | **REFUTED** — the gauge pointer and `+0x5C8` SP live outside the node system |

## Next angles, ranked

1. **Read `KomaList_Create` `0x0214F5C4`** (carried) — battle-side node system is dead, so the editor's container is where deck contents must live.
2. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried) — not the slot lists; may be the live storage.
3. **Read `Battle_MoveManCreate` `0x02082A50`** (carried).
4. **Trace `+0x5CC` and `+0x5CD`** at `0x02078290` (carried) — on the live side of the object.
