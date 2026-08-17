# Findings: vtable diff names slot `+0x18` as `Clone`; the hierarchy is four deep

Loop-Atlas iteration 132. Static.

Dumped both vtables from iteration 131 — parent `0x0209C30C` and derived `0x0209E114` — and diffed them.

**Exactly 3 of 44 slots differ.** One is `+0x18`, whose derived value is `0x0206CFC0` — the function
already tagged `CloneMain`. So **slot `+0x18` is the virtual clone method**, named without reading a single
instruction of its body.

This also surfaces a conflict with iteration 129, recorded here but not resolved.

---

## 1. The diff

44 slots read from each vtable. Every word is a plausible arm9 code pointer. Only three differ:

| slot | parent `0x0209C30C` | derived `0x0209E114` | derived function |
|---|---|---|---|
| `+0x00` | `0x02015E54` | `0x0206D010` | 20 bytes |
| `+0x04` | `0x02015E88` | `0x0206CFA4` | 28 bytes |
| `+0x18` | `0x0204B0C8` | `0x0206CFC0` | **`CloneMain`** — 68 bytes, `CommonEffect.h` |

The other 41 slots are byte-identical. That is textbook vtable inheritance: the derived class copies the
base's table and overwrites only the methods it overrides.

Two slots hold **odd** addresses — `+0x08` = `0x020102D1` and `+0x10` = `0x020119E5`. An odd function
pointer means **Thumb code**, targeting `0x020102D0` and `0x020119E4`. Both classes inherit them unchanged.

## 2. Why `+0x18 = Clone` is solid

The derived slot's value is the same address the census already tagged as `CloneMain` in `CommonEffect.h`
(iteration 131). A class that overrides slot `+0x18` with its own clone function tells us what that slot
means. The parent's entry `0x0204B0C8` is a 36-byte function with 0 callers and 2 callees — consistent
with a base-class clone, though I did not read it.

This is the cheapest naming route found so far: **diff a derived vtable against its parent, then look up
the differing entries in the census.** No disassembly of the method body required.

## 3. The hierarchy is four levels, not three

Iteration 131 traced the copy chain up three levels. `0x020240A4` calls one more:

```
0x02021960   496 bytes, 9 callers   <- base copy constructor
  0x020240A4   528 bytes, 5 callers   (calls 0x02021960 at 0x020240B0)
    0x02015DD4    56 bytes            (vtable 0x0209C30C, byte +0x78, counter++)
      0x0206CFC0  68 bytes CloneMain  (vtable 0x0209E114, halfword +0x80)
```

Each level sets its own vtable at `+0x00` right after calling its base — `0x020240BC` does
`str r1, [r7]` just after the `bl` at `0x020240B0`, the same pattern as the two levels above.

`0x020240A4` also builds a **subobject at `+0x6C`**: `add r0, r7, #0x6c` then `bl #0x201cf08`, followed
by `add r0, r7, #0x6c` with `mov r1, #4` then `bl #0x2010970`. So `+0x6C` is an embedded member with its
own constructor, initialised with a count or kind of `4`.

## 4. Iteration 130's `bit 0x40` lead connects here

Iteration 130 found two sites isolating bit `0x40` of a `+0x24` byte and recorded it as a lead because
neither containing function was traced. One resolves inside this hierarchy:

| site | containing function | size |
|---|---|---|
| `0x020219F4` | **`0x02021960`** — the base copy constructor above | 496 |
| `0x02021C4C` | `0x02021BB8` | 496 |

`0x020219F4` sits inside the base copy constructor of this class family. So the `+0x24` byte with bit
`0x40` belongs to **the base class of CommonEffect's hierarchy** — a real narrowing of iteration 130's
lead, though still not proof that it is the *same* `+0x24` as iteration 129's dirty byte.

`0x02021BB8` is also **496 bytes** — the same size as `0x02021960`, with 1 caller instead of 9. Two
same-sized functions with the same shape in one class are most likely the copy constructor and the
assignment operator. **PLAUSIBLE**, not read.

## 5. A conflict with iteration 129, recorded not resolved

Iteration 129 described `0x02024C3C` as calling a **notify** through vtable `+0x18` after marking a dirty
flag. In *this* vtable pair, `+0x18` is `Clone`.

Both cannot be true of one vtable. The honest position:

- The object in iteration 129 has a vector at `+0x0C`/`+0x10`/`+0x14` and a dirty byte at `+0x24`; the
  `0x84` object here has known members at `+0x78` and `+0x80`. Those do not conflict, so they *could* be
  the same class with the earlier fields inherited from a base.
- **"Notify" was my label, not an observation.** I inferred it from call position and never read the
  target. That inference is the weaker of the two claims.

Either these are two different vtables, or iteration 129's slot name is wrong. Resolving it means reading
`0x0204B0C8` (the parent's `+0x18`) and checking whether iteration 129's object reaches this vtable.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x0209C30C` and `0x0209E114` are vtables | **CONFIRMED_STATIC** — 44 plausible arm9 code pointers each |
| The derived vtable differs from the parent in exactly 3 of 44 slots | **CONFIRMED_STATIC** — `+0x00`, `+0x04`, `+0x18` |
| Slot `+0x18` is the virtual clone method | **CONFIRMED_STATIC** — the derived entry is `0x0206CFC0`, tagged `CloneMain` in `CommonEffect.h` |
| Two inherited slots point at Thumb code | **CONFIRMED_STATIC** — `0x020102D1` at `+0x08`, `0x020119E5` at `+0x10`, both odd |
| The hierarchy is three levels deep | **REFUTED** *(iteration 131)* — `0x020240A4` calls `0x02021960`, making four |
| `0x020240A4` builds a subobject at `+0x6C` | **CONFIRMED_STATIC** — `add r0, r7, #0x6c` before `0x0201CF08` and `0x02010970` |
| Iteration 130's `0x020219F4` is inside this hierarchy | **CONFIRMED_STATIC** — it lies within `0x02021960`, the base copy constructor |
| The `+0x24` bit-`0x40` byte is iteration 129's dirty byte | **not claimed** — same offset, same family, but not the same object proven |
| Iteration 129's vtable `+0x18` is a notify | **in conflict** — `+0x18` is `Clone` here; "notify" was an inference from position, never read |
| `0x02021BB8` is the assignment operator | **PLAUSIBLE** — same 496-byte size and shape as the copy constructor, 1 caller |
| `0x02021960` is the top of the hierarchy | **not claimed** — its callees were not examined |

## Next angles, ranked

1. **Read `0x0204B0C8`** (36 bytes, the parent's `+0x18`). If it allocates and copies, `+0x18 = Clone` is
   confirmed at both levels and iteration 129's "notify" label falls — the cleanest way to settle
   section 5.
2. **Read `0x0206D010` and `0x0206CFA4`** (20 and 28 bytes) — the other two overrides, so slots `+0x00`
   and `+0x04` get names too. Small, and they complete CommonEffect's override set.
3. **Dump the base vtables** set by `0x02021960` and `0x020240A4`, and diff the whole chain. A four-level
   diff would name every slot any level overrides.
4. **Trace the remaining `+0x24` sites** (carried) — now with `0x02021960` as a known-relevant base class.
