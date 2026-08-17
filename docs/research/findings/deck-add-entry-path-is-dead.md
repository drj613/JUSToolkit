# Findings: the battle deck's add-entry path never succeeds

Loop-Atlas iteration 113. Static.

Four independent routes to a deck pointer were enumerated. **None writes `deck+0x30`.**
The block is `memset` to zero at creation, so the ID table base and count stay `0`,
the bounds check rejects every id, and **add-entry always returns `0x10000000`**.

The 96 unattributed stores from iteration 112 all belong to other objects.

---

## 1. Every route to the deck pointer

| route | reach | writes `+0x30`? |
|---|---|---|
| the global `0x0214BD80`, ARM | 55 holder functions | **no** |
| one call hop from a holder | 79 distinct callees | **no** — see below |
| the global, **Thumb** | **0 references ROM-wide** | n/a |
| `root+0x114` | 21 sites in 17 functions | **no** |

The one call-hop hit was `0x0207AFB8`, `str r4,#0x30` inside **`Battle_ColObjCreate`** —
a `0x40`-byte ColObj writing its own `+0x30`. Coincidental offset match, not the deck.

**No Thumb instruction anywhere in the ROM loads `0x0214BD80`**, so the 375 Thumb
`str [rN,#0x30]` sites cannot reach a deck.

## 2. And nothing writes the count

`deck+0x18EC` exceeds a 12-bit immediate, requiring an `add` plus a store.
**Zero such pairs exist ROM-wide** (iteration 112).

## 3. What follows

`ComicDeckCreate` does `memset(deck, 0, 0x1914)`, so the count starts at `0`. Then:

```
0x02076CC0  ldr  r0, [r0, #0x8ec]   ; count = 0
0x02076CC4  cmp  r1, r0
0x02076CC8  movhs r0, #0            ; every id >= 0 fails
```

`0x02076C98` returns `0` for every input → `0x02076D30` returns `0` → `0x02076E38`
returns **`0x10000000`** and never links a node.

The entire deck-entry mechanism mapped in iterations 106–110 — the 16-node array,
free/active lists, unique-by-ID rule, the two walkers — is **machinery that never
runs in this build**.

## 4. What this does not say

This is the **battle-side** ComicDeck, created by `ComicDeckCreate` in arm9 via
`Battle_Add`. The ov5 deck *editor* allocates its own objects — `KomaList_Create`
`0x554`, `KomaEdit_Create` `0x4F4`, `KomaState_Create` `0x46C`. Decks work;
**this object's add path is unused**.

Fifth vestigial system, after ColPrm `+0x68`, `+0xE8`, `+0x140` and the view's 16-slot
handler table.

## Predictions status

| Claim | Verdict |
|---|---|
| No ARM holder of the deck global writes `+0x30` | **CONFIRMED_STATIC** — 0/55 |
| No callee of a holder writes `deck+0x30` | **CONFIRMED_STATIC** — 1/79 hit, `Battle_ColObjCreate`'s own field |
| No Thumb code references the deck global | **CONFIRMED_STATIC** — 0 pc-relative loads of `0x0214BD80` ROM-wide |
| No function reading `root+0x114` writes `+0x30` | **CONFIRMED_STATIC** — 0/17 |
| Nothing writes `deck+0x18EC` | **CONFIRMED_STATIC** *(iteration 112)* — 0 `add`+`str` pairs ROM-wide |
| Count is `0` at runtime | **CONFIRMED_STATIC** — `memset(deck, 0, 0x1914)`, no writer |
| `0x02076C98` returns `0` for every id | **CONFIRMED_STATIC** — `cmp r1, r0` vs zero count, `movhs r0,#0` |
| Add-entry can succeed | **REFUTED** — always returns `0x10000000` |
| The 96 stores from iteration 112 write the deck | **REFUTED** — none is reachable with a deck pointer |
| Decks do not work in this game | **REFUTED** — this is the battle-side object; the ov5 editor has its own |
| A register-offset or `stm` write reaches these fields | **not claimed** — neither form swept; ARM chains beyond one call hop not checked |

## Next angles, ranked

1. **Sweep `stm` and register-offset stores** against the 55 holders and 17
   `root+0x114` readers — the last unswept write form.
2. **Find how the battle deck is actually populated** — likely a bulk copy from the
   ov5 editor's structures.
3. **Read `KomaList_Create` `0x0214F5C4`** (carried) — the editor's own container.
4. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
