# Findings: `0x02076E38` is add-entry-to-deck, with three error codes

Loop-Atlas iteration 108. Static.

Complete **add-with-uniqueness-check**: three high-bit error codes, a duplicate-ID
rule, and a free-to-active node move. Confirms both list roles — construction links
onto `+0x560`, this function moves to `+0x558`.

---

## 1. The contract

`0x02076E38(r0 = slot, r1 = id, r2 = a, r3 = b, [sp+0x28] = c, [sp+0x2c] = d)`

| condition | result |
|---|---|
| `[slot+0x560]` empty | return **`0x20000000`** — no free node |
| an active node's ID matches | return **`0x40000000`** — duplicate |
| `0x02076D30(slot, id, a, b)` returns 0 | return **`0x10000000`** |
| `0x02076C98(slot, id)` returns 0 | bail to the exit path |
| otherwise | take a node and fill it |

Three status bits in the top nibble — `0x1`, `0x2`, `0x4` shifted to bit 28 — letting
callers distinguish failures.

## 2. The duplicate check

```
0x02076E60  ldr  r1, [sl, #0x558]      ; the active list
0x02076E68  ldr  r0, [r1, #0x34]       ; node's data record
0x02076E6C  ldrh r0, [r0]              ; its first halfword = the ID
0x02076E70  cmp  r0, sb                ; == the requested id?
0x02076E74  moveq r0, #0x40000000
0x02076E78  popeq {…}
0x02076E7C  ldr  r1, [r1]              ; next
```

`node+0x34` points at a data record whose **first halfword is an ID**; no two active
nodes may share one.

## 3. The fill

```
0x02076EE0  add r0, sl, #0x560
0x02076EE4  bl  #0x2037c24            ; unlink from the free list
0x02076EE8  add r0, sl, #0x158
0x02076EF0  add r0, r0, #0x400        ; = slot+0x558
0x02076EF4  bl  #0x2037b98            ; link onto the active list
0x02076EF8  add r0, r4, #0xc
0x02076F00  mov r2, #4
0x02076F04  bl  #0x20517fc            ; memset(node+0x0C, 0, 4)
0x02076F08  add r0, r4, #0x10
0x02076F10  mov r2, #0x22
0x02076F14  bl  #0x20517fc            ; memset(node+0x10, 0, 0x22)
0x02076F18  lsl r1, r7, #0x1c
0x02076F1C  and r0, r8, #0xf
0x02076F20  orr r0, r0, r1, lsr #24
0x02076F24  strh sb, [r4, #0xc]       ; node+0x0C = id
0x02076F28  strb r0, [r4, #0xe]       ; node+0x0E = (a & 0xF) | ((b & 0xF) << 4)
```

`node+0x0E` packs two 4-bit arguments into one byte. `+0x558` is reached as
`#0x158` + `#0x400` — a split immediate, invisible to a plain offset scan.

## 4. List roles, confirmed both ways

| head | role | evidence |
|---|---|---|
| `+0x560` | free | every node linked here at construction (iteration 106); unlinked here |
| `+0x558` | active | linked here on add; walked by both walkers (iteration 107) |

## Predictions status

| Claim | Verdict |
|---|---|
| `0x02076E38` adds an entry to the deck | **CONFIRMED_STATIC** — unlink from free, link to active, fill the ID |
| It returns `0x20000000` when no free node remains | **CONFIRMED_STATIC** — `cmp r0,#0`; `moveq r0,#0x20000000`; `popeq` at `0x02076E48`–`0x02076E5C` |
| It returns `0x40000000` on a duplicate ID | **CONFIRMED_STATIC** — the active-list scan at `0x02076E68`–`0x02076E78` |
| It returns `0x10000000` when `0x02076D30` fails | **CONFIRMED_STATIC** — `0x02076EA0`–`0x02076EA8` |
| `node+0x34` points at a record whose first halfword is an ID | **CONFIRMED_STATIC** — `ldr r0,[r1,#0x34]`; `ldrh r0,[r0]`; `cmp r0,sb` |
| `node+0x0C` holds the ID | **CONFIRMED_STATIC** — `strh sb,[r4,#0xc]` |
| `node+0x0E` packs two 4-bit arguments | **CONFIRMED_STATIC** — `and r0,r8,#0xf`; `orr r0,r0,r1,lsr #24` after `lsl r7,#0x1c` |
| `+0x560` is the free list and `+0x558` the active one | **CONFIRMED_STATIC** — unlink from one, link to the other, in one function |
| Entries are unique by ID | **CONFIRMED_STATIC** — a matching ID is refused outright |
| A node is a koma/card record | **not claimed** — unique-by-ID entries with a 4-bit pair and a data-record pointer fit one, but nothing names it |
| `0x02076D30` and `0x02076C98` are validation | **not claimed** — their failure paths are known, their bodies are not |

## Next angles, ranked

1. **Read `0x02076D30` and `0x02076C98`.** One gates with `0x10000000`, the other bails
   silently — together they hold the rule for what may enter a deck.
2. **Find who sets `node+0x34`** — links a deck entry to its static definition.
3. **Trace the `0x64` in `0x020785B8`** (carried).
4. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
