# Findings: the deck global's 55 holders are mostly the koma editor

Loop-Atlas iteration 111. Static.

No writer of `deck+0x30` among the holders, but a useful distribution: of the **55**
functions holding the deck global, **37 are in ov5** (`KomaList.cpp`, `KomaEdit.cpp`,
`KomaState.cpp`, `DeckMake.cpp`, `DatabasePersonal.cpp`).

The deck belongs to the **koma/deck editor**, not battle code.

Also: the **fourth mask bug**, same signature as the previous three.

---

## 1. The mask bug

```python
(x & 0x0F7F0000) == 0x059F0000      # can never match
```

`0x0F7F0000` clears bit 23 (the `U` bit), so `0x9F` in bits 23–16 is unreachable.
`ldr r0,[pc,#0x20]` is `0xE59F0020`; masked it becomes `0x051F0000`. The scan returned
**0 holders** — that's what made it obvious. Correct mask: `0x0FFF0000`, compare `0x059F0000`.

Fourth instance, after the `bl` mask, the `ldr` Rd/Rn mask, and the `mov` immediate mask.
Each produced a clean zero rather than an error.

## 2. Where the deck global is held

| region | holder functions |
|---|---|
| **ov5** | **37** |
| arm9 | 16 |
| ov6 | 1 |
| ov11 | 1 |

ov5's tagged allocations: `KomaList_Create` (`0x554`), `KomaEdit_Create` (`0x4F4`),
`KomaState_Create` (`0x46C`), `Database_PersonalCreate` (`0x1AC`), plus `DeckMake.cpp`
and `ComicDeckMakeDisp.cpp` from earlier censuses.

The editing UI overwhelmingly owns this structure. Battle code (ov6) touches the global **once**.

## 3. The single ov6 holder

`0x0215FAC4` — calls the character view's reset `0x0215FB88` and issues selector 5
(iterations 92, 89). Battle code's only direct reach for the deck global is inside the
view/CharaInfo path.

## 4. `deck+0x30` is not written by any holder

No word store to `+0x30` in any of the 55. The only hit was `str [r13,#0x30]` — a stack
store in `0x020790F0`.

Whoever fills the ID table base receives the deck **as an argument**, not via the global.
Different search: callers that pass the deck onward.

## 5. On the "koma" naming

Iterations 107–110 recorded the `0x50` node's shape — unique by ID, a 4-bit pair, a
pointer to a static definition — and declined to call it a koma record.

Now there's a module family behind the name: the owning overlay is full of `Koma*.cpp`.
Still indirect — module company is not a symbol — so it stays **not claimed**, but there's
somewhere specific to look next.

## Predictions status

| Claim | Verdict |
|---|---|
| `(x & 0x0F7F0000) == 0x059F0000` matches a pc-relative load | **REFUTED** — the mask clears the `U` bit; the compare is unreachable |
| 55 functions hold the deck global | **CONFIRMED_STATIC** — corrected scan, all 16 regions |
| ov5 holds it 37 times, more than all other regions combined | **CONFIRMED_STATIC** — arm9 16, ov6 1, ov11 1 |
| ov5 is the koma/deck editing overlay | **CONFIRMED_STATIC** — `KomaList_Create`, `KomaEdit_Create`, `KomaState_Create`, `Database_PersonalCreate` tags |
| Battle code holds the deck global in one place | **CONFIRMED_STATIC** — ov6 `0x0215FAC4`, the view-reset caller |
| Some holder writes `deck+0x30` | **REFUTED** — no word store to `+0x30` in any of the 55 |
| The table loader fetches the deck from the global | **REFUTED** — it must receive the deck as an argument |
| The `0x50` node is a koma record | **not claimed** — the owning overlay is `Koma*.cpp`, which is company, not a symbol |

## Next angles, ranked

1. **Search ov5 for stores to `+0x30` on any base**, then check which of those bases is the
   deck. The editor is where the table would be populated.
2. **Read `KomaList_Create` `0x0214F5C4`** (`0x554` bytes) — the largest ov5 allocation and
   the most likely owner of a koma table.
3. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
4. **Add the pc-relative-load mask to a shared helper** so a fifth instance is impossible.
