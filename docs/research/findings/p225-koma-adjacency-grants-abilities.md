# Loop-Atlas 225 — the 1..4 field is a direction; koma grant abilities by adjacency

Claim: [`jus-koma-adjacency-grants-abilities-70l`]. Builds on [`jus-second-ability-source-0x558-5rp`].

Last wake found a second ability source — a list at `battleObj+0x558` where type-2 nodes get their ability id appended, gated by `0x020779CC`. That gate constrains a field to `1..4`. The cardinality matched the nature enum, but it's not nature. It's a cardinal direction, and the gate is a koma grid-adjacency test.

## The gate, end to end

```
0x020779D0  ldrb r2, [r1, #0x0f]     k = [node+0x0F] & 0x0F
0x020779D4  ands r2, r2, #0xf        reject 0
0x020779E0  cmp  r2, #4              reject > 4
0x020779EC  ldrb lr, [r1, #0x0e]     the packed cell
0x020779F4  lsl  ip, r1, #1          index = (k-1)*2
0x02077A04  asr  r2, r2, #4          HIGH nibble of +0x0E
0x02077A08  ldrsb r3, [r3, ip]       dx
0x02077A0C  and  lr, lr, #0xf        LOW nibble of +0x0E
0x02077A10  ldrsb r1, [r1, ip]       dy
0x02077A18  adds r3, lr, r3          x' = low  + dx
0x02077A1C  add  r2, r2, r1          y' = high + dy
0x02077A2C  cmp  r3, #5
0x02077A30  cmplt r2, #4             require 0 <= x' < 5 and 0 <= y' < 4
0x02077A40  mov  r1, #0x14           row stride 20 = 5 cells x 4 bytes
0x02077A44  mla  r0, r2, r1, r0
0x02077A48  add  r0, r0, r3, lsl #2
0x02077A4C  ldr  r0, [r0, #8]        the pointer in that cell — returned, or 0
```

## The direction table

Eight bytes at `0x02092E34`, read from `arm9.bin`: `00 01  FF 00  00 FF  01 00`

| k | dx | dy | |
|---|---|---|---|
| 1 | 0 | +1 | down |
| 2 | −1 | 0 | left |
| 3 | 0 | −1 | up |
| 4 | +1 | 0 | right |

The four cardinals. Same data block as the damage class table (`0x02092E68`) and the ±25% mask tables (`0x02092E78` / `0x02092E90`).

## The mechanic

Each node on the `+0x558` list carries a **grid cell** (`+0x0E`: low nibble = column, high nibble = row), a **direction** (`+0x0F` low nibble), and an **ability id** (`+0x41`). The gate steps one cell in that direction, rejects anything off-grid, and returns whatever sits in the neighbour. The caller appends the ability id to that object.

**A koma grants its ability to the character in the adjacent cell, in the direction it points.**

## Convergent verification

Three independent paths to the same grid size:

- Code bounds: `x' < 5`, `y' < 4`
- Row stride: `0x14` = 20 bytes = 5 cells × 4 bytes → five columns
- Owner observation: `docs/design/Koma-System-Design-Brief.md` line 13 — "a 4-row × 5-column grid = 20 cells," written from live play

Code constants, an array stride, and a human looking at the screen all give 5 × 4. None derives from the others.

## What I'm not claiming

That the grid cells hold character structs. `AddAbility` does `ldrsb [r0+0x1A]` and `strb [r0 + count + 0x1B]` on the returned pointer, and `char+0x1A` / `char+0x1B` is the established ability-list location — so the cells hold objects with that layout. Strong, but it's one usage, and object identity is exactly where this campaign has been wrong before.

Also open: what writes the `+0x558` nodes, and whether `+0x0E`'s nibbles are really (column, row). The bounds pin which nibble is bounded by 5 and which by 4; "column" and "row" are my labels, and the design brief's 4-row × 5-column framing makes low = column the natural reading.

## Provenance

Static only. `jus_files/arm9/arm9.bin`, listing `jus_files/analysis/disasm/arm9.txt`, direction bytes read from the binary at `addr − 0x02000000`. No codex pass — the decisive check is code constants against a human-observed grid size, already cross-representational, so handing codex the same listing would be one artifact twice.

## Corrected the same wake: the list is at `arg0+0x558`, and it is one list walked twice

The runtime seat read `[0x02244020+0x558]` and got ASCII, which caught two errors of mine.

**The address.** `0x0207776C` is `mov sl, r0`, so the list head is at **`arg0+0x558`** and arg0's
identity is not established. I called it `battleObj` because the surrounding code smelled like it,
which is the guess-an-object's-identity error again.

**The shape, and this one matters more.** It is one list walked twice, not two lists. Pass 1
(`0x02077770`) takes nodes with `+0x40 == 0`, reads `+0x41` as a **chr_b index**, walks the five
record slots and appends to the node *itself* — so for type 0 the node **is** the character struct.
Pass 2 (`0x02077830`) takes `+0x40 == 2`, reads `+0x41` as an **ability id**, and appends it to the
adjacency-selected recipient. Both chain via `node+0x00`.

So `+0x41` means two different things depending on `+0x40`: a chr_b index on type 0, an ability id
on type 2.

**Confirmed from live memory, 3/3** — every appended id matches a type-2 node in the same chain,
and the mapping is **selective**: the opponent chain has two type-2 nodes, and one fighter got 14
but not 5 while the other got 5 but not 14. A broadcast would have given both to both, which is
what the adjacency gate predicts.

**Still untested, and this is the honest state.** The runtime seat refuted a *different*
hypothesis — that `[+0x0F] & 0x0F` names a deck position (measured 2/3/2 against recipient
positions 4/1/2). Adjacency says the recipient is `(cell + direction)` and neither field alone, so
those numbers are consistent with it and don't discriminate. The test that would: the full `+0x0E`
and `+0x0F` bytes per node plus the 80 bytes at `arg0+8`, checking that
`arg0 + 8 + y*0x14 + x*4` holds the recipient's address for all three. Three for three confirms;
one miss kills it.

## Correction: one "open question" above was not open

I listed the nibble order of `+0x0E` as unresolved. The code settles it — the gate adds `dx` to
the **low** nibble and bounds it by 5, and `dy` to the **high** nibble bounded by 4. A swapped
reading would be different code, not a rival hypothesis about this code. The only real question
was what to *name* the axes, and the observed 5-column × 4-row grid answers that. I then built a
test for the non-question, and it couldn't discriminate — which is what a test of a
non-hypothesis does.

## Confirmed 3/3 from live memory — and one open hazard

The runtime seat ran the constraint scan and `arg0` fell out as a **solution** rather than an
input: `arg0_opp = 0x021DF76C`, `arg0_ply = 0x021DF150`, difference `0x61C` — the known
`SIDE_DELTA`, arriving unbidden and breaking a two-candidate tie.

| node | anchor | k | target | grid holds | expected | |
|---|---|---|---|---|---|---|
| player, id 10 | (2,3) | 2 | (1,3) | `0x021DF2AC` | `0x021DF2AC` | HIT |
| opp, id 14 | (4,2) | 3 | (4,1) | `0x021DF7D8` | `0x021DF7D8` | HIT |
| opp, id 5 | (3,2) | 2 | (2,2) | `0x021DF828` | `0x021DF828` | HIT |

**And the grid is visibly a koma page.** Pointers repeat across multi-cell footprints —
`0x021DF1BC` in 4 cells, `0x021DF25C` in 3, `0x021DF2AC` in 3, `0x021DF20C` in 3, `0x021DF2FC`
in 2. Eleven nodes across both chains occupy eleven distinct cells of one 5×4 grid, in polyomino
shapes.

### A test I proposed would have killed this correct model

I suggested checking that the grid holds each fighter's own address at its own cell, no direction
step, as a free extra constraint. It returns **0 of 3** — because `+0x0E` is an *anchor*, not a
footprint, and the grid repeats a pointer across the whole panel. Run as the discriminator it
would have reported this model dead, by my own suggestion. It smuggled the premise that a fighter
occupies one cell. **A test is only as good as the assumption it hides.**

### Open hazard: row 0 is reachable and doesn't hold pointers

All three hits are in rows 1–3, and the opponent grid's (0,0) holds `0x00007882` — not a pointer.
But `y' = 0` **is** reachable under the gate's own bounds: high nibble 0 with `k=2` or `k=4`, or
high nibble 1 with `k=3`, and the only lower check is `>= 0`. So a node targeting row 0 would get
a non-null non-pointer back and `AddAbility` would do `ldrsb [0x00007882 + 0x1A]`.

Either no live node ever targets row 0, or `arg0+8` is not the indexing base — and it cannot be a
simple off-by-one row, because the three hits land correctly with that base and a `0x14` stride.
Pin this before indexing the array.

`arg0` is a known **address** and an unnamed **object**: `0x021DF150` / `0x021DF76C`, `0x61C`
apart, with char_structs in the same region (`0x021DF1BC` is `arg0_ply + 0x6C`). Not named, on the
fourth iteration of that discipline.

## "Anchor" retracted, and row 0 holds a cross-side link

All five player-side type-0 nodes checked: `[+0x0E]` = (footprint column, footprint top row **minus
one**), five for five. And for two of the five the declared cell is occupied by *another* koma —
`0x021DF1BC` holds both (1,1) and (3,1), which `0x021DF2AC` and `0x021DF2FC` declare. So the field
cannot mean "where I am", and **"anchor" implied exactly that**. What it does mean is not named
here: five samples on one deck, and a systematic off-by-one row has at least three innocent
readings.

**This is the second field whose meaning depends on `+0x40`.** Type-2 nodes index the grid
directly — all three adjacency hits used `y = high nibble + dy` with no adjustment — while type-0
nodes are off by one row. Same shape as `+0x41` being a chr_b index on type 0 and an ability id on
type 2. The property to carry is: **nothing in this struct is safe to read without checking `+0x40`
first.**

### Row 0 is a cross-side link, not junk

```
player grid cell (3,0)  at arg0_ply + 8 + 3*4  = 0x021DF164, value 0x021DF780
opponent grid cell (3,0) at arg0_opp + 8 + 3*4 = 0x021DF780   ← exact match
```

`player_grid[(3,0)]` holds the **address of** `opponent_grid[(3,0)]`.

That sharpens the hazard rather than resolving it: for `y' = 0` the gate returns a non-null
cross-side link, and `AddAbility` then does `strb [that + count + 0x1B]` — a targeted write into
the other side's grid array, not a garbage dereference. And row 0 is addressed by design, since
three of five type-0 nodes declare cells in it.

**Open, and it is the next real question:** what stops a live type-2 node producing `y' = 0`?
Either the gate has a check I've misread, or type-2 nodes never carry a high nibble of 0 or 1 by
construction, or nothing stops it.

### Layout of `arg0` as far as it is visible

```
+0x008 .. +0x057   the grid the gate indexes, 4 rows x 0x14
+0x058 .. +0x06B   0x14 unaccounted — exactly one more row's worth
+0x06C, stride 0x50  the character records (0x6C, 0xBC, 0x10C, 0x15C, 0x1AC)
```

A spare row-sized gap right after a 4-row grid, in a game with a 4-row deck, is worth checking
against the possibility that the array is declared with five rows and the gate excludes one. If the
declaration excludes row 0 and the gate's bounds do not, the off-by-one is the game's, not ours.

