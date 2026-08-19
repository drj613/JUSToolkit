# D0.3 — Ghidra isn't installed; I built a substitute, and it doesn't work

Loop-Atlas iteration 30. A negative wake, reported as one.

## The D0.3 decision

D0.3 starts with `brew install --cask ghidra`. Ghidra isn't on this machine — no `analyzeHeadless`, no `/Applications/ghidra*`, no cask.

I didn't install it. It's a large external download, and the loop charter prioritises D0.1 and D0.2, not D0.3 — so I don't have standing to pull in a heavyweight dependency unattended. **This is the one combat-phase decision that needs a human**, and I'm flagging it rather than guessing.

## What I built instead

Ghidra would be overkill for the actual gap. The problem is narrow: `str rD,[rN,rM]` has no literal offset, so every offset-based search misses it, and the writer of the pending-damage field `+0x134` is probably hiding behind one of those. What's needed is constant propagation within a basic block — track which registers hold known values, then read the offset off the register.

`scripts/decomp/resolve_reg_offsets.py` does that. **It doesn't work well enough to trust.**

## Reporting the failure, not the output

On ov6 the tool reports **0** register-offset accesses with a resolvable offset. That's wrong — a cruder check (scan up to 8 instructions back for `mov rm,#imm`) finds **14**. My state-clearing is too aggressive: conditional instructions, branch targets, and push/pop all wipe the register map, so it under-reports badly.

I labelled the bug in the tool's docstring rather than leaving a silent tool that returns plausible-looking emptiness. That failure mode has bitten this project four times already.

The cruder scan isn't trustworthy either. Its 14 hits resolve to offset `0` (13x) and `0x10` (1x), with the zeros looking like a stale producer match rather than the real one. **Neither approach finds anything at `+0x134`/`+0x138`.**

| technique | outcome |
|---|---|
| immediate-offset stores to `+0x134`/`+0x138` | 2 in ov6, both the vtable initialiser (wrong object) |
| folded base (`add` then store) | 0 |
| any instruction with immediate `0x134`/`0x138` | 0 in ov6, 0 in arm9 |
| `lsl #6` then store | 0 |
| **register-offset with propagated constants** | **0 usable — tool buggy, cruder version finds nothing relevant** |

Five techniques, zero results. The honest read: the offset is computed in a way none of these capture — across blocks, from a loop induction variable, or loaded from memory.

## Where this leaves the damage writer

Two routes forward, neither mine to take alone:

1. **Ghidra (D0.3)** — real data-flow analysis, which is exactly the missing capability. Needs a human to authorise the install.
2. **Harness-side frame bisection** — `+0x134` is set one frame before the HP drop, so breaking at candidate points and checking whether the field is already non-zero names the writer in a logarithmic number of runs. Cheaper, and it belongs to the emulator session.

Route 2 is probably the winner. The field is known, the frame is known, bisection needs no new tooling — and I've now spent two wakes proving the static route is exhausted.

## What was actually worth doing

The tool, even broken, is worth keeping. It documents the exact boundary of what offset-based static analysis can reach on this ROM, and its docstring records the measured discrepancy (0 vs 14) so the next person won't trust it blindly. A tool that reports its own unreliability beats one that returns confident emptiness — which has been the recurring failure of this whole phase.
