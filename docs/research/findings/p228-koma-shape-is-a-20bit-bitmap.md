# Loop-Atlas 228 — koma shape is a 20-bit polyomino bitmap; the re-read step paid immediately

Claim: [`jus-koma-shape-is-a-20bit-bitmap-423`]. Related: [`jus-koma-adjacency-grants-abilities-70l`].

This iteration added a step to the wake bracket: re-read your own last two beads before doing anything new. It caught something embarrassing on the first try — a note already sitting in my state file:

> `deck_add_validator: 0x02076D30 … fails if a >= 5, fails if b >= 4 … reads [result+0x14], extracting FOUR 5-BIT FIELDS`

Three wakes spent deriving the same geometry from the battle side while the answer was already written down.

## The deck placement rule, complete

`arm9 0x02076D30`, `f(deck, id, col, row)`:

```
0x02076D3C  cmp r5, #5  / movhs r0,#0 / pophs      col >= 5 -> reject
0x02076D4C  cmp r4, #4  / movhs r0,#0 / pophs      row >= 4 -> reject
0x02076D58  bl 0x02076C98                          lookup(deck,id) must be non-zero
0x02076D68  bl 0x02076D00 ; ldr r0,[r0,#0x14]       the SHAPE WORD
0x02076D70  lsr r3,r0,#5   \
0x02076D74  lsr r2,r0,#0xa  |  four 5-bit fields, each & 0x1f, ORed
0x02076D78  lsr r1,r0,#0xf  |  -> the shape's column profile
0x02076D7C  and ip,r0,#0x1f /
0x02076D98  lsl r1, r1, r5                          shift the profile by col
0x02076D9C  bics r1, r1, #0x1f / movne r0,#0        profile must still fit in 5 bits
0x02076DA8  add r1, r4, r4, lsl #2                  row * 5
0x02076DAC  add r2, r5, r1                          shift = col + row*5
0x02076DB4  lsl r0, r0, r2                          shift the shape into grid coordinates
0x02076DB0  mov r1,#0x100000 ; rsb r1,r1,#0         r1 = 0xFFF00000
0x02076DBC  tst r0, r1 / movne r0,#0                any bit >= 20 -> reject, it spills the grid
0x02076DC8  ldr r1, [r6, #0x568]                    the deck's OCCUPANCY MASK
0x02076DCC  tst r1, r0 / movne r0,#0                overlap -> reject
            otherwise return r0 = the shifted shape mask
```

What this gives us:

- **`[shapeObject + 0x14]` is a 20-bit polyomino bitmap** over the 5×4 grid — bits 0–4 are row 0, 5–9 row 1, 10–14 row 2, 15–19 row 3
- **`deck + 0x568` is the 20-bit occupancy mask** of the placed page
- Placement shifts the shape by `col + row*5`, rejects if any bit reaches 20 or higher, rejects on overlap
- The OR-then-shift step is a **width check**: the union of all four row masks, shifted by `col`, must fit in 5 bits — prevents wrap-around at row edges

## Third independent confirmation of 5×4 geometry

Three sources, none derived from the others:

- **Battle code** — adjacency gate bounds `x < 5`, `y < 4`, row stride `0x14` [`jus-koma-adjacency-grants-abilities-70l`]
- **Owner observation** — the live grid in `Koma-System-Design-Brief.md` is 4 rows × 5 columns
- **Deck-editor code** — rejects `col >= 5` and `row >= 4`, uses `row*5` stride

This also explains multi-cell footprints in battle: the pointer repeats across every set bit of the shifted shape mask.

## Not established

What `0x02076D00` returns — "shapeObject" is a placeholder name; the shape word sits at `+0x14` of whatever that function hands back. The similarity between `deck+0x568` here and the battle object's `arg0+0x558` is just adjacent-looking offsets in different structures, nothing more.

## Provenance

Static only. `jus_files/arm9/arm9.bin`, listing `jus_files/analysis/disasm/arm9.txt`. No codex pass — the key elements are a bounds pair and a shift stride read straight from instructions, already confirmed cross-representationally against a human-observed grid.
