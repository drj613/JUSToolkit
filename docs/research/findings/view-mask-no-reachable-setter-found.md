# Findings: no reachable setter of the view mask — narrowed, not closed

Loop-Atlas iteration 93. Static.

If nothing sets a bit in `view+0x0C`, all twelve live handlers never fire and the whole
16-slot table is dead.

**The primary mechanism is eliminated.** The `orr`-based "set bit N" idiom appears
exactly **once** in ov6 — inside the unreachable arm function — and nowhere applicable in
arm9. The view's own reset *clears* the mask.

**Not closed.** A whole-word store bypasses an `orr` scan. Five such stores exist in ov6,
plus 1022 `stm` and 181 register-offset stores unresolvable by offset. Three of the five
are ruled out below; two remain.

---

## 1. The `orr` route is eliminated

Scan for read-modify-write of `+0xc` — `ldr rA,[rB,#0xc]` … `str rC,[rB,#0xc]`
within 8 instructions — over both binaries:

| region | RMW sites at `+0xc` | using `orr` |
|---|---|---|
| ov6 | 20 | **1** |
| arm9 | 79 | 5 |

The single ov6 site is `0x0215FC24`→`0x0215FC3C`, the arm function `0x0215FC20`, which
iteration 92 showed is unreachable. The other 19 are arithmetic accumulates
(`add r2,r2,r6`) on a `+0x10`/`+0x14`/`+0x18` triple — a different struct.

None of arm9's five is a `1<<N` set:

```
0x02042EC4   bic r1, r1, #3 | orr r1, r1, #2          ; a 2-bit field
0x0205F7B4   orr r1, r1, r1, lsl #8 | ... lsl #16     ; byte-broadcast (memset idiom)
0x0205F7CC   same
0x0205F9C8   same
0x0205F9E0   same
```

## 2. Whole-word stores — the gap in an `orr` scan

A mask could be set by storing a constant outright. Non-zero immediate stores to
`+0xc`: **5 in ov6**, 23 in arm9.

| site | value | verdict |
|---|---|---|
| `0x0216AFA8` | `0x1000` | **ruled out** — base is `ldr r1,[pc,#0x260]`, a global |
| `0x02158 8AC` | `0x80000` | **ruled out** — bit 19, outside the 16-bit selector range |
| `0x02168250` | `0x4B000` | **ruled out** — multi-bit, not a single-selector set |
| `0x021553D8` | *(arg)* | open — 4-instruction setter writing `+0x8` and `+0xc` from arguments; the `0x1000` my back-scan attributed to it belongs to another path |
| `0x021694C8` | `0x1000` | open — `mov r0,#0x1000`; `str r0,[r1,#0xc]`; base `r1` not traced |

`0x1000` is bit 12, and selector 12 *is* live, so both matter.

## 3. What remains unresolved

| class | ov6 count |
|---|---|
| `stm` with a non-`sp` base | 1022 |
| register-offset stores | 181 |

Neither carries a matchable offset, so neither can be excluded by scanning. `+0xc` is far
too common to scope by address alone.

## 4. Where this leaves the table

The reset `0x0215FB88` sets `view+0x0C = 0` and is reachable. The only identified
bit-setter is unreachable.

Suggestive but **not** a proof — the table is not recorded as dead. Two named sites and
two unresolvable write classes stand between here and that claim.

## Predictions status

| Claim | Verdict |
|---|---|
| The `orr` "set bit N" idiom on `+0xc` occurs once in ov6 | **CONFIRMED_STATIC** — 20 RMW sites, 1 with `orr`, inside `0x0215FC20` |
| That one site is unreachable | **CONFIRMED_STATIC** *(iteration 92)* — one literal, in an unreferenced trampoline |
| arm9 has a `1<<N` set of a `+0xc` mask | **REFUTED** — 5 `orr` RMWs: one 2-bit field, four byte-broadcast idioms |
| `0x0216AFA8` sets a view mask | **REFUTED** — base is a pc-relative global |
| `0x021588AC` and `0x02168250` set a selector bit | **REFUTED** — `0x80000` is bit 19, outside the 16-slot range; `0x4B000` is multi-bit |
| The view's reset clears the mask | **CONFIRMED_STATIC** *(iteration 92)* — `str r3,[r0,#0xc]` with `r3 = 0` |
| No reachable code sets a view mask bit | **not claimed** — `0x021553D8` and `0x021694C8` untraced; 1022 `stm` and 181 register-offset stores unresolved |
| The 16-slot handler table is dead in retail | **not claimed** — follows only if the above closes |

## Next angles, ranked

1. **Trace the bases of `0x021553D8` and `0x021694C8`.** Two functions, bounded work, and
   they are the last scannable candidates. If both miss, the claim rests only on the two
   unresolvable classes.
2. **Read the table at `[[0x02172984]+0xC]`** (carried) — 16 `{u16, u16}` entries.
3. **Identify the global `0x02172984`** (carried).
4. **Name the `≥0x570` struct at `[char+0x1b4]`** (carried).
