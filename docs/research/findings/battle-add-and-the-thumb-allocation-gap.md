# Findings: ov6's entry point is `Battle_Add` — and the allocation census was ARM-only

Loop-Atlas iteration 98. Static.

The Thumb function at **`0x0214CD20`** — ov6's entry point — is **`Battle_Add`** in
**`Battle.cpp`**, tagged by its allocation call.

That call is a Thumb `blx`, which exposed an ARM-only blind spot in `alloc_census.py`:
494 ARM calls seen, **238 Thumb calls missed** — **32%** of the ROM's allocations.

Battle conclusions that depend on the census were re-checked and hold.

---

## 1. `Battle_Add`

```
0x0214CD20  b5f8       push {r3, r4, r5, r6, r7, lr}
0x0214CD22  b0aa       sub sp, #0xa8
...
0x0214CD5C  2017       mov r0, #0x17
0x0214CD62  0100       lsl r0, r0, #4          ; size = 0x170
0x0214CD5E  49b8       ldr r1, [pc, #0x2e0]    ; "Battle.cpp"
0x0214CD60  4ab8       ldr r2, [pc, #0x2e0]    ; "Battle_Add"
0x0214CD64  237f       mov r3, #0x7f
0x0214CD66  f6cd ea5a  blx #0x0201a21c
0x0214CD6E  6008       str r0, [r1, #0x0]      ; -> the global at 0x02172960
```

`0xA8` of locals accommodates the `sp+0x48` descriptor from iteration 97. The result is
stored to **`0x02172960`** — ov6's end address, the overlay's first BSS word, the module's
root object.

`Battle_Add` is the overlay's constructor; it creates battle characters in a loop during setup.

## 2. The census gap

Thumb `blx` calls to `0x0201A21C`, by region:

| region | calls |
|---|---|
| ov12 | 100 |
| ov1 | 70 |
| arm9 | 35 |
| ov7 | 24 |
| ov4 | 5 |
| **ov6** | **3** |
| ov5 | 1 |
| **total** | **238** |

`bl` is excluded — it cannot reach an ARM target (iteration 96).

## 3. The battle findings survive

ov6's three Thumb allocations, in full:

| site | size | function | file |
|---|---|---|---|
| `0x0214CD66` | `0x170` | `Battle_Add` | `Battle.cpp` |
| `0x02150FAE` | `0x40` | `Battle_TutorialCreate` | `BattleTutorial.cpp` |
| `0x02153F7C` | `0xD4` | `Battle_WindowCreate` | `BattleWindow.cpp` |

All named, all small, **none ≥ `0x570`**. Iteration 95's finding — the `≥0x5F1` struct at
`[char+0x1b4]` is not tagged-allocated — holds. Iteration 73's `Battle_CharaCreate`
identification from its tag is unaffected.

arm9's 28 Thumb allocations in the battle address range are all comms code —
`CommLib.cpp`, `CommWrap.cpp`, `CommGame.cpp`, `ALObjectImp.h`. None falls in the
collision engine's `0x0207A000`–`0x02085000`.

**Caveat on arm9 sizes:** several resolve to `0x214BE40` (a RAM address, not a size).
The back-resolver does not invalidate registers across calls, so it picked up an unrelated
`ldr r0,[pc,…]`. The ov6 three were verified against disassembly; arm9 sizes should not
be quoted.

## Predictions status

| Claim | Verdict |
|---|---|
| The Thumb setup function starts at ov6's entry point `0x0214CD20` | **CONFIRMED_STATIC** — the only `push {…,lr}` in `0x0214CD20`–`0x0214D5C4`, with `sub sp,#0xa8` |
| It is `Battle_Add` in `Battle.cpp`, allocating `0x170` | **CONFIRMED_STATIC** — call-site tag at `0x0214CD66` |
| Its object is stored at `0x02172960` | **CONFIRMED_STATIC** — `str r0,[r1,#0x0]` at `0x0214CD6E`, `r1` = `[0x0214D048]` = `0x02172960` |
| `0x02172960` is ov6's first BSS word | **CONFIRMED_STATIC** — ov6 spans `0x0214CD20`–`0x02172960` |
| `alloc_census.py` sees every allocation | **REFUTED** — 238 Thumb calls unseen against 494 ARM, 32% of the total |
| ov6 has Thumb allocations the census missed | **CONFIRMED_STATIC** — three: `0x170`, `0x40`, `0xD4` |
| One of them is the `≥0x5F1` struct | **REFUTED** — all three are named and none reaches `0x570` |
| Iteration 73's `Battle_CharaCreate` naming is affected | **REFUTED** — that site is an ARM `bl`, and no Thumb site competes with it |
| The arm9 Thumb allocation sizes reported here are reliable | **not claimed** — several decode to `0x214BE40`, an address; the back-resolver does not invalidate registers across calls |

## Next angles, ranked

1. **Extend `alloc_census.py` to Thumb** with register-invalidating back-resolver.
   238 sites, currently unnamed.
2. **Read `Battle_Add` whole** — the overlay constructor that builds every argument for
   battle character creation. `0x170` bytes of root object to map.
3. **Identify `0x02173004` and `0x02173014`** (carried) — they fill descriptor `+0x08` and
   `+0x0C`.
4. **Read `char+0x7c`'s users** `0x02158B20`, `0x021586D0` (carried).
