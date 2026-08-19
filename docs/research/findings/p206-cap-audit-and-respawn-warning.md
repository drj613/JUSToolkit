## P206 — cap audit: every load-bearing sweep survives; respawn test warning

### The audit

`query.py search-imm` / `search-op-imm` silently cap output at 200 lines (found at P205, where a `+0x48` sweep showed 200 of **644**). Every load-bearing sweep in the campaign was re-run with `--all` and compared.

| Sweep | capped | `--all` | verdict |
|---|---|---|---|
| `search-imm 0x134` | 35 | 35 | OK |
| `search-imm 0x130` | 70 | 70 | OK |
| `search-imm 0xE8` | 134 | 134 | OK |
| `search-op-imm 0x800 --mnemonic orr` | 12 | 12 | OK |
| `search-op-imm 0x800 --mnemonic mov` | 21 | 21 | OK |
| `search-op-imm 0x134 --mnemonic mov` | 35 | 35 | OK |
| `search-op-imm 0x188` | 9 | 9 | OK |
| `search-op-imm 0x40000000 --mnemonic mov` | 2 | 2 | OK |

**Positive control:** `search-imm 0x48` gives 200 capped vs 644 with `--all` — so the comparison method actually fires when there's a difference.

`CONFIRMED_STATIC`: no campaign conclusion was affected. The `+0x48` sweep was the only one over the cap, and it was caught at the time.

### Respawn test warning

The runtime loop's ability-list poke came back a real null — stimulus present, control alternating, poke verified to persist after hits. Next step is the respawn variant, since the bitset is re-cached in place on KO. Their stated caution: a respawn might restore a pristine copy rather than re-read the modified list.

**The record says that caution is likely to bite.** P177 documented the bitset writer, ov6 `0x0215FB3C`:

```
0x0215FB40: ldrb lr, [r1, #1]          ; ability ID from ENTRY+1
0x0215FB44: add  ip, r0, #8            ; bitset base = r0 + 8
0x0215FB4C: asr  r3, lr, #5            ; word index = ID >> 5
0x0215FB58: orr  r0, r2, r1, lsl r0
0x0215FB5C: str  r0, [ip, r3, lsl #2]
```

It reads each ability ID from **`entry+1`** — so the source is an array of entries at least 2 bytes wide with the ID at offset 1. That is **not** the packed byte list they poked at `char_struct+0x1B`, where IDs sit consecutively (`[9,25,12,14]` → `[25,12,14,0]`).

`PLAUSIBLE`: the respawn re-cache rebuilds the bitset from that **entry array**, not from the packed list. If so, poking `char_struct+0x1B` won't survive the respawn — producing a null with no stimulus, the exact failure they tried to avoid. Worth locating the entry array and poking *that* instead, or verifying the source at `0x0215FB3C`'s caller before spending the run.

Stated as plausible, not confirmed: both representations may exist, and `0x0215FB3C`'s caller hasn't been traced yet. That trace is the next static task and directly serves their load-time consumption question.

### Scoped question

They asked where abilities are consumed at character **load** (not hit time), and whether a **derived** per-character defence or scaling field is written once at battle start. P177 already names the loader and its module, `BattleCharaDataLoad.cpp`. What's missing: whether that loader also computes a **scalar**. The bitset is a copy, not a derived value, and their measurement shows it has no effect at hit time. Finding a derived field means reading `0x0215FB3C`'s caller and the rest of the load path. Next wake.
