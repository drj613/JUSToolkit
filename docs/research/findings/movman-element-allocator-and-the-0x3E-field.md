# Findings: the element allocator, a field at `+0x3E`, and the collision module reaching into BattleMove

Loop-Atlas iteration 138. Static.

Went looking for whoever sets `+0x34` bit `0x100` — the snapshot suppressor from iteration 137. **Did not
find it.** What the search found instead is more useful: the **element allocator**, a field at `+0x3E` that
materially strengthens iteration 137's stride, and a cross-module call I did not expect.

---

## 1. How the candidate was found

`+0x34` has **1092** hits ROM-wide, so offset matching alone is hopeless — the standing lesson since
iteration 69. `find_field_writers.py` with companions on the element's distinctive offsets
(`0x0C`, `0x14`, `0x18`, `0x26`) cut 85 direct writers down to a shortlist, and one candidate stood out:

```
MATCH 0x02082cd0  str r0, [r4, #0x34]   fn=0x02082c34  companions=['0x14','0x18','0xc']
MATCH 0x02082ce4  strne r0, [r4, #0x34] fn=0x02082c34  companions=['0x14','0x18','0xc']
MATCH 0x02082d24  str r1, [r4, #0x34]   fn=0x02082c34  companions=['0x14','0x18','0xc']
```

Three writes in one function, all three companions present, and `0x02082C34` sits immediately after
`Battle_MoveManCreate`'s literal pool — i.e. **inside `BattleMove.cpp`**. The companion pass is doing
exactly the job it was built for.

## 2. `0x02082C34` is the element allocator

248 bytes, one caller.

```
0x02082C38  mov r5, r0              ; r5 = the container
0x02082C3C  ldr r4, [r5, #8]        ; r4 = head of the FREE list
0x02082C44  cmp r4, #0
0x02082C4C  moveq r0, #0
0x02082C50  popeq {...}             ; pool empty -> return NULL
0x02082C58  add r0, r5, #8
0x02082C5C  bl  #0x2037c24          ; unlink(free, r4)   -- take it
0x02082C60  mov r0, r5
0x02082C68  bl  #0x2037b98          ; link(active, r4)    -- attach it
0x02082C6C  str r7, [r4, #8]        ; +0x08 = arg1
```

Free list at `container+0x08`, active list at `container+0x00`, graceful NULL on exhaustion — the same
fixed-capacity recycler shape as the ColPrm `+0x18` pool (iteration 70).

Then it initialises the element, with the **same previous/current snapshot iteration 137 found**, on all
three branches:

```
[r4+0x14] = [r4+0x0C]      ; at 0x02082C78, 0x02082C98 and 0x02082CB4
[r4+0x18] = [r4+0x10]
```

and sets the current pair either from the caller or to a default:

```
arg2 != 0:  [r4+0x0C] = [arg2]      [r4+0x10] = [arg2+4]
arg2 == 0:  [r4+0x0C] = 0x10000     [r4+0x10] = 0x10000
```

Three separate copies of the snapshot in one function is strong evidence that this and iteration 137's
consumer handle **the same object type**.

`0x10000` is `1.0` in 16.16 fixed point, which is the natural default for a **scale or rate pair** rather
than a position. **PLAUSIBLE** — the value is certain, the interpretation is not, and iteration 125 found a
*different* module using 24.8.

> **REFUTED in iteration 139.** Wrong. `+0x0C`/`+0x10` are the owner's transform x/y (`asr` 4), read from
> `[[owner+4]+0x50]` at the call site — so `0x10000` is a default **position**, not a unit scale. The error
> was reasoning from a recognisable constant instead of reading where the data comes from. Kept here rather
> than deleted; see `element-0x0C-is-the-owners-world-position.md`.

## 3. The field at `+0x3E` — why this matters most

```
0x02082CB8  mov r1, #0x20
0x02082CE8  strb r1, [r4, #0x3c]     ; +0x3C = 0x20
0x02082CEC  mov r0, #8
0x02082CF0  strb r0, [r4, #0x3d]     ; +0x3D = 8
0x02082CF4  strb r1, [r4, #0x3e]     ; +0x3E = 0x20
```

Iteration 137 could only show the element reaching `+0x34`, so it needed at least `0x38` bytes, and rated
the `0x40` stride PLAUSIBLE on tiling alone. **The element now demonstrably reaches `+0x3E`**, so it needs
at least `0x3F`.

`0x40` is the smallest aligned size that fits, and it is the only stride that tiles `+0x648`–`+0x2647` into
the 128 elements the constructor counted. That is a much narrower gap than tiling alone.

It is **still PLAUSIBLE, not CONFIRMED**, for the same reason as last wake: no instruction anywhere computes
`base + i * 0x40`. But `0x3F ≤ size ≤ 0x40` plus exact tiling leaves very little room.

## 4. New flag bits, and the one I was looking for is absent

| bit | when |
|---|---|
| `0x1` | always, at `0x02082CD0` |
| `0x200` | if `[container+0x28] & 1`, at `0x02082CE4` |
| `0x8` | at `0x02082D24`, just before the return |

**Bit `0x100` is never set here.** The allocator is the most obvious place for "suppress the first
snapshot", and it does not do it — so whatever sets `0x100` is elsewhere. The task's stated target is
**not achieved**.

Worth noting *why* the allocator does not need it: it performs the snapshot itself on every branch, so a
freshly allocated element already has consistent previous values. That makes `0x100` more likely to belong
to **repositioning** than to creation — which redirects the search rather than closing it.

## 5. The collision module reaches into BattleMove

The single caller is **`0x0207C988`** — the ColObj installer from iterations 71 and 72 — at `0x0207CA08`:

```
0x0207CA04  ldr r0, [sb, #0xf0]     ; arg0 = [installer_arg0 + 0xF0]
0x0207CA08  bl  #0x2082c34
```

So collision setup allocates a BattleMove element. That is a direct `BattleCol.cpp` → `BattleMove.cpp`
dependency, and it gives `+0xF0` on the installer's `arg0` a purpose: it holds the element container.

Iteration 72 established the installer's `arg0` as `[[r0]+0x8C]` at its own call site, and it is **not**
established to be the ColPrm manager — so I am *not* claiming this is `ColPrmMan+0xF0`, despite the queue
carrying an item about that offset. Same number, unproven identity.

## 6. One ambiguity I cannot resolve here

Iteration 137's consumer walks `ldr ip, [ip]` and reads `lr = [ip+8]`, then uses `lr+0x0C`/`+0x34`. Here,
`r4` is itself linked by the list library *and* has `+0x08` set to `arg1` *and* carries `+0x0C`/`+0x34`.

Two readings fit:

- `ip` is a separate `0xC` link and `lr` is this element (iteration 137's reading), or
- `ip` **is** this element, and `lr = [element+0x08]` is a different object that happens to share offsets.

The discriminator is what `arg1` actually is at `0x0207CA08` — `r1` is set earlier than the six instructions
I read. **Not claimed** either way.

## Predictions status

| Claim | Verdict |
|---|---|
| `+0x34` bit `0x100` is set by the element allocator | **REFUTED** — it sets `0x1`, `0x200` and `0x8` only |
| The queued task (find `0x100`'s writer) succeeded | **REFUTED** *(my own task)* — still unknown |
| `0x02082C34` allocates elements from a free list | **CONFIRMED_STATIC** — `unlink(container+8)`, `link(container)`, NULL on empty |
| The pool fails gracefully when exhausted | **CONFIRMED_STATIC** — `cmp r4,#0`; `moveq r0,#0`; `popeq` |
| This function and iteration 137's consumer share an object type | **CONFIRMED_STATIC** — the same `+0x14←+0x0C`, `+0x18←+0x10` snapshot, three times |
| The element reaches `+0x3E` | **CONFIRMED_STATIC** — `strb r1,[r4,#0x3e]` at `0x02082CF4` |
| The element is `0x40` bytes | **PLAUSIBLE** *(strengthened)* — needs ≥ `0x3F`, `0x40` is the smallest aligned fit and the only stride that tiles; still no `base + i*0x40` |
| `+0x0C`/`+0x10` default to `0x10000` when `arg2` is NULL | **CONFIRMED_STATIC** — `0x02082C9C`, `0x02082CAC`, `0x02082CB0` |
| `0x10000` means `1.0` in 16.16, i.e. a scale pair | **REFUTED** *(iteration 139)* — `+0x0C`/`+0x10` are the owner's transform x/y (`asr` 4); `0x10000` is a default **position**. See `element-0x0C-is-the-owners-world-position.md`. |
| The ColObj installer allocates a BattleMove element | **CONFIRMED_STATIC** — `0x0207CA08` inside `0x0207C988` |
| `[installer_arg0+0xF0]` is `ColPrmMan+0xF0` | **not claimed** — same offset, identity never established |
| `0x100` belongs to repositioning rather than creation | **SPECULATIVE** — the allocator snapshots on every branch, so creation does not need it |
| Iteration 137's `lr` is this element | **not claimed** — two readings fit; the discriminator is `arg1` at `0x0207CA08` |

## Next angles, ranked

1. **Read `0x0207C988`'s `r1`/`r2` setup before `0x0207CA08`.** One short read settles section 6's ambiguity
   *and* names the element's two-word current pair from the caller's side.
2. **Search for `orr .., #0x100` on a base with companions `0x0C`/`0x14`/`0x34`** — the direct hunt for the
   snapshot suppressor, now knowing the allocator is not it.
3. **Read the rest of `0x02082C34`** (`0x02082CF8`–`0x02082D2C`) — it touches `container+0x18`, another list.
4. **Read `0x0208317C`** (136 bytes, carried) — the second track's callback.
