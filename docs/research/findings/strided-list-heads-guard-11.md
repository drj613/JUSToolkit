# Findings: a strided pointer walk hides a whole field group — guard 11

Loop-Atlas iteration 85. Static.

Adding the detach routine as a fifth anchor should have picked up all three list heads
from iteration 83. It picked up **one**.

`+0x18` and `+0x20` are never accessed relative to the anchor register. The code loads a
pointer to the first head and advances it by 8 each pass, so anchor-register walking
sees only `+0x10`. Guard 11 recovers the group — the map goes from 20 offsets to **23**,
matching the hand reading.

---

## 1. The shape

```
0x0207CB70  add r6, sl, #0x10      ; first head -- the only one the walk sees
...
0x0207CBE8  add r8, r8, #1
0x0207CBEC  cmp r8, #3             ; trip count
0x0207CBF0  add r6, r6, #8         ; stride
0x0207CBF4  blt #0x207cb80         ; back-edge
```

Guard 11 fires on an address-taken field, scans forward for a self-increment
`add rD, rD, #K` of the same pointer plus a `cmp rC, #M`, and on a **backward** branch
reports `N + K`, `N + 2K`, … `N + (M-1)K` as kind `addr/strided`. It needs both a stride
and a trip count — no guessing at unbounded strides. The bound is capped at 64 to
prevent a misparse from flooding the map.

## 2. Two traps in the implementation

Both produced a clean empty result instead of an error.

**A forward branch is not the loop close.** The first version returned at any `B`. This
loop opens with `b #0x207cbe0` — a jump to its own condition test (standard
bottom-tested layout) — so the scan quit four instructions in. Only backward branches
close a loop.

**An inner loop's back-edge closes first.** The second version returned at the first
backward branch: `bne #0x207cb88`, the *inner* loop draining one list before the outer
loop advances. Fix: only return at a back-edge where both stride and trip count are
already known.

Both bugs returned `[]`, indistinguishable from "no strided group here." The selftest
asserts the three specific offsets, not just that something was found.

## 3. The map, 23 offsets

| offset | kind | note |
|---|---|---|
| `+0x008` | addr | `0x2C`-byte pool nodes |
| `+0x010` | ldr/split | `0x10`-byte nodes → `mgr+0x20` |
| `+0x018` | **addr/strided** | bucket nodes → `mgr+0xD8` |
| `+0x020` | **addr/strided** | bucket nodes → `mgr+0xD8` |
| `+0x030` | str | |
| `+0x034` | ldr,str | seeds node `+0x14` |
| `+0x038` | ldr,str | seeds node `+0x18` |
| `+0x03C` | ldr,str | |
| `+0x040` | ldr,str ×4 | flags: `0x100` set on detach, `0x200` cleared on install, `0x800` gates delta application |
| `+0x050` | str | |
| `+0x05C` | str | |
| `+0x060` | ldr,str ×4 | the ColObj |
| `+0x068` | ldr | partner link — never set (iteration 84) |
| `+0x06C` | ldr | |
| `+0x090` | addr | `int16[2]`, init `-1` |
| `+0x094` | addr | `int16[2]`, init `-1` |
| `+0x098` | ldrsh/strh split | `int16[2]`, init `-1` |
| `+0x0A4` | addr | start of the `0xD0` scratch region |
| `+0x174` | strb | |
| `+0x175` | ldrb,strb ×3 | bitfield |
| `+0x182` | strb | |
| `+0x184` | strh/split | |
| `+0x186` | strh/split | |

Plus `+0x0E8`, `+0x130`, `+0x140`, `+0x144` from the ov6 anchors — inside the `+0xA4`
scratch region.

The two `addr/strided` entries are the point: the tool now derives what iteration 83
found by hand.

## 4. Coverage

23 offsets from five anchors on a `0x188` struct. Unmapped: `+0x00`–`+0x2C`,
`+0x44`–`+0x4C`, `+0x54`–`+0x58`, `+0x64`, `+0x70`–`+0x8C`, `+0x9C`–`+0xA0`, and most of
`+0xA4`–`+0x173`. **Partial map, not the struct.**

## Predictions status

| Claim | Verdict |
|---|---|
| An anchor-register walk cannot see strided list heads | **CONFIRMED_STATIC** — the fifth anchor found `+0x10` only |
| Guard 11 recovers `+0x18` and `+0x20` | **CONFIRMED_STATIC** — both reported `addr/strided`, matching iteration 83's hand reading |
| The record map now has 23 offsets | **CONFIRMED_STATIC** — up from 20 |
| A forward branch closes the walk's loop | **REFUTED** — this loop opens with a forward `b` to its condition test |
| The first backward branch is the walk's back-edge | **REFUTED** — an inner loop closes first |
| The map is complete | **REFUTED** — large spans unmapped, five anchors only |

## Next angles, ranked

1. **Re-audit the map's `char+0xNN` offsets** across the three objects (carried) —
   oldest correctness debt.
2. **Name the arm9 `+0x56c` struct** (carried) — candidate `memset(r7+0x8, 0x5e0)` at
   `0x02076C2C`.
3. **Map `BattleCol.cpp`** (carried) — `Battle_ColManCreate` `0x0207AD3C`, and
   `0x0207B414`'s `+0x90` use.
4. **Dead-field sweep of the record** — three fields so far have no setter; the ColPrm
   band is only 10240 words, so the check is cheap per field.
