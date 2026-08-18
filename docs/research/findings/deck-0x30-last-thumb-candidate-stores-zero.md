# The deck's last Thumb-store candidate writes zero — and the Thumb disassembler misread `cmp` as `mov`

Iteration 150. Static only.

Iteration 149 narrowed the "deck add-entry never succeeds" claim down to one surviving
game-code Thumb-store candidate for `deck+0x30`: **`0x0206BB44`**, inside Thumb function
**`0x0206BAC8`** (`arm9`, 160 bytes). This pass reads that instruction. The claim
survives — and for a better reason than expected — but getting there uncovered a silent
bug in `thumb_disasm.py`.

## The candidate stores a constant zero

```
0x0206BB42: 2000  mov r0, #0x0
0x0206BB44: 6328  str r0, [r5, #0x30]
```

Halfword `0x6328` decodes as `str`, base `r5`, offset `0x30` — `imm5 = 12`, `12 << 2` =
`48` = `0x30`. The instruction right before it loads the constant `0`, so the stored value
is **zero**.

**This closes the question without needing to resolve `r5` at all.** The deck claim says
`deck+0x30` (the ID table base) stays `0`, which makes the bounds check reject every id
so add-entry always returns `0x10000000`. A store of zero can't falsify that — you'd need
a store of a *non-zero* table base. So regardless of whether `r5` is the deck,
`0x0206BB44` isn't the writer that would break the result.

That's a stronger closure than tracing the base register would give, because it holds no
matter what `r5` turns out to be.

## What the function is

`r5` is the function's first argument: `0x0206BACC` is `add r5, r0, #0`. The function is
plainly a teardown. Across its 160 bytes it zeroes six fields on `r5` — `+0x20`, `+0x30`,
`+0x48`, `+0x4C`, `+0x50`, `+0x60` — makes three reads of `+0x30` (`0x0206BB12`,
`0x0206BB34`, `0x0206BB3A`), dispatches through two vtable slots, and calls the deleting
destructor `0x0201B244`. Nulling a pointer field on the way out is exactly what a store of
zero to `+0x30` should look like.

## `r5`'s identity — not claimed

Module attribution doesn't settle it, and I want to be explicit that I tried and failed
rather than let it look resolved. Two of the function's five callees, `0x021B3BC8` and
`0x021B70F8`, land in `ov12`'s range and have no `functions.json` record (unresolved
cross-overlay edges). `Overlay-Map.md` has `ov12` as **shared in-game support, resident
on both battle and deck screens (100% deck, 59.6% battle)** — so calling into `ov12`
neither implicates nor exonerates the deck. The deck module proper lives at `0x02076xxx`,
nowhere in this function's call set, which is suggestive and nothing more.

It doesn't matter for the claim, per the argument above. Recorded as open because it's
the kind of loose end that gets quietly assumed later.

## The disassembler was turning comparisons into assignments

While reading this function, `thumb_disasm.py` printed `mov r0, #0x0` at `0x0206BB48`,
immediately followed by `beq`. A `beq` needs flags set, and `mov` doesn't set them. That
mismatch was the tell.

Root cause, `thumb_disasm.py`:

```python
if top == 0b0010:                       # top = h >> 12
    return f'mov {R[(h>>8)&7]}, #{h&0xff:#x}', 1
```

Format 3 is selected by bits **12–11**, not bit 12 alone. `top == 0b0010` matches the
whole `0x2000`–`0x2FFF` range, so **every `cmp Rd,#imm` (`0x2800`–`0x2FFF`) decoded as
`mov Rd,#imm`.** Two later branches were clearly meant to handle `cmp` and were both
unreachable — one tested `top == 0b0010 | 1`, which is `0b0011`, already returned by the
add/sub case above it; the other tested `(h >> 11) == 0b00101`, which the broken `mov`
case had already consumed.

Fixed by narrowing the `mov` case to `(h >> 11) == 0b00100` and letting the existing
`cmp` branch match. Verified across six encodings, now asserted in `--selftest`:

| halfword | before | after |
|---|---|---|
| `0x2000` | `mov r0, #0x0` | `mov r0, #0x0` |
| `0x2800` | **`mov r0, #0x0`** | `cmp r0, #0x0` |
| `0x28ff` | **`mov r0, #0xff`** | `cmp r0, #0xff` |
| `0x2101` | `mov r1, #0x1` | `mov r1, #0x1` |
| `0x3001` | `add r0, #0x1` | `add r0, #0x1` |
| `0x3801` | `sub r0, #0x1` | `sub r0, #0x1` |

**Why this one is nasty.** It's silent and it corrupts control-flow reasoning
specifically. A `cmp`+`beq` pair that reads as `mov`+`beq` looks like a branch testing a
stale flag from further back — which invites exactly the wrong conclusion about what
condition a branch depends on. Any Thumb reading done with this tool before iteration
150 — including the `ov6` Thumb work from iterations 95–96 — should be re-read if a
conditional branch carried the argument.

This did **not** affect the result above: `0x2000` has bit 11 clear and was always
decoded correctly as `mov`, and the store `0x6328` was never in doubt.

## Convergent verification, working as intended

Three decodes of `0x0206BB44`, and the disagreement is what found the bug:

| method | verdict on `0x0206BB44` | verdict on `0x2800` |
|---|---|---|
| hand decode of raw bytes | `str r0,[r5,#0x30]` | `cmp r0,#0` |
| `thumb_disasm.py` (project tool) | `str r0,[r5,#0x30]` | **`mov r0,#0x0`** — wrong |
| independent decoder, raw hex only | `str r0,[r5,#0x30]`, preceded by `movs r0,#0` | `cmp r0,#0` |

All three agree on the load-bearing instruction, so the deck conclusion is solid. Two of
three disagree with the project tool on `0x2800`, which pinpointed the defect. The charter
rule says disagreement tells you which side is wrong; here it did.

The independent decoder was given raw hex with no addresses beyond the start, no hint of
the expected answer, and no access to project files. It also volunteered a correct caveat
nobody asked for: `0x4788` (`blx r1`, register form) is ARMv5TE, not strict ARMv4T — true,
and correct for the ARM946E-S.

## One discrepancy, carried

The independent decode puts the `BL` pair at `0x0206BB36`/`0x0206BB38` at target
**`0x02020916`**. `functions.json` lists `0x02020934` in this function's callee set. Those
differ by `0x1E`. Hand-checking the encoding agrees with `0x02020916`: `hi = 0xF7B4`,
`lo = 0xFEEE`, giving a sign-extended displacement of `-0x4B224` from
`0x0206BB36 + 4`, which lands on `0x02020916`. So `functions.json`'s callee entry looks
wrong or refers to a different site. Queued rather than resolved here — it's a database
question, not a deck question.

## Not claimed

That `deck+0x30` has no Thumb writer anywhere. What is claimed is narrower: the one
game-code candidate iteration 149 surfaced stores zero and therefore cannot falsify the
add-entry result. Thumb register-offset stores (`str rD,[rN,rM]`) and split `add`+`str`
bases remain outside every sweep, and `r5`'s identity is unresolved.
