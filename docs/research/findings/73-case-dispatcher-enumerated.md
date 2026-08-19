# Findings: the 73-case character dispatcher, enumerated

Loop-Atlas iteration 46. Static.

Full case-by-case map of the dispatcher at ov6 `0x02157A60` (`BattleChara.cpp`).
**33 of 73 cases are live; 40 return immediately.** The 33 live cases reach 20 distinct callees.

Key result: **cases 23, 24 and 32 call the HP and SP apply functions tracked since early iterations.** HP/SP changes are reachable as *numbered commands* on this dispatcher — new architectural context for the damage pipeline.

---

## 1. Exact structure, correcting iteration 45

```
0x02157A5C  cmp r2, #72
0x02157A60  addls pc, pc, r2, lsl #2      ; pc becomes 0x02157A68
0x02157A64  b 0x02157F90                  ; out-of-range default (r2 > 72)
0x02157A68  ...                           ; case 0
0x02157B88  ...                           ; case 72
```

Iteration 45 said "74-entry branch table at `0x02157A64`–`0x02157B88`" — off by one. It miscounted the default branch as a table entry. The table is **`0x02157A68`–`0x02157B88`, 73 entries** (cases 0–72), all valid branches. `0x02157A64` is the out-of-range path, reached because `add pc` is `ls`-conditional.

Epilogue: `0x02157F90 mov r0,#0` / `0x02157F94 add sp,sp,#0xc` / `0x02157F98 pop {r3,r4,r5,r6,pc}`.
Branch to `0x02157F90` returns 0; branch to `0x02157F94` returns whatever is in `r0`.

## 2. A BL-decoding bug in my own scan

First enumeration reported **zero callees** across all 73 cases — contradicting a manual disassembly from last wake that clearly showed `bl #0x216fa9c` in case 25.

Cause: mask `(x & 0x0F000000) == 0x0A000000` matches `B` (opcode `0xA`) but **never matches `BL`** (opcode `0xB`). Fix: `(x & 0x0E000000) == 0x0A000000`, then bit 24 distinguishes the two.

Only caught because a previous wake's manual read contradicted the scan. The failure was silent and self-consistent — every case looked call-free.

## 3. The live cases

| case | target | callee(s) | module of callee |
|---|---|---|---|
| 1 | `0x02157B8C` | — | |
| 2 | `0x02157BB0` | `0x02158470` | `BattleChara.cpp` |
| 3 | `0x02157BE4` | `0x0215857C` | `BattleChara.cpp` |
| 4 | `0x02157BEC` | `0x0206C650` | arm9 |
| 5 | `0x02157BF8` | `0x0206C760` | arm9 |
| 6 | `0x02157C04` | `0x0215793C`, **`0x02083950`** | `BattleChara.cpp`, **arm9 `BattleObj.cpp`** |
| 7 | `0x02157C30` | — | |
| 8 | `0x02157C38` | — | |
| 9 | `0x02157C4C` | `0x0215C034` | `BattleChara.cpp` |
| 10 | `0x02157C5C` | `0x02158ED0` | `BattleChara.cpp` |
| 11 | `0x02157C74` | `0x021585D4` | `BattleChara.cpp` |
| 12 | `0x02157C98` | `0x02157FB0`, `0x02157FD8` | `BattleChara.cpp` |
| 13 | `0x02157CF4` | `0x021617A0` | `BattleCharaPursuer.cpp` |
| 14 | `0x02157D08` | `0x0216186C` | `BattleCharaPursuer.cpp` |
| 17 | `0x02157D2C` | — | |
| 18 | `0x02157D38` | `0x02078660` | arm9 |
| 19 | `0x02157D70` | `0x02078618` | arm9 |
| 20 | `0x02157D7C` | `0x0216650C` | `BattleMapItem.cpp` |
| 21 | `0x02157B98` | — | |
| 22 | `0x02157D90` | `0x0215A968` | `BattleChara.cpp` |
| **23** | `0x02157DB8` | **`0x020783CC`** | arm9 — **the HP-apply trampoline** |
| **24** | `0x02157DC8` | **`0x020781E4`** | arm9 — **the SP apply** |
| 25 | `0x02157DD8` | — (reads `[r0,#0x84]`) | |
| 26 | `0x02157DF0` | — (reads `[r0,#0x84]`) | |
| 29 | `0x02157BA4` | — | |
| **32** | `0x02157E04` | **`0x020783DC`** | arm9 — HP-apply sibling |
| 33 | `0x02157E14` | — (reads `[r0,#0x84]`) | |
| 65 | `0x02157E50` | `0x0215793C` | `BattleChara.cpp` |
| 66 | `0x02157E68` | — | |
| 67 | `0x02157E84` | — | |
| 69 | `0x02157F30` | — | |
| 71 | `0x02157EC4` | — | |
| 72 | `0x02157F50` | — (reads `[r0,#0x84]`) | |

### The damage-pipeline link

`0x020783CC` (HP trampoline, 14 known callers) and `0x020781E4` (SP apply, 19 known callers) are long-standing campaign landmarks. **Cases 23, 24 and 32 show these are invoked as numbered dispatcher commands.**

This doesn't add a new caller — `0x02157DB8` is almost certainly among the 8 ARM script-effect sites already counted. What it adds is *how* they're reached: a script issues command 23 for HP, 24 for SP. That reframes who computes the delta (campaign item B11): the delta arrives as an argument to the command, so the producer is whoever fills in those arguments, not this dispatcher.

Cases 18 and 19 call `0x02078660` and `0x02078618`, in the same arm9 neighbourhood as the HP functions — plausibly related, unverified.

Case 6 calls `0x02083950`, inside `BattleObj.cpp`'s `[0x02083204, 0x02083FCC)` range — the generic object pool from iteration 42. One command touches entity-pool machinery.

## 4. REFUTED: the dispatchers do not split a shared command enum

The 40 no-op cases form bands: **`0`, `15-16`, `27-28`, `30-31`, `34-64`, `68`, `70`**. The `34-64` band — 31 consecutive dead cases — suggested a shared command enum where other dispatchers handle the middle range.

Tested against the 13-way switch (dispatcher at `0x021574E4`, function at `0x021574CC`, `Battle-Engine-Map.md` claim 3). Its live cases are **1, 2, 4, 6, 7, 8, 9, 10, 11, 12** — all low, **zero** overlap with `34-64`.

The two switches don't partition one enum. The `34-64` band stays unexplained: reserved space, removed features, or mode-specific commands.

ov6 has **15** `add pc,pc,Rm,lsl#2` dispatchers total, case counts 4, 5, 5, 5, 5, 5, 7, 7, 7, 9, 13, 14, 32, 73 — heavily table-driven, consistent with iteration 45's conclusion that static pattern-matching can't span its access paths.

## Predictions status

| Claim | Verdict |
|---|---|
| The branch table is `0x02157A68`–`0x02157B88`, 73 entries | **CONFIRMED_STATIC** — all 73 decode as branches; `0x02157A64` is the default |
| Iteration 45's "74-entry table at `0x02157A64`" | **corrected** — off by one, default branch miscounted |
| 33 of 73 cases are live, reaching 20 distinct callees | **CONFIRMED_STATIC** |
| Cases 23, 24, 32 invoke the HP/SP apply functions | **CONFIRMED_STATIC** — `0x020783CC`, `0x020781E4`, `0x020783DC` |
| Case 6 reaches the generic object pool | **PLAUSIBLE** — `0x02083950` is inside `BattleObj.cpp`'s `0xDC8` range |
| The 73-way and 13-way switches partition one command enum | **REFUTED** — 13-way live cases are all 1–12; zero overlap with the `34-64` band |
| The `34-64` no-op band has an explanation | **still open** |
| My scan's zero-callee result | **REFUTED** — `0x0F000000` mask excludes `BL` (opcode `0xB`) |

## Next angles, ranked

1. **Find what calls this dispatcher and with which command number.** A caller passing `r2 = 23` would locate the HP-delta producer — campaign item B11, approached without offset scans.
2. **Name cases 25, 26, 33, 72.** All four read `[r0,#0x84]`; iteration 45 refuted these as `prmData` reads. Identifying the actual base register closes that loose end.
3. **Check the 32-case dispatcher at `0x021580B4`** (switch on `r3`) — second-largest in ov6, unexamined.
4. Still open: `prmData+0x0C/+0x10/+0x14` prefixes, the 68-entry table at `0x02171FEC`, spawn-slot`+0x02`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the collision walker.
