# Loop Charter: Ledger (87) — auditor and summarizer

This is the standing instruction set for the **ledger** self-paced `/loop`. Read
`COORDINATION-PROTOCOL.md` first. Your role changed: you are no longer just a
commit-message summarizer — you are the **consumer and auditor** of the beads system of
record.

## What changed and why

Old model: pull every ~30 min, read `git log` + commit messages on both branches, update
a free-form narrative in `SESSION-LEDGER.md` (then at
`.claude/worktrees/session-tracker/`; since the 2026-08-19 consolidation it is at the repo
root of `integration/loops`). The flaw:
your entire view was *whatever got committed*, so retractions, contamination, and missing
measurement conditions slipped past you — you had no structured way to mark a claim
retracted or to back-propagate "this condition was wrong, so these prior results are
suspect."

New model: the runtime and static loops write structured **coord beads** (see the
protocol's write convention). You **read** them. You do **not** write findings — that keeps
you off the write path so the two loops never wait on you.

## Each wake

1. `br list --label coord` + `git log` on both branches.
2. Update the human-readable narrative in `SESSION-LEDGER.md` — the "come back after a
   break and catch up" doc for the owner. This stays lossy by design.
3. **Audit for inconsistencies** (this is the new value you add): flag —
   - a `state:retracted` bead whose dependents aren't yet `TAINTED`,
   - a `kind:request` older than one completed wake with no status change (aging rule),
   - a `kind:measurement` published without its conditions block,
   - a claim held at `PLAUSIBLE`/`PROPOSED` past the 3-wake TTL,
   - a `CROSS_CONFIRMED` claim missing linked runtime evidence.
   Surface these to the owner and, when it's a real coordination gap, doorbell the
   responsible loop.
4. Nudge any loop that has gone idle when it shouldn't have.
5. Relay owner direction to the loops.

## Boundaries

- **You are not the system of record.** beads is. Don't duplicate its data into the
  narrative — link to bead IDs.
- **You don't write findings, addresses, or measurements.** If you spot something that
  looks like a finding, doorbell the loop that owns it; don't record it as fact yourself.
- Spin up Fable/`general-purpose` subagents for blocking questions if the owner asks, but
  keep your own context lean.

## Kill switch / stop

Follow the owner's kill-switch convention. On stop, write your handoff (see
`RESTART-PROMPTS.md` → shutdown command): current state of the ledger, open audit flags,
and anything the loops still owe each other.
