# P166 — Per-mode handler table: 31 × 12 bytes at `0x02170EAC`, plus two battle-root fields

Iteration 166. Static analysis, anchored by six runtime reference points. The runtime loop (bead `jus-hsc`) measured `root+0x000` across seven battles, one per rule mode, and got a different Thumb handler each time. This wake's job: find the static table those handlers live in.

Found it. The indexing code is unambiguous.

## The table

`CONFIRMED_STATIC`. **Base `0x02170EAC` in ov6. 31 records, 12 bytes each — three Thumb function pointers per record.** Indexed by rule mode.

Three independent lines of evidence, three different representations:

**1. Indexing code.** ov6 Thumb at `0x0214F91C`:

```
0x0214F91C: 6882  ldr  r2, [r0, #8]      ; r2 = mode
0x0214F91E: 210c  mov  r1, #0xC          ; stride 12
0x0214F920: 1c13  mov  r3, r2
0x0214F922: 434b  mul  r3, r1            ; r3 = mode * 12
0x0214F924: 4903  ldr  r1, [pc, #0xC]    ; pool 0x0214F934 -> 0x02170EB0
0x0214F926: 58c9  ldr  r1, [r1, r3]      ; r1 = [0x02170EB0 + mode*12]
0x0214F928: 6001  str  r1, [r0, #0]      ; *** [obj+0x00] = that handler ***
0x0214F92A: 2101  mov  r1, #1
0x0214F92C: 30c8  add  r0, #0xC8
0x0214F92E: 7001  strb r1, [r0, #0]      ; [obj+0xC8] = 1
0x0214F930: 4770  bx   lr
```

That `str r1, [r0, #0]` is literally the writer of the field the runtime loop measured.

Two sibling accessors use the same index arithmetic against neighbouring columns: `0x0214F872` loads from pool `0x02170EAC` and `blx`es the result; `0x0214F95A` loads from pool `0x02170EB4` and `blx`es it inside a loop that also reads the root global `0x02172960`. Three pool words four bytes apart, three call sites — one per column of a 12-byte record.

**2. Data shape.** The contiguous run of odd (Thumb-flagged) in-overlay pointers containing those seven values spans `0x02170EAC` to `0x02171020`: **93 words, exactly 31 × 3.** Divides evenly by three only at the base the code names, nowhere else.

**3. Runtime values.** Reading column `+0x4` at stride 12 from `0x02170EAC`, the runtime loop's measurements land at these indices:

| mode poked | `root+0x000` measured | table index of that value |
|---|---|---|
| 0 | `0x0214FA79` | **0** |
| 1 | `0x0214FDDD` | **1** |
| 2 | `0x0215004D` | **2** |
| 3 | `0x0215036D` | **3** |
| 4 | `0x0214FB3D` | **4** |
| 5 | `0x0214FEC9` | **5** |
| 7 | `0x021503B5` | **7** |
| 9 | `0x02150469` | **9** |
| 16 | `0x021508F1` | **16** |
| 17 | `0x0215097D` | **17** |
| 19 | `0x02150B01` | **19** |
| 21 | `0x02150C21` | **21** |
| training path (settings byte reads 0) | `0x02150D71` | **8** — see below |

Twelve of twelve poked modes land at their own index, exact, spanning 0 to 21. Strongest form available: the runtime loop didn't know where the table was, and the static analysis didn't know the live values.

**Codex cross-check (run before writing this).** The eleven halfwords were handed over with no addresses, no hypothesis — just the fact that word `0x02170EB0` sits at `L+0x18`. Codex returned `([R], [R+0xC8]) <- ([0x02170EB0 + 12 * [R+8]], 1)` — same multiplier, same base, same two destinations — and noted independently that the literal load requires `L` to be word-aligned, which it is. No disagreement.

## Two new battle-root fields

The `r0` in that routine is the battle root: the sibling accessor at `0x0214F950` reads root global `0x02172960`, and the store target `+0x000` is the field the runtime loop reads through that same global.

- `CONFIRMED_STATIC`: **`root+0x08` = the rule mode**, a 32-bit word. This is the table index. The engine reads the mode from here, not from settings byte `0x020AFEA0` directly — something copies it during setup.
- `CONFIRMED_STATIC`: **`root+0xC8` = a byte flag**, set to `1` by this routine.

The sibling at `0x0214F93C` is the counterpart: it stores a fixed handler `0x02150F65` into `[obj+0]` and writes `0` to `[obj+0xC8]`. So `+0xC8` tells you whether a per-mode handler or the default handler is installed, and `root+0x000` is not always table-derived.

That matters if you use `root+0x000` as a mode oracle: `+0xC8` of `0` means `+0x000` holds the default, and reverse-looking it up in the table will find nothing.

## 31 engine modes, 22 described modes

`bin/rulemess.bin` (P165) has **22** entries. This table has **31**. Nine handler slots exist with no description text. `not claimed`: whether slots 22–30 are reachable, dead, or debug-only.

Records that are byte-identical triples (same three handlers): `(9, 22)`, `(16, 30)`, and `(25, 28)`. Nothing else repeats.

## A prediction, refuted before it cost a runtime wake

`REFUTED` — my `jus-wbo` prediction from last wake. Five `rulemess.bin` entries duplicate an earlier entry's description text (18≈0, 19≈1, 20≈2, 17≈4, 21 is the short form of 7). I predicted each duplicate would share its twin's handler — same rule, different menu path.

Wrong. Modes 17–21 all have distinct handlers. The only shared records are `(9, 22)`, `(16, 30)`, `(25, 28)` — none a text-duplicate pair. **Duplicated description text does not imply shared battle logic.**

The runtime loop hadn't started those pokes yet, so the refutation cost nothing but the bead. Filed before the search deliberately so the search couldn't launder it.

**The runtime loop's objection, and why the static data answers it.** They flagged that thirteen tested indices gave thirteen distinct handlers, never a repeat, so `root+0x000` might discriminate the index rather than the rule — one function per slot. If true, handler equality could never reveal sameness and the test would have been incapable of confirming the prediction.

The table settles it: records `(9, 22)`, `(16, 30)`, and `(25, 28)` are byte-identical triples. Sharing is expressible in this structure and does occur, so the instrument can produce equal handlers for equal rules. The test was capable of confirming the prediction. It didn't, and the refutation stands at the code level.

What does not follow — and here they're right — is the semantic version. Two distinct functions can implement the same rule, so distinct handlers don't prove distinct rules. `CONFIRMED_STATIC` that text-duplicate entries have distinct handler code; `not claimed` whether they behave identically in play. Their offer to compare observable behaviour (win condition, HUD, score readout) for one pair is the right instrument for the semantic question, and it's worth spending a wake on only if the answer changes something downstream. Right now it doesn't, so I'm not asking for it.

**Two modes never build a battle at all.** Modes 18 and 20 leave `[0x02172960]` at zero through ~3000 frames. Mode 18 isn't hanging — it goes straight to a results screen with both players marked WINNER at 0 pts on a ポイント scoreboard. Mode 20 has nearly the same fingerprint. So they have no handler in flight, and the nine undescribed slots aren't the only oddity in the upper range.

## The index-space question: open

Two tables are indexed by "the mode": the 16-byte rulemess header (ov1, drives time-limit conversion) and this 12-byte handler table (ov6). **Whether they share one index space is established only for modes 0, 1, and 2.**

For: the runtime loop read the rule pill as ポイント / デスマッチ / Ｊシンボル at bytes 0/1/2, and rulemess entries 0/1/2 are point battle, death match, J-symbols. Three independent name matches.

Against, or at least unexplained:

- **The training path lands on index 8 while its settings byte reads 0.** Its handler is `0x02150D71` = table entry 8, and the runtime loop reports the mode byte as `0` in that state. So `root+0x08` is not a straight copy of `0x020AFEA0`. Something maps game path plus settings onto the mode index, and on the training path that mapping doesn't preserve the value.
- **Mode 3's battle doesn't obviously match rulemess entry 3.** Entry 3 is the Jump Pirates tutorial; the runtime loop's mode-3 screenshot was a real fight with a treasure chest and a DEVILBATS banner. Treasure chests are rulemess entry **12**. The banner is a stage name, so this is suggestive rather than conclusive.

`PLAUSIBLE`, not confirmed: the two tables share an index space. `CROSS_CONFIRMED` only for modes 0–2, on the pill names. Everything about "mode N is rule X" for N ≥ 3 rests on that unproven alignment, and it's labelled accordingly.

## Queued

1. **Static, top priority: find the writer of `root+0x08`.** The training-path result shows the mode index is not a copy of the settings byte, so this writer is the mapping from game path plus settings onto the mode index. Settles the index-space question with no runtime work. Next task.
2. **Runtime:** poke mode 12 and look for a treasure-chest battle. Tests rulemess-to-handler alignment at a mode far from 0–2.
3. Still open: writer of `root+0x118`/`+0x11C` (the runtime loop's top ask), writer of `root+0x4C` (term `V`), and the `0x0214CD20`-window sweep.
