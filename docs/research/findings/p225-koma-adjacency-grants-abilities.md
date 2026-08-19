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
