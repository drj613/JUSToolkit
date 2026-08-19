## P202 — the pipeline's object is the `Battle_ObjMan`, and every scratch lives inside it

Runtime shows `0x02081DDC` gets called (6 entries, `r0 = 0x0220DDE0`) but its loop body never runs (0 fires at `0x02081EA8`, unconditional counter, any element). `0x0215AC08` fires twice at `f134=384`. Rule 26's scenario, measured. The higher-value question: what *is* `0x0220DDE0`?

### Named, from the self-naming allocator

`sl = r0` at `0x02081DE4` — the pipeline's argument is the object itself, and `[sl+0x48]` is a list head on it. Both loops in `0x02081DDC` walk that same list (`0x02081DEC` and `0x02081EA0` each load `[sl,#0x48]`), so an empty list makes the whole function a no-op. That matches the measurement exactly.

`0x0207F480` (the pipeline's caller, 0 callers itself, so an installed callback) appears as data once, at `0x0207C5E8` — inside `0x0207C4C0`, the constructor with the inline handler table from P187. That constructor is called from `0x02083204`, which allocates:

```
0x0208320C: ldr r1, [pc, #0x234]   ; file string 0x0209FFF4
0x02083210: ldr r0, [pc, #0x234]   ; size        0x000042D8
0x02083214: ldr r2, [pc, #0x234]   ; func string 0x0209FFE0
0x02083218: mov r3, #0x50          ; line 80
0x0208321C: bl  0x0201A21C         ; the tagged allocator
```

Strings from `arm9.bin`: **`BattleObj.cpp`** and **`Battle_ObjManCreate`**. `CONFIRMED_STATIC`, and convergent with the charter, which already had `Battle_ObjManCreate` at `0x0208321C` with size `0x42D8` — reached here independently through pool words and the string table.

### Every address in this investigation is inside that one allocation

`0x0220DDE0 + 0x42D8` spans `0x0220DDE0`–`0x022120B8`:

| Address | Offset in `ObjMan` | |
|---|---|---|
| player scratch `0x0220FC3C` | `+0x1E5C` | inside |
| opponent scratch `0x0220FDC4` | `+0x1FE4` | inside |
| term source `0x0220FE68` | `+0x2088` | inside |
| `+0x188`'s target `0x022100D4` | `+0x22F4` | inside |

The two scratches are sub-objects embedded in the `Battle_ObjMan`, not separate allocations. `0x022100D4` — previously logged as an unidentified pointer — is `ObjMan`-internal. That's why no word in a scratch points into its own range: the containing structure holds the topology.

The empty list at `ObjMan+0x48` is a different collection from the doubly-linked scratch pair. Our fighters aren't in it.

### Card verdict, and why I'm not treating mine as refuted

My `0x02081F5C` card fails by a third route, not the one I specified. My failure signature was "bit 15 never set, or `r2 != 1`" — neither was tested, because the instruction is never reached. The gate and `r2` remain **UNKNOWN, not refuted**. If an executing path appears, the card is testable again as written. Their framing, and the right one: live-but-unreached, not killed on its merits.

Same for the `+0xE8` / `+0x130` accumulators — real code, same unexecuted body. The structural insight stands (three of four damage fields accumulate through one interior pointer, explaining why the offsets never appear directly), but its location doesn't help on this path.

### Two weaknesses they flagged, both worth keeping

Their first run filtered on *(opponent object)* OR *(bit 15 set)* — two filters, three cases, leaving "executed with another object and bit 15 clear" invisible. That run couldn't answer "did it execute at all," which was the actual question. An unconditional counter closed it. And "entry fires" vs. "body does not" came from two separate gdb sessions (the stub allows one connection per launch) — flagged rather than presented as a single observation.

### One of mine

I first computed the allocation's end address in my head as `0x022140B8`; it's `0x022120B8`. All four containments still held, but only because I scripted the arithmetic instead of trusting the mental version. Hex addition by eye is not a check.
