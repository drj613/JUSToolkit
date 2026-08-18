# Loop Charter: Atlas (combat engine + koma system)

This file is the standing instruction set for a self-paced `/loop`. Each wake: re-read this
file (it may have changed between wakes) and `scripts/analysis/loop-state-atlas.json`, do ONE
task, commit, update state, schedule the next wake.

## North star

`docs/PROJECT-GOAL.md` (on `master`, commit `f47d63d`) is the project goal this loop serves:
document JUS battle mechanics thoroughly enough to **rebuild the system in a new game**, and pin
down deckbuilding and koma for reimplementation. "Thoroughly enough" means field-level struct
detail, control flow, arithmetic formulas, and edge cases — enough for an engineer who has never
seen the original code to write a faithful recreation. Not architecture diagrams.

Two sessions work toward this. **justoolkit-06** (on `master`) runs runtime experiments through
the agentic melonDS harness and serves as this loop's **runtime validator**; this session handles
structural static analysis. Coordinate directly — send a struct-field hypothesis or function
address and ask for a breakpoint instead of leaving it unresolved. That is the only way this loop
gets dynamic evidence without breaking its static-only rule.

Note: `PROJECT-GOAL.md` lives on `master`, not on this branch, so it won't be in this worktree
unless merged.

## Mission

Two goals, ordered by finish-ability:

1. **Koma sprint (finish first — it's bounded):** understand the deckbuilding / koma system
   well enough to write `docs/design/Koma-System-Design-Brief.md` — a doc a designer with no
   RE background could use in a design session. Cover: the 5×4 grid, koma sizes/shapes,
   panel types (help/support/battle), nature system and deck bonuses, costs/limits, how koma
   map to on-disk data (`extracted_chrbin`, komas.bin/pcm.bin or wherever the shape+cost data
   lives), and what's still unknown. Existing partial docs: `Deck-System.md`,
   `Koma-Research.md`, `Deck-Memory-Structure.md`, `Character-Mapping.md`.
2. **Combat engine (open-ended, runs until stopped):** deepen `Battle-Engine-Map.md`.
   **Current focus (iteration 146 onward): entity and projectile subsystems** — entity pool
   layout and lifecycle, projectile struct fields (spawning, ownership, collision), how
   entities relate to the MoveMan system mapped in iterations 136–139, and the vtable hierarchy
   for projectile/entity classes. Known entry points: `Battle_ObjManCreate` arm9 `0x0208321C`
   (`0x42D8`, `BattleObj.cpp`), `Battle_ObjShotManCreate` ov6 `0x0216A7D4` (`0x3FD4`,
   `BattleObjShot.cpp`), `Battle_ObjCtrlManCreate` ov6 `0x02168BA0` (`0x314`), and the
   pooled-entity constructor `0x020834D4` with its wrapper `0x02083624`.
   Standing priorities behind that: (a) the two least-resolved subsystems, hitbox-priority and
   physics-writers; (b) Tier-2 plan tasks D0.1 and D0.2 from
   `docs/design/Decomp-Tier2-Plan.md` (overlay map, function denominator) — they unblock
   everything downstream; (c) any GDB-Validation-Queue card that can be settled statically.
   Cards that truly need a live debugger go to `Human-Testing-Queue.md` — this loop runs
   unattended and must NOT assume melonDS is up.

## Required reading for any koma task

`docs/research/Koma-System-Observed-Behavior.md` — ground truth from a live play session
(25 screenshots in `docs/research/assets/koma-ui/`). Tier **OBSERVED**: it outranks
CONFIRMED-from-disassembly for *behavior* but says nothing about byte layout. It carries the
falsifiable predictions K2 must check, including the nature enum (力/知/笑/なし) and the
Naruto 4力-vs-4笑 test case. Designer-facing twin:
`docs/design/Koma-Deckbuilder-UX-Spec.md`.

## Hard rules

- **One task per wake.** Small, committable, verifiable. Commit message prefix `loop-atlas:`.
- **Stay static.** No emulator, no GDB. Evidence comes from `scripts/analysis/query.py`
  (func, callers, callees, xrefs-to, search-imm, search-op-imm, disasm, strings,
  pool-values), the JSON DBs in `jus_files/analysis/`, and the extracted files in
  `jus_files/`. Never modify anything under `jus_files/ripped_jus_files/`.
- **Protect the main context.** The orchestrator never Reads disassembly, large JSON, or
  binary dumps directly. All heavy reading goes to subagents that return short summaries.
  Keep per-wake orchestrator output under ~2k tokens.
- **Evidence discipline** (carried over from Phase 0): every claim gets a confidence label
  (CONFIRMED / PLAUSIBLE / SPECULATIVE) and a pointer to the query.py command or file offset
  that supports it. Refuted hypotheses get recorded, not deleted.
- **Convergent verification** (owner rule, standing as of 2026-08-18). For any load-bearing
  decode or address claim, actively seek a second method that works in a **different
  representation** — relative displacement against absolute address, encoding-table
  arithmetic against an empirical ROM sweep, byte offset against instruction index.
  Agreement across representations cannot be shared bias, so it is the strongest
  confirmation available under static-only rules. Disagreement is equally useful: one side
  is wrong and the discrepancy usually says which. This is strictly better than running the
  same tool twice or having a checker agree from the same angle.
  - Worked example, iteration 149: Codex decoded `EB00034E` relatively as a branch to
    `A + 0xD40` with no address context, `query.py` reported the absolute target
    `0x0215305C`, and `0x0215231C + 0xD40` = `0x0215305C`. That agreement validated the
    window's *placement*, which neither tool could establish alone.
  - **Ask the independent checker BEFORE forming your own conclusion**, not after. Same
    iteration: concluding first would have hidden a halfword I had mis-transcribed
    (`0x6668` for `0x66bc`) — asking first got the inconsistency flagged instead of
    decoded around.

## Delegation plan (use subagents for everything heavy)

- **Scanning / searching** (find xrefs, sweep files, grep formats): `Explore` or
  `general-purpose` subagents with `model: "sonnet"`. Fan out 2–3 in parallel when the
  sub-questions are independent.
- **Synthesis / adversarial verification**: `general-purpose` with `model: "opus"`. Reuse the
  Phase-0 3-lens pattern — for each batch of claims, run three verifiers with different
  lenses (disasm re-check, aliasing/alternative-explanation, data-consistency) and mark
  CONFIRMED only on agreement.
- **Second opinion**: when a subsystem conclusion is about to land in canon docs, or when
  stuck two wakes in a row on the same question, invoke the `codex:rescue` skill (or the
  `codex:codex-rescue` agent) with the specific claim + evidence and ask it to confirm or
  refute independently.
- **Editing pass (mandatory, opus-4-6 specifically):** any time a doc under `docs/` is
  created or substantially changed, run it through a headless claude call pinned to
  claude-opus-4-6 (the Agent tool can't pin a version, so use Bash):

  ```
  claude -p --model claude-opus-4-6 \
    "Rewrite the following doc in your own voice for brevity and clarity. Plain words, \
  smart-11th-grader register. Preserve every address, hex value, confidence label, file \
  path, and table exactly. Cut filler, keep substance. Output ONLY the rewritten markdown, \
  no preamble." < DRAFT.md > EDITED.md
  ```

  Draft to the scratchpad, diff EDITED against DRAFT to confirm no addresses or hex values
  were dropped (e.g. compare `grep -oE '0x[0-9A-Fa-f]+' | sort` output of both), then write
  the edited version into `docs/`. If the call fails (model unavailable, auth), keep the
  draft, note the skipped pass in the commit message, and retry next wake.

## State

`scripts/analysis/loop-state-atlas.json`:
`{ "iteration": N, "phase": "koma" | "combat", "queue": [...], "done": [...], "stuck": {...} }`

Seed queue (do in order unless blocked; add new tasks as they come up):

1. `K1-koma-data-survey` — subagents inventory where koma shape/size/cost/nature data lives
   on disk and what tooling already parses it (check `src/`, `extracted_chrbin`, JUSToolkit
   converters). Output: short findings file `docs/research/findings/koma-data-survey.md`.
2. `K2-koma-format` — decode the koma data format(s) found in K1; cross-check 3+ known
   characters against the wiki-known facts already in `Deck-System.md`.
3. `K3-koma-runtime` — how deck/koma data reaches battle: tie to `Deck-Memory-Structure.md`,
   chr_b record access (`*(0x0214BD80)+0x40`, stride 0x3C), and PassiveIndex nuance from
   Research-Status.
4. `K4-design-brief` — write `docs/design/Koma-System-Design-Brief.md` (then opus edit pass).
   This closes the koma sprint; flip phase to "combat".
5. `C1-overlay-map` — Tier-2 task D0.1 exactly as written in Decomp-Tier2-Plan.md.
6. `C2-function-denominator` — Tier-2 task D0.2.
7. `C3-hitbox-priority-round2` — re-mine hitbox-priority with the Phase-0 findings as
   priors; 3-lens verify; update Battle-Engine-Map.md.
8. `C4-physics-writers-round2` — same for physics-writers.
9. `C5-gdb-queue-triage` — sweep `GDB-Validation-Queue.md`; settle statically what can be
   settled, move the rest to `Human-Testing-Queue.md` with sharpened one-breakpoint cards.
10. `C6+` — self-generated: pick the highest-value open question in Research-Status.md,
    write it into the queue with a one-line success criterion, then do it next wake.

## Pacing and budget

- **Default fallback delay ~1800s (30 min).** That's the user's stated preference; don't drift
  longer without a reason. Even if the next task is obvious and nothing is blocking, still do
  only one task per wake.
- If two consecutive wakes make no progress on the same task, mark it `stuck`, bring in
  codex for a second opinion once, and if still stuck, skip it and note why in
  Research-Status.md.
- Every ~8 iterations (or when flipping koma→combat), write a short progress note to
  `docs/research/Research-Status.md` (dated section, opus edit pass applies).

## Stop conditions

Stop the loop (`ScheduleWakeup stop: true`) when ANY of:
- a file named `scripts/analysis/LOOP_STOP` exists (the user's kill switch — check first
  thing every wake),
- the koma brief is done AND the queue is empty AND two attempts at self-generating C6+
  tasks produced nothing worth doing,
- 4 consecutive wakes with no committed progress.

On stop, write a final summary section in Research-Status.md.
