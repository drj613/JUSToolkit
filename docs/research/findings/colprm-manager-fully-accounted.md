# Findings: the ColPrm manager's `0xFB54`, fully accounted

Loop-Atlas iteration 120. Static.

Guard 13 makes split bases report their **real** offset instead of the low half. This
removed three phantom fields and revealed a fourth base — `+0x454` — the start of
**128 ColPrm records of `0x188` bytes, embedded inline**.

Every byte of the manager's `0xFB54` is now accounted for. The `0x188` record size from
iteration 77 is independently confirmed by the manager's own stride.

---

## 1. Guard 13

Addresses beyond ARM's rotated-immediate reach are built in two steps, often targeting a
**different** register:

```
add r0, r4, #0x354
add r5, r0, #0xe000      ; the real offset is 0xE354
```

Guard 8 sees only the first add. Guard 13 follows up to three chained adds, reporting the
accumulated offset as `addr/combined`.

| struct | before | after |
|---|---|---|
| ColPrm manager | phantom `+0x054`, `+0x254`, `+0x354` | real `+0x454`, `+0xC854`, `+0xDE54`, `+0xE354` |
| ComicDeck player slot | phantom `+0x21C` | `+0x61C`, flagged **CONTAMINATED** (= the struct size) |

The player-slot case demonstrates this well: `+0x61C` equals the `0x61C` stride, so the
size check catches it instead of a plausible-looking `+0x21C` entering the map.

## 2. `+0x454` is 128 embedded records

```
0x0207C54C  add r0, r0, #0xc800        ; bound = +0xC854
0x0207C554  str r3, [lr, #8]
0x0207C558  str r3, [lr, #0xc]
0x0207C55C  add ip, lr, #0x10
0x0207C560  add r1, lr, #0x28
0x0207C564  str r2, [ip]               ; clear +0x10..+0x27, stride 8
0x0207C56C  add ip, ip, #8
0x0207C570  cmp ip, r1
0x0207C578  str r2, [lr, #0x28]
0x0207C57C  str r2, [lr, #0x2c]
0x0207C580  add lr, lr, #0x188         ; the RECORD stride
0x0207C584  cmp lr, r0
0x0207C588  blo #0x207c554
```

`0x454 + 128 × 0x188 = 0xC854` — exactly the next pool's base.

The cleared fields are the record's list heads: `+0x08`, `+0x0C`, `+0x10`–`+0x27`,
`+0x28`, `+0x2C` — matching the layout from iterations 83 and 85, where `+0x08`
holds `0x2C`-byte nodes and `+0x10`/`+0x18`/`+0x20` are list heads.

## 3. The whole manager

| span | contents | size |
|---|---|---|
| `+0x0000`–`+0x0153` | header (43 mapped offsets) | `0x154` |
| `+0x0154`–`+0x0453` | **contact array**, 4 rows × `0xC0` *(corrected iteration 122 — this doc wrongly folded it into the header)* | `0x300` |
| `+0x0454`–`+0xC853` | **128 ColPrm records × `0x188`** | `0xC400` |
| `+0xC854`–`+0xDE53` | `0x80` nodes × `0x2C` → free list `+0x18` | `0x1600` |
| `+0xDE54`–`+0xE353` | 80 nodes × `0x10` → free list `+0x20` | `0x500` |
| `+0xE354`–`+0xFB53` | `0x200` nodes × `0xC` → bucket free list `+0xD8` | `0x1800` |
| | **total** | **`0xFB54`** |

The manager owns its records inline rather than allocating them — explaining why
iteration 109 found a record *free pool* at `+0x08` with no corresponding allocation.

## Predictions status

| Claim | Verdict |
|---|---|
| Guard 13 removes the three ColPrm phantoms and recovers the pool bases | **CONFIRMED_STATIC** — selftest asserts both directions |
| The player slot's `+0x21C` becomes `+0x61C` and is flagged | **CONFIRMED_STATIC** — equals the declared size, caught by the size check |
| `+0x454` begins 128 records of `0x188` | **CONFIRMED_STATIC** — `add lr,lr,#0x188`; bound `+0xC854`; `0x454 + 128 × 0x188 = 0xC854` |
| The record size `0x188` is confirmed independently of iteration 77 | **CONFIRMED_STATIC** — from the manager's stride, not the teardown's `memset` |
| The clearing loop zeroes the record's list heads | **CONFIRMED_STATIC** — `+0x08`, `+0x0C`, `+0x10`–`+0x27`, `+0x28`, `+0x2C` |
| Every byte of `0xFB54` is accounted for | **CONFIRMED_STATIC** — `0x454 + 0xC400 + 0x1600 + 0x500 + 0x1800 = 0xFB54` |
| Records are allocated separately from the manager | **REFUTED** — they are embedded inline |
| This loop links the records onto the `+0x08` free pool | **not claimed** — it only clears them; the linking was not observed here |

## Next angles, ranked

1. **Find where the 128 records are linked onto `+0x08`.** The clearing loop only clears them; iteration 109 proved the pool exists.
2. **Map the header `+0x360`–`+0x453`** — last unexamined span, only `0xF4` bytes.
3. **Read `+0x0EC`, `+0x0F0`, `+0x0F4`** (carried).
4. **Read `Battle_MoveManCreate` `0x02082A50`** (carried).
