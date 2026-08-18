# Session Ledger — JUS Reverse Engineering

Last updated: 2026-08-18 ~20:15 (ledger wake 1, session `justoolkit-87`)

## 1. Current state

This file is a human catch-up summary — not the system of record. beads (`br`) is the record; protocol in `docs/orchestration/`.

**Live sessions (from ListAgents):**
- `justoolkit-fa` [cedb9e] — busy, just started. **Runtime** role, branch `re/ability-bitset-not-resistance`.
- `battle-engine-atlas-76` [2e8ac4] — busy, just started. **Static** role, branch `loop/battle-engine-atlas`. Atlas now at **P164**.
- `justoolkit-d9` [699d1d] — idle 58 min. Protocol-design coordinator from earlier; unclear if it will persist.
- Two `test-suite-guardrails` sessions — not part of coordination.

Previous instances (`justoolkit-ed`, `battle-engine-atlas-5e`) have been replaced. The protocol doc's role table still names the old ones — it says "always resolve via ListAgents" which is correct.

**Coord beads exist (4 open).** See jus-f0v, jus-ovv, jus-6fo, jus-1g6. All carry the `coord` label. **None carry structured `kind:*` / `state:*` / `owner:*` labels** — the protocol's label schema isn't enforced yet. Content is good; machine-sweepable metadata is missing.

## 2. Open audit flags

### Flag A — Coord beads missing structured labels
All four coord beads have only the `coord` label. The protocol requires `kind:*`, `state:*`, `owner:*` labels for mechanical sweep (aging, TTL, taint propagation). Without them, every audit check is manual. **Action needed:** whichever loop next touches a coord bead should add the labels per the protocol's write convention.

### Flag B — jus-1g6 is an aging request
"Tell atlas: 0x020AFEA0 is CONFIRMED the rule mode" is a `kind:request` that hasn't changed status since creation. Atlas just restarted (`battle-engine-atlas-76`) — this should be in its ingest queue on its first wake. If it's not picked up by atlas's next completed wake, this flag escalates.

### Flag C — Gimmick contamination taint not propagated (carried forward)
`7145505` revealed the gimmick toggle was never off. jus-f0v was created to re-run the two-move proof, but no taint beads link contaminated measurements to the fix. The flat-damage and resistance-null results *probably* hold (gimmicks spawn projectiles, not alter base damage), but this hasn't been formally re-verified. No back-propagation has happened.

### Flag D — Atlas retractions without tainted dependents (carried forward)
- P158 "stat block" label refuted in P160. No downstream bead marked tainted.
- P154 struct-base claim refuted in P155. Same.
These are low-severity — no downstream findings explicitly depended on them — but the protocol requires explicit taint marking.

### Flag E — Stale pending asks (carried forward, aging)
1. ObjShot kind-byte walk — requested pre-handoff, still open. Runtime has nav working so it's unblocked.
2. Nature resolver in ov06 — atlas was asked to check if ov06 has its own nature reader. No commit addresses this. Still open.
3. Mode-ID byte read and overlay residency re-measure — may be moot after ov05 closure, status unclear.

## 3. Role change

Your predecessor was a pull-based commit-message summarizer. You are now the **auditor** of the beads-backed coordination protocol. Each wake:
1. `br list --label coord` + `git log` on both branches.
2. Update this narrative file — keep it lossy, link bead IDs instead of duplicating data.
3. **Flag coordination inconsistencies:** retractions without tainted dependents, requests aged past one wake with no status change, measurements missing conditions, claims past 3-wake TTL, `CROSS_CONFIRMED` claims missing linked runtime evidence.
4. Nudge idle loops. Relay owner direction. Spin up Fable subagents for blocking questions.
5. You do NOT write findings, addresses, or measurements.

Full charter: `docs/orchestration/Charter-Ledger.md`. Protocol: `docs/orchestration/COORDINATION-PROTOCOL.md`.

Until ed and atlas adopt the beads protocol (on their next restart), fall back to the old method: `git log` + commit messages.

---

# Session Ledger

What each active session is doing, where things live, and what they've delivered.
Last updated: 2026-08-18 20:15 — ledger wake 1 (auditor mode)

## Ultimate goal

Lock down JUS battle mechanics well enough to rebuild the system in a new game. Also pin down how deckbuilding and koma systems work for a head start on reimplementation. See `docs/PROJECT-GOAL.md`.

---

## Session 1: Runtime — `justoolkit-fa` [cedb9e] (was `justoolkit-ed`)

**Focus:** Runtime research via the agentic melonDS harness.

**Status:** Just started (fresh instance). Branch `re/ability-bitset-not-resistance`. Items 1–3 done, item 4 (full match playthrough) not started. Latest commit on branch: `e3c3737` (orchestration hooks).

**Assignments:**
1. ~~Resistance attribution~~ — **SETTLED** (both directions null)
2. ~~Harden menu nav~~ — **DONE** (touchscreen taps + pixel verification)
3. ~~Deck creation~~ — **DONE** (`ae6e8c4`): builds a full deck unattended, game grades it. Measured off framebuffer.
4. Full match playthrough — boot to finish, pulling RAM data throughout
5. Projectiles / ObjShot kind-byte walk (queued, unblocked now that nav works)

**This-session findings:**
- **Resistance SETTLED both directions null:** Setting bit 9 on a non-resistor = no change. Clearing bit 9 on real Luffy resistor (chr_b[12], abilities [9,25,12,14]) = no change (352 raw, 12 runs). entity+0x128 bitset is NOT read for damage scaling. Per-character defence value is the leading hypothesis.
- Entity addresses: player `0x022286E0`, opponent `0x0224E1E0` (Goku), Luffy opponent entity `0x022441E0` bitset `0x02244308`
- Convergent verification: entity+0x128 fits atlas's static 8-byte gap between char+0x120 and char+0x130 — runtime bitset at +0x128–+0x12F collides with neither sub-object. ~~vtable 0x0215D3B4~~ corrected to inline function pointers (`4ad036d`)
- Auto-Guard (bit 4) zeroes out damage completely — instrument is live
- **Headless screen capture:** `screen.dump(path)` patched into melonDS-lua, writes 256x384 PPM from GPU framebuffer. `jusemu.py screendump`. Commit `be007f1`.
- **Menu nav fixed:** Top menu is 4x2 icon grid, cursor starts on デッキメイク not Jギャラクシー. Old "one RIGHT" was walking into deck editor. Now using absolute touchscreen taps + per-screen pixel verification. Six screens learned.
- **Caution:** DOWN+B used in Damage-Reduction-Is-Flat.md may be "Forced Change" per the guide — move labelling needs second look (flat conclusion still holds)
- **Caution:** Rapid savestate loads intermittently hang melonDS (JIT block cache reset)
- **MILESTONE — ov05 contradiction CLOSED** (`9f836c2`): deck-make editor = ov05 (99.5%), deck-select list = ov01 (99.6%). Old measurement was correct, label was wrong (nav bug). Reusable tool: `scripts/emu/overlay_residency.py`. Doc: `docs/research/Overlay-Residency-Deck-Screens.md`.
- **NATURE RESOLVER HYPOTHESIS:** `0x0214E480` is ov05 code — reachable on deck-make screens, NOT during battle (where ov06 occupies that window). The twice-confirmed "nature doesn't affect battle damage" may be because the resolver is the EDITOR's, not the battle engine's. Testing: find what reads nature with ov06 resident (atlas's side).
- **MILESTONE — Deck creation DONE** (`ae6e8c4`): builds a whole deck unattended, game grades it. Measured off framebuffer (`d7afa94`). Research doc on editor signals (`6adcad7`).
- **Gimmick toggle fix** (`7145505`): toggle was never actually off — verification check agreed with itself (self-confirming bug).

**What the previous session built (all committed on master):**
- Emu harness M1-M3: `scripts/emu/` (agent_bridge.lua, launch/stop scripts, joypad patch, JSON plans)
- Damage research: all 8 callers in ov06, flat reduction (-2), base 8.000, nature doesn't affect battle
- Nature consolidation: `docs/research/Nature-System-Consolidated.md`
- Codex cross-check of the damage path: `0683ae0`
- Key docs: `docs/research/HP-And-Damage-Runtime-Findings.md`

**Latest master commits:**
- `0683ae0` docs(re): Codex cross-check of the damage path
- `f47d63d` docs: add PROJECT-GOAL.md + beads gitignore cleanup
- `2027816` docs(re): consolidate nature findings from both sessions

---

## Session 2: Static — `battle-engine-atlas-76` [2e8ac4] (was `battle-engine-atlas-5e`)

**Focus:** Structural static analysis of the battle engine.

**Branch location:** `.claude/worktrees/battle-engine-atlas/`

**Status:** Just started (fresh instance). Branch `loop/battle-engine-atlas`. Now at **P164**. Handoff doc written at `55651d6`. Latest research commit: `c8da30a` (P164 — mode classifier in ov1, 16-byte-per-mode descriptor table).

**Assignments:**
1. Entity and projectile subsystems (structural analysis)
2. Support justoolkit for deck creation and match playthrough (provide addresses, struct layouts)

**What the previous session mapped (all committed on branch):**
- ColPrm manager (0xFB54 bytes, 128 inline records, phase table, 19 handlers)
- MoveMan system (two 128-element arrays, per-frame snapshot, NoteTracks)
- Allocator (4th arg = __LINE__, CommonEffect 3-deep class hierarchy)
- Vtable hierarchy (4 deep, Clone/dirty-flag/facing bit)
- Record lifecycle (+0x34 runtime flag API, 0x6FF solved, +0x150 is highest-value unknown)
- Charter updated to reference PROJECT-GOAL.md (`8aab44d`)
- P146c: confirmed 0x40 element stride, entity call sites are map-item/obj-ctrl, projectiles = BattleObjShot
- P147: ObjShot manager fully mapped — `Battle_ObjShotManCreate` at `0x0216A7BC`, singleton `0x021729EC`, 72 elements of 0x6C bytes, 27-entry kind dispatch table at `0x02172864`. Doc: `docs/research/findings/objshot-manager-and-the-27-kind-dispatch-table.md` (`6e2a058`)
- P147b: ObjShot reachability CONFIRMED via Thumb BLX (`aaf46a3`). ~~Initially published as novel blind spot~~ — retracted, this was a re-derivation of findings from iterations 95–96 (`findings/thumb-caller-audit.md`). The real revision: `find_thumb_callers.py --audit` under-reports vs `--to` due to a plausibility heuristic (line 184); the 187 ROM-wide / 16 in-battle counts are a **floor**, not a census. Use `--to` on specific addresses to clear reachability.
- Better ObjShot anchor: battle root pointer `0x0214D928` → `[root+0x110]` = ObjShot manager, `[root+0x10C]` = ObjCtrl manager. More robust than hardcoded singleton. (`d1c8c3c`)

**Latest atlas commits:**
- `474b2b7` **P163: whole rule-select screen mapped to memory. `+0x2D` = team battle. Time limit is a frame count.**
- `9fd7c4a` P162: `0x020AFE90` is match-settings struct. Third unnamed rule flag. Two disassemblers print opposite literal comments.
- `d247318` P161: `0x0214D928` is a pool word, not a global — root confirmed. Repeated process mistake noted.
- `20aee41` P160: `[0x02172960]` is 368-byte ov6 object, P158 "stat block" label refuted. xrefs.json misses 89% of Thumb literal loads.
- `3ed2633` P159: complete 42-entry effect-id table, both selection routes. Status subsystem cleared of chain scaling.
- `a747eca` P158: status dispatcher `0x02158ED0` mapped. `[param+0x4]` is static table data, not computed. First non-constant formula found.
- `1b97d3b` P157 follow-up: closed a dropped Codex check honestly; noted backgrounded commands die at turn end.
- `8da841a` P157: ov6 `0x02171168` dispatch table names every status handler. Found the missing `0x20`. Rules out a chain multiplier at the HP boundary.
- `510f46d` P156: ov05 conflict officially closed as labelling error; aliasing hypothesis true but not load-bearing; cold Codex decode corroborates nibble layout, corrects a 'copy' claim.
- `2f24a65`: owner ground truth on dream-attack tap chains, support summons, chain-length damage scaling; multiplier hunt queued.
- `9fd3ed5` P154: session object at 0x021AA0D8 (0x1CB4 bytes), ov7 init/teardown. Census hypothesis dead by construction.
- `8e1b9f0` P153: 47-caller predicate = network-session test; 0x0214CCF8 only ov7/ov10, never arm9.
- `37e7302` P152: descriptor path traced to 47-caller null-test predicate; third index blind spot (9.4% arm9 literal loads); retracted 97.3%.
- `fdc4448` P151: cmp/mov fix reveals three descriptor paths in chara setup loop; corrects a CONFIRMED claim; loop bound converges on P147b's battle root.
- `5bb4ebf` P150: deck+0x30's last Thumb candidate stores zero — claim closed. Fixed thumb_disasm.py cmp/mov bug.
- `bf5a6de` P150: vtable correction, entity+0x128 gap convergence, ov05 misidentified-screen hypothesis.
- `f4881ae` voice pass on convergent-verification charter rule.
- `ce2fd2c` / `1170fb8` P149b: Independent decode confirms encoding ceiling + voice pass.
- `dbb3b45` / `3bb3c32` P149: Thumb store encoding ceiling analysis. B11 and deck+0x18EC are armoured. 3/7 vestigial claims cleared. record+0x68 false-positive confirmed. deck+0x30 narrowed to single candidate `0x0206BB44`.
- `a1ba2e8` P148: fixed find_thumb_callers.py — narrow adjacent-call window + silent audit gate. **187→340 confirmed ROM-wide, 15→31 in ov6.**
- `044a1bd` P147c: record+0x34 two 4-bit fields = team/side filter, not nature. record+0x3C low nibble = resistance-category lead.
- `401073b` P147c: mode-ID global hunt queued, entity+0x10 cross-check
- `d1c8c3c` retraction + --audit correction
- `aaf46a3` P147b: ObjShot reachability confirmed via Thumb BLX
- `6e2a058` P147: ObjShot manager and the 27-kind dispatch table
- `4231eb9` P146c: runtime confirms 0x40 element stride; projectiles are BattleObjShot
- `8aab44d` charter: add PROJECT-GOAL.md north star + entity/projectile focus
- `141a151` P146: record+0x34 runtime flag API (solves 0x6FF); 0x800 is category routing

**Pending runtime asks (relayed to justoolkit-ed):**
1. Walk ObjShot active list at manager+0x00 during a projectile move, log each element's +0x1A kind byte (unblocked now that nav works)
2. When mode-ID byte is found: read its value on deck-select vs deck-make vs koma browser to resolve atlas's ov05 contradiction
3. **NEW:** Re-measure overlay residency on the pixel-verified deck-MAKE screen (and koma browser if reachable). Atlas predicts ov05 >90%, ov01 drops. Fits naturally into deck creation work.

**Active coordination:** Atlas queued a static hunt for candidate mode-ID globals (overlay-load call sites, small-constant writes). Will send candidate addresses if found.

### Campaign history (cumulative)
1. **Phase 0** — Static RE: collision export, projectile verification, trampoline sweep, CHRB catalog, guard/SP gauges → Battle-Engine-Map.md, 31-card GDB queue
2. **Phase 1** — GDB live-discovery, HTML guide + macros
3. **Tier 2 / Koma** — koma.bin layout, kshape.bin decode, nature system, helper-passive taxonomy, HP bonuses
4. **P118–P146c** — ColPrm manager, allocator RE, MoveMan system, element struct naming, entity/projectile identification
5. **P147** — ObjShot manager: singleton, element layout, 27-kind dispatch table, free/active linked lists

---

## Coordination plan

**Standing arrangement:** justoolkit is the runtime arm (emu harness, breakpoints, controlled experiments). Atlas is structural analysis (static RE, struct mapping, vtable tracing). They coordinate directly via cross-session messages.

### Active work: projectiles/entities
Both sessions are pointed at the entity/projectile system. Atlas identifies structs and addresses; justoolkit validates at runtime.

### Stretch goals
- [x] **Deck creation** — DONE (`ae6e8c4`)
- [ ] **Full match playthrough** — justoolkit automates boot-to-finish with RAM captures
- [ ] **Koma deeper dive** — reimplementation-level detail still needed

---

## Standing cautions

- **functions.json merged-function hazard:** Multiple addresses reported as one function (e.g. `0x0207DD40` is 8 functions, `0x0207D064` container `0x0207CFE0` is 4 leaves). Always cross-check with atlas before using as breakpoint targets.
- **Codex cross-checks wanted:** Feed raw encoding hex, not addresses. Atlas confirmed 7/7 claims successfully.
- **Thumb caller under-reporting:** `find_thumb_callers.py --audit` was a floor, not a census. P148 fixed two bugs (narrow window + silent gate), jumping 187→340 ROM-wide, 15→31 in ov6. Still use `--to <addr>` on specific addresses for certainty.
- **Escalation path:** If a blocking question needs the owner's judgment, open a PR in the `jus_files` repo and @drj613 in a comment. Check for responses on cron wakeups.

---

## Experiment backlog

**Source 1:** Fable brainstorm — 29 experiments (scratchpad/experiment-ideas.md)
**Source 2:** GameFAQs guide cross-reference — 23 new experiments #30–52 (scratchpad/guide-derived-experiments.md)

**Key leads from the guide (unverified — treat as testable hypotheses):**
- **Nature is PER-MOVE, not per-character?** Guide claims each attack has its own nature flag. Atlas checked spawn filter — shape exists but semantics = team/side filter. **NEW LEAD:** the nature resolver `0x0214E480` is ov05 (deck editor), not ov06 (battle). Nature may not be consulted at all during battle. Atlas needs to check if ov06 has its own nature reader on the damage path.
- **Three damage resistance categories:** punch/kick, special attacks, blades. May be per-character passives, not ability bits.
- **Three universal special inputs unmapped:** down+B (Forced Change), down+Y (Guard Break), down+X (Push Attack)
- **16+ status effects** with single-slot-per-polarity rule
- **SP gauge is discrete bars** (base 3, expandable to 4+ via help koma)

Both sessions have been notified.

---

## Action items

- [x] Beads gitignore cleanup (done Aug 17)
- [x] Nature findings reconciliation (done, `docs/research/Nature-System-Consolidated.md`)
- [x] Broader goal doc (`docs/PROJECT-GOAL.md`, committed `f47d63d`)
- [x] Charter update (atlas did it: `8aab44d`)
- [x] Session handoffs produced and delivered (Aug 17)
- [x] Second handoff cycle (Aug 18) — both sessions wrote handoff docs before context clear
- [x] ov05 contradiction closed — labelling error, not code conflict
- [x] Resistance attribution settled — bitset entity+0x128 not read for damage scaling
- [ ] Doc cleanup pass — planned for after entity/projectile work wraps
- [ ] Merge justoolkit's `re/ability-bitset-not-resistance` branch into master (17 commits)
- [ ] Push atlas branch (24 commits ahead, never authorised)

---

## How to use this ledger

Come back here after a break. Each section tells you what happened, where files live, and what was last delivered. Session names change on reset — check `ListAgents` for current names.
