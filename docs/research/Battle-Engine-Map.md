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
confidence, both are shown. **One exception:** the `projectile-entities`
subsystem's verification lenses were skipped for time at the end of the
campaign — see its section for how that is handled.

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

- Who writes `[[charPtr+0x1a8]+0x10]+0xE8` (and `+0x130`)? This is the single highest-value unresolved item in the whole campaign — see next-campaign spec **B11**.
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
| 5 | The scratch base `[[char+0x1a8]+0x10]` is rooted at the MoveInfo object: allocated (`0x02156A58`, size `0x1F0` = 496 bytes) inside `0x02156A38`, and installed into `char+0x1a8` by setter `0x021570EC`. MoveInfo's own `+0x10` field points at the delta-holding sub-object (`+0x40` flags bit `0x800` gates delta application). The writer of that sub-object's `+0xE8`/`+0x130` fields is still unfound. | `0x02156A38`, `0x02156A58`, `0x021570EC` | **PLAUSIBLE** |

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

**Status:** PARTIAL *(loop-state: TRACING — most-refuted subsystem this round; needs a fresh round-2 angle before promotion)*

| # | Claim | Key addresses | Confidence |
|---|-------|---------------|------------|
| 1 | `0x020924B0` is **not** a raw pointer array — it is an 8-byte-stride table of homogeneous `{word0, word1}` records, indexed via `lsl#3` by the arm9 character-load routine. | `0x02074730`, `0x02074780`, `0x02074728` | **CONFIRMED_STATIC** |
| 2 | `word0` of a `0x020924B0` entry is a NUL-terminated ASCII character-ID C-string (e.g. `"db_b_01"`), fed through a strcpy-like byte loop. | `0x0207478C`, `0x0209E92C` | **PLAUSIBLE** *(was CONFIRMED_STATIC; demoted — aliasing lens REFUTED)* |
| 3 | The table has exactly 74 entries; ov0 function `0x0214EFAC` linearly scans all 74, extracting a 6-bit id (`word1` bits 14–19), hypothesized to equal chr_b's `classId`. | `0x0214EFD8`, `0x0214F034` | **SPECULATIVE** *(was CONFIRMED_STATIC; demoted — 2/3 lenses REFUTED)* |
| 4 | ov6 `0x02159EF8` (per-character state dispatcher, gated on `r6+0xCB`/`+0xD2`/`+0xD3`/`+0x1A4`/`+0x1A8`) is architecturally the right neighborhood for clash resolution, but no direct two-base-register hitTier comparison was found inside it. | `0x02159EF8`, `0x0215A03C` | **SPECULATIVE** |

**Nuance on claim 2's demotion:** the ASCII char-ID string itself is real and confirmed (entry 0 spells out `"db_b_01\0"` byte-for-byte). What was refuted is the framing that this string is "used to build the collision (and sibling sound/ai) resource path": the one traced consumer (claim 3's ov0 function) actually builds a **sprite-archive (`.aar`) / ending-credits** resource key, not a collision-file key — `c.aar` is a documented sprite-archive suffix convention (`ARM9-Research-Guide.md`), and the consuming subsystem is the game's ending/credits sequence.

**Nuance on claim 3's demotion:** chr_b's `classId` field actually ranges 256–684 in the exported data, which cannot fit in a 6-bit extraction (max 63) — the identification was a tracer arithmetic error, caught by two independent lenses. Only the table's raw shape (74 × 8-byte records) survives verification.

### Refuted hypotheses (hitbox-priority)

- **`0x020924B0` = char-ID-string-table-not-collision:** it is **not** a collision-blob pointer table, contrary to the framing carried in prior documentation (`ARM9-Research-Guide.md`'s "Collision file pointer table"; `Research-Status.md`'s "ARM9.bin offset 0x0924B0 contains pointer table to collision file names" — see the correction note added to `Research-Status.md`). It is an 8-byte-stride `{ASCII char-ID string, packed word}` table, and its one traced consumer is unrelated to collision loading.
- **The 6-bit id in `word1` is not chr_b's `classId`** — refuted by range mismatch (256–684 vs. a 6-bit field's 0–63 range).
- **The original round-1 next-angle** ("trace forward from the resource-loader thunks `0x0201A228`/`0x02010254` reached backward from `0x020924B0`") is now a dead end, per the above — round 2 must use a different entry point (see next-campaign spec **B11**, which supersedes it).

### Open questions

- Where is the actual runtime `CollisionEntry` parser — the code that walks the loaded 20-byte-stride collision array field-by-field at hit-test time? Not located in this campaign at all.
- No two-entity `hitTier`/`hitProperties` comparison (the literal clash-resolution code) was found anywhere in ov0/ov3/ov4/ov5/ov6.
- What does the 6-bit id in `word1` actually encode, if not `classId`? It increments by exactly 1 between consecutive raw table entries, consistent with *some* dense per-character index space, just not the one hypothesized.

---

## Subsystem: projectile-entities

**Status:** PARTIAL. **Evidence machine-verified; adversarial lens verification pending.** No `.scored.json` file exists for this subsystem — the three verification lenses (disasm-correctness/aliasing/data-consistency) were skipped for time at the end of the campaign. **Every claim below is therefore treated as PLAUSIBLE regardless of its stated `CONFIRMED_STATIC` confidence**, pending a future verify round.

| # | Claim | Key addresses | Stated confidence | Treated as |
|---|-------|---------------|--------------------|------------|
| 1 | **Alloc (Q1):** `0x020834D4` is a fixed-capacity pooled-entity constructor. Dereferences global manager singleton (literal `0x0214BE14`); checks manager`+0x14` (free-list head) for NULL; invokes a caller-supplied ctor callback via `blx`, storing the result at `entity+0x30`; unlinks from `+0x14`, appends to manager`+0xc` (success) or `+0x1c` (failure). | `0x020834DC`–`0x020835F0` | CONFIRMED_STATIC | **PLAUSIBLE** |
| 2 | **Free (Q1):** `0x02083648` is the symmetric destructor — sets `entity+0x2c` bit 0 ("marked dead"), calls the on-destroy hook at `entity+0x10`, unlinks from manager`+0xc` (active list), appends to manager`+0x1c` (pending/retire list). Called from 32 sites (2 arm9, 30 ov6). | `0x02083650`–`0x02083690` | CONFIRMED_STATIC | **PLAUSIBLE** |
| 3 | **Spawn dispatch (Q2):** ov6 `0x021574CC` is a 13-way switch keyed on its 3rd argument, operating on the character struct's `+0x1a4` (hit-tally) and `+0x1a8` (MoveInfo). Case index 8 unconditionally reaches `0x2168cf4` at `0x02157700`, passing the character's MoveInfo pointer and a per-move collision/type data block. | `0x02157684`–`0x021576C0` | CONFIRMED_STATIC | **PLAUSIBLE** |
| 4 | **Spawn + ownership (Q2/Q4):** `0x02168CF4` obtains a spawner/wrapper object from a second, ov6-local manager (literal `0x02172990`), calls the `0x020834D4` allocator, stores the new entity pointer at wrapper`+8`, and stores the attacking character's **MoveInfo pointer** (not the character struct directly) at wrapper`+0xc` — one indirection removed from the character struct. | `0x02168CFC`–`0x02168E5C` | CONFIRMED_STATIC | **PLAUSIBLE** |
| 5 | **Despawn (Q3):** ov6 `0x0216C958` has 4 independent per-frame kill conditions, all converging on `0x02083648`: (a) a flag-bit/boundary-test gate; (b) a 16-bit age counter at `entity+4` vs. hard threshold `0x20` (32 frames); (c)/(d) two further threshold checks on a separate field. | `0x0216CA00`–`0x0216CAE8` | CONFIRMED_STATIC | **PLAUSIBLE** |

### Refuted hypotheses (projectile-entities)

None — no verification lenses ran, so nothing was formally refuted this round. Treat every claim above with the caution its **PLAUSIBLE** downgrade implies.

### Open questions

- **Q5 (persistence across character switch)** was deliberately left unanswered (no guessing): the only observed ownership link (wrapper`+0xc` → MoveInfo, not the character struct) and the self-contained despawn conditions (no "is my owner still active" check found) are both *consistent with* persistence but do not prove it. The missing piece is the character-switch/tag-out teardown function itself.
- Exact semantics of manager`+0xc`/`+0x14`/`+0x1c` (working hypothesis: active/free/pending lists) are inferred from control flow only — never confirmed against a live dump.
- The relationship between the ov6-local manager (`0x02172990`) and the arm9 global pool manager (`0x0214BE14`) is only partially traced.
- Finalizers `0x2083c44`/`0x2083cd8` index a per-category table via `entity+0x38` — a possible mechanism for distinguishing "projectile" from other spawned hitbox/effect types, unexplored.

---

## Subsystem: physics-writers

**Status:** PARTIAL *(loop-state: TRACING — velocity/gravity/decay NOT found this round; the least-resolved subsystem in the campaign)*

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
- **Most promising unchased lead (from loop-state, not yet followed up):** koma.bin's `PassiveIndex` field may key into a separate ~50-entry ARM9 passive table — hypothesized to be the concrete mechanism behind Edajima's documented knockback-resistance passive (see `Research-Status.md`'s "Edajima outlier" note). Flagged as next-campaign spec **B14**.
- ~85 of the ~87 total code references to the chr_b singleton (`0x0214BD80`) remain undisassembled for their record-offset access — a systematic catalog was proposed but not executed this round.

---

## Subsystem: collision-data

**Status:** PARTIAL — **data-only** (no disassembly; statistical mining of exported collision/jpower JSON, single data-consistency verification lens rather than the usual three)

**Coverage caveat (applies to every claim below):** only **4 of ~74** expected per-character collision JSON files have been exported (`bb_b_01`, `bl_b_01`, `db_b_01`, `ds_b_03`) — **5.4% roster coverage**, and not a random sample (one base-form character, one buffable/Ichigo kit, one base-Goku, one alt-kit Caramelman J). All statistics describe these 4 files and 92 pooled collision entries only, and should not be generalized to the full 74-character roster.

| # | Claim | Confidence |
|---|-------|------------|
| 1 | Only 4/74 expected collision files exist on disk. | **CONFIRMED_STATIC** |
| 2 | Collision (22-field) and jpower (20-field) schemas share zero field names — no explicit numeric join key exists between a collision entry and a jpower row. | **CONFIRMED_STATIC** |
| 3 | `hitTier` occupies a small closed range `{0,1,2,3}` (4 values, 91 entries) vs. jpower's much wider damage ranges — shape-consistent with a priority/tier enum, not a damage magnitude. | **PLAUSIBLE** |
| 4 | `collisionType` predicts `hitTier` within-sample: type 5 → 87.5% tier 3 (14/16); type 3 → 65.1% tier 1 (28/43). | **PLAUSIBLE** *(capped: UNSURE)* |
| 5 | `knockback` vs. `hitTier` is **non-monotonic** in the pooled averages (14.49/12.11/15.00 by tier). | **SPECULATIVE** *(was PLAUSIBLE; REFUTED — see correction below)* |
| 6 | `hitModifier` is constant `0` across all 92 entries in all 4 files. | **CONFIRMED_STATIC** |
| 7 | `projectileId` takes only two values: `0` (90×) or `-32` (2×, in two *different* characters) — behaves as a shared type-tag/sentinel, not a unique per-instance id. | **PLAUSIBLE** |
| 8 | `collisionType=4` is necessary-but-not-sufficient for nonzero `projectileId`: both nonzero instances are type 4, but only 2 of 12 type-4 entries carry a nonzero id. | **PLAUSIBLE** |
| 9 | `hitProperties` uses only bits `0x1`/`0x2`, observed only as `3` or `0`, and is **near-perfectly file-constant per character** (bl_b_01/db_b_01 = 100% zero; bb_b_01/ds_b_03 ≈96% = 3) — looks like a per-character trait, not a per-hitbox gate. | **PLAUSIBLE** |
| 10 | The two nonzero-`projectileId` entries have **opposite** `hitProperties` (3 vs. 0) — contradicts a clean "hitProperties gates projectiles" reading. | **PLAUSIBLE** |
| 11 | `damageFlags==0` is the majority case (52/91 = 57.1%), consistent with (but not independent proof of) indirect jpower resolution for zero rows. `bl_b_01` (Ichigo) is a strong outlier at 1/20 = 5%. | **CONFIRMED_STATIC** |
| 12 | `damageFlagsLow`/`hasSpecialFlag` are exact bitfield decompositions of `damageFlags` — exporter-derived, not independent data. | **CONFIRMED_STATIC** |
| 13 | Only 1/92 entries flagged `isTerminator` (bb_b_01's last); the other 3 files have zero, despite presumably needing a terminator convention — may be an exporter-heuristic artifact. | **CONFIRMED_STATIC** |
| 14 | `reserved0`–`reserved3` are uniformly `(0,0,0,0)` across all 92 entries. | **CONFIRMED_STATIC** |
| 15 | `frameStart` ranges 0–80; `durationMult` only takes `{0,10,100}`; `width`/`height` range `-8..30`/`-13..30` with 12.1% of entries negative — raises an unresolved signed-axis/directional-offset question. | **CONFIRMED_STATIC** |

### Refuted hypotheses (collision-data)

- **Knockback rises monotonically with hitTier when bl_b_01 is excluded.** Claim 5's non-monotonicity finding is **REFUTED** — it was a pooling artifact caused by `bl_b_01` being 100% `hitTier=1` with an unusually high average knockback for that tier alone. Excluding `bl_b_01`, knockback rises cleanly **8.78 → 12.11 → 15.00** across tiers 1→2→3, which *supports* `hitTier` as a genuine intensity/priority proxy — the opposite of the original conclusion.
- The `collisionType=3 → hitTier=1` correlation (claim 4) is **UNSURE** at the per-file level and should not be treated as confirmed, unlike the more robust `collisionType=5 → hitTier=3` correlation.

### Open questions

- The still-unknown collision↔jpower entry-selection mechanism (`jpower-Mapping.md`'s "Selection mechanism unknown") was not resolved by this data-only pass, since no join key exists in either schema.
- With only 2 total nonzero-`projectileId` observations, is `-32` truly a fixed sentinel, or would a larger sample reveal other distinct nonzero values?
- **Tooling gap with a ready-made fix:** the repo's own CLI (`src/JUS.CLI/JUS/CombatCommands.cs`) has an `ExportAllCollisions` batch command that has never been run against the full character `.bin` directory. Running it would raise coverage from 4/74 toward 74/74 and let every `PLAUSIBLE`/`UNSURE` claim above be re-tested at full-roster scale.

---

## Cross-Cutting Structures

These structures were discovered piecemeal across multiple subsystem tracers above; they are consolidated here because several open questions in *different* subsystems turn out to be the **same** open question about the **same** object.

### 1. Character wrapper (`sl`) — identity ambiguity (highest-leverage open item)

Damage-pipeline, physics-writers, hitstun-timers, and weight-hunt **each independently** hit the same unresolved question this campaign: is the object referred to as `sl`/`charPtr`/`scratch` in ov6's hit-resolution code (`0x02158B20`) the *same* object as the GDB-verified character struct (rooted at pointer chain `0x023D2A74`), or is it one (or more) pointer indirections away? Static `xrefs-to`/`pool-values` on the literal `0x023D2A74` return **zero hits ROM-wide** (it is a heap/runtime-only address, invisible to static search), so this cannot be resolved without a live session. This is the campaign's single highest-leverage unresolved item — see next-campaign spec **B10**.

Known fields on whichever object this turns out to be:

- **`+0x1a4`** — hit-tally (confirmed consumer: projectile-entities' spawn dispatcher `0x021574CC`; also the object hosting physics-writers' `+0x6A` "track-minimum + saturating counter", `0x021607C0`).
- **`+0x1a8`** — MoveInfo pointer. Allocated via `0x02156A38`/`0x02156A58` (size `0x1F0` = 496 bytes) whenever an attack/move starts; installed via setter `0x021570EC`.
  - MoveInfo's own **`+0x10`** field → a scratch sub-object: **`+0x40`** = flags (bit `0x800` gates delta application), **`+0xE8`**/**`+0x130`** = two already-computed signed 32-bit deltas consumed by damage-pipeline's hit-resolution code. The writer of `+0xE8`/`+0x130` was never located across 3 rounds — see spec **B11**.
- **`+0x56c`** — the gauge/Meter struct pointer (see below). This field is confirmed to belong directly to the character struct itself (used by the GDB seed-anchor function `0x020784E4`), so it is **not** subject to the same "sl vs. character struct" ambiguity as `+0x1a4`/`+0x1a8`/`+0x1b4`.

### 2. Gauge / Meter struct

`char+0x56c` → `{+0x16 max (u16), +0x18 current (u16)}`. Accessors: `0x02078488` = `ApplyDeltaToCurrent` (clamped add, `[0, max]`); `0x020784B8` = `GrowMax` (capped at `0x4000`); `0x020784E4` = `IsCurrentBelowPercentOfMax` (the GDB seed anchor; both known callers pass `pct=25`). Trampoline `0x020783CC` tail-jumps into `0x02078488` with `r0` pre-loaded from `+0x56c`. A `+0x558`-rooted linked list (walked by `0x020783DC`) is confirmed to be a **reused, generic "Meter" utility** — the same clamp-accumulator machinery is architecturally reusable for other gauges (guard health, SP) at a different base offset than `+0x56c`. Only 1 of the trampoline's 8 known call sites has been disassembled — see spec **B12**.

### 3. chr_b singleton

`*(0x0214BD80)+0x40`, record stride `0x3C` (60 bytes, matching on-disk `BattleCharacterEntry`). `statA`/`statB`/`statC` at record `+8`/`+0xA`/`+0xC`. Indexed by `charStruct+0x41` = the koma's `PassiveIndex` (0–55), not confirmed identical to chr_b's own on-disk `CharId`. The same singleton also owns koma.bin (`->+0x30`) and 3 other still-unidentified tables (`->+0x44`, `->+0x48`, `->+0x54`).

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
| Guard/block | never traced | A documented "Guard Health" pool likely reuses the CONFIRMED clamp-accumulator gauge (cross-cutting §2) at a different base offset than `+0x56c`. |
| SP gauge & specials | never traced | Same clamp-accumulator family is the leading candidate; zero disassembly evidence located yet. |
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
| **B12** | guard/block, SP gauge | 1 | Sweep the remaining 7 (of 8) trampoline call sites to `0x020783CC` and any sibling trampoline hard-coding an offset other than `+0x56c` into the same clamp-accumulator — cheapest possible unlock of two never-traced targets at once. |
| **B13** | throws/grabs | 2 | Once B11 locates the runtime field offsets, manually read disasm around `hasSpecialFlag`/`hitProperties` bit tests (search-imm cannot find data-processing immediates — a confirmed tooling gap) for a branch that skips normal knockback in favor of a scripted throw outcome. |
| **B14** | weight-hunt (completion) | 2 | Systematically disassemble the ~85 (of ~87) still-unexamined `0x0214BD80` singleton references to build a complete chr_b byte-offset map; specifically check for any getter called from the ov6 hit-resolution path rather than exclusively ov5 menu code. |
| **B15** | support koma / character switch | 2 | Confirm the character constructor's actual caller set (9× reported from `ov8:0x02150392`) and check whether any call path is switch-specific. |
| **B16** | combo scaling | 3 | Find the writer that clears `[sl+0xf8]` (only the *set* site is known) and check for an adjacent hit-count field — a pure boolean cannot express per-hit-number scaling. |

### GDB-first recommendations (from the critic; see `GDB-Validation-Queue.md` for full cards)

1. **Identity check** — break `ov6 0x02158BA8`; compare `r1` against the live `0x023D2A74` pointer chain. Unblocks 4 subsystems at once (cross-cutting §1 / spec B10).
2. **Hitstun-timer init** — break `arm9 0x0207D16C`; confirm/deny against a real hit-landing.
3. **Position-vs-timer conflict** — break `ov4 0x02151E7C`; resolves the pre-existing `+0xA0` conflict in `Character-State-Struct.md`.
4. **Velocity/position fields** — break `ov6 0x02158BB4`/`0x02158BC4`; dump the full `+0x6A`–`0xBA` window of `[sl+0x1b4]` around a real hit.
5. **Combo-scale flag scope** — break `arm9/ov6 0x02158DC4`; watch `[sl+0xf8]` across a full combo and a match reset (can piggyback on recommendation #1's session).

### Tooling gaps (block future static rounds)

- `search-imm` finds load/store immediate *offsets* only — cannot find data-processing immediate *operands* (`mov`/`cmp`/`tst`/`and #imm`). Blocks B13 and any future flag-gated search.
- No register-provenance-aware search exists — only bare immediate-offset text matching, the single biggest false-positive source this campaign (hit at least 3 times independently: hitstun-timers ×2, physics-writers ×1).
- The jpower-indirect div-by-5 sweep used a fixed ARM-only 8-byte lookback and cannot verify it isn't missing a Thumb-mode call site.
- `arm9_tables.json`'s candidate ~74-entry/vtable tables were found by ROM file offset but never translated to RAM addresses, so none could be run through `xrefs-to`.
- `ExportAllCollisions` (the CLI's own batch export command) has never been run against the full roster — see collision-data's open questions.
