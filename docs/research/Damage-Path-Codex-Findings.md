# Damage path: static findings (Codex cross-check)

Produced by a Codex run on 2026-08-17, given the runtime results from this
session as calibration. Every claim below was decoded from **raw binary bytes**
with `llvm-mc --disassemble --triple=armv5te-none-eabi`, not from the stale
`ov6.txt` listing (which mis-decodes Thumb). Confidence is Codex's own.

## 1. The drain trampoline has exactly two callers

`0x020783B8` is the **negating** trampoline (`rsb r1,r1,#0` then tail-call to the
HP-apply function), i.e. the damage path. Confirmed with `scripts/find_callers.py`:

| caller | mode |
|---|---|
| `0x0215AC70` | ARM |
| `0x021518D6` | Thumb `blx` |

**Confidence: high.**

### Caller 1 — `0x0215AC70`, the pending-damage consumer, and it HALVES

```asm
0x0215AC00  ldr r1,[r5,#0x1a8]
0x0215AC04  ldr r1,[r1,#0x10]
0x0215AC08  ldr r4,[r1,#0x134]     ; pending damage magnitude
0x0215AC0C  bl  0x02159A10
0x0215AC10  cmp r0,#0
0x0215AC14  bne 0x0215AC28
0x0215AC18  mov r0,r5
0x0215AC1C  bl  0x021598D0
0x0215AC20  cmp r0,#0
0x0215AC24  beq 0x0215AC2C
0x0215AC28  asr r4,r4,#1           ; <-- HALVED when either predicate is true
...
0x0215AC68  ldr r0,[r5,#0x1b4]
0x0215AC6C  mov r1,r4
0x0215AC70  bl  0x020783B8
```

In C:

```c
r4 = obj->pending_damage;                       // obj+0x134
if (sub_02159A10(...) || sub_021598D0(r5))
    r4 >>= 1;                                   // halve
apply_drain(entity, r4);                        // negated inside
```

**A conditional halving sits on the damage path.** `0x02159A10` and `0x021598D0`
are unidentified predicates — guard state and/or a defensive status are the
obvious candidates. This is a *multiplicative* ×0.5 and is therefore a different
mechanism from the flat −2 measured for blunt resistance; both can coexist.

### Caller 2 — `0x021518D6`, a fixed 32-damage scripted path

```asm
0x021518CC  movs r0,#0x6d
0x021518CE  lsls r0,r0,#2        ; r0 = 0x1b4  (entity field offset)
0x021518D0  ldr  r0,[r1,r0]      ; target entity
0x021518D2  movs r1,#2
0x021518D4  lsls r1,r1,#10       ; r1 = 0x800 = 2048 raw = 32.0 displayed
0x021518D6  blx  0x020783B8
```

A hardcoded **32.0 displayed HP**, not table-derived and not read from `+0x134` —
a scripted or environmental damage source (stage hazard, ring-out, or similar).
Worth measuring at runtime: if anything ever deals exactly 32.0, this is it.

## 2. Ability `0x09` is cached as a BITSET at load — which explains our null result

This is the most useful part, because it gives a mechanism for a runtime negative
we could only bound empirically.

At character setup, `0x0215FAC4` walks the ability list and dispatches per ability
via `ability.bin`:

```asm
0x0215FAE4  ldrsb r4,[r6,#0xa]       ; ability count
0x0215FAFC  ldrsb r1,[r0,#0xb]       ; ability ID
0x0215FB00  ldr   r3,[r2,#0x50]      ; ability.bin data
0x0215FB08  ldrb  r2,[r3,r1,lsl #2]  ; handler class
0x0215FB14  blx   r2
```

The ordinary-ability handler `0x0215FB3C` caches the ID as a **bit**:

```asm
0x0215FB40  ldrb lr,[r1,#1]          ; ability ID
0x0215FB44  add  ip,r0,#8            ; -> entity+0x128
0x0215FB4C  asr  r3,lr,#5
0x0215FB50  ldr  r2,[ip,r3,lsl #2]
0x0215FB54  and  r0,lr,#0x1f
0x0215FB58  orr  r0,r2,r1,lsl r0
0x0215FB5C  str  r0,[ip,r3,lsl #2]   ; set bit (ID) in the cached word
```

`ability.bin` entry 9 (file offset `0x24`) is `00 09 00 00` — handler class 0. So
**ability `0x09` sets bit 9 (`0x200`) in the cached word at `entity + 0x128`.**

**This explains `HP-And-Damage-Runtime-Findings.md` §2c.** Rewriting a character's
visible ability array mid-battle changed damage by exactly zero because the
*bitset was already built at load*. The array is a source record; the bitset is
what runtime logic would consult.

### The experiment this unlocks

The attribution question — is the flat −2 caused by ability `0x09` or by some
per-character difference? — is now testable at runtime, which it previously was
not:

1. Locate the entity for a **blunt-resisting** target and read the word at
   `entity + 0x128`. Bit `0x200` should be set.
2. **Clear bit `0x200`** and re-measure the same move. If damage rises by exactly
   2.0 displayed (128 raw), the −2 is ability `0x09`.
3. Conversely, **set** bit `0x200` on the ability-free dummy (コマレッド,
   `chr_b[70]`) and confirm its damage taken drops by 2.0.

**Run 2026-08-17 — see `Ability-Bitset-Is-Not-Resistance.md`.** Steps 1 and 3
both came back negative. The bitset is exactly as described here (Goku reads
`0x00008080` for abilities `[7, 15]`), and it *is* consulted during combat —
setting bit 4, Auto-Guard, makes the target take zero damage. But bit `0x200` on
the ability-free dummy does not reduce blunt damage by 2.0, or by anything at
all, and neither do blunt weakness or slash resistance. The mechanism described
below is real; it just isn't where resistance is applied.

One correction: `entity + 0x56C = char_struct` does not hold as a subtraction —
it puts the opponent's entity inside the player's deck array. Derive the entity
as `char_struct = hp_block − 0x18`, then find the object holding a pointer to
`char_struct + 0x10`.

Either direction settles it. Note `entity` here is the object at
`char_struct − 0x56C`-ish level; use the resolved `r6`/entity chain from
`Nature-System-Consolidated.md` and the element work rather than assuming.

A separate load-time read exists in arm9 at `0x02077768`, which uses
`char+0x41` as the `chr_b` index, computes the 60-byte record, and iterates record
bytes `+3..+7` as ability IDs — i.e. abilities come from the `chr_b` source record
during construction.

## 3. Bounded negatives (both worth trusting)

**The writer of `obj+0x134` was not found.** All direct ARM `STR [Rn,#0x134]`
instructions in `arm9.bin` and ov06 were enumerated and rejected:

| candidate | why rejected |
|---|---|
| `0x0203AF20` | global init struct at `0x020A0C34`; stores `old \| 1` |
| `0x0207C744` | **vtable initialiser** — value is pool word `0x0207DE80`, a code address |
| `0x02161C2C` | **vtable initialiser** — value is `0x0207E5FC`, a code address |

The last two are exactly the trap the atlas session independently hit and
retracted — three independent arrivals at the same false positive.

Also a genuinely useful encoding fact: **Thumb-1 `STR (immediate)` cannot encode
offset `0x134`** (word offsets reach only `0x7C`), so a Thumb writer would need a
register offset or base adjustment. Codex scanned for those forms too and found
nothing in ov06. Remaining possibilities: a bulk copy loop, an indirect helper, or
a computed address. **Confidence: medium** — high that all *direct* ARM writers
were found, medium overall.

**The `−0x80` (flat −2) subtraction was not found.** Eliminated: the only ov06
`sub ...,#0x80` (`0x02168880`) is coordinate-delta squaring in `0x021686D8`, and
`0x0215AE6C`'s `sub r1,r1,#2` is a countdown timer on `entity+0x10E` after the
HP block. No damage-path read of `entity+0x128` testing bit `0x200` and
subtracting `0x80` was located.

## 4. What this changes about our model

- There is a **conditional ×0.5** on the damage path (`0x0215AC28`). Our flat −2
  finding stands, but damage is not a single flat pipeline — at least one
  multiplicative modifier exists, gated by two unidentified predicates.
- Resistance almost certainly reads the **cached bitset at `entity+0x128`**, not
  the ability array. That reframes every future poke experiment.
- The pending-damage field `+0x134` is read and conditionally halved *before*
  application, so the value we measured leaving `+0x134` (512) is pre-halving.
