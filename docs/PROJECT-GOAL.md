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
- Nature system (deck-building only — does not affect battle damage)

## Deckbuilding and koma (secondary)

- Deck editor (overlay 01)
- Koma data structures (koma.bin layout, kshape.bin)
- Nature system's role in deck construction
- Helper/passive ability taxonomy (42 categories mapped)

## Active sessions

Two sessions are currently working toward this goal:
- **justoolkit-06** (master) — runtime experiments via the agentic melonDS harness
- **battle-engine-atlas-c2** (loop/battle-engine-atlas) — structural static analysis

They coordinate directly with each other. justoolkit-06 serves as the runtime validator for atlas's structural findings.

## Documentation

Research docs live in `docs/research/`. A cleanup pass is planned to consolidate and organize these once the current entity/projectile investigation wraps up.
