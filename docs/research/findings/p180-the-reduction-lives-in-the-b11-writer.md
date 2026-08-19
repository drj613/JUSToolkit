# P180 — The flat −2.0 lives in the B11 writer, and `scratch+0xE8` is not vestigial

**Iteration 180. Static.** My queue said "look for a ×3/4 ratio." Reading `Damage-Reduction-Is-Flat.md` properly killed that before I burned a wake on it.

## The ratio hypothesis was already dead

The corrected table has both moves:

| move | unresisted | Luffy | difference | ratio |
|---|---|---|---|---|
| B | **8.000** | 6.000 | **−2.0** | 0.750 |
| DOWN+B | **7.000** | 5.000 | **−2.0** | 0.714 |

Constant difference, non-constant ratio — flat, not multiplicative. My queued "0.750 is a clean 3/4" would have re-derived something the doc already refuted. Second time in two wakes that actually reading this doc saved me from wasting one; grepping it cost three.

The doc states its own robustness argument: the auto-heal correction shifted every figure by 2.0 and the conclusion didn't move, because a constant offset cancels in a difference.

## The reduction happens upstream of the apply

`CONFIRMED_STATIC`. The doc reports a breakpoint showing **512** handed to the HP drain for the unresisted target — so Luffy gets 384. The difference exists before the apply. The flush inside `0x02158B20`:

```
0x02158B98: ldr  r1, [r0, #0x10]    ; the ColPrm scratch object
0x02158B9C: ldr  r0, [r1, #0x40]    ; its flags
0x02158BA0: tst  r0, #0x800         ; bit 11 — damage pending
0x02158BA4: beq  0x2158c50          ; not pending -> straight to the tick loop
0x02158BA8: ldr  r0, [r1, #0xe8]    ; *** the pending HP delta ***
0x02158BAC: ldr  r2, [r1, #0x130]   ; *** the pending second-gauge amount ***
0x02158BB0: rsb  r4, r0, #0         ; negate
0x02158BB4: ldr  r0, [sl, #0x1b4]
0x02158BB8: mov  r1, r4
0x02158BC0: bl   0x020783CC         ; apply(−delta)
```

The `512`/`384` the doc breakpointed is what sits in **`scratch+0xE8`**, negated at flush time. The −2.0 is applied when `+0xE8` is *written*, not when it's *read*.

That's why P175 and P176 came up empty. P175 looked for a constant `sub #0x80` in the arm9 HP/damage region; P176 looked for a per-character 128 in `chr_b`. Both were downstream or beside the point — the reduction is baked in before the value reaches either place.

## B11 is reinstated as the central question

`RETRACTED` — the record's `PLAUSIBLE` claim that "`+0xE8` is vestigial in retail and B11 may be the wrong question" (iteration 76, based on sibling `+0x140` reading 0 at runtime). `+0xE8` is read on **every** flush at `0x02158BA8`, gated on flags bit `0x800`, and the doc's breakpoint proves it carries live damage — `512` for a real punch. The note said "one harness read settles it"; that read happened and settles it the other way.

B11 isn't the wrong question — it's **the** question. The writer of `scratch+0xE8` is where the only confirmed damage-reduction mechanic lives.

Why it's hard: an exhaustive ROM-wide sweep at iteration 76 found **27** ARM immediate-offset stores to `+0xE8`, **none** in ov6, none sharing a companion offset with the owner, and **zero** split-offset (`add`+`str`) stores. Both arm9 candidates were individually refuted. The writer must use a **register-offset store or Thumb** — the immediate-offset search space is exhausted.

## What this changes for the two open cards

- **`jus-f0v`**: Luffy's half is confirmed clean — the runtime loop measured 6.000 with heal off, matching the doc's corrected figure. What remains is the dummy at 8.000 in a clean session; `pos_base` is the state for it. That would discharge the doc's cross-session caveat, its last weakness.
- **`jus-fun`** (melonDS watchpoint planning): now a blocker for the campaign's oldest question, not just a convenience. A write-watchpoint on `scratch+0xE8` names the writer in one capture. No static approach will — the reachable search space has been swept.

## Queued by this wake

1. **Register-offset store scanner.** The one static instrument that could still find the `+0xE8` writer: scan for `str rX, [rY, rZ]` and `add rY, #0xE8` / `str [rY]` pairs, which `search-imm` can't see by construction. Cost falls entirely on this loop; `jus-fun` lists it as one of four routes.
2. Polled-KO discriminator — deferred four times, now genuinely lower-value than the above.
3. Enumerate the `{kind,id}` table; extra-ability writer; auto-heal.
