# P158 — Status dispatcher at ov6 `0x02158ED0`: who writes `[param+0x4]`, and the first scaling formula

**Iteration 158. Static only.** Goal was to find who writes `[param+0x4]`, the signed halfword that every status tick and heal handler reads. Found it — and the answer kills the lead it was supposed to open. Also found the dispatcher driving the whole P157 table, which corrects a P157 claim and produces the campaign's **first non-constant scaling formula.**

## How I got there

The P157 table has a literal pointer to it. Scanning `ov06.bin` for any word landing in `0x02171140`–`0x021712C0` turned up **5**: `0x021590E8` → `0x02171168` (table base) plus four into the region past the table. `0x021590E8` is a literal pool word inside function `0x02158ED0` (532 bytes, 3 callers). That function is the dispatcher.

## The dispatcher

```
0x02158ED0: push {r3, r4, r5, r6, r7, r8, sb, lr}
0x02158ED4: movs r8, r1              ; r8 = arg1 = effect id
0x02158ED8: mov  sb, r0              ; r9 = battle object
0x02158EDC: beq  #0x21590dc          ; id == 0 -> return 0
0x02158EE0: ldr  r0, [pc, #0x1fc]    ; -> 0x02172984
0x02158EE4: ldr  r3, [pc, #0x1fc]    ; -> 0x02171168   (the P157 table)
0x02158EE8: ldr  r0, [r0]
0x02158EEC: lsl  r2, r8, #3          ; id * 8
0x02158EF0: ldr  r1, [r0, #4]        ; param array base = [[0x02172984]+4]
0x02158EF4: add  r4, r3, r8, lsl #3  ; r4 = &table[id]
0x02158EF8: ldrh r0, [r1, r2]        ; paramArray[id] + 0x0
0x02158EFC: add  r5, r1, r8, lsl #3  ; r5 = &paramArray[id]
0x02158F00: add  r1, sb, #0x7c
0x02158F04: tst  r0, #0x10           ; flag bit 4 of the param flags
0x02158F08: movne r7, #1
0x02158F0C: moveq r7, #0
0x02158F10: mov  r0, #0x18
0x02158F14: mla  r6, r7, r0, r1      ; r6 = battleObj + 0x7C + slot*0x18
0x02158F18: str  r5, [r6, #4]        ; <<<< node+0x4 = &paramArray[id]
```

`CONFIRMED_STATIC`: `0x02158ED0(battleObj, id)` is the **status/effect apply dispatcher**. It indexes **two parallel arrays at stride 8 using the same id** — the P157 handler table at `0x02171168` and a param array at `[[0x02172984]+4]` — then writes `node+0x4` to point at the param record.

`CONFIRMED_STATIC`: `battleObj+0x7C` holds **two effect slots of `0x18` bytes each**, selected by bit `0x10` of the param record's flags halfword.

## The answer: `[param+0x4]` is never written per-hit

`CONFIRMED_STATIC`: **`0x02158F18` is the only writer, and it writes a *pointer*, not an amount.** The record the handlers dereference (`ldr r1,[r1,#4]` then `ldrsh r1,[r1,#4]`) is `paramArray[id]` — an entry in a **static 8-byte-stride data array keyed by effect id**. So `[param+0x4]` is a **constant read from a table**. Nothing computes it at apply time.

`REFUTED`: `[param+0x4]` is not where chain-length damage scaling lives. It can't be — the field is table data. The P157 reframe ("chain scaling must be applied when `[param+0x4]` is written") is wrong. This closes it.

Param record layout, 8 bytes, `CONFIRMED_STATIC` except where noted:

| offset | width | meaning |
|---|---|---|
| `+0x0` | halfword | flags; bit `0x10` selects which of the two `0x18`-byte slots to use |
| `+0x2` | halfword | base duration (feeds the formula below) |
| `+0x4` | **signed** halfword | the amount every tick/heal handler applies — signed, so one field covers both drain and fill |
| `+0x6` | — | `not claimed` |

## The node at `battleObj + 0x7C + slot*0x18`

| offset | width | meaning |
|---|---|---|
| `+0x0` | word | per-frame tick handler: `table[id].fn` if it returned nonzero, else the stub `0x02159258` |
| `+0x4` | word | pointer to `paramArray[id]` |
| `+0xC` | halfword | the effect id |
| `+0xE` | halfword | duration, **unsigned** (`ldrh`) |
| `+0x10` | halfword | zeroed on apply |
| `+0x12` | halfword | written from `[[battleObj+0x1A8]+0x10]+0x182` on one path |
| `+0x14`, `+0x15` | bytes | both set to 1 on apply |

The handler runs and its return value decides persistence:

```
0x02158F8C: ldr  r2, [r4]        ; table[id].fn
0x02158F90: mov  r0, sb
0x02158F94: blx  r2              ; handler(battleObj, node)
0x02158F98: cmp  r0, #0
0x02158F9C: ldrne r0, [r4]       ; nonzero -> keep ticking with the handler
0x02158FA0: ldreq r0, [pc,#0x148] ; zero -> 0x02159258, the stub
0x02158FA4: str  r0, [r6]
```

`CONFIRMED_STATIC`: this is why `0x02159258` appears as both the table's 7-times-repeated no-op **and** the null tick handler. One-shot effects return 0 and get stubbed out; lasting ones return nonzero and keep ticking.

## The formula — the campaign's first non-constant scaling

```
0x02158F44: ldrh  r2, [r5, #2]     ; base duration from paramArray[id]+0x2
0x02158F4C: mov   r1, #0xa
0x02158F50: strh  r2, [r6, #0xe]   ; node duration = base
0x02158F58: ldrh  r0, [r6, #0xe]
0x02158F5C: bl    #0x200d12c       ; signed divide -> r0 = base / 10
0x02158F60: add   r1, sb, #0x100
0x02158F64: ldr   r2, [pc, #0x180] ; -> 0x02172960
0x02158F68: ldrsb r1, [r1, #0xe0]  ; charIdx = [battleObj+0x1E0], SIGNED byte
0x02158F6C: ldr   r2, [r2]
0x02158F70: ldrh  r3, [r6, #0xe]   ; re-read duration
0x02158F74: add   r1, r2, r1, lsl #2
0x02158F78: ldr   r2, [r1, #0x4c]  ; stat = [statTable + charIdx*4 + 0x4C]
0x02158F80: lsl   r2, r2, #1       ; stat * 2
0x02158F84: mla   r2, r0, r2, r3   ; r2 = (base/10) * (stat*2) + base
0x02158F88: strh  r2, [r6, #0xe]
```

`CONFIRMED_STATIC`:

```
duration = base + (base / 10) * (stat * 2)
  base    = paramArray[id] + 0x2        (unsigned halfword)
  charIdx = [battleObj + 0x1E0]         (signed byte)
  stat    = [[0x02172960] + charIdx*4 + 0x4C]   (word)
  result stored as an unsigned halfword at node+0xE
```

Every damage-side effect in this campaign so far has been flat. This is the first place a **per-character stat multiplies anything** — and it scales **status duration**, not damage. A character with a higher `+0x4C` stat keeps burn, poison, paralysis, etc. running longer, by a fifth of the base duration per stat point.

`SPECULATIVE`: `+0x4C` in a `0x4`-stride per-character table is a status-resistance or willpower-type stat. The stride is only 4 bytes, so `[base + idx*4 + 0x4C]` is really `[base + 0x4C + idx*4]` — a standalone `u32` array at offset `+0x4C` of the block, one word per character.

## Corrections

**My own P157 claim, `REFUTED`.** I said the byte at entry `+0x5` "is the table's real key," reasoning from it being a gapless unique permutation of `0x00`–`0x1F`. The dispatcher indexes `table + id*8` with the **caller's argument**, so the index is the id and `+0x5` is just a value field. The permutation is still a real property of that field — 32 unique gapless values isn't an accident — but it's not the key. I shouldn't have promoted a striking data pattern to a structural role without finding the indexing code first. `+0x5` is near-monotonic in the index with local swaps, so `SPECULATIVE`: a parallel enum, maybe an icon or message slot.

Entry layout, now read from the code that consumes it rather than inferred:

| offset | how the dispatcher reads it | meaning |
|---|---|---|
| `+0x0` | `ldr` then `blx` | handler function pointer |
| `+0x4` | `ldrsb`, skip if `== -1` | **sound index**, passed as `0x0207342C(0x7A, x)` |
| `+0x5` | not read here | the `0x00`–`0x1F` enum above |
| `+0x6` | `ldrsb`, skip if `== -1` | index into a **16-word array at `0x02171128`** |
| `+0x7` | not read here | status opcode `0x19`–`0x22` (P157, agrees with C6b) |

`CONFIRMED_STATIC`: `0xFF` really is the "none" marker — the dispatcher reads both bytes with `ldrsb`, compares against `mvn r0,#0` (`-1`), and branches past the work. P157 asserted this from data alone; the code now proves it.

`CONFIRMED_STATIC`: the `+0x6` array is at `0x02171128`, **immediately before the dispatch table**, 16 words (`0x02171128`–`0x02171167`), indexed `b2*4`. Observed `+0x6` values run `0x00`–`0x0E`, so the bound fits. Each word is a halfword pair: high half `0x0022` or `0x0023`, low half `0x0001`–`0x0013`. Passed as `0x02159b8c(battleObj, word)`. `SPECULATIVE`: a tagged effect or animation resource id.

`CONFIRMED_STATIC`: P157's stride-8 claim now has a **second representation** behind it. P157 got 8 from the data (a 42-entry permutation only closes at that stride); the dispatcher gets it from code (`add r4, r3, r8, lsl #3`). Different representations, same answer.

`not claimed`: the prologue checks only `id != 0`. No upper bound on `id` is visible here. Whether one exists in the three callers is unread.

Both globals — `0x02172984` and `0x02172960` — sit at or past `0x02172960`, exactly where `ov06.bin` ends. They are **BSS, filled at runtime**, so static analysis will never name their contents. Same ceiling as `0x021AA0D8` in P153.

## Convergent verification, and a Codex miss

Codex got the raw words of `0x02158F44`–`0x02158F88` with no addresses and no hypothesis, before this write-up, per the standing rule. It agreed on every load and store, on the widths, and on `ldrh` zero-extending. It **disagreed on the multiply-accumulate**, reading `mla r2, r0, r3, r2` (`r2 = r0*r3 + r2`) where the listing says `mla r2, r0, r2, r3` (`r2 = r0*r2 + r3`).

Settled by a third representation — the raw encoding. `0xE0223290`: `Rd` = bits 19–16 = `r2`, `Rn` = bits 15–12 = `r3`, `Rs` = bits 11–8 = `r2`, `Rm` = bits 3–0 = `r0`, bits 7–4 = `1001`. ARM `MLA` computes `Rd = Rm*Rs + Rn`, so `r2 = r0*r2 + r3`. **Codex swapped `Rn` and `Rs`.**  The listing and the bit fields agree; Codex is wrong.

This matters. Codex's version gives `(base/10)*base + 2*stat` — dimensionally incoherent, adding a raw stat to a squared duration. Mine gives `base + (base/10)*(2*stat)`, a sane percentage-style scale. The arithmetic sanity check points the same way as the encoding.

Two Codex remarks worth keeping:

1. The `ldrh r3, [r6, #0xe]` at `0x02158F70` is a **fresh read after the `bl`**, not a reuse of the value stored at `0x02158F50`. It equals `base` only because `0x0200D12C` is an arithmetic helper that doesn't touch that memory. Strictly, the formula assumes this.
2. Duration is **unsigned** (`ldrh`), and `strh` keeps only the low 16 bits, so a large `base * stat` product wraps rather than saturating. An overflow edge case for a reimplementation.

Also, my prompt to Codex claimed two `bl` words in the fragment. There was one. Codex said so plainly instead of inventing a second. A wrong framing in the prompt did not propagate.

## Tool note

`codex exec "<prompt>"` **reads stdin even when the prompt is a positional argument**, and blocks forever if stdin is an open terminal. P157's first call only worked because backgrounding gave it `/dev/null`. A foreground call this wake hung for the full 560s timeout and produced 39 bytes. **Always pass `< /dev/null`.** Combined with last wake's lesson — a backgrounded call dies when the turn ends — the only reliable form is foreground with stdin closed.

## Queued by this wake

1. Read the **3 callers of `0x02158ED0`** — they carry the `id`, so they show where an effect is chosen. If a dream attack picks a different `id` by chain length, it shows up there.
2. Identify `[0x02172960]` — the per-character stat block whose `+0x4C` word scales status duration. It's BSS, so find its **initialiser**, which is where the `+0x4C` value comes from (very likely a `chr_b` record field).
3. Read `0x02159B8C(battleObj, taggedId)`, the consumer of the `0x02171128` array.
4. Check whether any caller bounds `id` before calling; 42 entries, only `id != 0` checked here.
