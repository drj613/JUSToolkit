# Static RE Phase 0 — Gap-Closing Loop (pre-GDB)

Loop-executable follow-up to the Battle-Engine-Atlas campaign
(`docs/design/Static-RE-Orchestration.md`, completed 2026-07-02, see
`scripts/analysis/loop-report.md`). Goal: close every gap in
`docs/research/Battle-Engine-Map.md` that does NOT require an emulator,
so a single human GDB session (Phase 1) can resolve the rest.

**Protocol:** follow Section 3 (Loop Protocol), Section 4 (Evidence
Integrity), and Section 8 (Failure playbook) of
`docs/design/Static-RE-Orchestration.md` EXACTLY, with these overrides:

- State file: `scripts/analysis/loop-state-phase0.json` (same schema; create
  from the unit catalog below on iteration 0).
- Workspace: the EXISTING worktree `.claude/worktrees/battle-engine-atlas`,
  branch `loop/battle-engine-atlas`. If the session did not start there,
  enter it first (EnterWorktree with that path). Never work in the main
  checkout. `jus_files` is a symlink into the main checkout — expected.
- All tooling from the prior campaign is present and gated
  (`scripts/analysis/`: rom_loader, disasm_db, xref_db, query.py,
  verify_evidence.py, gates.py; venv at `scripts/analysis/.venv` — if the
  venv is missing, recreate: `python3 -m venv` + `pip install capstone`,
  then run `gates.py` before anything else).
- Git: the beads commit hook is broken repo-wide — commit with
  `--no-verify` always.
- Safety: iteration cap 30. Kill switch `scripts/analysis/STOP`. No pushes.
  No emulator/GDB. No edits to `src/`, `lib/` — RUNNING the CLI is allowed
  (P1), editing it is not. Exception to the orchestration doc's
  "no edits to scripts/analysis tooling": P6 explicitly amends the tooling,
  guarded by gates.
- Prior findings/verdicts live in `jus_files/analysis/findings/` (gitignored).
  Read `critic.round1.json` for the B12/B14 specs and
  `scripts/analysis/loop-state.json` (log) for full campaign context.

## Success criteria (DONE)

1. ≥70 per-character collision JSONs exported and re-mined (P1+P2).
2. projectile-entities has a `.scored.json` (3-lens verify complete) (P3).
3. B12 + B14 traced, 3-lens verified, scored (P4+P5).
4. Tooling upgrades landed with `gates.py` still exit 0 (P6).
5. `Battle-Engine-Map.md`, `GDB-Validation-Queue.md`, `../research/archive/Research-Status.md`
   updated from the new verified results; tree clean; report written (P7).

BLOCKED / safety stops: as per orchestration doc Section 1.

## Unit catalog

**P1-export-collisions** (tool, priority 1, no deps)
Run the repo CLI's `ExportAllCollisions` batch command
(`src/JUS.CLI/JUS/CombatCommands.cs` — read it first to learn exact
invocation; .NET SDK pinned via mise; build with `dotnet build` if needed)
against the full character `.bin` set under
`jus_files/ripped_jus_files/` (collision sources — locate via the command's
own expectations). Output JSONs land next to the existing 4 in
`jus_files/exported_combat/` (or the command's default — record where).
AC (mechanical): ≥70 `*_collision.json` files exist and parse; the original
4 files' contents unchanged (byte-compare); exporter exit 0.
Fallback: if the command needs per-file invocation, script the batch in the
scratchpad — do not edit src/.

**P2-remine-collision-data** (tracer/data, priority 2, deps P1)
Re-run + extend `jus_files/analysis/findings/collision_data_miner.py` over
the full export. Findings →
`jus_files/analysis/findings/collision-data.round2.json` (same schema/rules
as round 1, `data_only: true`, reproducible script mandatory). Re-test every
round-1 PLAUSIBLE/UNSURE claim at full-roster scale (hitTier distribution,
type5→tier3, projectileId sentinel values, hitProperties per-character
constancy, damageFlags==0 rate). One combined verify lens (independent
recomputation) as in round 1 → verdicts + scored files.
AC: round2 findings + verdicts + scored exist; miner deterministic (2 runs
identical); every cited number reproduced.

**P3-verify-projectile-entities** (verify, priority 2, no deps)
Run the standard 3 lenses (disasm-correctness, aliasing, data-consistency —
prompts per prior campaign) on
`jus_files/analysis/findings/projectile-entities.round1.json`; score with
the standard rule (≥2 REFUTED → SPECULATIVE; 3× UPHELD → keep; else
PLAUSIBLE). AC: 3 verdict files (5 verdicts each) + `.scored.json`.

**P4-B12-trampoline-sweep** (tracer, priority 2, no deps)
Execute critic spec **B12** (`critic.round1.json` → next_tracer_specs):
disassemble the 7 remaining call sites of trampoline `0x020783CC` plus any
sibling trampoline feeding clamp-accumulator `0x02078488`/`0x020784B8` with
a base offset ≠ `+0x56c` — quarry: guard-health and SP-gauge instances of
the Meter struct. Findings →
`jus_files/analysis/findings/guard-sp-gauges.round1.json` (standard schema,
verify_evidence.py must pass). Then 3-lens verify + score (own unit-internal
sequencing: tracer AC first, lenses as follow-up units).
AC: findings verified exit 0; scored file exists after lenses.

**P5-B14-chrb-catalog** (tracer, priority 2, no deps)
Execute critic spec **B14**: catalog ALL ~87 references to chr_b singleton
`0x0214BD80` — for each, the record byte-offset(s) accessed and one-line
consumer classification; specifically flag any getter reachable from ov6
battle code. Findings →
`jus_files/analysis/findings/chrb-catalog.round1.json` (standard schema;
catalog table may live in a claim's evidence_data-style appendix, but every
representative disasm quote must pass verify_evidence.py). 3-lens verify +
score.
AC: findings verified exit 0; catalog covers every xref hit for
`0x0214BD80`; scored file exists.

**P6-tooling** (tool, priority 3, no deps — run late so P4/P5 use stable DBs)
Three upgrades to `scripts/analysis/` (inline coding or one subagent):
(a) `query.py search-op-imm <val>`: find data-processing immediates
(`cmp/tst/mov/and/orr #imm`) — grep the disasm text files; deterministic
output like search-imm.
(b) Translate `jus_files/analysis/arm9_tables.json` candidate tables from
file offsets to RAM addresses (arm9 base 0x02000000) → write
`jus_files/analysis/arm9_tables_ram.json`; smoke-test `xrefs-to` on 3
candidates.
(c) OPTIONAL (skip if risky): improve disasm_db `bx <reg>` epilogue
handling; if attempted, regenerate DBs and require full `gates.py` pass +
spot-check that fn count stays in [1000, 20000].
AC: new subcommand smoke-tests pass; `gates.py` exit 0 after all changes;
`query.py --selftest` exit 0.

**P7-synthesis** (synthesis, priority 4, deps P2+P3+P4+P5)
Update the three canon docs from new VERIFIED results only (same rules as
prior D1): fold round-2 collision stats in, promote/demote
projectile-entities per P3 scoring, add guard/SP-gauge and chr_b-catalog
sections or fold into existing ones, regenerate the GDB queue (drop cards
answered statically, add new PLAUSIBLE/SPECULATIVE cards), refresh the
Phase-1 GDB session plan (the 5 discovery breakpoints). Write
`scripts/analysis/loop-report-phase0.md` (morning report per Section 9).
AC: docs updated, links resolve, no refuted-claim references, committed,
tree clean.

## Subsystems tracked in state

collision-data (round 2), projectile-entities (verify), guard-sp-gauges
(new), chrb-catalog (new). Others remain as the prior campaign left them.

## Pacing

Per orchestration doc Section 6 (60s next-unit, 1200s subagent fallback,
max 6 concurrent subagents; delegate tracers/verifiers/lenses to sonnet,
mechanical glue to haiku).
