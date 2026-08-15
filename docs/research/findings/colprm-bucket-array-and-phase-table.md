# Findings: ColPrm is a 22-bucket list system with a phase table — and two of my own labels were wrong

Loop-Atlas iteration 55. Static.

Iteration 54 called `0x0207F480` a "handler table." It's a function. Reading it and its two siblings
rewrites most of what iterations 53–54 recorded.

Four takeaways:

- `0x0207F480`/`0x0207FB60`/`0x0207FBB0` are **callback functions**, not tables. I labelled them without
  reading their contents.
- The "list heads at `+0x70` and `+0xD0`" from iteration 53 are **buckets 9 and 21 of a 22-entry array**.
- The "second init block" at `+0xFC`–`+0x148` is a **phase table of 19 function pointers**, not data.
- The one live per-frame phase does **not** write the contact array.

---

## 1. Correction: these are functions, not tables

Iteration 54 logged `0x02028384(obj->[4], table)` as "install a handler table." But dumping `0x0207F480`
gives `0xE92D4FF8`, `0xE5900004`, `0xE3A05000` — `push`, `ldr`, `mov`. All three "tables" are ARM code.
`0x02028384` **registers a callback function**.

The tell was free: I printed the words and called them a table without checking if they were instructions.

## 2. `0x0207F480` — the per-frame reset

```
0x0207F480  push {r3, r4, r5, r6, r7, r8, sb, sl, fp, lr}
0x0207F484  ldr r0, [r0, #4]
0x0207F48C  ldr r6, [r0, #0x10]      ; r6 = the ColPrm manager (back-pointer)
0x0207F494  add r8, r6, #0x28        ; the bucket array
0x0207F498  ldr r7, [r8]
0x0207F4A0  mov r0, r8
0x0207F4A4  mov r1, r7
0x0207F4A8  bl  #0x2037c24           ; unlink(list, node)
0x0207F4B0  add r0, r6, #0xd8        ; the free list
0x0207F4B4  str r4, [r7, #8]
0x0207F4B8  bl  #0x2037b98           ; link(freelist, node)
0x0207F4BC  ldr r7, [r8]
0x0207F4C4  bne #0x207f4a0           ; drain this bucket
0x0207F4C8  add r5, r5, #1
0x0207F4CC  cmp r5, #0x16            ; 22 buckets
0x0207F4D0  add r8, r8, #8           ; stride 8
0x0207F4D4  blt #0x207f498
```

**22 buckets of 8 bytes at `manager+0x28`**, drained each frame into a free list at `+0xD8` via generic
list helpers `0x02037C24` (unlink) and `0x02037B98` (link). A second drain loop follows over a list at
`+0x10` of another object.

### This corrects iteration 53's field map

`22 × 8 = 0xB0`, so the bucket array spans `+0x28`–`+0xD7`. Iteration 53 called `+0x70` and `+0xD0`
separate fields. They're **buckets 9 and 21** of one array — `0x28 + 9*8 = 0x70`, `0x28 + 21*8 = 0xD0`.
They looked distinct because the mapper sees individual accesses, not the array they belong to.

Lesson: a field mapper can't recognise arrays. A sparsely-used array shows up as scattered fields.

## 3. `0x0207FB60` — the phase driver

```
0x0207FB60  push {r4, lr}
0x0207FB64  ldr r0, [r0, #4]
0x0207FB68  ldr r4, [r0, #0x10]      ; the manager back-pointer again
0x0207FB6C  ldr r1, [r4, #0xfc]
0x0207FB74  blx r1
0x0207FB78  ldr r1, [r4, #0x100]
0x0207FB80  blx r1
0x0207FB84  ldr r1, [r4, #0x104]
0x0207FB8C  blx r1
```

Fetches the manager, then calls three of its fields as functions. Every write at `+0xFC`–`+0x148` uses a
pc-relative literal; resolving them gives **19 installed pointers**, 5 with a `push` prologue:

| slot | value | | slot | value |
|---|---|---|---|---|
| `+0x0FC` | `0x0207D9A4` | | `+0x11C` | `0x0207DE4C` |
| `+0x100` | `0x0207D9A8` | | `+0x120` | `0x0207DE08` |
| `+0x104` | `0x0207D9AC` | | `+0x124` | `0x0207DF60` |
| `+0x108` | `0x0207DD40` | | `+0x128` | `0x0207DFC0` |
| `+0x10C` | `0x0207DDD4` | | `+0x12C` | `0x0207DFC8` |
| `+0x110` | `0x0207DE08` | | `+0x134` | `0x0207DE80` |
| `+0x114` | `0x0207DE3C` | | `+0x138` | `0x0207DE88` |
| `+0x118` | `0x0207DE44` | | `+0x13C` | `0x0207DFF4` |
| | | | `+0x140`, `+0x144` | `0x0207DFD8` (twice) |
| | | | `+0x148` | `0x0207E010` |

So the block iteration 53 called "a second init block, stores only" is a **phase/vtable table**.

**Two of the three per-frame phases are no-ops.** `+0xFC` = `0x0207D9A4` and `+0x100` = `0x0207D9A8` are
single `bx lr` stubs. Only `+0x104` = `0x0207D9AC` does real work: 229 instructions, starting with
`ldr r5,[r0,#0x28]` — the bucket array.

## 4. REFUTED: the live phase is not the contact-matrix writer

All 229 instructions of `0x0207D9AC` scanned:

| test | result |
|---|---|
| stores at offset `>= 0x150` | **0** |
| `mov Rd,#0xC0` or `#0x30` (query 71's strides) | **none** |
| register-offset stores (`str Rd,[Rn,Rm]`) that could hide an offset | **0** |
| highest offset touched at all | **`0x78`** |

It stays inside the bucket region and never reaches `+0x158`. Iteration 54 already ruled out the
construction/teardown region. Two large areas excluded; the contact-array writer is still unfound.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x0207F480` etc. are handler *tables* | **REFUTED** *(my own, iteration 54)* — they are functions; `0x02028384` registers a callback |
| `0x0207F480` drains 22 buckets into a free list each frame | **CONFIRMED_STATIC** — `cmp r5,#0x16`, stride 8, `+0x28` → `+0xD8` |
| `+0x70` and `+0xD0` are separate list heads | **REFUTED** *(my own, iteration 53)* — buckets 9 and 21 of the `+0x28` array |
| `+0xFC`–`+0x148` is a data init block | **REFUTED** *(my own, iteration 53)* — 19 installed function pointers |
| Three phases run per frame | **CONFIRMED_STATIC** — `+0xFC`, `+0x100`, `+0x104` via `blx` |
| All three do work | **REFUTED** — `+0xFC` and `+0x100` are `bx lr` stubs |
| `0x0207D9AC` writes the contact array at `+0x158` | **REFUTED** — 0 stores ≥ `0x150`, highest offset `0x78` |
| `[subobj+4]+0x10` is the manager back-pointer | **CONFIRMED_STATIC** — both callbacks fetch it, then use manager offsets |

## Revised ColPrm layout

```
+0x00 .. +0x24   init block, 10 words
+0x28 .. +0xD7   22 bucket list heads, 8 bytes each   [+0x70 = bucket 9, +0xD0 = bucket 21]
+0xD8            free-list head
+0xE0/+0xE4/+0xE8  owned sub-objects (iteration 54)
+0xEC/+0xF0      further owned pointers
+0xFC .. +0x148  phase table, 19 function pointers; +0xFC/+0x100 are stubs, +0x104 is live
+0x14C           byte flag
+0x158           contact array (iteration 52), rows 0xC0, elements 0x30
```

## Next angles, ranked

1. **Read the other 16 phase-table entries** for a store to `+0x158`. Only 3 of 19 checked so far; the
   writer is likely among the rest.
2. **Identify the 22 buckets.** A per-frame drained bucket list of that arity in a collision manager
   points to a broadphase partition; naming the index would explain the subsystem.
3. **Read `0x0207D9AC` properly** — 229 instructions, the only live per-frame phase, currently excluded
   but not understood.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
