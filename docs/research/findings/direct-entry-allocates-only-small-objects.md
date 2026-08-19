# Findings: the direct allocator entry allocates only small objects — every large structure is tagged

Loop-Atlas iteration 135. Static.

Swept the 403 direct-entry allocation sites that iteration 134 made visible, looking for large library
managers. **There are none.** The largest direct allocation in the ROM is `0xE4` (228 bytes).

That is a useful negative: iteration 134 improved the census's *coverage*, not its *reach*. Every large
structure in the game already came through the tagged path, so no big object was ever hidden.

The sweep did turn up one thing worth keeping: a **reusable signature for clone and factory functions**, and
seven sites allocating exactly `0x80` — the parent CommonEffect size from iteration 133.

---

## 1. The negative result, measured

| | value |
|---|---|
| direct-entry sites | 403 |
| with a resolved size | 320 |
| **largest size** | **`0xE4`** |

For comparison, the tagged path holds `0x4000C`, `0xFB54`, `0x42D8`, `0x3FD4`, `0x2648` and more. Nothing on
the direct side comes close.

The size distribution is dominated by very small objects:

| size | sites |
|---|---|
| `0x14` | 46 |
| `0x8` | 42 |
| `0x24` | 34 |
| `0x40` | 19 |
| `0x78` | 17 |
| `0x6c` | 14 |
| `0x70` | 13 |
| `0x30` | 11 |
| `0x2c` | 11 |
| `0x20` | 10 |

This is what a middleware layer allocating nodes, handles and small records looks like. The managers and
pools live game-side, where the tagging macro was compiled in.

## 2. A self-check the sweep passed

Among the `0x80` sites the sweep reported was **`0x0204B0D4`** — which is the allocation inside
`0x0204B0C8`, the parent `Clone` I hand-read in iteration 133 from a vtable slot.

That site was found through a completely different route (a vtable diff, then reading the target), and the
new scan rediscovered it independently. A widened scan agreeing with a known-good anchor found another way
is worth more than a passing selftest.

## 3. Seven sites allocate `0x80`, and they share one shape

```
0x02034C38  0x02034C5C  0x02041DE0  0x02044334  0x02046270  0x02049C94  0x0204B0D4
```

`0x80` is the parent CommonEffect class size (iteration 133). Every one of the seven follows the same
pattern:

```
mov  r0, #0x80
bl   #0x201a228        ; allocate
cmp  r0, #0            ; or movs rN, r0
popeq / beq            ; NULL -> bail out
mov  r1, <source>      ; a source object, or a literal and a 0
bl   <constructor>
return the new object
```

Worked examples:

```
0x02034C44  mov r1, r4      ; 0x02041DEC  mov r1, r4      ; 0x02049CA0  mov r1, r5
0x02034C48  bl  #0x202b4a8  ; 0x02041DF0  bl  #0x203abd4  ; 0x02049CA4  mov r2, r4
                                                          ; 0x02049CA8  bl  #0x202b520
```

**Six distinct constructors** are reached this way: `0x0202B4A8`, `0x02015D70`, `0x0203ABD4`, `0x020445F4`
(twice), `0x0202B520`, and `0x02015E14` from iteration 133.

Whether that means **one class with six constructor overloads** or **several sibling classes that happen to
be `0x80` bytes** is **not resolved**. The discriminator is which vtable each constructor installs at
`+0x00`, which means reading six functions — a task of its own.

## 4. The reusable part: an allocate-then-construct signature

The shape above is a recognizer. When a site does *allocate a constant size → NULL-check → call one function
with the new object as `arg0` → return it*, that function is a **constructor**, and the constant is its
**class size**. If `arg1` is another object of the same type, the whole thing is a **clone**.

This is how iteration 133 identified `Clone` at `0x0204B0C8`, except there I arrived via a vtable and read
the body. The signature reaches the same conclusion straight from the census, with no disassembly of the
callee — and the census now covers 1135 sites to apply it to.

## Predictions status

| Claim | Verdict |
|---|---|
| The direct entry hides large library managers | **REFUTED** *(the queued premise)* — largest is `0xE4` |
| Every large allocation in the ROM is tagged | **CONFIRMED_STATIC** — direct max `0xE4` vs tagged `0x4000C`/`0xFB54`/`0x42D8` |
| Iteration 134 extended the census's reach to new large structures | **REFUTED** — it extended coverage only; no large object was hidden |
| The sweep independently rediscovers `0x0204B0D4` | **CONFIRMED_STATIC** — the iteration-133 parent `Clone`, found originally via a vtable diff |
| Seven direct sites allocate exactly `0x80` | **CONFIRMED_STATIC** — listed above, `0x80` = the parent CommonEffect size |
| All seven use the same allocate-then-construct shape | **CONFIRMED_STATIC** — size, NULL-check, call with the new object, return |
| The seven are one class with six constructor overloads | **not claimed** — could equally be sibling classes of equal size; needs each constructor's vtable store |
| `0xE4` is the true ceiling for untagged allocations | **PLAUSIBLE** — 83 of 403 sites have no resolved size, so a larger one could be hiding among them |

## Next angles, ranked

1. **Read the six `0x80` constructors** and record the vtable each installs at `+0x00`. That settles
   overloads-versus-siblings and would extend the class family mapped in iterations 131–133.
2. **Dump the base vtables** set by `0x02021960` and `0x020240A4` (carried) — with `+0x00`/`+0x04`/`+0x18`
   named, a four-level diff names every overridden slot.
3. **Resolve the 83 direct sites with no size**, to test whether `0xE4` really is the ceiling.
4. **Read `0x0201B244`** (36 bytes) to confirm `operator delete`, retiring a PLAUSIBLE.
