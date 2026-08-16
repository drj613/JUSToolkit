# Findings: `char+0x130` is the shared view every ov6 subsystem passes around

Loop-Atlas iteration 87. Static.

The three address-taken fields from iteration 86 are **embedded sub-objects**, not arrays.
Two constructors initialise them, both fully listed below.

`char+0x130`'s address is taken **29 times** in ov6, concentrated in the three subsystems
the map already covers: state dispatch, spawn dispatch, and hit resolution. These systems
get the view, not the character itself.

---

## 1. Two constructors, twelve bytes each

```
0x02156B30  ldr r2, [r4, #0x1b4]
0x02156B34  mov r1, r4
0x02156B38  add r0, r4, #0x130
0x02156B3C  add r3, r4, #0x7c
0x02156B40  bl  #0x215fb7c

0x02156B44  ldr r1, [r4, #0x1b4]
0x02156B48  add r0, r4, #0x120
0x02156B4C  add r2, r4, #0x130
0x02156B50  bl  #0x215fab8
```

Both callees are three instructions:

```
0x0215FB7C  str r1, [r0, #8]      ; +0x130 +0x8 = the character
0x0215FB80  stm r0, {r2, r3}      ; +0x130 +0x0 = [char+0x1b4], +0x4 = &char+0x7c
0x0215FB84  bx lr

0x0215FAB8  str r1, [r0, #4]      ; +0x120 +0x4 = [char+0x1b4]
0x0215FABC  str r2, [r0]          ; +0x120 +0x0 = &char+0x130
0x0215FAC0  bx lr
```

| sub-object | size | layout |
|---|---|---|
| `char+0x120` | 8 bytes | `+0x0` → `&char+0x130`; `+0x4` → `[char+0x1b4]` |
| `char+0x130` | ≥ `0xC` bytes | `+0x0` → `[char+0x1b4]`; `+0x4` → `&char+0x7c`; `+0x8` → the character |
| `char+0x7c` | unknown | address only; handed to `char+0x130+0x4` |

Both carry a back-pointer to the character's data block `[char+0x1b4]`, and `+0x130`
carries the character itself. This is the shape of a **view**: a small embedded struct so
generic code gets an address instead of the whole character.

`stm r0, {r2, r3}` at `0x0215FB80` is a store-multiple used as a two-field write — a
live example of the `stm` blind spot from iterations 76 and 84.

## 2. Where `+0x130` goes

Address-taken sites for each field in ov6:

| field | sites |
|---|---|
| `+0x07C` | 5 |
| `+0x120` | 4 |
| **`+0x130`** | **29** |

The 29, by function:

| uses | function | what it is |
|---|---|---|
| **10** | `0x02159EF8` | the per-character state dispatcher (map claim 4); also hosts the accumulator flush at `0x0215A300` |
| **4** | `0x021574CC` | the 13-way spawn dispatcher (map claim 3) |
| 4 | `0x0215A978` | — |
| 2 | `0x02156A38` | `Battle_CharaCreate`, the two constructor calls above |
| 2 | `0x02157958` | — |
| **2** | `0x02158B20` | hit resolution (map claim 8) |
| 2 | `0x0215EAEC` | — |
| 1 each | `0x0215CE28`, `0x0215D3B4`, `0x0215D53C` | — |

Three of the map's biggest claims — state dispatch, spawn dispatch, hit resolution — all
take the address of the same embedded view. These were mapped independently over many
wakes; the shared handle is convergence from a separate direction.

`char+0x7c`'s five sites include `0x02158B20` (hit resolution) and `0x021586D0`, placing
it on the damage side, not general-purpose.

## 3. Hazard: `+0x130` is also a ColPrm record field

The ColPrm record also has a `+0x130` — one of its four damage fields, read at
`0x02158BAC`. Different object, same offset. `0x02158B20` touches **both**: the record's
`+0x130` as a value and the character's `+0x130` as an address.

This is the eighth coincidental offset reuse, and the most dangerous — both live in one
function.

## Predictions status

| Claim | Verdict |
|---|---|
| `char+0x120` is an 8-byte sub-object | **CONFIRMED_STATIC** — `0x0215FAB8` writes `+0x0` and `+0x4`, then returns |
| `char+0x130` is a sub-object of at least `0xC` bytes | **CONFIRMED_STATIC** — `0x0215FB7C` writes `+0x0`, `+0x4`, `+0x8` |
| `char+0x130+0x8` is a back-pointer to the character | **CONFIRMED_STATIC** — `str r1,[r0,#8]` with `r1 = r4` from `0x02156B34` |
| `char+0x130+0x4` holds `&char+0x7c` | **CONFIRMED_STATIC** — `r3 = char+0x7c` at `0x02156B3C`, stored by the `stm` |
| These fields are arrays | **REFUTED** *(iteration 86's guess)* — they are embedded structs with back-pointers |
| `char+0x130`'s address is taken 29 times in ov6 | **CONFIRMED_STATIC** — full scan, grouped by function |
| The state, spawn and hit-resolution paths share this handle | **CONFIRMED_STATIC** — `0x02159EF8` ×10, `0x021574CC` ×4, `0x02158B20` ×2 |
| `char+0x7c` is general-purpose | **REFUTED** — its 5 sites cluster on the damage side |
| The ColPrm record's `+0x130` and the character's `+0x130` are the same thing | **REFUTED** — different objects; `0x02158B20` uses both |
| The size of `char+0x7c` is known | **not claimed** — only its address is ever taken |

## Next angles, ranked

1. **Read `0x02159EF8`'s ten uses of `char+0x130`.** It is the heaviest consumer by far
   and already the map's most-cited unresolved function; ten address-takes of one view
   should expose what the view is *for*.
2. **Size `char+0x7c`** by finding what its callees write through it — `0x02158B20` and
   `0x021586D0` are the damage-side users.
3. **Name the arm9 `+0x56c` struct** (carried) — candidate `memset(r7+0x8, 0x5e0)` at
   `0x02076C2C`.
4. **Dead-field sweep of the ColPrm record** (carried).
