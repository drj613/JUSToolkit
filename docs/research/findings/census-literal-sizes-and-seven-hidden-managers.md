# Findings: the census dropped literal sizes — seven big battle managers were hidden

Loop-Atlas iteration 101. Static.

`Battle_ObjManCreate` allocates **`0x42D8`** bytes via a **pc-relative literal**, not a
`mov` immediate. The resolver only accepted `mov`, so the census missed it.

Fixing that recovered 19 sites. Allocations `≥ 0x570` went from **12 to 25**; **seven are
battle objects** — including both collision managers mapped in this campaign.

**Iteration 99's conclusion is refuted.** "No allocation `≥ 0x570` is a battle object" was
an artefact of this gap, as was the claim that the `≥0x5F1` struct at `[char+0x1b4]` is
not tagged-allocated.

---

## 1. The gap

```python
'size': size[1] if size[0] == 'imm' else None,     # dropped 'lit'
```

Large sizes exceed ARM's rotated immediate, so the compiler emits them as pc-relative literals:

```
0x0207C4D4  ldr r0, [pc, #0x378]     ; Battle_ColPrmManCreate: 0xFB54
0x0207C4E0  bl  #0x201a21c

0x02083210  ldr r0, [pc, #0x234]     ; Battle_ObjManCreate: 0x42D8
0x0208321C  bl  #0x201a21c
```

These are the allocations most worth knowing. Sized sites: **640 → 659**; unresolved:
**92 → 73**.

## 2. The seven hidden battle allocations

| size | site | function | file |
|---|---|---|---|
| `0xFB54` | `0x0207C4E0` | **`Battle_ColPrmManCreate`** | `BattleColPrm.cpp` |
| `0x42D8` | `0x0208321C` | **`Battle_ObjManCreate`** | `BattleObj.cpp` |
| `0x3FD4` | `0x0216A7D4` | `Battle_ObjShotManCreate` | `BattleObjShot.cpp` |
| `0x2648` | `0x02082A50` | `Battle_MoveManCreate` | `BattleMove.cpp` |
| `0x219C` | `0x0207AD54` | **`Battle_ColManCreate`** | `BattleCol.cpp` |
| `0x11E4` | `0x021644E8` | `BattleMapLoadItem` | `BattleMapItem.cpp` |
| `0x1040` | `0x0207BD5C` | `Battle_ColJointManCreate` | `BattleColJoint.cpp` |

Three close open questions:

**`Battle_ColPrmManCreate` is `0xFB54`.** Buckets (`+0x28`–`+0xD7`), phase table
(`+0xFC`–`+0x148`), and contact array (`+0x154`, rows `0xC0`, elements `0x30`) now have a
confirmed total size. `0xFB54` is consistent with that contact array.

**`Battle_ColManCreate` is `0x219C`.** Iteration 79 ruled `BattleCol.cpp` `+0x90` sites
out on module grounds; the size confirms `+0x90` fits comfortably.

**`Battle_MoveManCreate` is new** — a `0x2648` manager in `BattleMove.cpp`, never examined
in this campaign.

## 3. What this refutes

Iteration 99 listed 12 allocations `≥ 0x570` and concluded none was the `≥0x5F1` struct at
`[char+0x1b4]`. With seven battle allocations restored, that reasoning collapses — all
seven exceed the `0x5F1` floor.

Still **no battle allocation between `0x5F1` and `0x1040`** — that band is WiFi
friend-match, friend list, voice chat, `Demo_Add`, comms, and quiz overlay. The struct is
either one of the seven large managers or not tagged-allocated. **Reopened, not resolved.**

## 4. `Battle_ObjManCreate`'s own shape

```
0x0208322C-0x02083240   zero +0x0C, +0x10, +0x14, +0x18, +0x1C, +0x20
0x02083244  add r1, r4, #0x24
0x02083248  add r2, r4, #0x74
0x0208324C  str r0, [r1]         ; loop: two words at a time
0x02083250  str r0, [r1, #4]
0x02083254  add r1, r1, #8
0x02083258  cmp r1, r2
0x0208325C  blo #0x208324c
0x02083260  add r0, r4, #0x84
```

`+0x24`–`+0x73`: a `0x50`-byte table cleared in 8-byte units — ten entries of two words.

## Predictions status

| Claim | Verdict |
|---|---|
| `alloc_census.py` resolved every unconditional size | **REFUTED** — pc-literal sizes were discarded; 19 sites recovered |
| `Battle_ObjManCreate` allocates `0x42D8` | **CONFIRMED_STATIC** — `ldr r0,[pc,#0x234]` → `[0x0208344C]` = `0x42D8` |
| `Battle_ColPrmManCreate` allocates `0xFB54` | **CONFIRMED_STATIC** — `ldr r0,[pc,#0x378]` at `0x0207C4D4` |
| `Battle_ColManCreate` allocates `0x219C` | **CONFIRMED_STATIC** — `ldr r0,[pc,#0x13c]` at `0x0207AD48` |
| No allocation `≥ 0x570` is a battle object | **REFUTED** *(iteration 99, mine)* — seven are |
| The `≥0x5F1` struct is not tagged-allocated | **REFUTED as established** — the census that supported it was incomplete; the question is reopened |
| A battle allocation exists between `0x5F1` and `0x1040` | **REFUTED** — that band is WiFi, comms, demo and quiz code |
| `Battle_ObjMan` has a `0x50`-byte table at `+0x24` | **CONFIRMED_STATIC** — `add r1,r4,#0x24`; `cmp r1,r2` against `r4+0x74`; 8-byte stride |
| One of the seven managers is the `[char+0x1b4]` struct | **not claimed** — all exceed the `0x5F1` floor; none is tied to it |

## Next angles, ranked

1. **Test the seven against `[char+0x1b4]`.** Check each constructor for the `+0x56c`
   gauge pointer and the byte at `+0x5F0`.
2. **Read `Battle_MoveManCreate` `0x02082A50`** — `0x2648` manager in `BattleMove.cpp`,
   never examined.
3. **Re-check claims resting on census coverage.** Third coverage bug in four wakes.
4. **Find what initialises the collision managers** (carried) — `Battle_Add` does not.
