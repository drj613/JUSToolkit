# C6f — restore-function lead is dead; damage producer STUCK

Loop-Atlas iteration 26.

## The 9 callers are restore functions, not damage

Read all nine ov6 callers of `0x02078660` plus the one caller of `0x020785B8`. The arguments give it away — they're flags and percentages, not damage amounts:

| site | args |
|---|---|
| `0x02157D44` | `r1=1, r2=1` |
| `0x0215AC4C` | `r1=1, r2=1` |
| `0x0215CAA8` | `r1=1, r2=0` |
| `0x0215CAF0` | `r1=0, r2=1` |
| `0x0215CCE8` | `r1=0, r2=1` |
| `0x0215CE40` | `r1=0, r2=1` |
| 3 Thumb sites | `r1=0`, `r0` from a table lookup |
| `0x0215CBEC` → `0x020785B8` | **`r1=0x64`** (= 100) |

`r1`/`r2` only ever take 0 or 1 — booleans. And `0x020785B8(entity, 100)` against a function body containing `mov r4,#0x64` is clearly "set HP to N percent" called at 100% — a **full restore**.

So `0x02078660` is an HP/SP restore utility with per-resource flags, and `0x020785B8` is a percentage setter. Neither touches damage. **Lead refuted.**

## Tool fix: shared load addresses create phantom callers

While tracing arg-passing dispatchers, `find_callers.py` reported `ov4 0x02159BB8 → 0x02157A44`. That's a **phantom**. ov4 and ov6 both load at `0x0214CD20` and never coexist, so ov4 code hitting that address is calling its own overlay, not the ov6 function I named.

The tool now warns when a shared window exists. Earlier results are fine — arm9 targets aren't affected because arm9 is always resident — but this would have produced a wrong conclusion here. It's the fourth time this session a tool's silence or over-reporting created a plausible-looking artifact.

After discarding the phantom, real callers are: `0x02158B20` ← `0x02156E94`, and `0x0215807C` ← `0x02158070`. `0x02157A44` has **no** direct ov6 caller — like `0x02159EF8`, it's reached through a pointer table.

## Marking the damage producer STUCK

Per the charter's stuck rule, two consecutive wakes (C6e, C6f) made no progress on this question. Marking it and moving on.

**Established (solid):**

- HP changes only through a store to `+0x18`. Every such store with clamp context is enumerated: **17 sites in 8 arm9 functions**, plus one ov6 serializer that isn't a writer.
- The core apply function `0x02078488` has **14 callers**, all classified: 6 Thumb heals, 2 status ticks (poison `0x1D`, burn `0x1B`), 2 thin script wrappers, 3 arg-passing dispatchers, 1 accumulator flush.
- The accumulator is **refuted** as the melee path by breakpoint.
- `0x02078660` / `0x020785B8` are **restore utilities**, refuted.
- Damage demonstrably happens: `7168 → 6784` = 384 raw = 6.000 displayed, reproducibly.

**Not established:** which path melee actually uses. The remaining candidates are the three arg-passing dispatchers, whose deltas arrive as function arguments and whose callers are either single or indirect (pointer tables). Following them requires indirect-call resolution, which none of my tools do.

**Why I'm stopping here:** every technique I have — value search, offset scan, constrained offset scan, caller enumeration — has been applied, and three of them produced confident false positives along the way. The honest next step is a different *kind* of tool, not another pass with the same ones.

Options for a future round, by expected value:

1. **Find the pointer tables.** Both `0x02159EF8` and `0x02157A44` are called indirectly. Scanning for word-aligned runs of plausible ov6 code addresses would locate the dispatch tables and fill in the missing call edges.
2. **Ghidra** — Tier-2 task D0.3 already calls for a headless import. It resolves indirect calls, which is exactly the gap.
3. A hardware watchpoint on the HP halfword, which this GDB stub doesn't support.

The charter allows one codex second opinion when stuck. I'd hold it: codex hung for an hour on this same damage path during the harness session, and the blocker is tooling capability, not reasoning.
