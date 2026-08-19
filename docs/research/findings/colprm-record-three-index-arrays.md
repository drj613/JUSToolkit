# Findings: `+0x90`–`+0x9B` is three parallel `int16[2]` arrays, all set to `-1`

Loop-Atlas iteration 79. Static.

Iteration 78 flagged `record+0x90` and `+0x94` as address-taken sub-structures. They
aren't. They are **three parallel two-element `int16` arrays**, all set to `-1` by one
small loop.

No readers were found because of a blind spot in every scanner: **post-indexed
addressing**. `strh r2,[r5],#2` carries no offset for an offset scan to match (§3).

---

## 1. One loop, three arrays

```
0x0207CAA8  add r0, r4, #0x90      ; r0 -> array A
0x0207CAFC  add r5, r4, #0x94      ; r5 -> array B
0x0207CB00  add r6, r4, #0x98      ; r6 -> array C
0x0207CB04  mvn r3, #0             ; r3 = -1
0x0207CB08  strh r3, [r6]          ; C[i] = -1
0x0207CB0C  ldrsh r2, [r6], #2     ; r2 = C[i]; r6 += 2
0x0207CB10  add r1, r1, #1
0x0207CB14  cmp r1, #2
0x0207CB18  strh r2, [r5], #2      ; B[i] = r2; r5 += 2
0x0207CB1C  strh r2, [r0], #2      ; A[i] = r2; r0 += 2
0x0207CB20  blt #0x207cb08
```

`r1` is `0` on entry — it's the `val` argument left over from `memset(record+0xA4,
0, 0xD0)` at `0x0207CA80`, and the two `strb r1,…` at `0x0207CA88`/`0x0207CA90` depend
on that. `cmp r1,#2` after the increment gives exactly **two iterations**.

Three bases, two `int16` each, `-1` everywhere:

| field | array |
|---|---|
| `+0x90`, `+0x92` | A |
| `+0x94`, `+0x96` | B |
| `+0x98`, `+0x9A` | C |

Twelve contiguous bytes, no gap. `-1` is this codebase's "unset index" convention — same
pattern as NoteTrack `+0x94`/`+0x98` and prmData `+0x18`/`+0x1C`/`+0x1E`.

Iteration 78's guard 9 read `+0x98`/`+0x9A` correctly but called `+0x90` and `+0x94`
plain address-taken fields — it only looks for `[rD,#imm]` and these use post-indexing.
Right offsets, wrong interpretation.

## 2. No reader could be attributed

Every halfword access at `+0x90`–`+0x9A` in arm9 (six sites) and ov6 (one):

| site | access | function | record companions |
|---|---|---|---|
| `0x0205561C` | `ldrh r4,[r1,#0x94]` | `0x02055588` | none |
| `0x02055644` | `ldrh r1,[r1,#0x98]` | `0x02055588` | none |
| `0x0207AE74` | `strh r0,[r4,#0x90]` | `0x0207AD3C` `Battle_ColManCreate` | none |
| `0x0207B43C` | `strh r0,[sl,#0x90]` | `0x0207B414` | none |
| `0x0207B77C` | `ldrh r2,[sl,#0x90]` | `0x0207B414` | none |
| `0x0207B7A4` | `strh r0,[sl,#0x90]` | `0x0207B414` | none |
| `0x021699A0` | `ldrsh r0,[r0,#0x90]` | `0x02169718` | `+0x5c` only |

None shares a distinctive record field with its base. The two `BattleCol.cpp` sites are
the strongest rule-out: `Battle_ColManCreate` is 332 bytes, `0x0207B414` is 988, and
across all 1320 bytes neither touches any of the record's twelve signature offsets. They
are the **ColMan** — a different struct reusing `+0x90`, the fourth coincidental-offset
collision in this subsystem.

## 3. The blind spot: post-indexed addressing

`strh r2,[r5],#2` and `ldrsh r2,[r6],#2` carry no offset immediate. Every scanner in this
campaign — `struct_fields.py`, `find_field_writers.py`, the inline sweeps — requires
`[base, #imm]` and silently skips these.

| form | arm9 | ov6 |
|---|---|---|
| post-indexed `[reg], #imm` | **331** | **8** |
| pre-indexed with writeback `[reg, #imm]!` | 35 | 0 |
| bare `[reg]` (offset 0 only) | 7007 | 1492 |

ov6's **8** is the key number: if readers walk these arrays with post-indexed addressing,
they're almost certainly in arm9. That fits the writer being arm9's installer and points
to collision-side bookkeeping rather than anything the ov6 damage path touches.

## Predictions status

| Claim | Verdict |
|---|---|
| `+0x90`, `+0x94`, `+0x98` are three parallel `int16[2]` arrays | **CONFIRMED_STATIC** — three post-indexed `strh …,#2` in one 2-iteration loop, `0x0207CB08`–`0x0207CB20` |
| All six entries are initialised to `-1` | **CONFIRMED_STATIC** — `mvn r3,#0` at `0x0207CB04`, propagated through `r2` |
| The loop runs exactly twice | **CONFIRMED_STATIC** — `r1 = 0` from the memset call, `cmp r1,#2` after increment |
| `+0x90`–`+0x9B` is fully accounted for, 12 contiguous bytes | **CONFIRMED_STATIC** — 3 × 2 × `int16`, no gap |
| `+0x90` and `+0x94` are sub-structures | **REFUTED** *(iteration 78's guess)* — they are array bases, not struct pointers |
| The `BattleCol.cpp` `+0x90` sites act on this record | **REFUTED** — 1320 bytes of code, zero record companion offsets; they are the ColMan's |
| A reader of these arrays was identified | **REFUTED** — 7 candidate sites, none attributable |
| The readers are in arm9 rather than ov6 | **PLAUSIBLE** — ov6 has only 8 post-indexed accesses ROM-wide |
| The arrays hold indices ("unset" = `-1`) | **PLAUSIBLE** — matches the convention on NoteTrack and prmData, but no consumer found |

## Next angles, ranked

1. **Teach the scanners post-indexed and pre-indexed-writeback forms.** 331 arm9 sites
   are invisible today, and this case shows they're exactly where array walks live.
   Bounded change to `struct_fields.py`; the selftest already has anchors for it.
2. **Resolve `record+0x68`** (carried) — the object whose `+0x20` list holds this
   record's bucket nodes.
3. **Re-run the record map with anchors from the eight per-frame collision stages**
   (carried) — most likely to touch the unmapped spans.
4. **Re-audit the map's `char+0xNN` offsets** across the three objects (carried).
