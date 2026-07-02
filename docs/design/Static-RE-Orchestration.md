# Static RE Orchestration — Battle Engine Atlas (Overnight Loop Edition)

Loop-executable plan for mapping the full JUS battle engine statically from
`arm9.bin` + overlays, with minimal emulator/GDB time. Designed to run
unattended via:

```
/loop map out the combat engine per docs/design/Static-RE-Orchestration.md — follow its Loop Protocol exactly
```

Target subsystems: damage pipeline, jpower indirect lookup, physics
(velocity/knockback/gravity), hitstun timers, movement, weight, projectile
entity lifecycle, hitbox/projectile **priority system** (move-vs-move,
proj-vs-proj, move-vs-proj overrides), plus whatever the completeness critic
surfaces (guard, SP gauge, throws, supports, switch mechanics).

---

## 1. Success Criteria

### DONE (loop terminates successfully) — ALL of:

1. `gates` all `pass` in state file (Section 5, Stage A acceptance).
2. Work queue empty.
3. `dry_rounds >= 2` — the critic ran twice consecutively without generating
   new work units.
4. `docs/research/Battle-Engine-Map.md` has a section for every subsystem in
   `state.subsystems`, each with status `MAPPED`, `PARTIAL`, or `EXHAUSTED` —
   zero `UNSTARTED`.
5. `docs/research/GDB-Validation-Queue.md` exists; every PLAUSIBLE and
   SPECULATIVE claim in the map has a one-breakpoint validation card.
6. `docs/research/Research-Status.md` updated: every newly CONFIRMED_STATIC
   item moved to its CONFIRMED section with a link to the map.
7. Working tree clean; every iteration's output committed.

On DONE: write the Morning Report (Section 9), do NOT schedule another wakeup.

### BLOCKED (loop terminates with handoff) — ANY of:

- A Stage A gate failed after 2 diagnose-and-fix attempts AND no
  gate-independent units remain in queue.
- 3 consecutive iterations ended in unit failure (any units).
- Git state unrecoverable (merge conflict, corrupted index) — do not force;
  stop.

On BLOCKED: write Morning Report with `## BLOCKED` header, diagnosis, and
exact resume instructions. Do NOT schedule another wakeup.

### Safety stops (hard caps, checked at iteration start):

- `iteration >= 40` → forced wind-down: run synthesis with whatever exists,
  write Morning Report, stop.
- Per-subsystem tracer attempts capped at 3 → status `EXHAUSTED`, move on.
- Per-unit attempts capped at 2 (Stage A units: 3).
- File `scripts/analysis/STOP` exists → finish current commit, write report,
  stop. (Manual kill switch: `touch scripts/analysis/STOP`.)

### Explicit NON-goals (do not drift into these overnight):

- No emulator/GDB execution. GDB work is *emitted as cards*, never run.
- No pushes. No edits to upstream code (`src/`, `lib/`, `scripts/*.sh`).
- No engine implementation. Mapping only.
- No ROM redistribution artifacts: raw disasm dumps and findings stay in
  gitignored `jus_files/analysis/`; only derived documentation is committed.

---

## 2. Architecture (three layers)

```
┌────────────────────────────────────────────────────────┐
│ 1. INDEX LAYER (deterministic, built once, no LLM)     │
│    rom loader · disasm DB · xref DB · query CLI        │
├────────────────────────────────────────────────────────┤
│ 2. AGENT LAYER (subagents: trace → verify → critic)    │
├────────────────────────────────────────────────────────┤
│ 3. CANON LAYER (committed docs)                        │
│    Battle-Engine-Map.md · Research-Status.md updates   │
│    GDB-Validation-Queue.md (the only human work)       │
└────────────────────────────────────────────────────────┘
```

Core principle: **agents never disassemble ad hoc.** The index layer is the
single ground truth; agents query it. Prevents the historical failure mode of
parallel work deriving contradictory "facts" (the ÷7 formula, the 0x00-0x3F
physics hypothesis).

### Seed anchors (known ground truth)

- `0x020784FC` — damage code breakpoint (proven via GDB; in static ARM9, always mapped)
- `0x0924B0` — collision file pointer table · `0x08D4A0` — chr_b identity map · `0x09E780` — koma name table (ARM9 file offsets)
- `0x023D2A74` — character struct pointer chain base
- Character struct: physics region `+0x6A–0xBA`; state flag `+0x78`
  (0x00 air / 0x22 ground / 0xC0 launched); countdown timers `+0x98–0xBA`
- `jus_files/analysis/cheat_addresses.json`, `arm9_tables.json` (prior scans)
- Collision entry fields (per exported JSON): `collisionType, subType,
  extFlags, projectileId, frameStart, durationMult, hitModifier, offsetX/Y,
  positionFlags, width, height, damageFlags, knockback, hitTier,
  hitProperties` — `hitTier`/`projectileId`/`hitProperties` are the priority
  system suspects
- Verified formula: `damage = floor(jpower.damage1 / 5) + (tier - 2)`, nature
  ×1.5 advantage-only
- Overlay caution: y9.bin shows overlays 0 and 1 both load at `0x0214CD20` —
  overlays overlap and swap at runtime. Address queries must carry overlay
  context.

---

## 3. Loop Protocol

The loop is a **ratchet**: each iteration does exactly one work unit, verifies
it mechanically, commits, updates state, schedules the next wakeup. All memory
lives on disk — an iteration must function correctly with zero conversation
context (post-compaction, next morning, new session).

### 3.1 State file

`scripts/analysis/loop-state.json` — committed every iteration. Schema:

```json
{
  "iteration": 0,
  "stage": "A | B_C_D | WINDDOWN | DONE | BLOCKED",
  "queue": [
    {"id": "A2-rom-loader", "type": "tool|gate|tracer|verify|synthesis|critic",
     "priority": 1, "attempts": 0, "depends_on": ["A1-env"], "status": "ready|blocked_dep|done|failed|exhausted",
     "spec": "section ref in this file, e.g. 5.A2"}
  ],
  "subsystems": {
    "damage-pipeline":  {"status": "UNSTARTED|TRACING|VERIFYING|MAPPED|PARTIAL|EXHAUSTED",
                          "tracer_attempts": 0, "claims": {"confirmed": 0, "plausible": 0, "speculative": 0}}
  },
  "gates": {"G1": "pending|pass|fail", "G2": "...", "G3": "...", "G4": "...", "G5": "..."},
  "dry_rounds": 0,
  "consecutive_failures": 0,
  "log": [ {"iter": 1, "unit": "A1-env", "result": "ok", "commit": "abc1234", "note": ""} ]
}
```

If the state file does not exist → this is iteration 0: create it from the
unit catalog (Section 5), full Stage A queue + one tracer unit per subsystem
(status `blocked_dep` on `A6-gates`), commit it, then proceed.

### 3.2 Iteration algorithm

```
1. READ   docs/design/Static-RE-Orchestration.md (this file) + loop-state.json
2. TRIAGE git status. Dirty tree from a crashed iteration →
          commit as "loop: WIP recovery iter N" before anything else.
          Unrecoverable git state → BLOCKED.
3. CHECK  termination: STOP file? DONE criteria? BLOCKED criteria? caps?
          → if any: write Morning Report, final commit, END (no wakeup).
4. PICK   highest-priority unit with status=ready and satisfied deps.
          Queue empty but subsystems unfinished → enqueue critic unit.
5. EXECUTE the unit per its spec (Section 5). Subagents allowed per spec.
          While subagents are in flight, do NOT schedule the next loop wakeup —
          their completion notifications continue this iteration.
6. VERIFY the unit's acceptance criteria MECHANICALLY (run the commands; a
          unit passes only if the commands pass). No self-certification.
7. RECORD pass → status=done, update subsystem statuses, dry/failure counters.
          fail → attempts++, one focused fix attempt this iteration;
          still failing → status=failed, consecutive_failures++,
          log diagnosis, move on next iteration.
8. COMMIT everything the unit produced + state file.
          Message: "loop: <unit-id> <ok|fail> — <one-line result>"
9. SCHEDULE next wakeup 60s ahead (work is continuous; short gap keeps cache
          warm), passing the same /loop prompt. EXCEPTION: step 3 said stop.
```

Sizing rule: one iteration = one ratchet click = the smallest unit that leaves
the repo strictly better and verifiable. A unit too big to finish in one
iteration must be split (edit the queue — that is the orchestrator's job) —
never left half-done uncommitted.

### 3.3 Subagent rules

- Tracers/verifiers run as subagents (they burn context on disasm reading;
  keep it out of the loop's context). Max 6 concurrent.
- Every subagent prompt is **self-contained**: repo path, query CLI usage,
  anchors, schema, output path. Assume the subagent knows nothing.
- Subagent output = files on disk (findings JSON), not prose in the transcript.
  The loop reads files, not memories.

---

## 4. Evidence Integrity (anti-hallucination, non-negotiable)

Overnight, nobody catches a fabricated disassembly quote. Defense:

1. Every claim must cite `addresses[]` + `evidence_disasm` (verbatim query
   output).
2. `scripts/analysis/verify_evidence.py <findings.json>` re-runs the query for
   every citation and string-matches the quoted instructions against actual
   disassembly. **Any mismatch = the whole findings file is rejected** and the
   tracer unit fails (attempts++). This is part of every tracer unit's
   mechanical acceptance criteria.
3. Canon docs are written ONLY from claims that passed evidence verification
   AND the verification lenses (Section 5, verify units). Confidence labels are
   preserved in the docs.
4. Findings JSONs are append-only artifacts in
   `jus_files/analysis/findings/` (gitignored); synthesis reads them fresh
   each time.

---

## 5. Unit Catalog

### Stage A — Index layer tooling (inline coding, no subagents needed)

New code in `scripts/analysis/`. Python 3 + capstone. Venv at
`scripts/analysis/.venv` (gitignore it).

**A1-env** — venv + `pip install capstone`; add gitignore entries for
`.venv/`, `loop artifacts under jus_files/`.
AC: `scripts/analysis/.venv/bin/python -c "import capstone"` exits 0.

**A2-rom-loader** — `rom_loader.py`: parse `y9.bin` (32-byte entries: id,
ram_addr, ram_size, bss_size, sinit_start, sinit_end, file_id, flags), map
`arm9.bin` @ `0x02000000` + all `overlay9_N`. MUST model overlapping overlays
(0 and 1 share `0x0214CD20`): every mapped region tagged with provenance
(`arm9` | `ov<N>`), and lookups for an overlapped address either take an
`--overlay` context or return all candidates.
AC (as pytest or `--selftest`): bytes at `0x02000000` == start of arm9.bin;
overlay 0 maps at `0x0214CD20`; overlapped address without context returns
both candidates; out-of-range address errors cleanly.

**A3-disasm-db** — `disasm_db.py`: capstone sweep of arm9 + each overlay
(ARM and Thumb; heuristic mode selection, literal-pool/data detection).
Function boundaries via prologues (`push {..,lr}`, `stmfd sp!,{..,lr}`) and
epilogues (`bx lr`, `pop {..,pc}`). Emit `jus_files/analysis/functions.json`
(addr, provenance, size, mode, callees, callers) + full disasm text per region
under `jus_files/analysis/disasm/`.
AC: function count in [1000, 20000]; `0x020784FC` falls inside a discovered
arm9 function; the three known ARM9 data tables are NOT classified as code;
runtime < 10 min.

**A4-xref-db** — `xref_db.py`: resolve pc-relative `ldr` literal pools +
immediate struct offsets → `jus_files/analysis/xrefs.json` (code→data,
code→code).
AC: `xrefs-to` the RAM address of the collision pointer table returns ≥1 hit;
`search-imm 0x78` and `search-imm 0x98` return hits (struct offsets are used
somewhere); spot-check one known cheat address resolves.

**A5-query-cli** — `query.py` subcommands: `func <addr>`, `callers`,
`callees`, `xrefs-to <addr>`, `search-imm <val>`, `disasm <addr> <n>
[--overlay N]`, `strings <region>`. This is the ONLY interface tracers use.
AC: every subcommand smoke-tests against a seed anchor; `--help` documents
usage (it gets pasted into tracer prompts).

**A6-gates** — `gates.py` runs all of the above ACs plus anchor plausibility:
disasm at `0x020784FC` decodes ≥10 sequential valid instructions including
data-processing ops. Writes results into state `gates` (G1 loader, G2 disasm,
G3 xref, G4 query, G5 anchors).
AC: exit 0. On fail: diagnose (wrong base? thumb/arm mispick? overlay
overlap?), fix, retry (≤3 attempts total) — else BLOCKED.

**A7-verify-evidence-tool** — `verify_evidence.py` per Section 4.
AC: accepts a hand-made valid findings fixture, rejects a fixture with one
altered instruction.

### Stage B — Tracer units (one subagent each; unlocked by A6-gates)

Nine initial tracers. Dependencies: B2 needs B1 done; B8 needs B5 done; rest
parallel-eligible (but the loop still runs ONE unit per iteration — a unit
may launch its single tracer subagent and, while waiting, that's the
iteration's work).

| ID | Subsystem | Entry point | Question set |
| --- | --- | --- | --- |
| B1 | damage-pipeline | `0x020784FC` | Locate ÷5, tier±1, nature ×1.5 in code; input/output structures |
| B2 | jpower-indirect | B1's traced block + jpower buffer xrefs | damageFlags=0 → jpower entry resolution (JUS-9lp.1; blocks 64/74 chars) |
| B3 | hitbox-priority | consumers of `hitTier`/`hitProperties`/`projectileId` | Clash resolution: is hitTier the priority value? move-vs-move, proj-vs-proj, move-vs-proj; tie behavior |
| B4 | projectile-entities | `projectileId` consumers; entity list mgmt | Spawn/despawn, ownership, persistence after switch (traps/summons) |
| B5 | physics-writers | writers of struct `+0x6A–0x7C` | Velocity fields; knockback impulse (collision `knockback` consumer); gravity/decay |
| B6 | hitstun-timers | writers of struct `+0x98–0xBA` | jpower.hitstun → timer init mapping; hitstun vs recovery timer |
| B7 | movement | statC consumers | Threshold `cmp` values → closes JUS-n3p with zero human testing; dash/flash-dash |
| B8 | weight-hunt | knockback code from B5 + `arm9_tables.json` candidates | Weight table location (JUS-cb0.1); check passive-system routing (Edajima lesson) |
| B9 | collision-data-miner | NO disasm — all 74 collision files + jpower.json | `hitTier`/`projectileId` distributions vs known gameplay overrides; cross-evidence for B3 |

**Tracer subagent prompt template** (fill {…}):

> Repo: /Users/djdjo/Documents/mine/JUSToolkit. Static RE of NDS game battle
> engine. Your ONLY disassembly interface:
> `scripts/analysis/.venv/bin/python scripts/analysis/query.py …` — usage:
> {paste query.py --help}. Do not disassemble by other means.
> Known ground truth: {relevant seed anchors + prior confirmed claims for this
> subsystem}. Question set: {subsystem questions}.
> Method: start at the entry point, expand via callers/callees/xrefs-to,
> follow data flow. Small steps; verify each hop.
> Every claim MUST cite addresses and verbatim query output as evidence —
> your findings will be machine-checked against the database and rejected on
> any mismatch. Unresolvable questions go in open_questions, never guessed.
> Write findings to jus_files/analysis/findings/{subsystem}.round{N}.json
> with schema: {schema}. Your final message: 5-line summary + path.

Findings schema:

```json
{"subsystem": "...", "round": 1, "claims": [{
  "claim": "hitTier compared at 0x0207XXXX; higher value wins clash",
  "addresses": ["0x0207XXXX"],
  "evidence_disasm": "0x0207XXXX: ldrb r2,[r4,#0x10] | 0x0207XXXX+4: cmp r2,r3 | ...",
  "confidence": "CONFIRMED_STATIC | PLAUSIBLE | SPECULATIVE",
  "gdb_check": "break 0x0207XXXX; confirm r2 == attacker hitTier",
  "open_questions": []
}], "no_progress_reason": null, "suggested_next_angles": []}
```

Tracer unit AC (mechanical): findings JSON exists, parses, schema-valid;
`verify_evidence.py` passes; ≥1 claim OR `no_progress_reason` +
`suggested_next_angles` populated (feeds the critic). On AC pass →
subsystem status `VERIFYING`, enqueue a verify unit. `tracer_attempts++`
regardless; 3 attempts without any verified claim → `EXHAUSTED`.

### Stage C — Verify units (three subagents per findings batch)

Three lenses, distinct prompts, run concurrently:

1. **disasm-correctness** — re-query every citation; does the code actually
   compute the claim?
2. **aliasing** — could the field/address serve a different purpose? (Timers
   were historically mistaken for velocity.) Propose the strongest alternative
   explanation and test it against the disasm.
3. **data-consistency** — does the claim survive the actual data? (e.g.,
   claimed priority rule vs `hitTier` values across all 74 collision files;
   claimed formula vs verified damage table in Research-Status.md.)

Each returns per-claim verdicts `{claim_idx, verdict: UPHELD|REFUTED|UNSURE,
reason}` to `jus_files/analysis/findings/{subsystem}.round{N}.verdicts.{lens}.json`.

Scoring: ≥2 REFUTED → claim demoted to SPECULATIVE + gdb card required.
All three UPHELD → claim may keep CONFIRMED_STATIC. Otherwise → PLAUSIBLE.
AC: verdict files exist for all three lenses, every claim has 3 verdicts,
scoring applied and recorded in state. Subsystem → `MAPPED` (≥1 confirmed,
no open questions), `PARTIAL` (some confirmed/plausible, open questions
remain), else stays `TRACING` for another round or `EXHAUSTED` at cap.

### Stage D — Synthesis and critic

**D1-synthesis** (re-enqueued whenever ≥2 subsystems changed status since last
run, and always before DONE/wind-down): rewrite
`docs/research/Battle-Engine-Map.md` from verified claims only (routine
tables, data flow, formulas, per-claim confidence). Update
`Research-Status.md` (move CONFIRMED_STATIC items). Regenerate
`GDB-Validation-Queue.md` — every PLAUSIBLE/SPECULATIVE claim gets its
one-breakpoint card, grouped to minimize emulator sessions.
AC: map has a section per subsystem; zero references to rejected claims; all
intra-doc links resolve; committed.

**D2-critic** (runs when queue is empty): one subagent reads the map + all
findings + this file's target list, answers: which battle-loop subsystems have
no claims? which open_questions and suggested_next_angles justify a new tracer
round with a NEW angle (never repeat a failed approach verbatim)? Output: list
of new tracer unit specs. Loop enqueues them (respecting the 3-attempt cap).
Zero new units → `dry_rounds++`; any new units → `dry_rounds = 0`.

---

## 6. Pacing

- Next-unit wakeup: 60s (continuous work, warm cache).
- Waiting only on in-flight subagents: no wakeup needed — completion
  notifications resume the iteration. Belt-and-suspenders fallback wakeup
  1200s in case a subagent dies silently.
- DONE/BLOCKED: no wakeup. The loop ends itself.

## 7. Pre-flight checklist (human, before bed)

1. Phase 0+1 cleanup agent's commits reviewed (or at least not conflicting —
   loop touches only `scripts/analysis/`, `jus_files/analysis/`,
   `docs/research/Battle-Engine-Map.md`, `GDB-Validation-Queue.md`,
   `Research-Status.md`, state file).
2. Permissions: session must be able to run `python3`/venv pip, `git add`
   / `git commit`, `mkdir` without prompting (acceptEdits or allowlist;
   consider running `/fewer-permission-prompts` first). Push stays blocked —
   loop never pushes.
3. Disk: disasm dumps ≈ tens of MB under `jus_files/analysis/` (gitignored).
4. Kill switch: `touch scripts/analysis/STOP`.

## 8. Failure playbook (for the loop itself)

- Unit fails once → one focused fix attempt in-iteration.
- Fails again → log diagnosis in state, move to next ready unit. Counter
  `consecutive_failures` resets on any success; at 3 → BLOCKED report.
- Subagent returns garbage/empty → counts as unit failure; re-dispatch with
  the diagnosis appended to its prompt (max attempts still apply).
- Evidence verification failure → treat as tracer failure, never "fix" the
  evidence by hand.
- Compaction mid-iteration → step 1 of the algorithm restores everything from
  disk; a WIP-recovery commit covers crashed writes.

## 9. Morning Report

Final iteration writes `scripts/analysis/loop-report.md` (committed):

- Outcome: DONE | BLOCKED | CAP-STOP + iteration count
- Per-subsystem table: status, confirmed/plausible/speculative claim counts,
  headline finding (one line each)
- Top 5 discoveries by impact (e.g., "hitTier clash rule found at 0x…")
- GDB validation queue size + estimated human minutes
- Open questions the next campaign should chase
- Full iteration log (from state file)
