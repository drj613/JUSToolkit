# Findings: `[char+0x1b4]` is a per-player slot in the battle root

Loop-Atlas iteration 102. Static.

Reading how the character descriptor is built answered this directly:

**`[char+0x1b4]` = `[root + 0x118 + index*4]`** — an array of per-player objects in the
battle root, indexed by the character's slot number.

The `+0x56c` gauge machinery belongs to **`ComicDeck.cpp`**, making these per-player *deck* objects and explaining the map's "SP is deck-wide" tension. One tempting arithmetic fit was refuted.

---

## 1. The descriptor's first word

In `Battle_Add`, just before the `Battle_CharaCreate` loop body:

```
0x0214D5E2  ldr r0, [pc, #0x84]   ; -> 0x0214D668 = 0x02172960
0x0214D5E4  mov r2, #0x46
0x0214D5E6  ldr r0, [r0, #0x0]    ; r0 = the root object
0x0214D5E8  lsl r7, r5, #2        ; index * 4
0x0214D5EA  add r1, r0, r7
0x0214D5EC  lsl r2, r2, #2        ; 0x118
0x0214D5EE  ldr r1, [r1, r2]      ; [root + 0x118 + index*4]
0x0214D5F0  str r1, [sp, #0x48]   ; descriptor +0x00
```

Iteration 97 established `descriptor+0x00` becomes `char+0x1b4`, so each character gets the array element matching its own index.

The same pass confirms iteration 100's ComicDeck slot:

```
0x0214D3A2  blx #0x02075fbc       ; ComicDeckCreate
0x0214D3A8  mov r1, #0x45
0x0214D3AC  lsl r1, r1, #2        ; 0x114
0x0214D3AE  str r0, [r2, r1]      ; root+0x114
```

`0x45*4 = 0x114`; the array starts one slot later at `0x46*4 = 0x118`. With `BattleAI_Create` at `+0x128`, there is room for **four** entries — `+0x118`, `+0x11C`, `+0x120`, `+0x124` — matching JUS's four-player battles.

## 2. The gauge belongs to `ComicDeck.cpp`

Six writers of `+0x56c` exist; four in ov3 (quiz overlay). The two in arm9:

```
0x02077FD0  orr r1, r1, #1
0x02077FD4  orr r1, r1, #0x100
0x02077FD8  str r1, [r5, #0x3c]     ; flags on the gauge
0x02077FDC  str r5, [r6, #0x56c]

0x020786D0  orr r2, r2, #1
0x020786D4  orr r2, r2, #0x100
0x020786D8  str r2, [r3, #0x3c]
0x020786DC  str r3, [r0, #0x56c]
```

Identical idiom: set bits `0x1` and `0x100` in the gauge's `+0x3c`, then install it.

Both sit between `ComicDeckCreate` (`0x02075FDC`) and `ComicDeck_DispCreate` (`0x02078CFC`) — the allocation tags that bracket `ComicDeck.cpp`. **So does the GDB-proven reader `0x020784E4`.** The entire `+0x56c` gauge mechanism is that module's.

Neither function carries an assert-string name; attribution is by address range between the two tags.

## 3. `0x1914 = 4 × 0x645` is a coincidence

`ComicDeckCreate` allocates `0x1914`; four equal slices would be `0x645` each. Since `0x645 > 0x5F0`, a byte at `+0x5F0` and a pointer at `+0x56c` would both fit — exact arithmetic, perfect field fit.

**Refuted.** `0x645` appears in arm9 as **neither an instruction immediate nor a literal pool word** — zero sites. Nothing strides by it, so `0x1914` is not four per-player decks.

## 4. Where that leaves it

`[char+0x1b4]` is a per-player object of at least `0x5F1` bytes, carrying the `+0x56c` gauge that `ComicDeck.cpp` installs. Its allocator is still unknown — not the `0x1914` block, and the array at `root+0x118` is filled somewhere this pass did not reach.

If these are per-player decks, deck-wide SP sits naturally on them, and each character reaching its own team's gauge through `+0x1b4` is exactly the structure the map's `+0x558`/`+0x56c` tension needed. **Plausible, not established.**

## Predictions status

| Claim | Verdict |
|---|---|
| `[char+0x1b4]` is `[root + 0x118 + index*4]` | **CONFIRMED_STATIC** — `0x0214D5E4`–`0x0214D5F0`, with `r5` the loop index |
| `ComicDeckCreate`'s result is at `root+0x114` | **CONFIRMED_STATIC** — `mov r1,#0x45`; `lsl r1,r1,#2`; `str r0,[r2,r1]` |
| The array has four entries | **PLAUSIBLE** — `+0x118` to `+0x124` before `BattleAI_Create` at `+0x128`; the loop bound was not read |
| Both arm9 `+0x56c` writers install the gauge the same way | **CONFIRMED_STATIC** — `orr #1`, `orr #0x100`, `str …,[gauge+0x3c]`, then the store |
| The `+0x56c` mechanism belongs to `ComicDeck.cpp` | **CONFIRMED_STATIC** — both writers and the GDB reader `0x020784E4` fall between the module's bracketing allocation tags |
| `[char+0x1b4]` is one of the seven large managers | **REFUTED** — it is an array element in the root, not a manager |
| The `0x1914` ComicDeck block is four `0x645` per-player decks | **REFUTED** — `0x645` appears nowhere in arm9 as an immediate or a literal |
| `[char+0x1b4]` is a per-player deck object | **PLAUSIBLE** — its gauge is installed by `ComicDeck.cpp`; its allocator is unfound |

## Next angles, ranked

1. **Find what fills `root+0x118`–`root+0x124`.** Names the object outright; narrow search — four stores at known offsets off the root global.
2. **Read the `Battle_CharaCreate` loop bound** in `Battle_Add` to confirm four entries.
3. **Read `Battle_MoveManCreate` `0x02082A50`** (carried) — `0x2648`, in an unexamined module.
4. **Find what initialises the collision managers** (carried).
