---
name: loop-wakeup-pacing
description: "Default /loop wakeup delay is ~30 minutes (1800s), not longer"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0a7773fe-cf57-42c6-b4b3-d4a6ffae4404
  modified: 2026-08-14T14:23:56.158Z
---

Default `ScheduleWakeup` delays to ~1800s (30 min) for this project's loops. The Atlas
charter originally said "lean toward 3600s"; the user overrode that to ~30min.

**Why:** the user wants to see loop progress at a reasonable cadence rather than optimizing
purely for token usage.

**How to apply:** use 1800s as the default fallback heartbeat unless there's a specific reason
to wait longer. The charter at `docs/research/Loop-Charter-Atlas.md` has been updated to match.
Related: [[koma-system-observed-behavior]]
