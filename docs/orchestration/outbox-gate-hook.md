# Outbox-gate hook (draft — not installed)

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

## Install (requires owner action — not done here)

This edits `settings.json`, which is out of scope for an automated draft. Install it with
the `/update-config` skill, or add a PreToolUse hook entry matching the scheduling tool
that echoes the reminder above. Scope it to the runtime and static loop sessions (the
ledger loop doesn't need it). Verify it fires with a dry wake before trusting it.

## Why only one hook

Everything else (fast lane, provenance schema, lifecycle, TTL) is enforced socially by the
charter + the ledger auditor + the bounce-back rule. Hooks enforce *completeness and
ordering*, not scientific correctness — so the outbox-flush gate is the one worth wiring.
