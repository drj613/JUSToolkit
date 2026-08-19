## P187 — `scratch+0x40` is the flag word; bit 11 is set in arm9 collision resolution

Jumped ahead of Z2 in priority because the melonDS stub acks Z2 without firing it, and a static hit here removes an emulator patch from DJ's decision entirely. Reordered off the `{kind,id}` table.

### The subtree is fully exhausted

`0x021591F4` and `0x02159210` both derive the scratch — `ldr r1, [r0, #0x10]` off the entity, the same chain runtime validated against `0x0220FDC4`. P186's caveat ("a deeper callee could still derive it") was worth stating. Both are three-instruction bit setters on `scratch+0x40`:

| Function | Bit | Immediate | Driven by |
|---|---|---|---|
| `0x021591F4` | 30 | `0x40000000` | `orrne`/`biceq` on `r1 != 0` |
| `0x02159210` | 25 | `0x2000000` | `orrne`/`biceq` on `r1 != 0` |

`0x0215911C` calls both with `r1 = 0`, so the expiry handler clears them. Flag maintenance, no damage write. Both have **0 callees** — the subtree is exhausted, not just closed at depth 1.

### The convergence

```
0x02158B94: ldr r0, [sl, #0x1a8]
0x02158B98: ldr r1, [r0, #0x10]     ; the scratch
0x02158B9C: ldr r0, [r1, #0x40]     ; the flag word
0x02158BA0: tst r0, #0x800          ; bit 11 = damage pending
0x02158BA8: ldr r0, [r1, #0xe8]     ; only then the amount
```

`CONFIRMED_STATIC`: `scratch+0x40` is a bitfield the damage flush gates on. Two unrelated paths — the flush and the two expiry-handler leaves — reach the same offset through the same deref chain. Known bits: **11** (damage pending), **25**, **30**.

Three things not to conflate:

- `scratch+0x3C`, the other flag word, whose OR/CLEAR pair is arm9 `0x0207CE7C` / `0x0207CEC8` (P186).
- The `+0x40` that generic setter `0x02028384` writes (P185) — a different object type at a coinciding offset, exactly the trap rule 1 exists for.

### Who sets bit 11: arm9 collision resolution

```
0x02081EA8: ldr r5, [r4, #8]
0x02081EAC: ldr r1, [r5, #8]        ; participant A
0x02081EB0: ldr r0, [r5, #0xc]      ; participant B
0x02081EB4: ldr r6, [r1, #0x1c]
0x02081EB8: ldr r7, [r0, #0x1c]
0x02081EC4: ldr r1, [r2, #0x40]     ; r2 = [r6+0xc]
0x02081ECC: orr r1, r1, #0x800
0x02081ED0: str r1, [r2, #0x40]     ; damage pending on A
0x02081EDC: orr r1, r1, #0x800
0x02081EE0: str r1, [r2, #0x40]     ; damage pending on B
```

Containing function `0x02081DDC`: arm9, 992 bytes, 8 callees, **one caller**. It walks a pair and stages damage on both sides — collision resolution, the stage the bracket said the `+0x134` write must precede.

### Scope correction

**Every sweep I ran was scoped to ov6** — the iteration-76 immediate-offset sweep and the P181 register-offset scanner — because the damage path is ov6. I then reported "no store exists" without qualifying the scope. The four routes are still closed, but route 1's basis was narrower than my wording implied, and the runtime loop was entitled to read it as global.

Re-ran globally with a control (`search-imm 0x134`, control = the known read at `0x0215AC08`). The only `+0x134` stores anywhere are bulk initialisers — `0x0207C744` (arm9) and `0x02161C2C` (ov6), both runs of pool constants into consecutive offsets, named before believing. The conclusion survives; the basis was narrower than stated.

### The card

`0x02081ED0` (arm9, instruction, ARM); also `0x02081EE0`. Confidence `PLAUSIBLE`.

- **Reachability:** `ESTABLISHED` for bit-11 semantics (the flush reads it live and runtime measured that path). **INFERRED** that `0x02081DDC`'s scratch is the same instance — it arrives via `[[participant+0x1C]+0xC]`, a **different chain** than `entity+0x10`.
- **Test:** break at `0x02081ED0`, read `r2`, compare against the known scratch `0x0220FDC4`, then read `[r2+0x134]`.
- **Failure signature:** if `r2` is never `0x0220FDC4` for either fighter, the two chains address different objects and the card is dead — retract, do not reinterpret.
- **The answer either way:** `[r2+0x134] == 384` puts the reduction upstream of collision resolution. `512` or `0` puts the write inside `0x02081DDC` — B11 in a 992-byte arm9 function with one caller, findable statically from there.

An execution breakpoint needs no emulator patch, so this should run before the Z2 gap is arbitrated.

### Three false nulls, all caught by controls

The first `orr 0x800` search returned empty — syntax error swallowed by `2>/dev/null`. Before that, a seven-function scan returned zeros because zsh doesn't word-split unquoted variables, so the command name was one token. Earlier still, `grep -E` didn't understand `\s`. Rule 13 earned its place three times: the tell was always a row of identical zeros, never an error message. **7 of the 12 `orr 0x800` sites are in overlays I didn't resolve** (no `--overlay` passed) — unchecked, not clear.
