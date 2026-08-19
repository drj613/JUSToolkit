# Findings: the slot-arm function, its data table, and no reachable caller

Loop-Atlas iteration 92. Static.

`0x0215FC20` **arms a slot**: sets the enable bit and fills both `int16[16]` arrays from
a `4`-byte-per-entry table behind a previously unseen global.

It has **no reachable caller** — its only literal sits in a trampoline nothing references.

That alone doesn't prove the table dead. A companion-filtered search over 93 `+0xc`
writers found one strong hit, but it **clears** the mask, not sets it. Stated as open.

---

## 1. Arming a slot

```
0x0215FC20  push {r3, lr}
0x0215FC24  ldr  r2, [r0, #0xc]        ; the enable mask
0x0215FC2C  tst  r2, r3, lsl r1
0x0215FC30  popne {r3, pc}             ; already armed -> idempotent, do nothing
0x0215FC34  orr  r3, r2, r3, lsl r1
0x0215FC3C  str  r3, [r0, #0xc]        ; set bit N
0x0215FC38  ldr  r2, [pc, #0x34]       ; -> 0x02172984
0x0215FC40  ldr  r3, [r2]
0x0215FC48  ldr  ip, [r3, #0xc]        ; the parameter table
0x0215FC44  lsl  lr, r1, #2            ; N * 4
0x0215FC4C  add  r3, r0, r1, lsl #1    ; view + N*2
0x0215FC50  ldrh r0, [ip, lr]          ; entry.u16 @ +0
0x0215FC54  lsl  r0, r0, #8            ; scale by 256
0x0215FC58  strh r0, [r3, #0x16]       ; arr16[N]
0x0215FC5C  ldr  r0, [r2]
0x0215FC64  add  r0, r0, r1, lsl #2
0x0215FC68  ldrh r0, [r0, #2]          ; entry.u16 @ +2
0x0215FC6C  strh r0, [r3, #0x36]       ; arr36[N]
```

Each slot's two parameters come from one `4`-byte entry `{u16 a, u16 b}`:
`arr16[N] = a << 8`, `arr36[N] = b` unscaled. The `<< 8` is fixed-point (8 fractional
bits), consistent with the engine's scaled-integer convention.

Table is `[[0x02172984] + 0xC]`. That global has 11 literal loads in ov6, including
`0x02158EE0` and four sites in `0x021614C8`–`0x02161530`.

## 2. No reachable caller

`query.py xrefs-to 0x0215FC20` reports **0 references**. A raw word scan of all 16
regions finds exactly **one** occurrence — `0x0215FB74`, a literal pool word — so the
xref database missed it.

The trampoline:

```
0x0215FB64  ldr  ip, [pc, #8]      ; -> 0x0215FC20
0x0215FB68  ldrb r1, [r1, #1]      ; selector = descriptor->byte[1]
0x0215FB6C  ldr  r0, [r0]
0x0215FB70  bx   ip
```

`0x0215FB64` itself has **0 references** — no `bl`, no literal load, not in the handler
table. Chain: arm ← trampoline ← nothing.

## 3. What I did not conclude

If no mask bit is ever set, all twelve live handlers and the whole table are dead. I
tried to establish this and could not.

**93** direct writers of `+0xc` exist in ov6. Companion-filtering leaves a handful; the
strongest — `0x0215FC08` inside `0x0215FB88`, six view companions — writes `r3`, which
`0x0215FB8C` sets to `0`. It **clears** the mask.

That function is the view's reset: `+0x5A`→`+0x56` and `+0x5C`→`+0x58` snapshots,
`+0x0C = 0`, `+0x10 = 0`, `+0x12 = 0x1B0`. Reachable, called from `0x0215FAC4`.

`+0x12` is initialised to exactly the cap slot 15 compares against, so that slot's `bhs`
takes the skip branch from the start.

Companion-filtering over 93 sites is not exhaustive, and `+0xc` is too common to scope
by address. **Whether any reachable code sets a mask bit is open.**

## Predictions status

| Claim | Verdict |
|---|---|
| `0x0215FC20` arms a slot: sets the mask bit and fills both arrays | **CONFIRMED_STATIC** — `orr`/`str` at `0x0215FC34`–`0x0215FC3C`, `strh` at `0x0215FC58` and `0x0215FC6C` |
| Arming is idempotent | **CONFIRMED_STATIC** — `tst`; `popne` at `0x0215FC2C`–`0x0215FC30` |
| Both parameters come from one `4`-byte entry at `[[0x02172984]+0xC]` | **CONFIRMED_STATIC** — `lsl lr,r1,#2`; `ldrh [ip,lr]`; `ldrh [r0,#2]` |
| `arr16[N]` is scaled by 256 | **CONFIRMED_STATIC** — `lsl r0, r0, #8` at `0x0215FC54` |
| `0x0215FC20` has no reachable caller | **CONFIRMED_STATIC** — one raw literal ROM-wide, in a trampoline with 0 references |
| `query.py xrefs-to` finds every literal load | **REFUTED** — it reported 0 for `0x0215FC20`; a raw word scan found the pool entry |
| `0x0215FC08` sets mask bits | **REFUTED** — it writes `r3 = 0`, clearing the mask |
| `0x0215FB88` is the view's reset | **CONFIRMED_STATIC** — mask `= 0`, `+0x10 = 0`, `+0x12 = 0x1B0`, plus the `+0x56`/`+0x58` snapshots |
| The handler table is dead because nothing arms a slot | **not claimed** — 93 `+0xc` writers in ov6, only companion-filtered; not exhaustive |

## Next angles, ranked

1. **Settle whether any mask bit is ever set.** Find every write of `+0xc` whose base
   provably reaches `char+0x130`, not just companion-filtered. Decides whether twelve
   handlers matter at all.
2. **Read the table at `[[0x02172984]+0xC]`** — 16 entries of `{u16, u16}`, the full
   effect parameters.
3. **Identify `0x02172984`** — new global, 11 literal loads in ov6.
4. **Fix xref literal-load coverage** — it missed a pool entry a four-line raw scan found.
