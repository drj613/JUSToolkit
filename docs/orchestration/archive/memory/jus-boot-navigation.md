---
name: jus-boot-navigation
description: "Pressing Start skips Jump Ultimate Stars' opening intro — needed when scripting boot-to-battle navigation"
metadata: 
  node_type: memory
  type: project
  originSessionId: de2560dd-5a95-4ccb-9bfc-3c4d1f9ff23d
  modified: 2026-08-14T15:15:28.843Z
---

When driving Jump Ultimate Stars from boot (e.g. via the melonDS agent bridge in
`scripts/emu/`), pressing **Start** skips the opening intro instead of waiting it out.

**Why:** unattended runs have to get from ROM boot to a battle with button
inputs only; knowing which button short-circuits the intro saves guessing and
many wasted frames.

**How to apply:** in a boot-to-battle input plan, latch `START` early rather
than mashing `A`. Owner supplies this kind of live-play ground truth on request —
see [[koma-system-observed-behavior]].
