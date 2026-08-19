# P174 — The effect tick driver, the faster-decay gate, and a third read of the ability bitset

**Iteration 174. Static.** Goal: find the per-frame driver that calls `node+0x0`. It was the last unexamined link on the DoT path.

Turns out it's not a separate function. **`0x02158B20` — the function P159 called "the on-hit flush" — is the per-character effect update.** The tick loop is its second half.

## The driver

`CONFIRMED_STATIC`. ov6 `0x02158B20`, 876 bytes. First half: the Route B flush from P159. Second half: ticks both effect slots.

```
0x02158C68: add   sb, sl, #0x7c      ; sb = node[0]; sl = battleObj
0x02158C6C: mov   r8, #0             ; slot index
0x02158C70: mov   r7, #0xf
0x02158C74: mov   fp, #2
0x02158C78: ldrh  r0, [sb, #0xe]     ; duration
0x02158C7C: cmp   r0, #0
0x02158C80: beq   0x2158d54          ; zero -> skip this slot
0x02158C84: sub   r0, r0, #1
0x02158C88: strh  r0, [sb, #0xe]     ; *** THE DECREMENT — 1 per tick ***
...
0x02158CE4: ldr   r2, [sb]           ; node+0x0 = the handler
0x02158CE8: mov   r0, sl             ; battleObj
0x02158CEC: mov   r1, sb             ; node
0x02158CF0: blx   r2                 ; *** THE PER-FRAME TICK CALL ***
0x02158CF4: ldrh  r0, [sb, #0xe]
0x02158CF8: cmp   r0, #0
0x02158CFC: bne   0x2158d10
0x02158D00: mov   r0, sl
0x02158D04: mov   r1, r8             ; slot index
0x02158D08: str   r6, [sb]           ; on expiry: node+0x0 = the stub
0x02158D0C: bl    0x215911c          ; expiry handler(battleObj, slot)
...
0x02158D54: add   r8, r8, #1
0x02158D58: cmp   r8, #2
0x02158D5C: add   sb, sb, #0x18
0x02158D60: blt   0x2158c78          ; exactly 2 slots, stride 0x18
```

Key facts: **`node+0xE` is decremented by the driver, one per tick** — no handler does this. The handler gets called with `(battleObj, node)`, same signature as the dispatcher's apply-time call. When duration hits zero *after* the handler runs, the driver installs the stub and calls the expiry path `0x0215911C(battleObj, slot)`. The slot loop confirms P158's two-slot layout at stride `0x18` from a second angle — the loop bound, not the apply arithmetic.

## Flags bit `0x20`: a faster-decay gate that reads the ability bitset

`CONFIRMED_STATIC`. Closes a `not claimed` from P169.

```
0x02158C8C: ldr   r0, [sb, #4]       ; paramArray[id]
0x02158C90: ldrh  r0, [r0]           ; the flags halfword
0x02158C94: tst   r0, #0x20          ; <- flags bit 0x20
0x02158C98: ldrhne r0, [sb, #0xe]
0x02158C9C: cmpne r0, #0
0x02158CA0: beq   0x2158ce4
0x02158CA4: tst   r0, #1             ; duration ODD?
0x02158CA8: beq   0x2158ce4
0x02158CAC: ldr   r0, [sl, #0x128]   ; *** the ability bitset ***
0x02158CB0: tst   r0, #0x100         ; ability bit 8
0x02158CB4: ldrhne r0, [sb, #0xe]
0x02158CB8: subne r0, r0, #1
0x02158CBC: strhne r0, [sb, #0xe]    ; extra decrement
0x02158CC0: bne   0x2158ce4
0x02158CC4: mov   r1, r7             ; 0xF
0x02158CC8: mov   r2, fp             ; 2
0x02158CCC: add   r0, sl, #0x1c
0x02158CD0: bl    0x21613c4
0x02158CD4: cmp   r0, #0
0x02158CD8: ldrhne r0, [sb, #0xe]
0x02158CDC: subne r0, r0, #1
0x02158CE0: strhne r0, [sb, #0xe]    ; another extra decrement
```

`flags & 0x20` marks effects whose duration **can drain faster than one per tick**. On odd durations, an extra decrement fires if **ability bit 8** is set on the afflicted character; failing that, a fallback through `0x021613C4(battleObj+0x1C, 0xF, 2)` can also grant one. From `state.bin`, `flags & 0x20` is set on ids 18, 19, 26, 27, 30, 31, 32, 34 — drains and several statuses, exactly the set a "shake it off" ability would target.

## The ability bitset is a behaviour switchboard

`CONFIRMED_STATIC`. The bitset at `battleObj+0x128` is now read from three places with three unrelated effects:

| site | bit | effect |
|---|---|---|
| cancel gate `0x02158EB0` | bit = the status **opcode** | a set bit cancels the effect outright |
| tick driver `0x02158CB0` | **bit 8** | statuses decay ~twice as fast |
| tick driver `0x02158D78` | **bit 14** (`tst r1, #0x4000`) | tested against a value built from `battleObj+0xBC` and `+0xBE` |

Not a resistance field. Not an immunity field. It's a **general per-ability behaviour switchboard** — each bit means whatever its ability means, read all over the effect update. This matches what the owner's branch name asserts, arrived at from a third independent direction. Bit 14 is **set on the opponent** in the runtime loop's capture (`0x02005200` = bits 9, 12, 14, 25), so that path is live in ordinary play.

## This also explains 15,732 empty dispatches

The runtime loop once breakpointed the dispatcher unconditionally and caught **15,732 calls, every one at id 0**, hitting both Route B flush sites. At the time we inferred "the flush runs per-frame with nothing staged." Now it's structural: the flush and the tick are **the same function**, so the flush runs on every character update whether or not anything is staged. That throwaway number was measuring exactly this.

**This corrects P159's framing.** Calling `0x02158B20` "the on-hit apply function" describes what its first half does when something is staged, not what the function is. It's the per-character effect update. `Battle_CharaCreate` loads `0x02156DDC` from its literal pool at `0x02156D64` and installs it; `0x02156DDC` calls `0x02158B20` at `0x02156E94`. Same architecture as the rule handler at `root+0x000` — a per-character callback, installed at construction, driven from outside.

## Still not found

`not claimed`: the owner's 1-HP floor. The driver never touches HP. The entire DoT path is now mapped — dispatcher, drain handlers, apply worker, tick driver — and **no clamp to 1 exists anywhere on it**. Remaining candidates: the KO check ignores HP reaching zero by drain, or the floor lives on the KO path rather than the damage path. Different subsystem, fresh task.

## Queued by this wake

1. **Runtime, cheap and falsifiable:** set **ability bit 8** on a character with an active timed status and watch `node+0xE`. Duration should fall roughly twice as fast on odd values. New bit, new predicted behaviour, existing poke tooling — and it tests the bitset identity a fourth time from a direction unrelated to Auto-Guard.
2. **Static:** the KO path, for the 1-HP floor.
3. **Static:** `0x0215911C`, the expiry handler — the last unread function on the effect lifecycle.
