# What selects between the chara setup loop's three descriptor paths

Iteration 152. Static only.

Iteration 151 found that the chara setup loop fills descriptor words `+0x08`/`+0x0C` from three different function pairs. This pass reads the selection logic and the six functions themselves. It also uncovered a third database blind spot, which is measured here.

## The selection logic — CONFIRMED_STATIC

Two byte guards pick Path A; a predicate then decides between B and C.

```
0x0214D600: cmp r1, #0x0    ; per-slot enable byte, sp+0x28 indexed by r5
0x0214D60A: cmp r1, #0x0    ; second gate, [r0 + r2 + 0x56]
                            ; both non-zero -> Path A
0x0214D62E: blx #0x02086BD4 ; else call the predicate
0x0214D632: cmp r0, #0x0    ; non-zero -> Path B, zero -> Path C
```

**The predicate `0x02086BD4`** (48 bytes, 6 callers) is a two-term OR:

```
0x02086BD8: ldr  r0, [pc, #0x24]     ; = 0x020AFE90
0x02086BDC: ldrb r0, [r0, #0x28]
0x02086BE0: cmp  r0, #0
0x02086BE4: bne  #0x2086BF4          ; byte set -> return 1
0x02086BE8: bl   #0x208C51C
0x02086BEC: cmp  r0, #0
0x02086BF0: beq  #0x2086BFC          ; else predicate -> return 0/1
```

That is: `[0x020AFE90 + 0x28] != 0` **OR** `0x0208C51C()`.

**The discriminator `0x0208C51C`** (24 bytes, **47 callers**) is a null test on a global object pointer:

```
0x0208C51C: ldr r0, [pc, #0x10]      ; = 0x0214CCF4
0x0208C520: ldr r0, [r0, #4]
0x0208C524: cmp r0, #0
0x0208C528: movne r0, #1
0x0208C52C: moveq r0, #0
```

`0x0214CCF4` is **not inside the arm9 image** — arm9 spans `0x02000000`–`0x020A9158` — and sits `0x2C` bytes below `ov6`'s load base `0x0214CD20`. It is a RAM global in the overlay-adjacent region, and `+0x4` is an object pointer whose nullness gates 47 call sites. `0x020AFE90` is loaded by **149** literal loads, making both major globals.

## The six functions

| path | `+0x08` (`sp+0x50`) | `+0x0C` (`sp+0x54`) |
|---|---|---|
| A | `0x02173004` | `0x02173014` |
| B | `0x020875B0` | `0x020875D8` |
| C | `0x02028920` | `0x020208EC` |

All six take `r0 = r5`, the slot index.

**Path C is a pure static table read.**

```
0x02028920: ldr r1, [pc, #4]         ; = 0x020A1EFC
0x02028924: ldr r0, [r1, r0, lsl #2]
0x02028928: bx  lr
```

And `0x020208EC` reads `[0x020A1EBC + slot*4]`, returning `0` if the entry is zero and otherwise passing it to `0x02011B38`. Two parallel word tables indexed by slot, no live state.

**Path B forks again on the same discriminator.** Both functions share an identical shape:

```
0x020875B0: bl #0x208C51C ; if non-zero -> bl 0x0219B9CC   else blx 0x0208C10C
0x020875D8: bl #0x208C51C ; if non-zero -> bl 0x0219BA00   else blx 0x0208C114
```

This means `0x0208C51C` is consulted **twice** on the way to a Path B value — once inside the predicate that selects B, and again inside each of B's two functions. `0x0219B9CC` and `0x0219BA00` resolve to **`ov10` unambiguously**: `ov10` spans `0x02172A60`–`0x021A73A0` and `ov11` only `0x02172A60`–`0x02181A60`, so both targets fall past `ov11`'s end.

**Path A's two targets cannot be attributed.** `0x02173004` and `0x02173014` land inside *both* `ov10` and `ov11`, which share load address `0x02172A60`. This is the phantom-overlay hazard, so which overlay provides them is **not claimed**.

## Interpretation — PLAUSIBLE, not claimed

The shape reads as a fallback hierarchy: Path C reads static tables with no live state, Path B routes through live code in `ov10` or Thumb helpers, and Path A goes to the overlay pair. A "prefer live data, fall back to a static table" reading fits, and the per-slot enable byte fits a "this slot is configured" flag. But none of the six functions' bodies past the first branch were read, and no string or allocation tag names any of them, so the *identity* of the three paths — local/remote/AI, or configured/default/absent, or anything else — is **not claimed**.

## A third database blind spot, measured

Verifying the literal resolutions against `xrefs.json` (a different representation from my own pc-relative arithmetic, per the charter rule) turned up a disagreement. The database records **5** loads of `0x020A1EFC` and **none of them is the one at `0x02028920`** — the load this finding depends on.

Raw bytes settle it: the instruction at `0x02028920` is `0xE59F1004` (`ldr r1,[pc,#4]`), and the word at `0x0202892C` is `0x020A1EFC`. The load is real; `xrefs.json` is missing it. There is no record with `insn_addr` `0x02028920` and none with `pool_addr` `0x0202892C`.

**Measured size.** Decoding every ARM `ldr Rd,[pc,#imm]` in arm9 that sits inside a recorded ARM function gives **4941** sites, of which **465** have no `xrefs.json` record — **9.4%**. Of those 465, **331 (71%)** have their literal pool at or past the *enclosing* function's end, and **51 (11%)** sit in a function of `16` bytes or fewer. `0x02028920` is both: a `12`-byte function whose pool word lies at `0x0202892C`, exactly one word past its end.

The likely cause is that the index resolves pools only within the enclosing function's extent. That is **PLAUSIBLE** at 71% coverage; the other 29% have some other cause and were not investigated.

**A wrong number I published mid-pass, retracted.** My first attempt at quantifying this reported **97.3%** of arm9 pc-relative pools as out-of-extent. That figure is meaningless and is withdrawn: it compared pools against *any* function extent rather than the *enclosing* one, and did not filter to *unrecorded* loads. Literal pools normally sit between functions, so a high out-of-extent rate is expected and tells you nothing about the index. The implausibility of the number is what prompted the re-check — 97% missing would have contradicted the database working at all in daily use.

**Consequence.** `query.py pool-values` and any "how many places load this value" count are floors, not censuses, for arm9 ARM — by about `9.4%`, concentrated in short functions whose pool follows immediately. This is the same family as the Thumb `BLX(1)` caller gap and the ARM-only field-writer scan: three separate indexes, each silently under-reporting.

## Not claimed

The identity of any of the six functions or the three paths. What `0x0214CCF4+0x4` points to, or what `[0x020AFE90+0x28]` means — only that both gate this selection and that the former gates 47 call sites. The cause of the 29% of missing literal loads not explained by the pool-past-end pattern. And the `ov10`/`ov11` attribution of Path A's two targets.
