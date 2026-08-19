# Findings: the owner is a ColPrm record, exactly `0x188` bytes

Loop-Atlas iteration 77. Static.

Sweeping block writes (iteration 76's blind spot) found the object's **teardown**, which named it.

The struct tracked since iteration 70 under three labels is **`0x188` bytes**, lives on two lists owned by the **ColPrm manager**, and is the record `BattleColPrm.cpp` manages. Four iterations of chasing pointers ended by asking what memsets it.

Iteration 69 asked whether `ColPrm+0x08` and `+0x10` are manager list heads. **Yes — they are the free pool and the active list of these records.**

---

## 1. The block sweep

`find_field_writers.py --blocks` resolves `memset`/`memcpy` destinations and sizes, then reports calls that cover the target offset. Five cover `+0xE8`; **124 calls with computed destination or size are excluded**.

| site | call | destination | size | companions |
|---|---|---|---|---|
| `0x02076C2C` | memset | `r7+0x8` | `0x5e0` | — |
| `0x0207BDB0` | memset | `r4+0x0` | `0x1040` | — |
| `0x0207CA80` | memset | `r4+0xa4` | `0xd0` | 9 of 10 |
| **`0x0207CE58`** | **memset** | **`r4+0x0`** | **`0x188`** | `0x40`, `0x60` |
| `0x02168BE0` | memset | `r4+0x0` | `0x314` | — |

`0x0207CA80` is the installer's known region wipe. `0x0207CE58` is new — `0x188` matches the minimum size iteration 75 derived from observed fields.

## 2. It is a teardown

Inside `0x0207CCD4(r0 = the manager, r1 = the record)`:

```
0x0207CE1C  ldr r1, [r4, #0x60]    ; the ColObj
0x0207CE34  bl  #0x207b000         ; destroy it
0x0207CE3C  str r0, [r4, #0x60]    ; owner+0x60 = 0
0x0207CE44  add r0, r5, #0x10
0x0207CE48  bl  #0x2037c24         ; unlink(mgr+0x10, record)
0x0207CE54  mov r2, #0x188
0x0207CE58  bl  #0x20517fc         ; memset(record, 0, 0x188)
0x0207CE60  add r0, r5, #8
0x0207CE64  bl  #0x2037b98         ; link(mgr+0x8, record)
```

Destroy the ColObj, leave the active list, wipe, join the free pool. Textbook free — the memset sizes the struct at **exactly `0x188`**.

Earlier in the same function it returns the record's bucket nodes: walks `[record+0x68]+0x20`, matches nodes whose `+0x8` is this record, and links them into `mgr+0xD8` — the bucket free list from iteration 68.

## 3. `r5` is the ColPrm manager

Fingerprinted, not assumed. Caller `0x0207FB60`:

```
0x0207FB64  ldr r0, [r0, #4]
0x0207FB68  ldr r4, [r0, #0x10]
0x0207FB6C  ldr r1, [r4, #0xfc]    ; +0xFC
0x0207FB74  blx r1
0x0207FB78  ldr r1, [r4, #0x100]   ; +0x100
0x0207FB80  blx r1
0x0207FB84  ldr r1, [r4, #0x104]   ; +0x104
0x0207FB8C  blx r1
0x0207FB90  ldr r1, [r4, #0x10]
0x0207FB98  mov r0, r4
0x0207FB9C  bl  #0x207ccd4         ; teardown(mgr, each record on mgr+0x10)
```

`+0xFC`, `+0x100`, `+0x104` are the first three entries of the ColPrm manager's 19-entry phase table (`+0xFC`–`+0x148`, iteration 62). Nothing else in the ROM has that shape. `r4` here — and `r5` inside the teardown — is the **ColPrm manager**, and this loop drains `mgr+0x10` one record at a time.

## 4. The name

`Battle_ColPrmManCreate` builds the manager. It keeps a free pool at `+0x08`, an active list at `+0x10`, allocates records to entities, and tears them down per frame. A **ColPrm manager manages ColPrms** — this record is what `BattleColPrm.cpp` is named after.

The contents follow: a per-entity **collision-parameter record** is where you'd expect `+0x60` (the ColObj), `+0x34`/`+0x38` (hitbox node seeds), `+0xA4`–`+0x173` (per-hit scratch region), and the damage fields `+0xE8`, `+0x130`, `+0x140`, `+0x144`.

Three labels, one struct, now sized and named:

| was tracked as | since |
|---|---|
| the damage pipeline's scratch base `[[char+0x1a8]+0x10]` | iteration 47 |
| the ColObj's owner, `[ColObj+0x28]` | iteration 71 |
| the `0x2C`-byte pool-node owner | iterations 70–73 |

## 5. ColPrm manager list heads, resolved

Iteration 69 found 21 link/unlink sites at `+0x08`/`+0x10`/`+0x18`/`+0x20` but declined to claim any as manager heads — offset matching without a verified base is worthless. With the base now fingerprinted:

| head | holds |
|---|---|
| `+0x08` | **free pool of `0x188`-byte ColPrm records** |
| `+0x10` | **active list of ColPrm records** |
| `+0x18` | free pool, `0x2C`-byte nodes (iteration 69) |
| `+0x20` | free pool, `0x10`-byte nodes (iteration 69) |
| `+0xD8` | bucket free list (iteration 68) |

Consistent with iteration 75: the installer takes a record from `[arg0+0x8]` where `arg0 = [[0x0214BE14]+0x8C]`, so that expression resolves to the ColPrm manager, and `+0x8` is the free pool it draws from.

**Careful:** iteration 70 showed `record+0x08` is *also* a list head (holding the `0x2C` nodes). Manager`+0x08` and record`+0x08` are different lists on different structs — same offset, different base.

## 6. `+0xE8` unchanged

The block pass adds nothing to B11. `0x0207CE58` wipes the record, `0x0207CA80` wipes the scratch region — both zero `+0xE8`, neither sets it. **Every confirmed write to `+0xE8` ROM-wide is still a memset.** The vestigial-field hypothesis stays PLAUSIBLE, with block writes swept and `stm` the only untried form.

## Predictions status

| Claim | Verdict |
|---|---|
| The record is exactly `0x188` bytes | **CONFIRMED_STATIC** — `mov r2,#0x188` / `memset(r4,0,0x188)` at `0x0207CE54`–`0x0207CE58` |
| `0x0207CCD4` is the record's teardown | **CONFIRMED_STATIC** — destroy ColObj, unlink `mgr+0x10`, wipe, link `mgr+0x8` |
| `r5`/`r4` is the ColPrm manager | **CONFIRMED_STATIC** — `+0xFC`/`+0x100`/`+0x104` phase-table dispatch at `0x0207FB6C`–`0x0207FB8C` |
| `ColPrm+0x08` is the free pool of records | **CONFIRMED_STATIC** — `link(r5+8, record)` at `0x0207CE64` after the wipe |
| `ColPrm+0x10` is the active list of records | **CONFIRMED_STATIC** — `unlink(r5+0x10, record)` at `0x0207CE48`; drained by `0x0207FB90` |
| `[[0x0214BE14]+0x8C]` is the ColPrm manager | **CONFIRMED_STATIC** — installer draws from its `+0x8`, which is the record free pool |
| The record's bucket nodes return to `mgr+0xD8` | **CONFIRMED_STATIC** — `add r0,r5,#0xd8` then link, at `0x0207CD18`–`0x0207CD20` |
| The record is what `BattleColPrm.cpp` manages | **CONFIRMED_STATIC** — free pool and active list both hang off `Battle_ColPrmManCreate`'s manager |
| Its name is literally "ColPrm" | **PLAUSIBLE** — no allocation tag or assert string binds to it; the name is inferred from its manager |
| A block write sets `+0xE8` | **REFUTED** — 5 covering calls, all memsets that zero it |
| `+0xE8`/`+0x140` are vestigial in retail | **PLAUSIBLE** *(carried)* — block writes now swept; `stm` remains |

## Next angles, ranked

1. **Map the ColPrm record's `0x188` bytes** with `struct_fields.py`, anchored on the teardown and installer. Most load-bearing struct in the combat engine, now bounded and reachable from two verified entry points.
2. **Resolve `record+0x68`** — points at something whose `+0x20` list holds this record's bucket nodes. Likely a bucket or the manager itself.
3. **Read the 124 block calls with computed sizes** if `+0xE8` matters again — only unswept route besides `stm`.
4. **Re-audit the map's `char+0xNN` offsets** across the three objects (carried).
