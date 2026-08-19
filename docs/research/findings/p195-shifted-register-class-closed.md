## P195 — shifted-register class scanned and empty; P181's last named gap closes

P181 called this class "a genuine gap, not theoretical" and left it open for fourteen iterations. The pattern: `str rX,[rBase, rIdx, lsl #2]` where `rIdx` holds `off/4`. Neither `search-imm` (no literal offset in the encoding) nor the existing `add`/`mov` scan (wrong constant) can see it.

Added `scan_shifted()` to `scripts/analysis/regoff_store_scan.py`. Covers arm9 and every overlay, same as the rest of the tool.

### Two controls, establishing different things

**1. Matcher control** — runs before any scan, aborts on failure. Hand-encoded instructions checked both directions:

| Encoding | Expected | Result |
|---|---|---|
| `0xE7841102` = `str r1,[r4, r2, lsl #2]` | match on index `r2` | matches |
| `0xE7941102` (bit 20 set, a **load**) | must NOT match | correctly rejected |
| `0xE7841102` against index `r3` | must NOT match | correctly rejected |
| `0xE3A0203A` = `mov r2,#58` | match | matches |

**2. Scan-level control** — proves the pattern fires on real code. `+0x80` produced one hit.

### The control hit is a false positive, and that's the useful part

```
0x0203FDF8: mov r2, #0x20            <- the scanner's anchor
0x0203FDFC: add r1, r1, r7, lsl #5
0x0203FE00: bl  0x0204572C
0x0203FE04: ldr r2, [sp, #0x2c]      <- r2 IS OVERWRITTEN
0x0203FE0C: str r0, [r3, r2, lsl #2]
```

`r2` is reloaded from the stack before the store, so the index isn't `0x20` there. The scanner has no clobber tracking. That makes its precision poor — but it proves the scanner reaches real code and fires, which is what a positive control needs to establish. Separate question from whether the hit is real. Both facts recorded; neither substitutes for the other.

### Results

| Offset | Shifted-class candidates |
|---|---|
| `+0xE8` | **0** (its 30 candidates are all the older `add`/`mov` class; 22 in unbinned code) |
| `+0x130` | **0** |
| `+0x134` | **0** |

`CONFIRMED_STATIC`, scope stated: no shifted-register word store to `+0xE8`, `+0x130`, or `+0x134` exists in arm9 or any overlay, where the index register is set by an unconditional `mov rN,#imm` within 8 instructions of the store.

### Residual gap, named narrowly

The scan misses an index register that is:

1. **Loaded from a literal pool** (`ldr rN,[pc,#…]`) instead of `mov`-ed — the encoding class I already argued is the likely hiding place for the bit-11 mask, so it's the one I'd least like to be blind to;
2. Set more than 8 instructions before the store;
3. Computed rather than assigned.

P181's gap is closed. A narrower one now stands in its place. That's progress, not exhaustion.
