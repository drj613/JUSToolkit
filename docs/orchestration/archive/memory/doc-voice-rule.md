---
name: doc-voice-rule
description: All research docs must be rewritten in Opus 4.6 voice via claude -p before committing
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0808c5dd-b8f4-4066-a3c4-01ed6013065c
  modified: 2026-08-17T19:33:44.678Z
---

Any time a research doc is updated or created, pass it through `claude -p` with claude-opus-4-6 to rewrite in Opus 4.6's voice before committing.

**Why:** Owner wants a consistent authorial voice across all documentation in the project.

**How to apply:** After writing or updating any doc in `docs/research/` (or similar), run it through `claude -p` targeting claude-opus-4-6 for a voice rewrite, then commit the rewritten version.
