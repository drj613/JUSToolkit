# P168 — Mode 12 stuck in state 1: a counter never finishes

**Iteration 168. Static, following the runtime loop's three-state observation.** The callback slot `[0x023DAC68+0x40]` walks `0x0214DAA5` → `0x0214DB21` → `0x0214DBCD`, and mode 12 never leaves state 1. Task: read state 1, find what blocks the advance.

Found. The chain bottoms out at an arm9 counter with a done-flag that never latches.

## State 1 advances only on a non-zero return

`CONFIRMED_STATIC`. ov6 `0x0214DAA4`, full function:

```
0x0214DAA4: b510       push {r4, lr}
0x0214DAA6: 2100       mov  r1, #0
0x0214DAA8: 1c04       mov  r4, r0
0x0214DAAA: f000 f817  bl   0x0214DADC        ; (arg, 0)
0x0214DAAE: 2800       cmp  r0, #0
0x0214DAB0: d003       beq  0x0214DABA        ; zero -> return, slot unchanged
0x0214DAB2: 6860       ldr  r0, [r4, #4]
0x0214DAB4: 4901       ldr  r1, [pc, #4]      ; pool 0x0214DABC -> 0x0214DB21 (the poll)
0x0214DAB6: f6da ec66  blx  <arm>             ; register: (obj = [arg+4], fn = the poll)
0x0214DABA: bd10       pop  {r4, pc}
```

The slot rewrites to the poll only if `0x0214DADC` returns non-zero. Otherwise state 1 returns unchanged, and the arm9 dispatcher calls it again next tick. That matches the runtime picture exactly: mode 12 sits in state 1 the entire run.

`0x0214DADC` calls `blx 0x0207382C` first, then gates on `cmp r0,#0` / `beq` to its own return. Both levels key on the same thing: **what `0x0207382C` returns.**

## `0x0207382C` is a bound-method veneer that discards its argument

`CONFIRMED_STATIC`. This is the part worth reading carefully:

```
0x0207382C: ldr ip, [pc, #4]     ; -> 0x0207387C  (the function)
0x02073830: ldr r0, [pc, #4]     ; -> 0x0214BD50  (the object)
0x02073834: bx  ip
0x02073838: .word 0x0207387C
0x0207383C: .word 0x0214BD50
```

`ldr r0,[pc,#4]` overwrites `r0` unconditionally, so **the ov6 caller's argument is thrown away.** The check isn't a function of the battle object — it's a fixed query against the singleton at `0x0214BD50`. Reading the ov6 side alone would suggest otherwise. That's the trap.

Four identical veneers sit in a row (`0x0207382C`, `0x02073840`, `0x02073854`, `0x02073868`), all binding `0x0207387C` to different objects — `0x0214BD50`, `0x0214BD70`, `0x0214BD70`, `0x0214BD60`. Same method, four bound instances. Nearby: `0x0214BD80` is the battle resource manager singleton from the chrb-catalog work, so these share the same global table.

## The condition: a counter ticking by 4 until a shifted value hits `0x10`

`CONFIRMED_STATIC`. `0x0207387C`, with `r0` = `0x0214BD50`:

```
0x0207387C: push  {r3, lr}
0x02073880: ldrb  r1, [r0, #8]      ; the done flag
0x02073884: cmp   r1, #0
0x02073888: movne r0, #1
0x0207388C: popne {r3, pc}          ; already done -> return 1
0x02073890: ldrh  r1, [r0, #2]      ; counter
0x02073894: add   r1, r1, #4        ; += 4 per call
0x02073898: strh  r1, [r0, #2]
0x0207389C: ldrh  r2, [r0, #2]
0x020738A0: ldrb  r1, [r0, #1]      ; shift amount
0x020738A4: asr   r1, r2, r1
0x020738A8: lsl   r1, r1, #0x10
0x020738AC: lsr   r1, r1, #0x10     ; & 0xFFFF
0x020738B0: cmp   r1, #0x10
0x020738B4: movhs r1, #1
0x020738B8: strbhs r1, [r0, #8]     ; done flag = 1
```

Object fields at `0x0214BD50`:

| field | address | meaning |
|---|---|---|
| `+0x1` | `0x0214BD51` | shift amount (byte) |
| `+0x2` | `0x0214BD52` | counter (halfword), `+= 4` per call |
| `+0x8` | `0x0214BD58` | done flag (byte) |

Returns 1 once `+0x8` is set. Sets `+0x8` when `((counter + 4) >> shift) & 0xFFFF >= 0x10`. Since `ldrh` zero-extends, the `asr` acts as a logical shift here.

`PLAUSIBLE`, not claimed: this is a **fade or screen-transition progress object** — a counter stepped by a fixed amount per tick, a per-instance rate set by the shift, and a latch when it finishes. The four veneers would be four transition channels.

If that reading holds, mode 12 is one story, not three coincidences: the transition never completes → `0x0207387C` never returns 1 → state 1 never registers the rule poll → `root+0xC8` stays `0`. The runtime loop's mode-12 framebuffer was **nearly black** with no stage and no fighters — exactly what an unfinished fade-in looks like. The black screen isn't a separate symptom; it's the same fact as the missing handler.

## Codex got one operand wrong; the bits settled it

Codex was given fragments A and B as raw hex — no addresses, no hypothesis. It matched every byte width, every base-register offset, the early-return condition, and the masking effect of the `lsl`/`lsr` pair. It independently noted that `ldrh` zero-extending makes the `asr` act as a logical shift.

It then decoded `0x020738B0` as `cmp r0, #16` instead of `cmp r1, #0x10`. The encoding is `E3510010`: bits 19–16 are `0001`, so `Rn` = `r1`. `query.py` agrees. Two representations against one — and there's a coherence check: under Codex's reading, `r0` is a pointer (always ≥ 16), so the conditional store would fire every time and the comparison would be dead code.

Same failure mode as P158's `mla` operand swap. **When Codex disagrees on a decode, go to the bits.** That rule has now paid twice.

## Queued

1. **Runtime, sharp:** watch `0x0214BD52` (counter), `0x0214BD51` (shift), and `0x0214BD58` (done flag) across a mode-2 battle and a mode-12 battle. Mode 2 should show the counter advancing and the flag latching to `1` right before the slot moves to the poll; mode 12 should show it stuck. Tests the whole chain in one capture.
2. **Static:** identify what `0x0214BD50` is and who resets its counter — names the transition and explains why mode 12's never finishes.
3. Unchanged: `root+0x08`'s writer, `root+0x118`/`+0x11C`'s writer, `root+0x4C`'s writer (term `V`).
