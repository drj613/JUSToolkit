# Findings: the collision machinery is wired up by the pooled-entity constructor

Loop-Atlas iteration 72. Static.

Traced what writes `ColObj+0x28` and found the collision subsystem connects to the **projectile-entities** subsystem (iterations 52–57).

**The ColObj installer is called from `0x020834D4`** — claim 1 in `Battle-Engine-Map.md`, the pooled-entity constructor in arm9 `BattleObj.cpp`.

The owner is still unnamed. It is now `[arg0+0x8]` of the installer — one hop further than last wake.

---

## 1. `ColObj+0x28` and the owner's fields, written together

```
0x0207CA48  ldr r1, [r4, #0x60]   ; r1 = the ColObj (stored there at 0x0207CA20)
0x0207CA50  str r4, [r1, #0x28]   ; ColObj+0x28 = r4    <- the owner
0x0207CA64  str r7, [r4, #0x34]   ; owner+0x34
0x0207CA6C  str r6, [r4, #0x38]   ; owner+0x38
0x0207CA70  add r0, r4, #0xa4
0x0207CA78  mov r2, #0xd0
0x0207CA80  bl  #0x20517fc        ; memset(owner+0xA4, 0, 0xD0)
0x0207CA88  strb r1, [r4, #0x182]
0x0207CA90  strb r1, [r4, #0x174]
```

`+0x34` and `+0x38` are **the same two fields the pool allocator reads** (`ldr r0,[r4,#0x34]` → node`+0x14`, `ldr r0,[r4,#0x38]` → node`+0x18`, iteration 70). Written here, read there — confirms the owner identity across two functions.

The owner is large: fields at `+0x34`, `+0x38`, `+0x3C`, ColObj at `+0x60`, a `0xD0`-byte region from `+0xA4`, and bytes at `+0x174` and `+0x182`. At least `0x183` bytes.

## 2. The chain to the entity constructor

```
0x020834D4   pooled-entity constructor          (claim 1, BattleObj.cpp, manager 0x0214BE14)
  0x02083550   ldr r0,[r0,#0x0]
  0x02083558   ldr r0,[r0,#0x8C]
  0x02083560   bl 0x0207C988                    ; the ColObj installer
  0x02083564   str r0,[r4,#0x10]                ; result kept at entity+0x10

0x0207C988   the installer
  0x0207C990   mov sb, r0                       ; sb = arg0
  0x0207C9AC   ldr r4, [r9, #0x8]               ; r4 = arg0->[0x8] = THE OWNER
  0x0207CA18   bl Battle_ColObjCreate           ; a 0x40-byte ColObj
  0x0207CA24   str ... [r0,#0x1c]               ; acquire method  -> ColPrm+0x18 pool
  0x0207CA34   str ... [r0,#0x20]               ; release method
  0x0207CA40   str ... [r0,#0x24]               ; third method
  0x0207CA50   str r4, [r1,#0x28]               ; ColObj+0x28 = the owner
```

`query.py callers` reports both the `functions.json` caller edge (`0x020834D4`) and the `bl` site (`0x02083560`) — they agree.

**Collision registration happens at entity construction.** Every entity from claim 1's pooled constructor gets a ColObj wired to the ColPrm `+0x18` pool. That links the two subsystems and explains why there's no standalone "register me" call — collision setup is part of entity creation.

## 3. Located again, still not named

The owner is `[arg0+0x8]` where the installer's `arg0` is `[[r0]+0x8C]` at the call site — two hops from a name instead of one.

Two consecutive wakes have moved the pointer without resolving the identity. The chain is getting longer, not shorter. Naming should come from a different angle — the assert-symbol table, or the object's size and field layout — not another hop.

## Predictions status

| Claim | Verdict |
|---|---|
| `ColObj+0x28` is written by the installer | **CONFIRMED_STATIC** — `str r4,[r1,#0x28]` at `0x0207CA50` |
| The owner is the same object the allocator reads `+0x34`/`+0x38` from | **CONFIRMED_STATIC** — written at `0x0207CA64`/`0x0207CA6C`, read at iteration 70's allocator |
| The installer is called by the pooled-entity constructor | **CONFIRMED_STATIC** — `0x02083560` inside `0x020834D4`, plus the `functions.json` edge |
| Collision setup has a dedicated registration entry point | **REFUTED** — it happens inside entity construction |
| The owner is `arg0` of the installer | **REFUTED** — it is `arg0->[0x8]` |
| The owner was named this wake | **REFUTED** — located at `[arg0+0x8]`, identity still open |
| The owner is at least `0x183` bytes | **PLAUSIBLE** — fields up to `+0x182` observed |

## Next angles, ranked

1. **Name the owner from its shape, not another hop.** ColObj at `+0x60`, `0xD0` region at `+0xA4`, bytes at `+0x174`/`+0x182`. Cross-check against `symbols.json` constructors and allocation sizes — `prior_art.py` plus the known-size approach that identified ColObj and ColWork.
2. **Read `ColObj+0x24`'s method** `0x0207D94C` (carried) — the last unexamined interface method.
3. **Update the map's projectile-entities section** with the collision link, since claim 1 now has a
   documented side effect.
4. **Harness watchpoint** on `ColPrm+0x154` — the bucket-1 contradiction, unresolvable statically.
