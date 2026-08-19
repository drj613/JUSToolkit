# P173 — `char+0x56C` is the character struct; the drain is HP; my P172 doubt was wrong

**Iteration 173. Static, cross-branch.** Goal: identify what `char+0x56C` points at and find the HP field behind the owner's 1-HP floor.

The answer already existed in this repo — on `master`, in a file missing from my worktree. The cross-branch rule caught it in two commands, which is the only reason this isn't a rediscovery.

## `char+0x56C` points to the character struct; `+0x16`/`+0x18` are max and current HP

`CONFIRMED_STATIC`, from `docs/research/HP-Struct-From-Disassembly.md` (on `origin/master` and the owner's branch; absent from `loop/battle-engine-atlas`). Two arm9 functions name the fields directly:

```
0x020784B8  ldr   r2, [r0, #0x56c]   ; r2 = character struct
0x020784BC  ldrsh r0, [r2, #0x16]    ; max HP, SIGNED halfword
0x020784C0  cmp   r0, #0x4000        ; the cap
...
0x020784E8  ldr   r4, [r0, #0x56c]
0x020784EC  ldrsh r2, [r4, #0x16]    ; MAX
0x020784FC  ldrsh r1, [r4, #0x18]    ; CURRENT
```

| char_struct offset | size | field |
|---|---|---|
| `+0x16` | s16 | **max HP**, capped at `0x4000` = 16384 = 256.0 displayed at 1/64 |
| `+0x18` | s16 | **current HP** |
| `+0x41` | u8 | `chr_b` index |

## I was wrong last wake; the map's name was right

`RETRACTED` — my P172 claim that `char+0x56C` "is not the HP the owner's 1-HP floor describes," and the "record inconsistency" I flagged around it.

I found id 19's drain path landing in a `{max +0x16, current +0x18}` halfword pair clamped to `[0, max]`, saw the clamp went to **zero** while the owner says DoT leaves you at 1 HP, and concluded the meter probably wasn't HP. It is HP. `Battle-Engine-Map.md` calling `0x020783CC` "the HP-apply trampoline" was correct all along, and the offsets I independently derived — `+0x16` max, `+0x18` current — match the same fields that doc names from different call sites. My decode was right; my *inference from a mismatch* was wrong.

**The error is worth naming because it's the third time in two days.** I had two facts that didn't fit — a clamp to 0 and a stated floor of 1 — and resolved the conflict by demoting the fact I'd derived myself instead of holding both open. The shape of the mismatch felt like evidence about which fact was weaker. It wasn't evidence at all.

Consequences, pushed the same wake:

- **Id 19's `−4` drains CURRENT HP.** The "it's a gauge, not HP" reading is `REFUTED` — it was reading (a) in the three I gave the runtime loop, and it's dead.
- **The remaining explanation for their unchanged `152.0` is the cancel gate**, backed by their own gate capture: for that target, bit 29 (`opcode 0x1D`) is **set**, so the effect was cancelled before applying. Two independent lines now converge on the same answer, and neither needs the drain to be a gauge.
- The message where I said `+0x56C` isn't HP is corrected.

## The 1-HP floor is not on this path

`CONFIRMED_STATIC`: `0x02078488` clamps to `[0, max]` — `movmi r1, #0` on a negative result. Nothing on the id-19 path floors at 1. The handler (`0x02159500`) is gate → apply → `mov r0,#1` → return, with no HP check.

The one function in the record that *does* set HP to 1 is something else. `0x02078428`:

```
0x0207842C  ldr   r6, [r0, #0x558]     ; walk the character list
0x02078440  mov   r4, #1
0x0207844C  ldrb  r0, [r6, #0x40]      ; per-node skip flag
0x02078458  cmp   r8, #0               ; arg1 == 0 ?
0x0207845C  strheq r4, [r6, #0x18]     ; -> current HP = 1
0x02078464  ldrsh r2, [r6, #0x16]      ; else: max * pct / 100
```

That's a **bulk set-HP utility** iterating `char+0x558`: with `arg1 == 0` it writes `1` to every living character's current HP; otherwise it sets a percentage of max. A story or gimmick reset, not a per-tick DoT floor. It also settles what `+0x558` is: a **list of character structs**, each with the HP pair at `+0x16`/`+0x18` and a skip flag at `+0x40` — the campaign has been calling it a "Meter-node list."

`not claimed`: where the 1-HP floor lives. Three candidates, none tested — the per-frame tick driver checks HP before calling the handler; the KO check requires a damage *event* and ignores HP reaching 0 by drain; or the owner's floor comes from something else entirely.

## Queued by this wake

1. **Static:** find who calls `node+0x0` per frame. That driver is the last unexamined link on the DoT path and the most likely home for a floor check. It also answers what decrements `node+0xE`.
2. **Owner (`jus-law`), sharpened:** does a poisoned or burning character at low HP *stop* losing HP, or does the drain keep running while the character survives at 1? Those are different mechanisms and a player can tell them apart instantly.
3. **Runtime:** nothing new — `jus-eml` already covers the last unmeasured link in the immunity chain.
