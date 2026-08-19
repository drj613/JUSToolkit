# Findings: a source-module map for the ROM, and why bulk re-attribution mostly fails

Loop-Atlas iteration 42. Static. Output: `jus_files/analysis/modules.json`.

Iteration 41 planned to re-attribute all 194 addresses in `Battle-Engine-Map.md` to source modules.

**Mostly refuted. Only 43 of 194 addresses (22%) land in a trustworthy range.** The rest fall inside
module gaps 0x2000–0x8618 bytes wide — too coarse to mean anything.

The 22% that works confirms the three-layer projectile-entities architecture and places claims 1 and 2
in a named module with a tight bound.

---

## 1. The module map

Each assert embeds both a function name and a source filename. Pairing them per function and sorting
by address gives module boundaries. All 25 of ov6's named functions resolve to a `.cpp`:

| module | first named function |
|---|---|
| `BattlePause.cpp` | `0x0214E388` `Battle_PauseCreate` |
| `BattlePauseWiFi.cpp` | `0x0214F524` `Battle_PauseWiFiCreate` |
| `BattleTutorial.cpp` | `0x0214F7AC` `Battle_TutorialCreate` |
| `BattleCamera.cpp` | `0x02151BE8` `Battle_CameraCreate` |
| `BattleComicDeck.cpp` | `0x02152110` `Battle_ComicDeckCreate` |
| `BattleDemo.cpp` | `0x021537E0` `Battle_DemoKoCreate` |
| `BattleWindow.cpp` | `0x02153EE0` `Battle_WindowCreate` |
| `BattleNoteTrack.cpp` | `0x021553E0` `Battle_NoteTrackCreate` |
| `BattleChara.cpp` | `0x02156A38` `Battle_CharaCreate` |
| `BattleCharaDataLoad.cpp` | `0x0215F050` `Battle_CharaDataInit` |
| `BattleCharaInfo.cpp` | `0x0215FFE0` `Battle_CharaInfoCreate` |
| `BattleCharaParam.cpp` | `0x021614B0` `Battle_CharaParamCreate` |
| `BattleCharaPursuer.cpp` | `0x02161608` `Battle_PursuerCreate` |
| `BattleMap.cpp` | `0x02161CB4` `BattleMapInit` |
| `BattleMapGimmick.cpp` | `0x02163188` `BattleMapGimmick_Create` |
| `BattleMapItem.cpp` | `0x021644C4` `BattleMapLoadItem` |
| `BattleMapWall.cpp` | `0x021671E8` `BattleMapInitWall` |
| `BattleMarker.cpp` | `0x02167F20` `Battle_MarkerCreate` |
| `BattleObjCtrl.cpp` | `0x02168B88` `Battle_ObjCtrlManCreate` |
| `BattleObjShot.cpp` | `0x0216A7BC` `Battle_ObjShotManCreate` |
| `BattlePrmData.cpp` | `0x021702BC` `Battle_PrmDataInit` |

## 2. A phantom-overlay bug in my own tool, caught before it was written up

First attribution run produced nonsense: battle-engine addresses landing in `Option.cpp`,
`Opening.cpp`, `Movie.cpp` and `EndingCopyright.cpp`.

Cause: **ten overlays share load address `0x0214CD20`.** The lookup walked every binary and returned the
first whose span contained the query address, so `0x0215xxxx` matched ov0 as well as ov6, and dict
order decided.

This is the same bug `scripts/decomp/find_callers.py` already warns about. Fixed by requiring an
explicit `ovN` label and defaulting to ov6 (the battle overlay) when none is named.

Worth recording: the nonsense was obvious this time. A wrong module that happened to look plausible
would have gone unnoticed.

## 3. The real limit: marker density

Only functions with an assert get a name, so module starts are sparse and each one spans the entire gap
until the next:

| binary | modules | span | median gap | max gap |
|---|---|---|---|---|
| arm9 | 29 | 0x1FDB8 | 0xB60 | 0x6578 |
| ov4 | 37 | 0x12458 | 0x758 | 0x14C8 |
| ov5 | 22 | 0x206A8 | 0x124C | 0x5540 |
| ov6 | 21 | 0x21F34 | 0x14D0 | 0x8618 |
| ov11 | 6 | 0xAD38 | 0x260C | 0x3ED8 |

Using ≤`0x2000` as the trust threshold:

- **43 of 194 attributions are tight.**
- **134 fall in ranges too wide to trust** — all 53 addresses in `BattleChara.cpp` and all 45 in
  `arm9:ComicDeck.cpp` included.
- 17 are unattributable (below the first named module, or the line names several overlays).

The two biggest apparent results are the two I have to discard. `arm9:ComicDeck.cpp` "containing" the
core HP-apply function `0x02078488` comes from a 0x2D18-wide range — meaningless. The HP pipeline's
module is still unknown.

An unnamed translation unit can sit anywhere inside a gap, so even a tight range **bounds** rather than
proves. Nothing here earns CONFIRMED_STATIC on its own.

## 4. What the tight 22% bought: the projectile-entities architecture

The four projectile-entities addresses that matter all attribute cleanly, and they land in three
different modules:

| claim | address | module | range | width |
|---|---|---|---|---|
| 1 — pooled-entity constructor | `0x020834D4` | **arm9 `BattleObj.cpp`** | `[0x02083204, 0x02083FCC)` | `0xDC8` TIGHT |
| 2 — symmetric destructor | `0x02083648` | **arm9 `BattleObj.cpp`** | `[0x02083204, 0x02083FCC)` | `0xDC8` TIGHT |
| 4 — spawn + ownership | `0x02168CF4` | **ov6 `BattleObjCtrl.cpp`** | `[0x02168B88, 0x0216A7BC)` | `0x1C34` |
| 5 — despawn + 2 siblings | `0x0216C958`, `0x0216E1C0`, `0x0216F398` | **ov6 `BattleObjShot.cpp`** | `[0x0216A7BC, 0x021702BC)` | `0x5B00` loose |

`BattleObj.cpp`'s named function is `Battle_ObjManCreate` at `0x02083204` — "battle object **manager**
create." That matches claim 1 exactly: a generic fixed-capacity pooled-entity constructor, not
projectile-specific.

Three layers, confirmed by source layout:

1. **arm9 `BattleObj.cpp`** — generic object pool. Construct (`0x020834D4`) and destroy
   (`0x02083648`), managed by `Battle_ObjManCreate`. Claim 2's destructor has 30 call sites across arm9
   and ov6 because it is shared infrastructure.
2. **ov6 `BattleObjCtrl.cpp`** — object control. Spawn and ownership (`0x02168CF4`).
3. **ov6 `BattleObjShot.cpp`** — projectile ("shot") specialisation. Claim 5's entire sibling family
   lives here.

### Why claim 5 stays PLAUSIBLE

Iteration 41 declined to promote claim 5 because neighbourhood is not containment. Now measured: the
interval holding all three sibling routines is **`0x5B00` bytes wide** — easily large enough to hide an
unnamed translation unit. "All three are projectile code" stays at **PLAUSIBLE**, now backed by a
number instead of just a principle.

## Predictions status

| Claim | Verdict |
|---|---|
| Re-attributing the map's 194 addresses is cheap and broadly informative | **REFUTED** — only 43/194 (22%) trustworthy |
| Module boundaries can be derived by pairing name and `.cpp` literals per function | **CONFIRMED_STATIC** — all 25 ov6 named functions resolve to a `.cpp` |
| My attribution respected shared overlay load addresses | **REFUTED** — 10 overlays share `0x0214CD20`; first run was nonsense |
| Claims 1 and 2 live in arm9 `BattleObj.cpp`, a generic object pool | **PLAUSIBLE (strong)** — `0xDC8` range, named `Battle_ObjManCreate` |
| Claim 4 (spawn) and claim 5 (despawn) are in different modules | **PLAUSIBLE** — `BattleObjCtrl.cpp` vs `BattleObjShot.cpp` |
| The core HP-apply `0x02078488` is in `ComicDeck.cpp` | **not claimed** — `0x2D18`-wide range, meaningless |
| Claim 5 can be promoted above PLAUSIBLE by module attribution | **REFUTED** — containing interval is `0x5B00` wide |

## Next angles, ranked

1. **Densify the module map with a second marker source.** Asserts aren't the only compiled-in strings;
   file-path literals (`chr/col/`, `bin/state.bin`) and format strings also sit inside the functions
   that use them. More markers = narrower gaps, converting LOOSE attributions to TIGHT. Direct fix for
   the 134 failures.
2. **Enumerate the generic entity API inside `BattleObj.cpp`'s tight bound.** `[0x02083204,
   0x02083FCC)` is only `0xDC8` bytes — holds the construct/destroy pair plus whatever else. Small
   enough to read end to end.
3. Still open: what indexes the 68-entry table at `0x02171FEC`, what reads slot`+0x02`, and the 24
   positive `ProjectileId` values.
