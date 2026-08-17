# Findings: element `+0x0C`/`+0x10` are the owner's world position — refuting last wake's "scale pair"

Loop-Atlas iteration 139. Static.

Read the ColObj installer's argument setup before `0x0207CA08`. It identifies three element fields directly
and **refutes iteration 138's reading of the default value**. It also failed to resolve the ambiguity I
predicted it would.

---

## 1. The call, fully resolved

```
0x0207C9CC  ldr r0, [r8, #4]          ; r8 = the installer's arg1 -- call it the OWNER
0x0207C9D0  mov r1, r8                ; arg1 = the owner
0x0207C9D4  ldr ip, [r0, #0x50]       ; ip = [[owner+4]+0x50]
0x0207C9D8  add r2, sp, #0            ; arg2 = a two-word stack struct
0x0207C9DC  ldr r0, [ip, #0xc]
0x0207C9E0  str r0, [sp, #8]          ; the raw x
0x0207C9E4  asr r3, r0, #4
0x0207C9E8  ldr r0, [ip, #0x10]
0x0207C9EC  str r0, [sp, #0xc]        ; the raw y
0x0207C9F0  ldr ip, [ip, #0x14]
0x0207C9F4  asr r0, r0, #4
0x0207C9F8  str ip, [sp, #0x10]       ; the raw z
0x0207C9FC  str r3, [sp]              ; arg2[0] = x >> 4
0x0207CA00  str r0, [sp, #4]          ; arg2[1] = y >> 4
0x0207CA04  ldr r0, [sb, #0xf0]       ; arg0 = the element container
0x0207CA08  bl  #0x2082c34
```

`ip = [[owner+4]+0x50]`, then reads `+0x0C`, `+0x10`, `+0x14`.

**That is iteration 128/129's transform node.** Iteration 128 reached it as `[[S+0x04]+0x50]` and negated
`+0x0C`; iteration 129 proved `+0x0C`/`+0x10`/`+0x14` are a single three-word vector. This is a **third
independent sighting of the same chain**, and the first to read all three components at once.

## 2. Three element fields identified

Iteration 138 showed the allocator storing `arg1` at `+0x08` and `[arg2]`/`[arg2+4]` at `+0x0C`/`+0x10`.
Plugging in what the caller actually passes:

| element field | value |
|---|---|
| `+0x08` | the **owner object** (the installer's `arg1`) |
| `+0x0C` | the owner's transform **x**, `asr` 4 |
| `+0x10` | the owner's transform **y**, `asr` 4 |

From iteration 137, `+0x14`/`+0x18` are the previous frame's copies of those two. So the element carries
**a position and its previous position** — exactly what the frame-snapshot pass exists to maintain.

The `asr #4` is a signed shift, so these are signed coordinates scaled down by 16 from the transform node's
units.

## 3. REFUTED: my own "scale pair" reading

Iteration 138 recorded, as PLAUSIBLE:

> `0x10000` means `1.0` in 16.16, i.e. a scale pair

**That is wrong.** `+0x0C`/`+0x10` are clearly position components, copied from a transform node's vector.
The `0x10000` the allocator writes when `arg2` is NULL is a **default position**, not a unit scale.

The mistake was reasoning from the *value* (`0x10000` is a well-known fixed-point `1.0`) instead of waiting
for the *source*. One read of the caller settled it. A recognizable constant is a weaker signal than where
the data actually comes from.

I am not replacing it with a claim about which fixed-point format applies — the transform node's units are
not established, and `asr #4` only tells me the element's units are 16× coarser than the node's.

## 4. Prediction failed: the `ip`/`lr` ambiguity survives

Iteration 138 said this read would settle whether iteration 137's consumer variable `lr = [ip+8]` is the
element or something else. **It did not.**

What it shows is that `element+0x08` holds the **owner**, so `[element+0x08]` is a game object, not a
sub-record. That fits both readings:

- If the consumer's `ip` is a separate `0xC` link, `lr` is the element (iteration 137's reading).
- If `ip` **is** the element, `lr` is the owner — and the owner would then need its own `+0x0C`/`+0x34`.

The consumer reaches its list through `[[[arg0+4]+0x10]+0x10]`, which is **not** the `container+0x00` active
list this allocator links onto. Two different lists, so the two functions may not be walking the same
structure at all. Still **not claimed**.

## 5. An observation I cannot explain yet

`0x0207C9A8` calls `0x0201899C` with `r0 = sp+8` — and the words at `sp+8`, `sp+0xC`, `sp+0x10` are then
**overwritten** by the raw vector at `0x0207C9E0`, `0x0207C9EC`, `0x0207C9F8`. So either `0x0201899C`
initializes a three-word temporary that is immediately reassigned, or its output is genuinely discarded.
Recorded, not resolved.

The raw (unshifted) x/y/z at `sp+8`…`sp+0x10` are also never passed to `0x02082C34` — they must be for a
later call in the installer, past the part I read.

## Predictions status

| Claim | Verdict |
|---|---|
| `element+0x08` is the owner object | **CONFIRMED_STATIC** — `mov r1, r8` at `0x0207C9D0`, stored by `0x02082C6C` |
| `element+0x0C`/`+0x10` are the owner's transform x/y, `asr` 4 | **CONFIRMED_STATIC** — `0x0207C9DC`–`0x0207CA00` |
| The chain `[[owner+4]+0x50]` is iteration 128/129's transform node | **CONFIRMED_STATIC** — same expression, and `+0x0C`/`+0x10`/`+0x14` all read here |
| `0x10000` is `1.0` in 16.16, a scale pair | **REFUTED** *(iteration 138, my own)* — these are position components; it is a default position |
| This read settles iteration 137's `ip`/`lr` ambiguity | **REFUTED** *(my own prediction)* — compatible with both readings |
| The consumer walks the same list this allocator links onto | **REFUTED** — the consumer uses `[[[arg0+4]+0x10]+0x10]`, not `container+0x00` |
| The element's units are 16× coarser than the transform node's | **CONFIRMED_STATIC** — `asr #4`, signed |
| Which fixed-point format the transform node uses | **not claimed** — never established |
| `0x0201899C`'s output at `sp+8` is used | **REFUTED** — overwritten at `0x0207C9E0` before any read |

## Next angles, ranked

1. **Read the rest of `0x0207C988`** past `0x0207CA18`. The raw x/y/z at `sp+8`…`sp+0x10` are prepared but
   unused so far, so a later call consumes them — and that call is why they were saved unshifted.
2. **Search for `orr .., #0x100`** with companions `0x0C`/`0x14`/`0x34` (carried) — the snapshot suppressor,
   now known to belong to repositioning rather than creation.
3. **Read `0x0201899C`** — called with a three-word buffer whose contents are then discarded; either a
   constructor or genuinely dead code.
4. **Establish the transform node's fixed-point format**, which would give the element's coordinates real
   units. Iteration 125 proved 24.8 for the arena bounds, but in a different module.
