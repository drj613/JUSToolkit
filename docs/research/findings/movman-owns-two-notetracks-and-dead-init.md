# Findings: the move manager owns two NoteTracks, and half its constructor is dead code

Loop-Atlas iteration 136. Static.

**Course correction first.** Iterations 127–135 were productive but walked steadily away from Mission 2
(the combat engine) into middleware: a boolean getter, a facing flag, a class hierarchy, the allocator, the
census. Useful infrastructure, but `Battle_MoveManCreate` — `0x2648` bytes, tagged `BattleMove.cpp`, one of
the largest battle allocations in the ROM — had sat in the queue unread the whole time. This wake reads it.

Results:

1. The manager **owns two NoteTracks**, built exactly the way ColPrm builds its two — which independently
   reproduces iteration 54's pattern in an unrelated manager.
2. **Half the constructor is dead.** Eight field clears and a 128-element loop are both followed by
   `memset(obj, 0, 0x2648)`.
3. On allocation failure it calls **`memset(NULL, 0, 0x2648)`**.

---

## 1. The function, and a correction to its address

`Battle_MoveManCreate` is at **`0x02082A38`**, 408 bytes, one caller (`0x02083204`, `bl` site
`0x020833D0`). `0x02082A50` — the address in the queue and in a dozen earlier docs — is the *allocation
site* inside it, not the function start. Line 50 of `BattleMove.cpp` (`mov r3, #0x32`).

## 2. Two NoteTracks, built identically

The body contains the same six-step block twice:

```
                          block A (+0x20)          block B (+0x24)
create the track          0x02082AB0               0x02082B0C     bl #0x2026f94
store the handle          0x02082AB4 -> +0x20      0x02082B10 -> +0x24
an id on the stack        0x02082AB8  #0xa1000     0x02082B14  #0xa6000
configure it              0x02082AC8               0x02082B24     bl #0x2012940(track, &id)
register a callback       0x02082AD8  0x02082E10   0x02082B34  0x0208317C   bl #0x2028384
self-register             0x02082AF0               0x02082B4C     vtable[+0x24](track, manager)
set a flag                0x02082B08  #0x2000000   0x02082B64  #0x2000000   vtable[+0x94](track, ...)
```

Both blocks reach the track through `[[obj+0x20]+4]` / `[[obj+0x24]+4]` — the same indirection each time.

**This is iteration 54's ColPrm pattern, reproduced.** That wake found ColPrm owning two of these at `+0xE4`
and `+0xE8` with ids `0xA5000` and `0xA0000`, via the same factory `0x02026F94` (`Battle_NoteTrackCreate`),
with the same "vtable-`0x24` self-registration". Finding the identical six-step shape in a manager reached
from a completely different direction is strong corroboration for both.

The id set grows to **`0xA0000`, `0xA1000`, `0xA5000`, `0xA6000`** — all `0x1000`-aligned, consistent with
the 12 distinct ids iteration 54 counted across arm9 and left open.

## 3. Half the constructor is dead

```
0x02082A5C  mov r0, #0
0x02082A60  str r0, [r4]            ; +0x00
   ... seven more, +0x04 through +0x1C

0x02082A80  add r0, r4, #0x248
0x02082A84  add r2, r4, #0x48
0x02082A88  add r0, r0, #0x400      ; end = obj + 0x648
0x02082A8C  mov r1, #0
0x02082A90  str r1, [r2, #8]        ; zero +0x8 of each element
0x02082A94  add r2, r2, #0xc        ; stride 0xC
0x02082A98  cmp r2, r0
0x02082A9C  blo #0x2082a90

0x02082AA0  ldr r2, [pc, #0x12c]    ; = 0x2648
0x02082AA4  mov r0, r4
0x02082AA8  mov r1, #0
0x02082AAC  bl  #0x20517fc          ; memset(obj, 0, 0x2648)  <-- wipes all of the above
```

I checked this rather than assuming, because the reading is surprising:

- The literal at `0x02082BD4` is **`0x00002648`** — the whole object, not a prefix. It is the *same word*
  the allocator's size argument loads at `0x02082A44`.
- No branch skips the `memset`. The loop's `blo` goes backward to `0x02082A90`; execution falls straight
  into `0x02082AA0`.
- `r2` is not rewritten between the `ldr` and the `bl`.

So the eight stores and all 128 loop iterations are **overwritten immediately**. A sixth vestigial finding
for this project, and the first that is redundant work rather than an unused feature.

**The dead loop is still evidence.** It documents the intended layout: an array of **128 records of `0xC`
bytes** at `+0x48`, spanning `+0x48`–`+0x647`, each with a field at `+0x8` worth clearing. 128 is the same
record count as the ColPrm manager's embedded array.

## 4. `memset(NULL, 0, 0x2648)` on allocation failure

```
0x02082A54  movs r4, r0
0x02082A58  beq #0x2082aa0     ; allocation failed -> jump to the memset setup
```

The `beq` target is `0x02082AA0`, which is the `memset` setup itself — with `r4 = 0`. On out-of-memory this
writes 9,800 zero bytes to address `0`.

This is the **second** instance of this exact shape; iteration 128 found `0x0206CEAC` producing a `NULL` and
calling a getter with it anyway. Two independent occurrences make it a codebase habit: the null check jumps
into shared cleanup rather than returning.

## 5. Layout so far

| offset | what |
|---|---|
| `+0x00`–`+0x1C` | eight words cleared individually — **dead**, wiped by the `memset` |
| `+0x20` | NoteTrack handle A, id `0xA1000`, callback `0x02082E10` |
| `+0x24` | NoteTrack handle B, id `0xA6000`, callback `0x0208317C` |
| `+0x2C` | halfword `= 0x29` (`strh` at `0x02082B6C`) |
| `+0x48`–`+0x647` | 128 × `0xC` records, `+0x8` of each cleared — **dead**, wiped |
| `+0x648`–`+0x2647` | `0x2000` bytes, unexplored |

## Predictions status

| Claim | Verdict |
|---|---|
| `Battle_MoveManCreate` starts at `0x02082A50` | **REFUTED** — that is the allocation site; the function is `0x02082A38` |
| The manager owns two NoteTracks | **CONFIRMED_STATIC** — `0x02026F94` twice, handles at `+0x20`/`+0x24` |
| The two are built by the same six-step block | **CONFIRMED_STATIC** — `0x02082AB0`–`0x02082B08` and `0x02082B0C`–`0x02082B64` |
| This is iteration 54's ColPrm `+0xE4`/`+0xE8` pattern | **CONFIRMED_STATIC** — same factory, same `0x02012940` id call, same vtable-`0x24` self-registration |
| The eight field clears and the 128-element loop are dead | **CONFIRMED_STATIC** — literal `0x02082BD4` = `0x2648`, no branch skips the `memset`, `r2` unmodified |
| A whole-object `memset` runs on the allocation-failure path with `r4 = 0` | **CONFIRMED_STATIC** — `beq #0x2082aa0` targets the `memset` setup |
| The intended array is 128 × `0xC` at `+0x48` | **CONFIRMED_STATIC** — `+0x48` to `+0x648`, stride `0xC`, from the (dead) loop |
| `+0x2C` holds `0x29` | **CONFIRMED_STATIC** — `mov r0,#0x29; strh r0,[r4,#0x2c]` |
| The `0xA_000` values are asset or file ids | **PLAUSIBLE** — four now known, all `0x1000`-aligned; iteration 54 left this open |
| The vtable `+0x24`/`+0x94` slots match iteration 132's dumped table | **not claimed** — same offsets, but a different object; conflating vtables is how iteration 129's label went wrong |

## Next angles, ranked

1. **Map `+0x648`–`+0x2647`** — `0x2000` bytes, the bulk of the manager, untouched by the constructor's
   surviving code. The consumers will have to name it.
2. **Read the two callbacks** `0x02082E10` and `0x0208317C`. They are the manager's per-track entry points
   and sit in `BattleMove.cpp`, so the census can name them.
3. **Read `0x02083204`**, the sole caller — it will say who owns the move manager.
4. **Resolve the `0xA_000` id space** (carried from iteration 54) — now with four of the twelve known.
