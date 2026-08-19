# Findings: the record's detach routine — four list heads, and `+0x68` is a partner link

Loop-Atlas iteration 83. Static.

Chasing `record+0x68` found `0x0207CB58`, the ColPrm record's **detach routine**, and a
correction: the record has **four** node lists, not one.

`+0x68` points to another object with a `+0x20` node list — and the record itself has a
`+0x20` node list. The simplest reading: `+0x68` links one record to another.

---

## 1. Finding it: distinctive companions, then module scope

The first sweep for `+0x68` writers returned 55 sites with a dozen apparent matches,
all in low arm9 (`0x0202xxxx`–`0x020Axxxx`), nowhere near collision code. The companion
list was too generic: `+0x50`, `+0x5c`, `+0x60`, `+0x6c` are common offsets that match
everything — the same trap as iteration 76's `+0x08` mistake.

Restricting to the record's distinctive offsets (`+0x174`, `+0x175`, `+0x182`, `+0x184`,
`+0x186`) gave **zero** matches. Restricting to the collision modules
`0x0207A000`–`0x02084000` gave **exactly one** store:

```
0x0207CBC8  str r5, [r0, #0x68]        (r5 = 0)
```

inside `0x0207CB58`. Lesson: scope by module when a struct's distinctive fields live in
code the target never runs.

## 2. `0x0207CB58` is the record's detach routine

`r0` is the record. It sets bit `0x100` in `+0x40` — the same flags word where the
installer clears `0x200` and ov6 tests `0x800`.

```
0x0207CB5C  mov sl, r0             ; sl = the record
0x0207CB60  ldr r0, [sl, #0x40]
0x0207CB68  orr r0, r0, #0x100     ; set a flag
0x0207CB70  add r6, sl, #0x10      ; first list head
...
0x0207CBE8  add r8, r8, #1
0x0207CBEC  cmp r8, #3
0x0207CBF0  add r6, r6, #8         ; -> +0x10, +0x18, +0x20
0x0207CBF4  blt #0x207cb80
```

Three passes over three list heads. Pass 0 frees; passes 1–2 unlink:

| pass | head | action |
|---|---|---|
| 0 | `+0x10` | `memset(node, 0, 0x10)`, `link(mgr+0x20, node)` — a `0x10`-byte node returned to the manager's free pool |
| 1, 2 | `+0x18`, `+0x20` | `r0 = [node+8]`; `str 0,[r0,#0x68]`; `str 0,[node+8]`; `link(mgr+0xD8, node)` |

Then it sweeps the manager's bucket array:

```
0x0207CC08  add r5, r0, #0x28      ; the bucket array
0x0207CC14  ldr r0, [r6, #8]
0x0207CC18  cmp sl, r0             ; a node belonging to this record?
0x0207CC28  bl  #0x2037c24         ; unlink it
0x0207CC54  cmp r4, #0x16          ; all 22 buckets
0x0207CC58  add r5, r5, #8
```

`0x16` = 22, matching the bucket array at `+0x28`–`+0xD7`. Finally it unlinks the record
from a manager-rooted list head.

Sole caller: `0x02083648`, in the same arm9 module as the pooled-entity constructor
`0x020834D4` and shim `0x02083624`. **Detach happens at entity teardown** — the mirror of
iteration 74's attach-at-construction finding.

## 3. `+0x68` is a back-pointer that gets cleared

`str r5,[r0,#0x68]` with `r5 = 0`, where `r0 = [node+8]`. Teardown clears `+0x68` on the
object at the far end.

At `0x0207CCD4` the same field is read from the other direction: `r2 = [record+0x68]`,
then walk `[r2+0x20]` for nodes whose `+0x8` is this record.

Both halves fit if `+0x68` points at **another ColPrm record**: a record has a `+0x20`
node list (pass 2 above), and its nodes carry an owner at `+0x8`. It cannot be the
manager — the manager's `+0x20` is a `0x10`-byte free pool (iteration 69), and unlinking
bucket nodes from a free pool into `+0xD8` would be incoherent.

**Not claimed:** which record, or what the pairing means. No non-zero `+0x68` write was
found in the collision modules — only this clear.

## 4. Correction: the record has four list heads

Iteration 78's map recorded `+0x08` as "the" node list. It is one of four:

| head | node type | evidence |
|---|---|---|
| `+0x08` | `0x2C`-byte pool nodes | `add r0,r4,#8` then link, `0x0207D490` (iteration 70) |
| `+0x10` | `0x10`-byte nodes, freed to `mgr+0x20` | pass 0 here |
| `+0x18` | bucket nodes, freed to `mgr+0xD8` | pass 1 here |
| `+0x20` | bucket nodes, freed to `mgr+0xD8` | pass 2 here |

**Hazard, live:** iteration 69 established `+0x18` and `+0x20` as the *ColPrm manager's*
free pools. They are also the *record's* list heads. Same offsets, different structs, one
subsystem — the sixth instance of this pattern, and the first near-merge.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x0207CB58` operates on a ColPrm record | **CONFIRMED_STATIC** — sets bit `0x100` in `+0x40`, the known flags word; bucket nodes matched by `[node+8] == sl` |
| The record has list heads at `+0x10`, `+0x18` and `+0x20` | **CONFIRMED_STATIC** — `add r6,sl,#0x10` then `add r6,r6,#8` × 3, `cmp r8,#3` |
| `+0x10` holds `0x10`-byte nodes freed to `mgr+0x20` | **CONFIRMED_STATIC** — `memset` `0x10` then `link(mgr+0x20)` |
| `+0x18` and `+0x20` hold bucket nodes freed to `mgr+0xD8` | **CONFIRMED_STATIC** — `link(mgr+0xD8, node)` at `0x0207CBD8` |
| The routine sweeps all 22 manager buckets | **CONFIRMED_STATIC** — `add r5,r0,#0x28`, `cmp r4,#0x16`, stride 8 |
| Detach runs at entity teardown | **CONFIRMED_STATIC** — sole caller `0x02083648`, the pooled-entity module |
| `record+0x40` bit `0x100` is set on detach | **CONFIRMED_STATIC** — `orr r0,r0,#0x100` at `0x0207CB68` |
| The record has one node list, at `+0x08` | **REFUTED** *(iteration 78)* — four heads |
| `[record+0x68]` is the ColPrm manager | **REFUTED** — the manager's `+0x20` is a `0x10`-byte free pool; the walk needs a bucket-node list |
| `[record+0x68]` is another ColPrm record | **PLAUSIBLE** — a record does have a `+0x20` node list with owners at `+0x8` |
| Anything writes a non-zero `+0x68` | **not claimed** — one store in the collision modules, and it writes `0` |

## Next angles, ranked

1. **Find who sets `+0x68` non-zero.** Cleared here and read by teardown, so a writer
   exists — outside the collision modules, or in a form the sweep misses (`stm`,
   register-offset, Thumb). Finding it names the pairing.
2. **Re-run the record map** with `0x0207CB58` and `0x0207CCD4` as anchors — this pass
   found three fields the last map missed.
3. **Re-audit the map's `char+0xNN` offsets** across the three objects (carried).
4. **Name the arm9 `+0x56c` struct** (carried) — candidate `memset(r7+0x8, 0x5e0)` at
   `0x02076C2C`.
