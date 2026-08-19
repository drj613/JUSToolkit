# Findings: when the `+0x48` flag changes, a coordinate is negated in place

Loop-Atlas iteration 128. Static.

Read `0x0206CEAC` in full (124 bytes) plus its three small helpers. Results:

1. **Vtable slot `+0x5C` is the setter** for the `Q+0x48` byte. Iteration 127 could only say it took
   `(Q, boolean)`; now the direction is pinned down.
2. The function is an **apply-if-changed** handler: it compares a desired flag against the current one, and
   when they differ, writes the new flag *and* **negates a coordinate in place**.
3. That negation is why I now read the flag as **facing / horizontal flip**, and why iteration 127's
   "side/team" guess is the weaker reading.
4. `0x0206CEAC` has **0 callers** — it is installed as a callback via `0x02028384`, matching the
   registration behavior already established at iteration 54's correction.

---

## 1. The whole function

```
0x0206CEAC  push {r3, r4, r5, lr}
0x0206CEB0  mov r5, r0             ; r5 = S (arg0)
0x0206CEB4  ldr r0, [r5, #4]       ; P = [S+0x04]
0x0206CEB8  ldr r0, [r0, #0x44]
0x0206CEBC  cmp r0, #0
0x0206CEC0  moveq r0, #0           ; redundant -- a ternary yielding 0
0x0206CEC4  beq #0x206cecc
0x0206CEC8  bl  #0x2011b38         ; lazy-init accessor
0x0206CECC  bl  #0x206cf28         ; r0 = the DESIRED flag
0x0206CED0  mov r4, r0
0x0206CED4  mov r0, r5
0x0206CED8  bl  #0x206cf28         ; r0 = the CURRENT flag (S's own)
0x0206CEDC  cmp r4, r0
0x0206CEE0  popeq {r3, r4, r5, pc} ; unchanged -> do nothing
0x0206CEE4  ldr r0, [r5, #4]
0x0206CEE8  mov r1, r4
0x0206CEEC  ldr r0, [r0, #0x64]    ; r0 = Q
0x0206CEF0  ldr r2, [r0]
0x0206CEF4  ldr r2, [r2, #0x5c]
0x0206CEF8  blx r2                 ; Q->vtable[+0x5C](Q, desired)   <- THE SETTER
0x0206CEFC  ldr r1, [r5, #4]
0x0206CF00  add r0, sp, #0
0x0206CF04  bl  #0x2024d44         ; out = [[P+0x50]+0x0C]
0x0206CF08  ldr r0, [r5, #4]
0x0206CF0C  ldr r1, [sp]
0x0206CF10  ldr r0, [r0, #0x50]
0x0206CF14  rsb r2, r1, #0         ; r2 = -value
0x0206CF18  mov r1, #1
0x0206CF1C  str r2, [r0, #0xc]     ; [[P+0x50]+0x0C] = -value
0x0206CF20  bl  #0x2024c3c         ; notify([P+0x50], 1)
0x0206CF24  pop {r3, r4, r5, pc}
```

## 2. `+0x5C` is a setter, not just "a method taking a boolean"

Iteration 127 saw `Q->vtable[+0x5C]` called with a freshly-read byte and could not tell whether it was a
read or a write. Here the argument is `r4` — the **other** object's flag — passed only after confirming it
differs from `Q`'s own value. Writing a new value after checking it changed is a setter. Nothing else fits.

The second `0x0206CF28` call takes `S`, so it resolves to `*(u8*)(*(*(S+4)+0x64)+0x48)` = **`Q+0x48`
itself**. The function reads `Q`'s flag directly and writes it back through `Q`'s vtable — read via the
field, write via the method.

## 3. The helpers

```
0x02024D44   ldr r1, [r1, #0x50] ; ldr r1, [r1, #0xc] ; str r1, [r0] ; bx lr
             ; out = *(*(P+0x50) + 0x0C)  -- a getter for the field the caller then overwrites

0x02011B38   if ([r0+0x18] == 0) r0->vtable[+0x14](r0);  return [r0+0x18];
             ; lazy-init cached-child accessor, 31 callers
```

The tail sequence is: **read `X` from `[[P+0x50]+0x0C]`, store `-X` back, then notify.**
`0x02024D44` reads the value and `0x0206CF1C` writes it — same address expression, one instruction apart
in effect. This is an **in-place negation**, not a copy to somewhere else.

## 4. Why "facing" rather than "team"

Iteration 127 floated "side/team selector" as SPECULATIVE. The deciding factor is what the code *does* when
the flag changes: it performs a **geometric mirror** (negates a coordinate), not an ownership or state
update. You negate a coordinate to flip something horizontally; you do not negate a coordinate because a
character changed teams.

Combined with the earlier evidence — a boolean (all 21 readers compare only to `0`, iteration 127) that
**selects which wall bound is tested** (iteration 125) — facing direction accounts for every observation.
It stays **PLAUSIBLE**: no symbol names it, and the inference rests on the negation.

## 5. Two things recorded, not smoothed over

**The zero path dereferences null.** When `[P+0x44] == 0`, `r0` is set to `0` and `0x0206CF28` is called
anyway — which does `ldr r0,[r0,#4]`, reading address `0x00000004`, then two more hops off whatever that
holds. The redundant `moveq r0, #0` shows this is a ternary that yields `NULL`, so the guard produces the
null rather than skipping the call. Either `[P+0x44]` is never `0` in practice, or the read is harmless on
this hardware. Nothing here settles which.

**`+0x0C` as a coordinate, reached two ways.** Iteration 125's walker read a base coordinate at `C+0x0C`
where `C = [B+0x5C]`; this function reads and writes one at `[[P+0x50]+0x0C]`. Same field offset, different
route. Whether it is the same object is **not claimed**.

## Predictions status

| Claim | Verdict |
|---|---|
| Vtable slot `+0x5C` is the setter for `Q+0x48` | **CONFIRMED_STATIC** — called with the differing value at `0x0206CEF8`, after the `cmp`/`popeq` guard |
| The function is apply-if-changed | **CONFIRMED_STATIC** — `cmp r4, r0`; `popeq` at `0x0206CEE0` |
| A coordinate is negated **in place** | **CONFIRMED_STATIC** — `0x02024D44` reads `[[P+0x50]+0xC]`, `0x0206CF1C` writes `-value` back to it |
| `0x02024D44` is a getter for that same field | **CONFIRMED_STATIC** — four instructions, `0x02024D44`–`0x02024D50` |
| `0x02011B38` is a lazy-init cached-child accessor | **CONFIRMED_STATIC** — `0x02011B40`–`0x02011B58`, 31 callers |
| `0x0206CEAC` is reached by a direct call | **REFUTED** — 0 callers; one literal load at `0x0206CC2C`, registered through `0x02028384` |
| The `+0x48` flag is a facing / horizontal-flip bit | **PLAUSIBLE** — the response to a change is a geometric mirror |
| The `+0x48` flag is a side/team selector | **weakened** *(iteration 127's SPECULATIVE)* — a team change would not negate a coordinate |
| The zero path is guarded | **REFUTED** — it produces `NULL` and calls the getter anyway |
| `[[P+0x50]+0xC]` is the same object as the walker's `C` | **not claimed** — same offset, different route |

## Next angles, ranked

1. **Read `0x02024C3C`** (64 bytes, 2 callers) — the notify called right after the negation, with `1`. It
   should reveal what the mirror invalidates.
2. **Name `Q`** (carried) — now has a setter at vtable `+0x5C` and a lazy child at `+0x18` via
   `0x02011B38`'s vtable `+0x14`.
3. **Read `0x0206CA8C`** (1004 bytes, 0 callers) — installs this callback and eleven others; it is the
   setup routine for whatever subsystem `S` belongs to.
4. **Name `B+0x78`'s other bits** (carried) — two of 32 known.
