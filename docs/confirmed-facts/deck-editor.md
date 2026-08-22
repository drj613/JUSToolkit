# Deck Editor — Confirmed Facts

Canonical spec for reimplementing the JUS deck editor without the original code.
Every claim cites its source. Items still unproven are marked **OPEN**.

Sources are in `docs/research/` unless noted. Claim beads cited as `[jus-...]`.

---

## 1. The deck model

A deck is a **5-column x 4-row grid** (20 cells) onto which panels ("koma") are
placed. Confirmed three independent ways: the placement validator rejects
`col >= 5` / `row >= 4` with a `row*5` stride; the battle-side adjacency gate
bounds `x < 5, y < 4`; and the owner observed the grid in live play
(`[jus-koma-shape-is-a-20bit-bitmap-423]`, `findings/p225-koma-adjacency-grants-abilities.md`,
`Deck-System.md`).

Panel classes, perfectly determined by cell count with zero exceptions across
all 890 koma (`findings/koma-format-decoded.md`):

| Size (cells) | Type | Count in koma.bin |
|---|---|---|
| 1 | Helper (passive) | 312 |
| 2–3 | Support (support attack) | 188 + 184 |
| 4–8 | Battle (playable fighter) | 62+61+55+16+12 |

Every one of the game's 312 characters has exactly one 1-cell helper
(`findings/koma-format-decoded.md`).

A valid deck additionally needs a **leader sticker** on a battle koma; without
it the editor refuses to exit with 「リーダーが居ません…」 (`Deck-Editor-Automated.md`).

---

## 2. On-disk data the editor consumes

### 2.1 koma.bin — the panel catalogue

890 records x 12 bytes (`findings/koma-format-decoded.md`):

| Off | Type | Field | Status | Meaning |
|---|---|---|---|---|
| 0x0 | u16 | imageId | CONFIRMED | 0..889, always equals record index (redundant) |
| 0x2 | u16 | characterId | CONFIRMED | 1..312 |
| 0x4 | u8 | seriesIdx | CONFIRMED | 1..42, indexes the series name table (ARM9 ptrs at 0x0209E840) |
| 0x5 | u8 | panelOrdinal | CONFIRMED | 0-based panel number within the character; (seriesIdx, panelOrdinal) is unique across all 890 records |
| 0x6 | u8 | panelType | CONFIRMED | 0=Battle, 1=Support, 2=Helper; redundant with size |
| 0x7 | u8 | abilityId | PLAUSIBLE | For battle panels indexes chr_b.bin (74 distinct values = 74 chr_b entries); helpers 0..55; supports 0..192 |
| 0x8 | u8 | kShapeGroupId | CONFIRMED | **size = value + 1** |
| 0x9 | u8 | kShapeElementId | CONFIRMED | which shape of that size |
| 0xA | u8 | unkA | **OPEN** | 0..8, always <= size |
| 0xB | u8 | flags | PLAUSIBLE | bit 0x10 ~ "primary variant"; **not** nature |

**Nature is not stored in koma.bin at all** — Naruto's size-2 (Laughter) and
size-3 (Power) panels are byte-identical in every candidate field. Where the
editor's per-panel nature display comes from is **OPEN**; best candidate is a
parallel table (piece.bin is variable-length, not a 890-stride table)
(`findings/koma-format-decoded.md`).

### 2.2 kshape.bin — the shape catalogue

1648 bytes (`findings/koma-format-decoded.md`, `findings/p229-koma-shapes-come-from-kshape-bin.md`):

- Header: `int32 groupStart[8]` = (0,1,3,9,21,35,49,62), then
  `int32 numElements[8]` = (1,2,6,12,14,14,13,4), sum 66.
- Then 66 entries of 24 bytes at base 0x40: a **20-byte cell map over the 5x4
  grid** (0 = empty; nonzero = occupied, value-1 = tileset index) plus a
  trailing word that includes the packed **20-bit shape bitmap** (matches the
  runtime shape word, section 4.1).
- Lookup: `entry = groupStart[kShapeGroupId] + kShapeElementId`.
- Group g always has exactly g+1 occupied cells — so the group IS size-1.
- Sizes 1–3 are the complete polyomino sets; sizes 4+ are hand-picked subsets
  (e.g. 12 of 19 tetrominoes). Independently confirmed: the editor's size-5
  shape filter shows 13 options, matching the 13 shapes koma.bin actually uses.

An earlier record base of 0x54 was wrong and retracted; 0x40 is current
(`findings/p229-koma-shapes-come-from-kshape-bin.md`, correction sections).

---

## 3. Overlay residency — which code runs where

ARM9 overlays 0–9 share load address 0x0214CD20, so only one is resident at a
time (`Overlay-Residency-By-Mode.md`).

| Screen | Resident at 0x0214CD20 | Source files (modules.json) |
|---|---|---|
| Deck select list (デッキセレクト) | **ov01** (99.6% RAM match) | DeckSelect.cpp, StageSelect.cpp, RuleSelect.cpp |
| Deck editor (KomaEdit) | **ov05** (99.5% RAM match) | DeckMake.cpp, KomaList.cpp, KomaEdit.cpp, KomaState.cpp, KomaHelp.cpp, KomaIBook.cpp, Database.cpp, JPower.cpp |
| Battle | ov06 | — |

Measured byte-for-byte against live RAM, with the symbol table agreeing
independently (`Overlay-Residency-Deck-Screens.md`). An earlier "ov01 is the
editor" reading was a mislabeled screen — it had measured the deck *list*, not
the editor. ov10 (WiFi) and ov12 (ALWidget/ALTextDS UI library) are resident on
both deck screens; ov12 is resident in battle too, partially overwritten from
the low end.

**Ownership:** of the 55 functions holding the deck global, 37 are in ov5
(KomaList/KomaEdit/KomaState/DeckMake/DatabasePersonal), 16 in arm9, 1 in ov6,
1 in ov11. The deck structure belongs to the editor; battle code touches it
once (`findings/deck-global-holders-and-a-fourth-mask-bug.md`). The core
validators and add-entry live in **arm9** (always resident), so the editor UI
in ov5 drives shared arm9 deck logic.

**Consequence for reimplementers:** anything the editor computes at 0x0214CD20
addresses (e.g. the ov05 nature resolver at 0x0214E480) is unreachable in
battle — the editor's derived values must be treated as display/deck-bonus
logic, not battle logic (`Overlay-Residency-Deck-Screens.md`).

---

## 4. The deck in memory

### 4.1 The ComicDeck block

Global holder at **[0x0214BD80]** points to a **0x1914-byte** block, `memset`
to zero at creation (`findings/deck-validators-and-the-id-table.md`,
`findings/shared-encoding-decoders-and-the-zeroed-deck.md`). Known fields:

| Offset | Field | Source |
|---|---|---|
| +0x30 | ID table base — 0xC-byte entries (the koma.bin record shape) | lookup fn 0x02076C98 |
| +0x38 | second table base, stride 0x18 (the kshape record shape), indexed via signed bytes at record +0x8/+0x9 | fn 0x02076D00 |
| +0x18EC | entry count for the ID table | fn 0x02076C98 |
| +0x558 | active node list head | add-entry 0x02076E38 |
| +0x560 | free node list head | add-entry 0x02076E38 |
| +0x568 | **20-bit occupancy mask** of the placed page | validator 0x02076D30 |

**OPEN:** no writer of +0x30 or +0x18EC was ever found despite an exhaustive
sweep of every store form among all 72 deck-pointer holders
(`findings/shared-encoding-decoders-and-the-zeroed-deck.md`,
`findings/dead-deck-residual-closed.md`). Either the tables are filled through
an unattributed path or this arm9 add-entry path is dead in practice
(`findings/deck-add-entry-path-is-dead.md` — see that file before assuming the
path is live).

### 4.2 Deck nodes

Each placed koma is a **0x50-byte node** moved from the free list (+0x560) to
the active list (+0x558) (`findings/deck-add-entry-contract.md`,
`findings/the-0x50-deck-node-mapped.md`):

| Offset | Field |
|---|---|
| +0x00 | next pointer |
| +0x0C | u16 koma ID (init -1); zeroed 4 bytes then ID written on fill |
| +0x0E | packed cell: low nibble = column, high nibble = row |
| +0x0F | low nibble = helper direction, 1..4 (see 5.4); bit 0x10 gates a halving in a battle walker |
| +0x10..0x31 | memset to 0 on fill (0x22 bytes) |
| +0x16 / +0x18 | signed source / destination halfwords (battle-side walker halves +0x16 into +0x18) |
| +0x34 | pointer to the koma data record (first halfword = ID; used by the duplicate check) |
| +0x3C | flags word |
| +0x40 | non-zero = skip node |
| +0x41 | ability ID (read by the adjacency granter) |

### 4.3 Save-region and runtime addresses (from GDB dumps)

From `Deck-Memory-Structure.md` (GDB dump diffs; treat as measured-once):

| Address | Meaning |
|---|---|
| 0x020A0C00–0x020B0000 | Deck-state region (the RAM oracle, section 6) |
| 0x020A0C98 | deck state flag; bit 1 = "no leader" (0x05 with leader, 0x07 without) |
| 0x020A1000–0x020A3000 | **pointer arrays, not raw koma IDs** — scanning for ID byte patterns here gives false positives |
| 0x020A2289 | leader boolean (1 = leader set) |
| 0x020A4368 | pointer to the leader koma's runtime data (0 when no leader) |
| 0x020AFEB4 | active deck slot index (0–7) |
| 0x020B0BAC | koma unlock bitmask |
| 0x020B9480 | koma master table in the save region: sequential u32 koma IDs; per-character sizes step by 0x0C (e.g. Eve: 1-koma 0x1DB0 … 4-koma 0x1DD4) |

**OPEN:** how these save-region structures map onto the ComicDeck block's ID
table (+0x30) has not been established. The relation between deck+0x568 (the
occupancy mask) and battleObj+0x558 (the battle node list head) is also just an
adjacent-looking pair of offsets in different structures, nothing more
(`[jus-koma-shape-is-a-20bit-bitmap-423]`).

---

## 5. Placement rules

### 5.1 Shapes are 20-bit polyomino bitmaps

The shape word at `shapeObject+0x14` is a 20-bit bitmap of the 5x4 grid: bits
0–4 = row 0, 5–9 = row 1, 10–14 = row 2, 15–19 = row 3
(`[jus-koma-shape-is-a-20bit-bitmap-423]`, arm9 0x02076D30). **OPEN:** the
identity of "shapeObject" (what 0x02076D00 returns) — the word is at +0x14 of
whatever that lookup yields, which reads deck+0x38 with stride 0x18, i.e. the
kshape-derived table.

### 5.2 The placement validator — arm9 `0x02076D30(deck, id, col, row)`

Reject in order (`[jus-koma-shape-is-a-20bit-bitmap-423]`,
`findings/deck-validators-and-the-id-table.md`):

1. `col >= 5` or `row >= 4`.
2. ID fails the bounds-checked lookup `0x02076C98` (rejects -1, negative,
   `id >= [deck+0x18EC]`; else returns `[deck+0x30] + id*0xC`).
3. **Width check:** OR the shape word's four 5-bit row fields into a column
   profile, shift left by `col`; if anything escapes the low 5 bits the shape
   would wrap a row edge — reject.
4. Shift the whole 20-bit shape by `col + row*5`; if any bit >= 20 sets
   (spills off the bottom of the grid) — reject.
5. If the shifted shape overlaps the deck's occupancy mask `[deck+0x568]` —
   reject.
6. Otherwise return the shifted shape mask (the caller ORs it into occupancy).

### 5.3 Add-entry — arm9 `0x02076E38(slot, id, col, row, …)`

Error codes in the top nibble (`findings/deck-add-entry-contract.md`):

| Condition | Return |
|---|---|
| free list [slot+0x560] empty | 0x20000000 |
| an active node already has this ID (no duplicate koma in a deck) | 0x40000000 |
| validator 0x02076D30 returns 0 | 0x10000000 |
| success | node unlinked from free list, linked to active list, ID at +0x0C, `(col & 0xF) | (row << 4)` at +0x0E |

### 5.4 Helper direction and adjacency abilities

Helpers point at a neighbour. Node +0x0F low nibble holds a direction 1..4
mapping through the table at arm9 0x02092E34 to (dy=+1 down, dx=-1 left,
dy=-1 up, dx=+1 right). Gate `0x020779CC` steps one cell from the node's
(col,row), rejects off-grid, reads the pointer in the neighbouring cell of a
5-wide, 4-byte-stride grid, and the caller appends the node's ability ID
(+0x41) to that object — **koma grant abilities by grid adjacency**
(`findings/p225-koma-adjacency-grants-abilities.md`). This matches the owner's
rule that most helpers must point at a specific battle character; the whole-deck
+1 SP helpers are the exception (`Deck-System.md`).

### 5.5 Rules observed in the editor (framebuffer-verified, no code path yet)

From `Deck-Editor-Automated.md`, three identical automated runs accepted by the
game:

- **Placing over an occupied cell evicts** the koma underneath back to the
  list; it does not fail. **OPEN:** the code path for eviction (the validator
  above rejects overlap, so the UI must remove-then-add).
- **One-character rule:** committing a koma greys out every koma of that
  character, and the grouping includes alternate forms and fusions (Goku greyed
  SSJ Goku and Vegetto). A deck cannot be built from one character's koma
  alone. Consistent with, but wider than, the add-entry duplicate-ID check —
  the ID check alone would not grey other koma. **OPEN:** where the
  character-grouping table lives.
- **Leader:** cell cursor on a battle koma, R picks up the sticker, A stamps.
  B after pickup cancels the stamp while still drawing the badge — the failure
  only surfaces at exit.
- Editor UI grammar: nearly every control takes **two taps** (first focuses,
  second activates); a single cell tap only moves an uncommitted preview.
- The final validity check is the game's own exit caution — stronger than any
  memory or pixel signal.

Route in: top menu デッキメイク → deck select (ov01) → tap slot twice → 編集 →
editor (ov05) (`Deck-Editor-Automated.md`).

---

## 6. The RAM oracle at 0x020A0C00 — what it can and cannot validate

The deck-state region 0x020A0C00–0x020B0000 is a useful but **coarse** oracle.
Measured byte-diff magnitudes (`Deck-Editor-Automated.md`):

| Event | Bytes changed |
|---|---|
| idle after savestate load | 17–42 |
| a tap/press that does nothing | 95–190 |
| SELECT with no pixel change | 1041 |
| clearing a full deck | 361 |
| placing one 4-koma | 1326 |

Rules for using it:

- It confirms **that something large happened, and nothing finer**. An
  ineffective tap costs ~100–190 bytes, so mid-size diffs are not evidence of a
  state change (a 107-byte "deck cleared" reading was a false positive).
- An **uncommitted preview also moves ~1326 bytes**, indistinguishable from a
  real placement. Placement must be verified by round-tripping the canvas
  (toggle away and back) or by the game's own exit verdict.
- Specific bytes within it that ARE reliable field-level signals: 0x020A0C98
  (leader bit), 0x020A2289 (leader boolean), 0x020A4368 (leader pointer),
  0x020AFEB4 (deck slot) — see section 4.3.
- Occupancy is better read elsewhere: on-screen (`canvas_cells()`, 81 samples
  per cell, 1.00 empty vs 0.00 occupied) or, in a reimplementation, as the
  20-bit mask semantics of deck+0x568.

---

## 7. Open items (consolidated)

1. **Nature storage per panel** — not in koma.bin; parallel table unfound
   (`findings/koma-format-decoded.md`).
2. **shapeObject identity** — what 0x02076D00 returns; shape word is +0x14 of it.
3. **No writer found for deck+0x30 / deck+0x18EC** — the arm9 add-entry path
   may be dead; the editor's live placement path is unattributed
   (`findings/deck-add-entry-path-is-dead.md`).
4. **koma.bin +0xA** (0..8, <= size) unidentified.
5. **Eviction-on-overlap code path** — observed behaviour only.
6. **Character-grouping (greying) table** — includes forms/fusions; location unknown.
7. **Save-region layout vs ComicDeck block** — how 0x020B9480 and the deck
   pointer arrays feed the runtime tables.
8. **deck+0x568 vs battleObj+0x558** — no established relationship.
