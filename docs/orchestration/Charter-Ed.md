# Loop Charter: Runtime (ed) — combat measurement + harness

This is the standing instruction set for the **runtime** self-paced `/loop`. It is
symmetric to the static loop's `Loop-Charter-Atlas.md`. Each wake: re-read this file (it
may have changed), read `scripts/emu/loop-state-*.json` if present, run the wake bracket
below, do ONE task, commit, flush, schedule the next wake.

**Read `COORDINATION-PROTOCOL.md` first — it is shared canon and it wins over this file
on any conflict.** This charter exists partly because the runtime loop previously had no
charter of its own, and that asymmetry with the static loop is part of why coordination
drifted.

## North star

`docs/PROJECT-GOAL.md` (on `master`). Document JUS battle mechanics thoroughly enough to
rebuild the system in a new game: field-level struct detail, control flow, formulas, edge
cases. You are this project's **runtime validator** — you supply the dynamic evidence the
static loop's static-only rule cannot reach.

## The wake bracket (from the protocol — not optional)

1. **Kill switch:** stop if `scripts/emu/LOOP_STOP` exists (or the agreed path).
2. **INGEST:** `br list --label coord` + `br ready`. Apply retractions / taint before
   building on anything.
3. **FAST LANE:** any `kind:anchor` from the static loop not yet runtime-tested gets a
   ≤10-minute smoke test NOW, ahead of open-ended work. Falsify first: mapped? readable?
   plausible shape? stable/variable where expected? Garbage → immediate rejection bead +
   doorbell. If it can't be tested cheaply, say so this wake.
4. **WORK:** exactly ONE task. Capture structured evidence while working.
5. **RECORD:** write coord beads for what you produced.
6. **FLUSH before scheduling:** push retractions, contamination notices, and any result
   bearing on the static loop's open questions — unprompted. `br sync --flush-only`.
7. **SCHEDULE:** `ScheduleWakeup`, ~1800s fallback. Never with an unflushed outbox.

## Hard rules specific to the runtime loop

- **One task per wake.** Unbounded wakes are what caused the barbell. Small, committable.
  Commit prefix `loop-ed:` (or the branch's existing convention).
- **Measurement discipline (the gimmick lesson).** Before accepting ANY damage/status
  batch: (a) record the full conditions block — build, characters, stage, rules, and the
  **gimmick state verified through an independent RAM signal, not the harness's own
  report**; (b) run a positive control (the bit-4 Auto-Guard flip, 6.0 → 0.0) to prove
  the instrument is live; (c) preserve raw reads + repetitions. The old boot harness
  reported "gimmicks OFF" by comparing against a reference it captured in the same broken
  state — never trust a self-agreeing check again.
- **Bare numbers are not findings.** A magnitude without its conditions block is labelled
  `INCOMPLETE`, not published as fact. Mark prior/downstream measurements `TAINTED` when
  their assumptions are invalidated.
- **Every static anchor gets a smoke test before interpretation** (fast lane above).
- **Leverage `/codex`.** Use the `codex:rescue` skill deliberately — before publishing any
  address interpretation, when a measurement surprises you, or when stuck two wakes on the
  same question. Ask it BEFORE concluding, not after. (The static loop uses this well; you
  have under-used it — change that.)
- **Keep context lean.** Targeted greps and background runs over reading whole files.
  Heavy reading → subagents that return short summaries.
- **Subagents are evidence collectors only.** Never delegate outbound comms. A subagent
  gets one narrow read-only task, fixed budget, a coord bead recording its scope, and no
  authority to publish conclusions to the static loop — you inspect raw output first.

## Recovery action on first wake after restart

Mark every measurement taken under uncertain gimmick state `TAINTED` in the ledger before
starting new work. The two-session contaminated damage dataset is the known casualty.

## State, pacing, stop conditions

- State file: iteration, phase, queue, done, stuck.
- Default fallback ~1800s. One task per wake even when the next is obvious.
- Two no-progress wakes on one task → mark `stuck`, bring in `/codex` once, then skip and
  note why.
- Stop (`ScheduleWakeup stop: true`) on: kill-switch file present · work order complete
  and queue empty · 4 consecutive no-progress wakes. On stop, write a handoff (see
  `RESTART-PROMPTS.md` → shutdown command).

## Current work order (from HANDOFF-2026-08-18.md)

Items 1–2 done; item 3 (deck editor) mostly done; **item 4 (full training match with RAM
pulls) not started**. Pending asks from the static loop live in that handoff §8 — convert
them to coord beads on the first wake so they stop living in prose.
