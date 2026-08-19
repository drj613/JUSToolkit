# Loop-Atlas 213 — damage flag word is at +0x44; ability 10 sets bit 5

Claims tracked in beads:
[`jus-gate-word-is-r8-0x44-fnz`], [`jus-bit5-is-ability-10-rxl`],
[`jus-peek-plus-0x44-and-flag-writer-uvp`].

## The +0x40 correction, reached twice on the same wake

The gates test **`[r8+0x44]`**, not `[r8+0x40]`
[`jus-gate-word-is-r8-0x44-fnz`]. The runtime loop published that correction, with
the same six gates and the same sixteen-byte class table, while I was deriving it
independently. Both readings are in the record; theirs is the bead that holds the
state. My own duplicate bead is closed.

That is worth noting rather than hiding: two loops working the same listing found the
same nibble error within an hour of each other, and neither knew the other was on it.
It also means the correction is not resting on one reader.

```
0x020824DC: ldr r2, [r8, #0x40]   ; 402098e5 -- nature bypass (bit 30) and
                                  ;   nature-advantage flag (bit 22)
0x02082574: ldr r2, [r8, #0x44]   ; 442098e5 -- THIS is what the gates test
```

`r2` isn't written again between `0x02082574` and the last gate at `0x02082650`.

Cold-asked with just the listing, `codex exec` independently reported all six
adjustments as gating on "`[r8+0x44]`, loaded at `0x02082574`" — a third reader, and
it wasn't told what to expect.

**The new part of this entry starts at "Who sets the bits".** The gate structure was
already corrected; who fills the gate word was not.

## Six gates, three of which add

| address | mask | bit | class byte | effect on r0 |
|---|---|---|---|---|
| `0x020825A8` | `0x4000` | 14 | — (element cond.) | **add** 25% of base |
| `0x020825DC` | `0x40` | 6 | — (element cond.) | subtract 25% |
| `0x02082608` | `0x1000` | 12 | `== 1` | **add** 25% |
| `0x02082624` | `0x2000` | 13 | `== 2` | **add** 25% |
| `0x0208264C` | `0x10` | 4 | `== 1` | subtract 25% |
| `0x02082674` | `0x20` | 5 | `== 2` | subtract 25% |

"Gate 1 fires on class 1 unconditionally" was wrong — `0x02082634` sits behind `tst r2, #0x10` at `0x02082628`. Nothing here is unconditional.

The element condition on bits 6 and 14 fires if `[[sl+0x10]+0]` is 4 or 5; otherwise it needs `[sl+0x14] & 0xF0`. Codex flagged the `cmp`/`cmpne` pair as easy to misread — the 4-or-5 case *bypasses* the second test, it doesn't add to it.

## The class-table index is an element byte, not the nature category

The handoff called `r1` at `0x02082634` load-bearing and unpinned, guessing a 2-bit nature category. Wrong on both counts:

```
0x02082570: ldr   r3, [sl, #0x10]
0x02082580: ldrsb r1, [r3, #0xe]    ; de10d3e1
0x020825E0: cmp r1, #0    / blt 0x2082678
0x020825E8: cmp r1, #0xf  / bgt 0x2082678
```

`r1 = ldrsb [element + 0xE]`, range-checked to `0..15` before any gate runs. The table at `0x02092E68` is 16 bytes wide, not 8:

| index | 0 | 1 | 2–11 | 12–15 |
|---|---|---|---|---|
| value | 1 | 1 | 2 | **0** |

From `arm9.bin`: `01 01 02 02 02 02 02 02 02 02 02 02 00 00 00 00`.
Element bytes 12–15 match neither `== 1` nor `== 2` — immune to both sides. The code's bound and the data's shape agree on the width, which is two representations confirming one fact.

## Who sets the bits

`arm9 0x02083BE0`, sixteen instructions, unnamed:

```
f(r0 = manager, r1 = mask index, r2 = variant)
    target = [r0+0x10]
    r2 != 0 :  [target+0x44] |=  tbl[r2-1][r1]
    r2 == 0 :  [target+0x44] &= ~(tbl[0][r1] | tbl[1][r1])

tbl[0] @ 0x02092E78 = 0x10 0x20 0x40 0x80 0x100 0x200        bits 4..9   (subtract)
tbl[1] @ 0x02092E90 = 0x1000 0x2000 0x4000 0x8000 0x10000 0x20000  bits 12..17 (add)
```

Stride `0x18` — six words per variant. The clear path ORs both tables together, which is why there are exactly two variants.

**Bit 5 is set by calling `0x02083BE0` with `r1 = 1`, `r2 = 1`.** That answers the question the campaign has been stuck on [`jus-bit5-is-ability-10-rxl`].

This is the pattern the predecessor warned about: the mask goes to a helper via `bl`, not directly to a `str`. Fourteen iterations were lost sweeping for stores. The sweep that found it searched for read-modify-write of `+0x44` inside battle code only (arm9 `0x0207xxxx`–`0x0209xxxx` plus ov6) — nineteen sites instead of 234.

## Who calls it, and with what

Two call sites in ov6, both inside `0x02157114`:

- `0x021572A8` — `r6 = 0..5`, `r2 = 0`. Clears all six indices. The reset.
- `0x021572F4` — driven by a 12 × 3-byte table at ov6 `0x021710BC`:

```
for r7 in 0..11:
    b = tbl[r7]                                  ; 3 bytes
    if bit (b[0] & 0x1f) of [battleObj + 0x128 + (b[0]>>5)*4]:
        f([battleObj + 0x1a8], r1 = b[1], r2 = b[2])
```

`battleObj+0x128` is the cached ability bitset. Raw table bytes:

```
09 00 01  0B 00 02  0A 01 01  0C 01 02  0D 02 01  15 02 02
10 04 01  11 04 02  12 05 01  13 05 02  17 03 01  18 03 02
```

| mask idx | subtract bit | ability id | add bit | ability id |
|---|---|---|---|---|
| 0 | 4 | **9** | 12 | 11 |
| 1 | **5** | **10** | 13 | 12 |
| 2 | 6 | 13 | 14 | 21 |
| 3 | 7 | 23 | 15 | 24 |
| 4 | 8 | 16 | 16 | 17 |
| 5 | 9 | 18 | 17 | 19 |

Six down/up couples. The damage routine reads indices 0, 1, and 2; bits 7–9 and 15–17 are consumed somewhere I haven't looked.

## Why poking the bitset did nothing

This rescues the runtime loop's negative result rather than contradicting it [`jus-w66`]. The bitset is read **once** in `0x02157114` and converted to flag bits. The damage routine never touches the bitset — it reads the flags. Poking the bitset after conversion changes nothing, which is exactly what was measured in both directions.

This also reframes `defence-candidates-ruled-out.md`, which attributes a flat `−2.0` to ability `0x09`. Ability 9 does reduce damage — by 25% of base, against class-1 elements only, through bit 4 of `+0x44` [`jus-reduction-is-quarter-multiplier-xk1`].

## What I'm not claiming

**Which combatant owns the flag word.** The helper writes `[[battleObj+0x1a8]+0x10] + 0x44`; the damage routine reads `[arg0+0xc] + 0x44`. Same offset, same mask semantics, but nobody has shown the two derivation paths land on the same object. The predecessor declined twice to guess an object's identity and was right both times, so this stays unnamed until runtime confirms [`jus-peek-plus-0x44-and-flag-writer-uvp`].

Also unread: what writes the element byte at `elem+0xE`, when `0x02157114` runs relative to a hit, and whether `[r8+0x44]` on the existing 6.000 capture actually has bit 4 set. That last check is cheap and could kill this entire entry — it's card 1 of the request.

## Provenance

Static only. `jus.nds` (`AJUJ`), `jus_files/arm9/arm9.bin` and `jus_files/arm9/overlays/arm9_ov06.bin`, listings in `jus_files/analysis/disasm/`. Table bytes read from the binaries at `addr − load_base`, not from the listing, so mask values and disassembly are independent reads. No emulator, no GDB. Independent second read: `codex exec`, cold, questions asked before any conclusion was stated.

## Which side is `r8`? The structure, not the label

The runtime loop asked for this specifically, so it is here rather than only in
[`jus-gate-word-is-r8-0x44-fnz`]'s comments.

At the call site `0x02081280`: `arg0 = r5`, `arg1 = r6`, `arg2` is one bit from
`[sl+0x14d]`, `arg3 = sp+0x4c` (the out-param). Both objects come from one collision
record — with `x = [sp+0x2c]+8`, `r5 = [[x+0x08]+0x1C]` and `r6 = [[x+0x0C]+0x1C]`.
The two participants live at `+0x08` and `+0x0C` of that record.

**`arg1` owns the attack**, for two reasons that don't share a source:

1. The class index is `ldrsb [[arg1+0x10]+0x0E]`, and at `0x02081258` — six
   instructions before the call — the caller reads the same byte off the same object:
   `ldr r0,[r6,#0x10]; ldrsb r0,[r0,#0x0e]`. The base damage byte is `elem+0x10+4` on
   that same element. The move's data hangs off `arg1`.
2. The nature factors at `+0x184`/`+0x186` and the 2-bit nature field at `+0x175` all
   hang off `r4`, which is walked from `[arg1+0x0C]`.

So `r8` is the participant that is *not* supplying the move, and `[r8+0x44]` is a mask
on that side. Bits 4/5/6 reduce incoming damage and bits 12/13/14 raise it, which is
the right shape for it, and it matches the ability chain above, where the flags land on
the ability holder.

I am not writing "defender". "The side not supplying the move" is what the code says;
attacker and defender are runtime attributions, and the last time someone guessed which
side a register pointed at it changed the meaning of the nature factors entirely. The
`0x0208257C` capture settles it at no extra cost: `r4 == 0x0220FC3C` (the scratch from
the earlier measurement) with `r8 != it` names both sides in one read, and `r8 == it`
refutes this section.

## How much the agreement is worth

Three readers landed on `+0x44`: the runtime loop, me, and codex. That is less than it
looks, and the runtime loop said so first. All three read the same disassembly listing.
Independence of *reader* is not independence of *representation*, and this doc argues two
sections above that cross-representation agreement is the strong signal — so the same
standard applies here.

What is genuinely two-representation in this entry is narrower: the six `tst` masks in the
code versus the two mask tables in ROM data at `0x02092E78`/`0x02092E90`, whose first three
entries are those masks in index order; and the `0..15` bound in the code versus the
sixteen-byte shape of the table at `0x02092E68`. Those two hold up. The offset itself rests
on one representation until the live capture lands, and `state:static-confirmed` on
[`jus-gate-word-is-r8-0x44-fnz`] should be read as "the disassembly says this clearly",
not as "measured".
