# Findings: `record+0x68` is never set — a second vestigial field on the same struct

Loop-Atlas iteration 84. Static.

Iteration 83 found `record+0x68` cleared at teardown but never written. This wake
enumerated **every write form** in the only code that touches ColPrm records. No setter
exists.

The teardown guards the field with `cmp r2,#0; beq`, so the branch it protects — walking
a partner's `+0x20` list — is **dead in retail**. That makes two vestigial fields on this
struct, after `+0xE8`.

---

## 1. ColPrm-aware code is a narrow band

The manager global `0x0214BE10` is referenced from exactly two places: arm9
`0x0207C83C`–`0x0207D99C`, and ov6 `0x02157EC8`/`0x02157FA8` (the query dispatcher).
Nothing else can reach a record without being handed one.

This keeps the search bounded. A ROM-wide sweep for `+0x68` returns 55 direct stores
and buries the answer.

## 2. Every write form in the band, enumerated

Collision band `0x0207A000`–`0x02084000`, 10240 words:

| form | count | can it reach `+0x68`? |
|---|---|---|
| direct `str …,[base,#0x68]` | **1** | yes — and it writes `0` |
| register-offset `str rD,[rN,rM]` | 4 | no |
| `stm` with a non-`sp` base | 2 | no |
| post-indexed | 2 | no |

Each non-direct case:

```
0x0207A1C8  str  r0, [sl, sb]              ; computed array index, not a fixed field
0x02081048  strbne r3, [r1, r4]            ; byte
0x020812DC  str  r3, [r8, r0, lsl #2]      ; scaled array index
0x02082260  strbne r3, [r1, r6]            ; byte
0x0207F908  strb r1, [r7], #1              ; byte, offset 0
0x020801F8  .word 0x24000100               ; data
0x0207E560  stmne r5, {r0, r1, r2, r3}     ; base+0x0..+0xC
0x0207E574  stm   ip, {r0, r1, r2, r3}     ; base+0x0..+0xC
```

The two `stm` blocks write four words from the base, reaching `+0xC` at most. The
register-offset stores are two byte writes and two scaled array indices. None reaches
`+0x68`. The ov6 dispatcher holds **0** stores to `+0x68`.

The only write to `record+0x68` anywhere is `0x0207CBC8`, and `r5` is `0` there.

## 3. The guarded branch is dead

```
0x0207CCDC  ldr r2, [r4, #0x68]
0x0207CCE4  cmp r2, #0
0x0207CCE8  beq #0x207cd88          ; skip the whole partner walk
0x0207CCEC  ldr r6, [r2, #0x20]
```

`+0x68` is never set, so `r2` is always `0` and the branch always taken. The partner
walk — ~26 instructions that unlink this record's nodes from a partner's `+0x20` list
and return them to `mgr+0xD8` — never runs.

This does *not* affect the rest of the teardown: iteration 83's four list heads are on
the fallthrough path.

## 4. Two vestigial fields, one struct

| field | evidence |
|---|---|
| `+0xE8` | 47 stores ROM-wide, none targeting a record; only ever memset (iterations 76, 81) |
| `+0x68` | 1 store in ColPrm-aware code, and it writes `0` (this wake) |

`+0x140`, a third field, was observed as `0` at a live breakpoint on every hit — already
on record.

Three fields, three independent routes to the same conclusion: **the ColPrm record
carries machinery the retail build does not use.** A record-to-record pairing was
designed, the teardown still checks for it, and nothing ever forms one.

This strengthens the `+0xE8` case by analogy, not proof. `+0x68`'s argument is stronger
because the code that could write it fits in 10240 words and every write form is listed.

## Predictions status

| Claim | Verdict |
|---|---|
| ColPrm-aware code is confined to `0x0207C83C`–`0x0207D99C` plus two ov6 sites | **CONFIRMED_STATIC** — the only references to `0x0214BE10` |
| Exactly one store to `+0x68` exists in the collision band, and it writes `0` | **CONFIRMED_STATIC** — `0x0207CBC8`, `r5 = 0` |
| No register-offset, `stm` or post-indexed store in the band can reach `+0x68` | **CONFIRMED_STATIC** — all 8 enumerated; max reach from a base is `+0xC` |
| The ov6 dispatcher writes `+0x68` | **REFUTED** — 0 stores |
| The teardown's partner walk is dead code in retail | **CONFIRMED_STATIC** — `cmp r2,#0; beq` with `r2` provably always `0` |
| `+0x68` is a partner link to another ColPrm record | **PLAUSIBLE** *(carried from iteration 83)* — the shape fits; no instance is ever created |
| The ColPrm record carries unused machinery | **PLAUSIBLE** — three fields (`+0x68`, `+0xE8`, `+0x140`) by three independent routes |
| Iteration 83's four list heads are affected | **REFUTED** — they are on the fallthrough path, not inside the dead branch |

## Next angles, ranked

1. **Re-run the record map** with `0x0207CB58` and `0x0207CCD4` as anchors (carried) —
   both were read by hand across two wakes and yielded fields the automated map missed.
2. **Re-audit the map's `char+0xNN` offsets** across the three objects (carried).
3. **Name the arm9 `+0x56c` struct** (carried) — candidate `memset(r7+0x8, 0x5e0)` at
   `0x02076C2C`.
4. **Map `BattleCol.cpp`** (carried) — `Battle_ColManCreate` `0x0207AD3C`, and
   `0x0207B414`'s `+0x90` use.
