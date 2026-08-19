# Findings: the ColPrm manager's constructor, 43 fields

Loop-Atlas iteration 118. Static.

Guard 8 carried the same `AL`-only assumption guard 12 exposed, so it was relaxed.
No existing maps changed — but `struct_fields.py` on the **ColPrm manager** (size from
iteration 101) had never been run, and it yields **43 offsets** from a single anchor.

Six prior facts confirmed, six offsets new, and the phase table has a **gap at `+0x130`**
matching its documented 19-entry count.

---

## 1. Guard 8's condition

`address_taken` required `cond == 0xE`. Guard 12 showed this ROM writes optional copies as
`addne`/`addeq` arms; the same shape appears for address-taken fields. Relaxed to reject
only `0xF`.

No effect on existing maps: NoteTrack stays at 12 fields, the player slot at 10.

## 2. The manager's constructor map

Anchor `0x0207C4E4:r4`, size `0xFB54`:

| offset | what |
|---|---|
| `+0x000`–`+0x024` | ten words set at construction |
| `+0x008` | **record free pool** (iteration 109) |
| `+0x010` | **record active list** (iteration 109) |
| `+0x018` | **`0x2C`-node free pool** (iteration 69) |
| `+0x020` | **`0x10`-node free pool** (iteration 69) |
| `+0x028`, `+0x02C` | start of the **22 buckets** (iteration 61) |
| `+0x054` | addr — **new** |
| `+0x0D8` | **bucket free list** (iteration 68) |
| `+0x0DC` | **new** |
| `+0x0E0`, `+0x0E4`, `+0x0E8` | the three **owned sub-objects** (iteration 68) |
| `+0x0EC`, `+0x0F0`, `+0x0F4` | **new** |
| `+0x0FC`–`+0x148` | the **phase table** (iteration 62) |
| `+0x14C` | byte (iteration 62) |
| `+0x254` | addr — **new** |
| `+0x354` | addr — **new** |

**Correction (iteration 119):** `+0x054`, `+0x254` and `+0x354` are **not fields**. They are the low halves of split immediates reaching the three node pools at `+0xC854`, `+0xDE54` and `+0xE354`. See `colprm-manager-three-node-pools.md`.

`+0x154` (contact array) is absent — the accumulators write it (iteration 56), not the
constructor.

## 3. The phase table's gap

Nineteen word stores land in `+0xFC`–`+0x148`:

```
+0xFC +0x100 +0x104 +0x108 +0x10C +0x110 +0x114 +0x118 +0x11C
+0x120 +0x124 +0x128 +0x12C        +0x134 +0x138 +0x13C +0x140 +0x144 +0x148
```

`+0x148 - 0xFC = 0x4C`, a **20-slot** span — and **`+0x130` is never written**. No block
write covers it either; the single direct `+0x130` store ROM-wide is in an unrelated
function.

This matches iteration 62's **19 entries**: slot `(0x130 - 0xFC) / 4 = 13` is simply
unused — a deliberate gap, not an uninitialised dispatch target.

Stores are emitted out of order (`+0x138` before `+0x120`, `+0x148` before `+0x140`) —
compiler scheduling, not table structure.

## Predictions status

| Claim | Verdict |
|---|---|
| Guard 8 required `AL` and should not | **CONFIRMED_STATIC** — same shape guard 12 was built for |
| Relaxing it changes existing maps | **REFUTED** — NoteTrack 12 and the player slot 10 are unchanged |
| The manager's constructor sets 43 distinct offsets | **CONFIRMED_STATIC** — one anchor, size `0xFB54` |
| The map confirms the record lists, node pools, buckets, bucket free list and sub-objects | **CONFIRMED_STATIC** — `+0x08`, `+0x10`, `+0x18`, `+0x20`, `+0x28`, `+0xD8`, `+0xE0`/`+0xE4`/`+0xE8` |
| `+0x054`, `+0x0DC`, `+0x0EC`, `+0x0F0`, `+0x0F4`, `+0x254`, `+0x354` are new | **CONFIRMED_STATIC** — not in any prior map |
| The phase table's span is fully initialised | **REFUTED** — 19 stores in a 20-slot span; `+0x130` is skipped |
| `+0x130` is left uninitialised by an oversight | **REFUTED** — it matches iteration 62's independently-derived 19-entry count |
| The contact array is set at construction | **REFUTED** — `+0x154` absent; the accumulators write it |
| The three new `addr` fields are sub-regions | **not claimed** — addresses taken, destinations untraced |

## Next angles, ranked

1. **Follow `+0x254` and `+0x354`.** Both address-taken, both past the phase table,
   neither seen in nine wakes of ColPrm work.
2. **Read `+0x0EC`, `+0x0F0`, `+0x0F4`** — three consecutive new words between the
   sub-objects and the phase table.
3. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
4. **Read `Battle_MoveManCreate` `0x02082A50`** (carried).
