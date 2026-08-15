# Findings: collision is three modules, and five new symbol names

Loop-Atlas iteration 65. Static.

Named `*(0x0214BE0C)` — it is the **ColJoint** manager. That lookup surfaced **five unrecorded collision
symbols**, proving the collision system is **three source modules**, not one.

Also ran a fifth check on the bucket-1 contradiction: **no overlay stores to ColPrm's bucket heads
either.**

---

## 1. Five new symbols, three modules

| address | symbol | module |
|---|---|---|
| `0x0207AD3C` | `Battle_ColManCreate` | `BattleCol.cpp` |
| `0x0207AEDC` | `Battle_ColObjCreate` | `BattleCol.cpp` |
| `0x0207B11C` | `Battle_ColObjAddColWork` | `BattleCol.cpp` |
| `0x0207BD40` | `Battle_ColJointManCreate` | `BattleColJoint.cpp` |
| `0x0207C4C0` | `Battle_ColPrmManCreate` | `BattleColPrm.cpp` |

All five were already in `symbols.json` from iteration 41 — never queried for `Col` until now.

The collision system is a three-layer stack:

```
BattleCol.cpp        ColMan + ColObj + ColWork   the base collision objects
BattleColJoint.cpp   ColJoint manager  = *(0x0214BE0C)
BattleColPrm.cpp     ColPrm manager    = *(0x0214BE10)   (the 22 buckets, contact matrix)
```

Iterations 52–64 mapped only the **ColPrm** layer. `BattleCol.cpp` and `BattleColJoint.cpp` are untouched
and sit below it in address order — likely where the collided entities live.

`Battle_ColPrmManCreate` at `0x0207C4C0` pins the contact-array writer at `0x02081340` exactly:
`Battle_ColPrmManCreate + 0x4E80` (iteration 56 had only a neighbourhood).

## 2. `*(0x0214BE0C)` is the ColJoint manager

Nine references in arm9, **one writer**:

| site | role |
|---|---|
| `0x0207BE70` | `str r4,[r1,#0]` — installs the manager |
| 8 others | read it |

It owns an 8-stride list array **at offset 0** (not `+0x28` like ColPrm's), indexed by a small register.
`cmp r6,#0x2` follows one insertion, so the index space is tiny. Insertions unlink from `+0x18` of a
node, then link into `array[idx]`.

## 3. `Battle_ColObjAddColWork` — what it is not

41 instructions:

```
0x0207B130  ldr r0,[r6,#0x18]     ; a guard on the owner
0x0207B14C  mov r0,#0x64
0x0207B150  bl 0x0201A21C         ; allocate 0x64 bytes (asserts at line 0x225)
0x0207B170  bl 0x020517FC         ; memset 0x64
0x0207B178  add r0,r6,#0x8
0x0207B17C  bl 0x02037B98         ; link into the OWNER's list at +0x8
0x0207B190  str r6,[r4,#0x20]     ; back-pointer to the owner
0x0207B194  str r0,[r4,#0x18]     ; = 0x20
```

A **ColWork is a `0x64`-byte record** linked onto a ColObj's list at `+0x8`, with a back-pointer at `+0x20`.

**It does not touch a ColPrm bucket** — does not explain the missing producers for buckets 1 and 8.

## 4. Fifth negative on the contradiction

Iteration 64's five checks were all **arm9-only**. Since iteration 52 found an ov6 reference to
`0x0214BE10`, overlays were an open hole.

Closed: all 14 overlays have exactly **one** reference to the ColPrm global — ov6 `0x02157EC8` (query
71), a reader. It dereferences the manager and stores nothing.

No overlay writes those buckets. The contradiction stands after a sixth check.

## Predictions status

| Claim | Verdict |
|---|---|
| `*(0x0214BE0C)` is the ColJoint manager | **CONFIRMED_STATIC** — `Battle_ColJointManCreate` `0x0207BD40`, `BattleColJoint.cpp` |
| It is installed at `0x0207BE70` | **CONFIRMED_STATIC** — the only write of 9 references |
| Collision is one module | **REFUTED** — three: `BattleCol.cpp`, `BattleColJoint.cpp`, `BattleColPrm.cpp` |
| `Battle_ColPrmManCreate` is at `0x0207C4C0` | **CONFIRMED_STATIC** — makes iteration 56's `+0x4E80` neighbourhood exact |
| A ColWork is a `0x64`-byte record on a ColObj's `+0x8` list | **CONFIRMED_STATIC** — `0x0207B14C`, `0x0207B17C` |
| `Battle_ColObjAddColWork` fills a ColPrm bucket | **REFUTED** — links into the owner's `+0x8`, not the manager |
| An overlay fills bucket 1 or 8 | **REFUTED** — 1 overlay reference to ColPrm total, and it is a read |
| The ColJoint array is at `+0x28` like ColPrm's | **REFUTED** — offset 0 |

## Next angles, ranked

1. **Query `symbols.json` before every subsystem task.** Five names sat unread for 24 wakes. A grep
   should precede any new investigation — add to the loose-ends rule.
2. **Map `BattleCol.cpp`** — `Battle_ColManCreate` and `Battle_ColObjCreate` are the layer beneath
   everything mapped so far; the ColPrm buckets probably hold ColObjs.
3. **Harness watchpoint on `ColPrm+0x154`** — the only path left to resolve the bucket-1 contradiction,
   now surviving six static checks.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values.
