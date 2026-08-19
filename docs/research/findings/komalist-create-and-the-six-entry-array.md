# Findings: `KomaList_Create` holds a six-entry array

Loop-Atlas iteration 116. Static.

The editor's container is `0x554` bytes with a **six-entry word array at `+0x14`**,
copied from a caller-supplied array or zeroed when null.

Eleven other fields mapped. The array itself is absent from the field map because
`add r0, r4, r3, lsl #2` then `[r0, #0x14]` is a **scaled-register** base — no
scanner in this campaign resolves it.

---

## 1. Construction

```
0x0214F5C4  bl  #0x201a21c            ; 0x554, tag KomaList_Create / KomaList.cpp
0x0214F5D0  ldr r2, [pc, #0x430]      ; -> [0x0214FA08] = 0x554
0x0214F5DC  bl  #0x20517fc            ; memset(obj, 0, 0x554)
0x0214F5E0  str r7, [r4, #0x3f0]
0x0214F5E4  str r6, [r4]
0x0214F5E8  bl  #0x2026f94
0x0214F5EC  str r0, [r4, #0x38]
```

`0x02026F94` is the same factory the NoteTrack used for `+0x8C` (iteration 49) —
shared infrastructure, not deck-specific.

## 2. The six-entry array

```
0x0214F624  mov r3, #0
0x0214F62C  cmp r5, #0                ; r5 = [sp+0x48], a stack argument
0x0214F630  ldrne r2, [r5, r3, lsl #2]
0x0214F634  addne r0, r4, r3, lsl #2
0x0214F638  strne r2, [r0, #0x14]     ; obj+0x14 + i*4 = source[i]
0x0214F63C  addeq r0, r4, r3, lsl #2
0x0214F644  streq r1, [r0, #0x14]     ; ...or 0
0x0214F640  add r3, r3, #1
0x0214F648  cmp r3, #6
0x0214F64C  blt #0x214f62c
```

Six words at `+0x14`–`+0x2B`, filled from the argument when present; null zeroes the
array instead.

## 3. A mode field at `+0x3F0`

```
0x0214F650  ldr r0, [r4, #0x3f0]
0x0214F654  cmp r0, #1
0x0214F658  bne #0x214f66c
0x0214F65C  bl  #0x21652e8
0x0214F660  str r0, [r4, #0xc]
0x0214F664  bl  #0x216d3c8
0x0214F668  str r0, [r4, #0x10]
```

`+0x3F0` is set from an argument at construction and gates two sub-objects. Nine
accesses — joint busiest field.

## 4. The map

| offset | accesses | notes |
|---|---|---|
| `+0x000` | 3 | set from an argument |
| `+0x004` | 3 | |
| `+0x00C` | 3 | sub-object, only when `+0x3F0 == 1` |
| `+0x010` | 3 | sub-object, same gate |
| `+0x014`–`+0x02B` | — | **six-word array**, scaled-register access |
| `+0x038` | 6 | the `0x02026F94` object |
| `+0x04C` | 9 | joint busiest |
| `+0x050` | 3 | |
| `+0x054` | 3 | addr |
| `+0x058` | 3 | |
| `+0x05C` | 6 | addr, ldr |
| `+0x3F0` | 9 | mode |

Most of `0x554` is unmapped from three anchors — same anchor-diversity limit as
iteration 104.

## 5. The scaled-register split

`add r0, r4, r3, lsl #2` then `[r0, #0x14]` is a **third** split form, after add-then-
immediate and the 8-bit `ldrsb` offsets. `struct_fields.py`'s guard 9 handles a constant
`add`; a register-scaled one needs the index's range for the field's extent — exactly
what `cmp r3,#6` supplies here.

## Predictions status

| Claim | Verdict |
|---|---|
| `KomaList_Create` allocates `0x554` and memsets it | **CONFIRMED_STATIC** — tag at `0x0214F5C4`, size literal `[0x0214FA08]` |
| `+0x14` holds six words | **CONFIRMED_STATIC** — `cmp r3,#6`; `blt`; stride `lsl #2` |
| The source array is an optional argument | **CONFIRMED_STATIC** — `cmp r5,#0` with `ldrne`/`streq` arms |
| `+0x3F0` is set at construction and gates `+0x0C`/`+0x10` | **CONFIRMED_STATIC** — `str r7,[r4,#0x3f0]`, then `cmp r0,#1`; `bne` |
| `0x02026F94` is deck-specific | **REFUTED** — the NoteTrack uses the same factory (iteration 49) |
| Guard 9 resolves a scaled-register split base | **REFUTED** — `+0x14` is absent from the field map for that reason |
| The field map is complete | **REFUTED** — 11 fields of `0x554`, three anchors |
| Six entries corresponds to a deck roster size | **not claimed** — the count is exact; its meaning is not established |

## Next angles, ranked

1. **Teach `struct_fields.py` the scaled-register split.** `add rD, base, rI, lsl #n`
   then `[rD, #imm]` — array at `imm`, extent from the guarding `cmp`. Same trick
   guard 11 already uses for strides.
2. **Read `+0x04C`** (joint busiest) and `+0x3F0` mode's other values.
3. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
4. **Read `Battle_MoveManCreate` `0x02082A50`** (carried).
