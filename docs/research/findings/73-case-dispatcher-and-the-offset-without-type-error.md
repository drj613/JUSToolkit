# Findings: a 73-case dispatcher in `BattleChara.cpp`, and why an offset match is not evidence

Loop-Atlas iteration 45. Static.

Iteration 44 asked "find the callers of the five ov6 prmData accessors at
`0x02157DD8`–`0x02157F50`". **The premise was wrong twice**:

1. They are not accessors. They are cases in a **73-case switch**.
2. They do not read `prmData`. The base register at those `+0x84` reads is not a character struct.

The second error matters more because it isolates a new mistake:
**matching a struct offset proves nothing until the base register's type is established.**

This wake produced a real landmark — a 73-case per-character dispatcher — and closed the book on
finding the collision walker by static analysis.

---

## 1. REFUTED: the "accessor bank" is a 73-case switch

All five sites sit inside one function. Every block branches to a common epilogue instead of returning:

```
0x02157DD8  ldr r0, [r0, #0x84]
0x02157DDC  cmp r0, #0
0x02157DE0  beq #0x2157f90        <-- common exit, not `bx lr`
0x02157DE4  ldr r1, [r5, #0x1a8]
0x02157DE8  bl #0x216fa9c
0x02157DEC  b #0x2157f90          <-- common exit
```

The dispatcher is at **`0x02157A60`**:

```
0x02157A5C  cmp r2, #72
0x02157A60  addls pc, pc, r2, lsl #2
```

followed by a 74-entry branch table at **`0x02157A64`–`0x02157B88`**, targeting
`0x02157B8C`–`0x02157F90`. The epilogue:

```
0x02157F90  mov r0, #0
0x02157F94  add sp, sp, #0xc
0x02157F98  pop {r3, r4, r5, r6, pc}
```

So `0x02157B8C`–`0x02157F90` is **one 73-case switch on `r2` (the third argument)** in ov6
`BattleChara.cpp` — a per-character command dispatcher. Iteration 44 misread five of its cases as
standalone accessor functions.

`Battle-Engine-Map.md` projectile-entities claim 3 already records ov6 `0x021574CC` as a "13-way switch
on 3rd arg", also in `BattleChara.cpp`. Two switches on `r2` a few hundred bytes apart points to a
family of command dispatchers.

`scripts/decomp/find_jump_tables.py` (iteration 40) found this table correctly without prompting.

## 2. REFUTED, and the real lesson: these sites do not read `prmData`

Iteration 43 established `prmData` is a **`0x20`-byte allocation** (`mov r0,#0x20` then the allocator at
`0x021702CC`–`0x021702DC`). Iteration 44 then treated every `ldr Rd,[Rn,#0x84]` site as a `prmData`
read.

The callees disprove that immediately:

| callee | how it uses its first argument |
|---|---|
| `0x0216FA9C` | `str r1,[r4,#0x4c]`, `ldr r2,[r4,#0x2c]` |
| `0x0216FB04` | `str r1,[r0,#0x4c]` |
| `0x02158000` | `ldrb r1,[r0,#0x1a]`, `ldr r0,[r0,#0x2c]` |

`+0x2c` and `+0x4c` are **past the end of a `0x20`-byte struct**. Whatever these receive, it is not
`prmData`, so the `+0x84` they came from is not `character+0x84`.

`0x02158000` is a near-miss: it reads `+0x1a`, and `prmData+0x1A` really is the halfword initialised
to `0x7a`. But it uses `ldrb`, not `ldrh`, and also reads `+0x2c`. Offset coincidence. This is exactly
how a plausible wrong attribution survives.

**Only one ROM site is confirmed to touch `character+0x84`: the store at `0x0215F6B0`.**
The other nine `+0x84` sites have unverified base types and are not `prmData` reads.

### The rule

An offset match is not evidence until the base register's type is established. Iteration 44 treated
`+0x84` as a global field name when it only names a field *relative to a character struct*.

This joins two earlier lessons (scanners must stop at function boundaries; constrain enough to read
every hit). Same family — searching by shape instead of by meaning — but this one has a cheap fix:
before believing an offset hit, trace where the base register came from.

## 3. The collision walker is out of static reach by every route tried

Four approaches, all closed:

| approach | outcome |
|---|---|
| Direct chain `char+0x84` → `prmData+0x00` | **REFUTED** — 0 of 10 sites, with function-boundary checking (iteration 44) |
| ×20 stride arithmetic | **REFUTED** — 70 hits ROM-wide; 20 is too common a struct size (iteration 44) |
| Callers of the "accessor bank" | **REFUTED** — no accessor bank exists; they are switch cases (this wake) |
| Direct callers of the collision stub bank | **REFUTED** — 28 of 36 stubs have zero direct callers (iteration 41) |

The engine reaches this data through dispatch tables and switch cases — the access path is assembled
at runtime from a table index. No static pattern can span it.

**Recommendation: use the harness.** The experiment is small and fully specified because the data's
runtime location is known:

1. Break on `Battle_PrmDataInit` (`0x021702BC`), let it return, and record `r0` — the `prmData` pointer.
2. Read `[r0+0x00]` — the collision record array base for that character.
3. Set a **read watchpoint** on that address and land a hit in battle.
4. The trapping PC is the walker.

Same shape as earlier harness wins (the `+128` regen delta, the accumulator refutation). Converts a
search that failed four ways into one measurement.

## Predictions status

| Claim | Verdict |
|---|---|
| ov6 `0x02157DD8`–`0x02157F50` is a prmData accessor bank | **REFUTED** — cases in a 73-case switch, common epilogue `0x02157F90` |
| A 73-case switch is dispatched at `0x02157A60` on `r2` | **CONFIRMED_STATIC** — `cmp r2,#72`; table `0x02157A64`–`0x02157B88` |
| The five `+0x84` sites read `prmData` | **REFUTED** — callees index `+0x2c`/`+0x4c`, past a `0x20`-byte struct |
| `prmData` is `0x20` bytes | **CONFIRMED_STATIC** — `mov r0,#0x20` before the allocator (iteration 43) |
| `character+0x84` holds `prmData` | **CONFIRMED_STATIC** — the store at `0x0215F6B0` only |
| Any other `+0x84` site is a `prmData` read | **not claimed** — base register types unverified |
| The walker is findable statically by pattern search | **REFUTED** — four independent approaches closed |
| `0x02158000` reading `+0x1a` indicates prmData | **REFUTED** — `ldrb` not `ldrh`, and it also reads `+0x2c` |

## Next angles, ranked

1. **Hand the walker to the harness session** with the four-step watchpoint recipe above. It is fully
   specified and needs no further static work.
2. **Enumerate the 73-case dispatcher.** 73 entries map everything the engine can ask about a character —
   more tractable than the walker and useful to several open subsystems. Cases are already delimited by
   the branch table.
3. **Check whether `0x021574CC`'s 13-case switch and this 73-case one share a command numbering.** If
   they do, claim 3's `r2=7` selector gains meaning.
4. Still open: `prmData+0x0C/+0x10/+0x14` prefixes, what indexes the 68-entry table at `0x02171FEC`, what
   reads spawn-slot`+0x02`, and the 24 positive `ProjectileId` values.
