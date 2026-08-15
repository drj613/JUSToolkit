# Findings: `Battle_PrmDataInit` is the collision/shot/effect loader, and where the arrays land

Loop-Atlas iteration 43. Static.

Two approaches were tested: `.cpp` references for map density, and path literals for function identification. The first fails; the second works.

Result: **`Battle_PrmDataInit` at `0x021702BC` loads `chr/col/`, `chr/shot/` and `chr/effect/`, storing the collision array pointer at `prmData+0x00`.**

---

## 1. REFUTED: `.cpp` references cannot densify the module map

Most modules only assert once, so `.cpp` references barely help. Measured on ov6:

- 22 distinct `.cpp` strings, **26 literal references total** — one assert per file.
- Only `BattleMapItem.cpp` (4) and `BattleCharaInfo.cpp` (2) have more than one.
- Markers went from 21 to 24; median gap improved from `0x14D0` to `0x119C`; **max gap unchanged
  at `0x8618`.**

ov6 has **561 ARM function prologues** and 24 markers. The 134 LOOSE attributions stay loose. Dead end — do not retry.

## 2. Path literals identify functions by purpose

A function that loads a file references that file's path. Each path literal resolved to its enclosing function:

| path literal | function | name (from the module map) |
|---|---|---|
| `chr/col/`, `chr/col/item.bin`, `chr/shot/`, `chr/effect/` | `0x021702BC` | **`Battle_PrmDataInit`** |
| `bin/state.bin`, `bin/exadd.bin` | `0x021614B0` | `Battle_CharaParamCreate` |
| `item/J_Power.aar`, `item/itemprob.ipf` | `0x021644C4` | `BattleMapLoadItem` |
| `chr/ai/` | ov11 `0x02177060`, ov11 `0x02181028` | (unnamed) |

The `chr/ai/` row feeds the queued ov11 battle-AI task.

This is semantic labelling, not boundary refinement — a different use of markers than iteration 42 proposed, and the one that paid off.

## 3. `Battle_PrmDataInit` decoded

Signature, from the prologue: `Battle_PrmDataInit(r0 = kind, r1 = index)`.

```
0x021702BC: push {r3, r4, r5, r6, r7, lr}
0x021702C4: mov r7, r0            ; kind
0x021702C8: mov r6, r1            ; index
0x021702CC: mov r0, #0x20
0x021702DC: bl #0x201a21c         ; allocate 0x20 bytes  (asserts with "Battle_PrmDataInit")
0x021702EC: bl #0x20517fc         ; memset 0x20 bytes to 0
0x021702F4: strh r1, [r4, #0x18]  ; = -1
0x021702FC: strh r0, [r4, #0x1a]  ; = 0x7a
0x02170300: strh r1, [r4, #0x1c]  ; = -1
0x02170304: strh r1, [r4, #0x1e]  ; = -1
```

A 3-way switch on `kind` picks a name table, indexed by `index` at **8-byte stride** (`add r5, r0, r6, lsl #3`):

| `kind` | table | meaning |
|---|---|---|
| 0 | `0x020924B0` | battle characters |
| 1 | `0x02092700` | support characters |
| 2 | `chr/col/item.bin` loaded directly, `r5 = 0` | the item collision file |

For each data kind it builds `prefix + name + ".bin"` on the stack (`bl 0x2074000` copy, `bl 0x20741bc` append), checks existence with `bl 0x2033bb8`, loads with `bl 0x206da64`, and stores the result. Prefixes come from the literal pool:

| store | prefix literal | resolves to |
|---|---|---|
| `0x02170380` `str r0,[r4,#0x0]` | pool `0x02170488` | `"chr/col/"` |
| `0x021703C0` `str r0,[r4,#0x4]` | pool `0x02170490` | `"chr/shot/"` |
| `0x02170400` `str r0,[r4,#0x8]` | pool `0x02170494` | `"chr/effect/"` |

The shared suffix literal at pool `0x0217048C` is `".bin"`, so filenames are `chr/col/<name>.bin` — matching the extracted layout exactly.

**PrmData struct:**

```
+0x00  pointer to the loaded chr/col/*.bin   <- the collision record array
+0x04  pointer to the loaded chr/shot/*.bin
+0x08  pointer to the loaded chr/effect/*.bin
+0x0C  three further loads at 0x0217041C, 0x02170440, 0x02170464 (prefixes unresolved)
+0x10
+0x14
+0x18  halfword, init -1
+0x1A  halfword, init 0x7a
+0x1C  halfword, init -1
+0x1E  halfword, init -1
```

In the `kind == 2` (item) path the collision pointer is stored by `0x02170344`, also to `[r4,#0x0]`.

### Why this matters

`Battle-Engine-Map.md` has asked since early on where the runtime collision array lives. **It lives at `prmData+0x00`.** The walker must read it from there, so the next search targets code loading `+0x00` off this struct.

## 4. The name tables cross-validate three earlier results

At `0x020924B0`, 8-byte stride, each entry is `{const char *name, u32 extra}`:

| index | name | extra |
|---|---|---|
| 0 | `db_b_01` | `0x0005C100` |
| 1 | `db_b_02` | `0x0005C200` |
| 2 | `db_b_03` | `0x0005C300` |
| 73 | `dt_b_04` | `0x000A8400` |
| **74** | **`db_s_01`** | `0x0015C100` |

Index 74 rolls into the support table: `0x02092700 - 0x020924B0 = 0x250 = 74 × 8`. The support table runs `db_s_01` … `dt_s_03` at index 192; index 193 (`bg_es`) is past the end.

One contiguous table split at 74: **74 battle characters, 193 support characters** — 267 total. This matches the split iteration 38 inferred from `chr/ai` file counts (74 `_b_` files, 193 `_s_` files), reached by a completely different route.

`extra` increments by `0x100` per index, starting at `0x0005C100` for battle and `0x0015C100` for support.

### Prior art

**This table was already documented.** `docs/research/ARM9-Research-Guide.md:44` records "Collision file pointer table" at file offset `0x0924B0`, and lines 123–127 list `[0] db_b_01 - extra=0x0005C100` and `[39] bl_b_01 - extra=0x00078100`. Runtime address `0x02000000 + 0x924B0 = 0x020924B0` is the same table.

What's new is the **consumer**: `Battle_PrmDataInit` reads it, the same table drives shot and effect loading too, and the `kind` switch has a third item-only case. The guide found the table by string-searching `bl_b_01` but never connected it to loading code.

## Predictions status

| Claim | Verdict |
|---|---|
| `.cpp` literal references can densify the module map | **REFUTED** — 26 refs for 22 files; max gap unchanged at `0x8618` |
| Path literals identify a function's purpose | **CONFIRMED_STATIC** — 4 loaders identified |
| `Battle_PrmDataInit` `0x021702BC` loads col, shot and effect data | **CONFIRMED_STATIC** — three prefix literals resolved from its pool |
| The collision array pointer is stored at `prmData+0x00` | **CONFIRMED_STATIC** — `0x02170380`, prefix pool `0x02170488` = `"chr/col/"` |
| `+0x04` is the shot array, `+0x08` the effect array | **CONFIRMED_STATIC** — pools `0x02170490`, `0x02170494` |
| `0x020924B0` holds 74 battle-character entries at 8-byte stride | **CONFIRMED_STATIC** — index 73 `dt_b_04`, index 74 rolls into `db_s_01`; `0x250 = 74 × 8` |
| `0x02092700` holds 193 support-character entries | **CONFIRMED_STATIC** — index 192 `dt_s_03` |
| This name table was an unknown | **REFUTED** — `ARM9-Research-Guide.md:44,123-127` already had it; the *consumer* is new |
| `prmData+0x0C/+0x10/+0x14` hold three further loaded files | **PLAUSIBLE** — stores confirmed, prefixes unresolved |

## Next angles, ranked

1. **Find code that loads `+0x00` off a PrmData pointer.** That's the collision-array consumer — the most direct route to the walker. The struct is only `0x20` bytes, so `+0x00` is common; constrain by requiring a nearby `#0x14` stride multiply, or start from `Battle_PrmDataInit`'s callers.
2. **Resolve the `+0x0C/+0x10/+0x14` prefixes** — three unidentified per-character data files.
3. Still open: what indexes the 68-entry table at `0x02171FEC`, what reads spawn-slot`+0x02`, and the 24 positive `ProjectileId` values.
