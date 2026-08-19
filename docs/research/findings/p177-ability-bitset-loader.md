# P177 — Ability bitset writer found: kind-dispatched loader in `BattleCharaDataLoad.cpp`

**Iteration 177. Static.** Jumped ahead of the polled-KO discriminator because the runtime loop needed a breakpoint address for the respawn re-cache, and this was already queued. They found that the bitset at `battleObj+0x128` is **re-cached in place on KO/respawn** — same object, same identity fields, different contents — and asked me to name the writer.

## The writer

`CONFIRMED_STATIC`. ov6 `0x0215FB3C`, eight instructions:

```
0x0215FB3C: push {r3, lr}
0x0215FB40: ldrb lr, [r1, #1]          ; ability ID from entry+1
0x0215FB44: add  ip, r0, #8            ; bitset base = r0 + 8
0x0215FB48: mov  r1, #1
0x0215FB4C: asr  r3, lr, #5            ; word index = ID >> 5
0x0215FB50: ldr  r2, [ip, r3, lsl #2]
0x0215FB54: and  r0, lr, #0x1f         ; bit index = ID & 0x1F
0x0215FB58: orr  r0, r2, r1, lsl r0
0x0215FB5C: str  r0, [ip, r3, lsl #2]  ; set it
0x0215FB60: pop  {r3, pc}
```

Same addressing as the cancel gate's read — `base + 4*(ID>>5) + 8`, bit `ID & 0x1F` — just from the write side. `r0` here is `battleObj+0x120`, the same base the gate receives. The two halves now meet: `0x0215FB3C` sets the bit, `0x02158EB0` tests it, same expression.

## The dispatcher

No `BL` anywhere in ov6 or arm9 targets `0x0215FB3C`. It's reached **through a table**. The loop at `0x0215FAF4`–`0x0215FB20`:

```
0x0215FB00: ldr  r3, [r2, #0x50]       ; the ability array
0x0215FB04: mov  r0, r7                ; the target object
0x0215FB08: ldrb r2, [r3, r1, lsl #2]  ; entry[i] byte 0 = ability KIND, stride 4
0x0215FB0C: add  r1, r3, r1, lsl #2    ; r1 = &entry[i]
0x0215FB10: ldr  r2, [sb, r2, lsl #2]  ; table[kind], sb = 0x02172210
0x0215FB14: blx  r2                    ; dispatch(target, &entry)
0x0215FB18: add  r5, r5, #1
0x0215FB1C: cmp  r5, r4                ; loop to count in r4
0x0215FB20: blt  0x215faf4
```

`CONFIRMED_STATIC`:

- **Ability entries are 4 bytes**: kind at `+0`, ID at `+1`.
- The array lives at `[obj+0x50]`; the count is the loop bound.
- Each entry dispatches through a table at **`0x02172210`** indexed by kind. **`table[0]` is the bit setter.** Four consecutive slots hold `0x0215FFDC` (a bare `bx lr`) — kinds that do nothing at load.

**The binary names the table itself.** Bytes just before it decode as ASCII: `"Init"` then **`"BattleCharaDataLoad.cpp"`** — the same self-naming trick that gave us `Battle_CharaCreate` and `RuleData_Create`.

## What this does to the P176 layout puzzle

P176 found Luffy's abilities `0x09` at record `+0x03` and `0x0C` at `+0x07`, and noted `+0x0B` reads `0x01` in both records, breaking a clean stride-4 list. With the entry layout now known, Luffy's bytes read as `{kind 0x05, id 0x09}` at `+0x02` and `{kind 0x00, id 0x0C}` at `+0x06` — 4-byte entries, kind first, exactly matching the loader's shape. `+0x0B` is simply past his count.

`PLAUSIBLE`, deliberately not stronger: the `chr_b` record's bytes **are** the array the loader walks. The loop reads `[obj+0x50]`, and the record may be copied or transformed on the way in. The kind/id pattern fitting Luffy is suggestive, not proof — and `0x09` sitting under kind `0x05` rather than kind `0x00` means the setter isn't the only handler that sets bits, or the mapping isn't what it looks like. `not claimed` which.

## Breakpoints for the respawn question

| address | catches | gives |
|---|---|---|
| `0x0215FB3C` | each bit being set | `LR` names the dispatcher; `r0−0x120` should equal their `battleObj`; `[r1+1]` is the ability ID |
| `0x0215FB14` | every dispatch, including no-op kinds | the kind for each entry — maps the whole table |
| `0x0215FAF4` | the loop entry | the whole re-cache as one event, with the count |

`0x0215FB3C` is cheapest and tests the core claim: if `r0 − 0x120` isn't their `battleObj`, my identification of `r0` is wrong and the gate's base needs re-reading.

## The caveat from their KO finding

`CONFIRMED_RUNTIME` (theirs): the bitset is **not stable across a match**. `{9, 12, 14, 25}` became `{2, 5, 14, 15}` after a KO, on an object that kept its pointer, side object, and `+0x1E0` identity byte.

The P176 three-way agreement — runtime bitset, on-disk record bytes, live-array reading — holds **only if the runtime half is read before a KO**. It was, but nobody knew that mattered. Their three measured bits (4, 8, 29) are unaffected: each was poked and observed in one uninterrupted window, so cause and effect hold. What needs a timestamp is any observation of which bits a character carries. **A character's ability set is not a constant of the character.**

`not claimed`: why the contents differ. Three candidates survive — respawn applies a different set, the word holds something wider than abilities, or the active character changed without the checked fields moving. The kind-dispatch table is most likely to answer this, since a second handler that sets bits would explain a different set arriving by the same route.

## Queued by this wake

1. **Polled-KO discriminator** (deferred twice): any read of `char_struct+0x18` branching on zero outside the apply.
2. **Map the rest of table `0x02172210`** — 12 slots read so far, four are the `bx lr` no-op. Naming the handlers names the ability kinds — the vocabulary the whole system is written in.
3. Auto-heal's flag and amount; `0x020781E4`; `0x0215911C`.
