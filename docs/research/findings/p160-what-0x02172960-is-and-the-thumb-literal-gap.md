# P160 — `[0x02172960]` is a 368-byte ov6 object, not a stat block; xrefs.json misses 89% of Thumb literal loads

**Iteration 160. Static only.** Came in to identify `[0x02172960]`, the multiplier term from P158's status-duration formula. Found the answer — and had to retract a name from last wake. Also found a toolchain blind spot much worse than the one on record.

## What the object is

`CONFIRMED_STATIC`: `0x02172960` is a **pointer global with exactly two writes**, both in ov6 Thumb.

Init at ov6 `0x0214CD5C`–`0x0214CD74`:

```
0x0214cd5c: 2017       mov r0, #0x17
0x0214cd5e: 49b8       ldr r1, [pc, #0x2e0]   ; = 0x0214d040
0x0214cd60: 4ab8       ldr r2, [pc, #0x2e0]   ; = 0x0214d044
0x0214cd62: 0100       lsl r0, r0, #4         ; r0 = 0x17 << 4 = 0x170 = 368
0x0214cd64: 237f       mov r3, #0x7f
0x0214cd66: f6cd ea5a  blx #0x0201a21c        ; alloc(0x170, __FILE__, __FUNCTION__, 0x7F)
0x0214cd6a: 49b7       ldr r1, [pc, #0x2dc]   ; = 0x0214d048  (holds 0x02172960)
0x0214cd6c: 2217       mov r2, #0x17
0x0214cd6e: 6008       str r0, [r1, #0x0]     ; [0x02172960] = the object
0x0214cd70: 2100       mov r1, #0x0
0x0214cd72: 0112       lsl r2, r2, #4         ; 0x170 again
0x0214cd74: f704 ed42  blx #0x020517fc        ; memset(obj, 0, 0x170)
```

Teardown at ov6 `0x0214E18A`–`0x0214E196`:

```
0x0214e18a: 480f       ldr r0, [pc, #0x3c]    ; = 0x0214e1c8  (holds 0x02172960)
0x0214e18c: 6800       ldr r0, [r0, #0x0]
0x0214e18e: f6cd e85a  blx #0x0201b244        ; free(obj)
0x0214e192: 480d       ldr r0, [pc, #0x34]    ; same pool word
0x0214e194: 2100       mov r1, #0x0
0x0214e196: 6001       str r1, [r0, #0x0]     ; null it
```

A **368-byte heap object** — allocated through the tagged allocator with its own `__FILE__`/`__FUNCTION__` arguments, zeroed, freed on exit. Lifetime = ov6 residency. Same allocate-store-null shape as the P153 network-session slot, same static-analysis ceiling: nothing in the code spells out its name.

`CONFIRMED_STATIC`: **only `+0x00` is ever accessed.** `base_offset_scan.py` across arm9, ov6, and ov11 reports 276 accesses and 2 stores, all at `+0x00`, with liveness tracking on. Positive control passed — the same scan against `0x0214CCF4` returns its known `+0x00`/`+0x01`/`+0x04` accesses. So this is a pure pointer global, not a struct base.

## Correction: not a "per-character stat block"

P158 called `[[0x02172960] + charIdx*4 + 0x4C]` a **per-character stat**. `REFUTED` as a label — the arithmetic was right, the name was wrong.

arm9 `0x020854F4`–`0x02085538` reads the same expression shape and does something no stat would:

```
0x020854F4: ldrsb r0, [r4, #5]      ; a character index
0x02085504: ldr   r1, [pc, #0xac]   ; -> 0x02172960
0x02085508: ldr   r1, [r1]
0x0208550C: ldr   r1, [r1, #0x158]
0x02085510: sub   r1, r1, #1
0x02085514: cmp   r0, r1
0x02085518: movge r0, r1            ; clamp the index to [obj+0x158] - 1
0x0208551C: ldr   r1, [pc, #0x94]   ; -> 0x02172960
0x02085520: ldr   r2, [r1]
0x02085524: ldr   r1, [r2, #0x15c]
0x02085528: add   r1, r2, r1, lsl #2
0x0208552C: ldr   r1, [r1, #0x4c]   ; [obj + [obj+0x15C]*4 + 0x4C]
0x02085530: cmp   r0, r1            ; compared against a character index
0x02085538: bne   #0x2085550        ; then a vtable call with 1 or 0
```

The value is **compared for equality against a character index** clamped to `[obj+0x158] - 1`. So entries in the `+0x4C` array are small integers of the same kind as character indices, not magnitudes. `not claimed`: what they actually mean.

P158's formula stands exactly — `duration = base + (base/10) * (V * 2)` — but `V` is now an unnamed small integer from this array, and calling it a stat was naming a term I hadn't identified. The "first non-constant scaling formula" is still real and still the only one; what it scales *by* is open again.

Object fields so far, all `CONFIRMED_STATIC`, all inside `0x170`:

| offset | what the code does with it |
|---|---|
| `+0x4C` | base of a word array, stride 4, indexed by a character index |
| `+0x158` | a count; used as `count - 1` to clamp an index |
| `+0x15C` | an index into the `+0x4C` array |

## Is it the battle root? Not settled

`PLAUSIBLE`: same object as the battle root P156 reached through global `0x0214D928`. The evidence is real but thin — P156 found `[root+0x158]` is the character count, and `[obj+0x158]` is used here as exactly that. P156's `root+0x110` (ObjShot manager) and `root+0x10C` (ObjCtrl manager) both fit inside 368 bytes.

`not claimed`: that they are the same. Two different globals in two different ov6 sections is equally consistent with two objects. The discriminator is cheap and queued: find `0x0214D928`'s writer and compare its allocation size against `0x170`.

## A cross-overlay handle, deliberately placed

From `overlays.json`: ov6 loads at `0x0214CD20` with `ram_size` `0x25C40` and `bss_size` `0x100`. Its image ends at exactly `0x02172960` and its BSS runs `0x02172960`–`0x02172A60` — ending where ov10/ov11 load. `0x02172960` is **the first word of ov6's BSS.**

`CONFIRMED_STATIC`: ov11 loads this global **12 times**. ov11 sits at `0x02172A60`, a different window, so the two can be resident together. This is a **deliberate cross-overlay handle** — ov6 publishes the pointer at a fixed address and ov11 reads it. Not stale-pointer reuse.

## Tool blind spot: xrefs.json misses 89% of Thumb literal loads

Chasing the writer turned up a discrepancy worth more than the writer itself.

| region | actual pc-relative loads of `0x02172960` | xrefs.json recorded |
|---|---|---|
| arm9 | 2 | 2 — exact |
| ov11 | 12 | 12 — exact |
| ov6, ARM | 88 | 88 — exact |
| ov6, Thumb | **167** | **18** |
| **ov6 total** | **255** | **106** |

`CONFIRMED_STATIC`: xrefs.json misses **149 of 167** ov6 Thumb pc-relative literal loads — **89%**. Every ARM figure matches exactly, so the gap is specifically **Thumb pc-relative literal loads in overlays**.

Convergent verification: two independent methods agree on 255. `base_offset_scan.py` gets there through its own decoder plus a liveness walk; my check is a raw sweep of `ov06.bin` for the Thumb `01001` encoding (`0x4800`–`0x4FFF`), resolving `Align(pc+4,4) + imm8*4` against the 120 pool words holding the value. Different representations, same number.

**This supersedes the bound on record.** The known figure was "465 of 4941 arm9 ARM pc-relative loads unrecorded = 9.4%". For Thumb-heavy overlay code it's an order of magnitude worse. Any literal-load count this campaign has quoted for a global touched by Thumb code is a **severe floor**, not an estimate — including the handoff's "`[0x020AFE90+0x28]`, 149 literal loads", which should be re-measured before anyone reasons from it.

## Convergent verification on the decode

Codex got both Thumb fragments as raw halfwords — no addresses, no hypothesis — before this was written. It agreed on everything load-bearing: `0x17 << 4 = 0x170` for both the allocation size and `memset` length, `r3 = 0x7F`, the two `blx` pairs being single 32-bit instructions, and the store of the allocator's return value into the global.

It also caught something I hadn't checked. In the teardown, the two literal loads use **different displacements** (`0x3C` and `0x34`) at instruction addresses eight bytes apart. Codex showed from displacement arithmetic alone that `Align(B+4,4) + 0x3C == Align(B+0xC,4) + 0x34`, so both resolve to **the same pool word** — proving the `free` and the null-store act on the same global, established without knowing a single address. That's the relative-versus-absolute cross-check the charter asks for, arrived at from the weaker representation on its own.

## Queued

1. **Find `0x0214D928`'s writer and its allocation size.** If `0x170`, it's the same object as `[0x02172960]` and two campaign threads merge. Cheap, decisive, top of queue.
2. **Re-measure every campaign literal-load count involving Thumb code**, starting with `[0x020AFE90+0x28]`. The 89% Thumb gap makes those numbers untrustworthy as stated.
3. Identify what the `+0x4C` word array holds, now that "stat" is retracted. The arm9 site compares an entry against a character index — read `0x020854C4` whole (244 bytes, 0 recorded callers).
4. Fix or document xrefs.json's Thumb literal-load indexing. It's the single largest measured gap in the toolchain and silently weakens every global's reference census.
