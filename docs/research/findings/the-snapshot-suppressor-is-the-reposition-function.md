# Findings: the snapshot suppressor is a reposition function — and iteration 144's "second writer" was mine to retract

Loop-Atlas iteration 145. Static.

Set out to read `0x0207E864` for what it writes to `record+0x34`. It doesn't write `record+0x34` at all.
Tracing the base register instead turned up two things: a correction, and the answer to a question open
since iteration 137.

1. **Correction:** `0x0207EF1C` writes `[record+0x5C]+0x34` — the **element's** flags, not the record's. My
   iteration-144 claim of "a second writer" was wrong.
2. **`0x020804E8` is the element's reposition function**, and it's what sets bit `0x100`. Iteration 138
   guessed this as SPECULATIVE; it is now confirmed.

---

## 1. The correction

Iteration 144 said `record+0x34` has a second writer at `0x0207EF1C`, and used that to withhold a runtime
conclusion. The instruction is `strne r0, [r2, #0x34]`, and `r2` comes from two lines up:

```
0x0207EF0C  tst r0, #8
0x0207EF10  ldrne r2, [r4, #0x5c]     ; <-- r2 = [record+0x5C]
0x0207EF14  ldrne r0, [r2, #0x34]
0x0207EF18  orrne r0, r0, #0x800
0x0207EF1C  strne r0, [r2, #0x34]
```

Iteration 140 established that **`record+0x5C` holds the BattleMove element**. So this writes
`element+0x34` — a different object's flags word that just happens to share the same offset.

I took the companion scan's `base=r2` at face value without tracing `r2`. Two instructions would have
caught it — the same kind of mistake as iteration 144's `tst r1, r0`, where I also stopped one step short
of the operand's origin.

**What this means for iteration 144:** the reason I gave for withholding the runtime conclusion was wrong,
so the reasoning is actually stronger than stated — the installer is now the only *identified* writer of
`record+0x34`. I'm still not claiming write-once: `+0x34` has 85 direct writers ROM-wide and most are
untraced. The conclusion stays withheld, but for an honest reason instead of a mistaken one.

## 2. The snapshot suppressor, found

`0x020804E8`, 40 bytes, three call sites (`0x020804BC`, `0x02080578`, `0x0208058C`):

```
0x020804E8  ldr r3, [r0, #0xc]
0x020804EC  str r3, [r0, #0x14]      ; previous = current
0x020804F0  ldr r3, [r0, #0x10]
0x020804F4  str r3, [r0, #0x18]
0x020804F8  str r1, [r0, #0xc]       ; current = arg1
0x020804FC  str r2, [r0, #0x10]      ; current = arg2
0x02080500  ldr r1, [r0, #0x34]
0x02080504  orr r1, r1, #0x100
0x02080508  str r1, [r0, #0x34]      ; suppress the next snapshot
0x0208050C  bx lr
```

It snapshots the current position, writes a new one, then sets bit `0x100`. That's a **reposition**. The
flag exists because the function has *already* saved the old position, so the per-frame pass must not
snapshot again and overwrite it.

This closes a thread that ran across four iterations:

- **137** found the frame pass copying `+0x0C`/`+0x10` into `+0x14`/`+0x18` unless bit `0x100` was set, but
  couldn't say who sets it.
- **138** looked in the allocator, didn't find it, and reasoned that since the allocator snapshots on every
  branch, `0x100` "more likely belongs to **repositioning** than to creation" — recorded SPECULATIVE.
- **139**, **140** named `+0x0C`/`+0x10` as a position pair.
- **145** finds exactly that: a reposition function that snapshots and sets `0x100`.

The iteration-138 inference — reasoning from *why the allocator would not need the flag* — turned out to be
the right way in. It named the answer before the answer was found.

## 3. A new element flag bit, and a table behind it

Bit `0x800` on `element+0x34` is new; iterations 137–138 catalogued `0x1`, `0x4`, `0x8`, `0x10`, `0x20`,
`0x100`, `0x200`, `0x600` and `0x1000`. It comes from a **table lookup**:

```
0x0207EEF8  ldr r3, [r5, #0xf8]
0x0207EEFC  mov r2, #0x18
0x0207EF00  ldr r3, [r3, #0x18]      ; the table base
0x0207EF04  smlabb r0, r0, r2, r3    ; base + index * 0x18
0x0207EF08  ldrb r0, [r0, #0x15]
0x0207EF0C  tst r0, #8               ; entry byte +0x15, bit 8
```

`smlabb r0, r0, r2, r3` computes `r3 + (r0.low16 × r2.low16)` — an indexed access into a table at
`[[r5+0xF8]+0x18]` with **stride `0x18`**. If the entry's byte at `+0x15` has bit `8`, the element gets
`0x800`.

This is **data-driven flag propagation**: a static table entry controls a runtime element flag. Worth noting
because it means some element behavior is authored in data, not code.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x0207EF1C` writes `record+0x34` | **REFUTED** *(iteration 144, my own)* — `r2 = [record+0x5C]`, so it writes `element+0x34` |
| `record+0x34` has an identified second writer | **REFUTED** — the installer is the only one identified |
| `record+0x34` is write-once | **not claimed** — 85 direct writers ROM-wide, most untraced |
| `0x020804E8` sets `element+0x34` bit `0x100` | **CONFIRMED_STATIC** — `orr r1, r1, #0x100` at `0x02080504` |
| `0x020804E8` is a reposition function | **CONFIRMED_STATIC** — snapshots `+0x0C`/`+0x10` into `+0x14`/`+0x18`, then writes `arg1`/`arg2` into the current pair |
| Bit `0x100` belongs to repositioning rather than creation | **CONFIRMED_STATIC** *(was SPECULATIVE, iteration 138)* — the only setter is a reposition |
| `element+0x34` bit `0x800` exists | **CONFIRMED_STATIC** — `orrne r0, r0, #0x800` at `0x0207EF18` |
| `0x800` is set from a table entry's byte `+0x15`, bit `8` | **CONFIRMED_STATIC** — `smlabb` stride `0x18`, `ldrb +0x15`, `tst #8` |
| The table lives at `[[r5+0xF8]+0x18]` | **CONFIRMED_STATIC** — `0x0207EEF8`/`0x0207EF00` |
| What the table's records are | **not claimed** — only the stride `0x18` and one tested bit are known |

## Next angles, ranked

1. **Read `0x020804BC`, `0x02080578`, `0x0208058C`** — the three reposition call sites. They supply the new
   position, so they tell us *what* moves an element.
2. **Identify the `0x18`-stride table** at `[[r5+0xF8]+0x18]`. A static table driving element flags is worth
   naming, and `+0xF8` on `r5` is a new manager-side field.
3. **Read `0x0207F7C8`** (carried) — the skip target of iteration 144's `0x6FF` test.
4. **Read `0x0207E864` properly** — 1976 bytes, **0 callers**, so likely a function pointer; only read 12
   instructions of it this wake.
