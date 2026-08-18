# P159 — Complete effect-id table; status subsystem cleared of chain scaling

**Iteration 159. Static only.** Traced the callers of the P158 dispatcher `0x02158ED0` to find where the effect id originates. Found two selection routes, neither of which scales anything. Enough structure to write out the **full 42-entry effect table with ids and reachability**.

## Caller count

`query.py callers` reports 8 references — **3 caller functions and 5 `bl` sites** (the known double-counting). The three callers are `0x02157A44`, `0x0215807C`, and `0x02158B20` — the same three holding the HP-adjust sites from P157. One subsystem, one set of entry points.

`find_thumb_callers.py --to 0x02158ED0` finds no Thumb callers, so the ARM enumeration is complete.

## Route A — script operand through a translation table (3 sites)

`0x02157C6C`, `0x02158204`, and `0x02158280` all use the same idiom:

```
0x02157C5C: 38139fe5  ldr  r1, [pc, #0x338]      ; -> 0x0217215C
0x02157C60: 0408a0e1  lsl  r0, r4, #0x10
0x02157C64: 2018d1e7  ldrb r1, [r1, r0, lsr #16] ; r1 = byteTable[(u16)r4]
0x02157C68: 0500a0e1  mov  r0, r5
0x02157C6C: 970400eb  bl   #0x2158ed0
```

`CONFIRMED_STATIC`: **all three resolve to the same byte table, ov6 `0x0217215C`.** The pool words at `0x02157F9C` and `0x02158460` both hold `0x0217215C`. The `lsl #16` / `lsr #16` pair masks `r4` to 16 bits — no scaling.

`CONFIRMED_STATIC`: the table is **26 bytes**, operand `0x00`–`0x19`, mapping script operand to effect id:

| operand | `0x00`–`0x10` | `0x11` | `0x12` | `0x13` | `0x14` | `0x15` | `0x16` | `0x17` | `0x18` | `0x19` |
|---|---|---|---|---|---|---|---|---|---|---|
| id | operand + 1 | `0x23` | `0x24` | `0x25` | `0x26` | `0x27` | `0x28` | `0x29` | `0x18` | `0x21` |

First 17 operands are just `id = operand + 1`; the rest jump into a high block. The table's **max value is `0x29` = 41**, and the P157 dispatch table has **exactly 42 entries (`0x00`–`0x29`)**. Three independent facts confirm the id space is **1–41 with 0 = "none"**: P157's data layout counted 42 entries, P158's indexing is `table + id*8` with a `id != 0` guard, and this operand map tops out at 41.

## Route B — staged effect ids on the entity (2 sites)

Both sites live in `0x02158B20`, the on-hit apply function from P157/P158:

```
0x02158B28: ldr   r1, [sl, #0x1a8]
0x02158B2C: ldr   r1, [r1, #0x10]
0x02158B30: add   r1, r1, #0x100
0x02158B34: ldrsb r1, [r1, #0x73]     ; [X+0x173], SIGNED byte
0x02158B38: rsb   r1, r1, #0          ; NEGATE
0x02158B3C: lsl   r1, r1, #0x18
0x02158B40: asr   r1, r1, #0x18       ; sign-extend to 8 bits
0x02158B44: lsl   r1, r1, #0x10
0x02158B48: lsr   r1, r1, #0x10       ; zero-extend to 16 bits
0x02158B4C: bl    #0x2158ed0
0x02158B60: ldrsb r1, [r1, #0x72]     ; [X+0x172], SIGNED byte, NOT negated
0x02158B64: bl    #0x2158ed0
```

`CONFIRMED_STATIC`: `X = [[battleObj+0x1A8]+0x10]`, and **`X+0x172` and `X+0x173` are staged effect ids**. `+0x173` is stored **negated** — the code flips its sign before dispatch — so a non-zero value is held negative, and 0 still means "none" (the dispatcher returns immediately on id 0). `+0x172` is used as-is.

`0x02158B20` now reads as one coherent thing: an **on-hit flush** that applies pending HP damage (`+0xE8`, P157), a pending second-gauge amount (`+0x130`, P157), and **two pending effect ids** (`+0x172`, `+0x173`).

`SPECULATIVE`: the exact form is `(uint16_t)(int8_t)(-x)`, so a stored `-128` would produce `0xFF80`, far outside 1–41. Either the field is never `-128` or there's a guard elsewhere; not claimed which.

## The complete effect table

Ids `0x00`–`0x29`, joined against the operand map. `-` is `0xFF`, the "none" marker.

| id | handler | `+0x4` sound | `+0x5` | `+0x6` | `+0x7` status | script operand |
|---|---|---|---|---|---|---|
| `0x00` | `0x02159258` | - | - | - | - | - |
| `0x01` | `0x021592A0` | 0x07 | - | 0x00 | - | 0x00 |
| `0x02` | `0x021592A0` | 0x07 | - | 0x00 | - | 0x01 |
| `0x03` | `0x021592A0` | 0x07 | - | 0x00 | - | 0x02 |
| `0x04` | `0x021592C0` | 0x0D | 0x00 | 0x01 | - | 0x03 |
| `0x05` | `0x021592DC` | 0x0D | 0x01 | 0x03 | - | 0x04 |
| `0x06` | `0x021592F8` | 0x0D | - | 0x05 | - | 0x05 |
| `0x07` | `0x0215930C` | 0x0D | 0x02 | 0x09 | - | 0x06 |
| `0x08` | `0x02159258` | 0x0D | 0x03 | 0x07 | - | 0x07 |
| `0x09` | `0x0215931C` | 0x0D | 0x05 | 0x05 | - | 0x08 |
| `0x0A` | `0x0215932C` | 0x0D | 0x04 | 0x05 | - | 0x09 |
| `0x0B` | `0x02159258` | 0x0D | 0x06 | 0x05 | - | 0x0A |
| `0x0C` | `0x02159344` | 0x0D | 0x13 | 0x05 | - | 0x0B |
| `0x0D` | `0x02159364` | 0x0D | 0x0B | 0x05 | - | 0x0C |
| `0x0E` | `0x02159378` | 0x0D | 0x08 | 0x05 | - | 0x0D |
| `0x0F` | `0x021593A4` | 0x0D | 0x09 | 0x05 | - | 0x0E |
| `0x10` | `0x021593D0` | 0x0D | 0x0A | 0x05 | - | 0x0F |
| `0x11` | `0x02159434` | 0x0D | 0x07 | 0x05 | - | 0x10 |
| `0x12` | `0x021594E4` | 0x0C | 0x0C | 0x0A | 0x1F | - |
| `0x13` | `0x02159500` | 0x0C | 0x0D | 0x0B | 0x1D | - |
| `0x14` | `0x02159538` | 0x0C | 0x0F | 0x0C | 0x1C | - |
| `0x15` | `0x02159258` | 0x0C | 0x10 | 0x0D | - | - |
| `0x16` | `0x02159578` | 0x0C | 0x11 | 0x08 | 0x21 | - |
| `0x17` | `0x02159594` | 0x0C | 0x12 | 0x0E | 0x1E | - |
| `0x18` | `0x02159608` | 0x0C | 0x14 | 0x0E | 0x22 | 0x18 |
| `0x19` | `0x02159608` | 0x0C | 0x15 | 0x0E | 0x22 | - |
| `0x1A` | `0x02159258` | 0x0C | 0x16 | 0x0E | - | - |
| `0x1B` | `0x02159258` | 0x0C | 0x17 | 0x0E | - | - |
| `0x1C` | `0x021596E0` | 0x0C | 0x19 | 0x0E | 0x20 | - |
| `0x1D` | `0x021597F8` | 0x0C | 0x1A | 0x0E | 0x20 | - |
| `0x1E` | `0x02159624` | - | 0x1B | - | 0x1B | - |
| `0x1F` | `0x02159694` | - | 0x1C | - | 0x19 | - |
| `0x20` | `0x02159678` | - | 0x1D | - | 0x1A | - |
| `0x21` | `0x021592DC` | 0x0C | 0x0E | 0x04 | - | 0x19 |
| `0x22` | `0x02159258` | 0x0C | 0x18 | 0x0E | - | - |
| `0x23` | `0x0215941C` | 0x0D | 0x1E | - | - | 0x11 |
| `0x24` | `0x021593E8` | 0x0D | 0x1F | - | - | 0x12 |
| `0x25` | `0x02159260` | 0x07 | - | 0x00 | - | 0x13 |
| `0x26` | `0x02159260` | 0x07 | - | 0x00 | - | 0x14 |
| `0x27` | `0x02159280` | 0x09 | - | 0x02 | - | 0x15 |
| `0x28` | `0x02159280` | 0x09 | - | 0x02 | - | 0x16 |
| `0x29` | `0x02159280` | 0x09 | - | 0x02 | - | 0x17 |

What the table shows (all `CONFIRMED_STATIC` unless marked):

- **Three blocks by `+0x4` sound byte.** Ids `0x01`–`0x11` use sound `0x07`/`0x0D` with **no status byte** — gauge/HP effects. Ids `0x12`–`0x22` use sound `0x0C` and hold **every status opcode `0x19`–`0x22`**. Ids `0x23`–`0x29` are a mixed tail.
- **The status block is mostly unreachable from scripts.** Of ids `0x12`–`0x22`, only `0x18` and `0x21` appear in the operand map. `PLAUSIBLE`: statuses are inflicted through Route B (the staged `+0x172`/`+0x173` bytes on hit), while script opcodes drive gauge effects. Clean division of labor, consistent with C6b's finding that no melee damage reaches this subsystem.
- **P157's "two shifted, three unshifted" puzzle is resolved — not a bug.** The `lsl #6` handler `0x02159260` covers ids `0x25`/`0x26` (operands `0x13`/`0x14`); the `lsl #8` handler `0x02159280` covers ids `0x27`–`0x29` (operands `0x15`–`0x17`); the unshifted `0x021592C0` is id `0x04`. **Different opcodes deliberately take their amount in different units** — raw, ×64, ×256.
- `+0x5` is a **dense allocation**: values `0x00`–`0x1F` each appear once, assigned only to ids that need one, roughly in id order. `SPECULATIVE`: an index into a 32-entry icon or message resource.
- `0x02159258` (the stub) fills id `0x00` **and** ids `0x08`, `0x0B`, `0x15`, `0x1A`, `0x1B`, `0x22` — allocated ids with sound and `+0x6` set but no behavior. `SPECULATIVE`: cut or unimplemented effects, since they still carry resource bytes.
- Duplicate handlers with different resource bytes are normal: `0x021592A0` covers `0x01`–`0x03`, `0x02159608` covers `0x18`/`0x19`, `0x021592DC` covers `0x05` and `0x21`.

## Chain-multiplier verdict: subsystem cleared

`CONFIRMED_STATIC`: **no non-constant scaling exists anywhere in effect selection.** Route A is a byte-table lookup masked to 16 bits. Route B is a signed byte, negated at one site. Codex was given both fragments as raw hex (no addresses, no hypothesis) and independently confirmed neither contains a multiply or non-constant scale, agreeing on every load width, addressing mode, and shift-pair purpose.

Stacked with previous wakes:

| wake | checked | result |
|---|---|---|
| P157 | delta at all ten HP-adjust `bl` sites | only constant shifts (`lsl #6`, `lsl #8`) |
| P158 | writer of `[param+0x4]` | writes a **pointer** to static table data; amount is constant |
| P159 | how the effect id is chosen at all five dispatcher sites | table lookup and negated byte; no scaling |

**Conclusion, `CONFIRMED_STATIC`: the status/effect subsystem has no chain-length scaling and cannot hold the dream-attack multiplier.** Combined with C6b's result that no melee damage reaches this subsystem, three wakes close it out. Productive detour — it yielded the dispatcher, id table, duration formula, and on-hit flush — but this is not the dream-attack path.

## Where next

A dream attack is a *move*, so the multiplier belongs to the move/attack script system (still `move_script_location_UNKNOWN`). The one non-constant formula found so far (P158's duration scale) drew its multiplier from a **per-character stat table** at `[[0x02172960] + charIdx*4 + 0x4C]`. That's the shape to look for: a per-character or per-chain word read from a table and fed to `mul`/`mla`. Finding `[0x02172960]`'s initializer is the most valuable remaining item — it names the stat block any such formula would draw from.

## Queued

1. **Identify `[0x02172960]`** — the per-character stat block. BSS, so find its initializer; `+0x4C` is very likely a `chr_b` record field. Top priority: it's the one confirmed multiplier source in the engine.
2. Find the writer of `X+0x172` / `X+0x173` where `X = [[battleObj+0x1A8]+0x10]` — where a move declares which status it inflicts, the move-side data this campaign has been missing.
3. Identify `[[battleObj+0x1A8]+0x10]`. It supplies `+0x140` (P157), `+0x172`, `+0x173`, and `+0x182` (P158) — a recurring per-hit or per-player state block worth naming.
4. Read ov6 `0x02159B8C(battleObj, taggedId)`, consumer of the 16-word array at `0x02171128`.
5. Name the `+0x5` 32-entry resource the effect table indexes.
