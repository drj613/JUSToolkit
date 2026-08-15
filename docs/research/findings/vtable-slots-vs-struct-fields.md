# Findings: the four remaining suspects are vtable calls — dispatcher cases 1–33 are dead

Loop-Atlas iteration 48. Static.

Iteration 47 said cases 1–33 (except 3) of the 73-case dispatcher are never invoked, but left the
verdict at **PLAUSIBLE** — four sites did `ldr r1,[r1,#0x70]` then `blx r1` with a variable `r2` and
unknown base objects.

**All four are C++ virtual calls at vtable slot `0x70`, not NoteTrack field reads.** Ruling them out
upgrades the conclusion to CONFIRMED_STATIC.

The broader takeaway: **an offset can be a struct field or a vtable slot — they look identical unless
you count dereferences.** ov6 makes 384 virtual calls across 33 distinct vtable slots, so this matters.

---

## 1. The four sites are virtual calls

All four share one idiom, three instructions long:

```
0x0215F1C0  ldr r1, [r0]          ; r1 = *object = the vtable pointer
0x0215F1C4  ldr r1, [r1, #0x70]   ; r1 = vtable[0x70] = a virtual method
0x0215F1C8  blx r1
```

Mechanical check: does a `ldr Rn,[Rm,#0]` feed the same register on the preceding line?

| site | preceding instruction | verdict |
|---|---|---|
| `0x0215F1C4` | `ldr r1,[r0,#0x0]` | **VTABLE LOAD** |
| `0x0215F318` | `ldr r1,[r0,#0x0]` | **VTABLE LOAD** |
| `0x02168FEC` | `ldr r1,[r0,#0x0]` | **VTABLE LOAD** |
| `0x0216FF6C` | `ldr r1,[r0,#0x0]` | **VTABLE LOAD** |

All four reach their object via `ldr r0,[X,#0x68]`, and nearby code hits other slots on the same object —
`ldr r1,[r1,#0x6c]` at `0x0215F2FC`, `ldr r2,[r2,#0xd8]` at `0x0216FF50`. Multiple slots on one object
through double indirection is a vtable, not a struct full of function pointers.

The **12 genuine NoteTrack callback sites have zero vtable loads before them** — each is a
single-dereference field read off the NoteTrack instance (`ldr ip,[r5,#0x70]`). The two groups separate
cleanly, no ambiguous cases.

## 2. Consequence: cases 1–33 (except 3) are unreachable

The dispatcher `0x02157A44` has one word reference in ROM (`0x02156D70`) and lives only at
`noteTrack+0x70`. All single-dereference reads of that field followed by an indirect call are enumerated —
12 sites, issuing commands **{3, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73}**. The four remaining candidates
are now excluded as virtual calls on unrelated objects.

Nothing invokes commands 1–33 apart from 3. **Cases 23 and 24 — calling the HP-apply trampoline
`0x020783CC` and the SP apply `0x020781E4` — are dead code in this build.** They are a second entry point
to functions already reached by the 8 ARM script-effect callers.

Caveat: this is static reachability. No *code* stores or issues those commands. A runtime-copied pointer
would not show up, though the single word reference makes that unlikely.

## 3. ov6 is heavily virtual, which explains a lot

Full idiom count (`ldr Rx,[Ry,#0]`; `ldr Rx,[Rx,#slot]`; `blx Rx`) across ov6:

**384 virtual calls across 33 distinct vtable slots.**

Most-used slots: `0xD8` (80 calls), `0x8` (45), `0x6C` (39), `0xC` (22), `0x24` (21), `0x94` (21), `0xEC`
(18), `0x14` (15), `0xA0` (14), `0x5C` (14). Slot `0x70` is used exactly 4 times — the four sites above.

Third independent confirmation that static pattern-matching cannot span this engine's access paths. The
list: dispatch tables (15 in ov6), function-pointer tables (the 68-entry one at `0x02171FEC`), instance
callbacks (`noteTrack+0x70`), and 384 virtual calls.

### The rule for future scans

Before treating an `ldr Rd,[Rn,#off]` hit as a struct-field read, check whether `Rn` was just loaded from
`[Rm,#0]`. If so, `off` is a **vtable slot index** and the object type is whatever `Rm` is — a
different fact entirely.

Fourth member of the same family of scan errors, and the cheapest to guard against:

| iteration | error | guard |
|---|---|---|
| earlier | offset-only scans returning hundreds of hits | constrain enough to read every hit |
| 44 | chain scan walked over `bx lr` | stop at function boundaries |
| 45 | offset matched without knowing the base type | trace where the base register came from |
| 47 | `Rn = r15` hits were pc-relative literal loads | exclude `r15` bases |
| **48** | **vtable slot read as a struct field** | **check for a preceding `ldr Rn,[Rm,#0]`** |

## Predictions status

| Claim | Verdict |
|---|---|
| The 4 variable-`r2` sites are `+0x70` field reads on unknown objects | **REFUTED** — all 4 are vtable loads |
| They are virtual calls at vtable slot `0x70` | **CONFIRMED_STATIC** — each preceded by `ldr r1,[r0,#0x0]` |
| The 12 NoteTrack sites are direct field reads | **CONFIRMED_STATIC** — 0 of 12 preceded by a vtable load |
| Dispatcher cases 1–33 except 3 are unreachable | **CONFIRMED_STATIC** *(was PLAUSIBLE)* — all candidate issuers now excluded |
| Cases 23/24 are a dead second entry point to `0x020783CC`/`0x020781E4` | **CONFIRMED_STATIC** |
| ov6 uses 384 virtual calls across 33 vtable slots | **CONFIRMED_STATIC** |

## Next angles, ranked

1. **Map the NoteTrack `0xA8` struct** — the move-script engine; several open questions route through it.
   Known: `+0x70` callback, `+0x74`, `+0x7c`, `+0x88`, `+0x94`/`+0x98`/`+0xa3` (init `-1`).
2. **Name commands 64–73** by reading the seven live cases. These are the commands actually issued —
   they define what a move script can do to a character.
3. **Identify the object at `[X,#0x68]`** with the 33-slot vtable. 384 calls in ov6 — naming it would
   label a large chunk of code at once.
4. Still open: `prmData+0x0C/+0x10/+0x14`, the 68-entry table at `0x02171FEC`, the 24 positive
   `ProjectileId` values, the `34-63` no-op band, and the harness watchpoint recipe for the collision walker.
