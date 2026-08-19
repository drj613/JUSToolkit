# jpower move damage: damage1 = displayed damage × 5

Loop-Atlas iteration 34. Static. The per-move damage value is located — and most of it was already written down.

## Record layout confirmed

`bin/jpower.bin` is **94544 bytes = 311 entries × 304 bytes** exactly. `jpower-Mapping.md` named the block-0 fields but not their offsets. Found them by reproducing that doc's published column, 9 of 9:

| offset | field | distinct values | range |
|---|---|---|---|
| `+0x0C` | **damage1** | 16 | 0..200 |
| `+0x0E` | **damage2** | 17 | 0..200 |
| `+0x10` | **damage3** | — | — |

CONFIRMED — matching nine independently-published values rules out coincidence.

## damage1 is displayed damage × 5

Every damage1 value in the file: `5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 100, 144, 150, 200`.

**All multiples of 5 except `144`.** The project's formula `floor(damage1/5) + (tier-2)` divides evenly, so damage1 is just **displayed damage × 5**. Designers picked the display number; the file stores it scaled up.

This makes `(tier-2)` a genuine per-character modifier, not part of the scaling. (`144` is the lone outlier — it's also Naruto's base HP, probably coincidence.)

## Both measured moves map to a unique damage1

| move | measured | required `floor(damage1/5)` | damage1 | entries with it |
|---|---|---|---|---|
| B | **8.000** | 8 | **40** (unique) | 16 |
| DOWN+B | **7.000** | 7 | **35** (unique) | 4 |

No other damage1 produces 8 or 7. With `tier-2 = 0`, the corrected measurements land exactly on real file values — an independent check on the harness session's `+2.0` net-of-regen correction, using data written before that correction existed.

## chr_b[0x02] REFUTED as tier; chr_b[0x01] fits

Last iteration I proposed `chr_b[0x02]` (values `2..6`) as the formula's `tier`. **That's wrong.**

Goku's B measures `8.000` with damage1 = `40`, so `floor(40/5) = 8` and `(tier-2)` must be **0** — meaning `tier = 2`. Goku's `chr_b[0x02]` is **3**, and both targets read **5**. Neither is 2.

`chr_b[0x01]` works: Goku reads **2**, and so do both targets, giving `tier-2 = 0` and `damage = damage1/5` exactly. Its distribution `{1:11, 2:56, 3:7}` yields a modifier of `{-1, 0, +1}` for 18 of 74 characters — a reasonable shape for a tier adjustment.

So my two candidates swap: **`chr_b[0x01]` is the tier candidate (PLAUSIBLE)** and **`chr_b[0x02]` is refuted as tier, back to unknown.** I'm not reassigning `[0x02]` to weight class by elimination — that's exactly the reasoning that produced the wrong answer last time.

This test can't distinguish attacker-side from defender-side `tier`, because Goku and both targets all read 2.

## Doc error

`jpower-Mapping.md` says Goku's B "uses `damage1=40` entries at global indices 146, 195, 218".

**Entry 146 has damage1 = 35, not 40.** Indices 195 and 218 do have 40. And 35 is exactly what DOWN+B (`7.000`) needs — so entry 146 is a **DOWN+B** candidate misfiled under B.

## Procedural note: check docs before opening binaries

Third time this phase I've rediscovered something already written down. `jpower-Mapping.md` already had the 304-byte entry size, the field names, the formula, and Goku's B at `damage1=40` — and I sat on `jpower.bin` for two wakes as "94 KB, never examined" without grepping the docs for its name.

Two prior instances (the drain trampoline in `GDB-Validation-Queue.md`, `scripts/gdb/README.md` from the other session) were recorded as lessons. This one says the lesson didn't stick, so it's a procedure now: **before opening a binary, grep the docs directory for its name.**
