# Findings: the ColPrm manager has no unexamined bytes

Loop-Atlas iteration 122. Static.

Iteration 120 recorded a `0xF4`-byte gap at `+0x360`–`+0x453`. **There is no gap.** That region is the tail of the **contact array** (mapped at iterations 56 and 62); the header boundary was mis-stated.

The manager's `0xFB54` now tiles with **zero** unaccounted bytes.

---

## 1. The arithmetic

Two `mla`s index the contact array:

```
0x02081340  mov r1, #0xc0
0x02081344  mla r1, r0, r1, r2      ; row stride 0xC0
0x02081348  mov r0, #0x30
0x0208134C  mla r2, fp, r0, r1      ; element stride 0x30
0x02081350  ldr r1, [r2, #0x10]
```

`0xC0 / 0x30 = 4` elements per row. Based at `+0x154`:

```
0x154 + 4 × 0xC0 = 0x454
```

— exactly where the 128 records begin.

## 2. The corrected layout

| span | contents | size |
|---|---|---|
| `+0x0000`–`+0x0153` | header, 43 mapped offsets | `0x154` |
| `+0x0154`–`+0x0453` | **contact array**, 4 rows × `0xC0` (4 elements × `0x30`) | `0x300` |
| `+0x0454`–`+0xC853` | 128 records × `0x188` | `0xC400` |
| `+0xC854`–`+0xDE53` | `0x80` nodes × `0x2C` → free list `+0x18` | `0x1600` |
| `+0xDE54`–`+0xE353` | 80 nodes × `0x10` → free list `+0x20` | `0x500` |
| `+0xE354`–`+0xFB53` | `0x200` nodes × `0xC` → bucket free list `+0xD8` | `0x1800` |
| | **total** | **`0xFB54`** |

`0x154 + 0x300 + 0xC400 + 0x1600 + 0x500 + 0x1800 = 0xFB54`.

## 3. Why the gap looked real

Iteration 120 put the header at `0x454` bytes because all 43 constructor offsets fell below `+0x360` and the records start at `+0x454`. The contact array is never touched by the constructor — the accumulators write it (iteration 56) — so it was invisible in a constructor-only map.

**A region absent from a constructor is not part of the header.** The reasoning that correctly predicted `+0x154`'s absence at iteration 118 should have prevented extending the header past it two wakes later.

## 4. Confirming the search was sound

Before spotting the arithmetic I scanned all 8 functions holding the manager global for any access in `+0x360`–`+0x453`: **zero hits**. Consistent — the accumulators reach the array by computed index from a base register, never by a fixed offset in that range.

## Predictions status

| Claim | Verdict |
|---|---|
| The contact array has 4 rows of `0xC0` | **CONFIRMED_STATIC** — `0x154 + 4 × 0xC0 = 0x454`, the record base |
| Each row holds 4 elements of `0x30` | **CONFIRMED_STATIC** — `mla` by `0xC0` then `0x30`; `0xC0 / 0x30 = 4` |
| The row count was read from a `cmp` | **REFUTED** — derived from the tiling, as with the `0x10` pool at iteration 119 |
| `+0x360`–`+0x453` is unexamined | **REFUTED** *(iteration 120, mine)* — it is the tail of the contact array |
| The manager's header is `0x454` bytes | **REFUTED** *(iteration 120, mine)* — it is `0x154` |
| Every byte of `0xFB54` is now accounted for | **CONFIRMED_STATIC** — six spans, exact sum, no gaps |
| No manager-global holder accesses `+0x360`–`+0x453` directly | **CONFIRMED_STATIC** — 8 functions scanned, 0 hits |

## Next angles, ranked

1. **Read `+0x0EC`, `+0x0F0`, `+0x0F4`** (carried) — three consecutive header words, no known role.
2. **Enumerate the other `record+0x40` bits** (carried) — `0x200` and `0x800` are known.
3. **Read `Battle_MoveManCreate` `0x02082A50`** (carried) — `0x2648`, never examined.
4. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
