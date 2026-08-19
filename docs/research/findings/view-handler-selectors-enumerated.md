# Findings: all 16 view selectors enumerated — 12 live, 4 dead, one issuer each

Loop-Atlas iteration 89. Static.

All call sites of the view's gate `0x0215FC78` and its sibling `0x0215FCE4` are resolved:
**17 sites, 17 immediates, 0 computed.**

Selectors **4–15 are all issued; 0–3 never are.** Those four are the table slots sharing
the no-op handler `0x0215FFDC` — dead slots and unissued selectors are the same set,
confirmed from two independent directions.

Each selector is issued by one function, so these are **subsystem-specific events**, not a
general-purpose API.

---

## 1. The 17 sites

| selector | site | issuing function | what that function is |
|---|---|---|---|
| `0x4` | `0x0215A06C` | `0x02159EF8` | state dispatcher |
| `0x5` | `0x0215FB2C` | `0x0215FAC4` | `BattleCharaInfo.cpp` |
| `0x6` | `0x0215A048` | `0x02159EF8` | state dispatcher |
| `0x7` | `0x0215D480` | `0x0215D3B4` | — |
| `0x8` | `0x0215ACB8`, `0x0215ACCC` | `0x0215A978` | — |
| `0x9` | `0x02158B90` | `0x02158B20` | hit resolution |
| `0xA` | `0x0215A054` | `0x02159EF8` | state dispatcher |
| `0xB` | `0x02158E54` | `0x02158B20` | hit resolution |
| `0xC` | `0x0215CEB8` | `0x0215CE28` | — |
| `0xD` | `0x021577D4` | `0x021574CC` | spawn dispatcher |
| `0xD` | `0x02157994`, `0x021579BC` | `0x02157958` | — |
| `0xE` | `0x0215A080`, `0x0215A36C`, `0x0215A3D8` | `0x02159EF8` | state dispatcher |
| `0xF` | `0x0215A00C` | `0x02159EF8` | state dispatcher |

Twelve distinct selectors. Each is issued from one function except `0xD`, which comes from
the spawn dispatcher and from `0x02157958` — `0x48C` apart in the same module.

## 2. Dead slots and unissued selectors are the same four

Iteration 88 found table indices 0–3 all pointing at `0x0215FFDC`. This iteration finds
selectors 0–3 never passed. Independent observations — one from the table, one from call
sites — and they agree exactly.

This rules out the alternative that `0x0215FFDC` is a real default for four
live-but-uninteresting cases. Nothing reaches it.

Effective table: **12 slots, 4–15.**

## 3. The same shape as the 73-case dispatcher

ov6 already has one enumerated dispatcher: `0x02157A44`, 73 cases, 33 live and 40 no-op
(iteration 46). The view's table is the same architecture at smaller scale — dead entries,
a gate, and issuers that only pass a fixed constant.

Both were pinned down the same way: enumerate every call site, back-resolve the immediate,
and treat "no issuer" as dead.

## 4. A scan bug worth recording

First pass reported all 17 selectors as COMPUTED. The mask was wrong:

```python
(y & 0x0FFF0000) == 0x03A01000      # wrong: mask zeroes bits 15-12, value sets them
(y & 0x0FFFF000) == 0x03A01000      # right
```

`mov r1,#0xf` is `0xE3A0100F`. Masking with `0x0FFF0000` gives `0x03A00000`, which never
equals a compare value carrying `Rd = 1` in bits 15–12. Result: a clean, plausible "all
computed" — the same failure mode as iteration 46's BL mask and iteration 47's `ldr` mask,
both of which also returned confident zeroes.

**Third mask bug of this campaign, same signature:** mask and compare value disagree about
which bits matter, producing an empty result instead of an error. When a scan reports 100%
of one category, check the mask before believing it.

## Predictions status

| Claim | Verdict |
|---|---|
| All 17 view-gate call sites pass an immediate selector | **CONFIRMED_STATIC** — 17 of 17 resolved, 0 computed |
| Selectors 4–15 are all issued | **CONFIRMED_STATIC** — every value in that range appears |
| Selectors 0–3 are never issued | **CONFIRMED_STATIC** — absent from all 17 sites |
| The 4 unissued selectors are the 4 slots sharing `0x0215FFDC` | **CONFIRMED_STATIC** — the two sets coincide |
| `0x0215FFDC` is a live default for real cases | **REFUTED** — nothing reaches it |
| Each selector has one issuing function | **CONFIRMED_STATIC** — with `0xD` the sole exception, from two functions in one module |
| The state dispatcher is the heaviest issuer | **CONFIRMED_STATIC** — 7 of 17 sites, selectors 4, 6, `0xA`, `0xE`, `0xF` |
| A selector might be passed in a register somewhere | **not claimed** — no computed site exists among these 17, but only the two known entry points were scanned |

## Next angles, ranked

1. **Read the handler for selector `0xD`** (`0x0215FF64`) — the most-issued selector and
   the one the spawn dispatcher uses. Slots 13 and 14 share that handler.
2. **Read selectors 9 and `0xB`** (`0x0215FF4C`, `0x0215FF74`) — the two the hit-resolution
   path issues, so they touch the damage pipeline directly.
3. **Find who sets `view+0x0C`** (carried) — the mask decides which of the 12 ever run.
4. **Size `char+0x7c`** (carried) — damage-side users `0x02158B20`, `0x021586D0`.
