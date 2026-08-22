# Project Goal

Lock down how JUS battle mechanics work well enough to rebuild the same system in a new game. Also pin down how the deckbuilding and koma systems work for a head start on reimplementation.

## What "locked down" means

For each subsystem, we need docs detailed enough that an engineer (or agent) who has never seen the original code could implement a faithful recreation. That means: data structures with field-level detail, control flow, arithmetic formulas, and edge cases — not just high-level architecture diagrams.

## Battle mechanics (primary)

- Damage calculation (flat reduction, HP encoding, all 8 callers in ov06)
- Collision system (ColPrm manager, contact arrays, phase tables)
- Move system (MoveMan, element lifecycle, priority resolution)
- Entity/projectile system (spawning, ownership, collision interaction)
- Guard/SP gauges
- Nature system's role in damage (nature/resist gates an additive term in the damage accumulator — see `docs/research/Nature-System-Consolidated.md`, bead `jus-nature-is-read-in-damage-path-hbt`)

## Deckbuilding and koma (secondary)

- Deck editor (overlay 01)
- Koma data structures (koma.bin layout, kshape.bin)
- Nature system's role in deck construction
- Helper/passive ability taxonomy (42 categories mapped)

## How work is organized

Work happens in one worktree on `integration/loops`, split by role rather than by session: **runtime**, **static**, **ledger**, and **harness**. Sessions come and go; the roles persist. See `docs/orchestration/COORDINATION-PROTOCOL.md` for the roles table and the rules they share.

## Documentation

- `docs/confirmed-facts/` — canonical rebuild-ready specs, one file per subsystem. Driven by the wayfinder map (bead `jus-wayfinder-map-digi`).
- `docs/research/` — the lab notebook: raw findings, experiments, and working notes.
