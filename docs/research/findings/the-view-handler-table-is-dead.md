# Findings: the view's 16-slot handler table never runs

Loop-Atlas iteration 94. Static.

Iteration 93 left two untraced sites and two unresolvable write classes. Both are now
ruled out — the **view pointer's reachability is finite and small**.

**All 31 functions in ov6 that can hold a view pointer** contain exactly **one** store to
`+0xc`, inside the unreachable arm function. `view+0x0C` is always `0`, the gate's
`tst`/`popeq` always returns, and none of the twelve live handlers ever executes. **The
16-slot table is dead in this build.**

---

## 1. The view pointer cannot travel far

Instead of chasing writers of a common offset, enumerate everywhere the pointer can go.

`&char+0x130` is taken **29** times in ov6, handed to exactly **12** functions:

```
0x0215D4E0  0x0215FAB8  0x0215FB7C  0x0215FC78  0x0215FCAC  0x0215FCB8
0x0215FCCC  0x0215FCD8  0x0215FCE4  0x0215FD48  0x0215FD58  0x0215FED8
```

The only stored copy is `char+0x120 +0x0`, written by the constructor (iteration 87).
`&char+0x120` is taken at **4** sites — `0x02156B48`, `0x02157258`, `0x0215947C`,
`0x0215987C` — and **`ldr rD,[rB,#0x120]` occurs 0 times in ov6**, so nothing else loads it.

Those 16 functions, the 11 handlers, and the two trampoline targets call only **two**
functions: `0x0200D12C` and `0x020781E4`. Neither receives the view — SP-apply gets
`[view+0x00]`.

Complete set: **31 functions.**

## 2. One store to `+0xc` in all of it

Scanning all 31 for any store to `+0xc`:

```
store to +0xc at 0x0215FC3C in 0x0215FC20 (ov6)
1 store total
```

`0x0215FC20` is the arm function, unreachable since iteration 92 — its only literal sits
in a trampoline nothing references. The reachable reset `0x0215FB88` writes `view+0x0C = 0`.

## 3. Both iteration-93 candidates die

| candidate | why it is not a view |
|---|---|
| `0x021553BC` | writes `+0x0`/`+0x4`/`+0x8` from **dereferenced** args and `+0xc = 0x1000`; the view's constructor stores pointers directly. Not among the 31. |
| `0x021694C8` | not among the 31. |

Neither can receive a view pointer, so neither writes this mask. The 1022 `stm` and 181
register-offset stores are moot — a write needs a pointer, and the pointer's destinations
are enumerated.

## 4. What is dead

- the 32-bit enable mask `view+0x0C`
- all **12** live selectors and their 11 handlers
- both `int16[16]` arrays at `view+0x16` and `view+0x36`
- the parameter table at `[[0x02172984]+0xC]`
- the arm function `0x0215FC20` and its trampoline

Still live: the view's other fields. The reset runs, the `+0x5A`/`+0x5C` snapshots happen,
and `0x0215FE14`'s gauge chain is how `[char+0x1b4]` was identified — all reached outside
the gate.

**Fourth** vestigial system found this campaign, after ColPrm `+0x68`, `+0xE8` and
`+0x140`, and the largest: a complete per-character effect system, data table included,
wired up and never switched on.

## 5. Residual

**ov6-scoped and ARM-only.** The enumeration decodes ARM address-takes; ov6 has 18 Thumb
functions out of 752 (2%), and a Thumb function taking `&char+0x130` would be invisible.
No view pointer escapes to arm9 — the only non-ov6 callees are `0x0200D12C` and
`0x020781E4`, and neither receives it.

## Predictions status

| Claim | Verdict |
|---|---|
| The view pointer reaches exactly 12 functions directly | **CONFIRMED_STATIC** — 29 address-takes, `bl` target set enumerated |
| Nothing loads the stored copy at `char+0x120` | **CONFIRMED_STATIC** — `ldr rD,[rB,#0x120]` occurs 0 times in ov6 |
| The full holder set is 31 functions | **CONFIRMED_STATIC** — 12 + 4 + 11 handlers + 2 trampoline targets + 2 callees |
| Exactly one store to `+0xc` exists across all 31 | **CONFIRMED_STATIC** — `0x0215FC3C`, inside the unreachable `0x0215FC20` |
| `0x021553BC` or `0x021694C8` sets the view mask | **REFUTED** — neither is in the holder set |
| The `stm` and register-offset classes leave the question open | **REFUTED** *(iteration 93's residual)* — a write needs a pointer, and the pointer's destinations are enumerated |
| `view+0x0C` is always zero | **CONFIRMED_STATIC** — one writer is unreachable, the reachable reset writes `0` |
| The 16-slot handler table is dead in retail | **CONFIRMED_STATIC** — the gate returns on a clear bit every time |
| The view itself is dead | **REFUTED** — the reset, the snapshots and the gauge chain run outside the gate |
| A Thumb function could arm a slot | **not claimed** — 18 of 752 ov6 functions are Thumb and are not covered by this enumeration |

## Next angles, ranked

1. **Read the table at `[[0x02172984]+0xC]`** (carried) — 16 `{u16, u16}` entries.
   Known-unused, but it is the designers' parameter set for a cut feature and cheap to dump.
2. **Name the `≥0x570` struct at `[char+0x1b4]`** (carried) — reachable from ov6 at
   `0x0215FE1C`.
3. **Read `char+0x7c`'s users** `0x02158B20`, `0x021586D0` (carried).
4. **Map `BattleCol.cpp`** (carried).
