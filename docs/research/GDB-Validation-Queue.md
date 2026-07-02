# GDB Validation Queue — Battle Engine Atlas

Every `PLAUSIBLE` and `SPECULATIVE` claim (post-verification, i.e. final
scored confidence) produced by the static RE campaign
(`docs/research/Battle-Engine-Map.md`), plus **all** `projectile-entities`
claims (that subsystem's verification lenses were skipped for time, so every
claim there is treated as unverified/PLAUSIBLE regardless of its stated
confidence — see the Map's projectile-entities section). No claim below has
ever been checked against a running emulator; this document exists so a
human can do that with the minimum number of sessions and breakpoints.

**Cards are grouped into sessions** by overlay/moment so one emulator sitting
can knock out several cards without reloading state. Within a session, set
up the scenario once, then walk the numbered breakpoints in order.

**Total estimate: ~31 cards across 8 sessions (7 live-GDB + 1 scripted data
re-export), ≈ 210 human-minutes (~3.5 hours)** — see the time table at the
end.

---

## Session 1 — Live Hit-Landing (ov6, function `0x02158B20` and its direct callees)

**Setup:** start a battle, control one attacker landing normal hits on a
defender with the on-screen HP bar visible. For card 5, additionally get the
attacker down to ≤25% of their own gauge to test the desperation-gated path.
For card 11, get two characters' hitboxes to overlap on the same frame
(a clash).

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 1 | damage-pipeline — `char+0x56c` is a 2-field gauge; `0x02078488`=clamped-add accessor | `0x02078488` | Watch `[r0+0x16]` (max) and `[r0+0x18]` (current) while landing hits that visibly change on-screen HP | `[r0+0x16]` tracks max-HP-like stat; `[r0+0x18]` drops by the delta in `r1` matching the visible HP loss | Fields don't correlate with the HP bar (e.g. track a different gauge — super/guard meter) |
| 2 | damage-pipeline — `0x020783CC` trampoline into the gauge accessor | `0x020783CC` | Confirm `r0` resolves to the defender's `char+0x56c` gauge pointer; confirm `r1` (delta) is negative, magnitude == `floor(damage1/5)+(tier-2)` | `r0`/`r1` match as described | `r0` points elsewhere, or `r1` doesn't match the known-good formula |
| 3 | damage-pipeline — `0x02158BC0` call site actually decrements gauge on a real hit | `0x02158BC0` | Same check as card 2, at this specific call site | Same as card 2 | Same as card 2 |
| 4 | damage-pipeline — scratch `+0xE8` = pre-computed per-hit damage magnitude | `0x02158BA8` | Read `[r1+0xE8]`; compare to `floor(damage1/5)+(tier-2)` for the hit that just landed; trace backward for the last store to this field this frame | Value matches formula output; a store instruction is found earlier in the same frame | Value doesn't match, or no write is found this frame (implying a cached/different source) |
| 5 | damage-pipeline — ×1.20 scale = desperation-gated universal `attack_boost`, not nature/combo bonus | `0x02158DC4` | Log `r4` before/after and byte at `[sl+0xf8]`; correlate against attacker's own gauge % (per cards 1–2) vs. combo position vs. nature-type advantage | Flag/scale triggers specifically when attacker's gauge ≤25% max, independent of combo position or opponent's nature | Scale correlates with first-hit-in-combo or nature-type-advantage instead (resurrects a refuted reading), or with neither |
| 6 | physics-writers — `+0xE8`/`+0x130` dispatch to two writers on `[sl+0x1b4]` | `0x02158BC0` and `0x02158BCC` | Confirm `r1` at each call == `-(scratch->0xE8)` / `-(scratch->0x130)`; dump `*(r0)=[sl+0x1b4]` at `+0x5C8`/`+0x56C` before/after each call | `r1` magnitudes match; `+0x56C` changes at one call (HP), `+0x5C8` changes at the other (percent-meter) | `r1` doesn't match scratch fields, or neither target field changes as predicted |
| 7 | physics-writers — `0x020781E4` accumulates into `object+0x5C8` (percent/hitstun meter, not velocity) | `0x02078204` | Watch `object+0x5C8` across a single knockback hit | Behaves like a percentage/hitstun meter (monotonic-ish, wraps at 25600) | Decays every frame like a velocity component |
| 8 | physics-writers — `0x020783CC`/`0x02078488` is the HP/gauge clamp, NOT a velocity writer | `0x02078488` | Dump `*r0` at `+0x16`/`+0x18` before/after; compare against any visible debug HP readout | `+0x16`/`+0x18` track current/max HP — settles the question definitively | Values don't track HP — reopens the velocity possibility |
| 9 | physics-writers — ov6 wrapper `+0x6A` (`0x021607C0`) = min-tracker + saturating hit counter, not velocity | `0x021607C0` | Confirm `r0` == wrapper/player pointer (not the deeper char struct); watch `+0x6a`/`+0x38` across several hits | Behaves like a hit-priority/lockout tracker | `+0x6a` decays/accumulates every frame like a velocity component |
| 10 | hitstun-timers — `0x0207D16C` writes `[r0+0xa0]` + sets `[r0+0x78]` bit `0x800000` (hitstun-init candidate; already 2/3-lens-REFUTED as a per-hitbox slot index) | `0x0207D16C` | On a live hit-landing, dump `r0` (diff against the `0x023D2A74` pointer chain) and `r1` (compare to the jpower move's hitstun value); confirm whether `[r0+0x78]&0xFF` becomes `0xC0`-family while `[r0+0xa0]` decrements to 0 | `r0` == known character struct; `r1` matches jpower hitstun; states transition as predicted (would REVERSE the lens's refutation) | `r0` is a per-hitbox record (not the character struct); the `0x800000` OR touches `+0x7A`, not `+0x78` (confirms the lens's refutation) |
| 11 | hitbox-priority — ov6 `0x02159EF8` per-character state dispatcher is the clash-resolution neighborhood | `0x02159EF8` (during a two-character clash) | Dump `r0` (character struct) each hit; inter-frame-diff `r0+0xCB`/`+0xD2`/`+0xD3`/`+0x1A4`/`+0x1A8` and the callee-visible fields inside `0x0215FC78`'s target struct | One of these fields holds an opponent's collision-entry pointer or `hitTier` at the moment both hitboxes overlap | None of these fields ever reflect opponent state — clash resolution lives elsewhere entirely |

---

## Session 2 — Move-Start / MoveInfo Allocation (arm9, fires whenever any attack begins)

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 12 | jpower-indirect — MoveInfo alloc (`0x02156A58`, size `0x1F0`) installed into `char+0x1a8` by `0x021570EC` | `0x02156A58`, then `0x021570F4` | Log size arg (`r0=#0x1f0`) and returned pointer; then confirm `r0` stored into `char+0x1a8` equals that same pointer | Lifecycle confirmed — pointer round-trips cleanly | Different pointer stored, or size differs — the MoveInfo identity assumption is wrong |

---

## Session 3 — Character-ID Table `0x020924B0` (arm9 load-time site + ov0 consumer)

**Setup:** trigger a character load (battle start / roster browse) for card 13; trigger the ending/credits sequence (the known consumer context) for card 14.

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 13 | hitbox-priority — `word0` = ASCII char-ID string, used to build a resource key | `0x0207478C` (or `0x02074790`) | Single-step the copy loop; confirm copied string content; backtrace to see what resource path/filename it ultimately builds | The string ends up in a **collision** resource path | The string ends up in a different resource path (sprite archive, sound, AI, etc. — consistent with the loop-state finding that at least one consumer builds a `.aar` ending-credits key) |
| 14 | hitbox-priority — ov0 `0x0214EFAC` 74-entry scan; 6-bit id in `word1` bits 14–19 (already refuted as chr_b's `classId` by range mismatch: classId spans 256–684, can't fit in 6 bits) | `0x0214EFD8` | Dump the extracted 6-bit id and caller-supplied `r7` across several calls; backtrace the call to `0x0214EFAC` to see what feature (ending/credits vs. gameplay) triggers the scan | The id correlates with something battle-relevant after all (unlikely, given the range mismatch) | Confirms the id is purely an ending/credits-internal index, closing this lead entirely |

---

## Session 4 — Character-Select / Roster Screen (ov5)

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 15 | weight-hunt — chr_b getter `0x0214E480` reads record `+0x0`, gated on `work+6==0` & `work[0xb]>>4==3` | `0x0214E4B8` | When gate conditions hold, confirm `r1` (post-load) equals the byte at `chr_b_record_base + charIndex*0x3C + 0x0` for that `charIndex`; cross-check against `chr_b.json` field 0 | Matches exported `chr_b.json` field 0 (likely FormType) for that roster slot | Mismatch — the getter reads a different offset/table than assumed |
| 16 | weight-hunt — sole caller of the offset-`+0x0` getter fills a roster/select-screen display record, not a battle physics object | `0x02151B88` (after `r7` fields filled) | Inspect memory at `r7` (fields `+2..+7`); inspect call stack/context | Record is destined for a menu/select-screen display — rules OUT weight for this offset | Record feeds into a live battle/physics object — reopens `+0x0` as a weight candidate |
| 17 | movement — only statC consumer (`0x020771C4`/caller `0x0215A31C`) is a koma-technique eligibility check, not a walk-speed selector | `0x020771C4` (or caller `0x0215A31C`) | During ordinary walking/dashing (no koma/technique menu open), confirm whether this function is ever hit purely from movement input | Function fires during plain movement too — walk-speed hypothesis survives | Function is NEVER hit outside menu/eligibility contexts — confirms the cached walk-speed value (if any) must be read from elsewhere |

---

## Session 5 — Shared-Window Move-Flag Test (resident overlay ambiguous: one of ov0/ov2/ov3/ov4/ov5/ov7)

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 18 | weight-hunt — `+0x60` per-index bitfield accessor off the chr_b singleton (`GetFlag(idx)`); one located call site indexes by move-id, not `charIndex` (already 2/3-lens-REFUTED as the passive table) | `0x0214D5A4` | Log `r0` (flag index) across an entire match, across every overlay sharing this address (ov0/ov2/ov3/ov4/ov5/ov7) | ANY call site ever passes a `charIndex`-derived (0–73) value rather than a move-id composite — confirms an innate-passive/ability dispatch table after all | Every call site passes a move-id composite — confirms this is NOT the per-character passive table; the real Edajima-style passive lookup lives elsewhere (see the PassiveIndex lead in the Map's weight-hunt section) |

---

## Session 6 — ov4 Position-vs-Timer Disambiguation

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE (position) | Expected if FALSE (timer / distinct object) |
|---|--------------------|-----------|----------------|--------------------------------|-----------------------------------------------|
| 19 | hitstun-timers — ov4 `0x02151E04`/`0x02151E7C` reads `+0xa0`/`+0xa2` as an (x,y) position pair (already 2/3-lens-REFUTED as a 3rd, distinct vtable-dispatched per-effect struct) | ov4 equivalent of `0x02151E7C` (whichever overlay is resident) | Dump `r4` (`=[r5+4]`), compare against the live `0x023D2A74` character-struct chain; log `[r4+0xa0]`/`[r4+0xa2]` across several frames of a knockback/fall | Large, motion-consistent X/Y deltas | Small monotonic countdown, OR `r4` doesn't match the character struct at all (confirms the lens's "3rd distinct object" reading) |

---

## Session 7 — Projectile Lifecycle (arm9 + ov6, spawn→track→despawn in one sitting)

**Setup:** use a character with a known projectile move (`bb_b_01` or `db_b_01` per `collision-data.round1.json` — both characters' only nonzero-`projectileId` entries have `collisionType=4`). Spawn the projectile, let it fly until it despawns naturally or hits something. **All 5 cards below are PLAUSIBLE-by-default (unverified lenses) regardless of the original CONFIRMED_STATIC label** — see Map.

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 20 | projectile-entities — alloc: manager `0x0214BE14`'s `+0xc`/`+0x14`/`+0x1c` are active/free/pending lists | `0x020834D4` entry (or `0x020834E4`) | Dump `*0x0214BE14` and walk its `+0xc`/`+0x14`/`+0x1c` list anchors before/after the projectile spawns | `+0x14` shrinks (free-list) on alloc, `+0xc` grows (active-list); `+0x1c` untouched on success | Anchors behave differently than this role assignment |
| 21 | projectile-entities — free: `0x02083648` symmetric destructor | `0x02083648` entry | Watch `entity+0x2c` bit 0, the `entity+0x10` hook call, and the `+0xc`→`+0x1c` list transfer when the projectile despawns | Matches the described symmetric alloc/free cycle | Destructor behaves differently (e.g. recycles straight back to `+0x14`) |
| 22 | projectile-entities — spawn dispatch: `[r8+0x1b]` byte correlates with on-disk `ProjectileId`/`CollisionType` | `0x021576C0` | Dump byte at `[r8+0x1b]`; compare with the current move's on-disk `CollisionEntry.ProjectileId`/`CollisionType` (expect `CollisionType==4` per the collision-data sample) | `[r8+0x1b]` correlates with `ProjectileId`/`CollisionType==4` | No correlation — the `+0x1b` byte encodes something unrelated |
| 23 | projectile-entities — ownership: wrapper`+0xc` = attacker's MoveInfo pointer, not the character struct | `0x02168E44` / `0x02168E5C` | Confirm wrapper`+8` = newly allocated entity pointer; wrapper`+0xc` = the attacking character's `char+0x1a8` (MoveInfo) pointer | Matches; also check whether the pooled entity itself carries a more direct character-struct back-pointer elsewhere (unchecked so far) | wrapper`+0xc` holds something else, or a direct char-struct pointer exists on the entity at another offset |
| 24 | projectile-entities — despawn: age counter (32-frame cap) + boundary/threshold checks | `0x0216CA28` and `0x0216CA98` | Watch `entity+4` (age counter) increment to `0x20`(32) and trigger destroy; identify the object behind "r4" (the `+0x100`/second-threshold field) and helper `0x216ee14`'s behavior as the projectile travels off-screen | Age counter caps lifetime at 32 frames; `r4`/helper implement an off-screen or wall-collision check | Projectile persists past 32 frames, or the boundary-test hypothesis for `r4`/helper doesn't hold |

---

## Session 8 — Data-Only Validation (no GDB): full-roster collision-data re-export

**Not a GDB session.** Instead: run the CLI's own `ExportAllCollisions` batch
command (`src/JUS.CLI/JUS/CombatCommands.cs`) against the full character
`.bin` directory to raise coverage from 4/74 to (potentially) 74/74, then
re-run `jus_files/analysis/findings/collision_data_miner.py` against the full
export. Every card below is a re-check of a distributional claim currently
based on only 4 characters (92 entries).

| # | Subsystem / claim | What to re-check | Expected if TRUE | Expected if FALSE |
|---|--------------------|--------------------|--------------------|----------------------|
| 25 | collision-data — `hitTier` occupies closed range `{0,1,2,3}` | Does `hitTier` ever exceed 3 for the 70 previously-unexported characters (meteor/super moves)? | Range stays `{0,1,2,3}` at full scale | Higher tiers appear — the enum is larger than currently observed |
| 26 | collision-data — `collisionType`→`hitTier` skew (type5→87.5% tier3; type3→65.1% tier1) | Does the skew generalize across the roster? | Skew holds or strengthens (promotable toward CONFIRMED_STATIC) | Skew washes out — a small-sample artifact, like the already-corrected knockback-monotonicity claim |
| 27 | collision-data — knockback rises monotonically with `hitTier` once `bl_b_01` is excluded | With 74 characters, does the monotonic rise (8.78→12.11→15.00-style) still hold, or does another character reproduce `bl_b_01`'s anomaly? | Monotonic rise holds at full scale | Some other character(s) reproduce the anomaly, reopening the non-monotonicity question |
| 28 | collision-data — `projectileId` sentinel value `-32` (only 2 observations) | Do any of the 70 newly-exported characters reveal additional nonzero `projectileId` values? | Only `0` and `-32` ever appear (sentinel hypothesis holds) | Other distinct nonzero values appear — `projectileId` is closer to a per-instance/per-type id |
| 29 | collision-data — `collisionType=4` necessary-not-sufficient for nonzero `projectileId` | With more `collisionType=4` entries (only 12 in this sample), does the 2/12 ratio stabilize, and what distinguishes the two groups? | Pattern holds (a minority of type-4 entries are true projectile-spawners) | Ratio shifts dramatically, or a clear distinguishing field emerges |
| 30 | collision-data — `hitProperties` is near-perfectly file-constant per character | At full roster scale, does any single character mix `hitProperties=0` and `=3` within their own moveset? | Each character stays internally consistent (all-0 or all-3) — per-character-trait reading holds | Some character mixes both values — reframes `hitProperties` as a per-hitbox gate after all |
| 31 | collision-data — the two nonzero-`projectileId` instances have opposite `hitProperties` | With more nonzero-`projectileId` instances available, does the "opposite hitProperties" pattern persist? | Pattern (no clean hitProperties↔projectile gating) persists | A consistent single `hitProperties` value accompanies all projectile instances once more data exists |

---

## Critic's GDB-first recommendations

These are the campaign critic's own top-5 picks for where a human's limited
GDB time has the highest cross-subsystem leverage. They substantially
overlap with the sessions above (noted); no new breakpoints are introduced.

1. **Identity check** (→ Session 1, cards 4/6/10) — break `ov6 0x02158BA8`
   (right after `ldr r0,[r1,#0xe8]`); dump `r1` and separately the live
   pointer chain rooted at `0x023D2A74`; compare equality. If equal, every
   open "is this object the documented character struct or a wrapper"
   question from damage-pipeline/physics-writers/hitstun-timers/weight-hunt
   collapses at once.
2. **Hitstun-timer init** (= Session 1, card 10) — break `arm9 0x0207D16C`;
   confirm/deny against a real hit-landing.
3. **Position-vs-timer conflict** (= Session 6, card 19) — break
   `ov4 0x02151E7C`; directly resolves the pre-existing `+0xA0` conflict in
   `docs/research/Character-State-Struct.md`.
4. **Velocity/position fields** (→ Session 1, card 6) — break
   `ov6 0x02158BB4` and `0x02158BC4`; dump the full `+0x6A..+0xBA` byte window
   of `[sl+0x1b4]` before/after a real hit with visible on-screen knockback.
5. **Combo-scale flag scope** (= Session 1, card 5) — break
   `arm9/ov6 0x02158DC4`; log `[sl+0xf8]` continuously across an entire
   multi-hit combo and across a match reset. Can be done in the same sitting
   as recommendation #1 (same function body, same breakpoint region).

---

## Time estimate

| Session | Cards | Estimate |
|---------|-------|----------|
| 1 — Live Hit-Landing (ov6) | 11 | 11×5 + 10 = 65 min |
| 2 — Move-Start/MoveInfo | 1 | 1×5 + 10 = 15 min |
| 3 — Character-ID Table | 2 | 2×5 + 10 = 20 min |
| 4 — Character-Select/Roster (ov5) | 3 | 3×5 + 10 = 25 min |
| 5 — Shared-Window Move-Flag Test | 1 | 1×5 + 10 = 15 min |
| 6 — ov4 Position-vs-Timer | 1 | 1×5 + 10 = 15 min |
| 7 — Projectile Lifecycle | 5 | 5×5 + 10 = 35 min |
| **GDB subtotal** | **24** | **≈190 min** |
| 8 — Data-only re-export (scripted, not manual breakpoint stepping) | 7 | ≈20 min (mostly automated: run `ExportAllCollisions`, re-run the miner, skim 7 refreshed stats) |
| **Total** | **31** | **≈210 min (~3.5 hours) across 8 sessions** |
