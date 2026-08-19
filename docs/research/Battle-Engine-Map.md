# Battle Engine Map — Jump Ultimate Stars Static RE Atlas

**Campaign date:** 2026-07-02. This is the canonical artifact of a static
reverse-engineering campaign against the JUS (NDS) battle engine binary
(`arm9.bin` + 14 overlays). Every claim below was extracted by a tracer
subagent working exclusively through a disassembly/xref query layer (never
"eyeballed"), then machine-verified: every cited instruction was re-queried
and string-matched against the actual disassembly database
(`verify_evidence.py`), and every claim ran through three independent
adversarial verification lenses (**disasm-correctness**, **aliasing**,
**data-consistency**) before its confidence label was finalized. No GDB/emulator
execution occurred anywhere in this campaign — GDB work is captured as cards
in `docs/research/GDB-Validation-Queue.md` for a human to run. Confidence
labels (`CONFIRMED_STATIC` / `PLAUSIBLE` / `SPECULATIVE`) are preserved
verbatim from that verification pipeline throughout this document; where a
claim's original confidence differs from its post-verification (scored)
confidence, both are shown.

**Phase-0 update (2026-07-02):** a follow-up gap-closing loop
(`docs/design/Static-RE-Phase0.md`) closed every "verification pending" gap
the original campaign left open — `projectile-entities` now has full 3-lens
verification (see its section below), `collision-data` was re-mined at
full-roster scale (round 2, 281/281 files), and two new subsystems
(`guard-sp-gauges`, `chrb-catalog`, specs B12/B14) were traced and verified
end-to-end. No claim in this document is unverified as of this update; see
`scripts/analysis/loop-report-phase0.md` for the phase's morning report.

---

## Memory-Map Primer

- **arm9** is mapped at `0x02000000` (the base image; all "arm9:" addresses
  below are absolute ROM/RAM addresses in this range).
- **14 overlays** (`ov0`–`ov13`) load at various fixed addresses. Three
  regions **overlap** — overlays sharing an address window are mutually
  exclusive at runtime (only one of the group can be resident at a time):
  - `ov0`–`ov9` (10-way overlap) all load at `0x0214CD20`. Within this group,
    **`ov6` is the live battle overlay** and **`ov5` is the menu / Jump
    Galaxy (deck-builder) overlay** — since they share the same window, **ov5
    and ov6 cannot both be resident**, which is load-bearing evidence for
    several claims below (notably jpower-indirect).
  - `ov10`/`ov11` overlap at `0x02172A60`.
  - `ov12`/`ov13` overlap at `0x021AC1C0`.
  - `ov9`/`ov13` are 32-byte stubs (not meaningfully populated).
  - No overlay compression was observed.
- **Implication for every address below:** an address that falls inside one
  of the three overlapping windows is only meaningful with overlay context;
  where a claim's home overlay could not be pinned down (a handful of
  weight-hunt/movement sites reached through "shared-window" code), that
  ambiguity is called out explicitly rather than guessed.

---

## Subsystem: damage-pipeline

**Terminology correction (iteration 50): the `0x02157A60` dispatcher is a *query* interface, not a command interface.** All seven live cases in the issued 64–73 band return a boolean (`mov r0,#1` → `0x02157F94`, else `0x02157F90` → `mov r0,#0`) and mutate nothing; the forwarder acts on the result (`cmp r0,#0; ldrbne r1,[note+2]; strbne r1,[note+1]`). So a NoteTrack asks the character "is condition N true?" and advances the note only if so. Signature: `query(r0 = NoteTrack, r1 = character, r2 = query number, r3 = parameter, +2 stack args) -> bool`. Cases 23/24/32 below really do call the HP/SP apply functions, but nothing issues those numbers — see the iteration-47 note. Details and the seven queries in `findings/commands-are-predicates.md`.

**HP/SP application is command-dispatched (2026-08-15, iteration 46).** The apply functions are reached as numbered cases of the 73-case per-character dispatcher at ov6 `0x02157A60` (`cmp r2,#72; addls pc,pc,r2,lsl#2`, table `0x02157A68`–`0x02157B88`, `BattleChara.cpp`):

| command | case target | calls |
|---|---|---|
| **23** | `0x02157DB8` | `0x020783CC` — the HP-apply trampoline |
| **24** | `0x02157DC8` | `0x020781E4` — the SP apply |
| **32** | `0x02157E04` | `0x020783DC` — HP-apply sibling |

This adds no new caller (`0x02157DB8` is almost certainly among the 8 ARM script-effect sites already counted) but it reframes **campaign item B11, "who computes the delta"**: the delta arrives as an *argument to a command*, so the producer is whatever fills the dispatcher's arguments — not anything inside the apply path. Full case map in `findings/73-case-dispatcher-enumerated.md`.

**(2026-08-15, iteration 47 — that B11 approach is a DEAD END.)** The dispatcher is installed exactly once, into `noteTrack+0x70` (`str r6,[r4,#0x70]` at `0x02155438` inside `Battle_NoteTrackCreate` `0x021553E0`, which `Battle_CharaCreate` calls at `0x02156CE4` passing the dispatcher in `r3`). Every command issued through that field is enumerated: **{3, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73}** — **23 and 24 never appear**. So cases 1–33 except 3 look unreachable in this build (PLAUSIBLE; 4 variable-`r2` sites on unidentified base types remain). The 8 ARM script-effect callers of `0x020783CC` stay the real HP-delta path, and case 23 is a second, unused entry point.

**Architectural payoff:** `character+0x1a8` holds the NoteTrack (a `0xA8`-byte move-script engine) at `+0x18` *and* the pending-delta struct at `+0x10`. Iteration 40's collision stub bank is NoteTrack code, and its 16-byte slot records are the notes — the forwarder `0x02156520` ticks a counter at note`+0x04` and moves note`+0x02` into note`+0x01`. See `findings/notetrack-issues-the-commands-b11-dead-end.md`.


**Status:** PARTIAL (4 confirmed / 3 plausible / 2 speculative claims)

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | `0x020784FC` (the GDB seed anchor) lives inside function `0x020784E4`, which is **not** the per-hit damage formula. It computes a boolean: `(current <= max * pct / 100)` on the gauge at `charPtr+0x56c` (`+0x16`=max, `+0x18`=current). | `0x020784E4`, `0x020784FC` | **CONFIRMED_STATIC** |
| 2 | Both known static callers pass literal `pct=25` (`0x19`) — the check is specifically "is current ≤ 25% of max", not a tunable threshold. | `0x02158D84`, `0x02160918` | **CONFIRMED_STATIC** |
| 3 | The `/100` inside `0x020784E4` is a call to the generic signed-division subroutine `0x0200D12C` with `r1=0x64`, not an inlined magic-multiply. | `0x0200D12C` | **CONFIRMED_STATIC** |
| 4 | No inlined ÷5 magic-multiply exists anywhere near the damage code: a ROM-wide pool-values scan for both canonical constants (`0x66666667` signed, `0xCCCCCCCD` unsigned) found only 4 occurrences total, all in unrelated routines (a Gregorian date function, two ÷13/÷7 calendar routines, a sprintf digit-extractor). | `0x02056394`, `0x020586AC`, `0x02058750`, `0x0205237C` | **CONFIRMED_STATIC** |
| 5 | `char+0x56c` is a two-field gauge (`+0x16` max, `+0x18` current, a.k.a. "Meter"). `0x02078488` = `ApplyDeltaToCurrent` (clamped add, returns alive flag); `0x020784B8` = `GrowMax` (capped at `0x4000`). | `0x02078488`, `0x020784B8` | **PLAUSIBLE** |
| 6 | `0x020783CC` is a 2-instruction trampoline: loads `charPtr->+0x56c` into r0, tail-jumps into `0x02078488`. Called from 8 sites in ov6 (only 1 disassembled this round). | `0x020783CC` | **PLAUSIBLE** |
| 7 | Inside the GDB-verified caller `0x02158B20`, the site at `0x02158BC0` invokes the trampoline with `r1` = a negated scratch value — the strongest static candidate for "where computed damage gets applied." | `0x02158BC0` | **PLAUSIBLE** |
| 8 | The same function reads two signed 32-bit fields (`+0xE8`, `+0x130`) off a scratch base `[[charPtr+0x1a8]+0x10]`, negates both, feeds `-field_0xE8` into the trampoline. `+0xE8` is the strongest candidate for "already-computed per-hit damage magnitude," but its writer was not located across 3 rounds of searching. | `0x02158BA8`–`0x02158BCC` | **SPECULATIVE** |
| 9 | A distinct **×1.20** scale (not ×1.5) applies at `0x02158DC4`–`0x02158DD0`, gated by a one-shot flag `[sl+0xf8]`. Disassembly arithmetic **UPHELD by all 3 lenses**; the semantic label "nature ×1.5 advantage multiplier" was **REFUTED by 2/3 lenses**. | `0x02158DC4` | **SPECULATIVE** |

**Reframing note (claim 9):** the ×1.20 scale's disassembly is real and confirmed, but its *meaning* is not "nature advantage." Cross-referencing against claims 1–2 (the confirmed 25%-of-max gauge check) suggests the correct reading is that this is the documented universal **`attack_boost`** multiplier, causally gated by the same 25%-gauge desperation check rather than by a Power/Knowledge/Laughter type triple. No code selecting a type-advantage multiplier was found anywhere in this pass.

### Refuted hypotheses (damage-pipeline)

- **`0x020784FC` = gauge-threshold, not the damage formula.** The address is real and inside the correct neighborhood, but it computes "is current ≤ 25% of max," not `floor(damage1/5)+(tier-2)`.
- **No inlined ÷5 magic-multiply anywhere near damage code** (claim 4) — ROM-wide, both canonical ÷5 constants together appear only 4 times, none combat-related.
- **The ×1.20 scale is not the documented ×1.5 nature-advantage bonus**, and is also *not* a first-hit/combo-starter bonus (an alternative guess raised and not supported); the desperation-gated `attack_boost` reading is the best current interpretation but is itself unconfirmed by GDB.

### Open questions

- Who writes `[[charPtr+0x1a8]+0x10]+0xE8` (and `+0x130`)? This is the single highest-value unresolved item in the whole campaign — see next-campaign spec **B11**. **(2026-08-15, iteration 75 — the target is now sharp.** `[[char+0x1a8]+0x10]` is the object installer `0x0207C988` **returns** (`mov r0,r4` at `0x0207CB34`), stored at `entity+0x10` by `0x02083564`. It is the same object as the ColObj owner `[ColObj+0x28]` and the `0x2C`-byte pool-node owner — three separately-tracked objects, one struct. So `+0xE8` lives on a base that also carries `+0x40` flags, `+0x60` (the ColObj) and the `0xD0`-byte region from `+0xA4`, and `+0xE8` is **zeroed at installation** by that memset. See `findings/entity-0x10-is-the-colobj-owner-and-the-damage-scratch-object.md`.)* **(2026-08-15, iteration 76 — the writer does not exist in any offset-encoded store.** An exhaustive ROM-wide sweep finds **27** ARM immediate-offset stores to `+0xE8`, **0** in ov6, **0** sharing a distinctive companion offset with the owner, and **0** split-offset (`add`+`str`) stores. Both arm9 candidates are refuted (`0x02046914` has a pc-relative global base; `0x0207C684` is `Battle_ColPrmManCreate`'s own `+0xE8`). The only confirmed write is the installation memset. With sibling `+0x140` already observed as `0` at runtime, **`+0xE8` is PLAUSIBLY vestigial in retail and B11 may be the wrong question** — one harness read settles it. Blind spots quantified in `findings/owner-0xE8-has-no-writer-b11-narrowed.md`.)* **(2026-08-15, iteration 77 — the struct is NAMED AND SIZED.** Sweeping block writes found its teardown `0x0207CCD4`, which `memset`s **exactly `0x188` bytes** and returns it to a free pool on the **ColPrm manager** (fingerprinted by the `+0xFC`/`+0x100`/`+0x104` phase-table dispatch at `0x0207FB6C`–`0x0207FB8C`). So the damage-pipeline scratch object **is a per-entity ColPrm record** from `BattleColPrm.cpp`. Also resolves iteration 69's unclaimed question: `ColPrm+0x08` is the record free pool and `ColPrm+0x10` the active list. `+0xE8` is still only ever memset. See `findings/the-owner-is-a-colprm-record-0x188-bytes.md`.)* **(iteration 78 — 24 fields of the record mapped.** `+0xE8`, `+0x130`, `+0x140` and `+0x144` **all lie inside the `+0xA4`–`+0x173` memset region**, and `+0x40` is reached independently from arm9 (`0x0207CB24`) and ov6 (`0x02158B9C`) — the first cross-binary evidence that the collision installer and the damage pipeline touch one object, previously resting only on an address expression. The highest field is a halfword at `+0x186` = `0x188 - 2`, confirming the size from a second direction. Partial map: 24 fields from six anchors. See `findings/colprm-record-field-map.md`.)* **(iteration 79 — `+0x90`/`+0x94`/`+0x98` are NOT sub-structures.** They are **three parallel `int16[2]` arrays** spanning `+0x90`–`+0x9B`, all six entries set to `-1` by one 2-iteration loop at `0x0207CB08`–`0x0207CB20`. No reader is attributable, and the cause is a newly quantified blind spot: **post-indexed addressing** (`strh r2,[r5],#2`), which every scan here silently skips — 331 sites in arm9, only 8 in ov6. See `findings/colprm-record-three-index-arrays.md`.)* **(iteration 80 — `+0x9A` was a PHANTOM; the record map is 20 offsets, not 21.** `struct_fields.py` was not blind to post-indexed addressing, it **decoded it wrongly**: `ldrsh r2,[r6],#2` accesses offset **0** and then advances the base, but the tool reported the stride as the offset. Two further encoding bugs fixed alongside — base writeback defeated the reassignment guard, and `U = 0` down-offsets were reported as positive. Affected population ROM-wide: 456 post-indexed, 46 writeback, 625 negative, of 106359 transfers. See `findings/post-indexed-addressing-was-decoded-wrongly.md`.)* **(iteration 81 — the `+0xE8` sweep recounted on a raw-word decoder: 47 sites, not 27.** The old text regex could not match **conditionally executed** stores (`strne`, `strgt`, `strlo`) — 19 of 47, 40%, silently dropped. Gained 19, **lost 0**. **B11 is unaffected:** restricted to arm9 and ov6 the result is identical — the same two sites, both already refuted, no companion matches, no split stores. See `findings/text-matching-missed-every-conditional-store.md`.)* **(iteration 83 — the record has FOUR list heads, not one.** `0x0207CB58` is its **detach routine**, called at entity teardown from `0x02083648` — the mirror of iteration 74's attach-at-construction. It drains `+0x10` (`0x10`-byte nodes → `mgr+0x20`), `+0x18` and `+0x20` (bucket nodes → `mgr+0xD8`), then sweeps all **22** manager buckets for nodes owned by this record. `record+0x68` is a **partner link**, cleared to `0` here and read by the teardown; PLAUSIBLY another ColPrm record. Note the live hazard: `+0x18`/`+0x20` are ALSO the manager's free pools — same offsets, different structs. See `findings/colprm-record-detach-and-four-list-heads.md`.)* **(iteration 84 — `record+0x68` is NEVER SET.** ColPrm-aware code is confined to arm9 `0x0207C83C`–`0x0207D99C` plus two ov6 sites, and **every** write form in that band was enumerated: 1 direct store (writes `0`), 4 register-offset, 2 `stm`, 2 post-indexed — none can reach `+0x68`. So the teardown's `cmp r2,#0; beq` guard always branches and its partner walk is **dead code in retail**. That is the struct's **second** vestigial field after `+0xE8`, with `+0x140` observed as `0` at a live breakpoint — three fields, three independent routes. Iteration 83's four list heads are on the fallthrough path and unaffected. See `findings/record-0x68-is-never-set-second-vestigial-field.md`.)* **(iteration 85 — the record map is now 23 offsets, derived automatically.** A **strided pointer walk** (`add r6,sl,#0x10` / `add r6,r6,#8` / `cmp r8,#3`) never expresses `+0x18` or `+0x20` relative to the anchor register, so an anchor walk saw only `+0x10`. New guard 11 recovers the group and the tool now reproduces iteration 83's hand reading. See `findings/strided-list-heads-guard-11.md`.)* **(iteration 86 — the offset audit is CLOSED and the map was right.** All three disputed offsets belong to the ov6 `0x1F0` battle character: `+0x1B4` (10 accesses) and `+0x1B8` (4) on `Battle_CharaCreate`'s allocation register, and `+0x84` via `0x02159AA0`, where the same unreassigned base carries `+0x1A0` at `0x02159A78`. Nothing needs revising. Eight new character fields found: `+0x07C`, `+0x120`, `+0x130` (address-taken), `+0x1A0`, `+0x1A4`, `+0x1BC`, `+0x1CC`, `+0xA2`. **Hazard:** `+0x84` is *also* a NoteTrack field, read 5× by the dispatcher `0x02157A44` — establish the base before attributing any `+0x84` hit. See `findings/char-offset-audit-resolved.md`.)* **(iteration 87 — `char+0x130` is the shared view.** `+0x120` and `+0x130` are **embedded sub-objects**, not arrays, built by two 12-byte constructors: `+0x120` = {`&char+0x130`, `[char+0x1b4]`}; `+0x130` = {`[char+0x1b4]`, `&char+0x7c`, the character}. `char+0x130`'s address is taken **29 times** in ov6, concentrated in the three subsystems this map already documents separately — the state dispatcher `0x02159EF8` (×10), the spawn dispatcher `0x021574CC` (×4, claim 3) and hit resolution `0x02158B20` (×2, claim 8). They share one handle. **Hazard:** the ColPrm record also has a `+0x130`, and `0x02158B20` uses both. See `findings/character-embedded-views-0x120-0x130.md`.)* **(iteration 88 — the view carries a 16-entry GATED HANDLER TABLE.** `view+0x0C` is a 32-bit enable mask; `0x0215FC78(view, N)` runs `table[N]` at `0x0217221C` only if bit `N` is set. The table has exactly **16** entries — index 16 onward is the ASCII `"Battle_CharaInfo"` — with indices 0–3 sharing one no-op and 9 unique handlers. `view+0x16` is an `int16` array indexed by the same selector. The state dispatcher exercises selectors 4, 6, `0xA`, `0xE`, `0xF`. The view runs to `+0x6A` and is **bounded at `0x70`** by the confirmed `char+0x1A0`, so it is **not** `Battle_CharaInfoCreate`'s `0xAC` heap object. See `findings/char-0x130-is-a-gated-handler-table.md`.)* **(iteration 89 — all 16 selectors enumerated: 12 live, 4 dead.** 17 call sites, 17 immediate selectors, 0 computed. Selectors **4–15 are all issued; 0–3 never are** — and 0–3 are exactly the four table slots sharing the no-op `0x0215FFDC`, so the table's dead entries and the unissued selectors coincide from two independent directions. Each selector has one issuing function (`0xD` excepted): state dispatcher `0x02159EF8` issues 4/6/`0xA`/`0xE`/`0xF`, hit resolution `0x02158B20` issues 9 and `0xB`, the spawn dispatcher `0x021574CC` issues `0xD`. Same architecture as the 73-case dispatcher. See `findings/view-handler-selectors-enumerated.md`.)* **(iteration 90 — the handlers are a LIVE path into SP-apply `0x020781E4`.** Selectors 9 and 12 (`0x0215FF4C`) tail-call it with `view+0x16[N]` as the amount and `view+0x00` = `[char+0x1b4]` as the target; selectors 13 and 14 (`0x0215FF64`) apply the `+0x64` scratch halfword the same way, skipping when zero. **All four are issued**, from hit resolution `0x02158B20` and the state dispatcher — so `0x020781E4` is not a dead function; only the *dispatcher's* cases 23/24 route to it is dead. Also found: `view+0x14` is a counter capped at `0x2D0`, and a **second `int16` array at `view+0x36`**, contiguous with the one at `+0x16`. See `findings/view-handlers-are-the-live-sp-apply-path.md`.)* **(iteration 91 — all 16 handlers read, and `[char+0x1b4]` IS the `+0x56c` struct.** Handler `0x0215FE14` does `ldr r0,[r5]` (= `[char+0x1b4]`) then `ldr r0,[r0,#0x56c]` — the same field the GDB anchor `0x020784E8` reads, so that anchor's `arg0` is `[char+0x1b4]`. The chain is **ov6 character (`0x1F0`) → `+0x1b4` → the `≥0x570` struct → `+0x56c` → the gauge**, which locates an object open since the earliest GDB work. Also: three counters on the view (`+0x10` cap `0x120`, `+0x12` cap `0x1B0`, `+0x14` cap `0x2D0`), and `char+0x7c` gains fields at `+0x4D` and `+0x5B` (both `cmp #3`), so it is ≥ `0x5C` bytes. **Correction:** the table has **11** unique handlers, not the 9 stated at iterations 88–89. See `findings/all-view-handlers-and-the-0x1b4-link.md`.)* **(iteration 92 — the slot-arm function, and an open question.** `0x0215FC20(view, N)` arms a slot: idempotent `tst`/`popne`, sets mask bit `N`, then fills `arr16[N] = entry.u16@0 << 8` and `arr36[N] = entry.u16@2` from a `4`-byte-per-entry table at `[[0x02172984]+0xC]` (a new global, 11 literal loads in ov6). The `<< 8` is a fixed-point scale. **It has no reachable caller** — one raw literal ROM-wide, in a trampoline at `0x0215FB64` that nothing references, and `query.py xrefs-to` missed the literal entirely. **Not claimed** that the table is therefore dead: ov6 has 93 writers of `+0xc`, the search was only companion-filtered, and the strongest hit (`0x0215FC08` in the view reset `0x0215FB88`) *clears* the mask. See `findings/view-slot-arm-and-the-unreachable-setter.md`.)* **(iteration 93 — the `orr` route is eliminated; the question is narrowed, not closed.** The "set bit `N`" read-modify-write of a `+0xc` field occurs **once** in ov6 — the unreachable arm `0x0215FC20` — and arm9's five `orr` RMWs are a 2-bit field and four byte-broadcast idioms, none a `1<<N` set. Whole-word stores were checked too: of ov6's five non-zero-immediate stores to `+0xc`, three are ruled out (`0x0216AFA8` has a global base; `0x80000` is bit 19, outside the 16-slot range; `0x4B000` is multi-bit), leaving `0x021553D8` and `0x021694C8` untraced. **Still unresolvable: 1022 `stm` and 181 register-offset stores.** The table is **not** recorded as dead. See `findings/view-mask-no-reachable-setter-found.md`.)* **(iteration 94 — CLOSED: the 16-slot table is DEAD in retail.** The right move was to enumerate where the view *pointer* can go rather than chase writers of a common offset. `&char+0x130` is taken 29× reaching 12 functions; the only stored copy is `char+0x120 +0x0` and **`ldr rD,[rB,#0x120]` occurs 0 times in ov6**; those plus the handlers and their 2 callees make a closed set of **31** functions. Across all 31 there is **exactly one** store to `+0xc` — `0x0215FC3C`, inside the unreachable arm — while the reachable reset writes `0`. So the mask is always `0`, the gate always returns, and all 12 selectors, 11 handlers, both `int16[16]` arrays and the parameter table are unused. Fourth and largest vestigial system found. Residual: ARM-only, and 18 of ov6's 752 functions are Thumb. See `findings/the-view-handler-table-is-dead.md`.)* **(iteration 95 — the ARM-only blind spot, and the residual closes.** `Battle_CharaCreate` has **zero ARM callers ROM-wide**; it is called from **Thumb** at ov6 `0x0214D65E` (`f009 e9ec` = `blx`, confirmed by `46c0` padding and a literal pool), in code `functions.json` does not catalogue. **Every caller analysis in this campaign has been ARM-only.** The same scan found **no** Thumb caller for the view's arm `0x0215FC20`, closing iteration 94's stated residual. Also: `[char+0x1b4]` is **≥ `0x5F1`** bytes (`strb r6,[r1,#0x5f0]` at `0x02156B0C`), arrives as `[arg1+0x0]` from a stack descriptor, and is neither tagged-allocated nor wholesale-memset. The parameter table `[[0x02172984]+0xC]` is **runtime-only** — `0x02172984` is past ov6's end at `0x02172960`. See `findings/thumb-callers-and-the-0x1b4-struct-floor.md`.)* **(iteration 96 — the blind spot is audited and mostly harmless.** Of the **nine** functions this campaign called "0 callers", only `Battle_CharaCreate` had a hidden Thumb caller; the other **eight stand**, including the view arm `0x0215FC20`, so the dead-table result survives a second check. ROM-wide, **187** of 3691 caller-less ARM functions have an accepted Thumb caller, **16** in battle code. New tool `scripts/decomp/find_thumb_callers.py` rejects impossible edges — a Thumb `bl` cannot target ARM, and ov0–ov9 share `0x0214CD20` so cross-overlay edges are phantoms — which threw out **499 of 686** decoded edges. See `findings/thumb-caller-audit.md`.)* **(iteration 97 — a Thumb disassembler, and the character-creation loop.** `scripts/decomp/thumb_disasm.py` is committed (selftested against the hand-decoded call site). It shows `Battle_CharaCreate` is called **from inside a loop** — `add r0,r5,#0` with `r5` the incrementing index, matching the constructor's `strb r6,[r4,#0x1e0]` entity-index write. `arg1` is a stack descriptor at `sp+0x48` whose first four words come from four distinct sources, two of them `blx #0x02173004` and `blx #0x02173014`; it runs to ≥ `0x20` bytes since the constructor reads `+0x10`/`+0x14`/`+0x1C`/`+0x1D`. `[descriptor+0x00]` is the `≥0x5F1` struct — **still unnamed**, its origin further back in a function whose prologue is below `0x0214D400`. See `findings/thumb-disassembler-and-the-chara-setup-loop.md`.)* **(iteration 98 — ov6's entry point is `Battle_Add`, and a second ARM-only tool.** The Thumb setup function starts at **`0x0214CD20`**, ov6's first byte; its call-site tag reads **`Battle_Add` / `Battle.cpp`**, allocating `0x170` into the global at **`0x02172960`** — exactly ov6's first BSS word, so the module's root object. That allocation is a Thumb `blx`, which `alloc_census.py` cannot see: **238 Thumb allocator calls** exist against 494 ARM, **32%** of the ROM's total. **The battle findings survive** — ov6 has only three Thumb allocations (`0x170` `Battle_Add`, `0x40` `Battle_TutorialCreate`, `0xD4` `Battle_WindowCreate`), all named and none ≥ `0x570`. See `findings/battle-add-and-the-thumb-allocation-gap.md`.)* **(iteration 99 — the census is complete: 732 sites, not 494.** `alloc_census.py` now scans Thumb `blx` too — 494 ARM + 238 Thumb, **640** sized, **670** named. Its back-resolver invalidates `r0`–`r3`/`ip`/`lr` at calls **and treats memory loads as writes**; without the latter a stale `ldr r0,[pc,…]` survived an `ldrh r0,[r4,#0x10]` and reported `0x214BE40` as a size. **The battle findings hold under full coverage:** of the 12 allocations ≥ `0x570`, all are text, comms, WiFi, fonts, input or `Battle_ColJointManCreate` — nothing that could be the `≥0x5F1` struct at `[char+0x1b4]`. Newly visible: `RecordLoad` `0x7560` (`Record.cpp`), the ROM's largest allocation. See `findings/allocation-census-completed-for-thumb.md`.)* **(iteration 100 — `Battle_Add` maps the module's ROOT OBJECT.** 1539 halfwords, 144 calls, 15 named callees. Eleven results land in the `0x170` root at `[0x02172960]`: `+0xD0` DemoKo, `+0xD4` Pause, `+0xD8` PauseWiFi, `+0xF0` Marker, `+0xF4` Battle_ComicDeck, `+0x104` map conveyor, **`+0x108` `Battle_ObjManCreate`**, `+0x10C` ObjCtrlMan, `+0x110` ObjShotMan, `+0x114` ComicDeck, `+0x128` AI — `+0x104`–`+0x114` a contiguous manager block. **`Battle_Add` does NOT build the collision managers** (`0x0207C4C0`, `0x0207BD40`, `0x0207AD3C` are never called), so that layer initialises on another path. See `findings/battle-add-root-object-map.md`.)* **(iteration 101 — CENSUS CORRECTION; iteration 99 was wrong.** The resolver discarded sizes arriving as **pc-relative literals**, which is how every large allocation is written. Fixing it added 19 sites (sized 640→659) and took allocations ≥ `0x570` from **12 to 25**, **seven of them battle objects**: `Battle_ColPrmManCreate` **`0xFB54`**, `Battle_ObjManCreate` `0x42D8`, `Battle_ObjShotManCreate` `0x3FD4`, `Battle_MoveManCreate` `0x2648` (`BattleMove.cpp`, a new module), `Battle_ColManCreate` **`0x219C`**, `BattleMapLoadItem` `0x11E4`, `Battle_ColJointManCreate` `0x1040`. So "no allocation ≥ `0x570` is a battle object" is **REFUTED**, and with it the claim that the `≥0x5F1` struct at `[char+0x1b4]` is not tagged-allocated — **reopened**. Still true: no battle allocation falls between `0x5F1` and `0x1040`. See `findings/census-literal-sizes-and-seven-hidden-managers.md`.)* **(iteration 102 — `[char+0x1b4]` is a PER-PLAYER ARRAY SLOT.** `Battle_Add` builds the descriptor as `[root + 0x118 + index*4]` (`0x0214D5E4`–`0x0214D5F0`), so each character receives the array element matching its own slot. With ComicDeck at `+0x114` and `BattleAI_Create` at `+0x128`, the array holds **four** entries — JUS's four players. The `+0x56c` gauge machinery is **`ComicDeck.cpp`'s**: both arm9 writers (`0x02077FDC`, `0x020786DC`, identical `orr #1`/`orr #0x100`/`str [gauge+0x3c]` idiom) and the GDB reader `0x020784E4` all fall between that module's bracketing allocation tags. So these are PLAUSIBLY per-player decks, which is what the `+0x558`/`+0x56c` deck-wide-SP tension needed. **REFUTED:** `0x1914 = 4 × 0x645` is a coincidence — `0x645` appears nowhere in arm9. See `findings/char-0x1b4-is-a-per-player-array-slot.md`.)* **(iteration 103 — NAMED: `[char+0x1b4]` is one of four `0x61C` PLAYER SLOTS inside the ComicDeck block.** `ComicDeckCreate`'s initialiser (`0x02075FE8`–`0x02076014`) walks from deck`+0x64` to deck`+0x18D4` with stride `#0x21C`+`#0x400` = `0x61C`, exactly **4** iterations; `0x61C` accommodates both `+0x56c` and `+0x5F0`. Slots are handed out by `0x02076908` from the free list at deck`+0x18DC` and published to `root+0x118+index*4`. **`+0x558`–`+0x564` are zeroed PER SLOT**, so the long-noted `char+0x558` is a player-slot field, not a character one. **Corrects iteration 102:** refuting `4 × 0x645` was right, but "not four per-player decks" over-reached — and note `0x61C` also appears nowhere as an immediate or literal, so that constant test cannot settle a stride. See `findings/char-0x1b4-is-a-comicdeck-player-slot.md`.)* **(iteration 104 — 12 slot fields mapped, and where the bulk is.** From twelve anchors: `+0x058` addr; **`+0x558` a list head** walked by `0x0207871C` (nodes carry a byte at `+0x40`; `Battle_Add` calls it once with `r1 = 0` and once with `r1 = 1`); `+0x55C`/`+0x560`/`+0x564` zeroed per slot; `+0x56C` the gauge; `+0x5E8`/`+0x5EC` written in ov6 and read in arm9; a byte cluster at `+0x5F0`/`+0x5F3`/`+0x5F5`/`+0x5F6`. **`+0x000`–`+0x557` — 87% of the slot — is untouched by every construction and gauge anchor**, so the deck payload has its own accessors. Note `+0x21C` is NOT a field: it is the stride's first half, `add r1,r4,#0x21c`. See `findings/player-slot-partial-field-map.md`.)* **(iteration 105 — SP LIVES AT `player_slot+0x5C8`.** `0x020781E4` (SP-apply) is `[slot+0x5C8] += amount`, refused when the amount is negative and the signed byte `[slot+0x5CF]` is non-zero — so the guard blocks loss but never gain. `+0x5C8` has **11** accesses, the most of any slot field, and is reachable from a character as **`[[char+0x1b4]+0x5C8]`** — deck-wide SP, where the per-player-slot reading predicted. Also: an ad-hoc offset scan reporting `0xCC`/`0xCF`/`0xE0`–`0xE3` was **all phantom** — `ldrsb`/`ldrsh`/`strh` carry 8-bit offsets, so anything above `+0xFF` is split (`add #0x500` first) and the real fields are `0x500` higher. **REFUTED:** split bases do *not* explain the unmapped `+0x100`–`+0x557` band; resolving them filled `0x5Cx` instead, and the band is genuinely untouched by `ComicDeck.cpp`. See `findings/player-slot-sp-total-at-0x5c8.md`.)* **(iteration 106 — the unmapped band is a NODE ARRAY.** The slot allocator builds **16 nodes of `0x50` bytes** at slot`+0x58` (`add r6,r5,#0x58`; `mov r7,#0x10`; stride `#0x50`), links every one onto slot`+0x560` via `0x02037B98`, and stamps `node+0x0C = -1`. `0x58 + 16 × 0x50 = 0x558` — exactly where the next known field begins, so the band is fully accounted for. `+0x558` is the **active** list head and `+0x560` the **free** one, both holding the same `0x50` records (the walker's `node+0x40` fits). Nothing indexes the region: after construction the nodes are reached only by list traversal, which is why offset scans found nothing. See `findings/player-slot-node-array-explains-the-band.md`.)* **(iteration 107 — the `0x50` node mapped: 20 fields plus the list pointer.** `+0x000` next; `+0x00C` init `-1`; `+0x00F` bit `0x10` gates a halving; `+0x016` signed source → `+0x018` = `+0x016 / 2` (round toward zero, `add r2,r2,r2,lsr #31`; `asr #1`); `+0x03C` a flags word; `+0x040` non-zero skips a node; a byte cluster `+0x041`–`+0x048` written by the initialiser `0x02076E38`. **Two walkers:** `0x0207871C(slot, mode)` does the gated halving (run twice per slot from `Battle_Add`, mode `0` then `1`), and `0x020785B8` **aborts the entire traversal** when `+0x03C` bit `0x2000` is set. Flags seen: `0x1000` cleared by both, `0x2000` stop, `0x4000` set on the halving path, `0x5000` on the zeroing path. See `findings/the-0x50-deck-node-mapped.md`.)* **(iteration 108 — `0x02076E38` is ADD-ENTRY-TO-DECK.** `(slot, id, a, b, …)` with three high-bit error codes: **`0x20000000`** no free node, **`0x40000000`** duplicate ID, **`0x10000000`** helper `0x02076D30` failed. The duplicate check walks the active list reading `[node+0x34]` and comparing its **first halfword** to the requested id — so `node+0x34` points at the entry's data record and **entries are unique by ID**. On success it unlinks from `+0x560`, links to `+0x558`, memsets `node+0x0C..+0x0F` and `+0x10..+0x31`, then sets `node+0x0C = id` and `node+0x0E = (a & 0xF) | ((b & 0xF) << 4)`. Confirms the list roles from both directions. See `findings/deck-add-entry-contract.md`.)* **(iteration 109 — the two validators, and a correction to this map.** `0x02076C98(_, id)` is a bounds-checked ID→record lookup: rejects `-1`, negative, and `id >= [deck+0x18EC]`, else returns `[deck+0x30] + id*0xC`. `0x02076D30(deck, id, a, b)` bounds **`a < 5`** and **`b < 4`** — exactly the two nibbles packed into `node+0x0E` — then requires the ID to resolve. **`0x0214BD80` is NOT a "chr_b base ptr"**: `str r0,[r3]` at `0x02076038` stores the `0x1914` **ComicDeck block** there, so it is reachable both from that global (97 literal loads) and from `root+0x114`; the same initialiser walks **four** slots from `+0x64`, confirming the count independently. New deck header fields: `+0x30` ID table (`0xC` entries), `+0x38` second table (`0x18` stride), `+0x18EC` count. See `findings/deck-validators-and-the-id-table.md`.)* **(iteration 110 — `node+0x34` is the ID-table entry; the table itself is BLOCKED.** `r5 = 0x02076C98(deck, id)` at `0x02076EB8` is stored to `node+0x34` at `0x02076F3C`, so every deck node points at its own static definition — and that is why the duplicate check works against `[node+0x34]`'s first halfword: **table entries carry their own id**. The table cannot be dumped statically: `deck+0x30` has **no word store** anywhere in `ComicDeck.cpp`, `deck+0x38` comes from a **virtual call** (`blx [[r0]+0x2c]` at `0x020760E0`), and `deck+0x18EC` is never written in the module. Runtime-loaded, same class as `[[0x02172984]+0xC]`. See `findings/node-0x34-and-the-runtime-table-block.md`.)* **(iteration 111 — the deck global's 55 holders are mostly the KOMA EDITOR.** ov5 holds `0x0214BD80` **37** times against arm9 16, ov6 1, ov11 1 — and ov5's allocation tags are `KomaList_Create`, `KomaEdit_Create`, `KomaState_Create`, `Database_PersonalCreate`, `DeckMake.cpp`, `ComicDeckMakeDisp.cpp`. So the deck object is chiefly owned by the editing UI; battle code reaches the global exactly once, at ov6 `0x0215FAC4` (the view-reset caller). **No holder writes `deck+0x30`**, so the table loader receives the deck as an argument rather than fetching the global. Also a **fourth mask bug**: `(x & 0x0F7F0000) == 0x059F0000` clears the `U` bit and can never match — it reported 0 holders. See `findings/deck-global-holders-and-a-fourth-mask-bug.md`.)* **(iteration 112 — shared encoding decoders, and the deck starts zeroed.** `struct_fields.py` now exports tested `is_bl` / `is_ldr_pc` / `is_mov_imm`, each selftested against a real instruction **and a case it must reject** — all four past mask bugs matched *nothing*, so positive-only tests would have passed them. Applied: `ComicDeckCreate` does `memset(deck, 0, 0x1914)` at `0x0207603C`, so `deck+0x30` and `deck+0x18EC` both start at **0**, and no identified writer sets either (0 of 55 holders write `+0x30`; 0 `add`+`str` pairs ROM-wide reach `+0x18EC`). If that holds, add-entry always returns `0x10000000` — **not claimed**, because 96 `+0x30` stores are unattributed and a function receiving the deck as an argument would not load the global. See `findings/shared-encoding-decoders-and-the-zeroed-deck.md`.)* **(iteration 113 — the battle deck's ADD-ENTRY PATH IS DEAD.** Four independent routes to a deck pointer, all empty: the global via ARM (0 of 55 holders write `+0x30`), one call hop (1 of 79, and it is `Battle_ColObjCreate`'s own `+0x30` on a `0x40`-byte struct), **Thumb (0 references to `0x0214BD80` ROM-wide)**, and `root+0x114` (0 of 17 readers). With `memset(deck, 0, 0x1914)` at creation and nothing writing `+0x18EC`, the count stays `0`, so `0x02076C98` rejects every id and add-entry always returns `0x10000000`. The 16-node array, both lists, the unique-by-ID rule and the two walkers are **machinery that never runs**. This is the *battle-side* object only — the ov5 editor has its own (`KomaList_Create`, `KomaEdit_Create`, `KomaState_Create`). Fifth vestigial system. See `findings/deck-add-entry-path-is-dead.md`.)* **(iteration 114 — residual CLOSED.** Across the 72 functions that can hold a deck pointer there are **7** register-offset stores and **2** `stm` — all read individually. The seven are scaled array (`lsl #2`) or byte writes, none with a deck base or a fixed offset; the two are a `ldm`/`stm` 32-byte block copy. So every write form is now swept — immediate, `add`+store split, register-offset, `stm`, and Thumb — and `deck+0x30` / `deck+0x18EC` keep the `0` the constructor's `memset` gives them. See `findings/dead-deck-residual-closed.md`.)* **(iteration 115 — the ACTIVE LIST is never non-empty, so the dead region is much larger.** Enumerating every `link`/`unlink` against both heads gives six sites, all in `ComicDeck.cpp`: `+0x558` has exactly **one linker** (`0x02076EF4`, inside the dead add-entry) and **one unlinker** (`0x020770E4`, the remove function); `+0x560` has four (two 16-node init loops, add-entry's take, remove's return). So no node ever reaches the active list — which kills the **remove function and BOTH walkers**, the `+0x016`→`+0x018` halving, the `+0x03C` flag manipulation and the unique-by-ID rule. Answer to "how is the battle deck populated": **it is not**. Still live: the two init loops, and the fields outside the node system (`+0x56C` gauge, `+0x5C8` SP, the guard bytes). See `findings/the-active-list-is-never-non-empty.md`.)* **(iteration 116 — `KomaList_Create` and a six-entry array.** The editor's container is `0x554` bytes, memset at creation, with a **six-word array at `+0x14`** copied from an optional stack argument (`cmp r3,#6`; null source zeroes it instead). `+0x3F0` is set from an argument and gates two sub-objects at `+0x0C`/`+0x10`; `+0x04C` and `+0x3F0` are the busiest fields at 9 accesses each. `0x02026F94` — its `+0x38` factory — is shared with the NoteTrack, not deck-specific. **New tooling gap:** the array is accessed as `add r0,r4,r3,lsl #2` then `[r0,#0x14]`, a **scaled-register** split that guard 9 does not resolve, which is why `+0x14` is absent from the field map. See `findings/komalist-create-and-the-six-entry-array.md`.)* **(iteration 117 — guard 12 resolves scaled-register arrays.** `add rD, base, rI, lsl #n` then `[rD, #imm]` is an array at `+imm`, element size `1 << n`, extent from the guarding `cmp rI, #N`. KomaList`+0x14` now reports `str/array[6]x0x4`; it was absent before. The adds are **conditional** (`addne`/`addeq` arms of an optional copy), so requiring `AL` finds neither. All four split forms in this ROM are now handled. **Correction:** the `0x50` deck node has **21** fields, not 20 — iteration 107's table dropped `+0x008` because I read the scan through `tail -20` on a 24-line output. `node+0x008` receives a table lookup indexed by `node+0x40`. See `findings/guard-12-scaled-arrays.md`.)* **(iteration 118 — the ColPrm manager's constructor map, 43 fields.** Guard 8 carried the same `AL`-only assumption (relaxed; **no** existing map changed). Running the scanner on the manager at its true size `0xFB54` had never been done and confirms six scattered facts in one place — `+0x08` record free pool, `+0x10` record active list, `+0x18`/`+0x20` node pools, `+0x28` bucket array, `+0xD8` bucket free list, `+0xE0`/`+0xE4`/`+0xE8` sub-objects — plus **seven new offsets**: `+0x054`, `+0x0DC`, `+0x0EC`, `+0x0F0`, `+0x0F4`, `+0x254`, `+0x354`. **The phase table has a gap:** 19 word stores in the 20-slot span `+0xFC`–`+0x148`, with **`+0x130` never written** and no memset covering the manager — which reconciles exactly with iteration 62's independently-derived 19-entry count, so the gap is deliberate. `+0x154` (the contact array) is absent, as expected. See `findings/colprm-manager-constructor-map.md`.)* **(iteration 119 — the `0xFB54` is THREE NODE POOLS, and three "fields" were false.** `+0x054`, `+0x254` and `+0x354` are low halves of split immediates, not fields. They reach pools that tile the manager exactly: **`0x80` × `0x2C` at `+0xC854`** → free list `+0x18`; **80 × `0x10` at `+0xDE54`** → `+0x20`; **`0x200` × `0xC` at `+0xE354`** → bucket free list `+0xD8`. `0xC854+0x1600 = 0xDE54`, `+0x500 = 0xE354`, `+0x1800 = 0xFB54` — the allocation size, no slack. Bucket nodes get `+0x8` zeroed in a separate pass bounded at `0xFB4C`. So the size, the three documented free pools and the node sizes from iterations 69–70 all reconcile. Unexamined: `+0x360`–`+0xC853`. See `findings/colprm-manager-three-node-pools.md`.)* **(iteration 120 — the `0xFB54` is FULLY ACCOUNTED, and the records are EMBEDDED.** New guard 13 follows chained `add` pairs so a split base reports its real offset: the three ColPrm phantoms become `+0x454`/`+0xC854`/`+0xDE54`/`+0xE354`, and the player slot's phantom `+0x21C` becomes `+0x61C`, correctly flagged CONTAMINATED as it equals the struct size. `+0x454` begins **128 ColPrm records of `0x188`** (`add lr,lr,#0x188`, bound `+0xC854`; `0x454 + 128 × 0x188 = 0xC854`) — confirming iteration 77's record size from the manager's own stride. Full layout: header `0x454` + records `0xC400` + `0x1600` + `0x500` + `0x1800` = **`0xFB54`**. The records are **embedded inline**, which is why iteration 109 found a record free pool at `+0x08` with no matching allocation. See `findings/colprm-manager-fully-accounted.md`.)* **(iteration 121 — `record+0x40` bit `0x200` is the FREE FLAG.** The 128 records are linked onto `manager+0x08` by a loop at `0x0207C788` (`add r0,r4,#8`; `bl #0x2037b98`; `cmp r6,#0x80`; `add r5,r5,#0x188`) — answering iteration 120's open question and giving the record count a third time, now read from a `cmp`. The same loop sets bit `0x200` in `record+0x40`, and the full lifecycle confirms its meaning: **set at construction** `0x0207C7A4`, **cleared on install** `0x0207CB2C`, **set again at teardown** `0x0207CE6C` *after* the `memset`. That closes two loose ends from iteration 77 — the installer's unexplained `bic` marks the record in use, and the teardown's post-wipe `orr` re-marks it free. See `findings/record-free-flag-and-the-linking-loop.md`.)* **(iteration 122 — there is NO unexamined span; the layout closes exactly.** Iteration 120 recorded a `0xF4` gap at `+0x360`–`+0x453`; that region is the tail of the **contact array**, mapped at iterations 56 and 62. The accumulators use `mla` by `0xC0` then `0x30`, so 4 elements per row, and `0x154 + 4 × 0xC0 = 0x454` — exactly the record base. Corrected layout: header `0x154` + contact array `0x300` + records `0xC400` + `0x1600` + `0x500` + `0x1800` = **`0xFB54`**, zero unaccounted bytes. The gap was my own error: the contact array is written by the accumulators, not the constructor, so a constructor-only map showed nothing there and I extended the header over it. See `findings/colprm-manager-layout-closed.md`.)* **(iteration 123 — all 19 phase-table handlers recovered, and `+0x0F4` is the COLJOINT MANAGER.** The table's 19 slots hold function pointers from constructor literals, all in `0x0207D9A4`–`0x0207E010`: **17 unique** (`0x0207DE08` at `+0x110`/`+0x120`, `0x0207DFD8` at `+0x140`/`+0x144`), of which `+0x0FC` and `+0x100` are single-instruction **`bx lr` no-ops** — so **15 real handlers**, and none carries an assert-string name. `+0x0F4` = `Battle_ColJointManCreate`'s result, called with `[manager+0xE0]`, so the ColPrm manager owns the ColJoint manager (also reachable via its own global `0x0214BE0C`). Also: the `0x10`-node pool's 80 count, only *derived* at iteration 119, is now **read** from `cmp r6,#0x50`. See `findings/colprm-phase-table-handlers.md`.)* **(iteration 124 — CORRECTION: those are not 15 handlers.** Seven of the 17 targets are **interior entry points inside `0x0207DD40`** (540 bytes, so `+540 = 0x0207DF5C` covers them all), one is inside `0x0207DFF4`, and three sit in an uncatalogued gap `0x0207DF5C`–`0x0207DFD7`. Several are one- or two-instruction routines: `0x0207DE44` is `mov r0,#0; bx lr`, `0x0207DE08` a predicate returning `3`, and `0x0207DF60` opens a 7-case jump table. **Only two targets are substantial** — `0x0207D9AC` (916 bytes) and `0x0207DD40` (540). So the table exposes 17 entry points across roughly **six** code bodies: an interface of mostly-trivial accessors, not a pipeline. Root cause: I counted unique addresses without resolving them against `functions.json`, and read the size-0 entries as missing data rather than mid-function labels. See `findings/phase-table-is-mostly-tiny-accessors.md`.)* **(iteration 125 — `0x0207DD40` read in full: it is **eight functions**, not one.** One list walker `0x0207DD40`–`0x0207DDD0` (`pop {r4,r5,r6,pc}`) plus seven leaf routines each ending in its own `bx lr`; `+540` lands exactly on a literal pool at `0x0207DF5C` (one word, `0x000003FF`). The leaves are **arena-boundary code** and pin three constants: **`0x4000`**, **`0x3C000`**, **`0x20000`** — in **24.8 fixed point** (`add r0, r2, r0, lsl #8` at `0x0207DD70`), i.e. left bound 64, right bound 960, vertical extent 512. The walker tests each element of the `arg0+0xB0` list (node`+0x8` = object A with centre `A+0x2C` and half-extent `A+0x30`; node`+0xC` = object B) and sets `B+0x78 |= 0x1000000` past the left bound, `|= 0x2000000` past the right — the two arms using **opposite** conditions (`ne`/`eq`) on the same `0x0206CF28` result. `0x0207DE88` is a 4-case rect getter whose `+0x8`/`+0xC` are a **signed extent** (case 2 stores `mvn r0,#0x3bc00` = `-(0x3C000-0x3FF)`), emitting the left and right wall regions. `0x0207DF60` is a **real function `functions.json` missed** (7-case jump table, cases 2–5 sharing `0x0207DF9C`), also loaded at `0x0207C734`. See `findings/arena-bounds-and-the-merged-function.md`.)* **(iteration 126 — `0x0207DF60`–`0x0207E018` read; corrects iteration 125.** The dispatcher `cmp r2,#6; addls pc,pc,r2,lsl #2` resolves against **`pc+8`** = `0x0207DF6C`, so the branch at `0x0207DF68` is the out-of-range **default** (`0x0207DFB8`, return `0`) and every case index shifts by one: `r2`=`0` -> `0x0207DF88` (`1` if `r1` in {`1`,`2`}), cases `1`,`2`,`3`,`4`,`6` -> `0x0207DF9C` (return `0`), case `5` -> `0x0207DFA4` (the exact complement). Iteration 125's "cases 2,3,4,5 share one target" is REFUTED. The `r1` in {`1`,`2`} test matches the rect getter's wall cases `1` and `2`, so `r1` is a region code and these two arms ask *is this a wall region* (PLAUSIBLE). Six more functions here: `0x0207DF60`, `0x0207DFC0` (`mov r0,#4`), `0x0207DFC8` (`1` if `r1`==`0`) are **absent from functions.json**; `0x0207DFD8` is listed at `size=28` exactly right; `0x0207DFF4` `size=36` **covers two** functions (`0x0207DFF4` and `0x0207E010`). Detection here is inconsistent, not uniformly blind. **Interface currency: a `0x10`-byte four-word struct** — `0x0207DFD8` zeroes it at `r3`, `0x0207DFF4` at `r2`, and the rect getter fills four words at `r2`; the out pointer is **not** at a fixed argument position. See `findings/phase-interface-passes-a-0x10-struct.md`.)* **(iteration 127 — `0x0206CF28` resolved, closing iteration 125's open asymmetry.** It is a four-instruction pure getter, `size=16`, `callees=0`, **21 references from 7 caller functions**: `ldr r0,[r0,#4]` -> P, `ldr r0,[r0,#0x64]` -> Q, `ldrb r0,[r0,#0x48]`, `bx lr` — i.e. `*(u8*)(*(*(arg0+4)+0x64)+0x48)`. The `ne`/`eq` split is **design, not a bug**: the identical mirrored pair recurs at `0x0207F410`/`0x0207F448` (`beq`/`bne`), and all 21 sites compare the result to `0`, pass it on, or compare two of them — **never** against `1` or `2`. In the walker the byte **selects which wall is flagged**: non-zero -> `0x1000000`, zero -> `0x2000000`. `[caller+0x30]` is the standard argument route (`0x0207DD80`, `0x0207F40C`, `0x0207F444`). `Q` carries a **vtable at its head with a `(Q, boolean)` method at slot `+0x5C`** (`0x0207E7D0`–`0x0207E7D8`, duplicated at `0x0208167C`). NOT claimed: that the field holds only `0` or `1` — `+0x48` is a conventional offset with 644 hits and no writer attributed. See `findings/0206cf28-is-a-boolean-getter.md`.)* **(iteration 128 — `0x0206CEAC` read whole (124 bytes).** It is an **apply-if-changed** callback (0 callers; one literal load at `0x0206CC2C`, registered through `0x02028384`): read the desired flag via `0x0206CF28` off `[[S+4]+0x44]` (through the lazy-init accessor `0x02011B38`), read the current flag off `S` (which resolves to `Q+0x48` itself), `cmp r4,r0` / `popeq` if unchanged — otherwise **`Q->vtable[+0x5C](Q, desired)`**, which fixes **`+0x5C` as the SETTER** for `Q+0x48` (iteration 127 could only say it took a boolean). It then **negates a coordinate in place**: `0x02024D44` reads `X = [[P+0x50]+0x0C]` and `0x0206CF1C` stores `-X` back, then `0x02024C3C([P+0x50], 1)` notifies. Because the response to a flag change is a **geometric mirror**, the `+0x48` byte reads as a **facing / horizontal-flip bit (PLAUSIBLE)**, and iteration 127's "side/team" guess is weakened — a team change would not negate a coordinate. Recorded, not smoothed: when `[P+0x44]==0` the ternary yields `NULL` and `0x0206CF28` is **called anyway**, reading address `0x00000004`. See `findings/facing-flag-change-negates-a-coordinate.md`.)* **(iteration 129 — `0x02024C3C` read; the coordinate is one axis of three.** It is a **dirty-flag OR-setter** on the byte `+0x24`: `new = cur | bits`, and `obj->vtable[+0x18](obj)` fires **only on a clear->set transition** (`cmp r2,r1`; `beq #0x2024c64`), then `+0x24 |= bits | 0x30` unconditionally — so `0x10` and `0x20` can be set **silently**, outside the notify scheme. The byte is **re-read** at `0x02024C64` rather than reusing `r2`, so the `+0x18` handler may modify `+0x24` itself. **Bit `0x01` marks a three-word vector at `+0x0C`/`+0x10`/`+0x14`** — two independent sites pass `1` right after writing it, and `0x02024BE4` treats the three as one `0xC`-byte unit (`mov r2,#0xc`; `bl #0x2051890`) resetting it to zero. This **strengthens iteration 128**: the negation touched `+0x0C` alone, leaving `+0x10`/`+0x14` — a **single-axis mirror**, not a scalar negation, so the facing reading is tighter (still PLAUSIBLE). Verified in passing: `0x02051890` is `memcpy(dst=r0, src=r1, n=r2)` (`0x020518A0`–`0x020518B4`). Recorded: `0x02024C78` is an orphan `bx lr` **inside** the 64-byte record, past the `pop` — merged-record hazard at one-instruction scale; whether anything reaches it is **not claimed**, since vtable contents are not indexed. See `findings/dirty-flag-byte-and-the-three-word-vector.md`.)* **(iteration 130 — a STRUCTURAL fact about arm9: the library/game boundary is `0x0206ADB8`.** The census has **62** tagged allocation sites in arm9; the lowest is `0x0206ADB8` (`CommonPaletteAnime_Create`, `CommonPaletteAnime.cpp`), and `0x02000000`–`0x0206ADB7` holds **zero**. Since the allocator tags every call site with a `File.cpp`, that region is **middleware/SDK** and **can never be named from allocation tags** — which is exactly why `0x02051890` (memcpy), `0x020517FC` (memset), `0x02037B98`/`0x02037C24` (list link/unlink), `0x02024C3C`, `0x02024BE4` and `0x02011B38` are all nameless. **`CommonEffect`'s class is `0x84` bytes** (`0x0206C590` `CreateImpFunc` and `0x0206CFD8` `CloneMain`, both `0x84`, both `CommonEffect.h` — call-site binding, not proximity), and the iteration 125–129 facing chain (`0x0206CA8C`, `0x0206CEAC`, `0x0206CF28`) is **bracketed between those two sites** => PLAUSIBLE that it is CommonEffect code. Consistency check: iteration 125's walker `0x0207DD40` sits above `0x0207C4E0` (`Battle_ColPrmManCreate`, `BattleColPrm.cpp`), matching where the docs already put the phase table. `AL*` (`ALPropSetImp.h`, `ALStreamImp.h`, `ALTextDS.cpp`) is a middleware namespace (PLAUSIBLE). The queued bits task **FAILED**: `+0x24` has 1838 ROM-wide hits, 64 in the library region, and only 3 near the setter (all inside it). Lead only, not claimed: `lsl #0x19; lsrs #0x1f` at `0x020219F4` and `0x02021C4C` isolates **bit 6 = `0x40`** of *a* `+0x24` byte; neither base is traced. See `findings/the-library-game-boundary-at-0x0206ADB8.md`.)* **(iteration 131 — CORRECTION to the allocator signature, affecting all 732 sites: `r3` is `__LINE__`, not a tag.** Decisive test: `CommonHSV_Create` has five sites whose `r3` runs `0x2d`/`0x42`/`0x43`/`0x48`/`0x49` = **45, 66, 67, 72, 73** — strictly increasing with **two adjacent pairs** (66/67, 72/73), which no tag or arena scheme produces. Six more sites across four files agree, all small and distinct (`CommonPaletteAnime_Create` 106, `ALPropSetImp.h` `Create` 273, `CommonEffect_Init` 103, `CreateImpFunc` 149, `CloneMain` 162, `CommonHSV_Create` 45); the two `CommonEffect.h` lines 149/162 match address order. `alloc_census.py`'s docstring corrected. `0x0206C3CC` builds line 273 as `add r3, r0, #0xf1` (`0x111` is not an ARM immediate), so it correctly reports COMPUTED. **The `0x84` CommonEffect object is a 3-deep C++ class:** `CloneMain` `0x0206CFC0` -> parent copy `0x02015DD4` -> grandparent copy `0x020240A4`, each calling its base, overwriting **`+0x00` with its own vtable**, then copying its own members: parent a **byte at `+0x78`** (vtable `0x0209C30C`), derived a **halfword at `+0x80`** (vtable `0x0209E114`, the final value). The parent copy also increments a counter at `0x020A0C34+0x4C` = **`0x020A0C80`**. Both allocators check for NULL (`popeq` `0x0206C598`, `beq` `0x0206CFE0`). `CreateImpFunc` passes `0x02024A30` (library region) to constructor `0x0206CA4C`. See `findings/allocator-arg3-is-line-number.md`.)* **(iteration 132 — both vtables dumped and diffed; slot `+0x18` is `Clone`.** 44 slots each, all plausible arm9 code pointers. **Exactly 3 of 44 differ**: `+0x00` (`0x02015E54` -> `0x0206D010`, 20B), `+0x04` (`0x02015E88` -> `0x0206CFA4`, 28B), and `+0x18` (`0x0204B0C8` -> **`0x0206CFC0` = `CloneMain`**), which **names slot `+0x18` as the virtual clone** with no disassembly of the body — diff a derived vtable against its parent, then look the differing entries up in the census. Two inherited slots are **Thumb**: `+0x08` = `0x020102D1`, `+0x10` = `0x020119E5` (odd addresses). The hierarchy is **four** deep, not three: `0x02021960` (496B) -> `0x020240A4` (528B) -> `0x02015DD4` (56B) -> `0x0206CFC0`; `0x020240A4` also builds a subobject at **`+0x6C`** (`0x0201CF08`, then `0x02010970` with `mov r1,#4`). Iteration 130's bit-`0x40` lead **connects**: `0x020219F4` lies inside `0x02021960`, this family's base copy ctor, so that `+0x24` byte is a **base-class** field (still not proven identical to iteration 129's dirty byte). `0x02021BB8` is another 496-byte twin, likely `operator=` (PLAUSIBLE). **CONFLICT recorded:** iteration 129 labelled vtable `+0x18` a *notify*; here `+0x18` is `Clone`. That label was inferred from call position, never read — unresolved, and flagged in iteration 129's doc. See `findings/vtable-diff-names-slot-0x18-as-clone.md`.)* **(iteration 133 — all three overridden slots named, and the allocator itself was mis-identified.** `+0x18` = **`Clone`** at both levels: the parent `0x0204B0C8` allocates `0x80`, copy-constructs via `0x02015E14`, returns the new object; `CloneMain` allocates `0x84` — and `0x80` + the derived halfword at `+0x80` rounds to `0x84`, so two independently-read sizes corroborate the layout. `+0x00` = **destructor** (`0x0206D010`: base dtor `0x02015ED8`, return `this`); `+0x04` = **deleting destructor** (`0x0206CFA4`: same base dtor, then `0x0201B244` = `operator delete`, return `this`). **`0x0201A21C` is NOT the allocator** — it is a 12-byte linker veneer (`ldr ip,[pc]; bx ip; .word 0x0201A228`). The real allocator is **`0x0201A228`** (72 bytes, size split at `0x100`, manager from `[global+0x1A4]`), and it **discards the tag arguments**: `r1`/`r2` are clobbered at `0x0201A22C`/`0x0201A230` and `r3` is never read. So `__FILE__`/`__FUNCTION__`/`__LINE__` are built at every call site and thrown away — a debug macro left in a retail build. The census is **unaffected** (its evidence is the call site), but it scans only the veneer, so tagged calls reaching `0x0201A228` directly would be invisible — scan both. Six sampled direct callers of `0x0201A228` pass **size only** and all sit below `0x0206ADB8`, which reframes iteration 130's boundary as a **compilation** boundary: two entry points, one allocator. Iteration 129's "notify" label for `+0x18` is **dropped** — wrong under either reading. See `findings/0x0201A21C-is-a-veneer-and-the-tags-are-dead.md`.)* **(iteration 134 — the census now scans BOTH allocator entries: 732 -> 1135 sites.** `ALLOC_ENTRIES = {0x0201A21C: veneer, 0x0201A228: direct}`, and every row records which entry it used. Iteration 133's open question is **answered NO**: of the 403 newly-visible direct sites, **zero** resolve to a real `.cpp`/`.h`, while **572 of 732** veneer sites do. So tagged code always goes through the veneer and untagged library code always goes direct — two entry points, one allocator, no overlap, and iteration 130's compilation boundary is clean in both directions. Direct rows are reported **`UNTAGGED`**: their apparent names were **stale registers** (`<0x020a0c34>` in the *file* column is iteration 131's instance counter), with a selftest that fires if a direct site ever does resolve to a real filename. **Bug found and fixed:** the ARM pass had **no plausibility bound** on sizes — only Thumb did (since iteration 101) — so site `0x020462EC` reported `0x2096568` (34 MB) on a 4 MB console. Bounded at `0x100000` for both passes (largest genuine allocation is `0x4000C`), and the selftest assertion widened from Thumb-only to all rows. Regression-verified: **659 old rows vs 659 new veneer rows, diff empty** — purely additive. See `findings/census-covers-both-allocator-entries.md`.)* **(iteration 135 — NEGATIVE RESULT: the direct entry allocates only small objects.** Swept all 403 direct sites (320 with a resolved size): the **largest is `0xE4`**, against `0x4000C`/`0xFB54`/`0x42D8`/`0x3FD4`/`0x2648` on the tagged path. So iteration 134 extended the census's **coverage, not its reach** — no large structure was ever hidden. Size distribution is tiny-object dominated (`0x14`x46, `0x8`x42, `0x24`x34, `0x40`x19, `0x78`x17), exactly a middleware layer allocating nodes and handles. Self-check the sweep passed: it independently rediscovered **`0x0204B0D4`**, the allocation inside iteration 133's parent `Clone` `0x0204B0C8`, which was originally found via a vtable diff. **Seven direct sites allocate exactly `0x80`** (the parent CommonEffect size): `0x02034C38`, `0x02034C5C`, `0x02041DE0`, `0x02044334`, `0x02046270`, `0x02049C94`, `0x0204B0D4` — all sharing one shape (constant size, NULL-check, call one function with the new object, return it) and reaching **six distinct constructors**: `0x0202B4A8`, `0x02015D70`, `0x0203ABD4`, `0x020445F4` (x2), `0x0202B520`, `0x02015E14`. Whether that is one class with overloads or sibling classes of equal size is **not claimed**. Reusable: that allocate-then-construct shape identifies a **constructor** (and the constant is its class size; if `arg1` is a same-type object, a **clone**) straight from the census, with no disassembly of the callee. See `findings/direct-entry-allocates-only-small-objects.md`.)* **(iteration 136 — back on Mission 2: `Battle_MoveManCreate` read.** The function is **`0x02082A38`** (408 bytes, 1 caller `0x02083204`, `bl` at `0x020833D0`), NOT `0x02082A50` — that is the allocation site inside it, the address a dozen earlier docs used. `BattleMove.cpp` line 50. **It owns two NoteTracks**, at `+0x20` (id `0xA1000`, callback `0x02082E10`) and `+0x24` (id `0xA6000`, callback `0x0208317C`), each built by the same six steps: `0x02026F94` factory -> store handle -> `0x02012940(track, &id)` -> `0x02028384(.., callback)` -> `vtable[+0x24](track, manager)` self-register -> `vtable[+0x94](track, 0x2000000)`. **This independently reproduces iteration 54's ColPrm `+0xE4`/`+0xE8` pattern** (ids `0xA5000`/`0xA0000`, same factory, same vtable-`0x24` self-registration), reached from a completely different direction. The `0x1000`-aligned id set is now `0xA0000`, `0xA1000`, `0xA5000`, `0xA6000`. **Half the constructor is DEAD:** eight word clears at `+0x00`–`+0x1C` and a 128 x `0xC` strided loop over `+0x48`–`+0x647` (zeroing `+0x8` of each) are both followed by `memset(obj, 0, 0x2648)` — verified: the literal at `0x02082BD4` is `0x2648` (the same word the size argument loads), no branch skips it, `r2` is not rewritten. A sixth vestigial finding, and the first that is redundant work rather than an unused feature. The dead loop still documents the intended layout: **128 records of `0xC` bytes at `+0x48`** — the same record count as the ColPrm manager. `+0x2C` = halfword `0x29`. `+0x648`–`+0x2647` (`0x2000` bytes) unexplored. Also: `beq #0x2082aa0` on allocation failure targets the `memset` setup with `r4 = 0`, so OOM writes 9,800 zero bytes to address `0` — the **second** instance of this shape after iteration 128. See `findings/movman-owns-two-notetracks-and-dead-init.md`.)* **(iteration 137 — the MoveMan region resolved as TWO PARALLEL 128-ELEMENT ARRAYS, and its callback read.** Offset scanning found **nothing**: `search-op-imm 0x648` 0 hits, `search-imm 0x648` 0 hits, `find_field_writers.py 0x648` 0 direct + 0 split. `0x648` is **not an encodable ARM immediate**, and the constructor built it only as a **loop bound** (`add #0x248` then `add #0x400`), never dereferencing it — so there is no `+0x648` field. The region is reached **by pointer** through the list payload, the fourth blind spot `find_field_writers.py` prints. Consumer `0x02082E10` (868 bytes, `callers=0`, installed via `0x02028384`) **walks a linked list**: `ip = [[[arg0+4]+0x10]+0x10]`, `ldr lr,[ip,#8]` for the element, `ldr ip,[ip]` / `cmp ip,#0` / `bne` to advance — `next` at `+0x00`, payload at `+0x08`, this codebase's list-library shape. So: **`+0x48`–`+0x647` = 128 x `0xC` links** (CONFIRMED: base, stride and bound all read from iteration 136's loop; `0xC` = next/prev/payload, and that loop zeroed `+0x8` of all 128 — the payload the consumer reads) and **`+0x648`–`+0x2647` = 128 x `0x40` elements** (PLAUSIBLE: tiles exactly with zero slack and elements need >= `0x38` since `+0x34` is touched, but **no code computes `base + i*0x40`** — the stride is inferred, never observed; the `0x645` false lead is the reason this is not CONFIRMED). **The callback is a frame snapshot:** every pass it ANDs `+0x34` with `0x0003FFFF`, then if bit `0x100` is set clears it, else copies `+0x0C`->`+0x14` and `+0x10`->`+0x18` — a **previous-value pair** for per-frame deltas, with `0x100` suppressing one snapshot. If `+0x34 & 0x600` it sets `0x20` and skips the rest; `[lr+0x26]` (signed halfword) `> 0` sets `0x4`. Element fields: `+0x0C`/`+0x10` current, `+0x14`/`+0x18` previous, `+0x26` signed halfword, `+0x34` flags (bits `0x4`, `0x10`, `0x20`, `0x100`, `0x600`, `0x1000`; masks `0x0003FFFF` and `0xFFFFEFCB` = `~0x1034`). See `findings/movman-two-parallel-arrays-and-the-frame-snapshot.md`.)* **(iteration 138 — the element ALLOCATOR found, plus a field at `+0x3E`; the `0x100` hunt FAILED.** `+0x34` has **1092** ROM-wide hits, so `find_field_writers.py` with companions `0x0C`/`0x14`/`0x18`/`0x26` was the only way in: three writes in one function, all companions present, and that function sits just past `Battle_MoveManCreate`'s literal pool — **`0x02082C34`**, 248 bytes, 1 caller. It is the **element allocator**: free list at `container+0x08`, active list at `container+0x00`, `unlink` then `link` via `0x02037C24`/`0x02037B98`, `moveq r0,#0` / `popeq` on exhaustion — the same graceful recycler shape as the ColPrm `+0x18` pool. `+0x08` = arg1. It performs iteration 137's **same snapshot** (`+0x14`<-`+0x0C`, `+0x18`<-`+0x10`) on **all three branches**, which confirms it and the consumer share an object type. `+0x0C`/`+0x10` come from `[arg2]`/`[arg2+4]`, or default to **`0x10000`** when arg2 is NULL (= `1.0` in 16.16, so a scale/rate pair — PLAUSIBLE, format inferred). **Key: `strb` to `+0x3C` (`0x20`), `+0x3D` (`8`) and `+0x3E` (`0x20`)** — the element demonstrably reaches `+0x3E`, so it needs >= `0x3F`. `0x40` is the smallest aligned size that fits AND the only stride tiling `+0x648`–`+0x2647` into 128, which narrows iteration 137's hypothesis a long way; still PLAUSIBLE only, because nothing computes `base + i*0x40`. New `+0x34` bits: `0x1` (always), `0x200` (if `[container+0x28] & 1`), `0x8` (before returning). **Bit `0x100` is NOT set here** — the task target is unmet; and since the allocator snapshots on every branch, `0x100` more likely belongs to **repositioning** than creation (SPECULATIVE). **Cross-module link:** the sole caller is the ColObj installer `0x0207C988` at `0x0207CA08`, passing `arg0 = [installer_arg0 + 0xF0]` — so `BattleCol.cpp` allocates a `BattleMove.cpp` element. NOT claimed that this is `ColPrmMan+0xF0`: same offset, identity never established. See `findings/movman-element-allocator-and-the-0x3E-field.md`.)* **(iteration 139 — the element's `+0x08`/`+0x0C`/`+0x10` named, and iteration 138's "scale pair" REFUTED.** The installer's setup before `0x0207CA08` resolves the call fully: `arg1 = r8` (the **owner**), and `arg2 = &sp[0]` where `sp[0] = [ip+0xC] asr 4` and `sp[4] = [ip+0x10] asr 4` for `ip = [[owner+4]+0x50]`. So **`element+0x08` = the owner object, `+0x0C`/`+0x10` = the owner's transform x/y shifted right 4 (signed)** — and with iteration 137's `+0x14`/`+0x18` holding their previous values, the element carries **a position and its previous position**, which is exactly what the frame-snapshot pass maintains. `[[owner+4]+0x50]` is a **third independent sighting** of iteration 128/129's transform node, and the first to read all three of `+0x0C`/`+0x10`/`+0x14` together. **REFUTED (my own, iteration 138):** `0x10000` is not `1.0`-in-16.16 marking a scale pair — these are position components, so it is a default **position**. The error was reasoning from a recognisable constant instead of waiting for the data's source. Also REFUTED, my own prediction: this did **not** settle iteration 137's `ip`/`lr` ambiguity — and the consumer's list `[[[arg0+4]+0x10]+0x10]` is **not** the `container+0x00` list this allocator links onto, so the two may walk different structures. Recorded unresolved: `0x0201899C` is called with `r0 = sp+8` and its three words are then overwritten at `0x0207C9E0`/`0x0207C9EC`/`0x0207C9F8`; the raw unshifted x/y/z are never passed to `0x02082C34`. See `findings/element-0x0C-is-the-owners-world-position.md`.)* **(iteration 140 — the installer's three-word buffer is ENTIRELY DEAD, and four record fields get names.** Scanning all 111 instructions of `0x0207C988`: `sp+8`/`sp+0xC`/`sp+0x10` are **written at three sites and read nowhere**. So `0x0201899C(sp+8, ..)` has its work overwritten three instructions later, its return value is clobbered at `0x0207C9AC`, and the raw x/y/z are never used — the **seventh vestigial finding**, and the first where a *function call*'s only output is discarded. Iteration 139's guess that "a later call consumes them" is **REFUTED**. Only `sp+0`/`sp+4` (the `asr 4` pair) reach anything. **`record+0x5C` = the BattleMove element** (`str r0,[r4,#0x5c]` right after `bl #0x2082c34`) — directly below `+0x60`, the ColObj: two subsystem handles side by side. **`[sb+0xEC]` = the ColObj factory's container** (into `0x0207AEDC`) and **`[sb+0xF0]` = the element container** (into `0x02082C34`), resolving a long-carried queue item (still on `sb` = the installer's `arg0`, NOT proven to be ColPrmMan). **`record+0x34` = the installer's `arg2`, `record+0x38` = `arg3`** — iteration 72 saw the pool allocator read these but not where they came from. **`record+0x3C`** = `arg5` (`[sp+0x30]`) `| 0x20C000`, plus `0x30000` if `arg2 & 0x00FCFFFF`, plus `((arg2 & 0xF) << 4) | 0x400000` if the low nibble is set — so `arg2` does double duty, stored whole at `+0x34` and re-encoded into `+0x3C` bits 4–7. The installer takes **at least six arguments** (`r0`–`r3`, `[sp+0x30]`, `[sp+0x34]`). `record+0x184`/`+0x186` initialise to `0x100` via the split form `add #0x100` then `+0x84`/`+0x86` (`0x186` is not an encodable ARM immediate — the same reason `+0x648` was invisible in iteration 137). The tail packs 2-bit fields from `[sp+0x34]` into `record+0x175` and stores it **twice** (`0x0207CAF4` then `0x0207CAF8`), so the first store is dead too. See `findings/installer-dead-buffer-and-record-fields-from-the-caller.md`.)* **(iteration 141 — `record+0x38` is a single-bit CATEGORY MASK, traced to four real call sites.** Chain: ov6 caller -> `0x020834D4` (pooled-entity constructor) -> `0x0207C988` (installer) -> record. The constructor passes `arg2`/`arg3` through **untouched** (`mov r7,r2` / `mov r6,r3`, then `mov r2,r7` / `mov r3,r6` at the `bl`). The argument numbering was **verified by frame arithmetic twice**: the installer pushes 7 regs (`0x1C`) + `sub #0x14`, so a caller's `[sp+0]` lands at its `[sp+0x30]`; the constructor pushes 6 (`0x18`) + `sub #8`, landing at `[sp+0x20]` — both exactly where each function reads. Four sites: `0x02164F0C` (ov6) `arg2=0x100`, `arg3=`**`0x8000`**; `0x02164F48` (ov6) `0x100`, **`0x4000`**; `0x02168E44` (ov6) `r3 & ~0xF`, **`0x800`**; `0x0208363C` (arm9) pass-through, **`0`**. `arg3` is zero or exactly one bit every time -> **a category/layer mask** in `record+0x38`, which iteration 70 showed the pool allocator copying to `node+0x18` (PLAUSIBLE: 4 points, no consumer read yet). **`arg2`'s low nibble is zero at every visible site** — two pass `0x100` and the third does `bic r2,r3,#0xf` — so the installer's `0x0207CA58`–`0x0207CA68` branch (`ands #0xf`; `lslne #4`; `orrne #0x400000`) has **no observed live caller**; NOT claimed dead, because `0x0208363C`'s `r2` is untraced. Since `0x100 & 0x00FCFFFF` != 0, those two sites give `record+0x3C = arg5 | 0x20C000 | 0x30000`. **`0x02083624` is a thin wrapper** that forces `arg3 = 0` and shifts the rest down — so the subsystem has two entry points, one supplying no category. `arg6` is **0 at all three ov6 sites**, so `record+0x175`'s packed 2-bit fields are all zero in practice (PLAUSIBLE), explaining why the installer's tail bit-shuffling yields nothing. See `findings/record-0x38-is-a-category-bitmask.md`.)* **(iteration 142 — `+0x38` CONFIRMED as a bitmask, and the bit picks an AXIS.** Four consumer sites inside `0x02081DDC` (992 bytes, 1 caller) all do `ldr ip,[r7,#0xc]` -> `ldr ip,[ip,#0x38]` -> **`tst`** against `0x4000` or `0x8000` — never a numeric compare. Those are exactly the bits real callers write (`0x8000` at `0x02164F0C`, `0x4000` at `0x02164F48`, iteration 141), so writer values and reader tests agree from opposite ends of the chain: **PLAUSIBLE -> CONFIRMED_STATIC**. The bit selects **which accumulator moves**: `0x4000` -> `r3`, `0x8000` -> `sb`. The gating flags come in **sign pairs**: `0x200`/`0x20000` for `r3`, `0x100`/`0x10000` for `sb` — flags choose direction, the category bit chooses the axis. The values are a pair of **signed bytes** at `[[r7+0x10]+4]`/`+5`, scaled by `lsl #8` (**24.8 fixed point**, the same format iteration 125 proved for the arena bounds — second sighting), and the adjustment is `lsl #7` = exactly **half** the base, so it adds or subtracts **50%** when both gates pass. NOT claimed: `sl+0x48` looks like MoveMan's link array (`ldr r5,[sl,#0x48]`, then `[r5]` and `[r5+8]`) but `+0x48` is conventional and `sl` is untraced. REFUTED: `fp` is `[[r6+0xC]+0x44]`, **not** the record's `+0x40` flags — adjacent offset, different base, only the bit *values* overlap; recorded so they are never merged. Still open: no consumer tests `0x800`, the third observed category bit. See `findings/category-mask-confirmed-selects-an-axis.md`.)* **(iteration 143 — category bit `0x800` found, and it is NOT an axis bit.** Of 13 `tst #0x800` sites in arm9, exactly three are immediately preceded by a `+0x38` load — that filter is what made it tractable, since most `tst #0x800` in this module test the record's `+0x40` flags instead. The three: `0x0207F7A0` (in `0x0207F480`, 1736 bytes, **0 callers**) and `0x0207FFD4`/`0x0207FFE4` (in `0x0207FBD0`, 1572 bytes, 1 caller). **At `0x0207FFCC`–`0x0207FFE8` it is tested on BOTH members of a pair** — `[[r5+0xC]+0x38]` and `[[r6+0xC]+0x38]`, the same `+0xC` indirection as iteration 142 — and either one set branches to the shared target `0x020801D4`; only if both are clear does it reach `[r8+0xD8]`, the bucket free list from iterations 68–69. A **pairwise veto**. **At `0x0207F7A0` the polarity is opposite:** after `tst r1,r0` / `bne`, a *set* `0x800` lets the operation through (`beq` skips when clear) — an **OR-bypass**. Recorded as observed, **not reconciled**: the two are different operations, and iteration 127 is the precedent for not labelling an asymmetry before reading enough. So **`+0x38` mixes two kinds of bit** — `0x4000`/`0x8000` are axis selectors, `0x800` is behavioural control — which means a new bit should not be assumed to be another axis. NOT claimed: `0x0207F794`'s `tst r1, r0` is a mask-against-mask test in shape (and would explain the field in one stroke) but neither operand is traced. See `findings/bit-0x800-is-a-pairwise-filter-not-an-axis.md`.)* **(iteration 144 — the test is `record+0x34 & 0x6FF`, a CONSTANT; iteration 143's top lead REFUTED.** Two instructions settle it: `0x0207F78C ldr r1,[r4,#0x34]` and `0x0207F790 ldr r0,[pc,#0x3b4]` -> the literal at `0x0207FB4C` = **`0x000006FF`**. So it is **not** a mask-against-mask layer test; `record+0x34` is checked against a fixed constant, with `record+0x38` bit `0x800` as an OR-bypass past that one check. **`0x6FF` = bits 0–7 plus bit 9 (`0x200`) and bit 10 (`0x400`) — bit 8 (`0x100`) is CLEAR** — and `0x100` is exactly what the two ov6 callers pass as `arg2` (iteration 141), stored whole into `record+0x34`. So at construction those two **fail** the mask test, and with `arg3` = `0x8000`/`0x4000` their `0x800` bypass fails too. NOT claimed that they are excluded at runtime: `record+0x34` has a **second writer** at `0x0207EF1C` (in `0x0207E864`), so its value at test time is not statically determined. Also: the loop above takes a node from the bucket free list `+0xD8` and links it to `+0xB0` with `node+0x8` = the element. I drafted `+0xB0` as an unaccounted manager field and **checked before publishing** — the list-head audit already records `+0x0B0` as **bucket 17** (heads at `+0x28 + N*8`; `0x28 + 17*8 = 0xB0`). That sharpens it: the `add r0, r6, #0xb0` is a **constant**, so this path always deposits into bucket 17. See `findings/the-mask-constant-is-0x6FF-and-excludes-0x100.md`.)* **(iteration 145 — the SNAPSHOT SUPPRESSOR found, and iteration 144's "second writer" RETRACTED.** `0x0207EF1C`'s base is `[r4+0x5C]`, and `record+0x5C` is the BattleMove element (iteration 140) — so it writes **`element+0x34`**, not `record+0x34`. I trusted the companion scan's `base=r2` without tracing `r2`; two instructions would have caught it. `record+0x34` therefore has **no identified second writer** (still not claimed write-once — 85 untraced writers ROM-wide), so iteration 144's withheld conclusion stands for an honest reason instead of a mistaken one. **`0x020804E8` (40 bytes, 3 call sites) is the element's REPOSITION function**: it copies `+0x0C`/`+0x10` into `+0x14`/`+0x18`, writes `arg1`/`arg2` as the new current pair, then `orr r1,r1,#0x100` — **it sets the snapshot suppressor** because it has already done the snapshot itself. That closes a four-wake thread: iteration 137 found the frame pass honouring `0x100` without knowing its setter; iteration 138 failed to find it in the allocator and reasoned *because the allocator snapshots on every branch* that `0x100` must belong to **repositioning** (SPECULATIVE) — now **CONFIRMED_STATIC**. Also new: `element+0x34` bit **`0x800`**, set at `0x0207EF18` when a **table** entry's byte `+0x15` has bit `8`; the table is at `[[r5+0xF8]+0x18]` with stride **`0x18`** (`smlabb r0,r0,r2,r3` = base + index*0x18) — data-driven flag propagation, so some element behaviour is authored in data. See `findings/the-snapshot-suppressor-is-the-reposition-function.md`.)* **(iteration 146 — THREE open questions closed, via two delegated traces + an independent Codex arithmetic review, all verified before publication.** **(a) `0x800`'s polarity is NOT a contradiction.** `0x020801D4` is the loop-continue point (`ldr r7,[r7]`; `bne #0x207fe88`, then the outer advance), so those `bne`s mean *reject this pair*; `0x0207F7C8` is merely the **next category check** in a chain that files records into per-category lists (`0x800` -> `r6+0x88`, `0x800000` -> `r6+0xC8`, `0x80000` -> `r6+0xD0`). One meaning throughout — *include in your own bucket* vs *exclude from the generic pass*. `0x0207F480` calls `0x0207FBD0` at `0x0207FA64`. **(b) `record+0x34` is NOT write-once** — REFUTED. A four-function set/clear API mirrors every change into `+0x38` **and** the `+0x08` node list: `0x0207D064` (orr), `0x0207D0BC` (bic), `0x0207CF18`/`0x0207CF78` (same, gated on node flag `0x20000000`); and the destructor `0x0207CCD4` does `memset(record, 0, 0x188)` then sets `+0x40 |= 0x200` (free). **(c) Iteration 144's `0x6FF` puzzle SOLVED.** ov6 code ORs **`[record+0x150] & 0xFF`** into `+0x34` (`ldr r1,[r0,#0x150]`; `and r1,r1,#0xff`; `bl #0x207d064` at `0x02165FB0`–`0x02165FB8`), and `0x6FF` covers bits 0–7 — so that test reads **runtime** bits, never the installer's `0x100` seed. The apparent contradiction came from knowing only the construction value. Also: the `+0x5C` misattribution retracted in iteration 145 is **one of seven** instances of the same shape, and `query.py` **mis-bins the flag API** (`func 0x0207D064` reports `0x0207CFE0`) — the merged-record hazard in a fourth module. Codex independently re-derived seven arithmetic claims from raw encodings: all confirmed, and it split the element-size evidence correctly — the tiling proves the **region** is 128 x `0x40`, while `strb +0x3E` proves only that **that struct** needs >= `0x3F`, so the `0x40` element size has **two** gaps, not one. Corrected a subagent claim in passing: `0x0207FBD0` has **one** caller (listed twice, as an edge and a `bl` site) and `0x0207F480` has **0** callers (one `literal_load` at `0x0207C5E8` — a function pointer). See `findings/record-0x34-is-a-mutable-flag-api-and-0x800-is-category-routing.md`.)* **(iteration 146c — RUNTIME CONFIRMATION from justoolkit-06, and the entity call sites are NOT the attack path.** **The `0x40` element stride is CONFIRMED empirically.** Breakpointing the allocator `0x02082C34` and its return at `0x0207CA0C` over 12 live allocations gave returned pointers `0x0220C208`, `0x0220C248`, `0x0220C288`, `0x0220C2C8`, `0x0220C308`, `0x0220C348`, `0x0220C388` — spaced **exactly `0x40`**. Container constant at `0x0220B740`, first element at `container+0xAC8`, and `(0xAC8 - 0x648) / 0x40 = 18` **with no remainder** — which validates the `+0x648` base and the `0x40` stride together. This closes **both** gaps Codex identified: the allocator is the same function that writes `+0x3C`/`+0x3D`/`+0x3E`, so the `+0x3E` struct **is** the region's element type. Two further corroborations: `r2` was in **DTCM** (`0x027C394C`), matching `add r2, sp, #0` — the xy pair is a stack temporary with no persistent struct to find; and elements read back as **all zeros**, which is the destructor `0x0207CCD4` memsetting `0x188` observed live. **Critically: the three known entity-constructor call sites are not on the attack path.** `0x02164F0C` and `0x02164F48` are both inside **`0x02164D48`** (ov6, 772 bytes), bracketed by census-named `BattleMapLoadItem` (`0x021644E8`) and `BattleMapItemInit` (`0x02165368`) -> **map items**; `0x02168E44` is inside **`0x02168CF4`** (ov6, 616 bytes), immediately above `Battle_ObjCtrlManCreate` (`0x02168BA0`) -> **object control**. PLAUSIBLE (bracketed proximity, not tags). This explains 06's verified negative: pressing plain B four times produced **zero** allocations. => **Projectiles are a different subsystem: `Battle_ObjShotManCreate`, ov6 `0x0216A7D4`, `0x3FD4`, `BattleObjShot.cpp`** — untraced, and now the top task.)*
- Is there a separate, unfound ×1.5 nature-advantage multiplier, or does JUS implement "nature advantage" as baked-in per-koma damage tables rather than a runtime multiply?
- Exact call site (of 358 total, ~60+ within ov6) where `0x0200D12C` is invoked with literal divisor 5 for the ground-truth damage/5 term — none found.

---

## Subsystem: jpower-indirect

**Status:** PARTIAL (4 confirmed / 1 plausible claims)

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | `bin/jpower.bin` is opened by `0x021652E8` **inside `ov5`** (menu/Jump-Galaxy overlay), tagged `JPowerData_Create` via its own debug-allocator strings. The filename string has exactly **one** xref in the whole ROM — this site. | `0x021652E8` | **CONFIRMED_STATIC** |
| 2 | Per-entry stride is exactly `0x130` (304 bytes), matching `JPowerEntry.BlockSize`. Accessor `0x02165398` = `base + index*0x130`; sibling `0x021653AC` adds unexplained nested `+0x3c`/`+0x14` sub-strides. | `0x02165398`, `0x021653AC` | **CONFIRMED_STATIC** |
| 3 | Exhaustive sweep of all 324 ROM-wide call sites to `0x0200D12C` found only 6 with literal divisor 5; the one **arm9** site (`0x020795E8`) is UI icon-grid pixel math, unrelated to combat. | `0x020795E8` | **CONFIRMED_STATIC** |
| 4 | The remaining 5 divisor-5 sites are all inside **ov5**, all implementing 5-column menu-grid row/column math — also unrelated to combat. Combined with claim 4 above, this rules out *both* canonical ARM ÷5 idioms anywhere in the ROM as the damage formula's ÷5 term. | `0x021535C0`, `0x02159D24`, `0x02159D38`, `0x02159EC0`, `0x0215A014` | **CONFIRMED_STATIC** |
| 5 | The scratch base `[[char+0x1a8]+0x10]` is rooted at the MoveInfo object: allocated (`0x02156A58`, size `0x1F0` = 496 bytes) inside `0x02156A38`, and installed into `char+0x1a8` by setter `0x021570EC`. **(2026-08-15, iterations 73–74 — "MoveInfo" is a MISNOMER; it is the pooled entity, and `char+0x1a8` hangs off the `0x1F0` battle character.** The allocator `0x0201A21C` is tagged, and the call site at `0x02156A58` passes `"BattleChara.cpp"` / `"Battle_CharaCreate"`. The `0x1F0` object **is the battle character**; the outer object holding it at `+0x1a8` — with the gauge at `+0x56c`, so ≥ `0x570` bytes — is something else, and is not heap-allocated. See `findings/allocations-are-tagged-and-the-battle-character-is-0x1F0.md`.)* MoveInfo's own `+0x10` field points at the delta-holding sub-object (`+0x40` flags bit `0x800` gates delta application). The writer of that sub-object's `+0xE8`/`+0x130` fields is still unfound. | `0x02156A38`, `0x02156A58`, `0x021570EC` | **PLAUSIBLE** |

**Lens extras (verification round, apply directly to this subsystem):**
`311 × 304 = 94,544` bytes is the exact on-disk size of `jpower.bin`, matching `JPowerEntry.BlockSize`. **All 147 nonzero `damage1` values in jpower.bin are multiples of 5** — this is very likely *why* no runtime ÷5 instruction was ever found: the division may never execute as a live instruction at all (pre-divided data, or a cached/pre-computed value). And because **ov5 and ov6 share the same overlay window and are mutually exclusive**, the live battle overlay (ov6) physically cannot have ov5's loaded `jpower.bin` blob resident at the same time it is running — jpower data must be staged into some other in-RAM structure before battle, or the per-hit damage is pre-resolved before ov5 unloads.

### Refuted hypotheses (jpower-indirect)

- **div5-idioms-absent-ROM-wide:** neither the inlined magic-multiply (damage-pipeline claim 4) nor the generic-subroutine-with-literal-5 idiom (claims 3–4 here, 324-site exhaustive sweep) implements the documented ÷5 term anywhere in the ROM.
- **ov6 reads jpower.bin directly at hit time** — refuted by construction: the file's only xref is in ov5, and ov5/ov6 cannot be co-resident.

### Open questions

- If ov6 never touches the jpower blob, does the arm9 per-character asset loader (`0x02074728`) fetch pre-converted jpower-derived data through a different path, or is jpower.bin a **menu-only** display table (e.g., a Jump-Power stat graph) rather than the live combat table, despite its byte-level match to the researcher-labelled file?
- What do the `0x021653AC` sibling accessor's extra `r2*0x3c`/`r3*0x14` index terms select within each 304-byte block?
- Same ARM/Thumb-lookback caveat as damage-pipeline: the div5 sweep used a fixed 8-byte ARM-mode lookback and could miss a Thumb-mode call site.

---

## Subsystem: hitbox-priority

**Status:** PARTIAL *(loop-state: TRACING — most-refuted subsystem; round-2 angle DELIVERED, see below)*

> ### Round-2 finding (2026-08-14): the three failed rounds searched a broken listing
>
> `jus_files/analysis/disasm/ov6.txt` decodes the whole battle overlay as **ARM**, and large Thumb
> regions come out as garbage (`0x02151300` reads as `stmvs sb, {r0, fp, sp, lr}`). Because ARM
> decoding steps 4 bytes, odd-halfword addresses are **absent from the file entirely** — 4 of the 5
> Thumb HP-apply call sites don't appear in it at all. `functions.json` labels only **18 of ov6's
> 752 functions** as Thumb.
>
> That is a sufficient explanation for both open questions below — "no two-entity comparison found
> anywhere" and B11's "damage-formula site unfound across 3 rounds". **Neither is evidence the code
> is absent.** New tool `scripts/decomp/thumb_dis.py` (validated against two independently-known
> sites) makes the region readable. Full write-up: `findings/c3-hitbox-priority-round2.md`.
>
> This removes a false constraint; it does **not** promote any claim below.

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | `0x020924B0` is **not** a raw pointer array — it is an 8-byte-stride table of homogeneous `{word0, word1}` records, indexed via `lsl#3` by the arm9 character-load routine. | `0x02074730`, `0x02074780`, `0x02074728` | **CONFIRMED_STATIC** |
| 2 | `word0` of a `0x020924B0` entry is a NUL-terminated ASCII character-ID C-string (e.g. `"db_b_01"`), fed through a strcpy-like byte loop. | `0x0207478C`, `0x0209E92C` | **PLAUSIBLE** *(was CONFIRMED_STATIC; demoted — aliasing lens REFUTED)* |
| 3 | The table has exactly 74 entries; ov0 function `0x0214EFAC` linearly scans all 74, extracting a 6-bit id (`word1` bits 14–19), hypothesized to equal chr_b's `classId`. | `0x0214EFD8`, `0x0214F034` | **SPECULATIVE** *(was CONFIRMED_STATIC; demoted — 2/3 lenses REFUTED)* |
| 4 | ov6 `0x02159EF8` (per-character state dispatcher, gated on `r6+0xCB`/`+0xD2`/`+0xD3`/`+0x1A4`/`+0x1A8`) is architecturally the right neighborhood for clash resolution, but no direct two-base-register hitTier comparison was found inside it. | `0x02159EF8`, `0x0215A03C` | **SPECULATIVE** *(2026-08-14: a concrete mechanism has now been found inside it — a **pending-damage accumulator flush** at `0x0215A300`–`0x0215A334`, applying `[r6+0x1A8]->+0x10->+0x140` to HP and `+0x144` to SP, each skipped when zero. **Update: the accumulator is REFUTED as the melee path** — a breakpoint at the flush logged `r1 = 0` on every hit during a run with two landed 6.000 hits. The accumulator exists and is flushed, but melee does not fill it. See `findings/c6c-damage-accumulator.md`. Claim 4 stays SPECULATIVE — the writer is not found — but it now has something concrete to hang on.)*|

**Nuance on claim 2's demotion:** the ASCII char-ID string itself is real and confirmed (entry 0 spells out `"db_b_01\0"` byte-for-byte). What was refuted is the framing that this string is "used to build the collision (and sibling sound/ai) resource path": the one traced consumer (claim 3's ov0 function) actually builds a **sprite-archive (`.aar`) / ending-credits** resource key, not a collision-file key — `c.aar` is a documented sprite-archive suffix convention (`ARM9-Research-Guide.md`), and the consuming subsystem is the game's ending/credits sequence.

**Nuance on claim 3's demotion:** chr_b's `classId` field actually ranges 256–684 in the exported data, which cannot fit in a 6-bit extraction (max 63) — the identification was a tracer arithmetic error, caught by two independent lenses. Only the table's raw shape (74 × 8-byte records) survives verification.

### Refuted hypotheses (hitbox-priority)

- **`0x020924B0` = char-ID-string-table-not-collision:** it is **not** a collision-blob pointer table, contrary to the framing carried in prior documentation (`ARM9-Research-Guide.md`'s "Collision file pointer table"; `Research-Status.md`'s "ARM9.bin offset 0x0924B0 contains pointer table to collision file names" — see the correction note added to `Research-Status.md`). It is an 8-byte-stride `{ASCII char-ID string, packed word}` table, and its one traced consumer is unrelated to collision loading.
- **The 6-bit id in `word1` is not chr_b's `classId`** — refuted by range mismatch (256–684 vs. a 6-bit field's 0–63 range).
- **The original round-1 next-angle** ("trace forward from the resource-loader thunks `0x0201A228`/`0x02010254` reached backward from `0x020924B0`" — **note, iteration 133: `0x0201A228` is not a resource-loader thunk, it is the real heap allocator; `0x0201A21C` is only a linker veneer to it**) is now a dead end, per the above — round 2 must use a different entry point (see next-campaign spec **B11**, which supersedes it).

### Open questions

- Where is the actual runtime `CollisionEntry` parser — the code that walks the loaded 20-byte-stride collision array field-by-field at hit-test time? Not located in this campaign at all. **(2026-08-14: the code is still unfound, but the DATA is now extracted — `chr/ChrBin.aar` was never unpacked and contains 281 collision files, 2837 records, stride 20 confirmed. The 20-byte claim is validated against the data. Two low-cardinality columns, `+0x10` (4 values) and `+0x11` (7 values), have the shape of `hitTier`/`hitProperties` — named as candidates only. See `findings/collision-data-extracted.md`.)** **(2026-08-14, later: those two candidates are now CONFIRMED_STATIC. `src/JUS.Tool/Combat/Converters/Binary2Collision.cs:74-100` is an authoritative field-by-field reader nobody in this campaign had read; it names `+0x10 HitTier` and `+0x11 HitProperties` exactly, and its four `Reserved0`–`Reserved3` slots land exactly on the four columns independently found uniformly zero (`+0x06/0x0B/0x12/0x13`). The runtime parser is still unfound — this is the *exporter's* schema, not engine code. See `findings/shot-data-and-projectileid-refuted.md`.)** **(2026-08-15: the question is now NARROWED, not closed. ov6 `0x02155900`–`0x02156900` is a bank of ~36 tiny functions that read collision fields off a record pointer passed in `r1` — **11 of the 16 named fields** are read there, including `HitTier`. It is an *accessor/stub layer*, **not** the walker: no stride arithmetic (`#0x14`) appears anywhere in it, which refuted my own first reading. 31 of the stubs pass a hardcoded kind constant (`0..16`, 17 distinct) to a shared factory `0x021565A4`, which indexes a **17-entry kind→slot table at `0x021710A8`** and builds 16-byte slot records. Two stubs (kinds 8 and 14) copy `ProjectileId` verbatim to slot`+0x02`. **The callers of these stubs are where the walker will be.** See `findings/collision-accessor-bank-and-kind-table.md`.)** **(2026-08-15, later: the stubs turned out to be entries in a 68-entry function-pointer table, not directly called — but the *loader* is now identified. **`Battle_PrmDataInit` at `0x021702BC` (ov6 `BattlePrmData.cpp`) loads the collision, shot and effect files and stores the loaded pointers in a `0x20`-byte struct: `+0x00` = the `chr/col/*.bin` record array, `+0x04` = `chr/shot/`, `+0x08` = `chr/effect/`** — prefixes pinned by literal-pool arithmetic at pools `0x02170488`/`0x02170490`/`0x02170494`. It selects the filename from the arm9 name table (`0x020924B0`, 74 battle entries at 8-byte stride; `0x02092700`, 193 support) via a 3-way `kind` switch whose third case loads `chr/col/item.bin` directly. **So the runtime collision array lives at `prmData+0x00`, and the walker reads it from there.** See `findings/prmdatainit-is-the-collision-loader.md`.)**
- No two-entity `hitTier`/`hitProperties` comparison (the literal clash-resolution code) was found anywhere in ov0/ov3/ov4/ov5/ov6.
- What does the 6-bit id in `word1` actually encode, if not `classId`? It increments by exactly 1 between consecutive raw table entries, consistent with *some* dense per-character index space, just not the one hypothesized.

---

## Subsystem: projectile-entities

**Module layout (2026-08-15, from recovered assert-string symbols — see `findings/module-map-and-attribution-limits.md`).** This subsystem spans three source files, which explains several of its claims:

| layer | module | addresses |
|---|---|---|
| generic object pool | **arm9 `BattleObj.cpp`**, `Battle_ObjManCreate` `0x02083204` | claim 1 ctor `0x020834D4`, claim 2 dtor `0x02083648` — both inside a tight `0xDC8` range |
| object control | **ov6 `BattleObjCtrl.cpp`**, `Battle_ObjCtrlManCreate` `0x02168B88` | claim 4 spawn/ownership `0x02168CF4` |
| projectile specialisation | **ov6 `BattleObjShot.cpp`**, `Battle_ObjShotManCreate` `0x0216A7BC` | claim 5 `0x0216C958` and siblings `0x0216E1C0`, `0x0216F398` |

**(2026-08-15, iteration 52 — claim 1's manager singleton independently confirmed.)** All **22** references to `0x0214BE14` in the ROM are in arm9 `BattleObj.cpp`, reached by word-reference counting rather than the module-range attribution used above. Two unrelated methods, one conclusion. The adjacent global `0x0214BE10` is the **BattleColPrm manager** (7 of 9 refs in `BattleColPrm.cpp`; written at `0x0207C844`), which holds a pair-wise contact array at `+0x158` — see `findings/colprm-contact-matrix.md`. Both sit in the globals block that also holds the chr_b base pointer at `0x0214BD80`.

Claims 1 and 2 being *generic* pool code is why claim 2's destructor has 30 call sites across arm9 and ov6 — it is shared infrastructure, not projectile-specific. All attributions here are **PLAUSIBLE**: an unnamed translation unit can hide inside any gap, and claim 5's containing interval is `0x5B00` bytes wide.


**Status:** PARTIAL (4 confirmed / 1 plausible). **Adversarial lens verification completed this phase (Phase-0 spec P3).** The prior campaign's "evidence machine-verified; adversarial lens verification pending" caveat no longer applies — all 5 claims ran through the standard 3 lenses (disasm-correctness / aliasing / data-consistency) and were scored; the confidence column below is now the authoritative post-verification confidence, not a stated/pending pair.

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | **Alloc (Q1):** `0x020834D4` is a fixed-capacity pooled-entity constructor. Dereferences global manager singleton (literal `0x0214BE14`); checks manager`+0x14` (candidate free-list head) for NULL; invokes a caller-supplied ctor callback via `blx`, storing the result at `entity+0x30`; unlinks from `+0x14`, appends to manager`+0xc` (success) or `+0x1c` (failure). **(2026-08-15, iteration 72: this constructor also WIRES UP COLLISION.** At `0x02083560` it calls the ColObj installer `0x0207C988`, keeping the result at `entity+0x10`. The installer creates a `0x40`-byte ColObj via `Battle_ColObjCreate` and installs three method pointers — `+0x1C` acquire and `+0x20` release against the **ColPrm `+0x18` node pool**, plus `+0x24` — and sets `ColObj+0x28` to the owning object. So collision registration is part of entity construction; there is no standalone registration call. First link between this subsystem and the collision subsystem mapped in iterations 52–71. See `findings/collision-wired-by-the-entity-constructor.md`.)** | `0x020834DC`–`0x020835F0` | **CONFIRMED_STATIC** |
| 2 | **Free (Q1):** `0x02083648` is the symmetric destructor — sets `entity+0x2c` bit 0 ("marked dead"), calls the on-destroy hook at `entity+0x10` (a direct `bl` through a fixed callee, not an indirect call *through* the field — a minor prose correction from the disasm lens), unlinks from manager`+0xc` (active list), appends to manager`+0x1c` (pending/retire list). **Corrected caller count: 30 real call sites (2 arm9 + 28 ov6), not the originally-stated 32 (2/30).** | `0x02083650`–`0x02083690` | **CONFIRMED_STATIC** |
| 3 | **Spawn dispatch (Q2):** ov6 `0x021574CC` is a 13-way switch keyed on its 3rd argument, operating on the character struct's `+0x1a4` (hit-tally) and `+0x1a8` (MoveInfo). **Corrected case index: the traced path is selector `r2=7` (jump-table target `0x2157684`), not index 8 as originally labeled** — an off-by-one in the label only, not in the traced control flow. It unconditionally reaches `0x2168cf4` at `0x02157700`, passing the character's MoveInfo pointer and a per-move collision/type data block, gated by a "one active spawn at a time" cap on `character+0x1ac`. | `0x02157684`–`0x021576C0` | **CONFIRMED_STATIC** |
| 4 | **Spawn + ownership (Q2/Q4):** `0x02168CF4` obtains a spawner/wrapper object from a second, ov6-local manager (literal `0x02172990`), calls the `0x020834D4` allocator, stores the new entity pointer at wrapper`+8`, and stores the attacking character's **MoveInfo pointer** (not the character struct directly) at wrapper`+0xc`. **The aliasing lens closed the campaign's own open question here:** the dispatcher's caller (`0x02157720`, immediately after `0x2168cf4` returns) additionally stores the raw **character struct pointer** into wrapper`+0x18` — a direct character-struct back-pointer *does* exist, just one level up on the wrapper rather than inside the pooled entity itself. | `0x02168CFC`–`0x02168E5C` | **CONFIRMED_STATIC** |
| 5 | **Despawn (Q3):** ov6 `0x0216C958` has 4 independent per-frame kill conditions, all converging on `0x02083648`: (a) a flag-bit/boundary-test gate; (b) a 16-bit age counter at `entity+4` vs. hard threshold `0x20` (32 frames) — **with a previously-unquoted suppression bit** (`[entity+6]&0x2`, checked at `0x0216CA74`, can suppress this destroy even past the age cap); (c)/(d) a *bounded-range* check `[0x100, 0x3FF00]` on a separate field (not "under both thresholds" as originally phrased). **Capped PLAUSIBLE:** the aliasing lens found the identical per-frame-check scaffolding (movement-delta accessor `0x216B740`, boundary helper `0x216EE14`) reused near-identically by ≥2 sibling spawned-object update routines elsewhere in ov6 (`0x0216E1C0`, `0x0216F398`) — this function cannot be statically proven to be *the* projectile despawn routine rather than a generic spawned-effect one. **(2026-08-15: that specific doubt is now NARROWED. Recovered assert-string symbols put all three routines in the same module — `0x0216C958`, `0x0216E1C0` and `0x0216F398` are respectively `Battle_ObjShotManCreate` +`0x219C`, +`0x3A04`, +`0x4BDC`, and that function's source file is `BattleObjShot.cpp`, the projectile "object shot" module. So the shared scaffolding is siblings inside one projectile translation unit, not a sign this is generic-effect code. Deliberately NOT promoted: neighbourhood attribution is PLAUSIBLE evidence and does not say which of the three is the despawn. Contrast claim 4's `0x02168CF4`, nearest `Battle_ObjCtrlManCreate` / `BattleObjCtrl.cpp` — a different module. See `findings/symbol-names-recovered-from-assert-strings.md`.)** | `0x0216CA00`–`0x0216CAE8` | **PLAUSIBLE** |

**(2026-08-17, iteration 147 — the BattleObjShot manager is now mapped, and shot behaviour is a 27-way table dispatch. CONFIRMED_STATIC.)** `Battle_ObjShotManCreate` `0x0216A7BC` is confirmed by its own allocator arguments (`__FILE__` `0x021728D0` `"BattleObjShot.cpp"`, `__FUNCTION__` `0x02172774`, `__LINE__` `0x118`), not by proximity — the first attribution in this subsystem that does not rest on module ranges. Manager is **`0x3FD4`** bytes, singleton at **`0x021729EC`**: `+0x00` active-list head, `+0x10` free-list head, `+0x18` a resource object from `0x02026F94` (id **`0x88000`**, same family as `MoveMan`'s `0xA1000`/`0xA6000`), `+0x1C` an array of **72 elements of `0x6C`** ending at `+0x1E7C`. Per-frame entry point is **`0x0216AF04`**, registered via `0x02028384`. The shot element's kind byte at `+0x1A` indexes a **27-entry function-pointer table at `0x02172864`** (kinds `0x00`–`0x1A`); the table's arity is pinned by data on both ends — it starts at `0x02172864` and the `"BattleObjShot.cpp"` string starts at `0x021728D0`, leaving exactly `0x6C` bytes, with no bound check in the caller. Six kinds (`0x01`, `0x05`, `0x0E`, `0x17`, `0x18`, `0x19`) carry no entity at `+0x2C`; the other 21 do, written by the handler rather than the initializer `0x0216ACC8`. Two byte-identical leaves `0x0216B3D8`/`0x0216B740` independently re-confirm the `entity+0x10 → ColPrm record → record+0x5C → MoveMan element → element+0x0C position` chain from a module we had not read. New: `record+0x17C` gates the multi-target spawn filter, and MoveMan element `+0x34` bit **`0x200`** is cleared on projectile attach (`0x0216AE80`) — a sibling of the known `0x100` snapshot suppressor. Note the manager offsets here (`+0x00`/`+0x10`/`+0x18`/`+0x1C`) are a *different* struct from the generic `BattleObj` manager `+0xc`/`+0x14`/`+0x1c` in the open question below; do not merge them. Also a **fifth `functions.json` binning gap**: kind `0x1A`'s handler `0x0216B2A0` is absent from the database (`0x0216B220` ends at `0x0216B29C`, next record `0x0216B2C8`). See `findings/objshot-manager-and-the-27-kind-dispatch-table.md`.

**(2026-08-17, iteration 147b — reachability CONFIRMED, and a NAMED TOOL BLIND SPOT that may invalidate past "0 callers" reasoning.)** `query.py xrefs-to 0x0216A7BC` reports **0** references, which would make this whole subsystem dead code. It is not. Three sweeps over arm9 + all 15 overlays: a raw data-word search finds **0** hits (control: the frame pointer `0x0216AF04` finds exactly **1**, in `ov06.bin` at offset `121760`); an ARM `bl` decode finds **0** for both ov6 constructors (control: `Battle_MoveManCreate 0x02082A38` finds exactly **1**, `arm9 0x020833D0`, encoding `0xEBFFFD98`); a **Thumb `BLX(1)` decode finds exactly 1 site each** — `0x0214D818 blx 0x02168b88` (ObjCtrl) and `0x0214D826 blx 0x0216a7bc` (ObjShot), 14 bytes apart in one sequential Thumb battle-init routine in ov6. Each stores its manager into the battle root via the root pointer global **`0x02172960`** (reached through the literal pool word at `0x0214D928`; **that address is the pool slot, not the global** — see `findings/p161-the-root-global-notation-fix.md`): **ObjCtrl → root `+0x10C`** (`0x43 << 2`), **ObjShot → root `+0x110`** (`0x11 << 4`). Both slots fall inside the battle root's known `0x170` bytes. **The blind spot: `xrefs.json`'s branch index does not record Thumb `BLX(1)` → ARM call sites, so "0 references" on an ARM function means "no ARM caller", NOT "unreachable."** **Self-correction, same iteration:** my first draft called this "the first time the cause is named." **Retracted** — the blind spot was already named and measured in `findings/thumb-caller-audit.md` (iterations 95–96), which reports the same **187** of **3691** figure this pass reproduced. **What is genuinely new is a correction to that audit:** `find_thumb_callers.py --to` finds and ACCEPTS both constructors, but `--audit` lists neither, because line **184** gates `--audit` on the `plausible()` heuristic while `--to` does not. Both sites score `plausibility: NONE` and are nonetheless real (coherent Thumb disassembly, two BLX pairs 14 bytes apart onto two named constructors). So **the audit's 187 ROM-wide and 16 in-battle counts are a floor, not a census**, short by at least these two. Past "0 callers, therefore a function pointer / vestigial" claims still need a Thumb re-check, and `--audit` alone cannot clear one — `--to` on the specific address can. Checked directly and **not** rescued by any Thumb caller: `0x0207E864`, `0x0207F7C8`, `0x0207DD40`, `0x0216B2A0` (zero hits each), so the `0x0207E864` function-pointer claim survives.

### Refuted hypotheses (projectile-entities)

None of the 5 claims were outright REFUTED by any lens. Claim 5's downgrade is a capped-PLAUSIBLE (UNSURE verdict from the aliasing lens, not a REFUTED one) — its four-kill-condition mechanics were independently re-confirmed instruction-for-instruction; only the "is this specifically the projectile update routine" identity is unresolved.

### Open questions

- **Q5 (persistence across character switch)** remains unresolved — no claim was made, per the no-guessing rule. The only observed ownership links (wrapper`+0xc`→MoveInfo, wrapper`+0x18`→character struct) and the self-contained despawn conditions (no "is my owner still active" check found) are both *consistent with* persistence but do not prove it.
- Exact semantics of manager`+0xc`/`+0x14`/`+0x1c` (working hypothesis: active/free/pending lists) are still inferred from control flow only — never confirmed against a live dump.
- Whether `0x0216C958` is projectile-specific or a shared generic spawned-effect updater (claim 5's capped confidence) needs a live GDB census across the ≥2 sibling routines the aliasing lens found reusing the same scaffolding.
- Finalizers `0x2083c44`/`0x2083cd8` index a per-category table via `entity+0x38` — unexplored as a possible projectile-vs-other-spawned-object type tag.

---

## Subsystem: physics-writers

**Status:** PARTIAL *(loop-state: TRACING — round-2 angle DELIVERED, see below; velocity/gravity/decay still not isolated)*

> ### Round-2 finding (2026-08-14): the region is an ARRAY, not a set of velocity fields
>
> ov11 `0x0217E4A0` writes three **identical** 5-field groups on one base register at **stride `0xC`**:
> records at `+0x58`, `+0x64`, `+0x70`, each laid out `+0x0` word, `+0x4` half, `+0x6` half,
> `+0x8` half, `+0xA` byte, from the same source registers in the same order.
>
> **All six GDB-observed "physics" offsets fall inside it** — `+0x6A` = record 1 field `+0x6`,
> `+0x6C` = rec 1 `+0x8`, `+0x72` = rec 2 `+0x2`, `+0x74` = rec 2 `+0x4`, `+0x7A` = rec 2 `+0xA`,
> `+0x7C` = **record 3** `+0x0` (so there are ≥4 records). The 2026-02-03 session read them as three
> 16-bit pairs at 8-byte spacing; they are different fields of different records at 12-byte spacing.
> The observation was real, the framing wasn't.
>
> **This explains the round-1 failure better than the tool gaps do:** there is no single "X/Y velocity
> offset" to find. Likewise the `+0x98`–`0xBA` "timer region" (`+0x98`, `+0xA0`, `+0xA8`, `+0xB0`,
> `+0xB8`) is **stride 8** — a second array, of 8-byte records.
>
> Layout is CONFIRMED_STATIC; that it's the same struct GDB observed is PLAUSIBLE; **what the records
> mean is unknown** and deliberately not guessed — naming them velocity fields is what produced four
> demoted claims in round 1. Full write-up: `findings/c4-physics-is-an-array.md`.

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | Collision-derived `+0xE8`/`+0x130` deltas are negated and dispatched to two writer functions on `[sl+0x1b4]` — originally read as a "knockback-impulse consumer." | `0x02158BA8`–`0x02158BC4` | **SPECULATIVE** *(was PLAUSIBLE; demoted — 2/3 lenses REFUTED)* |
| 2 | `arm9 0x020781E4` accumulates a delta into `object+0x5C8` with modulo-`0x6400` wraparound (`0x64 × 0x100` = percent × 256 fixed point) — reads like a **percentage/hitstun meter**, not an X/Y velocity (`+0x5C8` is far outside the documented `+0x6A`–`0xBA` physics window). | `0x020781E4`–`0x02078204` | **PLAUSIBLE** |
| 3 | `0x020783CC`/`0x02078488` (originally read as a velocity writer) actually re-derive the **same** `char+0x56c` gauge-clamp accumulator from damage-pipeline claims 5–6 — an HP/gauge clamp, not X/Y velocity. | `0x020783CC`, `0x02078488` | **SPECULATIVE** *(was PLAUSIBLE; demoted — 2/3 lenses REFUTED)* |
| 4 | ov6 wrapper offset `+0x6A` is written by `0x021607C0`, a "track-the-minimum-seen + saturating hit counter" (bhs-guarded compare, no addition), not a per-frame velocity accumulator. | `0x021607C0` | **SPECULATIVE** *(was PLAUSIBLE; demoted — 2/3 lenses REFUTED)* |
| 5 | **Concrete aliasing proof:** in ov7, `0x021619D8`–`F4` folds `+0x100` into the base register **before** storing to `+0x68`/`+0x6a`/`+0x6c` — those stores actually land at `+0x168`/`+0x16A`/`+0x16C`, not the documented physics region. This is the exact "timer mistaken for velocity" pitfall, demonstrated at these precise offsets. | `0x021619D8`–`0x021619F4` | **CONFIRMED_STATIC** |

### Refuted hypotheses (physics-writers)

- The `0x020783CC`/`0x02078488` pair is **not** a velocity/knockback writer — it is the shared HP/gauge clamp-accumulator (same function as damage-pipeline's `ApplyDeltaToCurrent`).
- The ov6 wrapper's `+0x6A` field, written by `0x021607C0`, is **not** a velocity component — it is a hit-priority/lockout tracker living on the `+0x1a4` hit-tally object, not necessarily the deeper GDB-verified character struct.
- The `+0xE8`/`+0x130` fields are **not** on a raw "collision entry" — they live on the MoveInfo-rooted scratch workspace (same object damage-pipeline claim 8 investigates).
- **Structural, ROM-wide lesson documented here:** naive `search-imm` sweeps at `+0x6A`–`0x7C` are dominated by false positives because at least one real function (ov7 `0x021619D8`) folds a constant into its base register before the store — this explains why this subsystem's search produced heavy noise, and the same folded-base pattern recurs in hitstun-timers (twice) below.

### Open questions

- The X/Y velocity fields, gravity constant, decay/friction term, and the "0xC0 launched-state writer" (Q3/Q4/Q5 in the original brief) were **not found** this round. The tool used (`search-imm`) can only find load/store immediate *offsets*, not register-indexed or jump-table addressing — likely why the launch-state writer (13 exhaustively-enumerated `+0x78` accesses, none matching) evaded static search entirely.
- Whether `[sl+0x1b4]` is the same runtime object as the GDB-verified character struct (rooted at `0x023D2A74`) or one more indirection away remains open — see cross-cutting identity note below and next-campaign spec **B10**.

---

## Subsystem: hitstun-timers

**Status:** PARTIAL (4 confirmed / 2 speculative claims)

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | Character-struct constructor `arm9 0x02053528` zero-initializes `+0x98`, `+0x9c`, `+0xa0`, `+0xa4..+0xac` (12-byte memset), `+0xb0`, `+0xb4` alongside the known `+0x78`/`+0x88` fields — confirms the whole `+0x98`–`0xb4` span belongs to the character struct. Construction-time zero-init only; the nonzero hitstun-init writer is not this function. | `0x02053584`–`0x02053614` | **CONFIRMED_STATIC** |
| 2 | Ruled out: ov0 `0x02157138` allocates an unrelated 172-byte settings object that coincidentally reuses offsets `0x98`–`0xa1` for config flags — not the character struct. | `0x02157148`–`0x0215748C` | **CONFIRMED_STATIC** *(exclusion result)* |
| 3 | Ruled out: `arm9 0x02080F14`'s `r8 = r0+0xa4` folded base means its apparent `+0xa8`/`+0xaa`/`+0xb0` accesses actually land at `entity+0x14c`/`+0x14e`/`+0x154` (an unrelated combo/juggle sub-record) — the same base-register-folding aliasing pattern flagged by physics-writers. | `0x02081148`–`0x02081630` | **CONFIRMED_STATIC** *(exclusion result)* |
| 4 | The canonical single-frame countdown-decrement idiom (`ldrsb/ldrsh; cmp #0; subne #1; strXne`) is confirmed via example `ov6 0x02158E78` (decrementing `sl+0xe0`) — but no occurrence of this idiom was found **at** the `+0x98`–`0xba` offsets themselves. | `0x02158E78`–`0x02158E84` | **CONFIRMED_STATIC** |
| 5 | SPECULATIVE candidate: `arm9 0x0207D16C` writes `r1 → [r0+0xa0]` and ORs `0x800000` into `[r0+0x78]` atomically — structurally matches "init countdown + set launched flag." | `0x0207D16C` | **SPECULATIVE** *(2/3 lenses REFUTED)* |
| 6 | Competing hypothesis: `ov4 0x02151E04`/`0x02151E7C` reads `+0xa0`/`+0xa2` as a 12-bit-fixed-point `(x,y)` **position** pair for a "place object at (x,y)" call — contradicts the timer hypothesis for this specific path. | `0x02151E14`–`0x02151E90` | **SPECULATIVE** *(2/3 lenses REFUTED)* |

**Both speculative leads were refuted by the aliasing lens on independent grounds:** `0x0207D16C`'s `[r0+0xa0]` write actually targets a per-hitbox slot index (not the character struct's `+0xa0`), and its `0x800000` OR bit touches `+0x7A` (a flags byte), not the `+0x78` state byte. The ov4 candidate turns out to be a **third**, distinct, vtable-dispatched per-effect struct that only coincidentally reuses offset `+0xa0`/`+0xa2` — the same "coincidental offset reuse" false-positive pattern documented twice already in this same subsystem (claims 2–3) and once in physics-writers.

### Refuted hypotheses (hitstun-timers)

- Neither `0x0207D16C` nor the ov4 `0x02151E04` candidate is the real hitstun-timer init writer — both are aliasing false positives on unrelated objects.
- This is the **third documented instance** in this campaign of the same failure mode: a small, common struct offset (here `+0x98`–`0xba`-ish) being coincidentally reused by an unrelated object, defeating naive immediate-offset search.

### Open questions

- Where is the nonzero write that actually starts a hitstun/recovery countdown on a live hit or landing? Not found after 3 rounds of static search.
- The pre-existing conflict in `docs/research/Character-State-Struct.md` at `+0xA0` ("Negative Status Flags" vs. "Countdown Timer Region") is **not resolved** — if anything, the ov4 finding adds a third candidate reading (position) without settling it. The GDB-observed ground truth (live decrementing timers at `+0x98`–`0xba`) still stands; only the init site is missing.
- Is `sl` (the object hosting the confirmed `+0xe0` decrement idiom, claim 4) the same object as the GDB base-chain character struct, or the same "one indirection away" wrapper flagged by damage-pipeline/physics-writers?

---

## Subsystem: movement

**Status:** PARTIAL (5 confirmed / 1 plausible claims)

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | chr_b.bin's parsed record array is cached at `*(0x0214BD80)+0x40` inside a global "battle resource manager" singleton. The same manager also owns koma.bin (`->+0x30`) and 3 other unidentified tables (`->+0x44`, `->+0x48`, `->+0x54`). | `0x020760F0`–`0x02076120` | **CONFIRMED_STATIC** |
| 2 | Record stride = `0x3C` (60 bytes, matching `BattleCharacterEntry.EntrySize`). Index = `charStruct[+0x41]`. Reads three consecutive 16-bit fields at `+8`/`+0xA`/`+0xC` = statA/statB/statC — the **only** place in the ROM where chr_b's raw statC is read via this base+stride addressing. | `0x020771A0`–`0x020771C4` | **CONFIRMED_STATIC** |
| 3 | Sibling getter `ov5 0x0214E480` independently confirms the **same** base+`0x40`/stride-`0x3C` mechanism, reading record offset `+0` (= FormType, matching the on-disk layout). | `0x0214E480`–`0x0214E4B0` | **CONFIRMED_STATIC** |
| 4 | `charStruct+0x41` (the index used by claim 2) is populated at spawn time (`arm9 0x02076E38`) from **koma-entry byte offset+7 = PassiveIndex** — not necessarily chr_b's own on-disk `CharId` byte (offset 3). Both are 0–55 ranges but were not proven identical. | `0x02076F48`–`0x02076F64` | **CONFIRMED_STATIC** |
| 5 | **Refutation:** `0x0208D4A0` (previously cited as "chr_b identity map") is **not** chr_b-related — its bytes are a plain ASCII lowercase→uppercase case-folding table, with exactly 2 xrefs in the whole ROM, both inside an unrelated text/glyph-width routine. | `0x0208D4A0`, `0x0208D500`, `0x0208D518` | **CONFIRMED_STATIC** |
| 6 | The **only** located statC consumer (`0x020771C4`/`0x02077178`) is a koma/technique stat-requirement **equality** matcher (does character's statA/B/C exactly satisfy a move's required stat?), not an inequality-based speed-tier bucket. Exhaustive cross-check of all 124 ROM-wide reads with immediate offset `0xC` found no second occurrence of this addressing pattern. | `0x020771CC`–`0x02077290` | **PLAUSIBLE** |

### Refuted hypotheses (movement)

- **`0x0208D4A0` = ASCII-case-fold-not-chr_b-map:** the address previously cited as chr_b's "identity map" is a plain case-folding table for text rendering, unrelated to chr_b, statC, or movement in any way. (See the correction note added to `Research-Status.md`.)
- **The walk-speed tier threshold cmp-chain does not exist at the raw chr_b statC read site.** That site is a koma-technique eligibility check, not a speed selector — the tier thresholds (ticket JUS-n3p) remain fully unresolved.

### Open questions

- Where **is** the cached walk-speed/tier value actually consumed, if not chr_b's raw statC at runtime? Two structural explanations remain untested: (a) tier resolution happens once at load time inside the chr_b "GetData" vtable call (`0x0207611C`, concrete vtable/class not yet identified), caching a derived speed value; or (b) it is a register-indexed table lookup (`speedTable[statC]`) invisible to immediate-offset search.
- Do the koma PassiveIndex (0–55) and chr_b's own on-disk CharId (0–55) numbering spaces literally coincide, or merely overlap in range?
- Per-character virtual-dispatch tables cached at `char_struct+8` (KomaType-indexed) and `char_struct+0x42` (per-character dispatch result), discovered incidentally in claim 4's init routine, are unexplored and are the most promising lead for both dash/flash-dash speed (Q4) and the Edajima passive-slowdown exception (Q5).

---

## Subsystem: weight-hunt

**Status:** PARTIAL (3 confirmed / 2 plausible / 1 speculative claims)

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | Status-effect-slot manager `ov6 0x02158ED0` recomputes hitstun duration via: **`newDuration = floor(duration/10) × [table+0x4c] × 2 + duration`** (division via `0x0200D12C`, doubling via `lsl#1`, combined into one `mla`). | `0x02158F58`–`0x02158F88` | **CONFIRMED_STATIC** |
| 2 | `0x0200D12C` reconfirmed as a generic signed-division primitive with no character-specific data of its own. | `0x0200D12C` | **CONFIRMED_STATIC** |
| 3 | The `[table+0x4c]` index is **not** the incoming attack-type parameter — it is a signed byte at **object offset `+0x1e0`** (`sb+0x100+0xe0`, double-indirected). This field is also read/compared elsewhere against a cached value, consistent with a **transient "current hit-type/element" tracker**, not a static per-character weight constant. Its write site was not found. | `0x02158F60`–`0x02158F74` | **CONFIRMED_STATIC** |
| 4 | New chr_b getter `ov5 0x0214E480` reads record offset `+0x0` (previously unexamined), gated behind two "work"-object condition checks. | `0x0214E480`–`0x0214E4B8` | **PLAUSIBLE** |
| 5 | The only located caller of the offset-`+0x0` getter (`ov5 0x02151B58`–`84`) fills a character-select/roster **display** record — arguing against `+0x0` being the weight/knockback value (reads as a UI/series classification instead). | `0x02151B58`–`0x02151B84` | **PLAUSIBLE** |
| 6 | A per-index bitfield accessor off the same chr_b singleton (`+0x60`, `GetFlag(idx)`) is architecturally the right shape for a per-character passive/ability table — but the one located call site indexes by a **move-id composite**, not `charIndex`. | `0x0214D594`–`0x0215CE78` | **SPECULATIVE** *(was PLAUSIBLE; demoted — 2/3 lenses REFUTED)* |

**Nuance on claim 6's demotion:** the traced call site actually hits a move-data cache lookup, not a passive-flag test. The real `GetFlag` consumer is only reachable via an indirect callback in `ov1`, which the disassembly database's function-boundary heuristics (a known `bx <reg>`-epilogue detection gap) had merged into the wrong neighboring function.

### Refuted hypotheses (weight-hunt)

- **`sb+0x1e0` = transient-hit-type, not weight.** The `[table+0x4c]` hitstun-scaling index chased across this entire subsystem is a per-attack/element classifier that changes per hit, not a static per-character weight/knockback-resistance constant. This closes off weight-hunt's primary lead as a dead end.
- The `+0x60` bitfield accessor is **not** confirmed as a per-character passive/ability table (2/3 lenses REFUTED) — its only found caller is move-id-keyed, and the real consumer was hidden by a tooling gap, not located.
- chr_b record offset `+0x0` is more likely a UI/roster-display classification byte (FormType) than a weight value, per its sole caller's context.

### Open questions

- Weight/knockback-resistance itself remains **completely unlocated** after 2 tracer rounds.
- **Most promising unchased lead (from loop-state, not yet followed up):** koma.bin's `PassiveIndex` field may key into a separate ~50-entry ARM9 passive table — hypothesized to be the concrete mechanism behind Edajima's documented knockback-resistance passive (see `Research-Status.md`'s "Edajima outlier" note). Flagged as next-campaign spec **B14**; note the PassiveIndex→passive-table lead itself is still unresolved even though B14 (below) is DONE — B14 catalogued the chr_b singleton's *own* record fields, not this separate passive-table hypothesis.
- ~~85 of the ~87 total code references to the chr_b singleton (`0x0214BD80`) remain undisassembled for their record-offset access~~ — **DONE this phase (spec B14):** all 97 (the true total, not ~87) are now catalogued. See § chrb-catalog.

---

## Subsystem: collision-data

**Runtime collision system located (2026-08-15, iterations 52–57).** The static `chr/col/*` records were always the *input*; this is the machinery that consumes them.

`*(0x0214BE10)` is the **BattleColPrm manager** (arm9 `BattleColPrm.cpp`, written at `0x0207C844`):

| region | contents |
|---|---|
| `+0x28`–`+0xD7` | 22 bucket list heads, 8 bytes each — drained every frame |
| `+0xD8` | free list |
| `+0xE0`/`+0xE4`/`+0xE8` | owned sub-objects, each with a registered callback |
| `+0xFC`–`+0x148` | 19-entry phase table (all excluded as array writers) |
| **`+0x154`** | **pair-wise contact array**: rows `0xC0`, elements `0x30`, 4 per row |

**Per-frame driver:** `0x0207F480`, the callback on `+0xE0` — 440 instructions that drain the 22 buckets, then run an **8-stage pipeline** (`0x0207FA60`–`0x0207FA98`), every stage taking the manager as `arg0`. Stage 8 reaches four accumulator blocks at `0x02081340`/`0x02081388`/`0x020813D0`/`0x02081418` which do `add r2,sl,#0x154` and `+=` into element fields `+0x10`(and `+0x28`), `+0x0C`, `+0x08`, `+0x04`.

**Producer/consumer confirmed across binaries:** block `0x02081418` writes element `+0x04`; ov6 query 71 (the move-script predicate "is any other entity in contact?") reads element `+0x04`. The full chain manager→writer is CONFIRMED_STATIC — `r6` holds the manager with zero intervening writes across all 440 instructions.

**Settled (iteration 59): the accumulated values are NOT damage.** Their sole producer `0x020823E4` is 175 instructions of 16-bit fixed-point 2D arithmetic — output `(r5 + r0) >> 2`, 32 shifts against 3 multiplies, delegating to a 303-caller coordinate-packing utility (`0x0207342C`), and containing neither documented damage scalar (`×5` for jpower, `×64` for HP). So the contact array is a geometric/positional ledger and does **not** link collision to the damage pipeline. What the magnitudes positively represent (overlap depth, separation, impulse) is still open. See `findings/collision-pipeline-closed.md` and `findings/contact-array-writer-found.md`.


**Status:** PARTIAL — full-roster scale reached this phase (**round 2**, Phase-0 specs P1+P2). **Coverage:** 281/281 collision JSONs now exist and were mined — 74/74 `*_b_*` battle-character files + 206 `*_s_*` support files + 1 shared `item_collision.json`. Round 1's 4-file/92-entry sample (5.4% roster coverage) is superseded by a full-roster 2047-entry (battle, non-terminator: 1861) / 747-entry (support) pooled dataset — an ~22x scale-up. Still **data-only** (no disassembly; a single data-consistency verification lens, not the usual three). **Round 2 confidence: 3 CONFIRMED_STATIC / 6 PLAUSIBLE / 4 SPECULATIVE** (13 claims; this table fully supersedes round 1's — several round-1 findings *broke*, not merely weakened, at scale).

| # | Claim | Confidence |
|---|-------|------------|
| 1 | `hitTier` still occupies the closed range `{0,1,2,3}` at full scale (pooled non-terminator: `{0:31, 1:789, 2:529, 3:512}`, n=1861) — the round-1 shape survives 20x more data. Terminator rows are **not** uniformly `hitTier=0`: only 118/186 (63.4%) are. | **PLAUSIBLE** |
| 2 | `collisionType=5 → hitTier=3` does **not** hold as a strong predictor at scale: pooled fraction drops from round 1's 87.5% (n=16) to 216/454 = **47.58%** (n=61 characters) — essentially a coin flip. Per-character spread: only 18/61 chars are 100% tier-3, 7/61 are 0%, 36/61 are "partial." | **SPECULATIVE** *(was PLAUSIBLE; round-1's small sample overstated this correlation)* |
| 3 | `collisionType=3 → hitTier=1` is similarly weaker at scale: pooled fraction 522/885 = **58.98%** (round 1: 65.1%). All 74/74 characters have ≥1 type-3 entry (the most universal type), but `hitTier=1` is a strict per-character majority in only 43/74 (58.1%) of characters. | **SPECULATIVE** *(was PLAUSIBLE)* |
| 4 | `knockback` vs. `hitTier` is **non-monotonic**, and this is now a population-level finding, not a single-outlier artifact: pooled avg-by-tier `[7.65, 14.76, 15.85, 12.42]` (tiers 0–3) rises then drops at tier 3. Only 17/74 (23.0%) characters show an individually monotonic non-decreasing trend; 55/74 (74.3%) are non-monotonic. **This reverses round 1's own "excluding `bl_b_01` restores monotonicity" correction** — that fix does not survive full-roster data. | **PLAUSIBLE** |
| 5 | Round 1's "`projectileId=-32` is a single fixed sentinel" hypothesis is **REFUTED** at full scale: 47/2047 (2.30%) battle entries have nonzero `projectileId`, spanning **15 distinct values** (`-34,-32,-31,-30,-28,-26,-25,-24,-23,-22,-20,-19,-18,18,36`); support files show **25 distinct nonzero values** at a 10x higher rate (172/747 = 23.03%). Far more consistent with a real per-projectile-type id/enum than a boolean-like sentinel. | **SPECULATIVE** *(was PLAUSIBLE; refuted by scale)* |
| 6 | Round 1's "`collisionType=4` necessary-but-not-sufficient for nonzero `projectileId`" framing is **REFUTED**: of 47 nonzero-`projectileId` entries, only 35/47 (74.5%) have `collisionType=4` — the real rule is **`collisionType ∈ {4,5}`, covering 46/47 (97.87%)**. 8/47 (17%) nonzero-`projectileId` entries are themselves `isTerminator=True` rows. | **SPECULATIVE** *(was PLAUSIBLE; the "4-only" framing is wrong — real rule is the {4,5} union)* |
| 7 | `hitProperties` per-character constancy holds for a majority (48/74 = 64.86%) but is **not** "near-perfectly file-constant" as round 1's sample suggested — 26/74 (35.1%) characters mix 2–3 distinct values within their own file. A previously-unseen bit (`hitProperties=5`, bit2 set) and bit1-without-bit0 (23/2047 entries) both appear, contradicting round 1's "only two bits, bit1 never alone" read. | **PLAUSIBLE** |
| 8 | The round-1 "two nonzero-`projectileId` entries have opposite `hitProperties`" observation was **n=2 noise**: at full scale (n=47), `hitProperties=1` dominates the nonzero-`projectileId` subset at 68.09% — more than double its ROM-wide baseline rate of 29.26% — suggesting bit0 (`0x1`) alone is enriched among projectile-flagged hitboxes. | **PLAUSIBLE** *(same claim slot as round 1; conclusion reversed)* |
| 9 | `damageFlags==0` is common but **not** a clean majority at scale: pooled 872/1861 = **46.86%** (round 1: 57.1%), essentially a coin flip. Per-character variance is extreme (`bu_b_01`/`sk_b_01` are 0% zero; only 1/74 characters is 100% zero). | **CONFIRMED_STATIC** |
| 10 | `hitModifier` is **NOT** constant at 0 — this directly **supersedes and breaks round 1's CONFIRMED_STATIC claim**. 9/2047 (0.44%) battle entries are nonzero (`{2,6,18,20,25,34}` across 5 characters (bl_b_03, db_b_07, op_b_03, sk_b_02, tr_b_01)); corroborated cross-population by independent nonzero values in `item_collision.json` (`30`) and support files (`{10,15,20}`). | **CONFIRMED_STATIC** |
| 11 | `isTerminator` does **not** follow "exactly one terminator row per file" — the per-file histogram spans 0–36 terminators (27/74 files have zero; `kn_b_01` has 36 of its own 60 entries). Strongly suggests `isTerminator` delimits **per-move hitbox sub-lists**, not end-of-file. The round-1 "sentinel values" read (`damageFlags=255`, `knockback=255`) is only a majority pattern at scale (62.4% of terminator rows carry both). | **PLAUSIBLE** |
| 12 | Support files (`*_s_*`, n=206) diverge from battle files on every re-tested axis, generally with *more* variance and a stronger projectile-related signal (10x higher nonzero-`projectileId` rate: 23.03% vs. 2.30%); `damageFlags==0` rate is nearly identical between populations (43.4% vs. 46.9%). | **PLAUSIBLE** *(was CONFIRMED_STATIC; capped by data-consistency lens: UNSURE)* |
| 13 | Core structural/schema facts from round 1 remain **exactly** true at 281-file scale: zero shared field names between collision (23-field) and jpower (20-field) schemas; `reserved0-3` uniformly `(0,0,0,0)` across all 2047 battle entries; `damageFlagsLow`/`hasSpecialFlag` bitfield decomposition has zero mismatches; exporter `count` matches `len(entries)` with zero mismatches (all 281 files). Structural *ranges* widened substantially at scale (`durationMult` now spans 12 values incl. `120`; `extFlags` nonzero on 5.23% of entries). | **CONFIRMED_STATIC** |

### Refuted hypotheses (collision-data, round 2)

- **`projectileId=-32` fixed sentinel** — refuted; 15 distinct nonzero values in battle files alone (25 in support). The single most consequential round-1→round-2 break in the whole campaign.
- **`collisionType=4` necessary for nonzero `projectileId`** — refuted; real rule is the `{4,5}` union (97.87% coverage), not `4` alone.
- **`collisionType=5 → hitTier=3` and `collisionType=3 → hitTier=1` as "strong predictors"** — both weakened to near-coin-flip at full scale (47.58% / 58.98% pooled) with substantial per-character inconsistency. Demoted PLAUSIBLE → SPECULATIVE.
- **`hitModifier` constant at 0** — refuted; 9/2047 nonzero entries across 5 characters (bl_b_03, db_b_07, op_b_03, sk_b_02, tr_b_01), corroborated by nonzero values in the item and support populations. A rare case in this campaign of full-scale data breaking, not just weakening, a round-1 CONFIRMED_STATIC finding.
- **`isTerminator` = exactly one row per file** — refuted; histogram spans 0–36 per file, consistent with per-move sub-list delimiters rather than an end-of-file sentinel.
- **`damageFlags==0` as a clean majority** — softened from round 1's 57.1% to a near-coin-flip 46.86% at scale; still the single most common value, but not "the majority case" as previously framed.
- **Round 1's own "knockback rises monotonically once `bl_b_01` is excluded" correction** — does **not** survive full-roster data: 74.3% of characters are individually non-monotonic in their own avg-knockback-by-tier sequence. The non-monotonic finding round 1 originally reported (before its own "fix") is closer to correct at population scale.

### Open questions (collision-data, round 2)

- The `isTerminator` per-move-sub-list-boundary hypothesis (histogram 0–36/file, correlated with total entry count) is untested against `jpower`'s per-character block count — if segment count matches jpower block size for several characters, that is the still-missing collision↔jpower join key.
- `projectileId`'s 15 (battle) / 25 (support) distinct nonzero values, clustered in a `-18..-34` band with rare positive outliers (`18`, `36`), are a strong candidate for a real lookup/enum table — a disassembly trace (not attempted this data-only round) of the code that *reads* `projectileId`/`hitModifier`/`hitProperties` is now higher-value than before, since concrete nonzero instances exist to set breakpoints on (see `GDB-Validation-Queue.md`).
- The support-file `projectileId` rate being ~10x the battle rate is the strongest lead for "support characters are structurally implemented as projectiles" — untested against `docs/research/Character-Mapping.md`'s per-character support descriptions.
- `hitModifier`'s newly-confirmed nonzero values (`bl_b_03`, `db_b_07`, `op_b_03`, `sk_b_02`, `tr_b_01`, plus item/support) and `hitProperties`'s newly-observed bit2/bit-without-bit0 cases are both concrete, addressable GDB targets now (previously under-sampled at n=4).

---

## Subsystem: guard-sp-gauges

**Status:** PARTIAL (2 confirmed / 11 plausible / 1 speculative; 14 claims, 3-lens verified). **New this phase — Phase-0 spec B12.** Goal: find guard-health/SP-gauge instances of the CONFIRMED HP clamp-accumulator (cross-cutting §2) at a base offset other than `+0x56c`. **Headline result: no second *fixed* offset exists** — all 8 trampoline call sites and the 1 direct walker call into `Grow`/`0x02078488`, plus the sole `GrowMax` caller, resolve to `+0x56c` or to a *dynamically-linked list node* rooted at `char+0x558`. The leading guard/SP candidate is therefore the **`+0x558` Meter-node list**, not a second fixed struct offset.

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | All 8 static call sites of the HP trampoline `0x020783CC` are enumerated and traced (1 already known from damage-pipeline; 7 new this round), all unconditional direct `bl` in ov6. | `0x02157DC0`, `0x021582C4`, `0x02158BC0`, `0x02159274`, `0x021592D0`, `0x0215952C`, `0x02159668`, `0x0215A318` | **CONFIRMED_STATIC** |
| 2 | Call site `0x02157DC0` sits in a ~73-case generic "apply-delta-by-opcode" battle-event dispatcher (`0x02157A44`) that reuses the same character-pointer/delta pattern across the HP trampoline, a `char+0x5c8` counter (`0x020781E4`), and the `+0x558` list walker — i.e. a generic opcode interpreter, not HP-specific plumbing. | `0x02157A44`–`0x02157E0C` | **PLAUSIBLE** |
| 3 | A structurally near-identical sibling dispatcher (`0x0215807C`) reuses the same case-ordering pattern with a different opcode selector (`r3` vs. `r2`) — a peer dispatcher, not a gauge-specific handler. | `0x0215807C`–`0x021582D4` | **PLAUSIBLE** |
| 4 | Two tiny wrapper functions (`0x02159260`/`0x021592C0`) feed the trampoline a signed halfword from `[[r1+4]+4]`, one scaled ×64 (`lsl#6`), the other unscaled, with no hard-coded sign (drain/fill is data-driven). **The aliasing lens found a third, undocumented sibling at `0x02159280` scaling the SAME field ×256 into the `char+0x5c8` counter** — reinforcing that this is a reused generic small-wrapper template, not gauge-specific code. | `0x02159260`–`0x021592D0` | **PLAUSIBLE** |
| 5 | Two more wrappers (`0x02159500`/`0x02159624`) gate the trampoline behind eligibility-check `0x0215986C`, called with codes `0x1d`(29)/`0x1b`(27); the predicate itself (`0x2158eb0`) is a generic bitmask test on `charPtr+0x120`, confirmed structureless w.r.t. gauge selection — i.e. the codes gate a battle-*effect* type, not a different gauge. | `0x02159500`–`0x0215988C` | **PLAUSIBLE** |
| 6 | Call site `0x0215A318` feeds the trampoline from scratch field `[[charPtr+0x1a8]+0x10]+0x140` with **no negation** (contrast the confirmed one-shot-hit drain at `+0xE8`, damage-pipeline claim 8) — most consistent with a passive fill/regen or DoT tick, gated by a "run once" sticky flag and an enable check at `+0xcc`. | `0x02159EF8`–`0x0215A318` | **PLAUSIBLE** |
| 7 | ~~The ONLY static caller of `Grow` (`0x02078488`) other than the trampoline is the `+0x558` walker.~~ **This enumeration is stale — see the sibling-trampoline discovery (claim 8).** | `0x020783DC`–`0x02078414` | **PLAUSIBLE** *(capped; aliasing REFUTED)* |
| 8 | **Tooling blind spot, independently demonstrated:** the trampoline `0x020783CC` reaches `Grow` via an indirect `bx ip` through an inline pool word — `xrefs-to`/`pool-values` against `0x02078488` both return **zero** literal_load hits for this demonstrably-real reference. **The aliasing lens exploited exactly this blind spot and found a second, previously undocumented trampoline at `0x020783B8`** (`ldr ip,[pc,#8] / ldr r0,[r0,#0x56c] / rsb r1,r1,#0 / bx ip`), called via `bl` from ov6 `0x0215AC70` — a genuine **DRAIN counterpart** to `0x020783CC` (same `+0x56c` target, but negates its delta first). This is the single most consequential discovery of this phase. | `0x020783CC`–`0x020783D8`; sibling `0x020783B8` | **PLAUSIBLE** *(capped; aliasing REFUTED the original "no sibling found" claim by finding one)* |
| 9 | `GrowMax` (`0x020784B8`) has exactly one static caller, `0x0215C73C`, gated on bit `0x80` of `char+0x128` and passing a fixed `+0x400` (1024) delta — the strongest candidate for the documented "max HP on respawn" passive ability (`0x07`). | `0x0215C728`–`0x0215C73C` | **PLAUSIBLE** |
| 10 | Synthesis: across every call path enumerated this round, no fixed offset *other than* `+0x56c` feeds `Grow`/`GrowMax` — **this enumeration is now known to be non-exhaustive** (claim 8's discovery was missed by the original sweep), though the newly-found sibling is *also* `+0x56c`, so the substantive "no other **fixed** offset" conclusion survives with reduced confidence. | `0x020783D0`, `0x0207840C` | **PLAUSIBLE** *(aliasing UNSURE)* |
| 11 | Full body of the `+0x558` linked-list walker (`0x020783DC`): loads list head from `charPtr+0x558`, skips nodes with either of two flag gates (`node+0x40` byte, `node+0x3c` bit 0), calls `Grow(node, delta)` on unflagged nodes, advances via `node+0x0` (next-pointer). | `0x020783DC`–`0x02078424` | **CONFIRMED_STATIC** |
| 12 | The two per-node skip flags (`+0x3c`/`+0x40`) are generic enable/pause gates, **not** a type discriminator between different gauge kinds — both paths converge on the identical single `Grow` call. | `0x020783F4`–`0x02078414` | **PLAUSIBLE** |
| 13 | Exactly 2 static call sites reach the `+0x558` walker (`0x02157E0C`, `0x021592B4`) — exposed through the same generic small-wrapper infrastructure as the HP trampoline. **How many distinct gauge-node "kinds" actually populate the list at runtime cannot be determined statically** — no type-dispatch code exists anywhere in the walker or its callers. | `0x02157E04`–`0x021592B4` | **SPECULATIVE** |
| 14 | `char+0x558`/`+0x55c`/`+0x560`/`+0x564` are zero-initialized together in one startup loop (consistent with a NULL-terminated, per-character list head). Of 37 total load/store hits to immediate `0x558` ROM-wide, only **1 is a store** (the zero-init) — **no node-insertion site was found anywhere in the database** (a split `add`+register-offset store would be invisible to this immediate-based search). | `0x02075FF8`–`0x02076008` | **PLAUSIBLE** |

**P157 update** (`findings/p157-status-dispatch-table-and-hp-delta-census.md`). A 42-entry,
8-byte-stride dispatch table at ov6 `0x02171168`-`0x021712B7` names every handler in this family
from data rather than from code shape.
code shape. It **promotes claim 5 to CONFIRMED_STATIC**, reproduces all nine status mappings in
`findings/c6b-poison-burn-opcodes.md` from a different representation, and closes that finding's
open item: **status `0x20` is handled by `0x021596E0` and `0x021597F8`** (both open
`bl 0x02087724; cmp r0,#2`, which is why the prologue-shape scan missed them). The same wake
censused how `r1` is produced at all ten call sites: every scale on the path is a **constant**
power of two (`lsl #6`, `lsl #8`), so **no chain-length or other non-constant multiplier is applied
at the HP-adjust boundary** — `CONFIRMED_STATIC`. Also: `0x02078428` sets HP to **1** on every
living character when its `r1` argument is 0 (`strheq r4,[r6,#0x18]`), skipping the percentage
multiply entirely.

**P158 update** (`findings/p158-status-dispatcher-and-duration-formula.md`). The dispatcher that
drives that table is ov6 **`0x02158ED0`**`(battleObj, id)`, 532 bytes, 3 callers. It indexes two
parallel `id`-keyed stride-8 arrays — the handler table and a param array at `[[0x02172984]+4]` —
and writes `node+0x4 = &paramArray[id]` at `0x02158F18`. That is the **only writer of the
`[param+0x4]` amount, and it writes a pointer, not a value**: the signed halfword every tick and
heal handler reads is **static table data**, so `REFUTED` — chain-length damage scaling cannot live
there. Effect nodes live at `battleObj + 0x7C + slot*0x18`, two slots, slot chosen by bit `0x10` of
the param flags; `node+0x0` holds the per-frame tick handler, set to `table[id].fn` if the apply
call returned nonzero and to the stub `0x02159258` otherwise.

**First non-constant scaling formula in the campaign** (`CONFIRMED_STATIC`, `0x02158F44`-`0x02158F88`):
`duration = base + (base / 10) * (stat * 2)`, where `base` = `paramArray[id]+0x2`, `charIdx` =
`[battleObj+0x1E0]` (signed byte), and `stat` = `[[0x02172960] + charIdx*4 + 0x4C]`. It scales
**status duration, not damage**. Also `REFUTED`: P157's claim that the table's `+0x5` byte is its
key — the index is the caller's `id`; `+0x5` is a value field that happens to be a gapless
`0x00`-`0x1F` permutation. Entry `+0x4` is a **sound index** (`0x0207342C(0x7A, x)`) and `+0x6`
indexes a 16-word array at `0x02171128`.

**P159 update** (`findings/p159-effect-id-table-and-selection-routes.md`). The dispatcher's callers
are **3 functions / 5 `bl` sites** (`callers` double-counting again) — and they are the same three
functions that hold the HP-adjust sites: `0x02157A44`, `0x0215807C`, `0x02158B20`. No Thumb callers.
Two selection routes:

- **Route A**, 3 sites, all resolving to the same 26-byte translation table at ov6 `0x0217215C`:
  `id = byteTable[(u16)operand]`. Operands `0x00`-`0x10` map to `id = operand + 1`; `0x11`-`0x17` map
  to `0x23`-`0x29`; `0x18`->`0x18`, `0x19`->`0x21`. Max value `0x29` = 41, matching the table's 42
  entries exactly — a third independent confirmation that the id space is **1-41, 0 = none**.
- **Route B**, 2 sites in `0x02158B20`: `X+0x172` and `X+0x173` (signed bytes, `X =
  [[battleObj+0x1A8]+0x10]`) are **staged effect ids**, with `+0x173` stored negated. So
  `0x02158B20` is an **on-hit flush**: pending HP damage `+0xE8`, pending second gauge `+0x130`, and
  two pending effect ids.

The finding carries the **complete 42-row id table** (handler, sound byte, `+0x5`, `+0x6`, status
byte, reachable operand). Ids `0x01`-`0x11` are gauge effects with no status byte; `0x12`-`0x22` hold
every status opcode `0x19`-`0x22` and are nearly unreachable from script operands, so
`PLAUSIBLE`: statuses are inflicted via Route B while script opcodes drive gauge effects. It also
resolves P157's shifted/unshifted puzzle — `0x02159260` (x64) is ids `0x25`/`0x26`, `0x02159280`
(x256) is `0x27`-`0x29`, unshifted `0x021592C0` is id `0x04`: **different opcodes deliberately take
different units**, not an inconsistency.

**`CONFIRMED_STATIC`: the status/effect subsystem contains no chain-length scaling.** P157 (only
constant shifts on the delta), P158 (`[param+0x4]` is static table data), P159 (selection is a table
lookup and a negated byte) close it out. With C6b's result that no melee damage reaches it, the
dream-attack multiplier is **not here** — it belongs to the move/attack script system
(`move_script_location_UNKNOWN`).

**P160 update** (`findings/p160-what-0x02172960-is-and-the-thumb-literal-gap.md`). `0x02172960` is a
**pointer global with exactly two writes**, both ov6 Thumb: `0x0214CD6E` stores a **368-byte
(`0x170`)** object from the tagged allocator `0x0201A21C` (then `memset` 0 via `0x020517FC`), and
`0x0214E196` nulls it after `free` (`0x0201B244`). Liveness-tracked scanning finds **only `+0x00`**
accessed across arm9/ov6/ov11 (276 accesses, 2 stores), positive control passed. It is the first word
of ov6's BSS (`ram_size 0x25C40`, `bss_size 0x100`), and **ov11 reads it 12 times** — a deliberate
cross-overlay handle, since ov6 and ov11 occupy different windows and can be co-resident.

`REFUTED` — P158's label "per-character stat block" for `[[0x02172960] + charIdx*4 + 0x4C]`. arm9
`0x0208552C` reads the same shape and **compares the value against a character index** clamped to
`[obj+0x158]-1`, so the `+0x4C` words are small index-like integers, not magnitudes. P158's formula
`duration = base + (base/10)*(V*2)` is unchanged; only the name for `V` is retracted, and what `V`
means is `not claimed`. Known fields: `+0x4C` word array (stride 4), `+0x158` a count, `+0x15C` an
index into `+0x4C`. `PLAUSIBLE` (not claimed): the same object as the battle root behind
`0x0214D928` — **now CONFIRMED, see P161 below**; on the strength of `[root+0x158]` also being a character count, and decidable by
comparing that global's allocation size against `0x170`.

**Tool blind spot, sharpened and superseding the figure on record.** For `0x02172960`: arm9 2/2,
ov11 12/12, ov6 ARM 88/88 — all exact — but ov6 **Thumb 167 actual vs 18 recorded**, so xrefs.json
misses **149 of 167 = 89%** of Thumb pc-relative literal loads. Two independent methods agree on the
255 ov6 total (`base_offset_scan.py`'s decoder+liveness walk, and a raw `0x4800`-`0x4FFF` encoding
sweep of `ov06.bin`). The old bound was 9.4% on arm9 ARM loads; for Thumb-heavy overlay code it is an
order of magnitude worse. **Every campaign "N literal loads" count for a global Thumb code touches is
a severe floor** — including "`[0x020AFE90+0x28]`, 149 literal loads".

### Refuted hypotheses (guard-sp-gauges)

- **"The `+0x558` walker is the only other static caller of `Grow`"** (claim 7) — refuted; a second, previously undocumented drain trampoline (`0x020783B8`) exists, reached via `0x0215AC70`. It still targets `+0x56c` (not a new gauge), but the enumeration itself was incomplete.
- **The trampoline blind-spot's own "no sibling found" negative result** (claim 8) — refuted by directly performing the manual disasm-sweep the claim itself proposed; a sibling was found ~20 bytes away on the very first attempt.
- No fixed-offset second gauge exists anywhere in the enumerated call graph (claims 9–10) — this negative result **survives**, but is now known to rest on a demonstrably incomplete sweep (see above), so it is held at PLAUSIBLE rather than CONFIRMED.

### Open questions

- **Node-insertion site for `char+0x558` was never found statically** — the list head is zero-initialized once and read 36 times, but no store ever populates it with a live node pointer (candidate: a split `add rX,#0x558` + register-offset store, invisible to immediate-based `search-imm`). See `GDB-Validation-Queue.md`.
- **How many distinct node "kinds" populate the `+0x558` list** (guard? SP? both, as separate nodes? a single shared "resource" node type?) is entirely unresolved by static analysis — no type-dispatch code exists in the walker.
- **SP deck-shared vs. per-character tension:** JUS's SP gauge is documented as deck-wide (shared across a player's 3-character team), which sits awkwardly with a *per-character* `char+0x558` list model — is SP a node aliased/shared across a team's three character structs, or does each character track its own SP contribution to a shared pool elsewhere?
- Whether other `ldr ip,[pc,#N]/ldr r0,[r0,#M]/bx ip`-shaped trampolines exist elsewhere in the ROM with `M != 0x56c` (the actual guard/SP fixed-offset gauge, if one exists) remains unanswered — this phase's tooling pass did not add a byte-pattern scanner for this shape (see Tooling gaps).

---

## Subsystem: chrb-catalog

**Status:** PARTIAL (10 confirmed / 6 plausible; 16 claims, 3-lens verified). **New this phase — Phase-0 spec B14.** Goal: catalog every reference to the chr_b singleton `0x0214BD80` and build a complete record-offset map. **Headline reframe: `0x0214BD80` is not "the chr_b pointer" — it is a "battle resource manager" singleton**, of which chr_b's own record array (manager`+0x40`) is just one of roughly 15 owned tables/resources. All 97 literal_load xref hits (51 arm9, 44 ov5, 1 ov6, 1 ov11 — not the ~87 previously estimated) were classified; only 13 hit-sites touch chr_b's own array.

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | The chr_b singleton is `*(0x0214BD80)`, a global "battle resource manager." The arm9 loader (`0x02075FBC`) opens `chr_b.bin`, stores its handle at manager`+0xC`, virtual-calls `GetData`, and caches the resulting 60-byte-record array base at manager`+0x40` — the ONE place this pointer is ever established. | `0x020760F8`, `0x02076120` | **CONFIRMED_STATIC** |
| 2 | `0x02077178` reads chr_b `statA`/`statB`/`statC` (`+8`/`+0xA`/`+0xC`) as a 16-bit triple for a koma/technique **stat-requirement eligibility matcher** (equality compare, not a tier threshold) — confirms and generalizes the prior campaign's movement finding. | `0x020771A0` | **CONFIRMED_STATIC** |
| 3 | `0x020772E4` walks the per-character `+0x558` list and caches chr_b `CombatStat(idx+1)Value` into an active-move/technique struct's `+0x16`/`+0x18` fields. **Whether this cached value is later read by ov6 hit-resolution via `charPtr+0x56c` (`0x020784E4`) is the campaign's TOP OPEN DISPUTE** — see the dedicated subsection below. Capped PLAUSIBLE by the disasm-correctness lens; the aliasing lens argues the opposite. | `0x02077310` | **PLAUSIBLE** *(disputed — see below)* |
| 4 | `0x02077768` loops chr_b record offsets `+3..+7` (on-disk `CharId`+`Flags`) **one byte at a time**, each byte independently indexing the manager`+0x50` ability/passive-effect table — **not** a combined 32-bit bitmask as `chr_b.json`/the C# converter models it. Schema mismatch against the exported JSON. | `0x020777A8` | **CONFIRMED_STATIC** |
| 5 | `0x02077C0C` is the "cache chr_b fields into the live move/technique struct" routine, run at technique-setup time (0 direct `bl` callers — reached only via a per-move-type dispatch table, i.e. core simulation code). Copies FormType/Tier/KomaSize/CombatStatN(Value+Mod)/TextIds into the move struct. | `0x02077C10` | **CONFIRMED_STATIC** |
| 6 | Two leaf getters (`0x02078514` reads `BattleParams` `+0x24` as `ushort[6]`; `0x0207853C` reads the tail as `byte[]`) — the SAME 12-byte blob read with two different element sizes, consistent with the exported schema's own noted uncertainty about `BattleParams`. | `0x02078514`, `0x0207853C` | **CONFIRMED_STATIC** |
| 7 | Both `BattleParams` getters' **only** caller in the ROM is ov11 (confirmed Battle-AI via `BattleAI_*`/`BattleAIObj_*` debug strings) function `0x02174330` — chr_b's `BattleParams` field is read **LIVE**, every time, by the CPU decision-tree, not cached. | `0x021746E0`, `0x02174724` | **CONFIRMED_STATIC** |
| 8 | A family of ov5 (menu) "special form" dispatch getters (`0x0214D944`, `0x0214DC18`, `0x0214E480`) reads chr_b `FormType` (record `+0`) whenever a selector nibble `==3` — corroborates `FormType=+0` via 3 independent sites beyond the one already known. | `0x0214D95C`–`0x0214E4D0` | **CONFIRMED_STATIC** |
| 9 | Two more ov5 getters (`0x0214E238`, `0x0214E284`) belong to the same "special form" family by strong structural analogy, but the disassembly database renders the bytes immediately after the index computation as apparent Thumb-mode text (ov5 is otherwise pure ARM) — most likely a shared-tail-veneer listing artifact, not confirmed by a clean verbatim `ldrb` read. | `0x0214E258`, `0x0214E2A8` | **PLAUSIBLE** |
| 10 | The sole ov6 literal_load hit to `0x0214BD80` (`0x0215FAEC`) touches the manager's ability-table slot (`+0x50`), **never** chr_b's own `+0x40` array — every direct chr_b-singleton access inside ov6 itself touches a sibling resource. | `0x0215FAEC` | **CONFIRMED_STATIC** |
| 11 | ov6's hit-resolution function `0x02158B20` calls arm9 `0x020784E4` (`0x02158D8C`), which reads `charPtr+0x56c`'s `+0x16`/`+0x18` fields. **Whether these are "the SAME fields" `0x020772E4` writes at `+0x558` is the same TOP OPEN DISPUTE as claim 3.** Capped PLAUSIBLE (disasm-correctness REFUTED; aliasing UPHELD). | `0x02158D8C` | **PLAUSIBLE** *(disputed — see below)* |
| 12 | The lone ov11 direct literal_load hit (`0x021752B8`) reads chr_s (manager`+0x48`), not chr_b — chr_b IS consumed elsewhere in ov11 (claim 7), but only via `bl` into arm9 getters, never a direct singleton dereference inside ov11 itself. | `0x021752B8` | **CONFIRMED_STATIC** |
| 13 | **COMPLETENESS (arm9):** the remaining 43 arm9 hits all resolve to sibling manager fields (koma, kshape, chr_s, ability table, several unidentified fixed-size tables, a `+0x1000`/`+0x1900` "match config" sub-struct). **Errata: 2 rows (fn `0x0207698C`, hits `0x02076990`/`0x020769AC`) dropped a `+0x1800` term in the original catalog — the real offsets are manager`+0x18D4`/`+0x18DC`, not `+0xD4`/`+0xDC`.** | `0x0207602C`–`0x020781BC` | **PLAUSIBLE** *(disasm-correctness UNSURE — see errata)* |
| 14 | **COMPLETENESS (ov5):** the remaining 38 ov5 hits all resolve to sibling manager fields (koma-filter-list builders, three still-unidentified fixed-size tables, chr_s, kshape, assorted config bitmasks) — none touch chr_b's own array. | `0x0214D594`–`0x021536EC` | **CONFIRMED_STATIC** |
| 15 | **Complete offset→accessor→use table for the 60-byte chr_b record** (base `*(0x0214BD80)+0x40`, stride `0x3C`): `+0x00` FormType, `+0x01` Tier, `+0x02` KomaSize, `+0x03` "CharId" (actually an ability-table index — MISMATCH vs. schema), `+0x04..+0x07` "Flags" (actually 4 independent ability-ID bytes — MISMATCH vs. schema), `+0x08/0xA/0xC` statA/B/C, `+0x0E` ClassId (**no observed consumer** among all 97 hits), `+0x10..+0x22` CombatStat1-5 (value/mod pairs), `+0x24..0x2F` BattleParams[12], `+0x30..0x3B` TextIds[6] (`[0]`=name, `[1..5]`=per-technique names). **Inherits the same 2/97-row `+0x1800` errata as claim 13.** | see claims 13/1 | **PLAUSIBLE** *(disasm-correctness UNSURE — errata)* |
| 16 | Synthesis — is chr_b reachable from ov6 battle code? **Nuanced yes, via two mechanisms, one negative:** (1) NEGATIVE — no ov6 code ever loads chr_b's own array pointer directly (claim 10). (2) POSITIVE via caching — ov6 hit-resolution consumes a value cached from chr_b at technique-setup, **contingent on the disputed `+0x558`/`+0x56c` identity** (claims 3/11). (3) POSITIVE via live read — ov11 Battle-AI reads `BattleParams` live (claim 7), architecturally a different overlay from ov6. **Capped PLAUSIBLE:** leg (2) is unproven per the dispute below, so the "two mechanisms" framing overstates the case — only leg (3) is fully confirmed. | `0x02077310`, `0x02078514` | **PLAUSIBLE** *(disasm-correctness REFUTED the "two mechanisms" framing — only leg 3 stands unconditionally)* |

### TOP OPEN DISPUTE: is the `+0x558` technique-node the same object as the `+0x56c` gauge pointer? (GDB card #1)

Claims 3, 11, and 16 all hinge on one unresolved identity question, and the campaign's own two adversarial lenses land on opposite sides of it:

- **Aliasing lens says YES:** function `0x02077E70` ("activate this move as current") reads a candidate move-struct's `+0x18` field (the exact field `0x020772E4` writes from chr_b), compares it against whatever `charPtr+0x56c` currently points to, and on selection stores the candidate pointer **unmodified** into `charPtr+0x56c` (`0x02077FDC`: `str r5,[r6,#0x56c]`) — i.e. the object landing at `+0x56c` is a raw, untransformed node of the same kind walked at `+0x558`.
- **Disasm-correctness lens says NO:** independently-verified, exhaustively-traced evidence from *other* subsystems contradicts this. `damage-pipeline` (GDB-proven) and `guard-sp-gauges` (exhaustive 8-site trampoline enumeration, this phase) establish `0x020784E4`'s `charPtr+0x56c` as a **fixed, single "HP/jpower gauge" pointer** with its own dedicated, fully-enumerated call graph that never intersects `0x020772E4`/`0x02077C0C`. `guard-sp-gauges` also found `+0x558`'s list head has exactly **one** static store (a zero-init) ROM-wide, and its walker (`0x020783DC`) is reached by only **2** call sites — a disjoint caller-graph footprint from the trampoline's **8** sites feeding `+0x56c`. Two structurally and causally distinct objects, by this reading.

Both readings survived their own lens's cross-examination. **This is deliberately left unresolved in the canon docs** — claims 3/11/16 are capped PLAUSIBLE rather than picking a side. **One GDB breakpoint settles it:** break `0x020784E4` (or `0x02077E70`) and compare the pointer value landing in `charPtr+0x56c` against the `+0x558`-rooted node addresses being walked/written elsewhere in the same session. See `GDB-Validation-Queue.md` card #1.

### Refuted hypotheses (chrb-catalog)

- **The "two mechanisms feed ov6 from chr_b" synthesis (claim 16)** — the caching mechanism (leg 2) is not proven; only the live-AI-read mechanism (leg 3, ov11) is unconditionally confirmed.
- The catalog's `0x0207698C` rows (`0x02076990`/`0x020769AC`) are corrected: real manager offsets are `+0x18D4`/`+0x18DC`, not `+0xD4`/`+0xDC` (a dropped `+0x1800` term in the original pass).

### Open questions

- **The `+0x558`/`+0x56c` identity dispute (above) is the single highest-leverage open item from this phase** — one breakpoint resolves 3 claims (3/11/16) at once.
- Where/how is `ClassId` (`+0x0E`) consumed, if at all? No instruction among the 97 direct xrefs to `0x0214BD80` reads it.
- Is the `CharId`/`Flags`-as-5-ability-index reinterpretation (offsets `+3..+7`) intentional design? If confirmed via GDB, `chr_b.json`'s exported schema should be revised from a single `flags` u32 to 5 named byte fields.

---

## Cross-Cutting Structures

These structures were discovered piecemeal across multiple subsystem tracers above; they are consolidated here because several open questions in *different* subsystems turn out to be the **same** open question about the **same** object.

### 1. Character wrapper (`sl`) — identity ambiguity (highest-leverage open item)

Damage-pipeline, physics-writers, hitstun-timers, and weight-hunt **each independently** hit the same unresolved question this campaign: is the object referred to as `sl`/`charPtr`/`scratch` in ov6's hit-resolution code (`0x02158B20`) the *same* object as the GDB-verified character struct (rooted at pointer chain `0x023D2A74`), or is it one (or more) pointer indirections away? Static `xrefs-to`/`pool-values` on the literal `0x023D2A74` return **zero hits ROM-wide** (it is a heap/runtime-only address, invisible to static search), so this cannot be resolved without a live session. This is the campaign's single highest-leverage unresolved item — see next-campaign spec **B10**.

Known fields on whichever object this turns out to be:

- **`+0x1a4`** — hit-tally (confirmed consumer: projectile-entities' spawn dispatcher `0x021574CC`; also the object hosting physics-writers' `+0x6A` "track-minimum + saturating counter", `0x021607C0`).
- **`+0x1a8`** — ~~MoveInfo~~ **battle-character** pointer. Allocated via `0x02156A38`/`0x02156A58` (size `0x1F0` = 496 bytes); installed via setter `0x021570EC`. **(iteration 73: the call-site allocation tag reads `Battle_CharaCreate` / `BattleChara.cpp`, so the `0x1F0` object is the battle character. **Iteration 74 corrects iteration 73's direction:** setter `0x021570EC` is a *callback*, its `arg1` is the character, and what lands at `character+0x1a8` is the **pooled entity** from claim 1's constructor `0x020834D4` (`blx ip` at `0x02083528`). There is no outer object; the entity holds a back-pointer to the character at `entity+0x30`. The NoteTrack is at `entity+0x18`. The `+0x56c` gauge belongs to a separate arm9 struct. See `findings/character-entity-link-and-a-reversed-setter.md`.)**
  - MoveInfo's own **`+0x10`** field → a scratch sub-object: **`+0x40`** = flags (bit `0x800` gates delta application), **`+0xE8`**/**`+0x130`** = two already-computed signed 32-bit deltas consumed by damage-pipeline's hit-resolution code. The writer of `+0xE8`/`+0x130` was never located across 3 rounds — see spec **B11**.
- **`+0x56c`** — the gauge/Meter struct pointer (see below). This field is confirmed to belong directly to the character struct itself (used by the GDB seed-anchor function `0x020784E4`), so it is **not** subject to the same "sl vs. character struct" ambiguity as `+0x1a4`/`+0x1a8`/`+0x1b4`.

### 2. Gauge / Meter struct

`char+0x56c` → `{+0x16 max (u16), +0x18 current (u16)}`. Accessors: `0x02078488` = `ApplyDeltaToCurrent` (clamped add, `[0, max]`); `0x020784B8` = `GrowMax` (capped at `0x4000`; sole caller `0x0215C73C`, gated on a `char+0x128` badge bit — candidate "max HP on respawn" passive ability `0x07`); `0x020784E4` = `IsCurrentBelowPercentOfMax` (the GDB seed anchor; both known callers pass `pct=25`). Trampoline `0x020783CC` tail-jumps into `0x02078488` with `r0` pre-loaded from `+0x56c`; **all 8 of its call sites are now traced** (spec **B12**, Phase-0 — see § guard-sp-gauges). **A previously-invisible sibling *drain* trampoline exists at `0x020783B8`** (same `+0x56c` target, negates its delta via `rsb` first) — found only because the aliasing verification lens manually swept the bytes adjacent to the known trampoline; both trampolines' pool-word jump targets are invisible to `xrefs-to`/`pool-values` (a demonstrated tooling blind spot for `bx ip`-style indirection). A `+0x558`-rooted linked list (walked by `0x020783DC`, full body now CONFIRMED) is the leading candidate for guard-health/SP: **no second *fixed* struct offset exists anywhere in the enumerated call graph** — every found path feeds either `+0x56c` directly or a dynamically-linked node reachable via `+0x558`. Whether `+0x558` nodes and `+0x56c`'s pointer are ever the *same* object is the campaign's top open dispute — see § chrb-catalog. See § guard-sp-gauges for full detail (spec **B12**, now DONE).

### 3. chr_b singleton

`*(0x0214BD80)+0x40`, record stride `0x3C` (60 bytes, matching on-disk `BattleCharacterEntry`). **Reframed this phase (spec B14): `0x0214BD80` is a "battle resource manager" singleton, of which chr_b's own array is one of roughly 15 owned tables/resources** (koma at `+0x30`/`+0x34`, kshape `+0x38`, chr_s `+0x48`, an ability/passive-effect lookup table `+0x50`, three still-unidentified fixed-size tables at `+0x44`/`+0x4C`/`+0x54`, a `+0x1000`/`+0x1900` "match config" sub-struct, and more). `statA`/`statB`/`statC` at record `+8`/`+0xA`/`+0xC`. Indexed by `charStruct+0x41` = the koma's `PassiveIndex` (0–55), not confirmed identical to chr_b's own on-disk `CharId`. **The full 60-byte record map is now complete** (all 97 xref hits classified) — see § chrb-catalog for the complete offset table, the `CharId`/`Flags`-as-ability-index schema mismatch, and the unresolved `+0x558`/`+0x56c` identity dispute (spec **B14**, now DONE).

### 4. Entity pool

Global manager singleton at literal `0x0214BE14` (a RAM-only address, unresolvable statically). `alloc = 0x020834D4` (checks manager`+0x14` free-list head, invokes a caller-supplied ctor callback, populates `entity+0x30`); `free = 0x02083648` (sets `entity+0x2c` bit 0 dead flag, calls `entity+0x10` on-destroy hook, moves the entity from manager`+0xc` active list to manager`+0x1c` pending list). A second, ov6-local manager (literal `0x02172990`) layers battle-specific bookkeeping on top.

### 5. Division primitive

`0x0200D12C`: generic signed long-division subroutine (sign-normalize via `eor`/`rsb`, shift-count ladder, unrolled subtract-and-shift table). Confirmed call sites use divisors: `100` (damage-pipeline's 25%-threshold check), `10` (weight-hunt's hitstun-duration scaling), and — unrelated to combat — `13`, `7`, and `5`-for-menu-grid-layout (multiple ov5 sites). **Never found used with divisor `5` anywhere near any combat structure** — the documented damage formula's ÷5 term has no confirmed runtime implementation anywhere in the ROM (see jpower-indirect's "all damage1 values are multiples of 5" lens extra for the likely explanation).

### 6. Status-effect / hitstun-duration manager

`ov6 0x02158ED0`. Formula: **`newDuration = floor(duration/10) × [table+0x4c] × 2 + duration`** (division via `0x0200D12C`; table-value doubling via `lsl#1`; combined via a single `mla`). Table index = signed byte at object `+0x1e0` (double-indirected via `sb+0x100+0xe0`) — a **transient** "current hit-type/element" field, **not** a per-character weight constant (write site never found). Sibling table offsets `+0x4e`/`+0x50` are candidate knockback-magnitude tables, unexplored.

### 7. 74-entry char-ID table

`0x020924B0`, 8-byte stride `{ASCII char-ID C-string, packed word}`. Consumed by the arm9 loader `0x02074728` (`lsl#3`-indexed) and by ov0's `0x0214EFAC` (linear 74-entry scan against a 6-bit id in `word1` bits 14–19 — this id does **not** match chr_b's `classId` range, and its true purpose is unresolved; the one traced consumer builds an ending-credits/sprite-archive key, not a collision-file key).

---

## Next-Campaign Queue

Summarized from `jus_files/analysis/findings/critic.round1.json` — a dedicated critic pass over the full campaign, run once the 9 tracer subsystems above completed their first round.

### Coverage gaps (never traced by any B1–B9 tracer)

| Area | Status | Why it matters |
|------|--------|-----------------|
| Guard/block | **PARTIAL (Phase-0, spec B12 — DONE)** | The CONFIRMED clamp-accumulator gauge (cross-cutting §2) has no second *fixed* offset; leading candidate is the `+0x558` dynamic Meter-node list. Node-kind census and the node-insertion site remain unfound statically. See § guard-sp-gauges. |
| SP gauge & specials | **PARTIAL (Phase-0, spec B12 — DONE)** | Same `+0x558` list candidate as guard/block; unresolved tension with SP being documented as deck-shared rather than per-character. See § guard-sp-gauges open questions. |
| Throws/grabs | never traced | `hasSpecialFlag`/`hitProperties` bit-fields (collision-data claims 9–10) are candidate markers; their disassembly consumer was never found. |
| Support koma attacks | never traced | Unknown whether support-koma attacks share the main fighter's damage/hitstun/physics pipeline. |
| Character switch mechanics | never traced | Unknown whether switching re-runs chr_b dispatch-cache setup or swaps between pre-built slot objects. |
| Combo scaling | never traced as such | Closest candidate is damage-pipeline's refuted-label ×1.20 scale (claim 9) — arithmetic real, purpose unresolved; the flag-reset site was never searched. |
| Ring-out/stage boundaries | existence itself unconfirmed | Zero mentions in any behavioral-testing doc; may not exist as a JUS mechanic (panel-based stages, not Smash-style). Deliberately deprioritized — no dedicated spec issued. |

### Next tracer specs (B10–B16, priority order)

| ID | Subsystem | Priority | One-line goal |
|----|-----------|----------|----------------|
| **B10** | cross-cutting object-identity | 1 | Build a forward call-graph provenance map so ONE future GDB session (see cross-cutting §1) settles the `sl`-vs-character-struct identity for damage-pipeline, physics-writers, hitstun-timers, and weight-hunt at once. |
| **B11** | damage-pipeline / hitbox-priority | 1 | Trace forward from the CONFIRMED MoveInfo allocator to find the writer of scratch `+0xE8`/`+0x130` — the actual damage-formula site, unfound across 3 rounds. |
| **B12** | guard/block, SP gauge | 1 | **DONE (Phase-0).** All 8 trampoline sites + 1 previously-invisible sibling drain trampoline traced; no second fixed offset found; the `+0x558` Meter-node list is the leading candidate. See § guard-sp-gauges. |
| **B13** | throws/grabs | 2 | Once B11 locates the runtime field offsets, manually read disasm around `hasSpecialFlag`/`hitProperties` bit tests (search-imm cannot find data-processing immediates — a confirmed tooling gap, partially closed this phase by `search-op-imm`) for a branch that skips normal knockback in favor of a scripted throw outcome. |
| **B14** | weight-hunt (completion) / chr_b catalog | 2 | **DONE (Phase-0).** All 97 xref hits to `0x0214BD80` classified; complete 60-byte record map built; singleton reframed as a "battle resource manager" owning ~15 tables. See § chrb-catalog. |
| **B15** | support koma / character switch | 2 | Confirm the character constructor's actual caller set (9× reported from `ov8:0x02150392`) and check whether any call path is switch-specific. |
| **B16** | combo scaling | 3 | Find the writer that clears `[sl+0xf8]` (only the *set* site is known) and check for an adjacent hit-count field — a pure boolean cannot express per-hit-number scaling. |

### GDB-first recommendations (from the critic; see `GDB-Validation-Queue.md` for full cards)

1. **Identity check** — break `ov6 0x02158BA8`; compare `r1` against the live `0x023D2A74` pointer chain. Unblocks 4 subsystems at once (cross-cutting §1 / spec B10).
2. **Hitstun-timer init** — break `arm9 0x0207D16C`; confirm/deny against a real hit-landing.
3. **Position-vs-timer conflict** — break `ov4 0x02151E7C`; resolves the pre-existing `+0xA0` conflict in `Character-State-Struct.md`.
4. **Velocity/position fields** — break `ov6 0x02158BB4`/`0x02158BC4`; dump the full `+0x6A`–`0xBA` window of `[sl+0x1b4]` around a real hit.
5. **Combo-scale flag scope** — break `arm9/ov6 0x02158DC4`; watch `[sl+0xf8]` across a full combo and a match reset (can piggyback on recommendation #1's session).

### Tooling gaps (block future static rounds)

- `search-imm` finds load/store immediate *offsets* only — cannot find data-processing immediate *operands* (`mov`/`cmp`/`tst`/`and #imm`). **Partially closed this phase (P6a):** `query.py search-op-imm <val>` was added (deterministic, covered by the tool's self-test), but B13 (throws/grabs) itself was not re-attempted with it this phase.
- No register-provenance-aware search exists — only bare immediate-offset text matching, the single biggest false-positive source this campaign (hit at least 3 times independently: hitstun-timers ×2, physics-writers ×1).
- The jpower-indirect div-by-5 sweep used a fixed ARM-only 8-byte lookback and cannot verify it isn't missing a Thumb-mode call site.
- `arm9_tables.json`'s candidate ~74-entry/vtable tables were found by ROM file offset but never translated to RAM addresses. **Partially closed this phase (P6b):** `arm9_tables_ram.json` was written (842 rows, offsets + scan ranges translated); 3 `xrefs-to` smoke tests against candidate entries were clean (0 hits each) — meaning the candidates remain unverified guesses, not confirmed tables, but the translation plumbing now exists for a future pass.
- `disasm_db`'s `bx <reg>`-epilogue function-boundary heuristic still has a known gap (merged two routines once, per the prior campaign's weight-hunt section). **Not attempted this phase (P6c skipped):** regenerating the disasm/xref DBs was judged too risky pre-synthesis, since every frozen evidence DB this phase's tracers cited would have needed re-verification.
- **New this phase:** `xrefs-to`/`pool-values` cannot see `bx ip`-style indirect jumps through an inline pool word — demonstrated concretely by guard-sp-gauges' sibling drain trampoline `0x020783B8`, which was invisible to both tools and was only found by a manual disasm sweep of the bytes adjacent to the known trampoline `0x020783CC`. No byte-pattern scanner for this `ldr ip,[pc,#N]/ldr r0,[r0,#M]/bx ip` shape was added this phase.
- `ExportAllCollisions` (the CLI's own batch export command) had never been run against the full roster — **closed this phase (P1):** it now has, and P2 re-mined the full 281-file export (see collision-data round 2).

---

## Subsystem: rule / match settings (P163–P165)

**Status:** PARTIAL. Consolidated here because P163–P164 landed only in `findings/`. Full detail:
`findings/p163-rule-select-screen-mapped-to-memory.md`,
`findings/p164-mode-classifier-is-ov1-and-reads-a-16-byte-table.md`,
`findings/p165-mode-table-is-rulemess-bin.md`.

| what | where | confidence |
|---|---|---|
| Match-settings struct (the ルールセレクト screen, six settings + three booleans) | `0x020AFE90` | `CONFIRMED_STATIC` |
| Rule mode, index into the rulemess table (`0` = ポイントバトル, `1` = デスマッチ, `2` = J-symbols) | `0x020AFEA0` | **`CROSS_CONFIRMED`** (runtime: bead `jus-1g6`) |
| Time limit, in frames | `0x020AFEAC` (settings `+0x1C`) | **`CROSS_CONFIRMED`** (4463 measured at じかん 30) |
| Team battle boolean — **not** cleared by the runtime harness's `rules_off()` | `0x020AFEBD` | `PLAUSIBLE` |
| COM count | `0x020AFEC3` | `PLAUSIBLE` (untested) |
| Menu-side settings record, array stride `0xA4` (164 bytes) | source object of `0x0207538C` | `CONFIRMED_STATIC` |
| Settings `+0x4C` = slot index, or `-1` (**not** `root+0x4C`) | `0x020AFEDC` | `CONFIRMED_STATIC` |
| Mode classifier: `mode_field(ctx, mode) = [[ctx+4] + mode*0x10 + 0xC]` | ov1 `0x0216446C` | `CONFIRMED_STATIC` |
| `ctx` builder = `RuleData_Create`; `[ctx+4]` is the data pointer for `bin/rulemess.bin` | ov1 `0x021643A4` | `CONFIRMED_STATIC` |
| The mode descriptor table is the 22-entry × 16-byte header of `bin/rulemess.bin`; the classifier's field is its `+0xC` int | `jus_files/ripped_jus_files/bin/rulemess.bin` | `CONFIRMED_STATIC` |
| Time conversion: `+0xC == 1` (mission rules) → `じかん * 60`; otherwise (versus rules) → `(じかん + 1) * 144 - 1` | ov1, per P163 | **`CROSS_CONFIRMED`** |

`not claimed`: why the constant is `144`, and why the `-1`. Needs one wall-clock measurement.

**Format correction with campaign-wide reach.** Pointers in the JUS `bin/*.bin` text files are
**self-relative** — a pointer's target is its own file position plus its value — not absolute, as
`docs/articles/specs/texts.md` says. Verified on 1,347 of 1,347 pointers across six files and against
`src/JUS.Tool/Texts/JusText.cs:90`. Read as absolute, only the first pointer in a file lands on a
string. Any hand-parse of these files from the old description produces garbage after string one.

### Per-mode rule handlers (P166)

`findings/p166-per-mode-handler-table.md`.

| what | where | confidence |
|---|---|---|
| Per-mode handler table: **31 records × 12 bytes**, three Thumb function pointers each | ov6 `0x02170EAC` | `CONFIRMED_STATIC` |
| Indexing: `handler = [0x02170EB0 + mode*12]`, then `[root+0x00] = handler` and `[root+0xC8] = 1` | ov6 Thumb `0x0214F91C` | `CONFIRMED_STATIC` (Codex-checked independently) |
| Column accessors: `+0x0` called at `0x0214F872`, `+0x4` installed at `0x0214F91C`, `+0x8` called in a loop at `0x0214F95A` | pools `0x02170EAC` / `0x02170EB0` / `0x02170EB4` | `CONFIRMED_STATIC` |
| `root+0x08` = the rule mode (word); the index into the table | via `0x0214F91C` | `CONFIRMED_STATIC` |
| `root+0xC8` = byte flag: `1` = per-mode handler installed, `0` = the fixed default `0x02150F65` (sibling `0x0214F93C`) | via `0x0214F91C` / `0x0214F93C` | `CONFIRMED_STATIC` |
| Twelve poked modes (0,1,2,3,4,5,7,9,16,17,19,21) each land at their own table index | runtime `jus-hsc` / `jus-wbo` | **`CROSS_CONFIRMED`** |
| Byte-identical records: `(9,22)`, `(16,30)`, `(25,28)` — nothing else repeats | ov6 `0x02170EAC` | `CONFIRMED_STATIC` |
| `root+0x08` is **not** a copy of `0x020AFEA0`: the training path runs table entry 8 with the settings byte at 0 | runtime `jus-wbo` | **`CROSS_CONFIRMED`** |
| `root+0x08` read directly across 5 paths: battle path is **identity** (`0→0`, `1→1`, `2→2`, `12→12`); only training substitutes (`0→8`) | runtime `jus-j1k` | **`CROSS_CONFIRMED`** |
| `root+0xC8` observed `0` at mode 12 with `root+0x000` = `0x02150F65`, the default handler named statically beforehand | runtime `jus-j1k` | **`CROSS_CONFIRMED`** |
| **31 records — decomposed.** Lower bound ≥ 31: index 30 installs its own exact table entry (`0x021508F1`) in live RAM → **`CROSS_CONFIRMED`**. Upper bound = 31: the odd-pointer run ends at `0x02171020`, and the next words are packed data (`0x00300078`, `0x00A800C0`) → `CONFIRMED_STATIC` | ov6 `0x02170EAC` / runtime `jus-gpx` | see cells |
| ~~The gate refusing 31 and 40 confirms the record count~~ — **RETRACTED, my over-claim.** At runtime, in-range mode 12 and out-of-range 31/40 are *indistinguishable*: all three sit permanently at default + flag 0. So a non-install cannot be read as "rejected for range" | runtime `jus-gpx` | `RETRACTED` |
| Handler sharing visible in live RAM: 22 = 9 (`0x02150469`), 25 = 28 (`0x0215057D`), 30 = 16 (`0x021508F1`) | runtime `jus-gpx` | **`CROSS_CONFIRMED`** |
| `root+0x08` identity across ten poked modes (0,1,2,12,22,25,28,30,31,40); only the training path substitutes (`0→8`) | runtime `jus-j1k` / `jus-gpx` | **`CROSS_CONFIRMED`** |
| The installer `0x0214F91C` is gated, and **the gate is not a bound check alone**: 31/40 are rejected for range, but mode 12 is *in* range and still gets the default, while 22/25/28/30 install fine | ov6 | `not claimed` |
| ~~Mode 12's install happened and was reverted~~ — **REFUTED** by runtime `jus-gpx`. Sampling every ~60 frames from object creation shows the order is `memset` → **default with flag 0** → per-mode with flag 1. The default is the *initial state*, not a fallback, so flag 0 at rest means the install step never ran. Mode 12's flag is never 1, so there is no `1→0` transition. Positive control: mode 2's `0→1` upgrade was caught at the same resolution | runtime `jus-gpx` | `REFUTED` |
| **Timing trap:** for ~160 frames after object creation (fc 4044→4204 for mode 2) a mode that installs perfectly reads flag 0 with the default. A single flag-0 observation proves nothing unless shown to persist | runtime `jus-gpx` | `CONFIRMED_RUNTIME` |
| What actually stops mode 12's install is `not claimed`. The bound is **not** at 22 — 22/25/28/30 all install despite sitting above rulemess's 22 described entries. That half of the argument stands; the runtime-signature half does not | ov6 | `not claimed` |

`REFUTED` (mine, same wake it was filed): rulemess text-duplicate entries do **not** share handler code.
`not claimed`: whether they behave identically in play, and whether the ov1 rulemess index and this ov6
index share one space for modes ≥ 3. 31 handler slots vs 22 described modes; modes 18 and 20 build no
battle object at all.

**Instrument rule adopted from the runtime loop (`jus-acq`).** "The anchor is non-zero" does not mean
"the object is populated" — a freshly `memset` battle root reads all-zero and fills in by roughly +300
frames, confirmed by running a known-good index through the same early-break protocol. Early all-zero
reads must never be interpreted.

Checked against the one finding it could have dissolved: `root+0x4C..+0x6C` reading all-zero is **not**
an early-read artifact, because sibling fields in the same dumps were populated (`+0x10C` and `+0x110`
held main-RAM pointers, `+0x158` held the correct character count, `+0x000` held a live per-mode
handler). A freshly-`memset` object cannot show those. The zeros are real, so term `V` stays
`SPECULATIVE` for the reason already recorded and not for this new one.

### The installer's caller and the gate (P167)

`findings/p167-installer-caller-and-the-bss-gate.md`.

| what | where | confidence |
|---|---|---|
| The installer `0x0214F91C` has **exactly one** `BL` caller, and the call is **unconditional** | ov6 `0x0214DA58` | `CONFIRMED_STATIC` (exhaustive Thumb `BL` scan of `ov06.bin`) |
| `r0` at the installer is `[0x02172960]` — the battle root. So `root+0x08` / `root+0xC8` are fields of the anchor's pointee | pool `0x0214DA9C` / runtime `jus-usf` (`lr` = `0x0214DA5D`, `r0` = `0x021DEA60`) | **`CROSS_CONFIRMED`** |
| Live return address `0x0214DA5C` = `0x0214DA58 + 4`, matching the statically scanned call site from the opposite direction | runtime `jus-usf` | **`CROSS_CONFIRMED`** |
| The byte at `0x0217296D` (ov6 BSS, 13 bytes past the root global) gates that path: zero → the install path is skipped (`0x0214DB24`–`0x0214DB2A`) | ov6, pool `0x0214DB54` | `CONFIRMED_STATIC` (Codex-checked independently) |
| It is a **poll**, not a one-shot check — 114 hits in a mode-2 battle, byte `0` on 113 and `1` on the 114th, with the installer firing immediately after | runtime `jus-2cu` | **`CONFIRMED_RUNTIME`** |
| ~~`0x0217296D` is the mode-12 discriminator~~ — **NOT the gate.** The rest-state read splits cleanly (1 for modes 0/1/2, 0 for mode 12) and looks causal, but the check **never runs at all** for mode 12, so its `0` is a consequence. The gate is higher | runtime `jus-2cu` | `REFUTED as the discriminator` |
| The poll is a **registered callback**, not an ov6 call: arm9 `0x02028620` does `ldr r1,[r4,#0x40]` / `blx r1`, and the runtime `lr` `0x02028628` is the `pop` after it | arm9 + runtime `jus-2cu` | `CONFIRMED_STATIC` |
| ~~`r4` = `r0` = `0x023DDE58`~~ — **RETRACTED, my decode error.** `mov r0, r4` at `0x02028614` is followed by `bl 0x0201B45C` at `0x0202861C`, which clobbers `r0` with its return value before the `blx`. So `r0` at the callback is that return, *not* `r4`. Runtime: `r4` = `0x023DAC68`, `r0` = `0x023DDE58` | arm9 `0x020285F8`–`0x02028628` / runtime `jus-rpl` | `RETRACTED` |
| The dispatcher **re-reads** the slot after that `bl` (`0x02028608` then again `0x02028620`), and compares the first read against a literal sentinel before branching. So the callee of `0x0201B45C` can change the slot | arm9 | `CONFIRMED_STATIC` |
| **Registration object `0x023DAC68`**, slot `+0x40`, is a **three-state machine**: `0x0214DAA5` → `0x0214DB21` (the poll) → `0x0214DBCD`. `root+0xC8` becomes `1` at the third state | runtime `jus-rpl` | **`CONFIRMED_RUNTIME`** |
| **Mode 12 never advances past state 1**, so the decision lives inside `0x0214DAA4` — the function holding pool `0x0214DABC`, which would otherwise write `0x0214DB21` into the slot | runtime `jus-rpl` | **`CONFIRMED_RUNTIME`**; the condition itself is `not claimed` |
| `root+0x144` = the object passed to the callback as `r0` (`0x023DDE58`), derived and verified rather than assumed | runtime `jus-rpl` | **`CONFIRMED_RUNTIME`** |
| `0x023DAC68` (the registration object) has **no derivation** — it appears nowhere in the `0x170` root, so it is not reachable from `[0x02172960]`. Session-local until a static writer is found | runtime `jus-rpl` | `not claimed` |
| The slot address `0x023DACA8` (= `0x023DAC68 + 0x40`) recovered **from the value side** — a blind 4 MB scan for state 3 `0x0214DBCD` returns exactly one non-code hit, at that address, matching the address obtained from `r4` under GDB | runtime `jus-p168` bonus | **`CROSS_CONFIRMED`** (two unrelated methods) |
| Sentinel `0x0202836C` occurs 363 times word-aligned across RAM, many in heap objects well above the overlay windows — the shape of a default idle callback stored into hundreds of live objects | runtime | `PLAUSIBLE` (supported, not proven) |
| The dispatcher's same-tick slot re-read stays `CONFIRMED_STATIC` and is **not** upgraded: the runtime evidence (the three-state sequence never stalls) is *consistent* with a re-read but does not require one | arm9 | `CONFIRMED_STATIC` |
| The slot reads `0x00000000` outside a battle. **Evidence of nothing** — the surrounding fields differ (first word `0x021D2A24` vs `0x020990E0`) and the region is populated either way, so it is a different allocation, not a contradiction of the sentinel | runtime | `not claimed` |
| The arm9 dispatcher is **not** at fault: it faithfully calls state 1 in mode 12. The hunt stays in ov6 | runtime `jus-rpl` | **`CONFIRMED_RUNTIME`** |
| The poll's entry `0x0214DB20` appears as the Thumb literal `0x0214DB21` exactly twice in ov6 — pools `0x0214DABC` and `0x0214DAD8`, each inside a small adjacent function. Two registration sites | ov6 | `CONFIRMED_STATIC` |
| Second gated entry to the same function, on a call result rather than the BSS byte | ov6 `0x0214DB94`–`0x0214DBA4` | `CONFIRMED_STATIC`; which path a real battle takes is `not claimed` |
| Mode 12 hits neither the installer nor its return site, in the same live GDB session that caught mode 2 — so the gate is **upstream of the call** | runtime `jus-usf` | **`CONFIRMED_RUNTIME`** |
| The handler at `root+0x000` is a **tick that reports completion**: invoked via trampoline `0x0214F948`; a non-zero return restores the default and clears `+0xC8` (`0x0214DD32`–`0x0214DD3E`) | ov6 | **`CROSS_CONFIRMED`** — runtime built a match-end oracle out of it and watched `+0xC8` go `1→0` with `root+0x000` restored to `0x02150F65` at rule completion |
| **`0x020AFEAC` = 4463 confirmed end to end.** Install completes at fc 4213 (`+0xC8` `0→1`, handler `0x0214FA79`); rule completes at fc 8503 (`+0xC8` `1→0`, handler back to default); battle object appears ~fc 4040. `8503 − 4040 = 4463`, exactly the configured value | runtime `jus-6fo` | **`CROSS_CONFIRMED`** (whole-match span vs a configured constant, through machinery unrelated to the on-screen counter) |
| Writer of `root+0x08` | — | `not claimed`. No `ldrb [x,#0x10]` → `str [y,#8]` pair exists anywhere in ov6; all 34 ov6 pool refs to `0x020AFE90` checked. Either a register-offset store or arm9. |

**Instrument rule adopted (runtime, `jus-usf`).** A breakpoint no-hit result is worthless unless the same
log shows the session stayed healthy and a control fired. Two earlier mode-12 runs printed identical
"0 hits" while GDB had detached on a `SIGILL` or the script had errored — either would have delivered a
clean-looking negative built on a dead debugger.

**Instrument rule adopted (runtime, `jus-2cu`) — pair a cheap test with one that fails differently.** A
rest-state correlation, clean across four modes and lining up exactly with installed-vs-not, was still
*downstream* of the real difference. A rest-state read cannot separate cause from consequence; a
breakpoint can. Requesting both in the same card is what caught it — the cheap read alone was persuasive
and wrong.

### The mode-12 gate, resolved to arm9 (P168)

`findings/p168-why-mode-12-never-installs.md`.

| what | where | confidence |
|---|---|---|
| State 1 (`0x0214DAA4`) rewrites the slot to the poll **only** if `0x0214DADC` returns non-zero; otherwise it returns having changed nothing | ov6 `0x0214DAA4` | `CONFIRMED_STATIC` |
| `0x0214DADC` `blx`es `0x0207382C`, then `cmp r0,#0` / `beq` to its own return | ov6 | `CONFIRMED_STATIC` |
| ~~Both levels gate on the same value, i.e. on what `0x0207382C` returns~~ — **RETRACTED.** That return only triggers an *early* return; `0x0214DADC`'s actual return value is produced by the rest of the function (`bl 0x0214D9C8` at `0x0214DAEA`, then three more calls). Runtime: the done flag is `1` in mode 12 too, so the veneer returns `1` there as well, yet mode 12 still never advances — so the discriminator is **downstream** | ov6 / runtime `jus-zko` | `RETRACTED` |
| `0x0207382C` is a **bound-method veneer**: `ldr ip,[pc,#4]` → `0x0207387C`, `ldr r0,[pc,#4]` → `0x0214BD50`, `bx ip`. **The caller's `r0` is discarded**, so the check is not a function of the battle object | arm9 | `CONFIRMED_STATIC` |
| Four identical veneers in a row bind `0x0207387C` to `0x0214BD50` / `0x0214BD70` / `0x0214BD70` / `0x0214BD60` — same method, four instances, in the same globals table as the `0x0214BD80` resource manager | arm9 `0x0207382C`–`0x02073868` | `CONFIRMED_STATIC` |
| The condition: returns 1 once `[0x0214BD58]` is set, and sets it when `((counter + 4) >> shift) & 0xFFFF >= 0x10`. Fields: `0x0214BD51` shift (byte), `0x0214BD52` counter (halfword, `+=4` per call), `0x0214BD58` done flag (byte) | arm9 `0x0207387C` | `CONFIRMED_STATIC` |
| ~~`0x0214BD50` is a fade / screen-transition progress object, and mode 12's black screen *is* the stuck transition~~ — **RETRACTED** (was `PLAUSIBLE`). The 16 bytes read byte-identical in four unrelated states (deck editor, arena menu, rule select, training battle): `02 01 20 00 3f 00 00 00 01 00 00 00`. Something that doesn't change when the game changes isn't tracking a transition | runtime `jus-zko` | `RETRACTED` |
| The done flag `[0x0214BD58]` is already `1` before START in **both** mode 2 and mode 12, and the counter never moves. Per my own decode a static counter is *predicted* by a set flag, so only the flag carries the argument | runtime `jus-zko` | **`CONFIRMED_RUNTIME`** |
| `0x0214BD50` is **arm9-owned static memory, not overlay space** — it sits below every overlay base (`0x0214CD20` for ov0–ov9, `0x02172A60` for ov10/11, `0x021AC1C0` for ov12/13), so there is no aliasing hazard and the runtime read is of the object I decoded. It is also past `arm9.bin`'s image end (`0x020A9158`), so it is BSS or autoload: zero at load, written once at init | arm9 | `CONFIRMED_STATIC` (clears the runtime loop's caveat) |
| `0x0214BD50` has **7 pool references, all inside one arm9 module** (`0x02073798`–`0x02073FF4`), alongside `0x0214BD60` (2) and `0x0214BD70` (5) — a family of sibling objects managed by one subsystem | arm9 | `CONFIRMED_STATIC` |
| The callback-slot sequence is **at least four states**, not three: `0x0214DAA5` → `0x0214DB21` → `0x0214DB61` → `0x0214DBCD`. `0x0214DB61` holds only ~30 frames and was invisible at 40-frame sampling. Four is a **lower bound** — treat the sequence as unenumerated until it comes from the code side | runtime `jus-zko` | **`CONFIRMED_RUNTIME`** |


**Codex was wrong on one operand and the bits settled it.** It matched every byte width, base offset, the
early-return, and the `lsl`/`lsr` masking (noting on its own that `ldrh` zero-extension makes the `asr`
logical) — then read `0x020738B0` as `cmp r0,#16` instead of `cmp r1,#0x10`. Encoding `E3510010` has bits
19–16 = `0001`, so `Rn` = `r1`; `query.py` agrees. Coherence check too: under its reading `r0` is a pointer,
always ≥ 16, so the conditional store would fire unconditionally and the comparison would be dead code.
Same shape as P158's `mla` swap — **when Codex disagrees on a decode, go to the bits.**

### Measurement constraints inherited from the runtime loop (2026-08-18)

Anything I design for them has to respect these:

- **`jus-5kf` (P1, open): the player's HP RECOVERS on the Battle path.** A clean point battle with items and
  gimmicks verified `0/0` in RAM showed the player going 5.8 → 58.6 → 110.4 with `chr_b` unchanged. Cause
  unsettled — auto-heal on by default, or the HP word animating up after a same-character respawn. **Any
  Battle-path measurement against an HP baseline is uninterpretable until it's settled.** Same shape as the
  gimmick contamination. Training path has auto-heal explicitly off and behaviourally confirmed.
  *Effect on my record:* none. Every damage figure the flat-damage synthesis leans on was taken on the
  training path. This is exposure for future Battle-path work, not retroactive taint.
- **Timeline resolution is ~400 emulated frames per sample round** (several IPC round trips per round, with
  the emulator free-running at 60 fps through all of them). 12 samples covered a 4463-frame match. So any
  duration experiment must use **base values well above ~500 frames**, or the per-round IPC has to be cut
  down first.
- **The Battle path defaults items and gimmicks ON** and nothing in that flow clears them; `rules_off()`
  works there but must be called explicitly. **Now gated (`jus-9ne`):** `match_run.py` raises *before*
  deriving addresses if items or gimmicks are on, so a contaminated run cannot reach the measurement.
  `--allow-contaminated` must be typed and stamps `contaminated_run: true` into the timeline. Every
  timeline carries its conditions block and `end_reason` at top level, so the harness can no longer emit a
  bare number. **What the gate does NOT cover:** `jus-5kf` (HP recovery) isn't gated, because the RAM value
  expressing it isn't known yet — so a Battle-path run still starts with a moving HP baseline and says
  nothing about it. When I design anything HP-based, that's mine to route to the training path.

**Evidentiary-weight rule (runtime's distinction, worth keeping).** Watching a transition land on a
*specific value named in advance* earns a cross-confirmation. Observing an *absence of contradiction* does
not — same instrument, different weight. That is why `root+0xC8` going `1→0` with `root+0x000` restored to
the pre-named `0x02150F65` upgraded the rule-completion path, while "the state sequence never stalls" left
the same-tick slot re-read at `CONFIRMED_STATIC`.

### The status param array is a data file (P169)

`findings/p169-state-bin-is-the-param-array.md`.

| what | where | confidence |
|---|---|---|
| The dispatcher's `paramArray = [[0x02172984]+4]` is the data of **`bin/state.bin`** — 336 bytes = exactly 42 × 8, parsing cleanly against P158's code-derived record layout | `jus_files/ripped_jus_files/bin/state.bin`; ov6 loader pools `0x02172364` (`"bin/state.bin"`), `0x02172374` (`"bin/exadd.bin"`) | `CONFIRMED_STATIC` |
| All **42 base durations** now known (frames). Longest: ids 7, 8 = `800`; ids 4, 5, 33 = `700`; ids 16, 19, 23, 35 = `600` | `state.bin` `+0x2` per entry | `CONFIRMED_STATIC` |
| `flags & 1` ⇄ `base == 0` holds across all 42 entries — instant effects have no duration to scale. Bit `0x10` set exactly on ids 20–34, matching the slot selector P158 read from code | `state.bin` `+0x0` | `CONFIRMED_STATIC` |
| `+0x4` is signed and carries positives (`10`…`60`) on instant entries, negatives (`-2`, `-4`, `-5`) on long timed ones — P158's "one field covers drain and fill", confirmed by the data | `state.bin` `+0x4` | `CONFIRMED_STATIC` |
| `+0x6` is `0x0000` in all 42 entries | `state.bin` | `CONFIRMED_STATIC` (still `not claimed` what it would mean if non-zero) |
| **Term `V` is readable, not timeable.** `0x02158F88` stores the formula's result at `node+0xE`, so `V = 0` predicts `node+0xE == base` exactly. One 16-bit read settles it — immune to the ~400-frame timeline resolution, needs no HP baseline, and needs no clean-rules run | ov6 `0x02158F88` | `CONFIRMED_STATIC` |
| Which in-play action inflicts which id | — | `not claimed`. Next static task (move-script opcodes). Until then the runtime test is a survey: any `(id, duration)` pair settles `V`. |

### Term `V` is ZERO in ordinary play — the campaign's only non-constant formula doesn't vary (P169, closed)

The runtime loop breakpointed the store at ov6 `0x02158F88` and captured a live pair: **effect id `10`,
stored duration `480`**. `bin/state.bin` entry 10 has `base = 480`. Since `base/10 = 48 ≠ 0`, the formula
`duration = base + (base/10)*(V*2)` gives `(480 − 480)/(2×48) = 0`, so **`V = 0`**.

| claim | confidence |
|---|---|
| `V = 0` in ordinary play, so `duration == base` and the only non-constant formula in the engine never actually varies | **`CROSS_CONFIRMED`** — a shipped data file's `+0x2` field and a live breakpoint capture agreeing exactly, through representations that share nothing |
| `bin/state.bin` **is** the param array — the dispatcher's `paramArray = [[0x02172984]+4]` reading, unchanged | `CONFIRMED_STATIC` |
| `node+0xE` holds the formula's result at apply time and then **counts down** | **`CONFIRMED_RUNTIME`** |
| `[root+0x4C]` (the `V` slot) reads zero in-battle, now on 5 states / 2 boots plus this derivation | **`CROSS_CONFIRMED`** |

**The runtime loop's apparent conflict dissolves — their `r4` is the wrong table.** They captured `r4 =
0x021711B8` and read an 8-byte record there (`2c 93 15 02 0d 04 05 ff`), noting it sits in ov6's image
rather than at `[[0x02172984]+4]` = `0x023DD5C0` (heap). The dispatcher builds **two** pointers at the same
stride from the same id:

```
0x02158EE4: ldr r3, [pc, #0x1fc]      ; r3 = 0x02171168  = HANDLER table (ov6 image)
0x02158EF0: ldr r1, [r0, #4]          ; r1 = [[0x02172984]+4] = PARAM array (heap, from state.bin)
0x02158EF4: add r4, r3, r8, lsl #3    ; r4 = &handlerTable[id]
0x02158EFC: add r5, r1, r8, lsl #3    ; r5 = &paramArray[id]
0x02158F44: ldrh r2, [r5, #2]         ; base duration comes from r5
```

`0x02171168 + 10*8 = 0x021711B8`, exactly their `r4`. And their record decodes perfectly as a *handler*
entry under P158's layout: `fn = 0x0215932C`, sound `0x0D`, enum `0x04`, `+0x6 = 0x05`, `+0x7 = 0xFF` — no
status opcode, which is right for id 10 being a gauge effect. So the record they read is the handler table
entry; the base duration comes from `r5`, which they didn't capture. Nothing about `state.bin` needs
revisiting.

**My scan design was wrong and they caught why.** `node+0xE` counts down after apply, while a 4 MB dump plus
scan costs hundreds of free-running frames, so the field no longer equals the base by the time the scan
runs. A differential scan across a fight found zero new hits. What *did* work was the `0x01 0x01`
discriminator I put in the card: of 6 baseline hits on the `(id, base)` halfword pattern, **none** carried
it, so it correctly rejected all six as coincidence. The fingerprint alone isn't specific in 4 MB of small
integers; breakpointing the store dodges the window entirely.

### The two tables joined — handler entry × `state.bin` param, all 42 ids (P169)

`CONFIRMED_STATIC`. Handler table at ov6 `0x02171168` (stride 8, in the overlay image) joined to
`bin/state.bin` (stride 8, loaded to the heap) by shared id. The split is clean and it names the two families:

- **ids 1–17, 35, 36** — `+0x7` is `0xFF` (no status opcode), sounds `0x07`/`0x09`/`0x0D`. The **gauge**
  effects. Both runtime captures (10 and 13) are here.
- **ids 18–34** — `+0x7` carries the status opcodes `0x19`–`0x22`, sound `0x0C` (or `0xFF` for 30–32). The
  **statuses**, which P159 found nearly unreachable from script operands.
- **ids 9–17** share `+0x6 = 0x05` and sound `0x0D` — one family, durations `120`–`600`.

| id | handler | sound | enum | `+0x6` | `+0x7` opcode | flags | base | amount |
|---|---|---|---|---|---|---|---|---|
| 0 | `0x02159258` | `0xff` | `0xff` | `0xff` | `0xff` | `0x0000` | 0 | 0 |
| 1 | `0x021592a0` | `0x07` | `0xff` | `0x00` | `0xff` | `0x0001` | 0 | 10 |
| 2 | `0x021592a0` | `0x07` | `0xff` | `0x00` | `0xff` | `0x0001` | 0 | 20 |
| 3 | `0x021592a0` | `0x07` | `0xff` | `0x00` | `0xff` | `0x0001` | 0 | 40 |
| 4 | `0x021592c0` | `0x0d` | `0x00` | `0x01` | `0xff` | `0x0002` | 700 | 5 |
| 5 | `0x021592dc` | `0x0d` | `0x01` | `0x03` | `0xff` | `0x0002` | 700 | 5 |
| 6 | `0x021592f8` | `0x0d` | `0xff` | `0x05` | `0xff` | `0x0001` | 0 | 0 |
| 7 | `0x0215930c` | `0x0d` | `0x02` | `0x09` | `0xff` | `0x0002` | 800 | 0 |
| 8 | `0x02159258` | `0x0d` | `0x03` | `0x07` | `0xff` | `0x0002` | 800 | 0 |
| 9 | `0x0215931c` | `0x0d` | `0x05` | `0x05` | `0xff` | `0x0002` | 120 | 0 |
| 10 **←runtime** | `0x0215932c` | `0x0d` | `0x04` | `0x05` | `0xff` | `0x0002` | 480 | 0 |
| 11 | `0x02159258` | `0x0d` | `0x06` | `0x05` | `0xff` | `0x0002` | 240 | 0 |
| 12 | `0x02159344` | `0x0d` | `0x13` | `0x05` | `0xff` | `0x0002` | 120 | 0 |
| 13 **←runtime** | `0x02159364` | `0x0d` | `0x0b` | `0x05` | `0xff` | `0x0002` | 300 | 0 |
| 14 | `0x02159378` | `0x0d` | `0x08` | `0x05` | `0xff` | `0x0002` | 240 | 0 |
| 15 | `0x021593a4` | `0x0d` | `0x09` | `0x05` | `0xff` | `0x0002` | 300 | 0 |
| 16 | `0x021593d0` | `0x0d` | `0x0a` | `0x05` | `0xff` | `0x0002` | 600 | 0 |
| 17 | `0x02159434` | `0x0d` | `0x07` | `0x05` | `0xff` | `0x0002` | 240 | 0 |
| 18 | `0x021594e4` | `0x0c` | `0x0c` | `0x0a` | `0x1f` | `0x0032` | 100 | 0 |
| 19 | `0x02159500` | `0x0c` | `0x0d` | `0x0b` | `0x1d` | `0x0032` | 600 | -4 |
| 20 | `0x02159538` | `0x0c` | `0x0f` | `0x0c` | `0x1c` | `0x0012` | 360 | 0 |
| 21 | `0x02159258` | `0x0c` | `0x10` | `0x0d` | `0xff` | `0x0012` | 480 | 0 |
| 22 | `0x02159578` | `0x0c` | `0x11` | `0x08` | `0x21` | `0x0012` | 540 | 0 |
| 23 | `0x02159594` | `0x0c` | `0x12` | `0x0e` | `0x1e` | `0x0012` | 600 | 0 |
| 24 | `0x02159608` | `0x0c` | `0x14` | `0x0e` | `0x22` | `0x0012` | 480 | 0 |
| 25 | `0x02159608` | `0x0c` | `0x15` | `0x0e` | `0x22` | `0x0012` | 480 | 0 |
| 26 | `0x02159258` | `0x0c` | `0x16` | `0x0e` | `0xff` | `0x0032` | 240 | 0 |
| 27 | `0x02159258` | `0x0c` | `0x17` | `0x0e` | `0xff` | `0x0032` | 240 | 0 |
| 28 | `0x021596e0` | `0x0c` | `0x19` | `0x0e` | `0x20` | `0x0012` | 180 | 0 |
| 29 | `0x021597f8` | `0x0c` | `0x1a` | `0x0e` | `0x20` | `0x0012` | 180 | 0 |
| 30 | `0x02159624` | `0xff` | `0x1b` | `0xff` | `0x1b` | `0x0032` | 480 | -2 |
| 31 | `0x02159694` | `0xff` | `0x1c` | `0xff` | `0x19` | `0x0032` | 240 | 0 |
| 32 | `0x02159678` | `0xff` | `0x1d` | `0xff` | `0x1a` | `0x0032` | 60 | 0 |
| 33 | `0x021592dc` | `0x0c` | `0x0e` | `0x04` | `0xff` | `0x0012` | 700 | -5 |
| 34 | `0x02159258` | `0x0c` | `0x18` | `0x0e` | `0xff` | `0x0032` | 300 | 0 |
| 35 | `0x0215941c` | `0x0d` | `0x1e` | `0xff` | `0xff` | `0x0002` | 600 | 0 |
| 36 | `0x021593e8` | `0x0d` | `0x1f` | `0xff` | `0xff` | `0x0002` | 360 | 0 |
| 37 | `0x02159260` | `0x07` | `0xff` | `0x00` | `0xff` | `0x0001` | 0 | 50 |
| 38 | `0x02159260` | `0x07` | `0xff` | `0x00` | `0xff` | `0x0001` | 0 | 30 |
| 39 | `0x02159280` | `0x09` | `0xff` | `0x02` | `0xff` | `0x0001` | 0 | 60 |
| 40 | `0x02159280` | `0x09` | `0xff` | `0x02` | `0xff` | `0x0001` | 0 | 30 |
| 41 | `0x02159280` | `0x09` | `0xff` | `0x02` | `0xff` | `0x0001` | 0 | 15 |

**Second independent `V = 0`** (runtime): id 13, stored duration `300`, and they read `base` live from
`r5+2` rather than from my table — `300 == 300`. Two ids now agree, and the second didn't depend on me
supplying the base. The two-table correction is also verified at runtime: `0x02171168 + 13×8 = 0x021711D0` =
their `r4`, while `r5 = 0x021E0AA8` sits on the heap in a different region.

**Instrument rule, sharpened by the runtime loop (this is a real hole in the version I'd adopted).** "A
control fired" is not enough — **a control that fires once at the start of a run cannot certify a negative
collected later in that run.** The installer `0x0214F91C` fires at battle start, so it proved the session was
alive at phase zero and said nothing about phase eight. A control has to *recur*, or liveness has to be
sampled alongside the measurement. This surfaced when an attribution sweep returned eight zero phases and the
battle had already ended on the 4463-frame limit partway through.

### `V = 0` generalises past the gauge family, and id 21 is positive evidence for Route B

Runtime captured four valid `(id, base, duration)` triples with derefs inside the breakpoint command:
id 21 → `480/480`, id 10 → `480/480` (twice, reproducible), id 7 → `800/800`. `r4 = handlerTable + id×8` on
every row. So **`duration == base` on three distinct ids**, and one of them is in the **status** family
(18–34), not the gauge family. `V = 0` is not confined to gauge effects.

**id 21 firing supports P159's Route B rather than undermining "nearly unreachable".** P159's claim was
narrower than it reads: *"of ids `0x12`–`0x22`, only `0x18` and `0x21` appear in the operand map"*, with
`PLAUSIBLE`: statuses are inflicted through **Route B** — the staged `+0x172`/`+0x173` bytes flushed on hit at
`0x02158B20` — while script opcodes drive gauge effects. id 21 is `0x15`, which is **not** in the operand map.
So a status that scripts can't reach fired in ordinary play, which is exactly what Route B predicts.
Strengthened, not confirmed: no runtime evidence yet links the staging bytes to that apply.

**Route attribution is one breakpoint, not a button sweep.** The dispatcher `0x02158ED0` has 3 callers, and
two of them are the Route B flush sites:

| `LR` at the dispatcher entry | route |
|---|---|
| `0x02158B50` | Route B via `X+0x173` (stored **negated**) |
| `0x02158B68` | Route B via `X+0x172` (used as-is) |
| anything else | Route A (script opcode) or the third caller |

`X = [[battleObj+0x1A8]+0x10]`. So breaking at the dispatcher entry and capturing `LR` attributes **every**
effect that fires, for all 42 ids at once, instead of guessing inputs.

**The garbage row is probably overlay aliasing, and the filter should say why rather than clip a range.**
Runtime saw one hit at `0x02158F88` with `id = 12287` and `r4 = 0x023DE2D0`. That `r4` cannot come from
`0x02171168 + id×8` for any id (id 12287 would give `0x02189160`). `0x02158F88` sits in the **shared overlay
window** `0x0214CD20`+, which ov0–ov9 all alias, so when a non-ov6 overlay is resident those bytes are
unrelated code and the register meanings don't hold. Better filter than an id range: **capture `[0x02172960]`
at each hit and reject hits where it reads `0` — no battle means the code at that address isn't the
dispatcher.** That drops aliased hits for a stated reason instead of silently clipping a genuine
out-of-range id, which was the runtime loop's own objection to range filtering.

### Route B drives the gauge family too — P159's division of labour is RETRACTED (P170)

Runtime ran the LR card (`jus-5qy`) with `break *0x02158ED0 if $r1 != 0`. Every non-zero dispatch:

| dispatch | `LR` | route | store |
|---|---|---|---|
| id 9 | `0x02158B68` | Route B via `X+0x172` | `120/120` |
| id 1 | `0x02158B68` | Route B via `X+0x172` | none — correct, `flags & 1`, base 0 |
| id 13 | `0x02158B68` | Route B via `X+0x172` | `300/300` |
| id 9 | `0x02158B68` | Route B via `X+0x172` | `120/120` |

`RETRACTED` — P159's `PLAUSIBLE` **"script opcodes drive gauge effects"**, and with it the clean
gauge/status division of labour. Ids 1, 9 and 13 are all gauge-family and all three arrived by **Route B**.
This is the exact refutation condition I wrote into the card, so the label comes off. Route A never appeared
and neither did the third caller.

What survives, and what doesn't:

- **Survives:** Route B is real and is the observed inflict path for gauge ids. `CONFIRMED_RUNTIME`.
- **Survives, and is now observed rather than inferred:** Route B is a **per-frame flush that usually has
  nothing staged.** An unconditional breakpoint caught **15,732** dispatcher calls, *all* with id 0, hitting
  both `0x02158B50` and `0x02158B68`. That is exactly what the staged-`+0x172`/`+0x173`-bytes model predicts.
- **Still untested:** "statuses arrive via Route B." No status-family id fired with an LR captured. The id 21
  from the earlier run has no LR and contributes nothing. So the finding is *"gauge ids use Route B"*, **not**
  *"both families use Route B"*. Bounded at n=4, one session, one matchup, items ON.
- **Bounded:** Route A's absence is an absence in this matchup, not a demonstration that Route A is dead.

**`V = 0` now on five ids** — 7, 9, 10, 13, 21 — with base read live from `r5+2` on the later ones.
`duration == base` every time.

**Instrument note worth keeping (runtime's).** The dispatcher is far too hot to breakpoint unconditionally:
15,732 stop/print/resume round trips throttled the emulator so hard that almost no real fight happened, and
those zeros were *the instrument's own cost, not the game*. A conditional breakpoint gave 4 useful captures
instead of 15,732 useless ones. This is a third distinct way to manufacture a worthless null, alongside dead
instrument and absent stimulus: **an instrument whose cost suppresses the phenomenon it measures.**

### Two corrections for the character-change hunt (P170)

- **The change attack targets the OPPONENT.** My own P165 table row abridged rulemess entry 9 to "make
  everyone the same character", which is ambiguous about whose character changes. The Japanese is explicit:
  `キャラチェンジ攻撃（↓＋Ｂ）を当てて、相手を全員同じキャラクターにするのだ！` — *land* ↓+B to make **`相手`
  (the opponents)** all the same character. So watching the player's own `chr_b` after pressing ↓+B is
  watching the wrong entity, and the attack must **land**, not merely be pressed.
- **`char+0x1E0` cannot be the switch indicator.** Already `CONFIRMED_STATIC` on record since iteration 73
  (`findings/allocations-are-tagged-and-the-battle-character-is-0x1F0.md`): `Battle_CharaCreate` (ov6
  `0x02156A38`, `BattleChara.cpp`) allocates the `0x1F0`-byte battle character and writes `+0x1E0` **once,
  from `arg0`, at construction**. A character change therefore cannot work by mutating it — it must swap
  which character object is active. So `+0x1E0` is a per-object identity, not a live "who is out" field.

### The real division of labour is between the two staging bytes (P170, runtime + static)

Runtime caught a status arriving on the other flush site:

| flush site | staging byte | ids observed | family |
|---|---|---|---|
| `0x02158B68` | `X+0x172`, used as-is | 1, 9, 10, 13 (n=6) | gauge |
| `0x02158B50` | `X+0x173`, **negated** | 20 (n=1) | status |

So **both families inflict through Route B, and the channel split is between the two staging bytes** — which
also explains why the code flips the sign on exactly one of them. That replaces the script-vs-Route-B
division P159 proposed and P170 retracted.

`n=1 on the status side`, in the label rather than a footnote: one status id, one LR, one matchup. The gauge
side is n=6 across four ids. **If a status ever lands on `+0x172`, the model collapses.**

**Independent static support, found the same wake.** Every writer of both bytes lives in **ov12**, not ov6 —
so staging and flushing are in different overlays. Two of them are dedicated two-instruction leaf setters,
one per channel:

```
0x021BC194: strb r1, [r0, #0x172]   ; bx lr      <- the +0x172 setter
0x021BC19C: strb r1, [r0, #0x173]   ; bx lr      <- the +0x173 setter
```

Separate public setters per byte is the two-channel structure by construction, arrived at from the writer
side with no knowledge of the runtime LRs. Full writer list: `+0x172` at `0x021BC194`, `0x021C7A10`,
`0x021C9770`, `0x021C9C24`; `+0x173` at `0x021BC19C`, `0x021C7A14`, `0x021C9AD8`.

**One caution for the gauge side.** `0x021C7A0C`–`0x021C7A1C` is an initialiser: `mov r0,#1` /
`strb r0,[r4,#0x172]` / `strb r1,[r4,#0x173]` / `strb r1,[r4,#0x174]` with `r1 = 0`. So `+0x172` is set to
**1** and `+0x173` to `0` at init. `PLAUSIBLE`: id 1 arriving via `+0x172` is a *default* staging rather than
an inflicted effect — consistent with runtime seeing id 1 dispatch with no store (`flags & 1`, base 0).
`not claimed` whether the other `+0x172` ids are defaults or inflicted.

**`V = 0` now on six ids across both families** — 7, 9, 10, 13, 20, 21. `duration == base` every time.

**Fourth instrument rule (runtime's, caught on themselves).** A *filtered* breakpoint that stays silent
cannot certify itself — silence is indistinguishable from "never installed". They recorded "0 dispatches
across 27 trials" with no evidence the conditional breakpoint was live, and it was only cleared by a lucky
late hit in the free-running gap. The fix is a third breakpoint on something that fires regularly, not
waiting for luck.

**And the effects are mostly the COM's doing.** Driving attacks produced nothing; *landing basic attacks*
produced nothing either, with contact confirmed through opponent HP (54.1 and 97.0 damage, a KO and a respawn)
— **narrowed at the runtime loop's own request: that negative covers landed BASIC attacks and does not extend
to landed attacks of any kind, because HP contact says nothing about whether a status move was thrown.** What
produced dispatches was letting the match play under light pressure — six dispatches in ~10 minutes of battle
time. So the parked stimulus hunts matter less for this question than expected: the game inflicts these on its
own and the task is to let it run and catch what it does.

### The channel split holds at n=17, and the families are better defined by opcode than by id range

| flush site | staging byte | ids observed | n |
|---|---|---|---|
| `0x02158B50` | `X+0x173`, negated | 19, 20, 32, 32 | 4 — all status |
| `0x02158B68` | `X+0x172`, as-is | 1, 8, 9, 10, 13 | 13 — all gauge |

**No crossover in either direction across 17 attributed dispatches.** My per-byte setters and the runtime LR
split now agree at n=17. The collapse condition (a status on `+0x172`) has not fired.

**Sharpening, and it removes a confound of my own.** I had been calling ids 18–34 "the status family" by id
range. The cleaner line is `+0x7` in the handler entry: **12 ids carry a status opcode** — 18 (`0x1F`), 19
(`0x1D`), 20 (`0x1C`), 22 (`0x21`), 23 (`0x1E`), 24 (`0x22`), 25 (`0x22`), 28 (`0x20`), 29 (`0x20`), 30
(`0x1B`), 31 (`0x19`), 32 (`0x1A`) — while 21, 26, 27, 33 and 34 sit in that id range with `+0x7 = 0xFF`.
Every `+0x173` id observed is opcode-bearing. And **id 21 has no status opcode**, so my earlier "a status
crossed the family boundary" claim rests on a bad definition — id 21 also has no LR capture, so it should be
dropped from the argument entirely rather than counted on either side.

`V = 0` on **eight** ids now: 7, 9, 10, 13, 19, 20, 21, 32.

### Reading ids 19 and 32 against the table (the freeze question)

The owner supplied ground truth mid-run: Goku's 4-koma inflicts a **freeze** on up+X. That move produced
both id 19 and id 32, and the runtime loop correctly declined to pick between them. From the joined table:

| id | handler | sound | `+0x6` | opcode | flags | base | amount |
|---|---|---|---|---|---|---|---|
| 19 | `0x02159500` | `0x0C` | `0x0B` | `0x1D` | `0x0032` | 600 | **−4** |
| 32 | `0x02159678` | `0xFF` | `0xFF` | `0x1A` | `0x0032` | 60 | **0** |

`PLAUSIBLE`: **id 32 is the freeze** — amount `0` (changes no resource), 60 frames = 1.0 s, no sound and no
`+0x6` resource index, which fits a brief hold rather than an ongoing effect. `PLAUSIBLE`: **id 19 is a
drain** — amount `−4` per tick over 600 frames, with its own sound and resource index.

**And there is a real tension worth resolving rather than smoothing over.** The runtime loop reports the
opponent's HP at `152.0` before and after, unchanged, in every rep — yet id 19 carries amount `−4`. If that
`−4` applied to HP over 600 frames the HP would have moved a long way. Three readings survive: the `−4`
applies to a **gauge** rather than HP (consistent with C6b's result that no melee damage reaches this
subsystem); the effect was applied to the **player** rather than the opponent; or the tick handler never ran.
`not claimed` which. Watching a gauge through an id-19 window separates the first from the others.

### Every observed effect is one-shot — including the status (P170)

The `node+0x0` readout works and is now part of the runtime loop's standard capture. Three stores:

| id | dur/base | `node+0x0` | amount | channel |
|---|---|---|---|---|
| 8 | 800/800 | `0x02159258` (stub) | 0 | `+0x172` gauge |
| 32 | 60/60 | `0x02159258` (stub) | 0 | `+0x173` **status** |
| 10 | 480/480 | `0x02159258` (stub) | 0 | `+0x172` gauge |

`CONFIRMED_RUNTIME`: all three were **stubbed out on apply** — the handler returned 0, so `table[id].fn` was
replaced by the no-op `0x02159258` (P158's mechanism) and **no tick handler runs for any of them**, status
included.

`PLAUSIBLE`, and it reframes what "duration" is: if the node's own tick handler is a stub, the `node+0xE`
duration cannot be driven by the node. It must be a **state timer read by other systems** — most likely gated
by the status opcode at handler `+0x7` — rather than a countdown the effect subsystem services itself. That
fits the whole subsystem being flat: no scaling, no per-tick work, just a staged id, a duration and an opcode
for someone else to honour.

`not claimed`: the id-19 `−4` tension is **still open**. Their amount read returned 0 for all three above,
which matches the table for each, so the read is sound — it just hasn't caught id 19 yet.

**A coincidence the runtime loop refused to bank, correctly.** Across five reps of Goku up+X the opponent's HP
never moved while *their own* HP dropped twice (152.0→149.0, 152.0→103.0). That superficially supports the
"self-cost" reading of id 19's `−4`. They declined to count it, on the simpler reading that the COM
counter-attacked and up+X never connected — which also explains the thin yield, one status store in five reps
against three in four previously. Recorded as **not** support for reading two.

Tally: `+0x173` — 4 dispatches across 3 opcode-bearing ids. `+0x172` — 13 across 5. No crossover.
