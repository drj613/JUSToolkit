# Findings: the deck's two validators, and `0x0214BD80` is the ComicDeck block

Loop-Atlas iteration 109. Static.

Add-entry's two gates — an **ID→record lookup** and an **argument validator** — expose
the deck's ID table, entry size, count field, and hard bounds on the two packed arguments:
**`a < 5`** and **`b < 4`**.

They also correct my own canon: `0x0214BD80`, recorded as "chr_b base ptr", actually
holds the `0x1914` **ComicDeck block**.

---

## 1. `0x02076C98(_, id)` — bounds-checked table lookup

```
0x02076C98  mvn  r0, #0
0x02076C9C  cmp  r1, r0
0x02076CA0  moveq r0, #0
0x02076CA4  bxeq lr                   ; id == -1 -> 0
0x02076CA8  cmp  r1, #0
0x02076CB0  bxlt lr                   ; id < 0 -> 0
0x02076CB4  ldr  r0, [pc, #0x20]      ; -> 0x0214BD80
0x02076CB8  ldr  r2, [r0]             ; the ComicDeck block
0x02076CC0  ldr  r0, [r0, #0x8ec]     ; deck+0x18EC = the count
0x02076CC4  cmp  r1, r0
0x02076CC8  movhs r0, #0              ; id >= count -> 0
0x02076CCC  ldrlo r2, [r2, #0x30]     ; deck+0x30 = the table base
0x02076CD0  movlo r0, #0xc            ; entry size
0x02076CD4  mlalo r0, r1, r0, r2      ; table + id * 0xC
```

ID table: **`0xC`-byte entries** at `deck+0x30`, count at `deck+0x18EC`.
Rejects `-1`, negative, and out-of-range IDs.

## 2. `0x02076D30(deck, id, a, b)` — argument bounds

```
0x02076D3C  cmp  r5, #5
0x02076D44  movhs r0, #0
0x02076D48  pophs {…}                 ; a >= 5 -> fail
0x02076D4C  cmp  r4, #4
0x02076D50  movhs r0, #0
0x02076D54  pophs {…}                 ; b >= 4 -> fail
0x02076D58  bl   #0x2076c98           ; the id must resolve
0x02076D68  bl   #0x2076d00
0x02076D6C  ldr  r0, [r0, #0x14]
0x02076D70  lsr  r3, r0, #5           ; four 5-bit fields out of +0x14,
0x02076D74  lsr  r2, r0, #0xa         ; ORed into one mask
0x02076D78  lsr  r1, r0, #0xf
0x02076D98  lsl  r1, r1, r5           ; shifted by a
```

`a` takes **5** values, `b` takes **4** — the two nibbles packed into `node+0x0E` by
iteration 108's add. `b < 4` matches the four player slots, but nothing here ties them.

`0x02076D00` reads two signed bytes at `+0x8`/`+0x9` and indexes a second table at
`deck+0x38` with stride `0x18`.

## 3. `0x0214BD80` holds the ComicDeck block

```
0x0207602C  ldr r3, [pc, #0x388]      ; -> 0x0214BD80
0x02076038  str r0, [r3]              ; = the 0x1914 allocation
0x02076040  ldr r7, [pc, #0x374]
0x02076048  ldr r0, [r7]
0x0207604C  add r8, r0, #0x64         ; the player-slot array
0x02076044  mov r4, #4                ; four of them
```

The block is reachable two ways — this global and `root+0x114`. The same initialiser
walks four slots from `+0x64`, independently confirming the count from iteration 103.

**97** literal loads reference this global — a heavily used handle.

## 4. Deck header fields recovered

| offset | what |
|---|---|
| `+0x0030` | ID table base, `0xC`-byte entries |
| `+0x0038` | second table base, `0x18`-byte entries |
| `+0x18EC` | entry count for the `+0x30` table |

`+0x30` and `+0x38` fall inside the `0x58` header left unexplained by iteration 106.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x02076C98` is a bounds-checked ID→record lookup | **CONFIRMED_STATIC** — three rejections, then `mla` with stride `0xC` |
| The ID table lives at `deck+0x30` with `0xC`-byte entries | **CONFIRMED_STATIC** — `ldrlo r2,[r2,#0x30]`; `movlo r0,#0xc`; `mlalo` |
| Its count is at `deck+0x18EC` | **CONFIRMED_STATIC** — `ldr r0,[r0,#0x8ec]` after `add r0,r2,#0x1000` |
| `0x02076D30` bounds `a < 5` and `b < 4` | **CONFIRMED_STATIC** — `cmp #5`/`pophs`, `cmp #4`/`pophs` |
| Those are the two nibbles packed into `node+0x0E` | **CONFIRMED_STATIC** — same two arguments, same order, iteration 108 |
| `0x0214BD80` is a "chr_b base ptr" | **REFUTED** *(my own note)* — `str r0,[r3]` at `0x02076038` stores the ComicDeck block |
| The ComicDeck block is reachable from a global and from `root+0x114` | **CONFIRMED_STATIC** — both stores seen |
| The slot array has four entries | **CONFIRMED_STATIC** *(second route)* — `mov r4,#4` with `add r8,r0,#0x64` |
| `b < 4` means the player index | **not claimed** — the bound matches the slot count; no code ties them |
| `+0x14` of a table entry holds four 5-bit fields | **CONFIRMED_STATIC** — three `lsr` by 5, `0xA`, `0xF` with `and #0x1f`, ORed |

## Next angles, ranked

1. **Dump the `0xC`-byte ID table** at `deck+0x30` — static definition of every deck entry;
   `+0x14` of the *other* table carries the 5-bit field group.
2. **Read `0x02076D00`** — second table at `deck+0x38`, stride `0x18`, indexed by two signed bytes.
3. **Find who sets `node+0x34`** (carried) — points at an entry's data record.
4. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
