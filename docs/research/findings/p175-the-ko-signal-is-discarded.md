# P175 — The HP apply reports a KO and every caller throws it away

**Iteration 175. Static.** Goal: find the KO path and the owner's 1-HP floor. The entire DoT path was mapped and nothing on it clamps to 1, so the floor had to be somewhere else.

Turns out it isn't a clamp at all. The HP apply computes a KO signal and none of its eight callers ever read it.

## The apply returns "still alive" — nobody checks

`CONFIRMED_STATIC`. The worker `0x02078488` ends:

```
0x020784A0: strh   r1, [r0, #0x18]     ; store the new current HP
0x020784A4: ldrsh  r0, [r0, #0x18]
0x020784A8: cmp    r0, #0
0x020784AC: movne  r0, #1
0x020784B0: moveq  r0, #0              ; return 0 when HP has reached zero
0x020784B4: bx     lr
```

The return value is a "still non-zero" flag — a natural KO signal. Every drain and heal reaches it through the trampoline `0x020783CC` (`ldr r0,[r0,#0x56c]` then tail-jump). Scanning ov6 for ARM `BL`s to that trampoline turns up eight call sites. The instruction right after each one:

| call site | next instruction | what happens to `r0` |
|---|---|---|
| `0x02157DC0` | `b` (branch) | discarded |
| `0x021582C4` | `b` (branch) | discarded |
| `0x02158BC0` | `ldr r0,[sl,#0x1b4]` | overwritten |
| `0x02159274` | `mov r0,#0` | overwritten |
| `0x021592D0` | `mov r0,#1` | overwritten |
| `0x0215952C` | `mov r0,#1` | overwritten — **id 19's drain handler** |
| `0x02159668` | `mov r0,#1` | overwritten — **id 30's drain handler** |
| `0x0215A318` | `ldr r0,[r6,#0x1a8]` | overwritten |

None of the eight tests it. Each one either branches away or overwrites `r0` with its own value on the very next instruction. `0x02078488`'s only direct caller (`0x02078414`, arm9) also overwrites `r0` immediately.

`CONFIRMED_STATIC`: the HP apply is not the KO trigger. The signal is computed and dropped at every site in the ROM that could use it.

## What this settles and what it doesn't

This explains the owner's ground truth without needing a floor: a drain pushes HP down through this path and nothing on the path raises a KO, because the one value that would say "this hit zero" gets thrown away by every caller — both drain handlers included.

`not claimed` — and the gap matters: this shows the apply doesn't *signal* a KO. It does not show that HP reaching zero by drain is survivable. KO detection could be a separate per-frame poll of `char_struct+0x18` somewhere else entirely. If that poll exists, a drain would still kill and the floor must be real.

- **If KO detection is signal-driven**, this finding is the whole answer — DoT can't kill because it never signals.
- **If KO detection polls HP**, the floor is still unfound and the poll is where to look.

Both paths are live. The discriminator: does any code read `char_struct+0x18` and branch on zero outside the apply?

## A reading correction on "1 HP" that reframes the hunt

`PLAUSIBLE`, and it changes the search target. Displayed HP is raw / 64 — `HP-Struct-From-Disassembly.md` fixes the max at `0x4000` = 16384 = 256.0 displayed. So "1 HP" on-screen is most likely raw 64, not raw 1.

Every floor search so far looked for a clamp to `1`. If the floor is real and sits at one displayed unit, the constant to find is `0x40`. That's a cheap, specific next search. Worth noting: the owner's phrase is a display reading, so treating it as a raw value was my assumption, not their claim.

## Found along the way: the chr_b record accessor family

`CONFIRMED_STATIC`, corroborating the chrb-catalog work from a fresh angle. `0x02078514` and its siblings are per-character table lookups:

```
0x02078518: ldrb r3, [r0, #0x41]   ; chr_b index, from char_struct+0x41
0x0207851C: ldr  r2, [r2]          ; the 0x0214BD80 manager
0x02078520: mov  r0, #0x3c
0x02078524: ldr  r2, [r2, #0x40]   ; the record array base
0x02078528: mla  r0, r3, r0, r2    ; record = base + idx*0x3C
0x0207852C: add  r0, r0, r1, lsl #1
0x02078530: ldrh r0, [r0, #0x24]   ; halfword at record+0x24 + arg*2
```

Manager `0x0214BD80`, array at manager`+0x40`, stride `0x3C` — exactly the chrb-catalog map — reached here through `char_struct+0x41`, the `chr_b` index field named in the HP doc. Two independently-derived records landing on the same three constants.

## Queued by this wake

1. **Static:** search for a comparison against `0x40` on the drain and tick paths — the floor as one displayed unit rather than raw 1.
2. **Static:** find any read of `char_struct+0x18` that branches on zero outside the apply. That decides signal-driven vs. polled KO detection, and the answer settles whether a floor needs to exist at all.
3. **Owner (`jus-law`):** when poison leaves a character alive, does the bar show a sliver or does a number read exactly 1? A sliver is consistent with raw 0 and no floor; an exact 1 means a real clamp at raw 64.
