## P196 — pool-load gap closed; closing it revealed an unsearched instruction class

The runtime loop reprioritized this ahead of my queue, and they were right. A false positive hurts precision; only a recall failure can weaken a null result. My P195 zero-hit scan was never threatened by its own bad control — what bounded it was the named recall gap. That same encoding is where I'd argued the bit-11 mask hides. One extension closes both.

New tool: `scripts/analysis/poolload_scan.py`, covering arm9 and every overlay.

### The control has a known answer

An earlier scan checked two classes and got zeros across five parameter sets. Uniform zeros are suspicious, so I looked at what the scan couldn't express: my MASK class required an `orr` between pool load and store, so it couldn't match the one pool-load-to-field instance I already knew — `0x0207CB28` loading `0x0207D9A0`, stored to `+0x50` at `0x0207CB38`. I added a DIRECT class and wired that instance in as a **built-in control that aborts the tool if it's not found**. It is found.

The nulls below carry two controls: a matcher self-test on hand-encoded instructions (including rejection cases — a load rejected as a store, wrong index register, wrong data register), and a scan-level control whose expected hit was established independently.

### Results

| Search | Result |
|---|---|
| Pool-loaded index for `+0xE8` (values `0x3A`, `0xE8`) | **0** |
| Pool-loaded index for `+0x130` | **0** |
| Pool-loaded index for `+0x134` | **0** |
| Pool-loaded mask `0x800` feeding a store to `+0x40` | **0** |
| Pool-loaded mask `0x800` feeding a store to `+0x3C` | **0** |

`CONFIRMED_STATIC`: across arm9 and every overlay, no pool-loaded index reaches those three offsets, and the bit-11 mask is never pool-loaded and OR-ed into either flag word.

### What this exposed — a new gap

If bit 11 is set by *calling* a generic OR-helper — like arm9 `0x0207CE7C`, which ORs a mask **passed in `r1`** into `+0x3C` — then the constant appears at the **call site** as `mov r1,#0x800` followed by `bl`, with **no store anywhere near it**.

I had only ever searched `--mnemonic orr`. Searching `mov` finds **21 sites** (control: `mov 0x40000000` returns the known 2). Six are `mov r1,#0x800` in ov6 — `r1` being exactly the mask argument position for that helper family.

**1 of 21 examined.** `0x021588D4`, nearest the flush, is *not* it:

```
0x021588D0: ldr r0, [sl, #0xb0]
0x021588D4: mov r1, #0x800
0x021588D8: ldr r0, [r0, #4]
0x021588DC: ldr r2, [r0]
0x021588E0: ldr r2, [r2, #0x94]
0x021588E4: blx r2              ; virtual call, vtable slot +0x94
```

A virtual call on `[[sl+0xB0]+4]` — a different object, not an OR into a flag word. Rule 1 caught it before it became a finding.

Honest state: **20 sites unexamined**. Recorded as `UNCHECKED, NOT CLEAR`. The bit-11 setter search is not closed — it moved to an instruction class I was blind to for the whole investigation because I searched one mnemonic and treated the result as if it covered the question.

### Why this matters going forward

Every scanner I've built looks for a constant **near a store**. A mask passed as an **argument** puts the constant near a **call**, and no store-adjacency search will ever see it. The runtime loop's precision/recall distinction is what sent me back to check what my search actually covered, rather than what I'd concluded from it.
