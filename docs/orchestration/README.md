# Orchestration — how the JUS RE loops coordinate

Designed 2026-08-18 after coordination between the runtime and static loops collapsed and
had to be hand-restarted. Two independent advisors (Fable, Codex) and the ledger session
converged on this design.

- **`COORDINATION-PROTOCOL.md`** — shared canon. The wake bracket, beads as system of
  record, provenance schema, claim lifecycle + taint, fast lane, TTL, instrument
  discipline, `/codex` rule, subagent limits. Read this first; it wins over any charter.
- **`Charter-Ed.md`** — runtime loop's standing charter (new; it had none before).
- **`Charter-Atlas-additions.md`** — additions to the static loop's existing charter.
- **`Charter-Ledger.md`** — ledger loop, recast as auditor of the beads ledger.
- **`RESTART-PROMPTS.md`** — the shutdown handoff command to send before clearing context,
  and the restart prompt for each role.
- **`outbox-gate-hook.md`** — the one hook (flush-before-schedule reminder); needs owner
  install via `/update-config`.

**Where the loops run:** all three now share the main worktree on the branch
`integration/loops` (master + all three loop branches merged, 2026-08-19). One branch, one
worktree — git cannot check out one branch in two worktrees, and `br` needs the db-backed
`.beads` that only the main worktree has. See the "Where the loops run" section of
`RESTART-PROMPTS.md` before restarting anything.
