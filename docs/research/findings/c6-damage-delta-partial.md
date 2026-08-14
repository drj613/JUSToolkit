# C6 — the damage delta is a parameter, not a table (partial)

Loop-Atlas iteration 20. Static. **Honest status: the trail goes cold one level above where I hoped.** No move-damage table yet. Recording the shape so the next attempt starts higher.

## What the eight ARM sites do

They're all cases in one switch, and they all do the same thing:

```asm
0x02157DB8  ldr r0,[r5,#0x1B4]   ; target character pointer
0x02157DBC  mov r1,r4            ; delta
0x02157DC0  bl  0x020783CC       ; apply
0x02157DC4  b   0x02157F90       ; switch exit
```

Same pattern at `0x021582C4`. `r5+0x1B4` is the target, and **`r4` is the delta** — set before the switch, not per-case.

## Where r4 comes from (and why this is a dead end)

Every write to `r4` in the enclosing function:

| site | instruction |
|---|---|
| `0x0215795C` | `ldr r4,[r0,#0x8]` |
| `0x021579EC` | `ldr r4,[r0,#0x18]` |
| `0x02157A4C` | **`mov r4,r3`** |

That `mov r4,r3` means the delta is a **function argument**. This dispatcher doesn't read damage from a data record — it receives an already-computed number and routes it. The `ldrsh r1,[r1,#4]` the harness session saw must live at one of the six sites I haven't decoded, not these two.

**Bottom line: move damage isn't tabulated here, so C6 as scoped can't produce a table.** The value is computed by this dispatcher's caller, one level up. That's where the next attempt starts.

## Verification targets

Against an ability-free target, the harness session measured:

| move | displayed | raw |
|---|---|---|
| Goku B (punch) | **6.000** | 384 |
| Goku DOWN+B | **5.000** | 320 |
| Goku UP+B | multi-hit 1.0, 2.0, 1.0, 1.0 | — |

Damage is authored in **displayed** units (the apply sites do `lsl #6`), so a real table should hold literal `6` and `5`. UP+B being multi-hit means a table needs per-hit values distinct from string totals — multiple records, or a repeat count.

## No per-character flat-defence field in chr_b

The harness session asked whether their measured **−2** might be a per-character defence stat instead of ability `0x09`. I compared `chr_b[70]` (コマレッド, the ability-free target) against `chr_b[12]` (ルフィ) across all 60 bytes.

Four fields differ by exactly 2 — `0x31`, `0x33`, `0x35`, `0x37` — but they're the **high bytes of u16 values** at `0x30`/`0x32`/`0x34`/`0x36`, not standalone stats. Read as u16: `536, 537, 538, 539` for Luffy, `0,0,0,0` for コマレッド. Not defence.

Nothing else looks like a flat defence value. That **weakly supports** attributing the −2 to ability `0x09` — weakly, because absence of an obvious field isn't proof, and I only compared two records.

Also: `chr_b[70]` is **コマレッド** ("Koma Red"), a mascot character; `chr_b[72]` is コマイエロー. Its four ID slots are all zero and its ability array is empty — exactly why it works as a clean unresisted target.

## An over-fit I backed out of

The four u16s at `chr_b +0x30`–`+0x36` looked like a per-character base plus 0,1,2,3 (Naruto `362,363,364,365`; Luffy `536,537,538,539`). Checked all 74: only **15 are sequential**, 8 are all-zero, and **51 are neither** (Goku is `337, 0, 338, 0`). So they're four independent IDs that happen to be contiguous for some characters. I tried matching the non-zero count to panel-size counts and failed. Recording as an unresolved field, not a pattern.

## Next step

Find the callers of the dispatcher containing `0x02157A4C` and decode where its `r3` argument is produced. `scripts/decomp/find_callers.py` handles this now that it covers Thumb.
