# Findings: the unmapped band is a 16-entry node array

Loop-Atlas iteration 106. Static.

`+0x059`–`+0x557` looked untouched because nothing indexes it. The slot allocator shows
why: **16 nodes of `0x50` bytes**, linked onto a free list at construction and reached only
through that list afterwards.

`0x58 + 16 × 0x50 = 0x558` — exactly where the next known field starts. Band fully
accounted for.

---

## 1. The construction loop

```
0x02076944  add  r6, r5, #0x58       ; first node
0x02076948  mov  r7, #0x10           ; 16 of them
0x0207694C  mvn  r4, #0              ; -1
0x02076950  mov  r1, r6
0x02076954  add  r0, r5, #0x560      ; the list head
0x02076958  bl   #0x2037b98          ; link(slot+0x560, node)
0x0207695C  sub  r7, r7, #1
0x02076960  strh r4, [r6, #0xc]      ; node+0x0C = -1
0x02076964  cmp  r7, #0
0x02076968  add  r6, r6, #0x50       ; stride
0x0207696C  bgt  #0x2076950
```

`0x02037B98` is the list-link routine. Every node is pushed onto `slot+0x560` and stamped
`-1` at `node+0x0C`.

## 2. The slot's two lists hold the same nodes

`0x0207871C` walks `slot+0x558` and tests `node+0x40` (iteration 104). `0x40 < 0x50`, so
both lists carry the same records:

| field | role |
|---|---|
| `+0x058` | the node array, 16 × `0x50` |
| `+0x558` | **active** list head — walked with a mode flag |
| `+0x560` | **free** list head — every node starts here |

`+0x55C` and `+0x564` sit between them, zeroed per slot; plausible tail or count fields,
**not claimed**.

## 3. Why offset scans found nothing

After construction, nodes are reached by list traversal. No code computes
`slot + 0x58 + i*0x50`, so no immediate offset in the band ever appears — invisible by
design, not a tooling gap.

Iteration 104 read the emptiness as "separate accessors". Closer than the split-base guess
of iteration 105, but wrong: there are no accessors, only a linked list.

## 4. Slot outline

| offset | size | what |
|---|---|---|
| `+0x000`–`+0x057` | `0x58` | header |
| `+0x058`–`+0x557` | `0x500` | 16 nodes × `0x50` |
| `+0x558` | | active list head |
| `+0x55C` | | zeroed per slot |
| `+0x560` | | free list head |
| `+0x564` | | zeroed per slot |
| `+0x56C` | | gauge pointer |
| `+0x5C8` | | **SP total** |
| `+0x5CC`, `+0x5CD`, `+0x5CF` | | signed-byte guards |
| `+0x5E8`, `+0x5EC` | | written in ov6, read in arm9 |
| `+0x5F0`, `+0x5F3`, `+0x5F5`, `+0x5F6` | | byte cluster |

`+0x000`–`+0x057` and gaps above `+0x564` remain unexplained.

## Predictions status

| Claim | Verdict |
|---|---|
| `slot+0x058` begins 16 nodes of `0x50` bytes | **CONFIRMED_STATIC** — `add r6,r5,#0x58`; `mov r7,#0x10`; stride `#0x50`; `bgt` |
| The array ends exactly where `+0x558` begins | **CONFIRMED_STATIC** — `0x58 + 16 × 0x50 = 0x558` |
| Every node is linked onto `slot+0x560` at construction | **CONFIRMED_STATIC** — `add r0,r5,#0x560`; `bl #0x2037b98` inside the loop |
| `node+0x0C` is initialised to `-1` | **CONFIRMED_STATIC** — `mvn r4,#0`; `strh r4,[r6,#0xc]` |
| `+0x558` and `+0x560` hold the same node type | **CONFIRMED_STATIC** — the walker tests `node+0x40`, inside a `0x50`-byte record |
| The band is untouched because its owner module was not found | **REFUTED** *(iteration 104)* — nothing indexes it; nodes are reached by list traversal |
| Split bases hide the band | **REFUTED** *(iteration 105, unchanged)* |
| `+0x55C` and `+0x564` are list tails or counts | **not claimed** — zeroed per slot, roles untraced |
| 16 nodes correspond to a game-visible deck capacity | **not claimed** — no runtime check |

## Next angles, ranked

1. **Map the `0x50` node.** `+0x0C` is a halfword initialised to `-1`; `+0x40` is a byte
   the walker tests. The active-list walker `0x0207871C` and its mode argument are the
   way in.
2. **Trace `+0x5CC` and `+0x5CD`** at `0x02078290` (carried).
3. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
4. **Re-audit map claims on `char+0xNNN` above `0x200`** (carried).
