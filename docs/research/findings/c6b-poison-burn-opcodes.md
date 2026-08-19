Let me read the document to make sure I have it all.

I'll rewrite it now.

---

# C6b — the "damage" sites are poison and burn ticks

Loop-Atlas iteration 21. Static analysis on raw `ov06.bin` bytes.

**Those record-reading damage sites are damage-over-time status ticks, not melee hits.** That answers what those handlers do — and means melee damage lives somewhere else entirely.

## The script-opcode handler family

`ov06` has a family of nine handlers that share one prologue shape: `push {...}`, `mov r2,#ID`, then a validator call to `0x0215986C`.

| opcode | handler | status (from `ability_t.bin` immunity entry at the same index) | applies HP damage |
|---|---|---|---|
| `0x19` | `0x02159694` | 帯電無効 shock | |
| `0x1A` | `0x02159678` | 氷結無効 freeze | |
| `0x1B` | `0x02159624` | 燃え無効 burn | **YES** |
| `0x1C` | `0x02159538` | 混乱無効 confusion | |
| `0x1D` | `0x02159500` | 毒無効 poison | **YES** |
| `0x1E` | `0x02159594` | 宣告無効 judgment | |
| `0x1F` | `0x021594E4` | 行動不能無効 paralysis | |
| `0x20` | *not found* | 画面妨害無効 blindness | |
| `0x21` | `0x02159578` | スピードダウン無効 speed-down | |
| `0x22` | `0x02159608` | チェンジ封印無効 seal | |

**The opcode IDs are the status-effect enum `0x19`–`0x22` exactly.** Only two handlers touch HP: `0x1B` burn and `0x1D` poison — the two damage-over-time statuses. Everything else leaves HP alone.

This is a strong confirmation because nothing was fitted after the fact. The `0x19`–`0x22` range came from `Cheat-Code-Analysis.md`'s ability IDs weeks earlier, and the handler IDs landed in the same range on their own.

**One ID space works both ways:** status effect `N` is applied by opcode `N`, and ability `N` grants immunity to status `N`. Clean design, and useful for the rest of the engine.

## The poison/burn handler, fully read

```asm
0x02159500  push {r3,r4,r5,lr}
0x02159504  mov   r2,#0x1D          ; opcode = poison
0x02159508  mov   r5,r0             ; arg0 = context
0x0215950C  mov   r4,r1             ; arg1 = script node
0x02159510  bl    0x0215986C        ; validator
0x02159514  cmp   r0,#0
0x02159518  movne r0,#0x0
0x0215951C  popne {r3,r4,r5,pc}     ; bail if it didn't apply
0x02159520  ldr   r1,[r4,#0x4]      ; r1 = node->[4]  = effect record
0x02159524  ldr   r0,[r5,#0x1B4]    ; r0 = target character
0x02159528  ldrsh r1,[r1,#0x4]      ; delta = SIGNED HALFWORD at record+4
0x0215952C  bl    0x020783CC        ; apply
0x02159530  mov   r0,#0x1
0x02159534  pop   {r3,r4,r5,pc}
```

The tick damage is a **signed halfword at offset `+4` of a record reached via script-node `+4`**. Signed matters — the same field can express a heal.

`0x02159668` (opcode `0x1B`, burn) has the same shape.

## Self-correction

I'd been treating all eight ARM callers as "the damage pipeline" and hunting for melee there. Two of them are status ticks. Combined with C3 (all six Thumb callers are heals), the full picture so far:

- 6 Thumb callers — heals (regen, full heal)
- 2 ARM callers — poison and burn ticks, value from an effect record
- 6 ARM callers — still unclassified

**No melee damage has been found among any caller identified so far.** The harness session measured hits of `192` and `2304` raw, and where those come from is still unknown.

## What I didn't establish

Two other sites read the same `ldrsh …,#4` record shape — `0x02159274` and `0x021592D0` — but they sit in functions my prologue scan didn't classify, so I can't name their opcodes. They might be a sibling family (different target, or SP instead of HP). Not claimed.

I also can't tabulate poison/burn values offline yet. The record is reached through a **script node**, so the numbers live in move/effect script data rather than a flat table in `bin/`. Finding where those scripts are parsed would be the next step if the numbers are needed.

## Next

1. Classify the remaining 6 ARM callers — melee is either among them or not a caller of this function at all.
2. If melee isn't there, the harness session's bypass reading is right and melee writes HP directly. The discriminating scan is the one flagged in C3: filter `strh [Rn,#0x18]` writers by proximity to a `+0x16` (max HP) read for clamping.
