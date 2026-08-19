# Findings: the NoteTrack commands are predicates, not actions

Loop-Atlas iteration 50. Static.

The seven live dispatcher cases in the 64–73 band are all predicates. Each returns a boolean: `mov r0,#1` then branch to `0x02157F94`, or fall through to `0x02157F90` which does `mov r0,#0`. None mutates the character.

This reframes the subsystem. Combined with iteration 47's forwarder (`cmp r0,#0; ldrbne r1,[note+2]; strbne r1,[note+1]`): **a NoteTrack asks the character "is condition N true?" and advances the note only if yes.** The dispatcher is a query interface. The name "command" from iterations 46–49 was wrong.

Also corrected: the dispatcher's argument registers and two NoteTrack fields iteration 49 missed.

---

## 1. The signature

```
0x02157A44  push {r3,r4,r5,r6,lr}
0x02157A48  sub  sp, sp, #0xc
0x02157A4C  mov  r4, r3            ; r4 = arg3 (the query parameter)
0x02157A50  ldr  r3, [sp, #0x20]
0x02157A54  ldr  r6, [sp, #0x24]
0x02157A58  mov  r5, r1            ; r5 = arg1
0x02157A5C  cmp  r2, #72           ; r2 = the query number
```

`r0` is never written, so `r0 = arg0`. Call sites confirm arg0 and arg1: at `0x02156538` the callback loads via `ldr ip,[r0,#0x70]`, and at `0x02156560` `r1` loads from `[r0,#0x74]` — the character (per iteration 49).

**`query(r0 = NoteTrack, r1 = character, r2 = query number, r3 = parameter, +2 stack args) -> bool`**

The case bodies confirm this: `r5` reads character fields (`+0x1A8` ×4, `+0x1B4` ×6, `+0x1B8` ×2, `+0x88`, `+0xCA`, `+0x1A0`) and `r4` appears only in comparisons as a threshold or index.

## 2. The seven live queries

| # | address | what it tests |
|---|---|---|
| 3 | `0x02157BE4` | **Not a predicate.** `bl 0x0215857C` then straight to the zero-return epilogue — a fire-and-forget action whose result is discarded. The only low-band number issued. |
| 65 | `0x02157E50` | `ldr r0,[NoteTrack+0x7C]`, `bl 0x0215793C`, boolean on the result. A query about the `+0x7C` object. |
| 66 | `0x02157E68` | `[char+0x1B4] + 0x500`, `ldrsb +0xDF`, `cmp r0,r4`, `blt` fail. **Threshold test**: returns true when a signed byte is `>=` the parameter. |
| 67 | `0x02157E84` | `[NoteTrack+0x80]`, null-check, `ldrh +0x26`, `tst #0x80`. **Flag-bit test** (bit 7 of a halfword). |
| 69 | `0x02157F30` | Table via `ldr r0,[pc,#0x74]`, `ldrsb r0,[r0,r4]`, compared as `u16` against `ldrh [char+0x88]`. **Table-lookup equality**: is the character's `+0x88` equal to `table[parameter]`? |
| 71 | `0x02157EC4` | Loop `ip` from 0 to `[global+0x158]`, skipping `ip == [char+0x100+0xE0]` (self), addressing `lr + slot*0xC0 + ip*0x30`, returns true if `[+0x158]` or `[+0x170]` is non-zero. **"Is any *other* entity in state X?"** — a 2D array walk, outer stride `0xC0`, inner `0x30`. |
| 72 | `0x02157F50` | `[NoteTrack+0x84]`, null-check, `bl 0x02158000`, then `[+0x10]` and `[+0x28]`. Boolean chain through the `+0x84` object. |

Query 71 is the most informative: its "skip myself, check everyone else" loop means move scripts gate on *other* characters' states. The `0xC0`/`0x30` strides describe an entity table nothing in this campaign has mapped.

## 3. Two NoteTrack fields iteration 49 missed, and why

The dispatcher reads four offsets from `r0` before reassigning it, all inside the `0xA8` allocation:

| offset | queries | status |
|---|---|---|
| `+0x7C` | 65 | in the iteration-49 map |
| `+0x80` | 67 | **new** |
| `+0x84` | 25, 26, 33, 72 | **new** |
| `+0x88` | 4, 5 | in the iteration-49 map |

Four consecutive pointer fields at `+0x7C`–`+0x88`. Iteration 49 missed the middle two because it only searched the 12 callback sites in `BattleNoteTrack.cpp`; the dispatcher lives in `BattleChara.cpp` and also takes a NoteTrack. **Anchoring on one module misses fields used across modules.**

### This settles iteration 45

Iteration 45 refuted the claim that the `+0x84` reads at `0x02157DD8`, `0x02157DF0`, `0x02157E14` and `0x02157F50` were `character+0x84` (i.e. `prmData`), because their callees index `+0x2c` and `+0x4c`, past `prmData`'s `0x20` bytes. That refutation was correct. The answer: they are **`NoteTrack+0x84`** — a different object, pointing to something with fields at `+0x1a`, `+0x2c` and `+0x4c`.

## 4. I repeated my own mistake from the previous wake

My first pass at §3 reported `+0xDF`, `+0xE0` and `+0x158` as NoteTrack fields. All three exceed `0xA8` — that's how I caught it. Cause: no reassignment tracking. Query 66 does `ldr r0,[r5,#0x1b4]` before reading `+0xDF`, so that read is off a different object.

**Iteration 49 found this exact defect and added the guard. One wake later I wrote a new scan without it.** The lesson isn't the rule (already recorded) but that recording a rule doesn't apply it. The guard belongs in a reusable tool, not a note. Six scan errors in this family now.

## Predictions status

| Claim | Verdict |
|---|---|
| Commands 64–73 mutate the character | **REFUTED** — all seven live cases return a boolean and mutate nothing |
| They are predicates gating a note's state transition | **CONFIRMED_STATIC** — boolean returns + the forwarder's `cmp r0,#0` |
| Signature is `(NoteTrack, character, query, parameter, …)` | **CONFIRMED_STATIC** — prologue plus `ldr r1,[r0,#0x74]` at the call site |
| Query 3 is a predicate | **REFUTED** — fire-and-forget action, result discarded |
| Query 66 is a `>=` threshold test on a signed byte | **CONFIRMED_STATIC** — `ldrsb`, `cmp r0,r4`, `blt` fail |
| Query 71 iterates other entities, skipping self | **CONFIRMED_STATIC** — `cmp ip,r4` skip; strides `0xC0`/`0x30` |
| `NoteTrack+0x80` and `+0x84` are fields | **CONFIRMED_STATIC** — read off arg0 before reassignment |
| The `+0x84` reads are `character+0x84` / `prmData` | **REFUTED** *(iteration 45, now explained)* — they are `NoteTrack+0x84` |
| My first §3 scan (`+0xDF`, `+0xE0`, `+0x158`) | **REFUTED** — no reassignment tracking; all exceed `0xA8` |

## Next angles, ranked

1. **Build the reassignment-tracking check into a tool.** Six scan errors in this family; this one has recurred twice in a row.
2. **Map the entity table behind query 71** — strides `0xC0` and `0x30`, count at `[global+0x158]`, fields `+0x158` and `+0x170`. Unmapped global structure the move-script engine consults.
3. **Identify the `+0x7C`/`+0x80`/`+0x84` objects.** Three pointer fields, each backing a query.
4. Still open: `prmData+0x0C/+0x10/+0x14`, the 68-entry table at `0x02171FEC`, the 24 positive `ProjectileId` values, the `34-63` no-op band, and the harness watchpoint recipe for the collision walker.
