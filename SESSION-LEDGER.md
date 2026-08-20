# Session Ledger — JUS Reverse Engineering

Last updated: 2026-08-19 (ledger wake 1 after restart, session `justoolkit-e8`)

## 1. Current state

This file is a human catch-up summary — not the system of record. beads (`br`) is the record; protocol in `docs/orchestration/`.

**All three loops were shut down and restarted on 2026-08-19 for the branch consolidation.** The old three-branch, three-worktree setup is gone. Everyone now works on `integration/loops` in the main worktree.

**Live sessions (from ListAgents):**
- `justoolkit-e2` [9764b0] — **Runtime**. Just started (idle). Assigned by `justoolkit-85`.
- `justoolkit-73` [fbc915] — **Static**. Just started (idle). Assigned by `justoolkit-85`.
- `justoolkit-e8` — **Ledger** (this session). Just started.
- `justoolkit-85` [2eb529] — busy. The owner's direct session, brought up the three loops.
- `trainer-d4` [d035a5] — busy, unknown role.
- `test-suite-guardrails-1d` [096ca1] — idle, unknown role.

**Roles table updated** in `docs/orchestration/COORDINATION-PROTOCOL.md`.

## 2. Where things stand (inherited from the predecessor's handoff)

**The damage chain is solved end to end** [jus-reduction-is-quarter-multiplier-xk1]. Reduction is x0.75 per gate (25% of base), not a flat -2.0. Two gates read a class table at `0x02092E68`; the formula routine is `0x020823E4`. The retracted flat-2.0 claim is tracked at jus-ccb.

**CORRECTION (runtime wake 1, commit `9c55797`):** The +/-25% gates read `[r8+0x44]`, not `[r8+0x40]`. There are six gates (three add, three subtract), none unconditional. The old scope caveat — "bit 5 of `[r8+0x40]` clear, only class-1 sampled" — was reading a word that gates none of the six adjustments. Zero of six gates have been individually sampled. The x0.75 measurement itself is untouched; the mechanism attribution moved. Tracked at jus-gate-word-is-r8-0x44-fnz (`state:proposed`, awaiting static verification). Note: runtime and static independently found the same +0x40/+0x44 error within the same hour — a genuine cross-check (the correction doesn't rest on one reader), though also duplicated effort.

**Next action (revised):** find what sets the bits of `[r8+0x44]`. This is the gate word for the entire +/-25% system.

**PROGRESS (static wake 1, commit `67bd41c`):** Static found the ability-to-flag chain [jus-bit5-is-ability-10-rxl, `state:static-confirmed`]. Bit 5 of the gate word (`[r8+0x44]`) is set by ability id 10 via a mask table at `0x02092E78`. The setter is arm9 `0x02083BE0`; it reads a cached ability bitset through ov6 `0x02157114`. Two mask variants (subtract bits 4-9, add bits 12-17) map all six gates to ability ids. This is the chain the campaign has been looking for. Awaiting runtime verification (live read of +0x44 at jus-peek-plus-0x44-and-flag-writer-uvp).

jus-gate-word-is-r8-0x44-fnz promoted from `state:proposed` to `state:static-confirmed` — runtime produced it, static verified independently. Valid cross-check.

**CHAIN CLOSED (runtime wake 2 + static wake 3, commits `6a9c3d5` + `848c26f`):** The gate word read `0x00002010` live — predicted to the bit by static's table before runtime launched. From the ability bitset `0x02005200` (ids 9, 12, 14, 25), the table said `[r8+0x44]` = `0x00002010`: id 9 giving subtract-bit 4, id 12 giving add-bit 13, ids 14 and 25 not in the table. Runtime read exactly that. Static re-derived it independently before reading runtime's arithmetic. Object identity also closed: `[[battleObj+0x1a8]+0x10]` == r8 == `0x0220FDC4`, from two derivations. Category 1 fires bit 4 for -512 and *blocks* bit 13 — a bit that's armed and declined is the category gating itself, stronger evidence than a bit that simply fired. Three caveats: (1) no hit landed — eight stops, no contact, formula runs on misses (jus-formula-bp-not-a-hit-oracle-ve6); (2) bit 4's causality untested — control arms out of range, trivial pass caught only by unconditional stop counter; (3) ability 10 → bit 5 split into its own bead jus-bit5-ability-10-untested-mvk (`state:proposed`) — static corrected their own record, recognizing the title named the least-supported row. Bit 5 has been clear in every capture; 10 of 12 table rows unexercised. Tracked at jus-gate-word-read-live-0x2010-nbz (`state:runtime-confirmed`).

**Next open question:** if the formula runs on misses, where is contact decided? Static is taking it — candidate at arm9 `0x0208207C`, inside the same function as the never-reached `0x02081F5C`.

**PROCESS WIN (static wake 2, commit `e0a5fd7`):** Static caught a false confirmation in runtime's capture plan *before it ran*. The planned breakpoint at `0x0208257C` would have read r1 as the class index, but at that address r1 is the nature term (r5*(nature-0x100)). Since nature has been 1.0 in every measurement, r1 = 0 — which was inside runtime's pre-registered prediction of {0,1}. The check would have passed, concluding "category 1" without ever reading the actual class index. This is the check-that-agrees-with-itself pattern, caught preemptively because runtime posted its plan as a bead comment on jus-peek-plus-0x44-and-flag-writer-uvp rather than leaving it in an unreviewed wake prompt. Fix: break at `0x02082584` instead, where both r1 and r4 are live. Also: jus-elem-0x0e-is-packed-8wz (`state:plausible`) — the class index byte at elem+0x0E is packed (low 6 bits a field, bit 7 a flag, 0x3F reset sentinel), so runtime's refutation signature for r1 outside 0..15 is too strong.

**~~Nature does not affect damage~~ — RETRACTED.** jus-nature-does-not-affect-damage-0c6 is now `state:tainted`. Nature IS read in the damage path [jus-nature-is-read-in-damage-path-hbt, `state:static-confirmed`]. The factor tables at `0x0209FEF4` and `0x0209FF14` contain `0x0180` (1.5 in 8.8) in a rock-paper-scissors pattern over three natures plus "none". The arithmetic gives 8→12, matching DJ's January live-play observation and the ROM data. However, no nonzero nature term has been measured at runtime yet — the finding is ROM-and-arithmetic only (`state:static-confirmed`, not cross-confirmed). The August 3/3 null was real but overgeneralised — it established that poking the nature byte mid-battle does nothing, not that nature isn't read. Five docs carried banners calling the correct January answer wrong; all five corrected in commit `f077884`. Nature and the class gates combine additively, not multiplicatively — advantage plus one resist gate is 1.25x, not 1.5 x 0.75.

**jus-nature-january-vs-august-9a6** carries a live question for the owner: January's data says nature IS a 1.5x multiplier, August says it's not read. Both may be right (different paths, different overlays).

## 3. Open audit flags (wake 1)

### Flag C — jus-f0v still open (gimmick taint re-measurement)
The re-measurement never fully completed. The premise shifted: the 8.000 baseline was measured directly from a signed byte at a breakpoint (atlas P210+), so jus-f0v's original goal is partly moot. Remaining question: what applies the x0.75 reduction. Bead is labelled `state:tainted`.

### Flag L — Atlas retractions in commits, not beads
~8 retractions documented in commits/Battle-Engine-Map.md but not as coord beads. Self-contained, no downstream damage. Carried forward.

### Flag N — jus-zko kept open with reasoning (status update received)
Static argues it's not superseded: the chr_b record gate chain (how ability ids get from chr_b into battleObj+0x128) is a load-time question distinct from the damage formula. The ability chain found this wake (jus-bit5-is-ability-10-rxl) makes it more relevant, not less. Aging rule satisfied by this status update. May need repricing rather than closure.

### Flag O — jus-3aw character switching
Touch-swallow bug diagnosed by Fable (plan_step last-mask-wins batching). Runtime built a touch control but the oracle was unsound. Owner approved L/R sticker fallback.

### NEW Flag Q — Three kind:request beads aged past the consolidation shutdown
jus-fms (write-watchpoint on `0x020AFEB8`), jus-cvx (ObjShot kind-byte walk), and jus-baz (runtime address audit) are all `kind:request`, created 2026-08-18, still open with no status change since the loops restarted. The aging rule says a request shouldn't survive one completed wake without an update. These survived a shutdown — understandable — but the runtime loop should acknowledge or reject them on its first wake.

### NEW Flag R — jus-dead-bead-ids-in-docs-r4y still open
Four bead ids (jus-wic, jus-vrz, jus-qsh, jus-q4b) cited 14 times across two docs don't resolve. The baseline has 14 entries for these. No progress since filing.

### Flag S — RESOLVED: Battle-Engine-Map.md bare CONFIRMEDs cleared
Static cleared all 8 bare CONFIRMED warnings in commit `1d02b0b`. Warnings dropped 289→285. Deadline was blown by one wake but delivered. Baseline still 14.

## 4. Items parked for the owner

- **jus-nature-january-vs-august-9a6** — **OWNER ANSWERED:** January 1.5x was from live play, not derived. Nature is most likely applied at load time, not read mid-battle. August's claim needs scoping. Next action: reproduce B at 8→12 on the current harness with nature set via the training menu.
- **jus-law** — remaining open: Q7 (HP drift), Q8 (modes 12/18/20). Low priority.
- **jus-5bg** — deck requests (Edajima, Eve). Owner hasn't built them. No rush given the premise shift.
- **jus-fix-beads-merge-driver-epg** — `.gitattributes` points at a `bd merge` subcommand that `br` 0.2.19 doesn't have. Hard-conflicts on every merge.
- **jus-agent-loop-emu-timing-30s** — unassigned.
- **jus-post-consolidation-worktrees-imu** — decide where the loops work. Resolved by the consolidation (everyone on `integration/loops`), but the bead is still open.

## 5. How to use this ledger

Come back here after a break. Each section tells you what happened. Session names change on restart — check `ListAgents` for current names. beads (`br list --label coord`) is the authoritative record.
