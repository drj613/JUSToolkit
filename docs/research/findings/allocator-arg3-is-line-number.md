# Findings: the allocator's 4th argument is `__LINE__`, and CommonEffect is a 3-deep class

Loop-Atlas iteration 131. Static.

Read `CreateImpFunc` (`0x0206C57C`, 44 bytes) and `CloneMain` (`0x0206CFC0`, 68 bytes) — the two tagged
functions that allocate the `0x84` CommonEffect object. Two results:

1. **The allocator's 4th argument is the source line number, not an opaque tag.** This corrects the
   signature recorded in `alloc_census.py` and applies to all 732 call sites.
2. `CloneMain` exposes a **three-level C++ copy-constructor chain**, which hands over the class hierarchy
   and three concrete member offsets.

---

## 1. `r3` is `__LINE__`

`alloc_census.py`'s header documents the allocator as
`r0 = size, r1 = "SourceFile.cpp", r2 = "Function_name", r3 = tag`. The first three are right. The fourth
is a line number.

The decisive test: `CommonHSV_Create` has **five** allocation sites in one function. If `r3` were a tag or
arena ID it would repeat; if it is `__LINE__` it must increase with address and cluster.

| site | `r3` | decimal |
|---|---|---|
| `0x0206D074` | `0x2d` | 45 |
| `0x0206D144` | `0x42` | 66 |
| `0x0206D15C` | `0x43` | 67 |
| `0x0206D190` | `0x48` | 72 |
| `0x0206D1A8` | `0x49` | 73 |

Strictly increasing, and with **two adjacent pairs** — 66/67 and 72/73. Those are consecutive source lines.
No tag or arena scheme produces that.

Six more sites across four files agree, all small and all distinct:

| site | file | function | `r3` |
|---|---|---|---|
| `0x0206ADB8` | `CommonPaletteAnime.cpp` | `CommonPaletteAnime_Create` | 106 |
| `0x0206C3CC` | `ALPropSetImp.h` | `Create` | 273 |
| `0x0206C3F8` | `CommonEffect.cpp` | `CommonEffect_Init` | 103 |
| `0x0206C590` | `CommonEffect.h` | `CreateImpFunc` | 149 |
| `0x0206CFD8` | `CommonEffect.h` | `CloneMain` | 162 |
| `0x0206D074` | `CommonHSV.cpp` | `CommonHSV_Create` | 45 |

Both `CommonEffect.h` entries land in the same header, 149 before 162, matching their address order.

**So every one of the 732 allocation sites carries `__FILE__`, `__FUNCTION__` and `__LINE__`.** Sites within
a file can now be ordered by source position, not just by address.

Worth noting how `0x0206C3CC`'s line 273 is materialised:

```
0x0206C3BC  mov r0, #0x20
0x0206C3C8  add r3, r0, #0xf1     ; 0x20 + 0xF1 = 0x111 = 273
```

`0x111` is not encodable as an ARM immediate, so the compiler built it from `r0`, which already held the
size. Any census pass that resolves only `mov`-immediate and pc-relative loads reports this as COMPUTED —
correctly, per the tool's own guard.

## 2. `CreateImpFunc` — allocate, then construct

```
0x0206C580  ldr r1, [pc, #0x20]   ; "CommonEffect.h"
0x0206C584  ldr r2, [pc, #0x20]   ; "CreateImpFunc"
0x0206C588  mov r0, #0x84
0x0206C58C  mov r3, #0x95         ; line 149
0x0206C590  bl  #0x201a21c
0x0206C594  cmp r0, #0
0x0206C598  popeq {r3, pc}        ; allocation failed -> return NULL
0x0206C59C  ldr r1, [pc, #0xc]    ; = 0x02024A30
0x0206C5A0  bl  #0x206ca4c        ; construct(obj, 0x02024A30)
```

Straightforward, and it checks the allocation before using it. The constructor's second argument
`0x02024A30` points into the **library region** (below iteration 130's `0x0206ADB8` boundary) — a function
pointer or library vtable handed to the object at construction.

## 3. `CloneMain` — a three-level copy-constructor chain

```
0x0206CFD0  mov r0, #0x84
0x0206CFD4  mov r3, #0xa2         ; line 162
0x0206CFD8  bl  #0x201a21c
0x0206CFDC  movs r4, r0
0x0206CFE0  beq #0x206cffc        ; failed -> return NULL
0x0206CFE4  mov r1, r5            ; r5 = the source object
0x0206CFE8  bl  #0x2015dd4        ; PARENT copy-construct(dst, src)
0x0206CFEC  ldr r0, [pc, #0x18]   ; = 0x0209E114
0x0206CFF0  str r0, [r4]          ; +0x00 = the DERIVED vtable
0x0206CFF4  ldrh r0, [r5, #0x80]
0x0206CFF8  strh r0, [r4, #0x80]  ; copy the derived member, a halfword
```

And the parent it calls does exactly the same thing one level down:

```
0x02015DD4  push {r3, r4, r5, lr}      ; (dst = r0, src = r1)
0x02015DE0  bl  #0x20240a4             ; GRANDPARENT copy-construct
0x02015DEC  str r0, [r5]               ; +0x00 = the PARENT vtable, 0x0209C30C
0x02015DF0  ldrb r2, [r4, #0x78]
0x02015DF8  strb r2, [r5, #0x78]       ; copy the parent member, a byte
0x02015DFC  ldr r2, [r1, #0x4c]        ; r1 = 0x020A0C34
0x02015E00  add r2, r2, #1
0x02015E04  str r2, [r1, #0x4c]        ; ++*(0x020A0C80)
```

Each level does the same three things in the same order: **call the base copy, overwrite `+0x00` with its
own vtable, copy its own members.** That is textbook C++ copy-constructor codegen, and reading it upward
gives the hierarchy and the member split for free:

| level | copy function | own vtable | own member copied |
|---|---|---|---|
| grandparent | `0x020240A4` | (not read this wake) | — |
| parent | `0x02015DD4` | `0x0209C30C` | **byte at `+0x78`** |
| derived | `0x0206CFC0` (`CloneMain`) | `0x0209E114` | **halfword at `+0x80`** |

So the `0x84`-byte object has a **vtable pointer at `+0x00`** written three times during construction, each
level overwriting the last, and the final value is the derived vtable `0x0209E114`. `+0x80` is the last
member, with `+0x82`/`+0x83` as tail padding to reach `0x84`.

**The parent copy constructor increments a global counter** at `0x020A0C34 + 0x4C` = `0x020A0C80`. Counting
in the parent, not the derived, means it counts parent-class instances — a live-instance or statistics
counter.

## Predictions status

| Claim | Verdict |
|---|---|
| The allocator's `r3` is an opaque tag | **REFUTED** *(`alloc_census.py`'s documented signature)* — it is `__LINE__` |
| `r3` is the source line number | **CONFIRMED_STATIC** — five sites in `CommonHSV_Create` give 45, 66, 67, 72, 73: increasing, with two adjacent pairs |
| Line numbers agree with address order inside one file | **CONFIRMED_STATIC** — `CommonEffect.h` 149 then 162 |
| `0x0206C3CC`'s `r3` is computed, not an immediate | **CONFIRMED_STATIC** — `add r3, r0, #0xf1` reusing the size register |
| The object's vtable pointer is at `+0x00` | **CONFIRMED_STATIC** — `str r0,[r4]` at `0x0206CFF0`, `str r0,[r5]` at `0x02015DEC` |
| The class is at least three levels deep | **CONFIRMED_STATIC** — `0x0206CFC0` → `0x02015DD4` → `0x020240A4`, each setting its own vtable |
| The parent adds a byte at `+0x78`, the derived a halfword at `+0x80` | **CONFIRMED_STATIC** — copied individually after each base call |
| The parent copy bumps a counter at `0x020A0C80` | **CONFIRMED_STATIC** — `0x02015DFC`–`0x02015E04` |
| Both `CreateImpFunc` and `CloneMain` check the allocation | **CONFIRMED_STATIC** — `popeq` at `0x0206C598`, `beq` at `0x0206CFE0` |
| `0x020240A4` is the top of the hierarchy | **not claimed** — not read this wake; it may have its own base |
| The counter at `0x020A0C80` is a live-instance count | **PLAUSIBLE** — incremented on copy; no decrement seen, because the destructor was not read |

## Next angles, ranked

1. **Dump the two vtables**, `0x0209C30C` (parent) and `0x0209E114` (derived). Concrete addresses, and every
   vtable slot read in iterations 127–129 was a guess at an offset in *some* vtable. This turns slot offsets
   into named function pointers.
2. **Update `alloc_census.py`'s docstring and add a `--line` column.** The tool's own documentation is now
   wrong, and line numbers are useful output.
3. **Read `0x020240A4`** — the grandparent copy, which should end the hierarchy and add more members.
4. **Trace the bases of the 64 `+0x24` sites** (carried from iteration 130).
