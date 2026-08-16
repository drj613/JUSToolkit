# Findings: `[char+0x1b4]` is one of four `0x61C` player slots inside the ComicDeck block

Loop-Atlas iteration 103. Static.

`0x02076908` hands out elements from a pool inside the `0x1914` ComicDeck allocation.
The initialiser shows the layout: **four `0x61C`-byte slots starting at ComicDeck`+0x64`.**

`0x61C > 0x5F1`, so both known fields fit. The object hunted since iteration 73 is a
**per-player slot in the comic deck**.

Iteration 102 correctly refuted `0x1914 = 4 × 0x645`, but wrongly concluded the block is
*not* four per-player decks. It is — with a `0x64` header and stride `0x61C`.

---

## 1. The initialiser

Right after `ComicDeckCreate`'s allocation:

```
0x02075FDC  bl  #0x201a21c            ; the 0x1914 block, in r0
0x02075FE8  add r1, r0, #0xd4
0x02075FEC  add r4, r0, #0x64         ; first element
0x02075FF0  add r2, r1, #0x1800       ; bound = r0 + 0x18D4
0x02075FF4  mov r3, #0
0x02075FF8  str r3, [r4, #0x558]      ; per-element field
0x02075FFC  str r3, [r4, #0x55c]
0x02076000  str r3, [r4, #0x560]
0x02076004  add r1, r4, #0x21c
0x02076008  str r3, [r4, #0x564]
0x0207600C  add r4, r1, #0x400        ; stride = 0x21C + 0x400 = 0x61C
0x02076010  cmp r4, r2
0x02076014  blo #0x2075ff8
0x0207601C  str r3, [r1, #0x8d4]      ; four list heads at +0x18D4,
0x02076020  str r3, [r1, #0x8d8]      ; +0x18D8, +0x18DC, +0x18E0
0x02076024  str r3, [r1, #0x8dc]
0x02076028  str r3, [r1, #0x8e0]
```

`(0x18D4 - 0x64) / 0x61C = 0x1870 / 0x61C = 4` exactly.

| ComicDeck block, `0x1914` bytes | |
|---|---|
| `+0x0000`–`+0x0063` | header |
| `+0x0064`–`+0x18D3` | **4 player slots × `0x61C`** |
| `+0x18D4`, `+0x18D8`, `+0x18DC`, `+0x18E0` | list heads |
| `+0x18E4`–`+0x1913` | remainder |

## 2. Handing a slot out

```
0x02076908  mov r4, r0
0x02076910  add r0, r4, #0x1000
0x02076914  ldr r5, [r0, #0x8dc]      ; free list at deck+0x18DC
0x02076918  cmp r5, #0
0x02076920  popeq {…, pc}             ; empty -> return 0
0x02076930  bl  #0x2037c24            ; unlink(deck+0x18DC, slot)
0x0207693C  …                         ; link into deck+0x18D4
```

Called from `Battle_Add`:

```
0x0214D3BC  blx #0x02076908
0x0214D3C0  ldr r1, [r7, #0x0]        ; the battle root
0x0214D3C2  add r2, r1, r5            ; index*4
0x0214D3C8  str r0, [r2, r1]          ; root + 0x118 + index*4
```

Each slot is allocated from the deck's free list, published in the root array, and later
copied into `char+0x1b4` by `Battle_CharaCreate`.

## 3. `+0x558` belongs to the player slot

The initialiser zeroes `+0x558`, `+0x55C`, `+0x560`, `+0x564` **per element**, adjacent to
the `+0x56c` gauge pointer. These are not character fields — they belong to the player slot,
one pointer away via `+0x1b4`.

## 4. The constant test that would have rejected the truth

Iteration 102 refuted `0x1914 = 4 × 0x645` because `0x645` appears nowhere in arm9. But
**`0x61C` appears nowhere either** — the compiler synthesises it as `#0x21C` then `#0x400`.

"Constant not in code" can refute a *guess*, but is not a valid test for a stride in
general. What settled this was reading the loop, where the stride is two instructions.

## Predictions status

| Claim | Verdict |
|---|---|
| The `root+0x118` array is filled by `0x02076908` | **CONFIRMED_STATIC** — `blx` at `0x0214D3BC`, store at `0x0214D3C8` |
| Player slots are `0x61C` bytes, four of them, from ComicDeck`+0x64` | **CONFIRMED_STATIC** — `add r4,r0,#0x64`; stride `#0x21C`+`#0x400`; bound `+0x18D4`; `0x1870/0x61C = 4` |
| `0x61C` accommodates both known fields | **CONFIRMED_STATIC** — `+0x56c` and `+0x5F0` are both below `0x61C` |
| Slots are handed out from a free list in the deck | **CONFIRMED_STATIC** — `ldr r5,[deck+0x18DC]`; unlink; link to `+0x18D4` |
| `+0x558`–`+0x564` are character fields | **REFUTED** — zeroed per player slot at `0x02075FF8`–`0x02076008` |
| The `0x1914` block is not four per-player decks | **REFUTED** *(iteration 102, mine)* — it is, with a `0x64` header and stride `0x61C` |
| `0x1914 = 4 × 0x645` | **REFUTED** *(unchanged)* — the arithmetic ignored the header and the list heads |
| "The constant appears nowhere in code" refutes a stride | **REFUTED** — `0x61C` is the real stride and appears nowhere either |
| The player slot has a name | **not claimed** — `0x02076908` and `ComicDeckCreate`'s callees carry no assert string for it |

## Next angles, ranked

1. **Map the `0x61C` player slot.** Now bounded; `+0x56c`, `+0x558`–`+0x564`, `+0x5F0`
   known. Run `struct_fields.py` anchored on `0x02076908` and the two `+0x56c` writers.
2. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0`.
3. **Re-audit `char+0xNNN` claims above `0x200`** — `+0x558` was misattributed; others may
   also belong to the player slot.
4. **Read `Battle_MoveManCreate`** (carried).
