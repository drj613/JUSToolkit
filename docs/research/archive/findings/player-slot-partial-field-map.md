# Findings: the `0x61C` player slot — 12 fields, and where the bulk is

Loop-Atlas iteration 104. Static.

Twelve anchors across arm9 and ov6 yield **12 offsets**, clustered in two bands: `+0x058`–`+0x060` and `+0x558`–`+0x5F6`.

The middle `0x558` bytes (`+0x000`–`+0x557`) are untouched by every anchor. The deck payload lives there, and no construction or gauge code touches it.

---

## 1. The map

| offset | kind | what |
|---|---|---|
| `+0x058` | addr | address taken in the slot allocator |
| `+0x558` | ldr, str | **list head** — walked by `0x0207871C` |
| `+0x55C` | str | zeroed per slot |
| `+0x560` | str, addr | zeroed per slot; address also taken |
| `+0x564` | str | zeroed per slot |
| `+0x56C` | ldr, str ×7 | **the gauge pointer** |
| `+0x5E8` | ldr, str ×3 | written by ov6, read in arm9 |
| `+0x5EC` | ldr ×3 | written by ov6, read in arm9 |
| `+0x5F0` | strb | iteration 95 |
| `+0x5F3` | strb | |
| `+0x5F5` | strb | |
| `+0x5F6` | strb | |

`+0x5F0`, `+0x5F3`, `+0x5F5`, `+0x5F6` — byte cluster written near `Battle_CharaCreate` in ov6.

## 2. `+0x558` heads a node list

```
0x0207871C  ldr  ip, [r0, #0x558]     ; the head
0x02078720  cmp  ip, #0
0x02078724  bxeq lr                   ; empty -> nothing to do
0x02078730  ldrb r2, [ip, #0x40]      ; a byte on each node
0x02078734  cmp  r2, #0
0x02078738  bne  #0x207877c
```

`Battle_Add` calls this twice per slot — `r1 = 0` (`0x0214D89A`) then `r1 = 1` (`0x0214D8B4`). The list is walked with a mode flag; nodes carry a byte at `+0x40`.

## 3. `+0x21C` is not a field

An earlier run reported `+0x21C` as address-taken. It is the first half of the stride computation — `add r1,r4,#0x21c` then `add r4,r1,#0x400` — from iteration 103. Guard 8 sees the `add` but can't distinguish a loop induction variable from a field address.

Excluded from the table. Lesson: an address-taken hit inside a clearing loop may be arithmetic, not structure.

## 4. Coverage

12 fields from anchors in the slot allocator `0x02076908`, the initialiser at `0x02075FF8`, both `+0x56c` writers, `0x0207871C`, and nine ov6 sites loading `[char+0x1b4]`.

All 12 sit in the last `0xC4` bytes plus `+0x058`. **`+0x000`–`+0x557` is unmapped** — 87% of the struct. Every available anchor is construction or gauge code; none touches the payload.

## Predictions status

| Claim | Verdict |
|---|---|
| `+0x558` is a list head with a mode-flagged walker | **CONFIRMED_STATIC** — `ldr ip,[r0,#0x558]`; null check; `0x0207871C` called with `r1 = 0` and `r1 = 1` |
| Nodes on that list carry a byte at `+0x40` | **CONFIRMED_STATIC** — `ldrb r2,[ip,#0x40]` at `0x02078730` |
| `+0x5E8` and `+0x5EC` cross the ov6/arm9 boundary | **CONFIRMED_STATIC** — written in ov6 at `0x02156B14`/`0x02156B18`, read in arm9 at `0x02077F74`/`0x02077F78` |
| A byte cluster exists at `+0x5F0`–`+0x5F6` | **CONFIRMED_STATIC** — `strb` at `+0x5F0`, `+0x5F3`, `+0x5F5`, `+0x5F6` |
| `+0x21C` is a slot field | **REFUTED** — it is the stride's first half, `add r1,r4,#0x21c` |
| The construction and gauge code touches the slot's payload | **REFUTED** — 12 anchors, nothing between `+0x059` and `+0x557` |
| This is a complete field map | **REFUTED** — 12 fields; `0x558` of `0x61C` bytes unmapped |
| `+0x058` and `+0x560` are list heads | **not claimed** — addresses taken, destinations not traced |

## Next angles, ranked

1. **Find code that touches `+0x000`–`+0x557`.** The payload must have its own accessors — likely in `ComicDeck.cpp` between the two `+0x56c` writers, or in koma/deck UI code.
2. **Follow `+0x558`'s node list.** Sizing a node would reveal what the deck holds.
3. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
4. **Re-audit map claims on `char+0xNNN` above `0x200`** (carried).
