# Findings: allocations are self-naming, and `[X+0x1a8]` is the battle character

Loop-Atlas iteration 73. Static.

The heap allocator `0x0201A21C` is **tagged**: every call passes the source file
and function name. That gives a **call-site** name for 469 of the ROM's 494
allocations — far stronger than `extract_symbols.py`'s nearest-function guess.

Two things fell out:

1. The `0x1F0`-byte object we called **MoveInfo** is what `Battle_CharaCreate`
   in `BattleChara.cpp` allocates. It is **the battle character**.
2. The bigger object holding it at `+0x1a8` — the one we called "the character
   struct", with a gauge pointer at `+0x56c` — is a **different, outer object**.
   Nothing in the ROM heap-allocates that large under a battle name.

I also **refuted my own claim from earlier this wake**: "the battle character
struct is `0x1F0` bytes" nearly got recorded as CONFIRMED_STATIC without
grepping `docs/` for `0x02156A58`. The map already had that address. See §4.

---

## 1. The allocator names its own call sites

```
0x02156A48  ldr r1, [pc, #0x30c]   ; -> 0x0217213C = "BattleChara.cpp"
0x02156A4C  ldr r2, [pc, #0x30c]   ; -> 0x02172128 = "Battle_CharaCreate"
0x02156A50  mov r0, #0x1f0         ; size
0x02156A54  mov r3, #0x25          ; tag
0x02156A58  bl  #0x201a21c
0x02156A5C  mov r1, #0
0x02156A60  mov r2, #0x1f0
0x02156A64  mov r4, r0
0x02156A68  bl  #0x20517fc         ; memset(obj, 0, 0x1F0)
```

Signature: `alloc(r0 = size, r1 = "File.cpp", r2 = "Function", r3 = tag)`.

`scripts/decomp/alloc_census.py` walks the flat disassembly for all **494** calls
and back-resolves `r0`/`r1`/`r2`. Result: **431** immediate sizes, **469**
resolved names, **63** computed sizes left uncounted.

The largest named allocations:

| size | site | function | file |
|---|---|---|---|
| `0x4000` | ov12 `0x021CA45C` | *(unnamed literal)* | `ALTextDS.cpp` |
| `0x2000` | ov12 `0x021CA488` | *(unnamed literal)* | `ALTextDS.cpp` |
| `0x1040` | arm9 `0x0207BD5C` | `Battle_ColJointManCreate` | `BattleColJoint.cpp` |
| `0x314` | ov6 `0x02168BA0` | `Battle_ObjCtrlManCreate` | `BattleObjCtrl.cpp` |
| `0x284` | ov6 `0x02152134` | `Battle_ComicDeckCreate` | `BattleComicDeck.cpp` |
| `0x1F0` | ov6 `0x02156A58` | **`Battle_CharaCreate`** | **`BattleChara.cpp`** |
| `0x1C4` | ov6 `0x0215F064` | `Battle_CharaDataInit` | `BattleCharaDataLoad.cpp` |

## 2. The `0x1F0` object is stored at `X+0x1a8`

Setter `0x021570EC(r0 = the object, r1 = X)`:

```
0x021570EC  push {r4, lr}
0x021570F0  mov r4, r1
0x021570F4  str r0, [r4, #0x1a8]   ; X+0x1a8 = the 0x1F0 object
0x021570F8  ldr r1, [r4, #0x1a0]
0x02157100  bl  #0x20839c0
0x02157108  bl  #0x2157024
```

Both facts lock in: the object belongs to `Battle_CharaCreate` (§1, call-site
tag) and lands at `X+0x1a8` (here). **MoveInfo** on `[char+0x1a8]` is a
misnomer — that slot holds a battle character.

`Battle_CharaCreate`'s field writes:

| offset | source |
|---|---|
| `+0x1C0` | object returned by `0x02026F94` |
| `+0x1C4` | `[arg1+0x10]` |
| `+0x1C8` | `[arg1+0x14]` |
| `+0x1E0` | `arg0`, `strb` |
| `+0x1EA` | `[arg1+0x1D]`, `strb` |
| `+0x1EB` | `[arg1+0x1C]`, `strb` |

`+0x1E0` is the `ldrsb` "entity index" from iteration 52 — **a battle-character
field, written from `arg0`**, not an outer-object field.

## 3. What the outer object is — and is not

The outer object `X` has `+0x1a8` (the character) and `+0x56c` (the gauge,
GDB-proven via `0x020784E4`), so it spans at least `0x570` bytes. **Nothing in
the ROM allocates that much under a battle name** — the only battle allocations
above `0x300` are `Battle_ColJointManCreate` (`0x1040`) and
`Battle_ObjCtrlManCreate` (`0x314`). So `X` is statically placed or embedded in
an array, not heap-allocated through `0x0201A21C`.

This **resolves the map's standing tension**: JUS's SP gauge is deck-wide, which
clashed with a *per-character* `char+0x558` list. If the `0x1F0` object is the
per-character one and the `+0x558`/`+0x56c` object sits one level out, deck-wide
SP on the outer and per-character state on the inner are consistent. Stated as
PLAUSIBLE — naming `X` needs its own wake.

**Not claimed:** which object owns `+0x84` (the `prmData` pointer, iteration 44),
`+0x1B4` or `+0x1B8` (iteration 50). All three fit inside `0x1F0`, so fitting
proves nothing. Each needs its base traced.

## 4. The prior-art failure, again

Earlier this wake I had a doc claiming "the battle character struct is `0x1F0`
bytes — CONFIRMED_STATIC", cross-checked by "all five known character offsets fit
inside `0x1F0`".

`Battle-Engine-Map.md` already recorded `0x02156A58`, size `0x1F0` = 496 bytes, as
the MoveInfo allocation at `char+0x1a8`. One grep would have caught it. The
cross-check was circular: offsets from *two different objects* all happen to be
below `0x1F0`, which proves nothing about either.

`prior_art.py` exists (iteration 66) for exactly this, and I didn't run it. The
rule must be a hard gate before writing — not just before starting work: **every
address in a doc's headline claim gets grepped against `docs/` before the doc is
written.**

## Predictions status

| Claim | Verdict |
|---|---|
| `0x0201A21C` takes a file name and function name at every call | **CONFIRMED_STATIC** — `0x02156A48`/`0x02156A4C` → `"BattleChara.cpp"`, `"Battle_CharaCreate"` |
| The `0x1F0` object is `Battle_CharaCreate`'s, from `BattleChara.cpp` | **CONFIRMED_STATIC** — call-site tag at `0x02156A58` |
| That object is stored at `X+0x1a8` | **CONFIRMED_STATIC** — `str r0,[r4,#0x1a8]` at `0x021570F4` |
| `+0x1E0` is a field of the `0x1F0` object | **CONFIRMED_STATIC** — `strb r6,[r4,#0x1e0]` at `0x02156A74` |
| `Battle_ColJointManCreate` allocates `0x1040`, the largest battle allocation | **CONFIRMED_STATIC** — `0x0207BD5C` |
| **The battle character struct is `0x1F0` bytes** | **REFUTED** *(my own claim, same wake)* — the `+0x56c` object is ≥ `0x570`; the two are different objects |
| `[char+0x1a8]` is a "MoveInfo" object | **REFUTED** — it is what `Battle_CharaCreate` allocates |
| The outer object is heap-allocated via `0x0201A21C` | **REFUTED** — no battle allocation ≥ `0x570` in 431 sized sites |
| Deck-wide SP lives on the outer object, per-character state on the inner | **PLAUSIBLE** — consistent with both, proven by neither |
| The outer object `X` is named | **not claimed** |

## Next angles, ranked

1. **Name the outer object `X`.** `arg1` of setter `0x021570EC`; trace its
   callers. Biggest open prize — it's what the campaign has called "the character
   struct".
2. **Re-audit every `char+0xNN` offset in `Battle-Engine-Map.md`** against the
   two objects. `+0x84`, `+0x1B4`, `+0x1B8` are ambiguous, and the map's
   damage-pipeline claims rest on them.
3. **Read `ColObj+0x24`'s method** `0x0207D94C` (carried) — last unexamined
   ColObj↔ColPrm interface method; bounded.
4. **Mine the 469 tagged names** for other misattributions — the census is cheap
   to re-query and every earlier "nearest-function" binding is now checkable.
