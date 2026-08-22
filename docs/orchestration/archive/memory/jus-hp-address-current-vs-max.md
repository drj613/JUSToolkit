---
name: jus-hp-address-current-vs-max
description: "JUS opponent HP — 0x021DF7F0 is CURRENT HP, 0x021DF7EE is MAX HP; they read identically at full health, which is what let the wrong one hide"
metadata: 
  node_type: memory
  type: project
  originSessionId: 329d0fef-b7f8-4c51-a5ce-144e785cd796
  modified: 2026-08-19T22:14:28.289Z
---

Per character struct: `+0x16` = max HP, `+0x18` = current HP (both 16-bit LE, 1/64 units, displayed = raw/64).
Opponent: max `0x021DF7EE`, current `0x021DF7F0`. Player: current `0x021DF1D4`.

**Why it matters:** the two addresses read identically whenever the target is at full health, so a damage-detection harness built and tested against a full-health opponent can silently watch the wrong field indefinitely — every measurement looks fine because "no change at full HP" is indistinguishable from "no change because I'm reading max HP." This produced several sessions of false "no hit landed" conclusions in the runtime loop, and voided at least one touch-input experiment before the mixup was caught. See `[[record-points-one-representation-away]]` and `[[dream-attack-and-touch-mechanics]]`.

**How to apply:** always use `+0x18` (current HP) for damage-detection watches, never `+0x16`. To sanity-check which address you actually have, don't just peek once — watch it across a window where HP is known to be moving (e.g. passive regen, or a poked/verified hit), since a static read at full health can't distinguish the two.
