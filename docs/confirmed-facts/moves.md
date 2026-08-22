# JUS move system — confirmed facts (DRAFT)

> **DRAFT.** Bead: `jus-wayfinder-map-digi.8`. Compiled 2026-08-21 by static mining of
> `docs/research/` only — no emulator runs. The move system's inventory verdict is
> **partial** (`docs/confirmed-facts/INVENTORY.md` §3): the MoveMan and NoteTrack
> structures are solid, but priority resolution and the move-script system are
> unsolved. Treat every gap in §7 as a settle-or-waive candidate before this
> graduates from draft.

For the move-data block the damage formula reads (`[elem+0x10]`: base damage,
class byte, flags), see `docs/confirmed-facts/damage.md` §2 — that element is the
*collision* hit element, a different object from the MoveMan element below.

---

## 1. MoveMan (the move manager)

Source: `docs/research/findings/movman-owns-two-notetracks-and-dead-init.md`.

- `Battle_MoveManCreate` is at **`0x02082A38`** (408 bytes, `BattleMove.cpp`).
  The `0x02082A50` address in older docs is the allocation site inside it, not
  the function start.
- Object size **`0x2648`** bytes — one of the largest battle allocations.
- Sole caller: `0x02083204` (`Battle_ObjManCreate`).

| offset | what | status |
|---|---|---|
| `+0x00`–`+0x1C` | eight words cleared individually — dead code, wiped by a whole-object memset | CONFIRMED_STATIC |
| `+0x00` / `+0x08` | element active list / free list heads (see §2) | CONFIRMED_STATIC |
| `+0x20` | NoteTrack handle A, id `0xA1000`, callback `0x02082E10` | CONFIRMED_STATIC |
| `+0x24` | NoteTrack handle B, id `0xA6000`, callback `0x0208317C` | CONFIRMED_STATIC |
| `+0x2C` | halfword = `0x29` | CONFIRMED_STATIC |
| `+0x48`–`+0x647` | 128 × `0xC` link records (intended layout, from the dead init loop) | CONFIRMED_STATIC |
| `+0x648`–`+0x2647` | `0x2000` bytes; tiles exactly as **128 elements × `0x40`**, but no code computes `base + i*0x40` — the region is reached by pointer through `node+0x8` | PLAUSIBLE (stride) |

Notes:

- **Half the constructor is dead.** The field clears and the 128-iteration loop
  are followed unconditionally by `memset(obj, 0, 0x2648)`; the dead loop still
  documents the intended `+0x48` array. On allocation failure the code jumps
  into the memset with `r4 = 0` — `memset(NULL, 0, 0x2648)`.
- The two NoteTracks are built by the same six-step factory pattern
  (`Battle_NoteTrackCreate 0x02026F94`, id call `0x02012940`, vtable-`0x24`
  self-registration) that ColPrm uses for its two (ids `0xA5000`/`0xA0000`) —
  independent corroboration in an unrelated manager.
- The per-frame consumer of the element region is a **frame snapshot pass**
  (copy current → previous, derive status bits), reached through the `0xC`
  link nodes, not by stride arithmetic
  (`findings/movman-two-parallel-arrays-and-the-frame-snapshot.md`).

## 2. MoveMan element lifecycle

Sources: `findings/movman-element-allocator-and-the-0x3E-field.md` (one section
carries a REFUTED banner — the corrected reading is below),
`findings/element-0x0C-is-the-owners-world-position.md`,
`findings/the-snapshot-suppressor-is-the-reposition-function.md`.

**Allocator `0x02082C34`** (248 bytes, `BattleMove.cpp`):

- Fixed-capacity recycler: free list at `container+0x08`, active list at
  `container+0x00`, unlink/link via the shared list library; returns **NULL
  gracefully on exhaustion** (`cmp r4,#0; moveq r0,#0; popeq`).
- **Sole caller is the ColObj installer `0x0207C988`** (call at `0x0207CA08`) —
  a direct `BattleCol.cpp` → `BattleMove.cpp` dependency. Collision setup
  allocates the move element; the container pointer lives at
  `[installer_arg0+0xF0]`. The element is later reachable from the ColPrm
  record at `record+0x5C`.

Element fields (allocation-time init; size ≥ `0x3F`, stride `0x40` PLAUSIBLE):

| offset | meaning | status |
|---|---|---|
| `+0x08` | owner (allocator arg1) | CONFIRMED_STATIC |
| `+0x0C`/`+0x10` | owner's **world position** x/y, read from the transform node `[[owner+4]+0x50]` `+0x0C/+0x10`, `asr #4`; default `0x10000` when no owner position is passed | CONFIRMED_STATIC |
| `+0x14`/`+0x18` | previous-frame snapshot of `+0x0C`/`+0x10` — the allocator copies current→previous on every branch | CONFIRMED_STATIC |
| `+0x34` | flags word. Set at alloc: bit `0x1` always, `0x200` if `[container+0x28]&1`, `0x8` before return. Bit **`0x100` = snapshot suppressor**, set only by the reposition function `0x020804E8` (skip one prev-snapshot after a teleport-style move). Bit `0x200` is cleared on projectile attach, and `0x0207EF1C` ORs `0x800` into it (this is the *element's* flags, not the ColPrm record's — a corrected aliasing trap) | CONFIRMED_STATIC |
| `+0x3C`/`+0x3D`/`+0x3E` | init `0x20`, `8`, `0x20` — meaning unknown; `+0x3E` proves the element reaches at least `0x3F` bytes | CONFIRMED_STATIC (values) |

## 3. NoteTrack (the note/script track)

Source: `findings/notetrack-struct-mapped.md`;
commands: `findings/notetrack-issues-the-commands-b11-dead-end.md`,
`findings/commands-are-predicates.md`.

`0xA8`-byte object. The character's own track is constructed into
`[char+0x1a8]+0x18` by `Battle_CharaCreate`; MoveMan owns two more (§1); ColPrm
owns two. Which consumer drives which track is **not established**.

```
+0x00 .. +0x6F   note slot array: 7 slots x 16 bytes
                   slot +0x00  kind (0..16)
                   slot +0x01  ExtFlags       (-1 = empty sentinel)
                   slot +0x02  ProjectileId
                   slot +0x04  u16 counter    (ticked down by the forwarder)
+0x70   command callback = 0x02157A44 (the 73-case dispatcher)
+0x74   the character (passed as r1 to the callback)
+0x7C, +0x80, +0x84, +0x88   four pointer fields, each backing a query (§3.2)
+0x8C   object from Battle_NoteTrackCreate's 0x02026F94 call (self-registers)
+0x90..+0xA3   small counters/flags, reset to 0 or -1
```

### 3.1 The 17→7 slot overwrite — SPEC-CRITICAL

The kind→slot table at **`0x021710A8`** maps **17 note kinds onto 7 slots
(0..6)**. Slots are **buckets, not a queue**: issuing a note writes its bucket
and **overwrites** whatever note of a sibling kind was there. Slot 2 collects
kinds **6, 7, 8, 9, 10, 14, 15** — those seven kinds are mutually exclusive at
runtime. The 7-slot count is doubly derived: the reset loop iterates exactly 7
times at stride `0x10`, and the data table uses exactly 7 distinct slots. A
reimplementation that queues notes, or that gives each kind its own slot, is
wrong. (`findings/notetrack-struct-mapped.md` §2; INVENTORY §3 flags this as
the spec-critical fact.)

The kind constants come from an accessor bank (ov6 `0x02155900`–`0x02156900`):
31 stubs pass hardcoded kinds 0..16 to a shared factory `0x021565A4`, which
builds the 16-byte slot records; kinds 8 and 14 copy the collision record's
`ProjectileId` verbatim into slot `+0x02`
(`Battle-Engine-Map.md` §hitbox-priority open-questions addendum, 2026-08-15).

### 3.2 Commands are predicates

Every command the NoteTrack issues through the dispatcher is in
**{3, 64–73}**. The seven live 64–73 cases are **boolean predicates** — they
mutate nothing; the forwarder advances the note only when the answer is true
(`cmp r0,#0; ldrbne/strbne`). Command 3 is the one fire-and-forget action
(result discarded). Commands **23/24 (HP/SP apply) are never issued** by any
caller — the dispatcher's HP route is dead from this direction, which is why
B11 (who writes the staged damage) could not be solved through NoteTracks.
Notable predicate: query 71 walks a global entity table (strides
`0xC0`/`0x30`), skipping self — **move scripts gate on other characters'
states**.

## 4. Walk speed

Sources: `ARM9-Research-Guide.md` §"Walk Speed (PARTIALLY SOLVED)",
`chr_b-Complete-Mapping.md` ("Walk speed IS in chr_b.bin"),
`Battle-Engine-Map.md` (statC consumer note), ticket `JUS-n3p`.

- Walk speed is authored in **`chr_b.bin` `statC`** (offset 12, 2 bytes) as a
  **threshold/tier system, not linear**: statC below ~100 → slow tier, at or
  above ~100 → normal/fast tier. Proof of non-linearity: Lenalee (153) and
  Killua (300) walk at the same speed; 16 battle characters fall in the slow
  tier.
- Confounder on record: **Edajima** has normal statC but is slowed by an innate
  passive — the earlier "walk speed is not in chr_b" conclusion came from him
  and was retracted.
- statC is meaningful only for battle characters (supports have high statC and
  never walk); `statA`/`statB` are series-grouped values, not physics;
  battleParams bytes 0–7 are **not** weight.
- **The runtime consumer is unresolved.** The only located raw-statC reader
  (`0x020771C4`, caller `0x0215A31C`) is a koma-technique eligibility check,
  not a speed selector; the tier threshold cmp-chain was never found
  (`Battle-Engine-Map.md` L330; GDB-Validation-Queue item 18). Exact
  thresholds (~95–100) and tier count > 2 are open (`JUS-n3p`).

## 5. Per-move damage table — Goku only

Source: `../research/archive/Move-Damage-Table-Goku.md`. **Limitation: single-character coverage** —
this table exists for Goku (`chr_b[0]`) vs コマレッド (`chr_b[70]`, no
abilities) only; no other character has a measured move table.

Three caveats stack on the numbers; read them before citing any row:

1. **Auto-heal offset** (the doc's own banner): measured with 自動回復 ON, so
   each value is net of one +2.0 regen frame. Neutral B was re-verified
   heal-off at **8.000** (not the tabulated 6.0); other single-hit rows are
   *inferred* `listed + 2.0`, not measured.
2. **Taint window**: measured 2026-08-14, inside the `jus-f30` (state:tainted)
   window — stage gimmick ON; do not cite these numbers as clean. Owner ground truth narrows this to *extra damage events*, not
   inflated magnitudes — values can be un-tainted individually.
3. **Button labels are wrong** (`jus-hbmn`, owner ground truth): B is light
   attacks, **Y is heavy, X is specials**, and Goku's only multi-hit B move is
   up+B. The table's "A is jump, B is attack" framing and its input column
   need re-labeling before reuse. Also: a runtime owner-match measured
   forward-Y at **3.750 × 22 hits, zero variance** (`jus-pzrw`), which
   contradicts the table's `+2.0` inference for that move (5.000 × 0.75 =
   3.750 fits the *uncorrected* row) — and 3.750 is degenerate between
   base 5 × 0.75 and base 3 × 1.5, so the mechanism is deliberately unnamed.

What survives the caveats as confirmed:

- **up+B and Y are multi-hit strings** (small per-hit values) — any move table
  must distinguish per-hit from per-string damage.
- **back+B resolves to neutral B** (pressing away turns the character).
- **Direct-hit damage is a whole number of displayed HP** (raw multiples of
  64); the one fractional raw value (80) was bench/splash damage, a different
  mechanic. The older "×16 quarter-HP quantum" generalisation is retracted.
- How the base bytes become displayed damage is the damage spec's job:
  `docs/confirmed-facts/damage.md` (base byte, ±25% gates, additive nature).

Startup frames: collision-file `frameStart` ≠ in-game startup (offset −3..+5
across 5 characters, manual video ±2–3 frames) — real startup likely lives in
animation data or the jpower extra section `0x80–0x12F`
(`frame-data-hitbox-notes.txt`).

## 6. Refuted hypotheses — do not resurrect

| Hypothesis | Verdict | Source |
|---|---|---|
| NoteTrack "commands" 64–73 mutate the character | REFUTED — all seven live cases are boolean predicates | `findings/commands-are-predicates.md` |
| A NoteTrack can hold more than 7 active notes / notes queue | REFUTED — fixed 7-slot array, bucketed by kind, overwrite | `findings/notetrack-struct-mapped.md` |
| Commands 23/24 (HP/SP) are issued through the NoteTrack | REFUTED — no caller passes 23 or 24 | `findings/notetrack-issues-the-commands-b11-dead-end.md` |
| Element `+0x0C`/`+0x10` are a 16.16 scale/rate pair | REFUTED — they are the owner's world position (`asr #4`); `0x10000` is a default position | `findings/element-0x0C-is-the-owners-world-position.md` |
| The element allocator sets the `0x100` snapshot-suppressor bit | REFUTED — it is set only by the reposition function `0x020804E8` | `findings/the-snapshot-suppressor-is-the-reposition-function.md` |
| `0x0207EF1C` is a second writer of ColPrm `record+0x34` | REFUTED — it writes the *element's* `+0x34` via `record+0x5C` | same |
| `Battle_MoveManCreate` starts at `0x02082A50` | REFUTED — that is the allocation site; function is `0x02082A38` | `findings/movman-owns-two-notetracks-and-dead-init.md` |
| `0x020924B0` is a collision-file pointer table (and its 6-bit id = chr_b `classId`) | REFUTED — it is a `{char-ID string, packed word}` table; consumer is sprite-archive/credits; classId range 256–684 can't fit 6 bits | `Battle-Engine-Map.md` §hitbox-priority refuted list; corrections in `ARM9-Research-Guide.md` |
| The NoteTrack `+0x84` reads are `character+0x84` (prmData) | REFUTED — different object, `NoteTrack+0x84` | `findings/commands-are-predicates.md` §3 |
| Walk speed is not in chr_b.bin | RETRACTED — it is (statC); Edajima's passive was the confounder | `chr_b-Complete-Mapping.md` |
| Damage authored in quarter-HP units ×16 | RETRACTED — direct-hit quantum is 64 (whole displayed HP) | `../research/archive/Move-Damage-Table-Goku.md` |
| "A is jump, B is attack" control mapping as tabulated | Contradicted by owner — B light, Y heavy, X specials | bead `jus-hbmn` |
| Three failed hitbox-priority search rounds prove the code is absent | REFUTED — they searched an ARM-decoded Thumb listing; absence there is not evidence | `Battle-Engine-Map.md` §hitbox-priority round-2 banner |

## 7. GAPS — settle-or-waive candidates

1. **Priority / clash resolution** — the most-refuted subsystem
   (`Battle-Engine-Map.md` §hitbox-priority). No two-entity
   hitTier/hitProperties comparison found anywhere; the runtime collision
   walker (the code that reads the 20-byte records at hit-test time) is
   unlocated. Best lead: the callers of the ov6 accessor bank / the 68-entry
   function-pointer table, now that `thumb_dis.py` makes the region readable.
   Settle (one targeted static pass over the Thumb region) or waive and spec
   priority as opaque.
2. **The move-script system** — the dream-attack / chain-multiplier home has
   never been located. NoteTracks are the closest thing found (predicates
   gating note advancement), but who *authors* the note sequences, and the
   fixed 32.0 scripted damage at Thumb `0x021518D6`, are open. Settle or
   waive.
3. **Per-character damage tables beyond Goku** — §5 covers one attacker vs one
   dummy. Static route exists (jpower `+0x0C` damage1 + tier, see
   `damage.md`), but the mapping "which jpower entries does character X's
   moveset actually use" is open (`chr_b-Complete-Mapping.md`: shared blocks
   are "template libraries, not complete movesets"). Settle via the jpower
   join or waive per-move tables entirely.
4. Element **stride `0x40`** — PLAUSIBLE only; one RAM read of two adjacent
   elements settles it (cheap settle).
5. **`MoveMan+0x648`–`+0x2647`** semantics — the frame-snapshot pass is known;
   the rest of the per-element fields are not.
6. **Which consumer drives which of the six NoteTracks** (character, 2×MoveMan,
   2×ColPrm) and what the id space `0xA0000`–`0xA6000` keys.
7. **Walk-speed tier thresholds and runtime consumer** (`JUS-n3p`, GDB queue
   item 18) — cheap to settle with one runtime capture; otherwise spec the
   two-tier ~100 threshold with an "approximate" flag.
8. **Goku table re-measurement** heal-off, gimmick-off, with corrected button
   labels (`jus-hbmn`; `jus-f0v` tracks the re-run because the original proof
   is state:tainted — do not cite it as support) — prerequisite for using §5 numbers in a
   spec.
