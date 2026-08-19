## P186 — last unexamined tree, depth-1 sweep (CONFIRMED_STATIC)

The four-point bracket ruled out the entire `0x02156DDC` span but left 7 of `0x0215C360`'s 10 callees untouched — the ones that never receive the scratch as an argument. Worth checking before the runtime loop's watchpoint attempt, since a named candidate plus an execution breakpoint would have been faster.

The seven: `0x0206C650`, `0x0207342C` (both arm9), `0x02157494`, `0x0215911C`, `0x0215AEA0`, `0x0215B460`, `0x0215C050`.

**One derives the scratch.** `0x0215B460`:

```
0x0215B488: ldr r0, [r4, #0x1a8]     ; the entity
0x0215B48C: mov r1, #0x10000000      ; bit-28 mask
0x0215B490: ldr r0, [r0, #0x10]      ; the scratch, derived the same way runtime derives it
0x0215B494: bl  0x0207CEC8           ; arm9, (scratch, mask)
```

`0x0207CEC8` is the **clear-side mirror** of `0x0207CE7C` (the OR side, already read):

```
0x0207CEC8: ldr r2, [r0, #0x3c] / mvn r3, r1 / and r1, r2, r3 / str r1, [r0, #0x3c]
            then walk the list at [scratch+8], clearing the same mask from +0x1C and [+8]+0x14
```

It clears bit 28 from `scratch+0x3C` and propagates the clear down the list. Flag maintenance — no word store near `+0x134`. The whole `0x0215C360` subtree is flag and list upkeep, consistent with its three scratch-taking callees (`0x0207CE7C`, `0x0207D180`, `0x0207D418`). This closes the gap rather than leaving it open.

**None of the seven writes `+0x134`.** Their only stores are byte and halfword writes to small offsets — `+0xBC`, `+0x5CE`, `+0x78`, `+0xC`, `+0xE`, `+0xCE`, `+0x11B`, `+0x11C`, `+0x11D` — plus two word stores in an arm9 helper to `+8` and `+0xC`. `+0x134` is read as a word (`ldr r4, [r1, #0x134]`), so none of these can be it.

**Depth limit, stated not glossed.** This closes depth 1, not the subtree. `0x0215911C` (the expiry handler, 7 callees) reads `[r5+0x1A8]` twice but never takes `+0x10`; it passes the **entity** to `0x021591F4` and `0x02159210`, so a deeper callee could still derive the scratch on its own. One level examined, one scratch-reaching path found, subtree not exhausted.

**What it means for B11:** the bracket's unexamined tree holds no plausible writer at depth 1, so no named-candidate execution breakpoint is available. The watchpoint stays the only route.

**Instrument note — the null was false twice over.** The first scan returned seven clean nulls, all wrong. Two independent bugs: `grep -E` doesn't understand `\s`, so every store count came back as a spurious zero; and an empty overlay argument made `query.py` exit with a usage error, so two of the "seven" were never disassembled at all — a null over five functions reported as a null over seven. A positive control on `0x0215C360`, known to contain stores, caught both. The control only got run because a column of identical zeros looked too tidy — the same tell as the clean listing in rule 8. Third false null this session, and the third time the null was the dangerous result.
