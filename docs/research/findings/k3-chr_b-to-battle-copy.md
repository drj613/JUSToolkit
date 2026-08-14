# K3 — how deck/koma data reaches battle structs, and the HP array refined

Iteration 31. Static analysis of `0x02077C0C`, the character-init function.

## The chr_b lookup

```asm
0x02077C10  ldr  r2,[pc,#0x9C]     ; r2 = 0x0214BD80
0x02077C18  ldr  r2,[r2,#0x0]      ; the battle resource manager
0x02077C1C  ldrb r4,[r1,#0x41]     ; chr_b index, off the battle struct
0x02077C20  ldr  r12,[r2,#0x40]    ; chr_b table base
0x02077C24  mov  r2,#0x3C          ; 60 = record size
0x02077C28  mla  r2,r4,r2,r12      ; r2 = base + index*60
```

`*(0x0214BD80)+0x40`, stride `0x3C` — confirmed in instructions, as the charter requested.

## +0x34 links deck to battle

```asm
0x02077C14  ldr   r3,[r1,#0x34]    ; r3 = the panel's koma record
0x02077C2C  ldrsb r3,[r3,#0x8]     ; koma +0x8 = kshapeGroup = size-1
0x02077C30  sub   r12,r3,#3        ; -> size-4
0x02077C34  add   r3,r2,r12,lsl #2 ; chr_b_rec + (size-4)*4
0x02077C3C  add   r4,r2,r12,lsl #2 ; same
0x02077C40  add   r12,r2,r12,lsl #1; chr_b_rec + (size-4)*2
```

Battle-struct `+0x34` holds a pointer to the panel's `koma.bin` record. The `kshapeGroup` byte in that record drives every per-size lookup. Three instructions tell the whole story: deck gives you a koma record, koma gives you the size, size indexes the stats.

Two per-size strides show up: **×4** and **×2**, feeding different arrays.

## HP array confirmed — and corrected

`add r3,r2,r12,lsl #2` nails the stride at **4**. The per-size HP array at `+0x10` is real.

**Self-correction:** I nearly misread this. My `add` decoder didn't print shift fields, so without the `lsl #2` it looked like stride 1 — which would've made Naruto's size-5 HP equal `1`.

The shift also shows my earlier reading was too coarse. `+0x10` isn't five single bytes at stride 4 — it's five **4-byte records**. I'd only identified the first byte of each:

| record field | contents | copied to |
|---|---|---|
| `+0x0` | per-size max HP (byte, ×64 to raw) | battle `+0x16` and `+0x18` |
| `+0x1` | **regen rate** (byte; **defaults to 4 if zero**) | battle `+0x49` |
| `+0x2` | unknown | battle `+0x14` |
| `+0x3` | unknown | battle `+0x15` |

This clears up a loose end from iteration 7. I'd seen "high bytes of `1, 4, 5, 16, 20, 22`" reading those slots as u16 and couldn't explain them. They weren't high bytes at all — they were the **regen-rate field** of each per-size record. The harness session measured a live regen rate of `1`, which matches a value in that set.

## Full init copy map

`r2` = chr_b record, `r4` = record + (size-4)×4, `r12` = record + (size-4)×2:

| source | → | battle struct | meaning |
|---|---|---|---|
| `chr_b[0x00]` | → | `+0x13` | **base nature** |
| `chr_b[0x01]` (signed) | → | `+0x11` | unknown |
| `chr_b[0x02]` (signed) | → | `+0x10` | unknown |
| `chr_b[0x10 + (size-4)*4]` | ×64 → | `+0x16`, `+0x18` | max HP, and current = max |
| `chr_b[0x11 + (size-4)*4]` | → | `+0x49` | regen rate (default 4) |
| `chr_b[0x12 + (size-4)*4]` | → | `+0x14` | unknown |
| `chr_b[0x13 + (size-4)*4]` | → | `+0x15` | unknown |
| `chr_b[0x30]` (halfword) | → | `+0x2E` | unknown |
| `chr_b[0x32 + (size-4)*2]` | → | `+0x30` | per-size halfword array |

## Two independent findings confirmed

- **`chr_b[0x00]` = base nature → battle `+0x13`.** My nature work identified `chr_b` offset `0x00` as base nature from a distribution argument; the harness session found nature at runtime `+0x13`. This instruction connects those facts, and neither was derived from it.
- **Regen lives at `+0x49`**, found by the harness session watching memory. Here it's written at init from a per-size field, with a hardcoded default of 4.

## Still unknown

Four copied fields remain unidentified: `chr_b[0x01]`/`[0x02]` → battle `+0x11`/`+0x10`, and per-size `+0x12`/`+0x13` → battle `+0x14`/`+0x15`. There's also a per-size **halfword** array at `chr_b[0x32]` (stride 2) → battle `+0x30`, which I hadn't seen before.

`0x02077C0C` has **zero direct callers** across arm9 and all 14 overlays — it's dispatched through a pointer table like the other constructors. The caller supplying the koma record at `+0x34` isn't statically reachable.

## Refinement (same day): the regen field is uniformly 1

I wrote above that the unexplained "u16 high bytes of `1, 4, 5, 16, 20, 22`" from iteration 7 were the
regen-rate field. Half right, and worth stating precisely.

Restricted to the sizes each character **actually owns** (174 records), the regen field is
`{1: 174}` — **uniformly 1, no exceptions.** So the odd values `4, 5, 16, 20, 22` came from **filler
slots** for sizes the character doesn't have, not from real regen values. The field identification
holds; my account of the odd values did not.

That also means the init's `moveq r3,#0x4` default-to-4 branch **never fires for a real panel**, and
the harness session's live measurement of rate `1` is the universal value rather than one sample.

## The iteration-20 over-fit, now explained

In iteration 20 I noticed four u16s at `chr_b +0x30`/`+0x32`/`+0x34`/`+0x36` that looked like a
per-character base plus 0,1,2,3 (Naruto `362,363,364,365`), backed out because only 15 of 74 were
sequential, and left it as "four independent IDs, not a pattern".

K3 explains it: `chr_b[0x30]` is a single halfword, and `chr_b[0x32]` is a **per-size array at stride
2**. So they were never four parallel fields — one standalone ID followed by a per-size array, read
through the wrong frame. Goku's `337, 0, 338, 0` is that array with filler in the slots he doesn't own.

Same shape of error as the physics window: reading an array through the wrong stride makes it look like
a set of unrelated fields.
