# Findings: `entity+0x10` is one object wearing three names

Loop-Atlas iteration 75. Static.

Iteration 72 called `entity+0x10` the ColObj; iteration 47 called it the damage
pipeline's scratch object. **Iteration 72 is wrong — `entity+0x10` is the ColObj's
*owner*, and settling this collapses three tracked objects into one.**

Installer `0x0207C988` **returns** the owner, not the ColObj. That owner is
`[[char+0x1a8]+0x10]`: the damage pipeline's scratch base.

**The pool-node owner parked since iteration 73 is the same object.** It was already
documented under a different name in an earlier campaign.

---

## 1. The installer returns its owner, not the ColObj

```
0x0207C988  push {r4, r5, r6, r7, r8, sb, lr}
0x0207C990  mov sb, r0             ; sb = arg0
0x0207C9AC  ldr r4, [sb, #8]       ; r4 = arg0->[0x8] = THE OWNER
...
0x0207CA18  bl  Battle_ColObjCreate
0x0207CA20  str r0, [r4, #0x60]    ; the ColObj goes at owner+0x60
...
0x0207CB24  ldr r0, [r4, #0x40]
0x0207CB2C  bic r0, r0, #0x200     ; clear a bit in owner+0x40
0x0207CB30  str r0, [r4, #0x40]
0x0207CB34  mov r0, r4             ; <- RETURNS THE OWNER
0x0207CB38  str r1, [r4, #0x50]
0x0207CB40  pop {r4, r5, r6, r7, r8, sb, pc}
```

The ColObj never reaches `r0` at return. It stays at `owner+0x60`.

## 2. `r4` is still the entity at the store

In `0x020834D4`, `r4` is loaded once (`ldr r4,[r0,#0x14]` at `0x020834EC`) and never
rewritten through `0x02083564`:

```
0x0208352C  str r0, [r4, #0x30]    ; entity+0x30 = the character (iteration 74)
0x02083550  ldr r0, [r0]           ; the manager global
0x02083558  ldr r0, [r0, #0x8c]    ; installer arg0
0x02083560  bl  #0x207c988
0x02083564  str r0, [r4, #0x10]    ; entity+0x10 = the OWNER
```

`entity+0x10` = the installer's return = the owner. Pure dataflow, no inference.

## 3. The three names are one object

| tracked as | since | evidence |
|---|---|---|
| the damage pipeline's scratch base `[[char+0x1a8]+0x10]` | earlier campaign, iteration 47 | fields `+0xE8`, `+0x130`, `+0x140`, `+0x144`; `+0x40` flags, bit `0x800` gates delta application |
| the ColObj's owner, `[ColObj+0x28]` | iteration 71 | `ldr r4,[r0,#0x28]` in both `+0x1C` and `+0x20` methods |
| the `0x2C`-byte pool-node owner | iterations 70–73, **parked** | node list at owner`+0x8`; nodes initialised from owner`+0x34`/`+0x38` |

Iteration 74 established `char+0x1a8` = the entity. This wake establishes
`entity+0x10` = the owner. So `[[char+0x1a8]+0x10]` **is** the owner — same address
expression, not resemblance.

Independent corroboration: the installer does `bic r0,r0,#0x200` on `owner+0x40`
(`0x0207CB2C`), and iteration 47 records `+0x40` as a flags word whose bit `0x800`
gates delta application. Two wakes, two bits, same bitfield.

Combined field map:

```
the owner  (>= 0x188 bytes; pool-allocated from [installer arg0 + 0x8], not the tagged allocator)
  +0x08   list head for the 0x2C-byte pool nodes
  +0x34   source for node+0x14
  +0x38   source for node+0x18
  +0x3C   written by the installer
  +0x40   flags: bit 0x200 cleared at 0x0207CB2C; bit 0x800 gates delta application
  +0x50   written at 0x0207CB38
  +0x60   the ColObj  (bookkeeping only -- NOT the method dispatch route, iteration 73)
  +0xA4   start of a 0xD0-byte memset region
  +0xE8   the one-shot per-hit damage magnitude (writer still unfound)
  +0x130  second signed field read alongside +0xE8
  +0x140  fed to the damage trampoline with no negation
  +0x144  the SP counterpart of +0x140
  +0x174  byte, +0x175 bitfield (bits 0x30, 0xC, 0x3 manipulated)
  +0x182  byte
  +0x184  halfword, +0x186 halfword
```

`+0xE8` sits inside the `0xD0`-byte memset region (`+0xA4`–`+0x173`), so the per-hit
damage field is **zeroed at installation** — fits a one-shot drain.

## 4. Why three wakes failed to name it

Iterations 71–73 walked pointers *outward* — allocator `r4` → `ColObj+0x28` →
`[installer arg0 + 0x8]` → shape-matching against allocation sizes. Every hop was
correct; none checked what the installer *returns*, one instruction away the whole time.

The object could never have been found by size: it comes from a pool at `[arg0+0x8]`,
not the tagged allocator. Iteration 73's method — match `>= 0x183` bytes against the
census — was searching a list the answer was not on.

**Rule:** when tracing an object's identity, read the **return value** of every
function that touches it before following another pointer. Returns are stronger handles
than fields, and cost one instruction to check.

## 5. What this does not settle

The owner still has **no name** — not in the tagged-allocation census, no assert string.
Naming it requires tracing the pool at `[[0x0214BE14]+0x8C]+0x8` to whatever fills it.

**Not claimed:** that `+0xE8`/`+0x130`/`+0x140`/`+0x144` and
`+0x34`/`+0x38`/`+0x60`/`+0x174` were ever observed on the same *runtime* object. The
identity is by address expression and rests on iteration 47's `[[char+0x1a8]+0x10]`
being correctly derived. If that expression is wrong, so is this unification.

## Predictions status

| Claim | Verdict |
|---|---|
| Installer `0x0207C988` returns the owner, not the ColObj | **CONFIRMED_STATIC** — `mov r0,r4` at `0x0207CB34`, `r4` from `0x0207C9AC` |
| `entity+0x10` holds the installer's return value | **CONFIRMED_STATIC** — `str r0,[r4,#0x10]` at `0x02083564`, `r4` unwritten since `0x020834EC` |
| `entity+0x10` is the ColObj | **REFUTED** *(iteration 72)* — the ColObj is at `owner+0x60` |
| `[[char+0x1a8]+0x10]` and `[ColObj+0x28]` are the same object | **CONFIRMED_STATIC** — same address expression, given iteration 74's `char+0x1a8` = the entity |
| The parked `0x2C`-node owner is the damage-pipeline scratch object | **CONFIRMED_STATIC** — all three are `entity+0x10` |
| `owner+0x40` is a flags word | **CONFIRMED_STATIC** — `bic #0x200` at `0x0207CB2C`, plus iteration 47's bit `0x800` |
| `+0xE8` is zeroed at installation | **CONFIRMED_STATIC** — inside the `0xD0` memset from `+0xA4` at `0x0207CA80` |
| The owner is heap-allocated via the tagged allocator | **REFUTED** — taken from a pool at `[installer arg0 + 0x8]` |
| The owner has a name | **not claimed** — no allocation tag, no assert string |
| The `+0xE8` group and the `+0x34`/`+0x60` group were seen on one runtime object | **not claimed** — identity is by address expression only |

## Next angles, ranked

1. **Find the writer of `owner+0xE8`** — highest-value unresolved item (spec **B11**).
   Now a sharper target: a store to `+0xE8` on a base that also carries `+0x60`,
   `+0x40`, or the `+0xA4` region.
2. **Name the owner** by tracing the pool at `[[0x0214BE14]+0x8C]+0x8`.
3. **Re-audit `char+0xNN` offsets** across the three objects (carried) — the ov6 `0x1F0`
   character, the entity, and the arm9 `+0x56c` struct.
4. **Read `ColObj+0x24`'s method** `0x0207D94C` (carried).
