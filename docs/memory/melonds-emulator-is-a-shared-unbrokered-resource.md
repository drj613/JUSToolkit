---
name: melonds-emulator-is-a-shared-unbrokered-resource
description: "The melonDS instance is a single shared resource with no access broker; input during a live battle from any session contaminates every other session's measurements"
metadata: 
  node_type: memory
  type: project
  originSessionId: 329d0fef-b7f8-4c51-a5ce-144e785cd796
  modified: 2026-08-19T21:42:33.919Z
---

On 2026-08-19, driving the emulator (loading `cb_battle`, sending `input.NDSTapDown(140,90)` during a live battle to investigate why in-battle touch seemed not to work) silently contaminated a concurrent runtime loop's damage-formula measurements — nine formula evaluations it had attributed to an "ambient element" were actually caused by this tap. Reads/screenshots are harmless; **input during a live battle is not** — see `[[cross-session-coordination]]` and `docs/orchestration/COORDINATION-PROTOCOL.md`.

**Why:** no mechanism in the coordination protocol arbitrates emulator access, and multiple sessions treating it as theirs alone produces confounds that look like game-logic mysteries (e.g. "ambient" formula fires) rather than a shared-resource bug — costing real attribution work on both sides before anyone thought to check.

**How to apply:** before sending ANY input to a running melonDS instance (not just reads), announce it — to whichever session/role currently holds the runtime role (check `docs/orchestration/COORDINATION-PROTOCOL.md`'s role table, resolve via `ListAgents` since names drift across restarts), and record the framecount/time window on `br` bead `jus-emulator-access-not-exclusive-tum`. Announce again when done. If no runtime role is currently assigned, still post the window to that bead so a later measurement session can rule your input in or out as a confound.
