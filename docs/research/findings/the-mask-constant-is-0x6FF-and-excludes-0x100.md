# Findings: the test is `record+0x34 & 0x6FF` — a constant, not another mask, and it excludes `0x100`

Loop-Atlas iteration 144. Static.

Iteration 143's top-ranked lead was that `0x0207F794`'s `tst r1, r0` might be a mask-against-mask layer
test, which "would explain the whole field in one stroke." **Refuted.** Two instructions settle it:

```
0x0207F78C  ldr r1, [r4, #0x34]     ; r1 = record+0x34
0x0207F790  ldr r0, [pc, #0x3b4]    ; r0 = a LITERAL
0x0207F794  tst r1, r0
```

`r0` comes from the literal pool at `0x0207FB4C`, not from a second object. The value is **`0x000006FF`**.

---

## 1. The actual test

```
proceed if (record+0x34 & 0x6FF) != 0
       or (record+0x38 & 0x800) != 0
otherwise skip to 0x0207F7C8
```

So `record+0x34` is checked against a **fixed constant**, and iteration 143's `0x800` bypass is an
alternative route past that one check. Not a layer-versus-layer interaction test at all.

## 2. `0x6FF` does not include `0x100` — and `0x100` is what the callers pass

`0x6FF` = `0b110_1111_1111` — bits 0–7, plus bit 9 (`0x200`) and bit 10 (`0x400`). **Bit 8 (`0x100`) is
clear.**

Iteration 141 found two ov6 callers passing `arg2 = 0x100`, which the installer stores whole into
`record+0x34`. So:

- `0x100 & 0x6FF == 0` → the mask test **fails** for those two objects.
- Their `arg3` was `0x8000` and `0x4000`, so `record+0x38 & 0x800 == 0` → the bypass **also fails**.

At construction-time values, both of those objects would take the skip branch. That is a pointed result: the
mask deliberately omits the one bit the two known callers set.

## 3. Why I am not claiming they are excluded

`record+0x34` has **another writer**: `0x0207EF1C` (`strne r0, [r2, #0x34]`, inside `0x0207E864`), which
turned up in iteration 138's companion scan. So the field is not write-once, and its value when
`0x0207F794` runs is **not statically determined**.

The honest statement is narrower than the tempting one:

- **Confirmed:** the constant is `0x6FF`, and it excludes `0x100`.
- **Confirmed:** at construction, the two known callers set `record+0x34 = 0x100`, which fails that test.
- **Not claimed:** that those objects are excluded at runtime — `0x0207EF1C` may change `+0x34` first.

This is the same discipline as iteration 141's "no observed live caller": describe the values and name the
untraced path, rather than concluding behaviour a second writer could overturn.

## 4. The bucket destination, and a false refutation I caught

The loop just above the test allocates bucket nodes:

```
0x0207F760  ldr r7, [r6, #0xd8]      ; take from the free list (iterations 68-69)
0x0207F764  add r0, r6, #0xd8
0x0207F76C  bl  #0x2037c24           ; unlink
0x0207F770  mov r1, r7
0x0207F774  add r0, r6, #0xb0        ; <-- the destination list
0x0207F778  str r5, [r7, #8]         ; node+0x8 = the walked element
0x0207F77C  bl  #0x2037b98           ; link
0x0207F780  ldr r5, [r5]             ; next element
0x0207F788  bne #0x207f6cc
```

So the bucket path is **free list `+0xD8` → the head at `+0xB0`**, with the node's payload pointing at the
element that earned it.

I drafted this as "a field the closed manager layout left unaccounted" and checked before publishing. **It is
already recorded**: the list-head audit lists `+0x0B0` as **bucket 17**. The heads sit at `+0x28 + N*8`, and
`0x28 + 17*8 = 0xB0` exactly.

That makes the finding sharper, not weaker: `add r0, r6, #0xb0` is a **constant**, so this code path always
deposits into **bucket 17** specifically — a hardcoded bucket index, not a computed one.

The element qualifies via `ldrhne r0, [r0, #0xc]` on `[r5+8]` — a halfword tested non-zero.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x0207F794` is a mask-against-mask layer test | **REFUTED** *(iteration 143's top lead, my own)* — `r0` is a literal |
| The test is `record+0x34 & 0x6FF` | **CONFIRMED_STATIC** — `0x0207F78C`, literal at `0x0207FB4C` = `0x000006FF` |
| `record+0x38` bit `0x800` is an OR-bypass for that test | **CONFIRMED_STATIC** — consistent with iteration 143's reading of `0x0207F7A0` |
| `0x6FF` includes bit `0x100` | **REFUTED** — bits 0–7, 9, 10 only |
| The two known callers' `record+0x34` fails the test | **CONFIRMED_STATIC** — `0x100 & 0x6FF == 0` |
| Their `0x800` bypass also fails | **CONFIRMED_STATIC** — `arg3` was `0x8000`/`0x4000` |
| Those objects are excluded at runtime | **not claimed** — `0x0207EF1C` also writes `+0x34` |
| `record+0x34` is write-once | **REFUTED** — a second writer exists at `0x0207EF1C` |
| Bucket nodes move from `+0xD8` to `+0xB0` | **CONFIRMED_STATIC** — `unlink(r6+0xD8)` then `link(r6+0xB0)` |
| `+0xB0` is a hardcoded bucket index | **CONFIRMED_STATIC** — `add r0, r6, #0xb0` is a constant, so always bucket 17 |
| `node+0x8` holds the element that earned the bucket | **CONFIRMED_STATIC** — `str r5, [r7, #8]` at `0x0207F778` |
| `+0xB0` is a field the manager layout left unaccounted | **REFUTED** *(my own draft, caught pre-publication)* — the list-head audit already records `+0x0B0` as bucket 17; heads are at `+0x28 + N*8` |

## Next angles, ranked

1. **Read `0x0207E864`** and find what value it writes to `record+0x34`. That is the only way to know whether
   the `0x6FF` test can ever pass for the known objects, and it decides section 3.
2. **Read `0x0207F7C8`** — the skip target. What is bypassed matters as much as the condition.
3. **Ask why bucket 17 is hardcoded here.** The head is reached by a constant `add`, so this path never
   varies its bucket — worth comparing against the other bucket-linking sites.
4. **Read `0x020801D4`** (carried) — the shared reject target that would settle `0x800`'s polarity.
