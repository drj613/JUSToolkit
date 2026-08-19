# Findings: 275 function names recovered from assert strings, and how the collision stubs are dispatched

Loop-Atlas iteration 41. Static. New tool: `scripts/decomp/extract_symbols.py`.
Output: `jus_files/analysis/symbols.json`.

Goal: find callers of the 31 ov6 collision stubs from iteration 40, expecting to reach the
`CollisionEntry` walker. The callers turned out to be a function-pointer table — answers the
mechanism, not the walker. Following that table into the ov6 data region uncovered something bigger:
**the retail ROM still has the developers' assert strings**, pairing function names with source
filenames.

**275 distinct functions now have their real names.** 40 prior iterations used bare addresses only.

---

## 1. The stubs are dispatched through a 68-entry function-pointer table

Direct-call scan (ARM BL + Thumb BL/BLX) over the 36 stub entry points: **15 call sites total, 28
of 36 stubs have zero direct callers.** They are not called by name.

Searching all binaries for the stub addresses as 32-bit words: 33 references, all in ov6, all in
one region. Dumping `0x02171FD0`–`0x02172120` shows every word from **`0x02171FEC` to `0x021720F8`**
is an ov6 code pointer — a contiguous **68-entry function-pointer table** with no gaps.

The stubs are dispatch-table entries. **This does not identify the walker.** Whatever indexes this
table is the next step.

## 2. The ROM kept its assert strings

The table sits in a data region bracketed by ASCII. Just before it: `battle/win_bt00.aar`. Just
after: `Battle_NoteTrackCreate`, then `BattleNoteTrack.cpp`.

That is the signature of a compiled-in assert — function name plus source file. The region has
dozens more:

| function name | source file |
|---|---|
| `Battle_CharaCreate` | `BattleChara.cpp` |
| `Battle_CharaDataInit` | `BattleCharaDataLoad.cpp` |
| `Battle_CharaParamCreate` | `BattleCharaParam.cpp` |
| `Battle_PursuerCreate` | `BattleCharaPursuer.cpp` |
| `Battle_MarkerCreate` | `BattleMarker.cpp` |
| `Battle_ObjCtrlManCreate` | `BattleObjCtrl.cpp` |
| **`Battle_ObjShotManCreate`** | **`BattleObjShot.cpp`** |
| `BattleMapGimmick_Create` | `BattleMapGimmick.cpp` |
| `BattleMapInitWall` | `BattleMapWall.cpp` |

Data paths appear alongside them, several already found the hard way:
`chr/col/item.bin`, `chr/col/`, `chr/shot/`, `chr/effect/`, `bin/state.bin`, `bin/exadd.bin`,
`bin/clear.bin`, `item/J_Power.aar`, `item/itemprob.ipf`, `stage/stage.aar`.

### Scale

**211 distinct `.cpp` source filenames** across arm9 and the 14 overlays. Binding each name to the
function that references its literal: **324 bindings, 275 distinct function addresses**:

| binary | named functions | | binary | named functions |
|---|---|---|---|---|
| arm9 | 91 | | ov6 | 25 |
| ov0 | 13 | | ov7 | 45 |
| ov1 | 14 | | ov8 | 1 |
| ov2 | 13 | | ov10 | 19 |
| ov3 | 6 | | ov11 | 6 |
| ov4 | 40 | | ov12 | 35 |
| ov5 | 16 | | | |

### Method and limits

For each NUL-terminated identifier, find the 32-bit literal pointing at it, then walk back to the
nearest preceding `stmfd sp!,{...,lr}`. That push is the function prologue, so the binding names a
real function. Literals more than `0x800` from a prologue are discarded.

Two limits (both stated in the tool output):

- **Only functions with an assert string get a name.** 275 out of thousands. This is not a symbol
  table.
- **`--nearest` gives neighbourhood, not containment.** Unnamed functions sit between named ones, so
  `Battle_ObjShotManCreate + 0x219C` means "after that function", **not** "inside it". ARM
  toolchains emit code per translation unit, so a near neighbour is usually the same `.cpp` — useful,
  but only PLAUSIBLE.

`Battle-Engine-Map.md` claim 7 (chrb-catalog) already used this trick once (`BattleAI_*` strings
confirming ov11 is battle AI) but never generalised it. The campaign's own note was the clue and
sat unused for many iterations.

## 3. Applied: this strengthens projectile-entities claim 5

`Battle-Engine-Map.md` projectile-entities claim 5 caps `0x0216C958` at **PLAUSIBLE** because sibling
routines `0x0216E1C0` and `0x0216F398` reuse identical scaffolding — static analysis alone cannot
show `0x0216C958` is *the* projectile despawn rather than a generic spawned-effect routine.

Neighbourhood attribution for all three:

| address | nearest named function |
|---|---|
| `0x0216C958` (claim 5 despawn) | `Battle_ObjShotManCreate` + `0x219C` |
| `0x0216E1C0` (sibling) | `Battle_ObjShotManCreate` + `0x3A04` |
| `0x0216F398` (sibling) | `Battle_ObjShotManCreate` + `0x4BDC` |

All three sit after `Battle_ObjShotManCreate`, whose source file is `BattleObjShot.cpp` — the
projectile ("object shot") module. The identical scaffolding is explained: they are **siblings in the
same translation unit**, not evidence that `0x0216C958` belongs to a generic-effect system.

This removes the specific doubt claim 5 recorded ("or a generic spawned-effect one") because the
whole sibling family is projectile code. It does **not** prove which of the three is the despawn.
Claim 5 stays **PLAUSIBLE** — doubt narrowed, not eliminated. Neighbourhood evidence cannot carry
CONFIRMED_STATIC.

Contrast: `0x02168CF4` (claim 4, spawn and ownership) is nearest `Battle_ObjCtrlManCreate`
(`BattleObjCtrl.cpp`) — a **different module** from ObjShot. Spawn-ownership and despawn live in
separate translation units, worth knowing before assuming one calls the other directly.

The iteration-40 stub bank lands nearest `Battle_NoteTrackCreate` (`BattleNoteTrack.cpp`), so those
collision accessors are probably not projectile code at all.

## Predictions status

| Claim | Verdict |
|---|---|
| The 31 stubs have direct callers leading to the record walker | **REFUTED** — 28 of 36 have zero direct callers |
| The stubs are reached through a function-pointer table | **CONFIRMED_STATIC** — contiguous 68-entry table, `0x02171FEC`–`0x021720F8` |
| The ROM retains assert strings pairing function names with source files | **CONFIRMED_STATIC** — 211 `.cpp` names, 324 bindings |
| 275 distinct functions can be named this way | **CONFIRMED_STATIC** — `jus_files/analysis/symbols.json` |
| `Battle_ObjShotManCreate` is at `0x0216A7BC` | **CONFIRMED_STATIC** — literal `0x02172774` |
| Claim 5's three sibling routines are all projectile-module code | **PLAUSIBLE** — all nearest `Battle_ObjShotManCreate`; neighbourhood, not containment |
| `0x0216C958` is specifically the despawn among the three | **still open** — not settled by this |
| The iteration-40 collision stub bank is projectile code | **unlikely** — nearest `Battle_NoteTrackCreate` |

## Next angles, ranked

1. **Re-attribute every address in `Battle-Engine-Map.md` via `--nearest`.** Dozens of bare addresses
   across 40 iterations; each now gets a module. Cheap, likely to confirm or correct several
   subsystem assignments at once.
2. **Find what indexes the 68-entry table.** The real answer to the walker question.
3. **Extract the `.cpp` filename list as a module map.** 211 translation units ordered by address
   would tighten neighbourhood inference and turn PLAUSIBLE attributions into bounded ranges.
4. Still open: what reads slot`+0x02` (the `ProjectileId` consumer), and the 24 positive
   `ProjectileId` values.
