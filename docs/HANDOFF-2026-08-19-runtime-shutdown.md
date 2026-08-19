# Handoff — runtime loop ("ed"), 2026-08-19, shutdown before branch consolidation

Written on `re/ability-bitset-not-resistance` so it survives the merge. 125 commits this session;
head at time of writing is in the reply to the ledger. Beads are the system of record — every
claim below has a bead, and **the bead text is more precise than this summary**.

## 1. The campaign's central question is ANSWERED, and the answer reverses the doc

**Damage reduction is a ×0.75 multiplier — 25% of the base — NOT a flat −2.0.**
`docs/research/Damage-Reduction-Is-Flat.md` is refuted in its central claim. Bead **jus-ccb**
(read the retraction section at the bottom, not the top — the top is my own withdrawn reading).

Certified with the in-session control firing twice:

| move | base byte | base (8.8) | after reduction | out (raw) | displayed |
|---|---|---|---|---|---|
| B | 8 | 2048 | 1536 | 384 | 6.000 |
| DOWN+B | 7 | 1792 | 1344 | 336 | **5.250** |

Subtracted 512 and 448 respectively — both exactly `base/4`. Ratio constant at 0.750. A flat term
would have predicted 5.000 for DOWN+B. The doc's 5.000 row is **wrong**, and that row was the
entire basis of its "non-constant ratio ⇒ flat subtraction" argument.

### The full chain, end to end

```
base byte (signed) at [elem+0x10 + 4]        8 for B, 7 for DOWN+B — displayed units
  -> <<8                                     8.8 fixed point
  -> nature factor, tables 0x0209FEF4 / 0x0209FF14   ×1.0 on our path
  -> minus 25% per gate                      0x02082644 moveq r4,r5,lsl #6
                                             0x0208264C subeq r0,r0,r4,asr #8   (r0 -= r5>>2)
  -> out = (r5 + r0) >> 2  at 0x02082684     the 8.8 -> raw/64 conversion
  -> [sp+0x4C], the out parameter            address taken at 0x0208126C
  -> accumulated at 0x020812DC               str r3,[r8,r0,lsl #2], r8 = scratch+0xA4
  -> summed at 0x020821F8                    into scratch+0x134 (sum has exactly ONE term)
  -> flushed to HP
```

The formula is `0x020823E4` (arm9, 680 bytes), called at `0x02081280` from pipeline stage 1
(`0x02080F14`). The pipeline is eight stages at `0x02080C28`, caller `0x0207F480`.

## 2. THE EXACT NEXT ACTION

**Find what sets bit 5 of the flag word `[r8+0x40]`.** It is the last unknown in the chain.

atlas found two gates, both reading the byte table at `0x02092E68` = `[1,1,2,2,2,2,2,2]`:
- gate 1, `0x02082634`: `table[r1] == 1` → subtract 25% unconditionally
- gate 2, `0x02082650`: **bit 5 of `[r8+0x40]`** set AND `table[r1] == 2` → subtract 25% again

So total reduction is 0%, 25% or 50%. In our conditions `flag40 = 0x00000008` and **bit 5 is CLEAR
on both moves** — we have only ever measured the class-1 path.

Method: `JUS_WATCH` on the flag word at `scratch+0x40`. For the opponent that is
`0x0220FDC4+0x40 = 0x0220FE04`, but **re-derive it in-session from the anchor** before trusting the
run. Expect many writes; filter on `val` having bit 5 set and **carry one unconditional counter** so
"no bit-5 write" is distinguishable from "the watch never fired".

This is also the ability-derived value the whole campaign has been circling: poking the cached
bitset and the live ability list both did nothing (**jus-w66**) because the resistance reads a flag
bit and a class table, not the abilities — so abilities must feed those at **load** time.

## 3. Load-bearing but NOT confirmed

- **Which side owns the class index `r1`** in the gate lookups. Unread. Attacker vs victim changes
  the interpretation completely, and I have been burned twice on exactly this kind of assumption.
- **What the base byte at `[elem+0x10 + 4]` is per-move-per-character.** Measured 8 and 7 for two
  Goku moves against one target. Whether it varies by target is untested — that is what the owner's
  three decks (**jus-5bg**) would still be good for.
- **`0x02390A60`** — element `+0x08`, a pointer well outside every range named so far. Unidentified.
- **`scratch+0x184` / `+0x186`** are the ATTACKER's nature factors and read exactly 1.0 on our path.
  Whatever writes them is where a per-character attacker multiplier would land. Unwatched.
- The nature tables are exact **transposes**, so the `ColPrmMan+0x14D` bit swaps *which side's*
  nature indexes rows. Verified numerically from `arm9.bin`; the mechanism reading is inferred.

## 4. Retractions partners may not have processed

- **Mine, most recent and most important:** the "flat −512 in 8.8" answer in jus-ccb is WITHDRAWN.
  If anyone quotes "the flat −2.0 is real, it's −512", that is my error, superseded by §1. It fit
  because `base/4` is exactly 512 when base is 2048 — one data point could not separate the models.
- **jus-e1c:** `0x02081DDC` IS called but its **loop body never runs** on a landed hit, so atlas's
  `subne` −2.0 candidate at `0x02081F5C` never executes. Its gate bit and `r2` are **UNKNOWN, not
  refuted** — the card is testable as written if an executing path is ever found.
- **jus-x6j:** `0x02081ED0`/`0x02081EE0` never execute on a landed hit. My original wording said
  "the code never executes"; the precise statement is that the FUNCTION executes and the BODY does not.
- **jus-ix2:** savestates `cb_healoff`, `cb_battle`, `m4_start` are CONTAMINATED (items=1 gimmick=1
  from RAM). Any figure taken there is tainted. `pos_base` does not exist and never did.
- **jus-s5q:** the container is the **Battle_ColPrmMan** (`0x0220DDE0`, size `0xFB54`) — NOT the
  ObjMan and NOT the ColMan. It was named wrong twice before landing. 128 slots declared, 19
  constructed, stride `0x188` from `+0x454`, fighters at slots 17 and 18, slots 19+ chained through
  `+0x00` as a free list.
- **An ability-free opponent CANNOT be built.** `chr_b` 70–73 are the only empty-ability records and
  all four are the Debug series (`dt_b_01`–`04`, Komaman/Taizo). Four separate workarounds in this
  campaign existed to obtain a number that was one signed byte away.
- `docs/research/defence-candidates-ruled-out.md` **in this worktree is stale** — it still concludes
  the flat −2 belongs to ability `0x09`. Refuted twice over (jus-w66, and the reduction is
  proportional). **Not yet fixed — this is the top documentation debt.**

## 5. Parked for DJ (bead jus-law)

- **Q17 open:** what does 自動回復 actually do — steady trickle or jump toward full? Regen is measured
  to be fine-grained (HP lands on non-integer displayed values), which already refutes the doc's
  "one frame = 2.0" model (**jus-i3v**).
- **Q16 answered** by the two-tap tip and can close. **Q18 withdrawn** — I answered it from the ROM.
- **A numbering collision to check:** the ledger relayed an answer to an *older* Q16 (team battle).
  Confirm DJ was shown my Q16–Q18 and not the old set.
- **Robin caveat still live:** her `chr_b` record is `[9,25,12]`, identical to Luffy's, but Luffy's
  LIVE list reads `[9,25,12,14]` — id 14 is appended at runtime and is in no record. So her
  owner-reported auto-guard is not in her record either. Either the runtime append is per-character,
  or defensive behaviour lives partly outside the ability system. **Read her live list before using
  her as a replicate arm.**

## 6. Harness gotchas not already written down

- **`JUS_WATCH` reports `pc = instruction + 8`** (ARM prefetch). **Subtract 8.** Verified by decoding
  `arm9.bin`: my reported "writer" `0x020812E4` is `str r0,[sp,#0x14]`; the real store is
  `0x020812DC`. The reported clear address `0x02051864` is a *branch*. This is the twin of the
  `0x02156EB4` return-address error — off by a fixed amount and still landing on a real instruction,
  so nothing complains.
- **The HP-delta oracle is INVALID for moves with side effects.** DOWN+B forces an opponent character
  switch, so HP afterwards belongs to a different character — my read went *up* by +0.578. Read the
  formula, not the HP dip. The doc almost certainly got its wrong 5.000 exactly this way.
- **Single-stepping starves the input plan.** A 140-step `stepi` loop inside a breakpoint command
  voided a run: the bridge threw a pending-command error and the control never fired. Use
  breakpoints, not stepping, when a landed hit is needed.
- **`$Z2` hardware watchpoints are broken** — the stub answers `OK` and never triggers, proven with a
  real stimulus (**jus-m22**). Fable's DataWrite patch replaces them and works:
  `JUS_WATCH=addr JUS_WATCH_LOG=file ./launch_emu.sh`, range-aware. Patch saved at
  `scripts/emu/patches/write-watchpoint.patch`.
- **Savestates DO survive a relaunch** — the older handoff's "none survive a reboot" is wrong. I did
  seven relaunches in one wake with no loss. This matters because the GDB stub allows **one
  connection per launch** and a dead stub freezes the emulator with only a relaunch as the exit.
- **Hand-write `.gdb` files as heredocs.** Generating one from Python left a literal `%%08X` in a
  `printf`; gdb errored on argument count and **detached**, producing zero fires — indistinguishable
  from a wrong breakpoint address.
- **`wp_inrange` first presses MISS.** Seek 1–2 steps RIGHT; hits land at x=649/650 for exactly
  −6.000. After ~3 hits the seek can walk past the opponent, so reload per arm.
- **`slot+0x29` is a STALE oracle** for the active character. I used it in jus-3aw after having
  retracted it earlier in the same campaign, which makes those switch negatives weak. Use the live
  ability list (count `char_struct+0x1A`, bytes from `+0x1B`) or the cached bitset at
  `battleObj+0x128`.
- **Long-hold touch plans DO deliver touch** — the rule-screen items pill at DS(73,51) flips
  `0x020AFEBB` with a 90-frame hold. That is the RAM oracle jus-3aw lacked. Battle taps still do not
  switch. Fable's `plan_step` last-mask-wins batching bug is real and worth fixing, but it does NOT
  explain the 20- and 90-frame failures.

## 7. On the beads db observation

The ledger's finding matches what I know: all three loops have been writing to the **same** beads db
because the other worktrees have no `.beads` dir and `br` walks up. Resolving the ledger by
**exporting from the live shared db** rather than line-merging `issues.jsonl` is the right call —
line-merging would produce a file that no longer matches the db every loop actually read from. One
related quirk already in project memory: `br` 0.2.19 rejects uppercase ids on **import** in a
worktree with no db; the fix is a db-backed `.beads`, not lowercasing ids.

## 8. The methodological thread, which is worth more than any single finding

Six times this session a **null with no stimulus** nearly became a finding, in a different costume
each time — a control that ran before the stimulus could arrive, a counter cap on a busy loop, two
filters covering three cases, an opponent's auto-guard blocking the hit, my own single-stepping
starving the input, and a detector (peek-polling a sub-frame field) that could not detect its target
at all. Every one was caught by a control, never by inspection.

And **four derivations in one thread reproduced the observed values from a wrong premise** — two of
atlas's predictions, one they drafted and binned, and mine. Mine is the instructive one: I claimed my
flat reading "reproduces the doc's other move without any fitting", having computed `1792 − 512` by
*assuming* flatness — the very thing in question — then offered agreement with the doc as independent
confirmation. A derivation that lands on the observed value from the wrong premise is the most
convincing kind of wrong, and only writing predictions down before looking exposed any of them.

Two more that generalise: **scripting a check does not make it a check** — what makes it one is that
it could have failed; both atlas and I "verified" containments against a size taken from the name we
were trying to establish. And **the record spans branches** — five damage docs exist only on other
branches, which is part of why this consolidation matters.
