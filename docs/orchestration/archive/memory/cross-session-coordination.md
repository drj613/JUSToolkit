---
name: cross-session-coordination
description: How the runtime/static/ledger loops coordinate; the protocol lives in docs/orchestration/
metadata: 
  node_type: memory
  type: project
  originSessionId: 8e6163a0-24e4-46e7-890e-b5eb1a8591ff
  modified: 2026-08-18T22:37:02.171Z
---

The JUS RE work runs as self-paced `/loop` sessions that must coordinate: a **runtime**
loop (drives melonDS, measures damage — currently `justoolkit-ed`), a **static** loop
(disassembly, addresses/formulas — `battle-engine-atlas`), and a **ledger** loop
(`justoolkit-87`). Key off ROLES, not names — names drift across restarts (atlas's charter
still says the runtime loop is `justoolkit-06`).

On 2026-08-18 coordination collapsed (runtime went silent a whole session; a bad static
anchor sat untested for 4 wakes; two sessions of damage were measured with a stage gimmick
silently ON while a self-agreeing check reported OFF; numbers/addresses travelled without
their conditions/reachability). Root cause: coordination was a social act, not a protocol
step. Two advisors (Fable, Codex) plus the ledger session converged on a fix, written up
in **`docs/orchestration/`** (README indexes it; `COORDINATION-PROTOCOL.md` is canon).

The design: **beads (`br`, prefix `JUS-`, label `coord`) is the system of record**;
SendMessage is a doorbell. Every wake is a bracket — ingest beads first, flush outbound
before scheduling. Partner-anchor validation is a ≤10-min P0 fast lane. Every measurement
carries its match conditions; every address carries its reachability basis + a one-line
falsification test. Claim lifecycle PROPOSED→…→CROSS_CONFIRMED with RETRACTED/TAINTED and a
3-wake TTL. The ledger loop became an **auditor** of beads, not a commit-message
summarizer. One reminder hook gates flush-before-schedule (needs owner install). See
[[br-jsonl-format]], [[loop-wakeup-pacing]], [[convergent-verification]].

Both loops must **leverage `/codex`** (ask before concluding); atlas does this well, ed had
under-used it. The orchestration docs must reach `master` (or each worktree) before restart
— they're born on branch `re/ability-bitset-not-resistance`.
