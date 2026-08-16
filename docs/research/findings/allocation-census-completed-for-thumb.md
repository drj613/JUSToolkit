# Findings: the allocation census now covers Thumb — 732 sites, not 494

Loop-Atlas iteration 99. Static.

`alloc_census.py` counted ARM `bl` only. It now scans Thumb `blx` too: **732 call
sites** (494 ARM + 238 Thumb), **640** with a resolved size, **670** with a resolved name.

The iteration-98 scratch scan reported `0x214BE40` — a RAM address — as an allocation
size. The committed resolver invalidates registers and the selftest rejects implausible sizes.

With full coverage, the battle conclusions hold: **no allocation of `0x570` or more
belongs to the battle engine.**

---

## 1. Two resolver bugs, both producing confident wrong output

**Calls clobber argument registers.** `r0`–`r3`, `ip` and `lr` are now dropped at every
`bl`/`blx` in the back-scan window.

**Memory loads are writes.** The bug that produced the fake size:

```
0x02088A28  8a20   ldrh r0, [r4, #0x10]
```

A stale `ldr r0,[pc,…]` survived past this instruction, so `0x214BE40` was reported as a
size. The resolver now treats every Thumb load form as an opaque write — register-offset,
`imm5` word/byte, `imm5` halfword, sp-relative, and `ldmia`'s whole register list.

The selftest asserts `Battle_Add` resolves to `0x170` and fails on any Thumb size above
`0x100000`.

## 2. A swallowed error

The Thumb pass returned zero sites. The cause:

```python
try:
    words, base = SF.load(region)
except Exception:
    continue
```

`struct_fields` was not imported, and the bare `except` turned a `NameError` into "no
binary" for all sixteen regions — same shape as this campaign's mask bugs: a clean,
plausible, empty result instead of a failure. Narrowed to `(FileNotFoundError,
StopIteration)`.

## 3. The battle findings survive

Every allocation `≥ 0x300`, ROM-wide, both instruction sets:

| size | site | isa | function | file |
|---|---|---|---|---|
| `0x7560` | arm9 `0x02072900` | thumb | `RecordLoad` | `Record.cpp` |
| `0x4000` | ov12 `0x021CA45C` | arm | — | `ALTextDS.cpp` |
| `0x2000` | ov12 `0x021CA488` | arm | — | `ALTextDS.cpp` |
| `0x2000` | arm9 `0x02088FC6` | thumb | `CommLibInit` | `CommLib.cpp` |
| `0x1980` | ov12 `0x021CC2A8` | thumb | `WiFiVC_Proc_Init` | `WiFiVoiceChat.cpp` |
| `0x1040` | arm9 `0x0207BD5C` | arm | `Battle_ColJointManCreate` | `BattleColJoint.cpp` |
| `0xF00` | arm9 `0x02088F84` | thumb | `CommLibInit` | `CommLib.cpp` |
| `0x880` | ov12 `0x021CC294` | thumb | `WiFiVC_Proc_Init` | `WiFiVoiceChat.cpp` |
| `0x710` | ov7 `0x0215198A` | thumb | `CommuMenuFrndList_Add` | `CommuMenuFrndList.cpp` |
| `0x400` | arm9 `0x02088FB0` | thumb | `CommLibInit` | `CommLib.cpp` |
| `0x400` | ov12 `0x021CB6AE` | thumb | `InitHash` | `ALFont.cpp` |
| `0x3E8` | ov5 `0x0215F42C` | thumb | `Input_Add` | `Input.cpp` |
| `0x314` | ov6 `0x02168BA0` | arm | `Battle_ObjCtrlManCreate` | `BattleObjCtrl.cpp` |

Above `0x570`: text rendering, comms, WiFi voice chat, the friend list, fonts, and
`Battle_ColJointManCreate`. **Nothing that could be the `≥0x5F1` struct at
`[char+0x1b4]`.** Iteration 95's finding now rests on a complete census.

`RecordLoad` at `0x7560` is the ROM's largest single allocation — invisible before this wake.

## Predictions status

| Claim | Verdict |
|---|---|
| The census covers every allocator call | **REFUTED** *(as it stood)* — 238 Thumb sites were unseen; now 732 total |
| A back-resolver can ignore memory loads | **REFUTED** — `ldrh r0,[r4,#0x10]` at `0x02088A28` left a stale value that became a fake `0x214BE40` size |
| `Battle_Add` resolves to `0x170` under the committed resolver | **CONFIRMED_STATIC** — selftest assertion |
| No Thumb site reports an implausible size | **CONFIRMED_STATIC** — selftest rejects anything above `0x100000`; none remain |
| A bare `except Exception` is safe around a loader | **REFUTED** — it turned a `NameError` into an empty result for all 16 regions |
| Some allocation ≥ `0x570` is the `[char+0x1b4]` struct | **REFUTED** — all 12 are text, comms, WiFi, fonts, input, or ColJoint |
| Iteration 95's "not tagged-allocated" holds under full coverage | **CONFIRMED_STATIC** — complete ARM + Thumb census |
| The 92 unresolved sites hide a large battle allocation | **not claimed** — they are unresolved, not shown to be small |

## Next angles, ranked

1. **Read `Battle_Add` whole** (carried) — ov6's constructor, a `0x170` root object at
   `[0x02172960]`, and it builds every argument the battle characters get.
2. **Identify `0x02173004` and `0x02173014`** (carried) — they fill chara descriptor
   `+0x08` and `+0x0C`.
3. **Read `char+0x7c`'s users** `0x02158B20`, `0x021586D0` (carried).
4. **Map `BattleCol.cpp`** (carried).
