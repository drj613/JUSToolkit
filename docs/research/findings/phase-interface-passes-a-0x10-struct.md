# Findings: the phase interface's common currency is a `0x10` four-word struct

Loop-Atlas iteration 126. Static.

Read `0x0207DF60` through `0x0207E018` — the last uncatalogued stretch of phase-table targets. Three
results, one of which corrects last wake.

1. **CORRECTION to iteration 125.** I read the dispatcher's branch list positionally and got the case
   mapping wrong. `addls pc, pc, r2, lsl #2` resolves against **`pc + 8`**, not the next instruction.
2. The region holds **six more functions**, three of them absent from `functions.json` and one *inside*
   a detected record — the same merge/miss hazard iteration 125 found, now confirmed as systematic.
3. Three separate slots handle a **`0x10`-byte, four-word output struct**. That is the interface's shared
   data shape.

---

## 1. The dispatcher, mapped correctly

```
0x0207DF60  cmp r2, #6
0x0207DF64  addls pc, pc, r2, lsl #2     ; pc here = 0x0207DF64 + 8 = 0x0207DF6C
0x0207DF68  b #0x207dfb8                 ; <- DEFAULT (r2 > 6 falls through to this)
0x0207DF6C  b #0x207df88                 ; <- r2 = 0
0x0207DF70  b #0x207df9c                 ;    r2 = 1
0x0207DF74  b #0x207df9c                 ;    r2 = 2
0x0207DF78  b #0x207df9c                 ;    r2 = 3
0x0207DF7C  b #0x207df9c                 ;    r2 = 4
0x0207DF80  b #0x207dfa4                 ;    r2 = 5
0x0207DF84  b #0x207df9c                 ;    r2 = 6
```

The table **starts one word after** the `addls`, so the branch immediately following it is the
out-of-range default, and every case index shifts by one.

| `r2` | target | behaviour |
|---|---|---|
| default (`> 6`) | `0x0207DFB8` | `mov r0,#0; bx lr` |
| `0` | `0x0207DF88` | `1` if `r1` ∈ {`1`,`2`}, else `0` |
| `1`, `2`, `3`, `4`, `6` | `0x0207DF9C` | `mov r0,#0; bx lr` |
| `5` | `0x0207DFA4` | `0` if `r1` ∈ {`1`,`2`}, else `1` |

Iteration 125 said "cases 2, 3, 4 and 5 all branch to one target". Wrong on both counts: it is
cases **1, 2, 3, 4 and 6** that share `0x0207DF9C`, case `5` has its own body, and the default arm
`0x0207DFB8` is a *separate* byte-identical copy of "return 0".

The two real arms are exact complements:

```
0x0207DF88  sub r0, r1, #1 ; cmp r0, #1 ; movls r0, #1 ; movhi r0, #0   ; r1 in {1,2} -> 1
0x0207DFA4  sub r0, r1, #1 ; cmp r0, #1 ; movhi r0, #1 ; movls r0, #0   ; r1 in {1,2} -> 0
```

**Cross-check with iteration 125:** the rect getter switches on `r1` = `0`–`3`, and its cases **1 and 2
are the left and right wall regions**. These predicates test exactly "is `r1` one of 1 or 2" — i.e.
*is this a wall region*. Two functions, reached independently, agreeing on what `1` and `2` mean.

## 2. Six more functions, three of them unlisted

| start | end | in `functions.json`? | body |
|---|---|---|---|
| `0x0207DF60` | `0x0207DFBC` | **no** | the dispatcher above |
| `0x0207DFC0` | `0x0207DFC4` | **no** | `mov r0,#4; bx lr` |
| `0x0207DFC8` | `0x0207DFD4` | **no** | `1` if `r1` == `0`, else `0` |
| `0x0207DFD8` | `0x0207DFF0` | yes, `size=28` — exact | `memset(r3, 0, 0x10)`, return `0` |
| `0x0207DFF4` | `0x0207E00C` | yes, `size=36` | `memset(r2, 0, 0x10)`, return `0` |
| `0x0207E010` | `0x0207E014` | **inside** the above | `mov r0,#0; bx lr` |

`0x0207DFF4 + 36 = 0x0207E018`, so that one 36-byte record covers **two** functions — the same failure
shape as iteration 125's 540-byte record covering eight, at a size small enough that nothing looked wrong.

## 3. The `0x10` struct

```
0x0207DFD8  push {r3, lr} ; mov r0, r3 ; mov r1, #0 ; mov r2, #0x10 ; bl memset ; mov r0, #0
0x0207DFF4  push {r3, lr} ; mov r0, r2 ; mov r1, #0 ; mov r2, #0x10 ; bl memset ; mov r0, #0
```

Two near-identical stubs that differ **only in which argument register holds the out pointer** — `r3` in
one, `r2` in the other. Both zero `0x10` bytes and return `0`.

`0x10` is four words, the exact size iteration 125's rect getter fills at `r2`
(`[r2]`, `+0x4`, `+0x8`, `+0xC`). So three slots of this interface traffic in one **four-word struct**:
one fills it with a wall region, two clear it and report nothing.

The out pointer is **not at a fixed argument position** across slots — `r2` for the rect getter and
`0x0207DFF4`, `r3` for `0x0207DFD8`. Recorded as observed. It means these are not one virtual method with
one signature; the table mixes slots with different argument layouts.

## Predictions status

| Claim | Verdict |
|---|---|
| Iteration 125's case mapping (`2,3,4,5` share a target) | **REFUTED** *(my own)* — `1,2,3,4,6` share it; `pc+8` shifts every index |
| The default arm is a distinct body from the shared case arm | **CONFIRMED_STATIC** — `0x0207DFB8` and `0x0207DF9C`, byte-identical, both present |
| Cases `0` and `5` are complementary predicates | **CONFIRMED_STATIC** — `movls`/`movhi` swapped, same `sub`/`cmp` |
| `r1` ∈ {`1`,`2`} means "a wall region" | **PLAUSIBLE** — matches the rect getter's wall cases `1` and `2`; the correspondence is by index, not proven |
| `0x0207DFF4 size=36` is one function | **REFUTED** — it covers `0x0207DFF4` and `0x0207E010` |
| Three of the six functions here are missing from `functions.json` | **CONFIRMED_STATIC** — `func` returns no record for `0x0207DF60`, `0x0207DFC0`, `0x0207DFC8`. `0x0207DFD8` **is** listed at `size=28`, exactly right — so the detector is inconsistent here, not uniformly blind |
| The interface passes a `0x10`-byte four-word struct | **CONFIRMED_STATIC** — `mov r2,#0x10` twice, plus four word stores in the rect getter |
| The out pointer is at a fixed argument position | **REFUTED** — `r2` in two slots, `r3` in a third |
| `0x0207DFC0` returns a meaningful constant `4` | **SPECULATIVE** — the instruction is certain, what `4` denotes is not |

## Next angles, ranked

1. **Name the four words of the `0x10` struct.** Iteration 125 fixed `+0x8`/`+0xC` as a signed extent;
   `[r2]`/`+0x4` are an origin. A consumer that reads it would confirm the field roles.
2. **Read `0x0206CF28`** (carried) — the callee both wall arms consult with opposite conditions.
3. **Re-run function detection over `0x0207D9A4`–`0x0207E018`** and record the true boundaries, now that
   two records are known to be merged. This whole module's sizes are untrustworthy.
4. **Name `B+0x78`'s other bits** (carried) — two of 32 known.
