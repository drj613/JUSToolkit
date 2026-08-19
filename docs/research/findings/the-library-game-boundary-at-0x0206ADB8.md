# Findings: the library/game boundary is at `0x0206ADB8`, and the facing chain is CommonEffect code

Loop-Atlas iteration 130. Static.

**The queued task failed.** I set out to name the other bits of the `+0x24` dirty byte and couldn't. What
the attempt turned up instead is more useful: a **hard boundary in arm9 between middleware and game code**,
which explains why several functions in this chain have no name in any tool I have.

---

## 1. Why the bits task is blocked

`0x02024C3C` is the only setter, and **both** its callers pass `bits = 1` (iterations 128–129). The setter
tells me nothing about bits beyond `0x01`.

Going the other way — finding code that *reads* the flags — hits the common-offset wall:

| scope | `ldrb`/`strb` at `+0x24` |
|---|---|
| ROM-wide, any access | 1838 hits |
| ROM-wide, `strb` only | 86 |
| the library region `0x0200`–`0x0206` | 64 |
| the setter's own neighbourhood `0x02024`–`0x02026` | **3** — all inside `0x02024C3C` itself |

Only three accesses sit near the setter, and all three *are* the setter. The readers are scattered among 64
unattributed candidates, and `+0x24` is too common an offset to attribute by offset alone. This needs
per-site base tracing, which is its own task.

## 2. The boundary: `0x0206ADB8`

Running the allocation census over address ranges instead of sizes:

- **62** tagged allocation call sites in arm9.
- The **lowest** is `0x0206ADB8` (`CommonPaletteAnime_Create`, `CommonPaletteAnime.cpp`).
- Below it — the whole of `0x02000000`–`0x0206ADB7` — there are **zero** tagged allocations.

The game's allocator names every call site with a `File.cpp` and a function. A region with none of those
tags is not game code. Everything below `0x0206ADB8` is **middleware / SDK**, and the census can *never*
name it.

That explains a whole run of dead ends:

| function | role established | why it has no name |
|---|---|---|
| `0x02051890` | `memcpy(dst=r0, src=r1, n=r2)` (iteration 129) | below the boundary |
| `0x020517FC` | `memset` | below the boundary |
| `0x02024C3C` | dirty-flag setter (iteration 129) | below the boundary |
| `0x02024BE4` | vector reset-to-zero (iteration 129) | below the boundary |
| `0x02011B38` | lazy-init child accessor (iteration 128) | below the boundary |
| `0x02037B98` / `0x02037C24` | list link / unlink | below the boundary |

Every unnamed helper this investigation has leaned on lives in the untagged region. That is not a
coincidence and not a gap in the tooling — it is the shape of the binary. **Stop trying to name functions
below `0x0206ADB8` from allocation tags.**

## 3. The facing chain sits inside CommonEffect

Above the boundary, tags resume. The census sites bracketing the iterations 125–129 chain:

```
0x0206C3CC  0x20  Create           ALPropSetImp.h
0x0206C3F8  0x28  CommonEffect_Init CommonEffect.cpp
0x0206C590  0x84  CreateImpFunc    CommonEffect.h     <- in function 0x0206C57C
      ...
0x0206CA8C        (the callback installer, 1004 bytes, iteration 128)
0x0206CEAC        (the apply-if-changed callback, iteration 128)
0x0206CF28        (the boolean getter, iteration 127)
      ...
0x0206CFD8  0x84  CloneMain        CommonEffect.h     <- in function 0x0206CFC0
0x0206D074  0x60  CommonHSV_Create CommonHSV.cpp
```

Two things follow.

**`CommonEffect`'s object is `0x84` bytes.** `CreateImpFunc` and `CloneMain` both allocate `0x84` under the
same `CommonEffect.h` tag — a create and a clone of the same class, agreeing on size. This is call-site
binding, the strong kind of evidence, not proximity.

**The facing chain is bracketed by CommonEffect code.** `0x0206CA8C`, `0x0206CEAC`, and `0x0206CF28` all
fall between two `CommonEffect.h` sites that share the same file *and* the same size. Bracketed containment
beats nearest-neighbour guessing, but it is still proximity — a `.cpp` boundary could fall inside the gap.
**PLAUSIBLE**, not confirmed.

As a consistency check in the other direction: iteration 125's arena walker at `0x0207DD40` sits above
`0x0207C4E0` (`Battle_ColPrmManCreate`, `BattleColPrm.cpp`), exactly where the existing docs place the
phase table. The boundary reasoning agrees with what was already known.

**`AL` is a middleware namespace.** `ALPropSetImp.h`, `ALStreamImp.h`, `ALTextDS.cpp` — with `Create` and
`CreateImpFunc` entry points, i.e. a templated library sitting just above the boundary.

## 4. A lead on bit `0x40`, recorded as a lead

Two sites read a `+0x24` byte and extract one bit with identical code:

```
0x020219F4  ldrb r0, [r0, #0x24]        0x02021C4C  ldrb r0, [r0, #0x24]
0x020219F8  lsl  r0, r0, #0x19          0x02021C50  lsl  r0, r0, #0x19
0x020219FC  lsrs r0, r0, #0x1f          0x02021C54  lsrs r0, r0, #0x1f
0x02021A00  bne  #0x2021a14             0x02021C58  bne  #0x2021c6c
```

`lsl #N` then `lsr #31` isolates bit `31 - N`. With `N = 0x19` (25) that is **bit 6 = `0x40`**.

So *a* `+0x24` byte has a bit `0x40` that gets tested. Whether it is **the same** `+0x24` — the dirty byte
from iteration 129 — is **not established**: neither base is traced, and `+0x24` is conventional. Recorded
as a lead for the base-tracing task, not as a bit assignment.

## Predictions status

| Claim | Verdict |
|---|---|
| The other bits of `+0x24` can be named this wake | **REFUTED** *(my own task)* — 3 accesses near the setter, all inside it; 64 unattributed candidates |
| The lowest tagged allocation in arm9 is `0x0206ADB8` | **CONFIRMED_STATIC** — census, 62 arm9 sites sorted by address |
| `0x02000000`–`0x0206ADB7` contains zero tagged allocations | **CONFIRMED_STATIC** — same census pass |
| `memcpy`, `memset`, the list library and the iteration-128/129 helpers are all below the boundary | **CONFIRMED_STATIC** — every address checked against `0x0206ADB8` |
| `CommonEffect`'s class is `0x84` bytes | **CONFIRMED_STATIC** — `0x0206C590` and `0x0206CFD8`, both `0x84`, both `CommonEffect.h` |
| The facing chain is CommonEffect code | **PLAUSIBLE** — bracketed between two same-file same-size sites; a file boundary could still fall in the gap |
| `AL*` is a middleware namespace | **PLAUSIBLE** — three files, `Create`/`CreateImpFunc` entry points |
| Bit `0x40` of the dirty byte is tested at `0x020219F4`/`0x02021C4C` | **not claimed** — the bit extraction is certain, the object identity is not |
| Functions below `0x0206ADB8` can be named from allocation tags | **REFUTED** — by construction, there are none |

## Next angles, ranked

1. **Trace the bases of the 64 `+0x24` accesses in the library region.** This is the real bits task, and it
   now has a clear scope and a first candidate pair (`0x020219F4`, `0x02021C4C`).
2. **Read `0x0206C57C` and `0x0206CFC0`** (44 and 68 bytes) — `CreateImpFunc` and `CloneMain`, both
   allocating the `0x84` object. Small, tagged, and they should reveal the object's field layout.
3. **Check whether `0x0206CA8C` is inside `CommonEffect.cpp`** by looking for a string or assert reference
   that names the file, which would turn the PLAUSIBLE above into a confirmation.
4. **Name `Q`** (carried) — setter at vtable `+0x5C`, boolean at `+0x48`, lazy child at `+0x18`.
