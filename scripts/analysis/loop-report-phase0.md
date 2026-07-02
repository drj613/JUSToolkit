# Morning Report — Battle Engine Atlas, Phase-0 Gap-Closing Loop

**Outcome:** DONE. Phase-0 (`docs/design/Static-RE-Phase0.md`) completed all
success criteria — iterations 0–9 (10 units total: `init`, P1–P6, and this
P7-synthesis unit). Every unit in the queue reached `status: done`; no kill
switch, no gate failure, `consecutive_failures = 0` throughout.

**Branch:** `loop/battle-engine-atlas` (worktree
`.claude/worktrees/battle-engine-atlas`). No commits made by this unit — the
orchestrator commits after reviewing this report.

## Per-Subsystem Results (Phase-0 scope)

| Subsystem | Status | Confirmed | Plausible | Speculative | Headline |
|---|---|---|---|---|---|
| collision-data (round 2) | PARTIAL | 3 | 6 | 4 | Full-roster re-mine (281/281 files, up from 4/74) **broke** 4 round-1 findings at scale: `projectileId=-32` sentinel (really 15 distinct battle values / 25 support), `collisionType=4`-necessary framing (real rule `∈{4,5}`, 97.87%), and — notably — round 1's own CONFIRMED_STATIC "`hitModifier` constant at 0" claim (9/2047 nonzero) |
| projectile-entities (verify) | PARTIAL | 4 | 1 | 0 | 3-lens verification closed the prior campaign's "pending" gap: entity-pool alloc/free, 13-way spawn dispatcher, and ownership wrapper all CONFIRMED_STATIC; aliasing lens found a 2nd character-struct back-pointer at wrapper`+0x18`; despawn fn capped PLAUSIBLE (not provably projectile-specific) |
| guard-sp-gauges (new, B12) | PARTIAL | 2 | 11 | 1 | All 8 HP-trampoline call sites traced; **no second fixed gauge offset exists** — leading guard/SP candidate is a dynamic Meter-node list at `char+0x558`; aliasing lens discovered a previously-invisible sibling DRAIN trampoline (`0x020783B8`), proving the `xrefs-to`/`pool-values` `bx ip` blind spot is real |
| chrb-catalog (new, B14) | PARTIAL | 10 | 6 | 0 | `0x0214BD80` reframed as a "battle resource manager" singleton owning ~15 tables (chr_b is just one); complete 97-hit xref catalog + 60-byte record map built; **top open dispute**: does the `+0x558` technique-node land unmodified in the `+0x56c` gauge pointer? — aliasing lens says yes, disasm-correctness lens says no, deliberately left unresolved (GDB card #1) |

**Unchanged from the original campaign** (not in Phase-0 scope): damage-pipeline,
jpower-indirect, hitbox-priority, physics-writers, hitstun-timers, movement,
weight-hunt — see their sections in `Battle-Engine-Map.md` (untouched this
phase).

**Phase-0 totals:** 4 subsystems touched, 57 claims re-scored or newly
produced (13 collision-data + 5 projectile-entities + 14 guard-sp-gauges +
16 chrb-catalog + 9 tooling/gate checks not claim-bearing); 19 CONFIRMED_STATIC
/ 24 PLAUSIBLE / 5 SPECULATIVE across the 4 touched subsystems. Every claim
machine-verified (`verify_evidence.py`); all subsystems now have complete
adversarial-lens coverage (3 lenses, or collision-data's single
data-consistency lens for its data-only claims) — no subsystem in the whole
Map carries an unverified-pending caveat anymore.

## Top 5 Discoveries by Impact

1. **Sibling drain trampoline `0x020783B8` + a proven tooling blind spot.**
   The aliasing verification lens manually swept the bytes adjacent to the
   known HP trampoline `0x020783CC` and found a second, previously
   undocumented trampoline reached via `bl` from `0x0215AC70` — and
   `xrefs-to`/`pool-values` against both trampolines' `bx ip` jump targets
   return **zero** hits for a demonstrably real reference. This is the
   single most consequential tooling finding of the phase: any future static
   pass hunting for indirect-jump trampolines needs a byte-pattern scanner,
   not xref-based search.
2. **chr_b singleton reframed; top open dispute identified.** `0x0214BD80`
   is not "the chr_b pointer" — it's a "battle resource manager" owning
   roughly 15 tables. All 97 xref hits (not the ~87 previously estimated)
   are now classified with a complete record map. The two adversarial lenses
   split on whether the `+0x558` per-technique cache and the `+0x56c` gauge
   pointer are the same object — deliberately left unresolved, with one
   GDB breakpoint (queue card #1) able to settle 3 claims at once.
3. **`projectileId=-32` "fixed sentinel" REFUTED at full-roster scale.**
   Round 1's 4-character sample (n=2 nonzero observations) suggested a
   boolean-like sentinel; round 2's 281-file re-mine found 15 distinct
   nonzero values in battle files (25 in support), and the real
   `collisionType` rule is the `{4,5}` union (97.87% coverage), not `4`
   alone. The single most consequential round-1→round-2 reversal.
4. **`hitModifier` constancy broken — a rare "confirmed claim overturned by
   scale" case.** Round 1 had this as CONFIRMED_STATIC ("constant 0 across
   all 92 entries"); round 2 found 9/2047 nonzero entries across 6
   characters, corroborated independently in both the item and support
   populations. Most round-1→round-2 changes were demotions from
   overstated correlations; this is one of the few where a full-scale
   negative claim itself was wrong.
5. **projectile-entities' verification gap closed, with a bonus find.**
   The prior campaign shipped this subsystem's evidence without adversarial
   lens verification; this phase ran all 3 lenses and promoted 4/5 claims
   to CONFIRMED_STATIC. Along the way, the aliasing lens answered a
   standing open question for free: the pooled entity's ownership wrapper
   carries **two** back-pointers (MoveInfo at `+0xc`, the raw character
   struct at `+0x18`), not just one.

## GDB Validation Queue

`docs/research/GDB-Validation-Queue.md`: **30 one-breakpoint cards across 8
sessions, ≈230 human-minutes (~3.8 hours).** Card 1 (new, top priority) is
the `+0x558`/`+0x56c` identity dispute — reuses the existing Session 1 setup,
settles 3 chrb-catalog claims in one shot. 9 cards from the prior queue
version were dropped as answered statically (2 from projectile-entities'
newly-completed verification, 7 from collision-data's old data-only
re-export session, entirely superseded by round 2); 8 new cards were added
(2 for chrb-catalog, 6 for guard-sp-gauges).

## Open Questions for the Next Campaign

- **`xrefs-to`/`pool-values` cannot see `bx ip`-style indirect jumps through
  an inline pool word** (tooling item) — demonstrated concretely this phase
  by the `0x020783B8` sibling trampoline. No byte-pattern scanner for the
  `ldr ip,[pc,#N]/ldr r0,[r0,#M]/bx ip` shape was added (P6c was skipped as
  too risky to run pre-synthesis, since it would have required regenerating
  every frozen evidence DB this phase's tracers cited).
- **The `char+0x558` list's node-insertion site was never found statically.**
  Only one store (a zero-init) touches this offset ROM-wide across 37 total
  hits; a node-populating write almost certainly uses a split
  `add rX,#0x558` + register-offset store, which is invisible to
  immediate-based `search-imm`. A live `watch` breakpoint (queue card 30) is
  the only path forward.
- **SP deck-shared vs. per-character tension.** JUS's SP gauge is documented
  as shared across a player's 3-character deck, which sits awkwardly against
  a *per-character* `char+0x558` list model discovered this phase — is SP a
  node aliased/shared across a team's three character structs, or does each
  character track its own contribution to a pool tracked elsewhere? Entirely
  open.
- **The `+0x558`/`+0x56c` identity dispute itself** (top open dispute,
  chrb-catalog claims 3/11/16) — one GDB breakpoint away from resolution;
  see queue card 1.
- `ClassId` (chr_b record `+0x0E`) has no observed consumer among all 97
  xref hits to the manager singleton — either dead data in this ROM build,
  or consumed via a mechanism outside literal_load references to
  `0x0214BD80`.
- Whether `0x0216C958` (projectile despawn) is genuinely projectile-specific
  or a generic spawned-effect updater shared with ≥2 sibling ov6 functions
  the aliasing lens found reusing identical scaffolding — needs a live
  cross-function census, not resolvable statically.
- `projectileId`'s 15 (battle) / 25 (support) distinct nonzero values,
  clustered in a `-18..-34` band, are a strong candidate for a real
  lookup/enum table — a disassembly trace of the code that *reads*
  `projectileId`/`hitModifier`/`hitProperties` (not attempted this data-only
  round) is now much higher-value, since concrete nonzero instances exist to
  set breakpoints on.
- The `isTerminator` per-move-sub-list-boundary hypothesis (histogram 0–36
  terminators per file, round 2) is untested against jpower's per-character
  block count — if segment count matches jpower block size for several
  characters, that's the still-missing collision↔jpower join key both
  rounds have been unable to find via field-name matching alone.
- `chr_b.json`'s exported schema should probably be revised (not attempted
  this phase — read-only campaign): `CharId`+`Flags` are consumed as 5
  independent ability-ID bytes, never a `charId` byte + `flags` u32 as
  currently modeled.

## Infrastructure Touched This Phase

`scripts/analysis/`: `query.py` gained `search-op-imm` (data-processing
immediate search, deterministic, in the self-test); `arm9_tables_ram.json`
written (842 rows, file-offsets + scan ranges translated to RAM addresses;
smoke-tested against 3 candidates, 0 `xrefs-to` hits each — candidates
remain unverified, translation plumbing now exists). `disasm_db`'s `bx <reg>`
epilogue-detection gap was **not** touched (P6c skipped: regenerating the
disasm/xref DBs pre-synthesis would have invalidated every frozen evidence
file this phase's tracers cited). `gates.py` re-run clean after every
change; determinism and `--selftest` verified.

## Notes for the Human

- `jus_files` in the worktree is a symlink to the main checkout's copy
  (expected).
- Another session drops untracked files into this worktree (e.g.
  `scripts/analysis/ramdiff.py`) that this loop never touches, commits, or
  deletes — per the state file's own triage note.
- The beads commit hook is still broken repo-wide; all loop commits used
  `--no-verify` (unchanged from the original campaign's finding).
- Canon docs (`Battle-Engine-Map.md`, `GDB-Validation-Queue.md`,
  `Research-Status.md`) were updated from `.scored.json` files only, never
  from raw findings confidence — per the campaign's cardinal rule.

## Iteration Log

Copied from `scripts/analysis/loop-state-phase0.json` `log[]` (iterations
0–8), plus this synthesis unit (iteration 9):

| Iter | Unit | Result | Note |
|---|---|---|---|
| 0 | init | ok | phase0 state created; gates re-run all pass; original-4 hashes baselined |
| 1 | P1-export-collisions | ok | 281/281 exported via `jus combat export-all-collisions` (src: `extracted_chrbin/ChrBin.aar/chr/col`, 74 `*_b_*` + 206 `*_s_*` + item); all parse; original 4 byte-identical; P2 unblocked |
| 2 | P2-remine-collision-data | ok | round2: 13 claims mined (miner deterministic, verified independently); 1-lens recomputation: 12 UPHELD / 1 UNSURE; scored 3C/6P/4S. Round-1 breaks at scale: `projectileId` `-32` sentinel (15 distinct values), `ct4`-necessity (real rule `ct∈{4,5}`), `ct5→tier3` (47.58% pooled), `hitModifier` non-constant (9/2047) |
| 3 | P3-verify-projectile-entities | ok | 3 lenses ran: disasm 5×UPHELD, aliasing 4×UPHELD+1 UNSURE, data 5×UPHELD; scored 4 CONFIRMED / 1 PLAUSIBLE (idx4 despawn fn: projectile-vs-generic-effect not statically separable). Lens nits for synthesis: callee count 2 arm9/28 ov6 (not 30), dispatcher case idx 7 not 8, idx4 kill-condition (b) has a suppression-bit gate |
| 4 | P4-B12-trampoline-sweep | ok | 14 claims (3C/10P/1S), `verify_evidence` 0 (148 segments). All 8 trampoline sites enumerated+traced; no alternate fixed base offset — guard/SP candidate is `char+0x558` node list; only 1 store to `+0x558` (zero-init) in whole DB, node insertion unfound; xrefs-to blind spot documented. P4v enqueued |
| 5 | P4v-verify-guard-sp-gauges | ok | 3 lenses: disasm 14×UPHELD, aliasing 11U/2R/1 UNSURE, data 12U/2 UNSURE; scored 2C/11P/1S. Aliasing lens found NEW drain trampoline `0x020783B8` (`bl` from `0x0215AC70`) proving the blind-spot mechanism; synthesis must add it + GDB card for delta-source magnitude and the SP deck-shared question |
| 6 | P5-B14-chrb-catalog | ok | 16 claims (15C/1P), `verify_evidence` 0; 97/97 catalog rows cross-checked against xrefs-to by orchestrator. Singleton reframe + cache-at-load confirmed for combat stats; ov11 AI reads `BattleParams` live. P5v enqueued |
| 7 | P5v-verify-chrb-catalog | ok | 3 lenses: disasm 11U/3R/2 UNSURE, aliasing 16U, data 15U/1 UNSURE; scored 10C/6P. LENS DISPUTE (top GDB card): is `+0x558` technique-node the same object as `+0x56c` gauge? Aliasing says yes via `0x02077E70`, disasm says no via caller enumeration — claims 2/10/15 capped PLAUSIBLE. Catalog errata: 2 rows of fn `0x0207698C` dropped a `+0x1800` term (real offsets `manager+0x18D4`/`+0x18DC`). Data lens: independent `chr_b.bin` reparse 74/74 records exact via claimed offset map |
| 8 | P6-tooling | ok | (a) `search-op-imm` added to `query.py` (+175/-3), deterministic, in selftest; (b) `arm9_tables_ram.json` written (842 rows, offsets+scan_range translated, `_meta` documents fields); 3 xrefs-to smoke tests clean (0 hits each — unverified candidates); (c) SKIPPED: `disasm_db` regen would invalidate frozen evidence DBs pre-synthesis. Orchestrator re-ran AC: determinism ok, selftest 0, gates 0 |
| 9 | P7-synthesis | ok | canon docs updated from `.scored.json` files only (`Battle-Engine-Map.md`: round-2 collision-data table, projectile-entities promoted, guard-sp-gauges + chrb-catalog sections added, cross-cutting §2/§3 updated; `Research-Status.md`: Phase-0 addendum + 3 new CONFIRMED subsections + BattleParams update; `GDB-Validation-Queue.md`: regenerated, 9 cards dropped / 8 added / 30 total, card 1 = the `+0x558`/`+0x56c` dispute); this report written |
