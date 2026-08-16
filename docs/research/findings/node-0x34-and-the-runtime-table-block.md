# Findings: `node+0x34` is the ID-table entry — and the table itself is runtime

Loop-Atlas iteration 110. Static.

The `0xC`-byte ID table at `deck+0x30` **cannot be read statically** — neither pointer is
a ROM address. But the attempt settled that **`node+0x34` holds the ID table entry**,
closing the deck-entry construction chain.

---

## 1. Both tables are runtime

`deck+0x30` has **no word store in `ComicDeck.cpp`** (`0x02075FBC`–`0x02078D00`);
the only `+0x30` writes are halfword stores to a different base.

`deck+0x38` is set from a **virtual call's return value**:

```
0x020760D8  ldr r2, [r0]
0x020760DC  ldr r2, [r2, #0x2c]
0x020760E0  blx r2                    ; a vtable slot
0x020760E4  ldr r1, [pc, #0x2d0]
0x020760E8  ldr r1, [r1]              ; the deck
0x020760EC  str r0, [r1, #0x38]
```

`deck+0x18EC` (the count) has no store in the module either — the deck's static data is
loaded at runtime, presumably from the game archive. The table is not at any computable ROM
address.

**Blocked by the static-only constraint** (same class as `[[0x02172984]+0xC]` at
iteration 95).

## 2. `node+0x34` is the entry pointer

Inside add-entry `0x02076E38`:

```
0x02076EB0  mov  r1, sb               ; the id
0x02076EB4  bl   #0x2076c98           ; the bounds-checked lookup
0x02076EB8  movs r5, r0               ; r5 = [deck+0x30] + id*0xC
...
0x02076F3C  str  r5, [r4, #0x34]      ; node+0x34 = the table entry
```

Every deck node carries a pointer to its own static definition, computed once at add time.

## 3. Why the duplicate check works

The duplicate check (iteration 108) reads `[node+0x34]` and compares its **first
halfword** to the requested id. With `+0x34` now known to be `[deck+0x30] + id*0xC`,
**each table entry stores its own id in its first halfword**.

Could be a dense table where entry `i` carries id `i`, or just an id field that happens to
be first — indistinguishable here.

## 4. The deck entry, end to end

| step | |
|---|---|
| validate | `a < 5`, `b < 4`, id resolves (iteration 109) |
| look up | `r5 = [deck+0x30] + id*0xC` |
| allocate | unlink a node from `slot+0x560` |
| attach | link it onto `slot+0x558` |
| clear | `memset(node+0x0C, 0, 4)`; `memset(node+0x10, 0, 0x22)` |
| fill | `node+0x0C = id`; `node+0x0E = (a & 0xF) \| ((b & 0xF) << 4)`; `node+0x34 = r5` |

## Predictions status

| Claim | Verdict |
|---|---|
| `node+0x34` receives the ID-table lookup result | **CONFIRMED_STATIC** — `movs r5,r0` at `0x02076EB8` after `bl #0x2076c98`; `str r5,[r4,#0x34]` at `0x02076F3C` |
| Every node points at its own static definition | **CONFIRMED_STATIC** — set once during add |
| Table entries carry their id in the first halfword | **CONFIRMED_STATIC** — required for the duplicate check to work against `[node+0x34]` |
| The `0xC`-byte ID table can be dumped from the ROM | **REFUTED** — `deck+0x30` has no word store in the module |
| `deck+0x38` is a ROM address | **REFUTED** — it is a virtual call's return, `blx [[r0]+0x2c]` at `0x020760E0` |
| `deck+0x18EC` is set inside `ComicDeck.cpp` | **REFUTED** — no store to it in `0x02075FBC`–`0x02078D00` |
| The table is dense with entry `i` holding id `i` | **not claimed** — indistinguishable here from an id field that is merely first |
| The deck's static data is loaded from the game archive | **PLAUSIBLE** — the pointers arrive at runtime; the loader was not traced |

## Next angles, ranked

1. **Find who writes `deck+0x30` and `deck+0x18EC`.** Outside `ComicDeck.cpp` — ROM-wide
   search using deck global `0x0214BD80` as discriminator. Names the loader even if the
   data stays runtime.
2. **Read `0x02076D00`** (carried) — runtime table, but static indexing: stride `0x18`,
   two signed bytes at `+0x8`/`+0x9`.
3. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
4. **Trace the `0x64` in `0x020785B8`** (carried).
