# Findings: the three disputed `char+0xNN` offsets all belong to the battle character

Loop-Atlas iteration 86. Static.

Iteration 73 split "the character struct" into three objects and left `+0x84`, `+0x1B4`
and `+0x1B8` unassigned — the campaign's oldest correctness debt, since the
damage-pipeline claims depend on them.

**All three belong to the ov6 `0x1F0` battle character.** The map was right all along.
Eight more character fields fell out, plus one real hazard: `+0x84` also exists on the
NoteTrack.

---

## 1. `+0x1B4` and `+0x1B8`, from the constructor

Anchoring `struct_fields.py` on `Battle_CharaCreate`'s allocation register yields 16
offsets, all below `0x1F0`:

| offset | accesses | kind |
|---|---|---|
| `+0x07C` | 2 | addr |
| `+0x120` | 2 | addr |
| `+0x130` | 4 | addr |
| `+0x1A0` | 8 | ldr,str |
| `+0x1A4` | 2 | str |
| `+0x1A8` | 12 | ldr |
| **`+0x1B4`** | **10** | ldr,str |
| **`+0x1B8`** | **4** | ldr,str |
| `+0x1BC` | 6 | ldr,str |
| `+0x1C0` | 8 | ldr,str |
| `+0x1C4` | 2 | str |
| `+0x1C8` | 2 | str |
| `+0x1CC` | 2 | str |
| `+0x1E0` | 6 | ldrsb/split,strb |
| `+0x1EA` | 2 | strb |
| `+0x1EB` | 2 | strb |

`+0x1B4` is touched **ten** times and `+0x1B8` four, both on the register holding the
object `Battle_CharaCreate` just allocated. Case closed.

Eight offsets are new to the map: `+0x07C`, `+0x120`, `+0x130` (all address-taken —
sub-regions or array bases), `+0x1A0`, `+0x1A4`, `+0x1BC`, `+0x1CC`, and `+0xA2` from §2.

## 2. `+0x84`, from a base that also carries `+0x1A0`

The `prmData` store alone is not enough:

```
0x0215F6A4  bl  #0x21702bc          ; Battle_PrmDataInit
0x0215F6AC  ldr r1, [r6]            ; r6 walks a 0x1C-byte descriptor array
0x0215F6B0  str r0, [r1, #0x84]
0x0215F6B8  add r6, r6, #0x1c
```

`[r6]` is a pointer from a table, not visibly a character. None of the four `+0x84`
stores in ov6 shares a character companion offset.

A *reader* settles it. In `0x02159A60`:

```
0x02159A70  ldr r5, [r0, #0x10]
0x02159A74  ldrh r0, [r5, #0xa2]
0x02159A78  ldr r1, [r5, #0x1a0]    ; +0x1A0 -- a confirmed character field
...
0x02159AA0  ldr r0, [r5, #0x84]     ; same base, never reassigned
```

`r5` carries both `+0x1A0` and `+0x84` with no intervening write. `+0x1A0` is touched
eight times inside `Battle_CharaCreate`, so `r5` is a battle character and `+0x84` is a
character field. `+0xA2` comes free.

## 3. Hazard: `+0x84` is also a NoteTrack field

The 73-case dispatcher `0x02157A44` reads `+0x84` five times off `r0`, and `r0` is the
**NoteTrack** there, not the character. The NoteTrack's `+0x7C`/`+0x80`/`+0x84`/`+0x88`
were already recorded as pointer fields at iteration 49.

`+0x84` is live on two different objects in the same overlay — the seventh coincidental
offset reuse in this campaign. Any future `+0x84` hit must have its base established
before attribution.

This also weakens §2's store. `[r6]+0x84` receiving `prmData` fits a character, but a
NoteTrack would match equally well. The descriptor array's element type is **not claimed**.

## 4. Where this leaves the three objects

| object | size | disputed offsets |
|---|---|---|
| ov6 battle character (`Battle_CharaCreate`) | `0x1F0` | **all three: `+0x84`, `+0x1B4`, `+0x1B8`** |
| the pooled entity (`0x020834D4`) | — | none |
| arm9 struct with the `+0x56c` gauge | ≥ `0x570` | none |

The damage-pipeline claims that read `[char+0x1a8]` and `[char+0x1b4]` target the ov6
character throughout. No map claim needs revising.

## Predictions status

| Claim | Verdict |
|---|---|
| `+0x1B4` is a field of the `0x1F0` battle character | **CONFIRMED_STATIC** — 10 accesses on the allocation register inside `Battle_CharaCreate` |
| `+0x1B8` is a field of the `0x1F0` battle character | **CONFIRMED_STATIC** — 4 accesses, same anchor |
| `+0x84` is a field of the `0x1F0` battle character | **CONFIRMED_STATIC** — `0x02159AA0`, same base as `+0x1A0` at `0x02159A78`, `r5` unreassigned |
| The `prmData` store proves `+0x84` is a character field | **REFUTED** — its base is `[r6]` from a `0x1C`-byte descriptor array; not decisive alone |
| `+0x84` is unique to the character | **REFUTED** — the NoteTrack has one too, read 5× by the dispatcher at `0x02157A44` |
| Any of the three offsets belongs to the entity or the arm9 struct | **REFUTED** — all three resolve to the ov6 character |
| The `0x1C`-byte descriptor array holds character pointers | **not claimed** — consistent, but a NoteTrack fits the encoding equally |
| The character has fields at `+0x07C`, `+0x120`, `+0x130`, `+0x1A0`, `+0x1A4`, `+0x1BC`, `+0x1CC`, `+0xA2` | **CONFIRMED_STATIC** — same anchors |

## Next angles, ranked

1. **Follow `+0x07C`, `+0x120`, `+0x130`** — all address-taken inside the constructor, so
   each is a sub-region or array base. Iteration 79 showed these repay loop-reading.
2. **Name the arm9 `+0x56c` struct** (carried) — candidate `memset(r7+0x8, 0x5e0)` at
   `0x02076C2C`.
3. **Map `BattleCol.cpp`** (carried) — `Battle_ColManCreate` `0x0207AD3C`.
4. **Dead-field sweep of the ColPrm record** (carried) — three fields checked so far have
   no setter.
