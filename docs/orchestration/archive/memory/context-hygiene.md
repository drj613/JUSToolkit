---
name: context-hygiene
description: Sessions should delegate heavy work to subagents to keep main context windows lean
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0808c5dd-b8f4-4066-a3c4-01ed6013065c
  modified: 2026-08-17T19:33:47.751Z
---

Keep the main context window clean by delegating heavy work to subagents — file exploration, long analysis, raw output processing. The main context should stay lean for longevity.

**Why:** Prevents premature compaction and lets sessions work longer without losing critical context.

**How to apply:** Use fork subagents or other agent types for anything that produces large raw output. Keep the main thread for coordination, decisions, and concise results.
