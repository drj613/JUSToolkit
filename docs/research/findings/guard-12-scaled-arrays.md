# Findings: guard 12 recovers scaled-register arrays

Loop-Atlas iteration 117. Static.

`struct_fields.py` now resolves `add rD, base, rI, lsl #n` followed by `[rD, #imm]` as
an **array at `+imm`**, element size `1 << n`, extent from the guarding `cmp rI, #N`.

KomaList's six-word array now reports as `+0x014 str/array[6]x0x4` (previously unmapped).

This also caught a **reporting error**: iteration 107's deck-node table omitted a field
because I truncated the tool's output.

---

## 1. The guard

```
0x0214F634  addne r0, r4, r3, lsl #2      ; 0x10840103
0x0214F638  strne r2, [r0, #0x14]
0x0214F648  cmp   r3, #6                  ; the extent
```

Three details:

**Condition is not `AL`.** `addne` for the source-present path, `addeq` for zeroing.
Requiring `cond == 0xE` misses both.

**Extent from `cmp` on the index register**, searched in a window either side of the add
(same approach as guard 11).

**Element size is `1 << shift`** — `lsl #2` reports `x0x4`.

## 2. Effect on the existing maps

| struct | before | after |
|---|---|---|
| KomaList `0x554` | 11 | **12** — `+0x014 array[6]x0x4` |
| ColPrm record `0x188` | 23 | 23 |
| ov6 battle character `0x1F0` | 16 | 16 |
| `0x50` deck node | 20 | 21 — but see below |

The two unchanged structs are a genuine null: neither uses a scaled-register array in its anchors.

## 3. A correction: the deck node's `+0x008`

The 20 → 21 bump is **not** guard 12:

```
0x02076F64  ldrb sb, [r4, #0x40]
0x02076F68  ldr  r3, [r3, sb, lsl #2]
0x02076F6C  str  r3, [r4, #8]        ; node+0x08, a plain field
```

`access` reports `('str', 8)` and `scaled_array` returns `None`. The field was always
found — **iteration 107's table dropped it** because `tail -20` on 24-line output cut the
first row.

The `0x50` node has **21** fields, not 20. `+0x008` receives a word indexed out of a table
by `node+0x40` — the same byte the walkers use as a skip flag.

## 4. Split forms, all four now handled

| form | guard |
|---|---|
| `add rD, base, #N` then `[rD, #M]` | 9 |
| `add rD, base, #N` then a strided walk | 11 |
| 8-bit offsets on `ldrsb`/`ldrsh`/`strh` | 10 (via `effective_offset`) |
| `add rD, base, rI, lsl #n` then `[rD, #imm]` | **12** |

## Predictions status

| Claim | Verdict |
|---|---|
| Guard 12 recovers KomaList's array with extent and element size | **CONFIRMED_STATIC** — `+0x014 str/array[6]x0x4`, selftest-asserted |
| The scaled adds are unconditional | **REFUTED** — `addne`/`addeq` pairs; requiring `AL` finds neither |
| The ColPrm record or battle character gain fields | **REFUTED** — both unchanged; no scaled arrays in their anchors |
| The deck node's new `+0x008` came from guard 12 | **REFUTED** — a plain `str r3,[r4,#8]`; `scaled_array` returns `None` |
| Iteration 107's node table was complete | **REFUTED** *(mine)* — 21 fields, not 20; `tail -20` cut the first row |
| `node+0x008` receives a table lookup indexed by `node+0x40` | **CONFIRMED_STATIC** — `ldrb sb,[r4,#0x40]`; `ldr r3,[r3,sb,lsl#2]`; `str r3,[r4,#8]` |
| All split forms in this ROM are now handled | **not claimed** — four are; a fifth may exist |

## Next angles, ranked

1. **Re-run the field maps that predate guard 12** — the NoteTrack, prmData, the ColPrm
   manager. Any scaled array in those is currently missing.
2. **Read KomaList `+0x04C`** and the `+0x3F0` mode's other values (carried).
3. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
4. **Read `Battle_MoveManCreate` `0x02082A50`** (carried).
