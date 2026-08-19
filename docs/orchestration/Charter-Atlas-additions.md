# Charter additions: Static (atlas)

The static loop already has a strong charter (`docs/research/Loop-Charter-Atlas.md` — since
the 2026-08-19 consolidation it is on `integration/loops` alongside everything else, not in
a separate worktree). These are **additions**, to be merged into it at the next restart — not a
rewrite. They import the shared `COORDINATION-PROTOCOL.md`.

## Fix the stale reference

The charter's North Star names the runtime loop `justoolkit-06`. That name is stale
(currently `justoolkit-ed`). Replace hard-coded partner names with **role resolution via
`ListAgents`** — names drift across restarts.

## Adopt the wake bracket

Add the protocol's INGEST → … → FLUSH → SCHEDULE bracket. The static loop already does
"one task per wake, commit, update state, schedule" — extend it so that **before
scheduling the next wake** you: apply the runtime loop's retractions/taint notices, and
flush your own outbound artifacts. Never schedule with an unflushed outbox or an
unreported urgent invalidation.

## Address packets are falsifiable cards

Every `kind:anchor` you send the runtime loop ships as a card (protocol schema):
address + type + build applicability + **reachability basis** (and whether live-battle
reachability is *established* or only inferred) + expected runtime shape + confidence +
**a one-line runtime test with its recognizable failure signature**. Example that would
have prevented the bad-anchor incident: "deref `0x…`, expect a pointer into
`0x02xxxxxx–0x02yyyyyy`; a literal-pool-looking word means it's wrong."

Static self-correction does **not** substitute for an early runtime smoke test. Do not
call an address `CROSS_CONFIRMED` without linked independent runtime evidence; hold it at
`PLAUSIBLE` until then.

## Push retractions; enumerate dependents

You retract often (the `+0x4C` "stat" label, the P154 struct base, etc.) — that's healthy,
but retractions must go out the **same wake** you make them, naming every dependent claim
and marking it `TAINTED`. The runtime loop builds tooling on your addresses; a silent
relabel has the highest blast radius in the system.

## Track and age your requests

Convert runtime dependencies into explicit `kind:request` coord beads with owner,
priority, expected output, and failure signature. A request unverified after 2 wakes →
ping the runtime loop; after 3 → downgrade the dependent claim to `SPECULATIVE`.

## Don't build on context-free numbers

A measurement from the runtime loop that arrives without its conditions block is
`INCOMPLETE` — bounce it back, don't build on it.

## `/codex` — keep doing what you're doing

You already use `codex:rescue` well (second opinion before canon, when stuck two wakes,
ask-before-concluding). Keep it. No change — this is the bar the runtime loop is being
asked to meet.
