# Findings: SP lives at `player_slot+0x5C8`

Loop-Atlas iteration 105. Static.

`0x020781E4` — the SP-apply function view handlers tail-call — is three lines:
**`[slot+0x5C8] += amount`**, refused when negative and `[slot+0x5CF]` is non-zero.

`+0x5C8` has **11 accesses**, the most of any slot field. Reached from a character as
`[[char+0x1b4]+0x5C8]` — deck-wide SP, exactly as predicted.

Hypothesis that the unmapped `+0x100`–`+0x557` band was hidden by split bases: **refuted**.

---

## 1. SP-apply

```
0x020781E4  push {r4, r5, r6, lr}
0x020781E8  mov  r4, r0              ; the player slot
0x020781EC  cmp  r1, #0
0x020781F0  bge  #0x207824c          ; positive -> the unguarded path
0x020781F4  add  r0, r4, #0x500
0x020781F8  ldrsb r0, [r0, #0xcf]    ; slot+0x5CF
0x020781FC  cmp  r0, #0
0x02078200  popne {r4, r5, r6, pc}   ; guard set -> refuse the drain
0x02078204  ldr  r0, [r4, #0x5c8]
0x0208820C  add  r0, r0, r1
0x02078210  str  r0, [r4, #0x5c8]    ; SP += amount
```

Non-zero `+0x5CF` blocks **only** negative amounts — gains always apply. `+0x5CC` and `+0x5CD`
are read the same way at `0x02078290`.

## 2. The slot map, 14 fields

| offset | accesses | what |
|---|---|---|
| `+0x058` | 2 | addr |
| `+0x558` | 1 | list head, walked by `0x0207871C` |
| `+0x55C`, `+0x560`, `+0x564` | 1 each | zeroed per slot; `+0x560` address also taken |
| `+0x56C` | 5 | the gauge pointer |
| **`+0x5C8`** | **11** | **SP total** |
| `+0x5CC`, `+0x5CD`, `+0x5CF` | 1 each | signed-byte guards |
| `+0x5E8`, `+0x5EC` | 4, 2 | written in ov6, read in arm9 |
| `+0x5F0`, `+0x5F3`, `+0x5F5`, `+0x5F6` | 1 each | byte cluster |

## 3. Why a raw scan reported `+0xCC` and `+0xCF`

`ldrsb`, `ldrsh`, and `strh` carry only an **8-bit** offset, so anything above `+0xFF`
must split — `add r0,r4,#0x500` then `ldrsb r0,[r0,#0xcf]`.

A raw scan of `ComicDeck.cpp` reported `0xA0`, `0xCC`, `0xCD`, `0xCF`, `0xDA`,
`0xE0`–`0xE3`, `0xF0`–`0xFC`. **All phantom** — the real fields are `0x500` higher.
`struct_fields.py` guard 9 resolves these; the ad-hoc scan did not.

## 4. The unmapped band is real

Resolving split bases moved offsets *up* into `0x5Cx` rather than filling the gap.
After 9 anchors with split resolution, **`+0x059`–`+0x557` remains untouched by
`ComicDeck.cpp`**.

## 5. A guard that cost a field

The first run missed `+0x5C8`. Guard 2 stops a walk when the anchor register is written,
and `popne {r4, r5, r6, pc}` at `0x02078200` writes `r4` — truncating the walk two
instructions before the SP field.

Fixed by anchoring past it. Conditional early-returns need their own anchor.

## Predictions status

| Claim | Verdict |
|---|---|
| `slot+0x5C8` is the SP total | **CONFIRMED_STATIC** — `ldr`/`add`/`str` at `0x02078204`–`0x02078210`, 11 accesses overall |
| A non-zero `+0x5CF` blocks SP loss but not gain | **CONFIRMED_STATIC** — the guard sits behind `bge #0x207824c` |
| SP is reachable from a character as `[[char+0x1b4]+0x5C8]` | **CONFIRMED_STATIC** — `+0x1b4` is the player slot (iteration 103) |
| `0xCC`, `0xCF`, `0xE0`–`0xE3` are ComicDeck fields | **REFUTED** — split bases; the real offsets are `0x500` higher |
| Split bases explain the unmapped `+0x100`–`+0x557` band | **REFUTED** — resolving them populated `0x5Cx`, not the gap |
| `+0x059`–`+0x557` is untouched by `ComicDeck.cpp` | **CONFIRMED_STATIC** — 9 anchors with split resolution, nothing in the band |
| `+0x5CC` and `+0x5CD` are guards like `+0x5CF` | **PLAUSIBLE** — read as signed bytes at `0x02078290`; their branches were not traced |
| The slot map is complete | **REFUTED** — 14 fields of `0x61C`; the payload band is still unexplained |

## Next angles, ranked

1. **Find the module that owns `+0x059`–`+0x557`.** Try ov6 koma/deck-UI and `Battle_ComicDeckCreate` `0x02152110` at root`+0xF4`.
2. **Trace `+0x5CC` and `+0x5CD`** at `0x02078290` — likely `+0x5CF` siblings.
3. **Follow the `+0x558` node list** (carried) — nodes carry a byte at `+0x40`.
4. **Re-audit `char+0xNNN` claims above `0x200`** (carried).
