# Findings: the move manager is two parallel 128-element arrays, and its callback is a frame snapshot

Loop-Atlas iteration 137. Static.

Set out to map `MoveMan +0x648`–`+0x2647` — `0x2000` bytes the constructor never touches. Offset scanning
found **nothing**, for a reason worth recording. Reading the consumer instead produced the layout and a
clear read of what the manager *does* per frame.

1. **`+0x648` is never formed as an address.** Zero direct writers, zero split writers. The constructor
   built it only as a **loop bound**.
2. The region is reached **by pointer**, through the list-node payload at `node+0x8` — precisely the blind
   spot `find_field_writers.py` prints.
3. The consumer is a **frame snapshot pass**: it copies current values into previous ones and derives status
   bits.

---

## 1. The tempting arithmetic, and why it is not enough on its own

```
0x648 + 128 * 0x40 = 0x2648   <- exactly the object size, zero slack
```

`0x40` is also the only stride that tiles the region into the **128** elements the constructor's dead loop
counted (iteration 136). It is very tempting.

But this project already has a false lead of exactly this shape — the `0x645` division at an earlier wake —
and the standing rule is that **perfect tiling counts only alongside code that uses the stride**. So I went
looking for that code:

| probe | result |
|---|---|
| `search-op-imm 0x648` | **0 hits** |
| `search-imm 0x648` | **0 hits** |
| `find_field_writers.py 0x648` direct | **0 sites** |
| `find_field_writers.py 0x648` split (`add`+`str`) | **0 sites** |

`0x648` is not an encodable ARM immediate (it needs an 11-bit span), which is why the constructor built it
as `add r0, r4, #0x248` then `add r0, r0, #0x400` — and it built it as the **end address for a comparison**,
never dereferencing it. So there is no `+0x648` field, and offset scanning was never going to find this
region.

## 2. How the region is actually reached

`0x02082E10` (868 bytes, `callers=0` — installed as a callback via `0x02028384`, iteration 136) walks a
**linked list**, not an array:

```
0x02082E1C  ldr r3, [r0, #0x10]      ; r0 = [arg0+4]
0x02082E24  ldr ip, [r3, #0x10]      ; ip = the first link
0x02082E3C  b   #0x2083168           ; bottom-tested loop
   ...
0x02082E40  ldr lr, [ip, #8]         ; lr = the ELEMENT, via the link's payload
   ...
0x02083164  ldr ip, [ip]             ; next
0x02083168  cmp ip, #0
0x0208316C  bne #0x2082e40
```

`next` at `+0x00` and a payload pointer at `+0x08` — the shape of this codebase's list library
(`0x02037B98` / `0x02037C24`). Elements are handed out as **pointers**, so their offsets never appear
relative to the manager. That is the fourth blind spot the tool lists, and it is the whole answer to why
pass 1 and pass 2 came back empty.

## 3. Which makes the two-array model well-supported

Putting iteration 136's constructor together with this consumer:

| region | size | evidence |
|---|---|---|
| `+0x48`–`+0x647` | **128 × `0xC`** | the constructor's strided loop: base `+0x48`, stride `0xC`, bound `+0x648` |
| `+0x648`–`+0x2647` | **128 × `0x40`** | tiles exactly; elements reached via `node+0x8` |

`0xC` is three words, and a list link needs exactly three: `next` at `+0x00`, `prev` at `+0x04`, payload at
`+0x08`. The constructor's dead loop zeroed **`+0x8` of all 128** — the payload pointer. The consumer reads
**`[ip+8]`** to get the element. Two independent sightings of the same field, doing the same job.

And the element cannot be `0xC` bytes: the consumer touches `+0x34`, so an element needs at least `0x38`.
`0x40` is the smallest aligned size that fits and the only one that tiles.

**Still PLAUSIBLE, not CONFIRMED.** What is missing is explicit: no instruction anywhere computes
`element = base + i * 0x40`. The elements are only ever reached through the payload pointer, so the stride is
inferred from the tiling plus the minimum element size — never observed.

`prev` at `+0x04` is likewise inferred from the library's shape, not read here.

## 4. The callback is a frame snapshot

The loop body is the useful part regardless of the array question:

```
0x02082E44  ldr r0, [pc, #0x32c]     ; = 0x0003FFFF
0x02082E48  ldr r1, [lr, #0x34]
0x02082E4C  and r0, r1, r0
0x02082E50  str r0, [lr, #0x34]      ; clear the top 14 bits every pass
0x02082E54  tst r0, #0x100
0x02082E5C  bicne r0, r0, #0x100     ; set -> just clear it
0x02082E64  ldreq r0, [lr, #0xc]     ; clear -> snapshot
0x02082E68  streq r0, [lr, #0x14]    ;   +0x14 = +0x0C
0x02082E6C  ldreq r0, [lr, #0x10]
0x02082E70  streq r0, [lr, #0x18]    ;   +0x18 = +0x10
0x02082E74  ldr r0, [lr, #0x34]
0x02082E78  tst r0, #0x600
0x02082E7C  orrne r0, r0, #0x20      ; 0x600 set -> flag 0x20 and skip the rest
0x02082E84  bne #0x2083164
   ...
0x02083150  ldrsh r0, [lr, #0x26]
0x02083158  ldrgt r0, [lr, #0x34]
0x0208315C  orrgt r0, r0, #4         ; +0x26 > 0 -> flag 0x4
```

`+0x14`/`+0x18` receive `+0x0C`/`+0x10` — a **previous-value pair**, which is how you get per-frame deltas.
Bit `0x100` suppresses the snapshot for one pass, exactly what a freshly-created or repositioned element
needs so its first delta is not garbage.

Element layout so far:

| offset | what |
|---|---|
| `+0x0C`, `+0x10` | current values |
| `+0x14`, `+0x18` | previous values, copied from `+0x0C`/`+0x10` |
| `+0x26` | signed halfword; `> 0` sets flag `0x4` |
| `+0x34` | flags word |

Flag bits seen at `+0x34`: `0x4`, `0x10`, `0x20`, `0x100` (suppress snapshot), `0x600` (tested as a pair),
`0x1000`. Masks: `0x0003FFFF` applied every pass, and `0xFFFFEFCB` = `~0x1034` in the pool.

## Predictions status

| Claim | Verdict |
|---|---|
| `+0x648` is a field with writers | **REFUTED** — 0 direct, 0 split; it is a loop bound, and not an encodable ARM immediate |
| Offset scanning can find this region | **REFUTED** — elements are reached by pointer, the tool's fourth blind spot |
| `0x02082E10` walks an array | **REFUTED** — it walks a linked list, `ldr ip,[ip]` at `0x02083164` |
| Elements are reached via a payload pointer at `node+0x8` | **CONFIRMED_STATIC** — `ldr lr,[ip,#8]` at `0x02082E40`, and the constructor zeroes `+0x8` of all 128 |
| `+0x48`–`+0x647` is 128 × `0xC` | **CONFIRMED_STATIC** — iteration 136's loop: base, stride and bound all read |
| `+0x648`–`+0x2647` is 128 × `0x40` | **PLAUSIBLE** — tiles exactly, and elements need ≥ `0x38`; but **no code computes `base + i*0x40`** |
| `prev` sits at `node+0x04` | **PLAUSIBLE** — the list library's shape; not read here |
| `+0x14`/`+0x18` are previous values of `+0x0C`/`+0x10` | **CONFIRMED_STATIC** — `0x02082E64`–`0x02082E70` |
| Bit `0x100` suppresses the snapshot for one pass | **CONFIRMED_STATIC** — `bicne` clears it and the `eq` arm does the copy |
| Bit `0x100` marks a freshly-created element | **SPECULATIVE** — fits, but nothing here sets it |
| The callback is a per-frame update pass | **PLAUSIBLE** — clears transient bits, snapshots, derives status; no frame driver read yet |

## Next angles, ranked

1. **Find who sets `+0x34` bit `0x100`.** It is the snapshot suppressor, so its writer is whatever creates or
   repositions an element — the fastest route to naming the element type.
2. **Read the middle of `0x02082E10`** (`0x02082E88`–`0x02083148`, ~180 instructions). It is the bulk of the
   per-frame logic and will name more element fields.
3. **Read `0x0208317C`** (136 bytes), the second track's callback — smaller, and a diff against this one
   would separate shared logic from per-track logic.
4. **Read `0x02083204`** (580 bytes, carried) — the move manager's sole caller.
