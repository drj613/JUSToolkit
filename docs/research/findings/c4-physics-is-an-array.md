# C4 — the "physics window" is an ARRAY, not individual velocity fields

Loop-Atlas iteration 27. Static.

## The reframe

Round 1 hunted for individual X/Y velocity offsets in `+0x6A`–`0xBA`. They don't exist in that form. The region is an array of 12-byte records, and that's why round 1 failed — not (just) tool gaps.

## Proof: three identical store groups

ov11 function `0x0217E4A0` writes three back-to-back records on base `r5`, same source registers (`r12`, `r2`, `r1`, `r3`, `r11`) every time, at **stride `0xC`**:

| record | absolute offsets | field layout |
|---|---|---|
| 0 @ `+0x58` | `+0x58`, `+0x5C`, `+0x5E`, `+0x60`, `+0x62` | `+0x0` word, `+0x4` half, `+0x6` half, `+0x8` half, `+0xA` byte |
| 1 @ `+0x64` | `+0x64`, `+0x68`, `+0x6A`, `+0x6C`, `+0x6E` | same |
| 2 @ `+0x70` | `+0x70`, `+0x74`, `+0x76`, `+0x78`, `+0x7A` | same |

Three copies of one layout at regular spacing is an array, not a coincidence.

## The GDB observations fit inside it

`Character-State-Struct.md` records a 2026-02-03 GDB session that saw "large deltas during knockback" at several offsets. Every one lands in this array:

| GDB offset | record | field |
|---|---|---|
| `+0x6A` | 1 | `+0x6` |
| `+0x6C` | 1 | `+0x8` |
| `+0x72` | 2 | `+0x2` |
| `+0x74` | 2 | `+0x4` |
| `+0x7A` | 2 | `+0xA` |
| `+0x7C` | **3** | `+0x0` |

That last one (`+0x7C`) implies at least **four** records. The GDB session read these as three 16-bit pairs at 8-byte spacing; they're actually different fields of different records at 12-byte spacing. The observations were real. The framing wasn't.

## The timer region is probably a second array

The "-5/-3 alternating decrement" the same session saw at `+0x98`, `+0xA0`, `+0xA8`, `+0xB0`, `+0xB8` has **stride 8** — that's an 8-byte-record array. The session guessed "32-bit values read as 16-bit?", which was the right instinct aimed at the wrong structure.

## Why round 1 failed

Round 1 searched for "the X/Y velocity field, gravity constant, decay term" as standalone offsets. If the region is a record array, no single velocity offset exists to find. That's a better explanation than tool limitations alone (though those are real — `search-imm` genuinely can't see register-indexed stores).

## A dead end, recorded for posterity

I tried proving the physics and HP offsets share one struct by finding a function that touches both on the same base register. Got **65 hits**, many on `r13` (stack pointer — locals, not a struct). Useless. For the fourth time this session, the problem is that `+0x18`, `+0x6C`, `+0x78` are such common offsets that co-occurrence proves nothing.

What actually worked was the opposite question: not "do these offsets co-occur?" but "do they have **structure**?" The stride-12 repetition is self-evidencing in a way co-occurrence never is.

## Confidence

**CONFIRMED_STATIC:** Offsets `+0x58`–`+0x7A` form three 12-byte records with the layout above, written identically by ov11 `0x0217E4A0`.

**PLAUSIBLE:** This is the same struct the GDB session observed. All six observed offsets land inside the array — strong evidence, but I haven't proven `r5` here points to that struct.

**Unknown: what the records mean.** The function writes the same values to all three, so it's initialising or broadcasting — that reveals layout, not semantics. Candidates: per-limb hitbox state, a short position/velocity history ring, or per-hit records. A 12-byte record holding `word, half, half, half, byte` would fit `{pointer-or-id, x, y, misc, flags}`.

I am **not** naming them velocity fields. That guess produced four demoted claims in round 1.

## Next steps

1. **Empirical (cheap for the harness session):** dump the struct across frames during a jump and diff. Physics fields are easy to spot by observation and hard to find by static search — round 1 spent a whole campaign proving the latter.
2. Find the array's true length and who reads it (versus this initialiser).
3. Confirm whether `+0x98`–`0xBA` really is an 8-byte-record array using the same method.
