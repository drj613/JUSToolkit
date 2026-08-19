# Findings: the dead-deck residual is closed

Loop-Atlas iteration 114. Static.

Iteration 113 left one gap: register-offset and `stm` stores were never swept. Of the
**72 functions** holding a deck pointer, **7** use register-offset and **2** use `stm`.

None writes `deck+0x30` or `deck+0x18EC`.

---

## 1. The seven register-offset stores

```
0x020793EC  strb r1, [r3, r2]              ; byte, indexed
0x02079588  str  r0, [sb, sl, lsl #2]      ; word array
0x02077298  streq ip, [r2, r6, lsl #2]     ; word array
0x021517A8  str  r0, [r3, r2, lsl #2]      ; word array, part of a read-modify-write
0x0215380C  strb r6, [r7, r1]              ; byte, indexed
0x0214E5CC  str  r0, [r3, ip, lsl #2]      ; word array, bit-set idiom
0x0214E5E4  str  r0, [r1, ip, lsl #2]      ; word array, same idiom
```

All are **scaled array element writes or byte writes** — none has the shape of a
fixed-offset table-base store, and none of the bases (`r3`, `sb`, `r2`, `r7`, `r1`) is a deck.

## 2. The two `stm`

```
0x02152FE8  ldm r7!, {r0, r1, r2, r3}
0x02152FEC  stm r6!, {r0, r1, r2, r3}
0x02152FF0  ldm r7,  {r0, r1, r2, r3}
0x02152FF4  stm r6,  {r0, r1, r2, r3}
```

A 32-byte block copy (inlined `memcpy`), not a field write. These are in ov0, which
entered scope via a `root+0x114` read. ov0 and ov5 share a load address, so that read may
be a phantom — either way, a block copy at an arbitrary base is not a `+0x30` store.

## 3. Every write form, swept

| form | in scope | writes the fields? |
|---|---|---|
| direct immediate offset | 0 to `+0x30` among holders | no |
| `add` + store split | 0 ROM-wide to `+0x18EC` | no |
| register-offset | 7 | no |
| `stm` | 2 | no |
| Thumb, any form | 0 references to the deck global ROM-wide | no |

`deck+0x30` and `deck+0x18EC` keep the `0` from the constructor's `memset`. Iteration 113's
conclusion stands: **add-entry always returns `0x10000000`**.

## Predictions status

| Claim | Verdict |
|---|---|
| Register-offset or `stm` stores reach `deck+0x30` | **REFUTED** — 7 + 2 in scope, all read individually |
| The 7 register-offset stores are fixed-field writes | **REFUTED** — all scaled array or byte writes |
| The 2 `stm` sites are field writes | **REFUTED** — `ldm`/`stm` 32-byte block copy |
| Every write form has been swept for these two fields | **CONFIRMED_STATIC** — immediate, split, register-offset, `stm`, Thumb |
| Iteration 113's dead-deck conclusion has an unswept residual | **REFUTED** — closed |
| The ov0 `root+0x114` read is genuine | **not claimed** — ov0/ov5 share a load address; irrelevant either way |

## Next angles, ranked

1. **Find how the battle deck is actually populated** (carried) — add-entry is dead; bulk copy from the editor's structures is the remaining candidate.
2. **Read `KomaList_Create` `0x0214F5C4`** (carried).
3. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
4. **Read `Battle_MoveManCreate` `0x02082A50`** (carried) — `0x2648`, unexamined module.
