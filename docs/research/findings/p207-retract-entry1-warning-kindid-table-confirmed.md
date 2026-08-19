## P207 — Retracting the `entry+1` warning; `{kind,id}` table confirmed

### The retraction

P206 warned that the ability-list poke wouldn't survive a respawn because the bitset writer `0x0215FB3C` reads its id from `entry+1`, suggesting a ≥2-byte array source instead of the packed one-byte list at `char_struct+0x1B`. The runtime loop held its respawn variant on that warning. **The warning was wrong.**

The loader loop, read directly:

```
0x0215FAE4: ldrsb r4, [r6, #0xa]       ; count  = char_struct+0x1A   (r6 = char_struct+0x10)
0x0215FAF4: add   r0, r6, r5           ; r0 = r6 + i
0x0215FAF8: ldr   r2, [r8]             ; r2 = *global
0x0215FAFC: ldrsb r1, [r0, #0xb]       ; r1 = char_struct+0x1B + i   <- the packed list byte
0x0215FB00: ldr   r3, [r2, #0x50]      ; r3 = the {kind,id} table
0x0215FB08: ldrb  r2, [r3, r1, lsl #2] ; r2 = table[byte].kind
0x0215FB0C: add   r1, r3, r1, lsl #2   ; r1 = &table[byte]           <- what the handler receives
0x0215FB10: ldr   r2, [sb, r2, lsl #2] ; dispatch[kind], sb = 0x02172210
0x0215FB14: blx   r2
```

`CONFIRMED_STATIC`: the packed list at `char_struct+0x1B` is the **iteration source**; the `{kind,id}` table is the **lookup target**. The handler's `[r1,#1]` reads the id from the entry the list byte selected. Poking the list changes which entries dispatch, and a respawn re-cache **would** rebuild the bitset from the modified list. The runtime loop's variant is valid.

**How I got it wrong.** P177 says "the array lives at `[obj+0x50]`" and I read that as the iteration source. It's the lookup target. P178 already had the answer — *"the record holds the index list; the table holds the `{kind,id}` pairs those indices point into."* I checked one finding and skipped the adjacent one that answered the question. Rule 7, in my own record, and the cost landed on the partner: a held run on a warning my own notes contradicted.

What survives: to change **which ability an id means** (not which ids a character has), the table at `[global]+0x50` is the place — stride 4, kind at `+0`, id at `+1`.

### The `{kind,id}` table — closed after nine deferrals

`CONFIRMED_STATIC`. Table at `[global]+0x50`, **stride 4**, `kind` at `+0`, `id` at `+1`, indexed by the packed list byte from `char_struct+0x1B`. Each entry dispatches through a second table at `0x02172210` indexed by `kind`; `table[0]` is the bit setter `0x0215FB3C`, and four consecutive slots hold `0x0215FFDC`, a bare `bx lr` — kinds that do nothing at load. The binary self-names the dispatch table: the bytes before it read `"Init"` then `"BattleCharaDataLoad.cpp"`.

Nine deferrals on an item that was load-bearing for exactly the question I got wrong. The deferral is the error worth recording, not the finding.

### The `chr_b` correction — accepted

**An ability-free opponent cannot be built.** All four records with empty ability arrays — 70, 71, 72, 73 — are the Debug series (`dt_b_01`–`dt_b_04`, jpower 0) and aren't selectable. The doc's `chr_b[70]` baseline was reached by a route that no longer exists, and **the 8.000 unresisted figure has never been obtainable in-game.** Every workaround in this campaign was engineering around an unreachable target.

The runtime loop's deck design also beats mine on merit. Only three non-debug characters carry id 9: `chr_b[12]` Luffy `[9,25,12]`, `chr_b[18]` Robin (identical set), `chr_b[67]` Edajima `[9,10,56]`. No character is Luffy-minus-9, so my "matched pair differing in exactly one ability" is unavailable. Edajima shares **only** id 9, so a single measurement implicates id 9 and excludes 25 and 12 — sharing nothing else is more informative than differing by one thing. Robin is the replicate arm: same set, different character.

### Tooling status

The `jus-fun` write-watchpoint patch is **built**. The three deprioritised threads — `scratch+0xA4` term writer, `ColPrmMan+0x48` list insert, remaining computed-offset scans — are unblocked by a single `JUS_WATCH=` stop. They stay deprioritised as *static* work: a watchpoint names the writer directly, whereas everything I can add only narrows which shapes are possible.
