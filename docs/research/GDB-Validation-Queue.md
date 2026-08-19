# GDB Validation Queue — Battle Engine Atlas

Every `PLAUSIBLE` and `SPECULATIVE` claim (post-verification, i.e. final
scored confidence) produced by the static RE campaign and its Phase-0
gap-closing loop (`docs/research/Battle-Engine-Map.md`). Every subsystem in
the Map now has adversarial lens verification (3 lenses, or — for the
data-only `collision-data` subsystem — the standard single data-consistency
lens); no claim is carried here purely because verification was skipped. No
claim below has ever been checked against a running emulator; this document
exists so a human can do that with the minimum number of sessions and
breakpoints.

**Cards are grouped into sessions** by overlay/moment so one emulator sitting
can knock out several cards without reloading state. Within a session, set
up the scenario once, then walk the numbered breakpoints in order.

**Card 1 is the single highest-priority breakpoint in this queue.** It
settles the Phase-0 campaign's top open dispute (chrb-catalog claims
3/11/16: does the `+0x558` per-technique node land, unmodified, in the
`+0x56c` gauge pointer ov6 hit-resolution reads?) in one shot, and it reuses
Session 1's setup — nothing extra to configure.

**Total estimate: 30 cards across 8 sessions, ≈230 human-minutes (~3.8
hours)** — see the time table at the end. (The prior version of this queue's
data-only Session 8 — 7 collision-data re-export cards — is retired:
Phase-0's round-2 re-mining already answered every one of those cards
statically; see "Resolved by Phase-0" below.)


> ### Triage 2026-08-14 (Loop-Atlas C5)
>
> **Card 3's parenthetical note was the most valuable line in this document.** Its aside that "a
> sibling DRAIN trampoline exists at `0x020783B8` (same `+0x56c` target, negates its delta)" is
> confirmed, and it unstuck a thread that had cost five loop iterations. Damage passes a *positive*
> magnitude to the drain trampoline, which is why enumerating callers of the plain `0x020783CC`
> found only heals and status ticks. See `findings/c5-damage-field-0x134.md`.
>
> **Cards now settled without an emulator:**
> - **Card 2** — CONFIRMED. `+0x16` = max HP, `+0x18` = current HP, verified live by the harness
>   session *and* statically (`0x02078488` does `ldrsh +0x18` / `adds` / `ldrsh +0x16` / `strh +0x18`,
>   clamped at `0x4000` = 256 displayed).
> - **Card 9** — CONFIRMED, same evidence. `0x020783CC`/`0x02078488` is the HP clamp, not a velocity
>   writer.
> - **Card 3, first half** — CONFIRMED statically: `0x020783CC` resolves `r0` via `ldr r0,[r0,#0x56C]`.
>   The formula half is *not* settled and should be re-derived: the harness measured resistance as a
>   **flat −2**, not a ratio, and the queue's `floor(damage1/5)+(tier-2)` predates the u16 HP
>   correction.
> - **Card 10** — REFRAMED. `+0x6A` is not a standalone field at all; it's record 1, field `+0x6` of a
>   12-byte-strided array. See `findings/c4-physics-is-an-array.md`.
> - **Card 8** — partly settled. `0x020781E4` is the **SP-apply sibling** of the HP apply (19 call
>   sites, each immediately following an HP apply), which supports "a gauge, not velocity".
>
> **Card 12** advanced but not settled: `0x02159EF8` does contain concrete mechanism (the pending-delta
> family at `+0x134`/`+0x138`/`+0x140`/`+0x144`), but no two-entity comparison has been found in it.
>
> The highest-value remaining live check is now in `Human-Testing-Queue.md` as **CARD D1b** — one
> number, `+384`, on one landed hit.

---

## Session 1 — Live Hit-Landing (ov6, function `0x02158B20` and its direct callees)

**Setup:** start a battle, control one attacker landing normal hits on a
defender with the on-screen HP bar visible. For card 6, additionally get the
attacker down to ≤25% of their own gauge to test the desperation-gated path.
For card 12, get two characters' hitboxes to overlap on the same frame
(a clash).

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 1 | **[TOP PRIORITY — chrb-catalog's top open dispute]** Is the `+0x558` per-technique node the same object as the `+0x56c` gauge pointer? Settles 3 claims (3/11/16) at once. | `0x020784E4` (or `0x02077E70`) | At `0x020784E4`: dump the pointer `r4=[r0+0x56c]` right before it reads `+0x16`/`+0x18`. Separately (or in the same session), at `0x02077E70`'s store `0x02077FDC` (`str r5,[r6,#0x56c]`), dump `r5` and compare it against the node addresses the `+0x558` list walker (`0x020783DC`) visits. | The pointer landing in `charPtr+0x56c` is a live node from the `+0x558` list — the aliasing lens's reading is confirmed; the technique-setup cache DOES feed ov6 hit-resolution | `charPtr+0x56c` is a distinct, fixed gauge object never touched by the `+0x558` walker's call graph — the disasm-correctness lens's reading is confirmed; the two mechanisms are genuinely separate |
| 2 | damage-pipeline — `char+0x56c` is a 2-field gauge; `0x02078488`=clamped-add accessor | `0x02078488` | Watch `[r0+0x16]` (max) and `[r0+0x18]` (current) while landing hits that visibly change on-screen HP | `[r0+0x16]` tracks max-HP-like stat; `[r0+0x18]` drops by the delta in `r1` matching the visible HP loss | Fields don't correlate with the HP bar (e.g. track a different gauge — super/guard meter) |
| 3 | damage-pipeline — `0x020783CC` trampoline into the gauge accessor. **Note (Phase-0): a sibling DRAIN trampoline exists at `0x020783B8`** (same `+0x56c` target, negates its delta) — if `r1` here comes back unexpectedly positive on a hit that should decrement HP, check whether that hit routed through `0x020783B8` instead (called from `0x0215AC70`). | `0x020783CC` (and, if needed, `0x020783B8`) | Confirm `r0` resolves to the defender's `char+0x56c` gauge pointer; confirm `r1` (delta) is negative, magnitude == `floor(damage1/5)+(tier-2)` | `r0`/`r1` match as described | `r0` points elsewhere, or `r1` doesn't match the known-good formula |
| 4 | damage-pipeline — `0x02158BC0` call site actually decrements gauge on a real hit | `0x02158BC0` | Same check as card 3, at this specific call site | Same as card 3 | Same as card 3 |
| 5 | damage-pipeline — scratch `+0xE8` = pre-computed per-hit damage magnitude | `0x02158BA8` | Read `[r1+0xE8]`; compare to `floor(damage1/5)+(tier-2)` for the hit that just landed; trace backward for the last store to this field this frame | Value matches formula output; a store instruction is found earlier in the same frame | Value doesn't match, or no write is found this frame (implying a cached/different source) |
| 6 | damage-pipeline — ×1.20 scale = desperation-gated universal `attack_boost`, not nature/combo bonus | `0x02158DC4` | Log `r4` before/after and byte at `[sl+0xf8]`; correlate against attacker's own gauge % (per cards 2–3) vs. combo position vs. nature-type advantage | Flag/scale triggers specifically when attacker's gauge ≤25% max, independent of combo position or opponent's nature | Scale correlates with first-hit-in-combo or nature-type-advantage instead (resurrects a refuted reading), or with neither |
| 7 | physics-writers — `+0xE8`/`+0x130` dispatch to two writers on `[sl+0x1b4]` | `0x02158BC0` and `0x02158BCC` | Confirm `r1` at each call == `-(scratch->0xE8)` / `-(scratch->0x130)`; dump `*(r0)=[sl+0x1b4]` at `+0x5C8`/`+0x56C` before/after each call | `r1` magnitudes match; `+0x56C` changes at one call (HP), `+0x5C8` changes at the other (percent-meter) | `r1` doesn't match scratch fields, or neither target field changes as predicted |
| 8 | physics-writers — `0x020781E4` accumulates into `object+0x5C8` (percent/hitstun meter, not velocity) | `0x02078204` | Watch `object+0x5C8` across a single knockback hit | Behaves like a percentage/hitstun meter (monotonic-ish, wraps at 25600) | Decays every frame like a velocity component |
| 9 | physics-writers — `0x020783CC`/`0x02078488` is the HP/gauge clamp, NOT a velocity writer | `0x02078488` | Dump `*r0` at `+0x16`/`+0x18` before/after; compare against any visible debug HP readout | `+0x16`/`+0x18` track current/max HP — settles the question definitively | Values don't track HP — reopens the velocity possibility |
| 10 | physics-writers — ov6 wrapper `+0x6A` (`0x021607C0`) = min-tracker + saturating hit counter, not velocity | `0x021607C0` | Confirm `r0` == wrapper/player pointer (not the deeper char struct); watch `+0x6a`/`+0x38` across several hits | Behaves like a hit-priority/lockout tracker | `+0x6a` decays/accumulates every frame like a velocity component |
| 11 | hitstun-timers — `0x0207D16C` writes `[r0+0xa0]` + sets `[r0+0x78]` bit `0x800000` (hitstun-init candidate; already 2/3-lens-REFUTED as a per-hitbox slot index) | `0x0207D16C` | On a live hit-landing, dump `r0` (diff against the `0x023D2A74` pointer chain) and `r1` (compare to the jpower move's hitstun value); confirm whether `[r0+0x78]&0xFF` becomes `0xC0`-family while `[r0+0xa0]` decrements to 0 | `r0` == known character struct; `r1` matches jpower hitstun; states transition as predicted (would REVERSE the lens's refutation) | `r0` is a per-hitbox record (not the character struct); the `0x800000` OR touches `+0x7A`, not `+0x78` (confirms the lens's refutation) |
| 12 | hitbox-priority — ov6 `0x02159EF8` per-character state dispatcher is the clash-resolution neighborhood | `0x02159EF8` (during a two-character clash) | Dump `r0` (character struct) each hit; inter-frame-diff `r0+0xCB`/`+0xD2`/`+0xD3`/`+0x1A4`/`+0x1A8` and the callee-visible fields inside `0x0215FC78`'s target struct | One of these fields holds an opponent's collision-entry pointer or `hitTier` at the moment both hitboxes overlap | None of these fields ever reflect opponent state — clash resolution lives elsewhere entirely |

---

## Session 2 — Move-Start / MoveInfo Allocation (arm9, fires whenever any attack begins)

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 13 | jpower-indirect — MoveInfo alloc (`0x02156A58`, size `0x1F0`) installed into `char+0x1a8` by `0x021570EC` | `0x02156A58`, then `0x021570F4` | Log size arg (`r0=#0x1f0`) and returned pointer; then confirm `r0` stored into `char+0x1a8` equals that same pointer | Lifecycle confirmed — pointer round-trips cleanly | Different pointer stored, or size differs — the MoveInfo identity assumption is wrong |

---

## Session 3 — Character-ID Table `0x020924B0` (arm9 load-time site + ov0 consumer)

**Setup:** trigger a character load (battle start / roster browse) for card 14; trigger the ending/credits sequence (the known consumer context) for card 15.

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 14 | hitbox-priority — `word0` = ASCII char-ID string, used to build a resource key | `0x0207478C` (or `0x02074790`) | Single-step the copy loop; confirm copied string content; backtrace to see what resource path/filename it ultimately builds | The string ends up in a **collision** resource path | The string ends up in a different resource path (sprite archive, sound, AI, etc. — consistent with the loop-state finding that at least one consumer builds a `.aar` ending-credits key) |
| 15 | hitbox-priority — ov0 `0x0214EFAC` 74-entry scan; 6-bit id in `word1` bits 14–19 (already refuted as chr_b's `classId` by range mismatch: classId spans 256–684, can't fit in 6 bits) | `0x0214EFD8` | Dump the extracted 6-bit id and caller-supplied `r7` across several calls; backtrace the call to `0x0214EFAC` to see what feature (ending/credits vs. gameplay) triggers the scan | The id correlates with something battle-relevant after all (unlikely, given the range mismatch) | Confirms the id is purely an ending/credits-internal index, closing this lead entirely |

---

## Session 4 — Character-Select / Roster Screen (ov5)

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 16 | weight-hunt — chr_b getter `0x0214E480` reads record `+0x0`, gated on `work+6==0` & `work[0xb]>>4==3` | `0x0214E4B8` | When gate conditions hold, confirm `r1` (post-load) equals the byte at `chr_b_record_base + charIndex*0x3C + 0x0` for that `charIndex`; cross-check against `chr_b.json` field 0 | Matches exported `chr_b.json` field 0 (likely FormType) for that roster slot | Mismatch — the getter reads a different offset/table than assumed |
| 17 | weight-hunt — sole caller of the offset-`+0x0` getter fills a roster/select-screen display record, not a battle physics object | `0x02151B88` (after `r7` fields filled) | Inspect memory at `r7` (fields `+2..+7`); inspect call stack/context | Record is destined for a menu/select-screen display — rules OUT weight for this offset | Record feeds into a live battle/physics object — reopens `+0x0` as a weight candidate |
| 18 | movement — only statC consumer (`0x020771C4`/caller `0x0215A31C`) is a koma-technique eligibility check, not a walk-speed selector | `0x020771C4` (or caller `0x0215A31C`) | During ordinary walking/dashing (no koma/technique menu open), confirm whether this function is ever hit purely from movement input | Function fires during plain movement too — walk-speed hypothesis survives | Function is NEVER hit outside menu/eligibility contexts — confirms the cached walk-speed value (if any) must be read from elsewhere |
| 19 | **[NEW, chrb-catalog]** ov5 "special form" family getters `0x0214E238`/`0x0214E284` — is the FormType read (record `+0`) genuine ARM `ldrb`, or does the disasm DB's apparent Thumb-mode decode past the index computation reflect a real mode switch? | `0x0214E268` and `0x0214E2B8` (right after the `mla`/`smulbb` index computation) | Single-step 2–3 instructions past the breakpoint; confirm the CPU executes an `ldrb`-with-register-offset (reading chr_b record `+0`) | CPU executes a normal ARM `ldrb` — confirms this is a disasm-listing artifact (shared-tail-veneer), not real Thumb code; the `+0` (FormType) reading is confirmed for these 2 sites too | CPU genuinely switches to Thumb mode here — a surprising, previously-undocumented mode switch inside otherwise-pure-ARM ov5 |

---

## Session 5 — Shared-Window Move-Flag Test (resident overlay ambiguous: one of ov0/ov2/ov3/ov4/ov5/ov7)

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 20 | weight-hunt — `+0x60` per-index bitfield accessor off the chr_b singleton (`GetFlag(idx)`); one located call site indexes by move-id, not `charIndex` (already 2/3-lens-REFUTED as the passive table) | `0x0214D5A4` | Log `r0` (flag index) across an entire match, across every overlay sharing this address (ov0/ov2/ov3/ov4/ov5/ov7) | ANY call site ever passes a `charIndex`-derived (0–73) value rather than a move-id composite — confirms an innate-passive/ability dispatch table after all | Every call site passes a move-id composite — confirms this is NOT the per-character passive table; the real Edajima-style passive lookup lives elsewhere (see the PassiveIndex lead in the Map's weight-hunt section) |

---

## Session 6 — ov4 Position-vs-Timer Disambiguation

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE (position) | Expected if FALSE (timer / distinct object) |
|---|--------------------|-----------|----------------|--------------------------------|-----------------------------------------------|
| 21 | hitstun-timers — ov4 `0x02151E04`/`0x02151E7C` reads `+0xa0`/`+0xa2` as an (x,y) position pair (already 2/3-lens-REFUTED as a 3rd, distinct vtable-dispatched per-effect struct) | ov4 equivalent of `0x02151E7C` (whichever overlay is resident) | Dump `r4` (`=[r5+4]`), compare against the live `0x023D2A74` character-struct chain; log `[r4+0xa0]`/`[r4+0xa2]` across several frames of a knockback/fall | Large, motion-consistent X/Y deltas | Small monotonic countdown, OR `r4` doesn't match the character struct at all (confirms the lens's "3rd distinct object" reading) |

---

## Session 7 — Projectile Lifecycle (arm9 + ov6)

**Setup:** use a character with a known projectile move (`bb_b_01` or
`db_b_01` per `collision-data.round1.json` — both characters' only
nonzero-`projectileId` entries have `collisionType=4`). Spawn the projectile,
let it fly until it despawns naturally or hits something.

**3-lens verification completed this phase (P3):** 4/5 original claims are
now CONFIRMED_STATIC (alloc, free, spawn dispatch, spawn+ownership); only
the despawn function remains PLAUSIBLE. Two former cards were dropped as
answered statically — see "Resolved by Phase-0" below. The cards remaining
below check open semantic/behavioral questions the static verification
could *not* settle.

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 22 | projectile-entities — manager `0x0214BE14`'s `+0xc`/`+0x14`/`+0x1c` are active/free/pending lists (mechanism CONFIRMED; semantic role labels still inferred from control flow only, never proven against a live dump) | `0x020834D4` entry (or `0x020834E4`) | Dump `*0x0214BE14` and walk its `+0xc`/`+0x14`/`+0x1c` list anchors before/after the projectile spawns | `+0x14` shrinks (free-list) on alloc, `+0xc` grows (active-list); `+0x1c` untouched on success | Anchors behave differently than this role assignment |
| 23 | projectile-entities — spawn dispatch: `[r8+0x1b]` byte correlates with on-disk `ProjectileId`/`CollisionType`. **Note: the confirmed dispatcher case selector is `r2=7`, not 8 as originally labeled** — the dispatch mechanism itself is otherwise CONFIRMED_STATIC. | `0x021576C0` | Dump byte at `[r8+0x1b]`; compare with the current move's on-disk `CollisionEntry.ProjectileId`/`CollisionType` (expect `CollisionType==4` per the collision-data sample) | `[r8+0x1b]` correlates with `ProjectileId`/`CollisionType==4` | No correlation — the `+0x1b` byte encodes something unrelated |
| 24 | projectile-entities — despawn: age counter (32-frame cap, with a suppression bit at `[entity+6]&0x2` found this phase) + boundary/threshold checks. **Capped PLAUSIBLE — cannot be statically proven specific to projectiles** (the aliasing lens found ≥2 sibling ov6 functions reusing the identical scaffolding). | `0x0216CA28`, `0x0216CA74`, and `0x0216CA98` | Watch `entity+4` (age counter) increment to `0x20` (32) and trigger destroy unless `[entity+6]&0x2` suppresses it; identify the object behind `r4` (the `+0x100`/second-threshold field) and helper `0x216ee14`'s behavior as the projectile travels off-screen; separately, break the same age-counter idiom in sibling functions `0x0216E1C0`/`0x0216F398` to check whether THIS is projectile-specific or shared | Age counter caps lifetime at 32 frames (modulo the suppression bit); `r4`/helper implement an off-screen or wall-collision check; sibling functions handle a *different* entity kind | Projectile persists past 32 frames even with the suppression bit clear, or the sibling functions turn out to handle the SAME entity kind (would mean `0x0216C958` isn't uniquely "the" projectile despawn routine even architecturally) |

---

## Session 8 — Guard/SP Gauge Mechanics (guard-sp-gauges, new this phase)

**Setup:** a single "combo dojo"/practice-mode session against a dummy
covers cards 25–28 (trigger a mix of guard blocks, SP-spending specials, and
a status effect). Card 29 needs a "max HP on respawn"-style passive
equipped (candidate ability `0x07`). Card 30 needs a full match plus a
save-state reload (to observe `char+0x558` from a cold start).

| # | Subsystem / claim | Breakpoint | What to check | Expected if TRUE | Expected if FALSE |
|---|--------------------|-----------|----------------|--------------------|----------------------|
| 25 | guard-sp-gauges — dispatchers `0x02157A44`/`0x0215807C` route battle-event opcodes to the HP trampoline vs. the `char+0x5c8` counter vs. the `+0x558` list walker | `0x02157A44` and `0x0215807C` | Log `r2` (opcode, dispatcher 1) / `r3` (opcode, dispatcher 2) and the delta register on entry across many distinct battle events (guard block, SP spend, status tick, HP hit) to build an opcode→target table | A cluster of opcode values routes specifically to the `+0x558` walker (candidate guard/SP opcodes), distinct from the HP-trampoline opcode cluster | Opcodes routing to the `+0x558` walker are indistinguishable in kind from HP-trampoline opcodes — no clean guard/SP-vs-HP opcode split exists |
| 26 | guard-sp-gauges — scaling wrapper trio `0x02159260`/`0x021592C0` (×64/unscaled, target HP) and `0x02159280` (×256, target `+0x5c8`) all read the same `[[r1+4]+4]` signed halfword source | `0x02159260`, `0x021592C0`, `0x02159280` | Dump `[[r1+4]+4]` and its sign at each; determine what kind of object `r1` (2nd wrapper argument) is, and whether the ×64/×256 scale factors convert a shared "raw stat" unit into each target's own units | A single shared raw-stat source feeds all three gauges via different fixed scale factors (unit-conversion reading confirmed) | The three wrappers' source values are unrelated/uncorrelated in practice — the shared-template reading is cosmetic only |
| 27 | guard-sp-gauges — eligibility codes `0x1b`(27)/`0x1d`(29) gate wrappers `0x02159500`/`0x02159624` via predicate `0x0215986C`→`0x2158eb0(charPtr+0x120, code)` | `0x0215986C` | Log `r5` (char ptr), the `r2` code (`0x1b`/`0x1d`), and the return of `0x2158eb0` across different attack/status types (guard-break, poison/burn per the existing ailment-code hypothesis, elemental match, etc.) | Codes 27/29 map cleanly onto two known status-effect types (e.g. Burn/Poison) — confirms these gate a battle-*effect* type, orthogonal to gauge selection | Codes correlate with something gauge-specific instead — reopens the "these select a gauge kind" alternative |
| 28 | guard-sp-gauges — `0x0215A318`/`0x02159EF8` feeds the HP trampoline from `[[charPtr+0x1a8]+0x10]+0x140`, unnegated (passive-fill/DoT-tick candidate) | `0x0215A2D0` and `0x0215A308` | Log the signed value at `[[charPtr+0x1a8]+0x10]+0x140` and its sign every frame on a status-effect-afflicted character; also check the `+0xcc` enable-gate and the "run once" sticky flag at `[r6+0x14]` bit 0 | Value is negative during a damage-over-time effect (poison/burn tick) and/or positive during a regen effect — confirms a per-frame passive/DoT tick, not a one-shot hit | Value stays at 0 outside of a specific one-shot event, or behaves like a one-shot-hit magnitude instead |
| 29 | guard-sp-gauges — `GrowMax` caller `0x0215C73C` = "max HP on respawn" passive (bit `0x80` of `char+0x128`, fixed `+0x400` delta) | `0x0215C73C` | Equip a candidate "max HP up" passive, trigger a respawn/tag-in; confirm bit `0x80` of `char+0x128` is set and that `[charPtr+0x56c]+0x16` (max) increases by exactly `0x400` (1024) | Matches — identifies the concrete equip/passive that sets this bit | Bit never sets for any equipped passive tested, or the max-HP field doesn't move by exactly 1024 — reopens what triggers this path |
| 30 | guard-sp-gauges — `+0x558` node census + insertion-site watch (no store into `char+0x558` other than the one zero-init was found statically) | `watch *(charPtr+0x558)` for writes; also break `0x020783DC` across a full match | Catch the actual node-constructor/insertion write (candidate: a split `add rX,#0x558`+register-offset store, invisible to static `search-imm`); separately, log every distinct node address and its `+0x00`(next)/`+0x16`(max)/`+0x18`(cur)/`+0x3c`/`+0x40`(flags) fields walked by `0x020783DC` to census how many node "kinds" exist (guard? SP? both? shared across a 3-character deck?) | A concrete insertion site is found; the node census reveals ≥2 distinct node kinds (or a single shared node referenced by multiple character structs, resolving the SP deck-shared-vs-per-character tension) | No insertion write is ever caught (nodes might be statically pre-linked at ROM-load rather than dynamically inserted); all census'd nodes look identical (single generic node type, tension unresolved) |

---

## Resolved by Phase-0 (no longer queued)

These cards from the prior version of this queue are dropped — the question
each was designed to answer is now settled statically (via 3-lens
verification or full-roster re-mining), with no live-behavior question left
to check.

- **Former Session 7 card — destructor active→pending symmetry.** CONFIRMED via 3-lens verify (P3): the destructor's mechanics (`entity+0x2c` bit-0 set, `+0xc`→`+0x1c` list transfer) were re-confirmed byte-for-byte by independent re-disassembly.
- **Former Session 7 card — ownership wrapper `+0xc` = MoveInfo, not character struct.** CONFIRMED via 3-lens verify; the aliasing lens additionally found the direct character-struct back-pointer at wrapper `+0x18` (written by the dispatcher's caller), closing the "more direct back-pointer" open question too. See `Battle-Engine-Map.md` § projectile-entities claim 4.
- **Former Session 8 (collision-data data-only re-export), all 7 cards.** Superseded wholesale: P1+P2 ran the full 74-battle + 206-support re-export and re-mining this phase.
  - `hitTier` range `{0,1,2,3}` — holds at full scale.
  - `collisionType`→`hitTier` skew generalizing — REFUTED; the real rule is `collisionType ∈ {4,5}` (union), not a clean per-type skew, and both individual correlations weaken to near-coin-flip (47.58% / 58.98%).
  - Knockback monotonic once `bl_b_01` excluded — REFUTED again at full scale; 55/74 (74%) characters are individually non-monotonic.
  - `projectileId=-32` sentinel — REFUTED; 15 distinct nonzero values in battle files, 25 in support.
  - `collisionType=4` necessary for nonzero `projectileId` — REFUTED; real rule is the `{4,5}` union.
  - `hitProperties` per-character constancy — PARTIALLY REFUTED; 26/74 (35%) characters DO mix values within one file (65% remain constant).
  - Opposite-`hitProperties`-on-projectiles pattern — REFUTED; `hitProperties=1` dominates (68%) the nonzero-`projectileId` subset instead.

  See `Battle-Engine-Map.md` § collision-data for the full round-2 table.

---

## Critic's GDB-first recommendations (refreshed, Phase-0)

These are the highest cross-subsystem-leverage picks in the current queue.
Each substantially overlaps with the sessions above; where a recommendation
adds a static (non-GDB) follow-up alongside a breakpoint, that is noted.

1. **chr_b cache identity** (= Session 1, card 1) — **new top pick this
   phase.** Break `0x020784E4` (or `0x02077E70`); compare the pointer
   landing in `charPtr+0x56c` against `+0x558`-rooted node addresses.
   Settles chrb-catalog claims 3/11/16 (3 claims) in one shot — the single
   highest-leverage item this phase discovered.
2. **Object identity** (→ Session 1, cards 5/7/11) — break `ov6 0x02158BA8`
   (right after `ldr r0,[r1,#0xe8]`); dump `r1` and separately the live
   pointer chain rooted at `0x023D2A74`; compare equality. If equal, every
   open "is this object the documented character struct or a wrapper"
   question from damage-pipeline/physics-writers/hitstun-timers/weight-hunt
   collapses at once.
3. **Drain-trampoline / `bx ip` sibling sweep** (→ Session 1, card 3;
   Session 8, card 30) — **new this phase.** Confirm `0x020783B8`'s `rsb`
   negation feeds the same `+0x56c` HP gauge (not a hidden second gauge);
   alongside that breakpoint, manually sweep the ROM for further
   `ldr ip,[pc,#N]/ldr r0,[r0,#M]/bx ip`-shaped trampolines with `M != 0x56c`
   — this closes the `xrefs-to`/`pool-values` blind spot this phase
   demonstrated is real and load-bearing, not theoretical.
4. **Hitstun-timer init** (= Session 1, card 11) — break `arm9 0x0207D16C`;
   confirm/deny against a real hit-landing.
5. **Position-vs-timer conflict** (= Session 6, card 21) — break
   `ov4 0x02151E7C`; directly resolves the pre-existing `+0xA0` conflict in
   `docs/research/Character-State-Struct.md`.

(Two items from the pre-Phase-0 top-5 — velocity/position-field dumping and
combo-scale flag scope — remain queued as Session 1 cards 7 and 6
respectively; they're no longer in the top 5 given this phase's higher-leverage
discoveries, but are unchanged and still worth doing in the same sitting.)

---

## Time estimate

| Session | Cards | Estimate |
|---------|-------|----------|
| 1 — Live Hit-Landing (ov6) | 12 | 12×5 + 10 = 70 min |
| 2 — Move-Start/MoveInfo | 1 | 1×5 + 10 = 15 min |
| 3 — Character-ID Table | 2 | 2×5 + 10 = 20 min |
| 4 — Character-Select/Roster (ov5) | 4 | 4×5 + 10 = 30 min |
| 5 — Shared-Window Move-Flag Test | 1 | 1×5 + 10 = 15 min |
| 6 — ov4 Position-vs-Timer | 1 | 1×5 + 10 = 15 min |
| 7 — Projectile Lifecycle | 3 | 3×5 + 10 = 25 min |
| 8 — Guard/SP Gauge Mechanics | 6 | 6×5 + 10 = 40 min |
| **Total** | **30** | **≈230 min (~3.8 hours) across 8 sessions** |
