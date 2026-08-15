# Findings: the NoteTrack struct mapped — 7 note slots, then the callback

Loop-Atlas iteration 49. Static.

Field map of the `0xA8`-byte NoteTrack object (the move-script engine from iteration 47).

**Key fact: `NoteTrack+0x00` is an array of 7 slots × 16 bytes = 112 = `0x70` bytes, and the command
callback sits right after it at `+0x70`.** A reset loop iterates exactly 7 times with
`add r4,r4,#0x10`, and iteration 40's kind→slot table independently mapped 17 note kinds onto exactly
7 slots. Two independent derivations, same number.

This closes iteration 40, which inferred "at least 112 bytes (7 × 16)" from the slot table alone.

---

## 1. Method: type-verified base registers

Per iteration 45: an offset means nothing without the base register's type. The type comes free here —
12 known callback sites do `ldr ip,[rN,#0x70]`, so `rN` holds a NoteTrack at that instruction.

From each site I walked both directions, collecting `[rN,#imm]` accesses, **stopping when anything writes
`rN`**, and skipping any access whose base was loaded from `[Rm,#0]` (iteration 48's vtable rule). The
constructor's stores off `r4` are included since `r4` is the allocator's return value.

A first pass without the reassignment check reported `+0x10`, `+0x28`, `+0x40` and `+0x5C` — all false,
from register reuse. It also **missed** `+0x94` and `+0xa3`, which the constructor writes. Both problems
vanished once reassignment was tracked, and every constructor store is now accounted for.

## 2. The layout

```
+0x00 .. +0x6F   note slot array: 7 slots x 16 bytes
                   slot +0x00  kind (0..16)
                   slot +0x01  ExtFlags        (reset to -1)
                   slot +0x02  ProjectileId
                   slot +0x04  u16 counter     (ticked down by the forwarder)
+0x70   command callback  = 0x02157A44, the 73-case dispatcher   (16 reads)
+0x74   the character     — passed as r1 to the callback          (15 reads)
+0x7C   constructor arg 2                                         (4 reads)
+0x88   constructor arg 1
+0x8C   object returned by 0x02026F94 — vtable calls at slots 0xA0 and 0x24
+0x90   word,     reset to 0
+0x94   word,     init -1
+0x98   word,     init -1, reset to -1
+0x9C   halfword, reset to 0
+0x9E   halfword, reset to 0
+0xA0   byte,     reset to 0
+0xA1   byte,     reset to 0
+0xA2   byte,     reset to 0
+0xA3   byte,     init -1
```

15 distinct offsets. Nothing is touched at or beyond `0xA8`, matching the `mov r0,#0xa8` allocation.

### The 7-slot array

```
0x021555E4  mov  r1, #7
0x021555E8  sub  r1, r1, #1
0x021555EC  strb r0, [r4, #1]     ; r0 = -1  -> slot ExtFlags
0x021555F0  cmp  r1, #0
0x021555F4  add  r4, r4, #0x10    ; next slot
0x021555F8  bgt  #0x21555e8
```

Seven iterations at stride `0x10` from the NoteTrack base — slots span `+0x00`–`+0x6F`.
`7 × 0x10 = 0x70`, exactly where the callback lives.

Iteration 40 decoded the kind→slot table at `0x021710A8`: 17 kinds map onto **7 distinct slots (0..6)**,
with slot 2 collecting kinds 6, 7, 8, 9, 10, 14 and 15. Data table and reset loop agree on 7.

A NoteTrack holds **at most 7 active notes**, bucketed by category, not queued: issuing kind 8 writes
slot 2, overwriting whatever kind-6/7/9/10/14/15 note was there.

### `+0x74` is the character

```
0x02155434  ldr r0, [sp, #0x20]   ; the 5th argument
0x02155438  str r6, [r4, #0x70]   ; the callback
0x0215543C  str r0, [r4, #0x74]   ; <- the character
```

`Battle_CharaCreate` passes the character as the 5th argument (`str r4,[sp]` at `0x02156CD4`), and call
sites load `r1` from `+0x74` before invoking the callback (`ldr r1,[r0,#0x74]` at `0x02156560`). Callback
signature: **`dispatcher(r0, r1 = character, r2 = command, ...)`** — a stored (function, self) pair.

### The reset routine

`0x021555C0`–`0x021555F8` clears `+0x90`, `+0x9C`, `+0x9E`, `+0xA0`, `+0xA1`, `+0xA2` to 0, sets `+0x98`
to -1, then runs the 7-slot loop setting every slot's `ExtFlags` to -1. `-1` is the "empty slot" sentinel,
matching the constructor's `-1` init of `+0x94`, `+0x98` and `+0xA3`.

### Constructor tail

`0x02155444` stores the result of `bl 0x02026F94` at `+0x8C`, makes vtable calls on it at slots `0xA0`
and `0x24`, and passes `r1 = r4` (the NoteTrack) into the `0x24` call — registering itself with that
object. `0x0215548C str r4,[r5]` writes the NoteTrack into the caller's output slot, which
`Battle_CharaCreate` set to `[char+0x1a8]+0x18`.

## Predictions status

| Claim | Verdict |
|---|---|
| `NoteTrack+0x00` is 7 slots × 16 bytes, ending exactly at `+0x70` | **CONFIRMED_STATIC** — 7-iteration loop, `add r4,r4,#0x10`; `7 × 0x10 = 0x70` |
| Iteration 40's 16-byte slot records live in the NoteTrack | **CONFIRMED_STATIC** *(was PLAUSIBLE)* — the reset loop writes slot `+0x01` |
| The 7 slots match the kind→slot table's 7 distinct slots | **CONFIRMED_STATIC** — `0x021710A8` maps 17 kinds onto slots 0–6 |
| `+0x74` holds the character, passed as the callback's `r1` | **CONFIRMED_STATIC** — `0x0215543C` stores it; `0x02156560` loads it |
| `-1` is the empty-slot sentinel | **CONFIRMED_STATIC** — reset loop and ctor both use it |
| `+0x8C` holds an object the NoteTrack registers itself with | **PLAUSIBLE** — `r1 = r4` into a vtable-`0x24` call |
| A NoteTrack can hold more than 7 active notes | **REFUTED** — fixed 7-slot array, bucketed by kind |
| My first field scan (`+0x10`, `+0x28`, `+0x40`, `+0x5C`) | **REFUTED** — register reuse; no reassignment check |

## Next angles, ranked

1. **Name commands 64–73** by reading the seven live dispatcher cases. These define what a move script
   can do to a character. Each case is a short block with a known target address.
2. **Identify `0x02026F94`'s return type** — the object at `+0x8C` with vtable slots `0xA0` and `0x24`.
   Likely the animation or timing manager driving note advancement.
3. **Explain the bucketing.** Slot 2 absorbs 7 of the 17 kinds, so those kinds are mutually exclusive.
   Worth confirming against observed play — good question for the owner.
4. Still open: `prmData+0x0C/+0x10/+0x14`, the 68-entry table at `0x02171FEC`, the 24 positive
   `ProjectileId` values, the `34-63` no-op band, and the harness watchpoint recipe for the collision walker.
