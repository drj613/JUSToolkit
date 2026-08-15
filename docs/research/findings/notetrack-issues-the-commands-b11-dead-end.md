# Findings: NoteTrack owns the character command callback — and commands 23/24 are never issued

Loop-Atlas iteration 47. Static.

Iteration 46 reframed B11 ("who computes the HP delta") as: find a caller passing `r2 = 23` to the
73-case dispatcher. This wake traced the dispatcher's full ownership chain and enumerated every command
issued through it.

**No caller passes 23 or 24.** The dispatcher lives only at `noteTrack+0x70`, and every command issued
through it is in **{3, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73}**. The HP/SP cases are unreachable in
this build.

The real payoff is the chain itself: it connects three separate findings — the 73-case dispatcher, the
`char+0x1a8` pending-delta base, and iteration 40's 16-byte "slot" records — into one subsystem.

---

## 1. The ownership chain

```
Battle_CharaCreate (0x02156A38)
  0x02156CCC  ldr r6, [r4, #0x1a8]     ; character+0x1a8  (the known pending-delta base)
  0x02156CD0  ldr r3, [pc, #0x98]      ; r3 = 0x02157A44  (the 73-case dispatcher)
  0x02156CD4  str r4, [sp]             ; 5th arg = the character
  0x02156CD8  ldr r1, [r6, #8]
  0x02156CDC  add r0, r6, #0x18        ; construct into [char+0x1a8]+0x18
  0x02156CE0  mov r2, r6
  0x02156CE4  bl  #0x21553e0           ; Battle_NoteTrackCreate

Battle_NoteTrackCreate (0x021553E0)
  0x021553F4  mov r6, r3               ; the callback
  0x02155400  mov r0, #0xa8            ; allocate 0xA8 bytes
  0x02155408  bl  #0x201a21c
  0x02155418  bl  #0x20517fc           ; memset 0xA8 to 0
  0x0215541C  str r8, [r4, #0x88]
  0x02155424  str r0, [r4, #0x98]      ; = -1
  0x02155428  str r0, [r4, #0x94]      ; = -1
  0x0215542C  strb r0, [r4, #0xa3]     ; = -1
  0x02155430  str r7, [r4, #0x7c]
  0x02155438  str r6, [r4, #0x70]      ; <-- the dispatcher lands at noteTrack+0x70
```

The **NoteTrack object is `0xA8` bytes**, constructed at `[character+0x1a8]+0x18`, with the command
dispatcher at `+0x70`.

The dispatcher is `0x02157A44` (prologue `push {r3,r4,r5,r6,lr}`), signature
`(r0, r1, r2 = command, r3, +2 stack args)`. **Zero real callers**: `find_callers.py` reported one in
ov4, but ov4 and ov6 share load address `0x0214CD20` — the exact phantom case the tool warns about.
One word reference in the ROM (`0x02156D70`), so `noteTrack+0x70` is its only home.

### This ties three findings together

- `character+0x1a8` was already the pending-delta base (`+0x134` HP damage, `+0x138` SP drain,
  `+0x140` HP heal, `+0x144` SP add, off `[char+0x1A8]→+0x10`). It also holds the NoteTrack at `+0x18`.
  Two subsystems, one container.
- Iteration 40's collision stub bank sits in `BattleNoteTrack.cpp` — it *is* NoteTrack code. Its
  17 spawn "kinds" are note kinds.
- Iteration 40's 16-byte slot records (`+0x00` kind, `+0x01` ExtFlags, `+0x02` ProjectileId) are the
  notes. The forwarder below reads `+0x01`, `+0x02` and a counter at `+0x04`.

A NoteTrack is a timeline of scheduled events — a move script. The dispatcher is how a note affects its
character.

## 2. Every command issued through the callback

Scanned ov6 for `ldr Rd,[Rn,#0x70]` followed by `blx`/`bx Rd`, with the `r2` immediate in between:

| site | command | site | command |
|---|---|---|---|
| `0x021554EC` | 3 | `0x0215605C` | 72 |
| `0x02155E3C` | 65 | `0x02156130` | 69 |
| `0x02155E9C` | 66 | `0x02156420` | 71 |
| `0x02155F10` | 66 | `0x021564BC` | 70 |
| `0x02155F4C` | 73 | `0x02156584` | **64** (tail-call stub) |
| `0x02155FC0` | 73 | `0x02156594` | **68** (tail-call stub) |
| `0x02155FFC` | 67 | | |

The two stubs tail-call a **generic forwarder** at `0x02156520`, which never sets `r2` — it passes its
own third argument through:

```
0x02156520  push {r3, r4, lr}
0x02156528  mov r4, r1              ; r1 = the note record
0x0215652C  ldrh r1, [r4, #4]
0x02156530  sub r1, r1, #1
0x02156534  strh r1, [r4, #4]       ; tick the note's counter down
0x02156538  ldr ip, [r0, #0x70]     ; the callback
0x02156560  ldr r1, [r0, #0x74]
0x02156564  blx ip                  ; r2 forwarded from this function's caller
0x0215656C  ldrbne r1, [r4, #2]     ; ProjectileId
0x02156578  strbne r1, [r4, #1]     ; -> ExtFlags, if the command returned non-zero
```

Only the two stubs call it, passing 64 and 68. Full issued set:
**{3, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73}** — command 3 plus a contiguous 64–73 band.

### Cross-check against the dispatcher's own case map

| command | dispatcher case status |
|---|---|
| 3, 65, 66, 67, 69, 71, 72 | **LIVE** |
| 64, 68, 70 | **NO-OP case** |
| 73 | **out of range** (`cmp r2,#72` → default branch) |

The issuer sends commands the handler ignores — normal for a polymorphic callback. This explains the
upper edge of the `34-64` no-op band left open by iteration 46.

## 3. B11: a dead end, stated plainly

**Commands 23 and 24 are never issued with an immediate anywhere in ov6.** The dispatcher lives only at
`noteTrack+0x70` and every `blx` through that field is enumerated above, so cases 1–33 (except 3) are
unreachable in this build.

**Why PLAUSIBLE, not confirmed.** Four sites do `ldr r1,[r1,#0x70]` then `blx r1`, forwarding a variable
`r2`: `0x0215F1C4`, `0x0215F318`, `0x02168FEC`, `0x0216FF6C`. Their base objects are unknown — they could
be `+0x70` callbacks on different types entirely. They can't be ruled out as issuers of 23/24.

Iteration 46's reframing was architecturally right but operationally a dead end: the HP-apply cases exist
in the handler, but nothing reaches them. The 8 ARM script-effect callers of `0x020783CC` remain the real
HP-delta path; case 23 is a second, unused entry point to the same function.

### Scan-hygiene note

The widened scan returned 36 `ldr Rd,[Rn,#0x70]` sites, but **14 have `Rn = r15`** — pc-relative literal
loads, not field reads. Same base-register filtering discipline as iteration 45. Only 12 sites in the
NoteTrack address range are genuine callback invocations.

## Predictions status

| Claim | Verdict |
|---|---|
| `Battle_CharaCreate` passes the 73-case dispatcher to `Battle_NoteTrackCreate` as `r3` | **CONFIRMED_STATIC** — `0x02156CD0`, `0x02156CE4` |
| The callback is stored at `noteTrack+0x70` | **CONFIRMED_STATIC** — `str r6,[r4,#0x70]` at `0x02155438` |
| The NoteTrack object is `0xA8` bytes, built at `[char+0x1a8]+0x18` | **CONFIRMED_STATIC** — `mov r0,#0xa8`; `add r0,r6,#0x18` |
| The dispatcher has any real direct caller | **REFUTED** — the single ov4 hit is a shared-load-address phantom |
| The dispatcher is installed anywhere other than `noteTrack+0x70` | **REFUTED** — exactly one word reference, `0x02156D70` |
| NoteTrack issues commands {3, 64–73} | **CONFIRMED_STATIC** — 12 enumerated call sites |
| `0x02156520` is a generic forwarder passing its caller's `r2` | **CONFIRMED_STATIC** — no `mov r2` in the function |
| Iteration 40's 16-byte slot records are NoteTrack notes | **PLAUSIBLE (strong)** — the forwarder reads `+0x01`, `+0x02`, `+0x04` |
| Some caller passes `r2 = 23` (the B11 plan) | **REFUTED** — no immediate 23 or 24 anywhere in ov6 |
| Dispatcher cases 1–33 (except 3) are unreachable in this build | **PLAUSIBLE** — 4 variable-`r2` sites on unidentified base types remain |

## Next angles, ranked

1. **Identify the base objects of the four variable-`r2` sites** (`0x0215F1C4`, `0x0215F318`,
   `0x02168FEC`, `0x0216FF6C`). Only way cases 1–33 could be reached — either closes the "unreachable"
   question or reopens B11.
2. **Map the NoteTrack `0xA8` layout.** Known fields: `+0x70` (callback), `+0x74`, `+0x7c`, `+0x88`,
   `+0x94`/`+0x98`/`+0xa3` (all init `-1`). This is the move-script engine; several open subsystems need it.
3. **Name commands 64–73** by reading the seven live cases. These describe what a move script can do to
   a character.
4. Still open: `prmData+0x0C/+0x10/+0x14`, the 68-entry table at `0x02171FEC`, the 24 positive
   `ProjectileId` values, the `34-63` no-op band, and the harness watchpoint recipe for the collision walker.
