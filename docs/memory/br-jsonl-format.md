---
name: br-jsonl-format
description: br rejects legacy uppercase bd ids only on the IMPORT path — fix by routing through the db-backed .beads, not by lowercasing
metadata:
  node_type: memory
  type: project
  originSessionId: a60267d0-17d9-454b-bb1e-16e9dda33cfb
  modified: 2026-08-18T22:49:24.192Z
---

`bd` is now `br` (beads_rust; 0.2.19 as of 2026-08-18) — same binary, symlinked. It has
TWO code paths with different strictness, and this is the key to the "Preflight checks
failed: N invalid issue record(s): id: invalid format (expected prefix-hash)" error:

- **db-backed path** (list/create/update/export, i.e. `br sync --flush-only` when a
  `beads.db` is present): TOLERATES the legacy uppercase `JUS-xxx` ids. Works fine.
- **import path** (no `beads.db`, so br must import `issues.jsonl` to build state):
  REJECTS uppercase ids as invalid format.

So the failure is not "the data is corrupt" — it's "br was forced down the import path."
That happens in a **git worktree that tracks its own `.beads/` but has no `beads.db`**
(e.g. `ledger/session-tracker`). Worktrees whose branch does NOT track `.beads` (e.g.
`battle-engine-atlas`) work fine because br walks up to the main repo's db-backed
`.beads`.

**Correct fixes (in order of preference):**
1. Route through the main repo's db-backed `.beads`. The committed pre-commit hook
   (`.git/hooks/pre-commit`, rewritten 2026-08-18) now `cd`s to the main repo root before
   `br sync --flush-only` and never hard-blocks a commit on a flush hiccup. Run manual
   flushes from the main root too.
2. Durable: **don't track `.beads` on worktree branches** — `git rm -r --cached .beads`
   on such a branch so its worktree falls through to the main `.beads`.

**Do NOT blindly `sed 's/JUS-/jus-/'` the jsonl** (the old advice here). The canonical
`beads.db` uses uppercase ids; lowercasing only the jsonl forks it from the db, and the
next export rewrites uppercase anyway. Lowercasing is only right as a full one-time
migration of db + jsonl + config + all dependency/comment refs together — not a quick fix.

br is non-invasive (never auto-commits, unlike old bd) — that's why the pre-commit flush
must degrade to a warning, not block. See [[bd-to-br-migration]] and
[[cross-session-coordination]].
