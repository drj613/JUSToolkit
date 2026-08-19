# Loop-Atlas 220 — one routine assembles both load-time derived values

Claims in beads: [`jus-one-routine-assembles-both-u24`], [`jus-bit5-is-ability-10-rxl`],
[`jus-nature-column-selector-8gk`], [`jus-base-2-is-jpower-damage1-10-mse`].

We spent a long time chasing two separate questions — where abilities feed the damage path, and where nature does. Turns out the answer is the same routine.

## ov6 `0x02157114` composes both the nature byte and the gate word

This routine was already known for turning the cached ability bitset at `battleObj+0x128` into the ±25% gate word at `+0x44`. It also assembles the packed three-slot nature field at `+0x175`, same object, same pass:

```
0x021571C4  ldr  r0, [r4, #0x1a8]        r4 = battleObj
0x021571CC  ldr  r0, [r0, #0x10]         the ColPrm scratch — the same object the flag
                                          helper 0x02083BE0 writes +0x44 on
0x021571C8  ldrb r2, [r5, #3]            slot A
0x021571D8  ldrb ip, [r5, #4]            slot B
0x021571D0  ldrb r1, [r5, #5]            slot C
0x021571D4  ldrb r3, [r0, #0x175]        read-modify-write: bits 6–7 survive
0x021571E4  orr  r6, r3, r2              slot A -> bits 1:0
0x021571F4  orr  r3, r3, r2, lsr #28     slot B -> bits 3:2
0x02157204  orr  r1, r2, r1, lsr #26     slot C -> bits 5:4
0x02157208  strb r1, [r0, #0x175]
```

Three 2-bit slots packed from **three consecutive bytes** at `r5+3`, `r5+4`, `r5+5`, where `r5 = [[[battleObj+0x1a0]+0x174]+8]`, set at `0x02157130`.

## The asymmetry has a shape now

The damage routine reads bits 1:0 of the **defender's** byte as the table row, and one of three fields from the **attacker's** byte as the column, selected per move by `[arg1+0x18]` bits 6–7 [`jus-nature-column-selector-8gk`]. So each fighter carries three natures, the move picks which one to attack with, and the defender always defends with slot A. That looks like a design decision, not an implementation accident.

## Probably the koma route — but that's a lead, not a claim

The owner's ground truth says natures are four values (力/知/笑/なし) and are **per panel**. Three consecutive per-character source bytes feeding three slots, with the move choosing among them, is exactly what a deck contributing several natures would look like. What `r5` points at is still unidentified. That's the next question, not a conclusion — and it's the same unlocated structure as the on-disk ability list, so one answer unblocks several things.

## Why this was urgent

The runtime seat was about to diff `+0x175` across a training-menu nature change. A full sweep for `imm == 0x175` finds **8 stores in the whole ROM**, and only `0x02157208` composes three slots. The others rule out: `0x021C9D78` writes a literal `0` (initialiser); `0x021CA22C` writes `0` or `1` from `cmp r0,#8`, a boolean rather than a four-value nature; the rest are init pairs.

So the menu almost certainly can't write `+0x175` directly — it must write the source bytes at `r5+3..5`, and `+0x175` only refreshes when `0x02157114` re-runs. "The byte didn't move on the A press" is therefore the *expected* result, and the planned diff would have shown a clean stable byte and licensed the wrong conclusion that the menu doesn't set nature.

That's the third planned null this session that a design would have misread, and the first where the misreading was baked into the **target address** rather than the readout. The revised target is `r5+0..16` across the press, at the same navigation cost.

## Provenance

Static only. Listing `jus_files/analysis/disasm/ov6.txt`; the store sweep is `query.py search-imm 0x175 --all`, 16 hits, 8 stores, every one inspected. Pointer chain read from the instruction stream, not inferred from a live value.
