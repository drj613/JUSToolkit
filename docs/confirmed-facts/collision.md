# Collision system — DRAFT spec

> **DRAFT — static mining only.** Built from `docs/research/findings/` and beads;
> no new emulator runs. INVENTORY verdict for this subsystem is **partial**
> ([INVENTORY.md §2](INVENTORY.md)): the ColPrm layer is spec-ready, but the
> contact-array semantics, ColMan/ColJoint, and the runtime hitbox parser are open.
> Spec bead: `jus-wayfinder-map-digi.7`.

> **Supersession warning.** The iteration-59 headline "the contact array is NOT
> damage" is superseded and actively misleading: the producer it dismissed *is*
> the damage formula (P208–P211). Do not cite
> [../research/archive/findings/contact-array-is-not-a-damage-ledger.md](../research/archive/findings/contact-array-is-not-a-damage-ledger.md)
> or Battle-Engine-Map §collision-data "Settled (iteration 59)" for a
> "no collision→damage link" conclusion. Same for §hitbox-priority (the
> most-refuted section) and the `0x020924B0` "collision table" (refuted — it keys
> sprite archives).

---

## 1. Architecture: three modules

Collision is three source modules, recovered from assert strings
([collision-is-three-modules.md](../research/findings/collision-is-three-modules.md),
[symbol-names-recovered-from-assert-strings.md](../research/findings/symbol-names-recovered-from-assert-strings.md)):

| module | constructor | mapped? |
|---|---|---|
| `BattleCol.cpp` (ColMan) | `Battle_ColManCreate 0x0207AD3C` | **no** — untouched |
| `BattleColJoint.cpp` | `0x0207BD40` | **no** — untouched |
| `BattleColPrm.cpp` (ColPrmMan) | `Battle_ColPrmManCreate 0x0207C4C0` | yes — this document |

Everything below is the ColPrm layer. Iterations 52–126 mapped only this layer.

## 2. The ColPrm manager (Battle_ColPrmMan)

- **Identity:** the runtime object at `0x0220DDE0` IS Battle_ColPrmMan, settled
  after the P202/P203 retractions
  ([p204-object-is-colprmman.md](../research/findings/p204-object-is-colprmman.md),
  bead `jus-s5q`). Runtime addresses are session-local — re-derive with
  `scripts/find_battle_structs.py`.
- **Allocation:** `Battle_ColPrmManCreate 0x0207C4C0`, size `0xFB54` bytes.
- **Zero unaccounted bytes.** The full tiling
  ([colprm-manager-layout-closed.md](../research/findings/colprm-manager-layout-closed.md),
  [colprm-manager-fully-accounted.md](../research/findings/colprm-manager-fully-accounted.md)):

| offset | contents |
|---|---|
| `+0x28`–`+0xD7` | 22 bucket list heads. Buckets 1 and 8 have **no producer anywhere** (verified against the complete 60k-entry index; [buckets-1-and-8-confirmed-against-complete-index.md](../research/findings/buckets-1-and-8-confirmed-against-complete-index.md)) |
| `+0xE0` | per-frame callback slot; the driver `0x0207F480` is registered here in the ctor at `0x0207C860` ([collision-pipeline-closed.md](../research/findings/collision-pipeline-closed.md)) |
| `+0xFC` | phase table, 19 entries — mostly tiny accessors ([phase-table-is-mostly-tiny-accessors.md](../research/findings/phase-table-is-mostly-tiny-accessors.md)) |
| `+0x14D` | flag byte; **bit 0 is arg2 of the damage formula** `0x020823E4` ([p208](../research/findings/p208-damage-formula-0x020823E4.md)) |
| `+0x154` | contact array: rows stride `0xC0`, elements stride `0x30` (4 per row), indexed by two `mla`s at `0x02081340`/`0x0208134C`; ends exactly at `+0x454` |
| `+0x454` | **128 inline ColPrm records**, stride `0x188` (record size independently confirmed by the manager's own stride) |

## 3. The ColPrm record (0x188 bytes)

One object, three names: the entity constructor's *owner*, the ColObj owner,
and the damage-path *scratch*. 24 fields are mapped across six anchor
functions; the map is explicitly **partial, not the full struct**
([colprm-record-field-map.md](../research/findings/colprm-record-field-map.md) §4 —
unmapped spans `+0x00`–`+0x2C`, `+0x44`–`+0x4C`, `+0x70`–`+0x8C`, and most of
the `+0xA4`–`+0x173` scratch region). Note the distinction: the *manager* is
fully tiled; the *record* is not.

Structural fields:

| offset | what | source |
|---|---|---|
| `+0x08` | list head of `0x2C`-byte pool nodes (the record's own list, distinct from manager `+0x08`) | field map |
| `+0x34` | mutable flag API; `0x800` here is a **pairwise filter**, part of category routing | [record-0x34-is-a-mutable-flag-api-and-0x800-is-category-routing.md](../research/findings/record-0x34-is-a-mutable-flag-api-and-0x800-is-category-routing.md), [bit-0x800-is-a-pairwise-filter-not-an-axis.md](../research/findings/bit-0x800-is-a-pairwise-filter-not-an-axis.md) |
| `+0x38` | category bitmask; bits `0x4000`/`0x8000` pick an axis | [record-0x38-is-a-category-bitmask.md](../research/findings/record-0x38-is-a-category-bitmask.md), [category-mask-confirmed-selects-an-axis.md](../research/findings/category-mask-confirmed-selects-an-axis.md) |
| `+0x40` | flags word, reached from **both** arm9 (installer clears `0x200` at `0x0207CB2C`) and ov6 (damage flush tests `0x800` at `0x02158BA0`) — the cross-binary proof that collision and damage share one object | field map §3 |
| `+0x60` | the ColObj; zeroed by the teardown | field map |
| `+0x68` | object whose `+0x20` list holds this record's bucket nodes; unresolved tension — flagged "vestigial, no writer" vs the formula's live `[r4+0x68]` walk ([record-0x68-is-never-set-second-vestigial-field.md](../research/findings/record-0x68-is-never-set-second-vestigial-field.md)) | field map |
| `+0xA4`–`+0x173` | `0xD0`-byte per-hit scratch region, memset by the installer | field map |

**Damage-side scratch fields** (`+0x40` bits, `+0xE8`, `+0x130`, `+0x140`,
`+0x144`, `+0x175` nature selector, `+0x184`/`+0x186` 8.8 multipliers) are
already specced field-by-field in [damage.md §2.2](damage.md) — that is the
canonical table; this document does not restate it.

## 4. Wiring and loading

- **No standalone registration.** The installer `0x0207C988` is called inside
  the entity constructor `0x020834D4` and returns the owner (a ColPrm record);
  `entity+0x10` = owner = damage scratch
  ([collision-wired-by-the-entity-constructor.md](../research/findings/collision-wired-by-the-entity-constructor.md),
  [entity-0x10-is-the-colobj-owner-and-the-damage-scratch-object.md](../research/findings/entity-0x10-is-the-colobj-owner-and-the-damage-scratch-object.md)).
- **Authoring data loader:** `Battle_PrmDataInit 0x021702BC` loads `chr/col/`,
  `chr/shot/`, `chr/effect/`; prmData pointer at `char+0x84`, collision array at
  `prmData+0x00`
  ([prmdatainit-is-the-collision-loader.md](../research/findings/prmdatainit-is-the-collision-loader.md),
  [prmdata-at-char-0x84...](../research/findings/prmdata-at-char-0x84-and-why-offset-scans-cannot-find-the-walker.md)).
- **On-disk format:** 281 collision files in `ChrBin.aar`, 20-byte record
  stride, 2837 records total. Full-roster facts: hitModifier is *not*
  constant, damageFlags==0 in 46.86% of records, projectileId spans −34..36
  ([collision-data-extracted.md](../research/findings/collision-data-extracted.md)).
  Round-1 claims (−32 sentinel, constant hitModifier, one terminator per file,
  knockback monotonicity) are all broken — use only the full-roster numbers.
- damageFlags is the damage gates' class index (bead
  `jus-class-index-is-damageflags-mx5`); damageFlags→jpower is two systems
  (10 direct, 64 indirect) per
  [DamageFlags-Character-Classification.md](../research/DamageFlags-Character-Classification.md) —
  **unverified prose**, treat per the README rule.

## 5. The per-frame pipeline

Driver `0x0207F480` (440 instructions), registered on manager `+0xE0`
([collision-pipeline-closed.md](../research/findings/collision-pipeline-closed.md),
[driver-is-the-primary-bucket-filler.md](../research/findings/driver-is-the-primary-bucket-filler.md)):

- Drains the buckets and is also their **primary filler**; runs an 8-stage
  pipeline via forwarder `0x02080C28` → `0x02080F14`.
- The narrowphase pair test **is the damage formula** `0x020823E4`
  ([narrowphase-pair-test.md](../research/findings/narrowphase-pair-test.md)) —
  collision does not hand off to a separate damage step; the pair test computes it.
- Results accumulate into the contact array at `manager+0x154` via four RMW
  blocks at `0x02081340`–`0x02081418`
  ([contact-array-writer-found.md](../research/findings/contact-array-writer-found.md)).

## 6. Bit 11: the collision-resolution damage-pending flag

Confirmed
([p187-scratch-0x40-flag-word-and-arm9-collision.md](../research/findings/p187-scratch-0x40-flag-word-and-arm9-collision.md)):

- `scratch+0x40` is a bitfield; the ov6 damage flush gates on **bit 11
  (`0x800`, damage pending)** at `0x02158BA0` before reading the amount at
  `+0xE8`. Bit-11 semantics are ESTABLISHED (the flush reads it live).
- Known bits: 11 (damage pending), 25 and 30 (three-instruction setters
  `0x021591F4`/`0x02159210`, cleared by the expiry handler; bit 30 also
  forces the nature factor to 1.0, see damage.md).
- A static setter exists in arm9 collision resolution: `0x02081DDC` (992
  bytes, one caller) ORs `0x800` onto **both** participants' scratches at
  `0x02081ED0`/`0x02081EE0`, deriving the scratch via `[[participant+0x1C]+0xC]`.
- **However**, the runtime card was rejected: `0x02081ED0`/`0x02081EE0` never
  execute on a landed hit (control fired, card did not — bead `jus-x6j`). So
  bit 11's *semantics* are confirmed, but its live setter on a landed hit is
  still unidentified (see GAPS). 7 of the 12 `orr 0x800` sites sit in
  overlays that were never resolved — unchecked, not clear (P187).

---

## GAPS — settle-or-waive candidates for reimplementation

Each item: what's missing, what an implementer would have to invent if we
waive it, and how risky that invention is.

### G1. The runtime hitbox parser — never found (settle-or-waive)

No code that walks the 20-byte on-disk CollisionEntry records at hit-test time
was ever located; no hitTier/hitProperties comparison exists anywhere in the
searched listings. The ARM/Thumb disassembly bug (`ov6.txt` decodes Thumb as
ARM; ~89% of Thumb literal loads invisible) is a *sufficient excuse* for the
null, not evidence of absence (INVENTORY §2 open Q2).
**If waived, invent:** the entire mapping from authored 20-byte records to the
live ColPrm record fields — which columns become position/extent, how records
are selected per animation frame, and what hitTier/hitProperties do at contact
time. **Risk: high.** This is the front half of the system; a wrong guess here
changes which hits connect at all. Frame-data caveat compounds it: collision
`frameStart` ≠ in-game startup (offset −3..+5,
[frame-data-hitbox-notes.txt](../research/frame-data-hitbox-notes.txt)).
Recommendation: **settle** (re-run the search on a correct Thumb listing
before waiving).

### G2. ColMan and ColJoint — untouched layers (settle-or-waive)

Two of the three modules (`Battle_ColManCreate 0x0207AD3C`, ColJoint
`0x0207BD40`, ColJoint manager `*(0x0214BE0C)`) have no field map at all.
**If waived, invent:** whatever these layers do — plausibly world/terrain
collision (walls, floors, panel boundaries) and joint/attachment collision.
**Risk: medium.** The damage path demonstrably runs entirely through ColPrm,
so combat damage may not need them; but movement/terrain response would be
invented from black-box behavior. A cheap partial settle: run the constructor
map (guards 8/9/13) on the two ctors to at least size and skeleton them.

### G3. The `+0x48` list insert — 644-hit sweep null (settle-or-waive)

No list insert into element `+0x48` exists as an **immediate-offset** word
store anywhere in arm9 or the overlays (644 hits examined, control passing;
[p205-no-immediate-offset-list-insert.md](../research/findings/p205-no-immediate-offset-list-insert.md)).
`+0x48`/`+0x4C` are cleared as a pair by the pipeline's caller at `0x0207F87C`
(head/tail reading), and stage 1 runs an accumulator on a *numeric* `+0x48` at
`0x020812F4` — but the insert itself is only reachable through a computed or
register offset (same blind-spot class as the `+0xA4` term writer).
**If waived, invent:** how contacts are queued between pipeline stages — order,
capacity, and dedup of the per-frame hit list. **Risk: medium.** Ordering
affects multi-hit moves and simultaneous-hit resolution; a naive
append-in-scan-order queue may be behaviorally close but is a guess.

### G4. Phase tables and pipeline attribution (settle-or-waive)

The manager's 19-entry phase table at `+0xFC` is "mostly tiny accessors"
([phase-table-is-mostly-tiny-accessors.md](../research/findings/phase-table-is-mostly-tiny-accessors.md);
the phase interface passes a `0x10` struct,
[phase-interface-passes-a-0x10-struct.md](../research/findings/phase-interface-passes-a-0x10-struct.md)),
but pipeline stages 4–7 are unattributed, 13 of 22 buckets are unassigned, and
buckets 1/8 are dead-or-hidden. **If waived, invent:** the meaning of most
bucket categories (which entity kinds go where) and what half the pipeline
does per frame. **Risk: low-to-medium.** The load-bearing stages (bucket fill,
narrowphase = damage formula, contact accumulation) are already attributed;
the rest may be culling/bookkeeping a reimplementation can restructure freely.
Buckets 1/8 with zero producers are a plausible waive (dead code).

### G5. Contact-array element semantics (settle-or-waive; INVENTORY's highest-value question)

The four element magnitudes at `+0x04/+0x08/+0x0C/+0x10` of each `0x30`-byte
contact element are unexplained — is this the damage staging area between the
formula and the HP flush? This is entangled with damage open question 5 (the
B11 residue: how formula output reaches `scratch+0xE8`/`+0x130`, open since
iteration 75). **If waived, invent:** the hand-off buffer between hit
detection and HP application — per-hit vs per-frame aggregation, and multi-hit
accounting. **Risk: high** for multi-hit correctness (the `jus-f30` lesson was
exactly "extra damage *events*";
the taint bead `jus-f30` is tainted — do not cite it as a number source). Recommendation: **settle**; it also closes
G6.

### G6. Who sets bit 11 on a landed hit (settle)

Semantics confirmed (§6), but the only located setter never executes on a
landed hit (bead `jus-x6j`), and 7 of 12 `orr 0x800` sites are in unresolved
overlays. **If waived, invent:** the trigger condition for "this contact
becomes damage this frame". **Risk: high** — this is the collision→damage
edge itself. Cheap settle path: resolve the 7 unchecked overlay sites
statically before any emulator work.

### G7. Collision↔jpower join key (waive-leaning)

isTerminator as a per-move sub-list delimiter is untested (INVENTORY §2 open
Q5); jpower entry selection for damageFlags==0 is open (`JUS-9lp.1`).
**If waived, invent:** the record-to-move grouping inside each collision file.
**Risk: low-to-medium** — it's a data-pipeline question answerable later by
cross-referencing extracted data ([collision-data-extracted.md](../research/findings/collision-data-extracted.md))
against measured move damage, without touching the binary.
