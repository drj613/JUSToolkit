# Loop-Atlas 227 — the kind-2 abilities are stat modifiers, and three are stubs

Builds on [`jus-second-ability-source-0x558-5rp`]. Claim bead: [`jus-kind2-abilities-are-stat-modifiers-bdq`].

Eight handler addresses filed three wakes ago, never opened until now. 36 instructions total.

## The eight kind-2 abilities

Handler index from `ability.bin` byte 1; parameter from byte 2, signed.

| id | handler | effect |
|---|---|---|
| 49, 50, 51 | `0x0207793C` | **Stub** — `mov r0,#0 ; bx lr`. Returns failure, does nothing. |
| 52 | `0x02077974` | max HP (`+0x16`) += byte2 × 64, clamped to `0x4000`, then current HP (`+0x18`) = max. byte2 = +8, so **+8,000 displayed HP and a full heal**. |
| 53 | `0x020779A4` | `char+0x5CC` += 1, clamped to `0x10` |
| 54 | `0x02077944` | `char+0x4A` = +1 |
| 55 | `0x02077954` | `char+0x4B` = +3 |
| 56 | `0x02077964` | `char+0x4C` = −3 |

## The loader zeros the modifier bytes first

```
0x0207778C  strb sb, [r6, #0x4a]
0x02077790  strb sb, [r6, #0x4b]
0x02077794  strb sb, [r6, #0x4c]
0x02077798  strb sb, [r6, #0x1a]     the ability count, already known
```

`+0x4A`/`+0x4B`/`+0x4C` are a triple of **signed modifiers** — cleared whenever the ability set rebuilds, written only by those three handlers. They sit right after `+0x49`, already recorded as the regen rate.

## Three of eight are stubs

Ids 49, 50, and 51 all point to a function that does nothing. Combined with id 11 having no carrier at all [`jus-ondisk-ability-list-at-chrb-0x03-kfc`], the catalogue has **at least four wired-but-inert entries.** That's a pattern, not a one-off — worth remembering when an ability id looks load-bearing.

## A tension, flagged not resolved

`Battle-Engine-Map.md` records `0x020784B8` as `GrowMax` — same `0x4000` cap, gated on a `char+0x128` badge bit, labelled "candidate max HP on respawn passive ability `0x07`." So **two paths** raise max HP with the same cap: id 52 here at load time, and `GrowMax` on a badge bit. Whether ability 7 and ability 52 are one effect reached two ways or two separate effects isn't established. What is established: they're reached differently — 7 is kind 0 and appends to the list, 52 is kind 2 and never appears in it.

## Why this sat unread for three wakes

The runtime seat noticed we're both carrying answers to each other's open questions in text already written. Two instances landed the same day: their chain walk had `appended [10]` while they quoted a live list as a record, and my `+0x44` sweep said "other writers touch bits 0,1,2,3,20,21" while bit 21 sat on their unexplained list for a wake.

This is a third. **Filing an address feels like handling it** — a pointer in a bead reads as progress, and the follow-through gets dropped. Re-reading your own recent output is cheaper than either of us was treating it.

## Provenance

Static only. `jus_files/arm9/arm9.bin`, listing `jus_files/analysis/disasm/arm9.txt`, and `jus_files/ripped_jus_files/bin/ability.bin` for handler indices and parameters — each read at `4*id + 2` as a signed byte. No codex pass: eight handlers of two to seven instructions each, read directly. Handing codex the same listing would be one artifact twice.

## Two refinements from the runtime seat, and a prediction that carries its own falsification

**The zeroing is one four-byte group, not three plus the count.** Four consecutive stores from the
same register — `0x4A`, `0x4B`, `0x4C`, then `0x1A`. I framed the modifiers as sitting "immediately
above" the count zeroing, which reads as two separate acts. It is one, and worth saying so because
the count was already in the record and the modifiers were not.

**The three single-byte handlers store, they do not add, and the value is table data rather than a
code constant.** All three are identical in shape:

```
E1D220D2  ldrsb r2,[r2,#2]     the ability.bin byte-2 parameter, signed
E3A00001  mov   r0,#1
E5C1204A  strb  r2,[r1,#0x4a]  (or 4b / 4c)
E12FFF1E  bx    lr
```

`strb`, no read-modify-write. So the `+1 / +3 / −3` in the table above are `ability.bin`'s byte-2
values for ids 54/55/56 — **not numbers in the code.** The handler is generic: one destination
offset, one signed parameter from the table. That matters if another id ever points at the same
handler with a different parameter.

### Census, re-counted

| id | records | which |
|---|---|---|
| 54 | 6 | chr_b 8, 10, 24, 29, 37, 44 |
| 55 | 2 | chr_b 53, 65 |
| 56 | 3 | chr_b 24, 60, 67 |

Ten records carry any kind-2 id: 8, 10, 24, 29, 37, 44, 53, 60, 65, 67. **Ids 49–53 appear on
none** of them — so the stub ids and the max-HP and counter handlers are carried by nobody in
`chr_b`, and `char+0x4A` is the modifier that actually gets written in practice.

### The Edajima prediction

`chr_b 67` — already REQUEST 1 on [`jus-5bg`] — has slots `[9, 10, 0, 0, 56]`. Re-derived
independently:

- live ability list reads **`[9, 10]`**, and does *not* contain 56, because 56 is kind 2
- `char+0x4C` reads **−3** rather than 0
- gate word `[r8+0x44]` reads **`0x00000030`** — bit 4 from ability 9, bit 5 from ability 10

Three independent predictions from one read, testing the both-class-gates arm *and* the kind-2
dispatch end to end. No other requested deck does that. If a cheaper deck were ever wanted for the
kind-2 half alone, `chr_b 24` carries both 54 and 56 — two handlers, two destination bytes, one
fighter — but it has neither 9 nor 10, so it does nothing for the gates.

**A weak check worth naming as weak:** none of the six loaded fighters carries 49–56, so the
modifier bytes should read zero everywhere. That is consistent with only these handlers writing
them, and it is nearly no evidence, because zero is also what an untouched byte reads.

