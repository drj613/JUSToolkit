# P172 — The effect cancel gate: what the status opcode is for, and where the drains land


> **RESOLVED SAME DAY — the gate's bitset is the repo's already-documented CACHED ABILITY BITSET.** For
> `opcode < 32`, `char+0x120 + 4*(opcode>>5) + 8` **is** `entity+0x128`, the subject of
> `docs/research/Ability-Bitset-Is-Not-Resistance.md` (on branch `re/ability-bitset-not-resistance`, not on
> mine — see the process note below). That word is runtime-confirmed live and read during combat: setting bit 4
> (ability `0x04` オートガード Auto-Guard) drives damage to zero, and it is the campaign's canonical positive
> control. It is populated at load by `0x0215FB3C`, which walks the character's ability list and caches each
> ability ID as a bit.
>
> The bitset is indexed **by ability ID**; my gate indexes it **by effect opcode**. If both hold, then
> **effect opcode == ability ID**, and the mechanism is: *having ability N cancels effects whose opcode is N.*
> **Status immunity is an ability.** Labelled the owner's way — the cached ability bitset — rather than minting
> "cancel bitset" as a second name for the same word. Do not call it a resistance bitset.
>
> **This resolves a negative sitting in that doc.** It concluded status-resistance abilities "do exactly
> nothing", having tested them only at **damage** time. The gate is not a damage-time modifier — it is an
> effect-**cancel** path. A status-resistance ability doing nothing to damage and everything to effect
> application is fully consistent, which converts that doc's dead end into a wrong-place-to-look.
>
> **Two things my expression adds to that doc.** It only ever examined the 32 bits of one word. The
> `4*(opcode>>5)` term means opcodes ≥ 32 read a **second word at `entity+0x12C`** — and the status opcodes
> `0x19`–`0x22` (25–34) straddle the boundary: 25–31 are bits 25–31 of `+0x128`, while 32/33/34 are bits 0/1/2
> of `+0x12C`. id 22's opcode `0x21` = 33 lands in that second word. So the bitset is wider than 32 abilities.
> And `base +0x120` with a `+8` displacement is a more precise description of the structure than "a word at
> `+0x128`".
>
> **The `+0x56C` inconsistency is resolved, and in the doc's favour.** It cautioned that
> `entity + 0x56C = char_struct` "was almost certainly a pointer load, `ldr [entity, #0x56C]`, not a
> subtraction." The bits confirm it: `0x020783D0` is literally `ldr r0, [r0, #0x56c]`. So `+0x56C` holds a
> **pointer** to the `{max +0x16, current +0x18}` meter node, which is why the apply clamps to `[0, max]` and
> why it is not the HP the owner's 1-HP floor describes. Their "almost certainly" → `CONFIRMED_STATIC`.


**Iteration 172. Static.** Read the three drain handlers — id 19 (`0x02159500`), id 30 (`0x02159624`), and the shared id 5/33 handler (`0x021592DC`) — looking for a return value, an HP-or-gauge answer, and the clamp-to-1 the owner's ground truth predicts.

Found the gate that explains the whole subsystem's shape, and answered an open question: **what the `+0x7` status opcode is for.**

## The drains keep ticking, gated by their own opcode

`CONFIRMED_STATIC`. Both opcode-bearing drains share the same skeleton:

```
0x02159500:  push {r3,r4,r5,lr}          ; id 19
0x02159504:  mov  r2, #0x1d              ; <- its own opcode from the handler table
0x02159508:  mov  r5, r0                 ; battle character
0x0215950C:  mov  r4, r1                 ; the node
0x02159510:  bl   0x0215986C             ; the gate (char, node, opcode)
0x02159514:  cmp  r0, #0
0x02159518:  movne r0, #0
0x0215951C:  popne {r3,r4,r5,pc}         ; gate said yes -> RETURN 0 -> node gets stubbed
0x02159520:  ldr  r1, [r4, #4]           ; paramArray[id]
0x02159524:  ldr  r0, [r5, #0x1b4]
0x02159528:  ldrsh r1, [r1, #4]          ; the signed amount (-4)
0x0215952C:  bl   0x020783CC             ; apply it
0x02159530:  mov  r0, #1
0x02159534:  pop  {r3,r4,r5,pc}          ; RETURN 1 -> keep ticking
```

id 30 (`0x02159624`) is identical through the gate call with `r2 = #0x1b`, its own opcode.

The P171 prediction holds with a condition: a non-zero-`amount` id returns 1 and keeps its handler — *unless the gate cancels it*, returning 0 and stubbing the node just like an amount-0 id would. Same id, different outcome depending on target.

**id 30 also uses the duration as a phase counter:** `ldrh r0,[r4,#0xe]` / `tst r0,#0xf` / `bne` past the work — it fires only when `duration & 0xF == 0`, once every 16 frames. So `node+0xE` is read by the handler even though the handler doesn't decrement it — the state-timer reframe made concrete.

## The gate is a bitset test keyed by the status opcode

`CONFIRMED_STATIC`. `0x0215986C` computes `char+0x120`, calls `0x02158EB0(char+0x120, opcode)`, and **if that returns non-zero it zeroes `node+0xE`** and reports cancel, stubbing the handler.

`0x02158EB0` is an eight-instruction leaf:

```
return (Mem32[base + 4*(opcode >> 5) + 8] >> (opcode & 0x1F)) & 1
```

32 bits per word, word index `opcode >> 5`, bit index `opcode & 0x1F`, table at `base + 8`. Codex was given the eight words with no addresses or hypothesis and returned that expression exactly — same shifts, same `+8`, same return values — and noted unprompted that only `0` or `1` can come back.

**This is what the `+0x7` opcode is for.** After the channel-boundary retraction I had "what does the opcode distinguish, if not the channel?" queued as open. It's the **bit index into a per-character bitset that cancels the effect**. Two things fall straight out:

- **Only opcode-bearing effects are gated.** The shared id 5/33 handler `0x021592DC` (both `+0x7 = 0xFF`) has **no gate call** — it applies and returns 1 unconditionally. The five opcode-less ids in the status range are ungated by construction.
- The opcode range `0x19`–`0x22` are bit positions, not a behaviour enum. With `opcode >> 5 == 0` for all of them, every status reads bits 25–34 of one bitset — the second word is in use, so the table is at least 2 words wide.

**A caution I'm not going to talk myself out of.** `char+0x120` is documented in this campaign (`findings/character-embedded-views-0x120-0x130.md`, `char-0x130-is-a-gated-handler-table.md`), and the owner's working branch is named **`re/ability-bitset-not-resistance`** — which reads like they've already refuted a resistance interpretation of a bitset in this area. So: `CONFIRMED_STATIC` that a set bit cancels the effect. `not claimed` what the bitset *is*. Whether it's populated from abilities, a status-already-active flag, or something else is exactly the kind of thing the owner may already know, and it's going to `jus-law` rather than into a label.

## Where the drains land — and the clamp is to ZERO, not to 1

`CONFIRMED_STATIC`. id 19 applies its amount through `0x020783CC`, a two-instruction trampoline: `ldr r0,[r0,#0x56c]` then tail-jump to `0x02078488`. The worker:

```
0x02078488: ldrsh r2, [r0, #0x18]     ; current
0x0207848C: adds  r1, r1, r2          ; current + delta
0x02078490: ldrsh r2, [r0, #0x16]     ; max
0x02078494: movmi r1, #0              ; negative -> clamp to 0
0x02078498: cmp   r1, r2
0x0207849C: movgt r1, r2              ; above max -> clamp to max
0x020784A0: strh  r1, [r0, #0x18]
0x020784A4: ldrsh r0, [r0, #0x18]
0x020784A8: cmp   r0, #0
0x020784AC: movne r0, #1
0x020784B0: moveq r0, #0              ; returns "still non-zero"
```

The object at `char+0x56C` is a **`{max at +0x16, current at +0x18}` halfword meter**, clamped to `[0, max]`, returning whether the meter is still non-zero.

**The clamp is to `0`. The owner says poison and burn never kill and leave the victim at 1 HP.** Those two facts can't both describe the same field, so one of these is true — I'm not picking between them:

- `char+0x56C` is **not** the HP meter, and id 19's `−4` drains something else. This also explains the runtime observation that the opponent sat at `152.0` unchanged while id 19 fired — no stub needed.
- It *is* HP and the 1-HP floor is enforced somewhere else entirely, meaning this path would allow a kill and something upstream prevents it.

**Record inconsistency, flagged not resolved.** `Battle-Engine-Map.md` calls `0x020783CC` "the HP-apply trampoline" and "the real HP-delta path" in the B11 and guard sections — while also correctly documenting that it dereferences `char+0x56C`. The mechanism in the record is right; the *name* is doing work the bits don't support. The guard/SP-gauge section separately treats `+0x56C` as a gauge and `+0x558` as a meter-node list, which is the reading the clamp-to-0 supports. `not claimed`: which meter `+0x56C` is.

The id 5/33 handler takes a different path — `0x020781E4`, branching on the **sign** of the amount (`cmp r1,#0` / `bge`) and reading a signed byte at `char+0x5CF`. Different object, different offset region. The two drain families don't even share an apply path.

## Queued by this wake

1. **Owner (`jus-law`):** what the `char+0x120` bitset is, given the branch name; and whether the 1-HP floor applies to *every* HP loss or only to DoT.
2. **Static:** identify `char+0x56C` — which meter it is, and whether a separate HP field exists with a clamp to 1. That settles the drain target properly instead of by elimination.
3. **Runtime, cheap:** with the gate known, an id-19 capture that also reads `char+0x120+8`'s two words says whether the target was gated. If the bit for `0x1D` is set, the `−4` was never applied and the HP-unchanged observation needs no other explanation.
