# Outbox-gate hook (INSTALLED 2026-08-18)

Installed as a command hook: `.claude/settings.json` → PreToolUse matcher
`ScheduleWakeup` → `.claude/hooks/outbox-gate-reminder.sh`. The script emits a
`systemMessage` reminder and exits 0 — it sets no `permissionDecision`, so it can never
block or deny wake scheduling. **Hooks load at session start**, so it takes effect for
each loop on its next restart (exactly the intended timing). Because `.claude/` is
per-project-root, each worktree needs `master` merged (or `.claude/` copied) for the hook
to apply there.


One hook, and only one, because a hook is the one layer that doesn't depend on an agent's
willingness. It reminds the runtime and static loops to flush before scheduling the next
wake — the single rule that must not be left to a heads-down agent's judgment.

**Make it a reminder, not a hard block.** A hard block on `ScheduleWakeup` can deadlock an
unattended loop (e.g. if the flush legitimately can't complete). A prompt-style PreToolUse
hook that injects a reminder is enough — it puts the checklist in front of the model at
exactly the decision point.

## What it gates

Fires on the loop's wake-scheduling tool call (`ScheduleWakeup`). Injects:

> Before scheduling the next wake: have you flushed the outbox this wake? Specifically —
> published any retraction or relabel of something you previously sent the partner? Sent
> any result bearing on the partner's open questions? Run `br sync --flush-only`? If a
> measurement is missing its conditions block or an address its reachability basis, it is
> INCOMPLETE — fix or label it before it lands in anyone's canon.

## Install (done)

Committed as `.claude/settings.json` + `.claude/hooks/outbox-gate-reminder.sh`. It fires
project-wide (harmless in the ledger loop, which has no findings outbox). To verify it
fires, start a session with `claude --debug` and watch for the hook on a `ScheduleWakeup`
call. To disable, remove the `PreToolUse` block from `.claude/settings.json`.

## Why only one hook

Everything else (fast lane, provenance schema, lifecycle, TTL) is enforced socially by the
charter + the ledger auditor + the bounce-back rule. Hooks enforce *completeness and
ordering*, not scientific correctness — so the outbox-flush gate is the one worth wiring.
