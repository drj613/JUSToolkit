# Findings: `0x0206CF28` is a four-instruction boolean getter, and the `ne`/`eq` split is an idiom

Loop-Atlas iteration 127. Static.

Iteration 125 found the two wall arms calling `0x0206CF28` and branching on **opposite** conditions, and
recorded it unresolved rather than guessing bug-or-design. Resolved now: **design.** The same mirrored pair
appears in at least three independent places, and every one of the 21 call sites treats the result as a
boolean.

---

## 1. The whole function

```
0x0206CF28  ldr  r0, [r0, #4]      ; arg0+0x04 -> object P
0x0206CF2C  ldr  r0, [r0, #0x64]   ; P+0x64    -> object Q
0x0206CF30  ldrb r0, [r0, #0x48]   ; Q+0x48    -> a byte
0x0206CF34  bx   lr
```

`size=16`, `callees=0`, **21 references from 7 caller functions**. A pure accessor:
`return *(u8*)(*(*(arg0 + 4) + 0x64) + 0x48)`.

Two hops and a byte load. Nothing in it can be asymmetric, so iteration 125's puzzle had to live in the
callers — which is where it lives.

## 2. Every caller compares against zero, and only zero

Checked the instructions following each `bl` site:

| call site | what follows |
|---|---|
| `0x0207DD84` | `cmp r0, #0` → `ne` arm (iteration 125's left wall) |
| `0x0207DDAC` | `cmp r0, #0` → `eq` arm (iteration 125's right wall) |
| `0x0207F410` | `cmp r0, #0`; `beq #0x207f434` |
| `0x0207F448` | `cmp r0, #0`; `bne #0x207f46c` |
| `0x020818F0` | `cmp r0, #0` |
| `0x02081944` | `cmp r0, #0`; `ldrne r0, [r1, #0x40]` |
| `0x02081C68` | `cmp r0, #0`; `orreq r0, r0, #0x20` |
| `0x0206CECC`, `0x0206CED8` | `cmp r4, r0` — compared against *another* object's byte |
| `0x0207E7C0`, `0x0208167C` | `mov r1, r0` — passed straight on as an argument |

**Not one site compares against `1`, `2`, or any other value.** Despite being a `ldrb` that could carry
`0`–`255`, the field is consumed purely as true/false.

## 3. The mirrored pair is a repeated idiom

`0x0207F410` and `0x0207F448` are the giveaway — two call sites in one function, taking opposite branches
on the same test, and both fetching their argument the same way:

```
0x0207F40C  ldr r0, [r1, #0x30]     0x0207F444  ldr r0, [r0, #0x30]
0x0207F410  bl  #0x206cf28          0x0207F448  bl  #0x206cf28
0x0207F414  cmp r0, #0              0x0207F44C  cmp r0, #0
0x0207F418  beq #0x207f434          0x0207F450  bne #0x207f46c
```

Identical shape to the walker's pair at `0x0207DD84`/`0x0207DDAC`, which also loaded `[reg+0x30]` first.
So `+0x30` on the caller's object is the standard route to this getter, and **handling the two boolean
values in adjacent mirrored arms is the module's normal way of writing this** — not a slip in one place.

For the walker specifically: the byte **selects which wall gets flagged.** Non-zero and past the left
bound sets `0x1000000`; zero and past the right bound sets `0x2000000`.

## 4. A companion consumer takes the byte as an argument

```
0x0207E7C0  bl  #0x206cf28
0x0207E7C4  ldr r2, [r4, #4]
0x0207E7C8  mov r1, r0            ; the byte becomes arg1
0x0207E7CC  ldr r0, [r2, #0x64]   ; arg0 = Q, the same object it was read from
0x0207E7D0  ldr r2, [r0]
0x0207E7D4  ldr r2, [r2, #0x5c]
0x0207E7D8  blx r2                ; virtual call, vtable slot +0x5C
```

`0x0208167C` is byte-for-byte the same sequence. So `Q` has a **vtable at its head with a slot at
`+0x5C`** taking `(Q, boolean)` — the byte is read off `Q` and handed back into one of `Q`'s own methods.

## 5. What I could not establish

I tried to bound the field's value set by finding its writers. `search-imm 0x48` returns **644 hits**, 18
of them `strb`, spread across arm9, ov6 and ov10. `+0x48` is another conventional offset — the same trap
recorded at iteration 69 for `+0x18`/`+0x20`. Attributing those writers needs each base traced
individually, which is its own task.

So "the field only ever holds `0` or `1`" is **not claimed**. What is established is weaker and still
useful: every *reader* treats it as a boolean.

## Predictions status

| Claim | Verdict |
|---|---|
| The `ne`/`eq` split is a bug in one arm | **REFUTED** — the same mirrored pair recurs at `0x0207F410`/`0x0207F448` |
| The asymmetry lives in the callee | **REFUTED** — the callee is four instructions with no branch |
| `0x0206CF28` is a pure getter, `*(u8*)(*(*(arg0+4)+0x64)+0x48)` | **CONFIRMED_STATIC** — `0x0206CF28`–`0x0206CF34` |
| Every reader treats the result as a boolean | **CONFIRMED_STATIC** — all 21 sites compare to `0`, pass it on, or compare two of them |
| `[caller+0x30]` is the standard argument route | **CONFIRMED_STATIC** — `0x0207DD80`, `0x0207F40C`, `0x0207F444` |
| `Q` has a vtable with a `(Q, boolean)` method at slot `+0x5C` | **CONFIRMED_STATIC** — `0x0207E7D0`–`0x0207E7D8`, duplicated at `0x0208167C` |
| The byte selects which wall the walker flags | **CONFIRMED_STATIC** — non-zero → `0x1000000`, zero → `0x2000000` |
| The field holds only `0` or `1` | **not claimed** — `+0x48` has 644 hits, no writer attributed |
| The byte is a side/team selector | **SPECULATIVE** — fits "two objects compared, act only if different" at `0x0206CEAC` and fits opposite walls, but nothing here names it |

## Next angles, ranked

1. **Name `Q`.** It is reached as `[[arg0+4]+0x64]`, has a vtable, a boolean at `+0x48`, and a method at
   vtable `+0x5C`. The size-and-shape route that identified ColObj applies.
2. **Read `0x0206CEAC`** — it fetches the byte from *two* objects and returns early when they match. That
   comparison is the strongest lead on what the flag means.
3. **Name `B+0x78`'s other bits** (carried) — two of 32 known.
4. **Name the four words of the `0x10` struct** (carried from iteration 126).
