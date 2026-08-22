# Portability Inventory

Bead: `jus-wayfinder-map-digi.5`. Date: 2026-08-21. Read-only sweep of `docs/research/`
(canon docs + `findings/` journal) sorting material per subsystem into CONFIRMED /
DISPUTED-TAINTED / SUPERSEDED, for the spec tickets `.7`–`.11` and the drafts `.1`–`.3`.

## Ground rules that apply everywhere

- **Layering** (`docs/research/README.md`): beads are the record, `docs/research/*.md` is
  canon, `findings/*.md` is an append-only journal — "history, never current." A findings
  file cited below is evidence for a claim; check the bead before speccing a number.
- **Battle-Engine-Map.md carries a blanket banner** (lines 3–22): the 2026-07-02 campaign
  cites tainted evidence in ~11 places (`jus-f30`, `jus-f0v`, `jus-5kf`). Its own guidance:
  layout claims usable, **every number needs a bead**. Tainted/retraction-bearing sections
  (line numbers approximate):
  - top banner (L8, L22)
  - "Measurement constraints inherited from the runtime loop (2026-08-18)" (L829)
  - "Owner ground truth (2026-08-19, via `jus-law`)" (L1296–1300) — narrows `jus-f30`:
    the gimmick added *extra damage events*, not inflated magnitudes
  - "A scope error, and a dependent of mine it taints" (L1521, L1541)
  - "chr_b 12 IS Luffy — and that may void the flat −2.0 reduction (P175 addendum)" (L1908, L1912)
  - "The auto-heal leg of that argument is weakened… (P175 addendum 2)" (L1954)
  - "Auto-heal REFUTED as the explanation… (P175 addendum 3)" (L1987)
  - "Two corrections to things I relayed… (P180 close)" (L2327)
  - "Pushback as requested… (P181 close 2)" (L2486)
  Also: §hitbox-priority is the self-described "most-refuted subsystem"; §collision-data's
  "Settled (iteration 59): the accumulated values are NOT damage" is superseded by
  P208–P211 and actively misleading.
- **Tooling hazards behind most retractions** (a spec writer citing "no caller / dead /
  vestigial" claims must check these): `ov6.txt` decodes Thumb regions as ARM (odd
  addresses absent entirely); `xrefs.json` misses Thumb `blx` call sites and ~89% of
  Thumb literal loads; watchpoint PC is +8; split-immediate bases and post-indexed stores
  are invisible to naive offset scans.
- **Runtime addresses are session-local** — re-derive with `scripts/find_battle_structs.py`.
- Taint beads: `jus-f30` (all pre-2026-08-18 damage runs had the stage gimmick ON),
  `jus-f0v` (two-move flat proof), `jus-5kf` (stale not wrong). Linter:
  `python3 scripts/check_docs.py` fails docs citing retracted/tainted/nonexistent beads.

## Verdict summary

| Subsystem | Verdict | Blocking spec bead |
|---|---|---|
| Damage calculation | **Portable now** (formula, gates, nature term, HP encoding) | `jus-wayfinder-map-digi.1` (in progress) |
| Collision | **Partial** — ColPrm layer spec-ready; contact-array semantics, ColMan/ColJoint, runtime hitbox parser open | `.7` |
| Move system | **Partial** — MoveMan/NoteTrack structures solid; priority resolution essentially unsolved | `.8` |
| Entity/projectile | **Partial** — lifecycle/ownership/ObjShot dispatch solid; projectileId decode and despawn open | `.9` |
| Guard/SP gauges | **Thin** — apply machinery confirmed, but list population and per-player-vs-per-character SP model unresolved | `.10`, `.13` |
| Nature | **Portable now** (resolution rule + damage-path read both confirmed) | `.2` |
| Deck editor | **Partial** — UI automation and validators solid; live-deck object identity contradiction open | `.3` |
| Koma/kshape | **Portable now** (koma.bin, kshape.bin, placement, adjacency all closed) | `.6` |
| Helper/passive taxonomy | **Partial** — all 57 abilities named and kinds mapped; slot-count conflict and magnitudes open | `.11` |

## Superseded docs — flag/archive list

Verified against banners and `README.md` §"Documents currently marked refuted or superseded":

| Doc | Status |
|---|---|
| `Damage-Reduction-Is-Flat.md` | ⛔ REFUTED banner confirmed. Reduction is ×0.75 per gate (`jus-reduction-is-quarter-multiplier-xk1`); its DOWN+B 5.000 row is wrong (5.250). |
| `Combat-Mechanics.md` | Superseded-style: bare "CONFIRMED" prose, flat-reduction language, multiplicative composition. **Nuance:** its 1.5× nature claim is RIGHT and was restored (the 2026-08-19 refutation banner was itself the error — read the corrected banner). |
| `Combat-Mechanics-Reference.md` | Same as above. |
| `Menu-Nav-Oracle-Attempt-1.md` | 📕 Superseded banner confirmed; replaced by `Menu-Nav-Verified-From-Pixels.md`. Kept as failed-experiment record. |
| `findings/defence-candidates-ruled-out.md` | ⛔ REFUTED banner confirmed (reduction is not ability 0x09; `jus-w66`). |
| `Research-Status.md` | 📕 Unmaintained banner confirmed. Cites four beads that no longer exist (`jus-wic`, `jus-vrz`, `jus-qsh`, `jus-q4b`); its "nature ×1.5 refuted" line is now wrong. |
| **Extensions found by this sweep:** | |
| `Move-Damage-Table-Goku.md` | Numbers superseded by heal-off re-measurement (B = 8.000 not 6.000); button labels wrong per owner (`jus-hbmn`). |
| `HP-And-Damage-Runtime-Findings.md` §2b | Self-superseded (HP formulas dead; struct now in `HP-Struct-From-Disassembly.md`). Keep §1 (1/64 encoding) and §2d warning. |
| `Nature-Damage-Controlled-Test.md` | Measurement valid, generalisation dead — **no banner yet; needs one** (a standalone reader gets the wrong answer). |
| `Damage-Path-Codex-Findings.md` §1 | Caller-1 ×0.5 refuted (P182). §2 (ability bitset) still stands. |
| `Passives-Reference.md` helper section | Superseded by `Helper-Passives-Catalog.md` (42 owner categories vs ~20 GameFAQs). Battle section still canon. |
| `findings/contact-array-is-not-a-damage-ledger.md` | Headline superseded by P208/P209 — its dismissed "sole producer" IS the damage formula. |
| `findings/player-slot-partial-field-map.md` | Superseded by `findings/player-slot-sp-total-at-0x5c8.md`. |
| `findings/char-0x1b4-is-a-per-player-array-slot.md` | Superseded by `findings/char-0x1b4-is-a-comicdeck-player-slot.md`. |
| `findings/shot-data-and-projectileid-refuted.md` | Superseded by `findings/projectileid-is-a-selector-not-an-index.md`. |
| `findings/nature-base-plus-override.md` | Mechanism corrected by `findings/nature-SOLVED.md`. |
| `findings/koma-format-decoded.md` (nature-negative headline only) | Overturned by `nature-SOLVED.md`; field map stands. |
| `Multi-Hitbox-Mechanics.md`, `DamageFlags-Character-Classification.md` | Not refuted, but Feb-2026 bare-"CONFIRMED" prose with no beads — treat as unverified per README rule. |
| `ARM9-Research-Guide.md` | Carries corrected notes re the `0x020924B0` "collision file pointer table" error; cite the corrections, not the original text. |

---

## 1. Damage calculation — **portable now**

### Confirmed (spec-ready)

| Fact | Source | Bead |
|---|---|---|
| Formula routine `arm9 0x020823E4`; out-param call from `0x02081280`/`0x02080F14`; sig `f(elemList, elem, ColPrmMan+0x14D bit0, &out)` | `findings/p208-damage-formula-0x020823E4.md` | `jus-formula-bp-not-a-hit-oracle-ve6` (breakpoint ≠ hit oracle) |
| Pipeline: `base = ldrsb [[elem+0x10]+4]`, ×2 8.8 factors (`scratch+0x184/0x186`), additive nature term, ±25%-of-base per gate, `>>2` to raw/64 | `findings/p211-damage-formula-end-to-end.md` §"The formula, end to end" | `jus-reduction-is-quarter-multiplier-xk1` |
| Six gates on word `[r8+0x44]` (bits 4/5/6 subtract, 12/13/14 add), class index `ldrsb [elem+0x0E]`, class table `0x02092E68` (16 bytes) | `findings/p213-flag-word-is-plus-0x44-ability-10-sets-bit-5.md` | `jus-gate-word-is-r8-0x44-fnz`, `jus-elem-0x0e-is-packed-8wz` |
| Gate-word writer `0x02083BE0`; mask tables `0x02092E78`/`0x02092E90`; driven by ability bitset at `battleObj+0x128` | same + `findings/p177-ability-bitset-loader.md` | `jus-bit5-is-ability-10-rxl` |
| Gate word read live `0x00002010`, predicted in advance, 8 stops | `findings/p-runtime-gate-word-read-live.md` | `jus-gate-word-read-live-0x2010-nbz` |
| Nature tables `0x0209FEF4`/`0x0209FF14` (4×4, values 1.0/1.5 in 8.8); additive with gates (advantage+resist = 1.25×); bypass bit 30 of `+0x40` | `findings/p216-nature-is-read-in-the-damage-path.md`, `findings/p210-*` | `jus-nature-is-read-in-damage-path-hbt` |
| Load-time: ov6 `0x02157114` assembles gate word AND packed nature byte together | `findings/p220-one-routine-assembles-both-derived-values.md` | `jus-one-routine-assembles-both-u24` |
| HP = u16 × 1/64; block at `char+0x56C` (+0x16 max, +0x18 current, cap 0x4000); apply trampolines `0x020783CC`/`0x020783B8`; KO signal discarded by all callers | `HP-Struct-From-Disassembly.md`, `HP-And-Damage-Runtime-Findings.md` §1, `findings/p175-the-ko-signal-is-discarded.md` | `jus-hp-block-at-char-0x56c-q86` |
| Per-size base HP in `chr_b.bin` (74×0x3C, five 4-byte per-size records at +0x10); `max = chr_b[idx][size−4] + 8×sources`, cap +32, sources dynamic | `findings/hp-all-74-characters.md`, `hp-per-size-chr_b.md`, `Helper-Passives-Catalog.md` "Confirmed numbers" | |
| jpower: 311×304 records; `+0x0C` damage1 = displayed×5; `damage = floor(damage1/5) + (tier−2)`, tier = `chr_b[+0x01]` | `findings/jpower-damage-located.md`, `jpower-Block-Pattern-Analysis.md` §"Damage Formula (SOLVED)" | `jus-base-2-is-jpower-damage1-10-mse` |
| Dispatch: 73-case per-character dispatcher `0x02157A44/60`; cases 23/24/32 → HP/SP/walker applies; band 64–73 are predicates, not commands | `findings/73-case-dispatcher-enumerated.md`, `commands-are-predicates.md` | |

### Disputed / tainted

- All pre-2026-08-18 runtime damage numbers: `jus-f30` window (gimmick ON). Narrowed to
  "extra events, not inflated magnitudes" — values can be un-tainted one at a time
  (Battle-Engine-Map L1296).
- `jus-nature-does-not-affect-damage-0c6` → `state:tainted`; `jus-nature-1p5-never-observed-uh8`
  → retracted (1.5 observed live, P216).
- ×1.20 at `0x02158DC4` — SPECULATIVE label; arithmetic upheld, "nature advantage" label
  refuted (Battle-Engine-Map claim 9). Don't conflate with the 8.8 nature tables.
- P211's two-gate model, P209's `0xC0` factor story, the `0x0215AC28` ×0.5, and the
  "0%/25%/50%" framing — all retracted; latest is P213's six-gate model.
- `+0x134` / accumulator as the melee path — REFUTED (`findings/c6c-damage-accumulator.md` banner).

### Top open questions

1. Attacker-vs-victim assignment of `r8` vs `r4` (explicitly "not claimed", P209).
2. Who writes the 8.8 factors `scratch+0x184/0x186` (always 1.0 so far).
3. Gates 5/6/12/14 never exercised; add side never observed changing a number.
4. Nature column selector — which 2-bit slot of `+0x175` (`jus-nature-column-selector-8gk`, untested).
5. B11 residue: how the formula's accumulated output reaches the HP flush (`scratch+0xE8`/`+0x130`)
   — open since iteration 75 across ~15 iterations (P176–P201).
6. Multi-hit accounting (up+B, Y strings); jpower `nextId` chains unexplored.
7. `element+0x0E` authoring source; the fixed 32.0 scripted damage at Thumb `0x021518D6`.

---

## 2. Collision — **partial**

### Confirmed

| Fact | Source |
|---|---|
| Three modules with recovered symbols: `BattleCol.cpp` (`Battle_ColManCreate 0x0207AD3C`), `BattleColJoint.cpp` (`0x0207BD40`), `BattleColPrm.cpp` (`Battle_ColPrmManCreate 0x0207C4C0`) | `findings/collision-is-three-modules.md`, `symbol-names-recovered-from-assert-strings.md` |
| ColPrm manager `0xFB54` bytes, zero unaccounted: 22 bucket heads `+0x28`–`+0xD7`, phase table `+0xFC` (19 entries, mostly tiny accessors), flag byte `+0x14D` (bit 0 = formula arg2), contact array `+0x154` (rows 0xC0 × elems 0x30), 128 inline records at `+0x454` stride `0x188` | `findings/colprm-manager-layout-closed.md`, `colprm-manager-fully-accounted.md`, `phase-table-is-mostly-tiny-accessors.md` |
| Manager identity: `0x0220DDE0` IS Battle_ColPrmMan (after P202/P203 retractions) | `findings/p204-object-is-colprmman.md`, bead `jus-s5q` |
| Per-frame driver `0x0207F480` (440 instr) drains buckets, is the primary bucket filler, runs 8-stage pipeline; narrowphase pair test IS the damage formula `0x020823E4`; results accumulate into `manager+0x154` via 4 RMW blocks `0x02081340`–`0x02081418` | `findings/collision-pipeline-closed.md`, `driver-is-the-primary-bucket-filler.md`, `narrowphase-pair-test.md`, `contact-array-writer-found.md` |
| Buckets 1 and 8 have no producer anywhere (verified against complete 60k-entry index) | `findings/buckets-1-and-8-confirmed-against-complete-index.md` |
| ColPrm record `0x188` bytes, 24 fields; `+0x34` mutable flag API (0x800 = pairwise/category routing), `+0x38` category bitmask (0x4000/0x8000 pick an axis); shared arm9/ov6 — collision and damage share one object | `findings/the-owner-is-a-colprm-record-0x188-bytes.md`, `record-0x34-*.md`, `record-0x38-*.md`, `category-mask-confirmed-selects-an-axis.md` |
| Wiring: no standalone registration — installer `0x0207C988` called inside entity ctor `0x020834D4`; returns the *owner* (a ColPrm record), ColObj at `owner+0x60`; `entity+0x10` = owner = damage scratch object (one object, three names) | `findings/collision-wired-by-the-entity-constructor.md`, `entity-0x10-is-the-colobj-owner-and-the-damage-scratch-object.md` |
| Loader `Battle_PrmDataInit 0x021702BC` loads `chr/col`, `chr/shot`, `chr/effect`; prmData at `char+0x84` | `findings/prmdatainit-is-the-collision-loader.md` |
| Authoring data: 281 collision files in `ChrBin.aar`, stride 20, 2837 records; full-roster claims (hitModifier not constant, damageFlags==0 at 46.86%, projectileId −34..36) | `findings/collision-data-extracted.md`, Battle-Engine-Map §collision-data round-2 table |
| damageFlags→jpower is two systems (10 direct, 64 indirect) | `DamageFlags-Character-Classification.md` §"Complete Classification" (unverified prose; open Blocking Unknown) |

### Disputed / tainted

- **"Contact array is NOT damage" (iteration 59) — the most important supersession in the
  repo.** The producer it dismissed is the damage formula. Discard the "no collision→damage
  link" conclusion (Battle-Engine-Map §collision-data "Settled (iteration 59)").
- §hitbox-priority: claims 2 and 3 demoted; `0x020924B0` refuted as a collision table (it
  keys sprite archives / credits); three rounds searched a broken (ARM-decoded Thumb) listing.
- Round-1 collision-data claims (projectileId = −32 sentinel, hitModifier constant 0,
  one terminator per file, knockback monotonicity) — all broken by full-roster data.
- Round-2 table is data-only, one lens; claim 12 capped UNSURE.
- `record+0x68`: "vestigial, no writer" vs the formula's live `[r4+0x68]` walk — unresolved tension.

### Top open questions

1. What the four contact-array element magnitudes mean (`+0x04/+0x08/+0x0C/+0x10`) — is this
   the damage staging area? Highest-value question here.
2. The runtime CollisionEntry parser (walks the 20-byte records at hit-test time) was never
   located; no hitTier/hitProperties comparison found anywhere (ARM/Thumb bug is a
   sufficient excuse, not evidence).
3. Buckets 1/8 dead-or-hidden; pipeline stages 4–7 unattributed; 13/22 buckets unassigned.
4. ColMan and ColJoint layers untouched (iterations 52–126 mapped only ColPrm).
5. Collision↔jpower join key (isTerminator as per-move sub-list delimiter — untested).
6. Who sets `scratch+0x40` bit 11 (damage-pending); P188 candidate retracted.

---

## 3. Move system — **partial**

### Confirmed

| Fact | Source |
|---|---|
| `Battle_MoveManCreate 0x02082A38`; object `0x2648`; owns two NoteTracks (+0x20/+0x24, ids 0xA1000/0xA6000); half the ctor is dead code (memset wipes it) | `findings/movman-owns-two-notetracks-and-dead-init.md` |
| Element allocator `0x02082C34`: free list `+0x08`, active `+0x00`, graceful NULL on exhaustion; sole caller is the ColObj installer (`BattleCol.cpp → BattleMove.cpp` dependency) | `findings/movman-element-allocator-and-the-0x3E-field.md` (REFUTED banner on one section — read it), `movman-two-parallel-arrays-and-the-frame-snapshot.md` |
| Element fields: `+0x08` owner, `+0x0C/+0x10` owner world position (asr#4), `+0x14/+0x18` frame snapshot; `+0x34` flags incl. `0x100` snapshot suppressor (sole setter = reposition fn `0x020804E8`), `0x200` cleared on projectile attach | same + `findings/the-snapshot-suppressor-is-the-reposition-function.md`, `element-0x0C-is-the-owners-world-position.md` |
| NoteTrack `0xA8` bytes at `[char+0x1a8]+0x18`: 7 slots × 16 bytes (`kind, ExtFlags, ProjectileId, u16 counter`); kind→slot table `0x021710A8` maps 17 kinds onto 7 slots — **overwrite, no queueing** (slot 2 collects kinds 6,7,8,9,10,14,15) | `findings/notetrack-struct-mapped.md` §2 |
| NoteTrack issues commands {3, 64–73}; 64–73 are boolean predicates (mutate nothing); 3 is fire-and-forget | `findings/notetrack-issues-the-commands-b11-dead-end.md`, `commands-are-predicates.md` |

### Disputed / open structure

- Element stride `0x40` is PLAUSIBLE only — nothing computes `base + i*0x40`.
- `+0x0C/+0x10` as a 16.16 scale pair — self-refuted (they're position).
- Commands 23/24 never issued; the 73-case dispatcher has no real direct caller (the dead
  route is the dispatcher's, not the function's).
- **Priority resolution is essentially unsolved** — §hitbox-priority is the most-refuted
  subsystem; the move-script system (dream-attack/chain multiplier home) has never been located.
- `frame-data-hitbox-notes.txt`: collision `frameStart` ≠ in-game startup frames (offset −3..+5
  across 5 characters, manual video ±2–3 frames); real startup likely in animation data or
  jpower extra section `0x80–0x12F`.

### Top open questions

1. Element stride (assume 0x40 or read RAM). 2. `+0x648`–`+0x2647` (0x2000 bytes, bulk of
MoveMan) unexplored. 3. Who consumes which of the two NoteTracks. 4. Move/attack priority —
no located code; move-script system unlocated. 5. How a character selects entries from a
shared jpower block (`chr_b-Complete-Mapping.md`: "template libraries, not complete movesets").

---

## 4. Entity / projectile — **partial**

### Confirmed

| Fact | Source |
|---|---|
| Three-layer split: `BattleObj.cpp` (pool, `0x02083204`), ov6 `BattleObjCtrl.cpp` (`0x02168B88`), ov6 `BattleObjShot.cpp` (`0x0216A7BC`); wired into battle root `0x02172960` at +0x10C/+0x110 by Thumb blx pairs | Battle-Engine-Map §projectile-entities, `findings/battle-add-root-object-map.md` |
| Pooled entity lifecycle (ctor `0x020834D4`, dtor `0x02083648` marks `+0x2C` bit 0, 30 call sites); free/active/retire lists at manager +0x14/+0xc/+0x1c | Battle-Engine-Map claims 1–4 (CONFIRMED_STATIC) |
| Ownership: `char+0x1a8` = pooled entity; `entity+0x30` = character; battle character is `0x1F0` bytes (allocator `__FILE__/__FUNC__/__LINE__` tags — strongest attribution mechanism in the corpus); spawn dispatch `0x021574CC` 13-way, cap at `char+0x1ac` | `findings/character-entity-link-and-a-reversed-setter.md`, `allocations-are-tagged-and-the-battle-character-is-0x1F0.md` |
| ObjShot manager `0x3FD4` bytes, 72 elements × 0x6C; kind byte `elem+0x1A` indexes 27-entry dispatch table `0x02172864` (no bounds check); default lifetime 30 frames; spawn path `0x0216A944` two arms with ColPrm-record target filters (`+0x38 & 0x800`, `+0x34` nibble attacker-vs-target) | `findings/objshot-manager-and-the-27-kind-dispatch-table.md` |
| Character struct: `char+0x56C` (HP pair, chr_b index +0x41); `char+0x558` list of character structs; init copy from chr_b (`0x02077C0C`): tier +0x11, base nature +0x13, HP +0x16/+0x18, koma ptr +0x34, regen +0x49 | `findings/p173-char-0x56c-is-the-character-struct.md`, `Character-State-Struct.md` init-copy table |
| `char+0x130` shared view (back-ptr +0x8), address taken 29× | `findings/character-embedded-views-0x120-0x130.md`, refined by `char-0x130-is-a-gated-handler-table.md` |
| projectileId: sbyte at collision +0x03, one value per character (92/120), attached to CollisionType 4/5 | `Binary2Collision.cs` note in findings; `findings/projectileid-is-a-selector-not-an-index.md` |

### Disputed / tainted

- **projectileId decode: four refutations** (per-char index, biased index, 17-entry table,
  chr/col/item.bin). Standing hypothesis: code-side spawn-behaviour selector — PLAUSIBLE,
  untested. Treat as opaque in a spec.
- Despawn: `0x0216C958` vs `0x0216E1C0` vs `0x0216F398` — capped PLAUSIBLE, never promoted.
- `Character-State-Struct.md`: struct-identity caveat (B10); physics region 0x00–0x3F
  DISPROVEN; `+0xA0` status flags overlap unreconciled; battle addresses session-local.
- chr_b name-within-series ordering wrong (chr_b[24] is Kyuubi Naruto, not Kakashi); series
  column 74/74 valid, name column not.
- ColPrm record `+0x130` ≠ character `+0x130` — real aliasing trap (`0x02158B20` uses both).

### Top open questions

1. projectileId decode (highest-value blocker). 2. 54% of ObjShot manager (`0x2158` bytes)
unaccounted. 3. Which routine is the despawn (needs GDB census). 4. Persistence across
character switch (Q5 — no owner-liveness check found). 5. `record+0x17C` gate field
unexplored. 6. Kind names for the 27 handlers; kind 0x1A handler missing from functions.json.

---

## 5. Guard / SP gauges — **thin**

Subsystem's own scorecard: 2 confirmed / 11 plausible / 1 speculative (Battle-Engine-Map
§guard-sp-gauges, materially overtaken by P157–P161 appended below the claim table).

### Confirmed

| Fact | Source |
|---|---|
| `[char+0x1b4]` = one of four `0x61C` player slots in the ComicDeck block (from +0x64) | `findings/char-0x1b4-is-a-comicdeck-player-slot.md` |
| **SP total at `slot+0x5C8`** (`[[char+0x1b4]+0x5C8]`); `+0x5CF` byte blocks SP loss but not gain; 14-field slot map | `findings/player-slot-sp-total-at-0x5c8.md` |
| HP trampoline `0x020783CC` has 8 static ov6 call sites; `+0x558` walker `0x020783DC` fully decoded (two skip gates, Grow per node) | Battle-Engine-Map §guard-sp-gauges claims 1, 11 |
| 42-entry status/effect dispatch table ov6 `0x02171168`; **no chain-length scaling anywhere** — all HP-boundary scales are constant powers of two; duration formula `base + (base/10)*(stat*2)` at `0x02158F44` | P157–P158 sections; `findings/p157-*`, `p158-*` |
| Effect ids 1–41 (0 = none); nodes at `battleObj+0x7C + slot*0x18` (two slots); on-hit flush `0x02158B20` reads staged deltas `+0xE8`/`+0x130` and two staged effect ids `X+0x172/0x173` | `findings/p159-*`, `p172-*`, `p180-*` |
| View is a live SP-apply path (selectors 9/12 → `0x020781E4`); the 16-slot view handler *table* is dead in retail, but the view is not — a fine distinction a spec writer will get wrong | `findings/view-handlers-are-the-live-sp-apply-path.md`, `the-view-handler-table-is-dead.md` |
| Second, undocumented **drain trampoline `0x020783B8`** (rsb-negate) exists — found only by manual read; invisible to xrefs (inline-pool `bx ip`) | claim 7 refutation, Battle-Engine-Map |

### Disputed / open

- Claim 7 ("walker is the only other Grow caller") REFUTED by the drain trampoline; claim 8's
  "no sibling" refuted 20 bytes away; claim 10 ("no second fixed-offset gauge") rests on an
  incomplete sweep (`jus-hp-block-at-char-0x56c-q86`, plausible).
- P172's "`+0x56C` is not HP" — RETRACTED by P173 (it IS HP; id 19's −4 drains current HP).
- 1-HP floor location: explicitly not claimed (three untested candidates).
- No node-insertion site for `char+0x558` exists in the database (1 store in 37 hits, the
  zero-init) — a spec cannot yet say how the meter list is populated.

### Top open questions

1. **How `+0x558` nodes are inserted** (likely split-base store, invisible to scans).
2. How many node kinds populate the list — statically unresolvable (claim 13 SPECULATIVE).
3. **Deck-shared vs per-character SP** — SP is documented deck-wide but lives on a per-player
   slot at `+0x5C8` next to a per-character `+0x558` list. Biggest design question for the spec.
4. The `+0x558` node vs `+0x56C` gauge-pointer identity dispute — bead `jus-wayfinder-map-digi.13`
   ("Settle or waive: +0x558 vs +0x56c gauge dispute"), GDB card #1.
5. 87% of the player slot (+0x000–+0x557) unmapped.

---

## 6. Nature — **portable now**

### Confirmed

| Fact | Source | Bead |
|---|---|---|
| Enum 0 力 / 1 知 / 2 笑 / 3 なし (also no-override sentinel); triangle 力>知>笑>力 | `Nature-System-Consolidated.md` §1, `findings/nature-SOLVED.md` | |
| Resolution rule (accessor `0x0214E480`): helper→3; battle→koma flags high nibble else `chr_b+0x00`; support→`chr_s[abilityId*20 + (kshapeGroup−1)*8]`; verified 9/9 | `findings/nature-SOLVED.md` "The rule" | |
| Runtime byte at `char+0x13` (high nibble of koma +0xB) | same | |
| **Nature DOES affect battle damage**: 4×4 tables `0x0209FEF4`/`0x0209FF14` (1.0/1.5, inverse 3-cycles, bonus-only); read on a 2-bit per-scratch field; additive with gates; bypass bit 30 | `findings/p210-*`, `p216-*` | `jus-nature-is-read-in-damage-path-hbt` |
| Non-damage uses: sprite-archive selection (`_b.aar`) and an advantage counter into `[r7+0x60]` | `findings/c0-nature-in-battle.md` §1, §3 | |
| Distribution: 890 panels → 226/183/169/312; only 32 explicit battle overrides | `nature-SOLVED.md` | |

### Disputed / tainted

- "Nature is deck-building only" — `jus-nature-does-not-affect-damage-0c6` is
  **`state:tainted`**; the measurement stands, the scope didn't. **PROJECT-GOAL.md line 16
  still states the tainted claim** ("does not affect battle damage") — staleness already
  ticketed as `jus-wayfinder-map-digi.4`.
- `Nature-System-Consolidated.md` §3/§5 retracted by its own banner; January's 1.5× was right
  (`jus-nature-january-vs-august-9a6`).
- "Nature not in koma.bin" refuted; "bit 0x10 marks override / 26 panels" refuted (real test:
  high nibble == 3; 32 panels).

### Top open questions

1. Which 2-bit column field of `+0x175` under which flags (`jus-nature-column-selector-8gk`).
2. What sets `ColPrmMan+0x14D` bit 0 (table orientation). 3. What sets/clears the immunity
bit 30 (`0x021591F4` toggles; Jotaro's passive is the likely consumer). 4. Who consumes the
advantage counter `[r7+0x60]`. 5. Low nibble of koma +0xB; `chr_s+0x10`.

---

## 7. Deck editor — **partial**

### Confirmed

| Fact | Source |
|---|---|
| Route, two-tap rule, full framebuffer geometry (list rows, canvas 5×4 grid pitch 48, filter x-bands), screen oracles | `Deck-Editor-Automated.md` |
| Placement validator `0x02076D30` (bounds, shape shift `col + row*5`, occupancy mask at `deck+0x568`); id lookup `0x02076C98` (table `deck+0x30`, entry 0xC, count `deck+0x18EC`); add-entry `0x02076E38` error codes | `findings/p228-koma-shape-is-a-20bit-bitmap.md`, `deck-validators-and-the-id-table.md`, `deck-add-entry-contract.md` |
| Deck node `0x50` bytes, 16 per slot, field map | `findings/the-0x50-deck-node-mapped.md` |
| Ownership: 55 holders of global `0x0214BD80`, 37 in ov5 (KomaList/KomaEdit/KomaState/DeckMake) — editor-owned, not battle | `findings/deck-global-holders-and-a-fourth-mask-bug.md` |
| GDB RAM map: deck state `0x020A0C00`, active deck index `0x020AFEB4`, koma master table `0x020B9480`, leader flags | `Deck-Memory-Structure.md` (session-local caveat applies) |
| Legality: ≥1 battle + support + helper + Leader sticker; 8 slots; eviction and helper-facing UI behaviour | `Koma-System-Observed-Behavior.md`, `Deck-Editor-Automated.md` |

### Disputed

- One-tap placement / one-tap clear — false positives; deck-state byte-diff is not a signal
  (no-op taps cost 95–190 bytes); use pixel oracles.
- **`0x0214BD80` notation clash**: ComicDeck block vs root table-pointer block (`+0x38` kshape,
  `+0x40` chr_b, `+0x48` chr_s). Reconcilable but will trip a spec writer — flag it.
- **"Add-entry path never succeeds"** (`findings/deck-add-entry-path-is-dead.md`): no writer of
  `deck+0x30`/`+0x18EC` found — a negative-from-exhaustion contradicting a working editor;
  likely the live deck is a different object. Do not spec from it.

### Top open questions

1. Which object holds the *live* deck; who writes `deck+0x30`/`+0x18EC`. 2. Where helper
facing (2-bit) and L/R sticker bindings live in save data. 3. Deck save serialisation format.
4. KomaList `0x554` object mostly unmapped. 5. ov01 vs ov05 exact screen split
(`Overlay-Residency-Deck-Screens.md`).

---

## 8. Koma / kshape — **portable now**

### Confirmed

| Fact | Source | Bead |
|---|---|---|
| `koma.bin` = 890 × 12; full field map (imageId, characterId, seriesIdx, panelOrdinal, panelType, abilityId, kshapeGroup/Element, flags with nature nibble) | `findings/koma-format-decoded.md` | |
| `kshape.bin`: header (cumulative starts + per-class counts, 66 shapes), records base **0x40** stride 0x18 = 20-byte ordinal map + 20-bit bitmap at +0x14; loads verbatim to RAM `0x021AF100` | `findings/p229-koma-shapes-come-from-kshape-bin.md` (read the last three sections only — middle is self-superseded) | `jus-koma-shapes-come-from-kshape-bin-0j2`, `jus-d9a` |
| Grid is **5 wide × 4 tall** — three independent confirmations | placement validator + adjacency gate + owner play | `jus-tv3a` (transpose correction RETRACTED — read it) |
| Lookup `0x02076D00`: `(class, sub)` via cumulative table | `findings/p229` | `jus-kshape-lookup-identified-a1j` |
| Placement rule complete (validator `0x02076D30`) | `findings/p228` | `jus-koma-shape-is-a-20bit-bitmap-423` |
| **Adjacency grants abilities**: gate `0x020779CC`, node +0x0E own cell, +0x0F direction 1..4 (down/left/up/right table `0x02092E34`); a koma grants its ability to the adjacent cell it points at; 3/3 live + 20-cell tiling | `findings/p225-koma-adjacency-grants-abilities.md` (final sections) | `jus-koma-adjacency-grants-abilities-70l` |
| Deck-battle object: grid at +0x008 (5×4×4), 16 node slots stride 0x50 at +0x058, chain head +0x558; node +0x40 type discriminates +0x41 (chr_b index vs ability id) | same | `jus-second-ability-source-0x558-5rp` |
| 312 characters, each exactly one 1-cell helper; type↔size exact; shapes curated (sizes 1–3 complete, 4+ hand-picked) | `koma-format-decoded.md`, `nature-SOLVED.md` | |

### Disputed / retracted

- kshape base 0x54 (`jus-d9a`), "~81 shapes @20B", "0x5 = char-in-series", "43 series",
  piece.bin as per-koma table, "row-0 cross-side link" — all retracted; final answers above.
- Node slot count went 19.6 → 18 → **16** (fractional values were the error signal); the
  `0xC0` gap before the next side's object unexplained.
- kshape record 59 has a duplicate ordinal (likely a data bug); five trailing u32s per record
  unidentified.

### Top open questions

1. koma.bin byte 0xA (0..8, ≤ size — render anchor? sort key?). 2. Low nibble of +0xB.
3. piece.bin indexing and the 3-relationships table (P7). 4. Where per-panel base HP comes
from is answered for battle (chr_b per-size) — but the koma-side "size×k" speculation should
be deleted from `Koma-System-Observed-Behavior.md`. 5. What writes the `+0x558` chain (the
deck→battle bridge). 6. Do unlocks gate shapes?

---

## 9. Helper / passive taxonomy — **partial**

### Confirmed

| Fact | Source | Bead |
|---|---|---|
| `ability.bin` 57 × 4 (`kind, sub, s8 param, pad`); `ability_t.bin` 57 × 12 relative string ptrs (base = pointer-field offset — quirk in `JusText.cs:90`); **all 57 named**, ten former unknowns resolved | `findings/abilities-all-57-named.md` | |
| Kinds: 0 = ids 0–37 (append), 1 = 38–48 (SP triggers, append), 2 = 49–56 (**never append** — stat modifiers applied at load: id 52 maxHP+8, 53 SP-max+1, 54/55/56 strb into `char+0x4A/4B/4C`) | `findings/p224-*`, `p227-*` | `jus-kind2-abilities-are-stat-modifiers-bdq` |
| On-disk ability list: `chr_b+0x03`, five sparse byte slots, zeros = empty not terminators; the 4 empty records are the Debug series | `findings/p223-ondisk-ability-list-found.md` | `jus-ondisk-ability-list-at-chrb-0x03-kfc` |
| Runtime list: count `char+0x1A`, ids `char+0x1B..`, cap 15, append `0x02077A74`; two sources (chr_b slots + the `+0x558` koma chain) | `findings/p224`, `p178-ability-list-is-in-chr_b.md` | `jus-second-ability-source-0x558-5rp` |
| Cached bitset `entity+0x128`; writer `0x0215FB3C`; **only bit 4 (Auto-Guard) of 32 changes blunt damage**; resistance is NOT in the bitset (both directions null) | `Ability-Bitset-Is-Not-Resistance.md`, `findings/p177-*` | `jus-w66` |
| Abilities feed the ±25% gates via mask tables `0x02092E78/0x02092E90` | `findings/p213` | `jus-bit5-is-ability-10-rxl` |
| Deck bonuses: Leader +8 HP, +8 per relationship adjacency, 4 sources cap +32, additive | `Helper-Passives-Catalog.md` "Confirmed numbers" | |
| Status enum: 10 contiguous ids 0x19–0x22 | `Cheat-Code-Analysis.md` + catalog | |
| Helper = directional single-passive buff emitter (owner live; matches adjacency gate) | `Helper-Passives-Catalog.md`, `p225` | `jus-koma-adjacency-grants-abilities-70l` |
| `battle-chars-passives.json`: 66 objects of community English text (name, 3 "boost" partners, passive strings) — guide text, no ids/magnitudes; 66 ≠ 74 chr_b | file itself | |

### Disputed

- **Slot-count conflict, unresolved**: p178 says count at `chr_b+0x02` + six slots; p223 says
  five slots at +0x03 (loader `cmp #5`) and the exporter labels +0x03 differently. Must be
  settled before writing an exporter.
- 19% of the catalogue is orphaned (11 ids carried by no chr_b record; 49–51 also route to a
  stub) — presence in ability.bin is not evidence of reachability. Demonstrated-live set is
  ~12 of 57.
- `jus-mask-index-is-damage-class-gls` — naming RETRACTED (see its comments).
- Ability 7 vs kind-2 id 52 (two maxHP+ paths, same 0x4000 cap) — one effect or two, unknown.
- Auto-Guard zero-damage measured with SP available; no-SP case untested.
- `Helper-Passives-Catalog.md` slot guesses for the 4 unclaimed categories REFUTED (they're
  group 2); its "6 Unknown IDs" line obsolete.

### Top open questions

1. The 5-vs-6 slot / `+0x02` count conflict. 2. Enumerate the `{kind,id}` dictionary at
`[global]+0x50`. 3. What causes the residual damage reduction (per-character defence?
`record+0x3C` low nibble?). 4. Passive magnitudes are hardcoded in the damage path (only 3
of 57 strings carry a number) — locate them. 5. Helper facing: one cell or row/column
(UI vs type-2 chain mechanism unproven identical). 6. Static helper ids vs runtime
`0x021DF1D7` array numbering (P9). 7. The queued Edajima test (`jus-5bg`) — three
predictions unrun.
