# P178 — The ability list lives in `chr_b` at `+0x02`/`+0x03`, and Luffy has one ability his record doesn't explain

**Iteration 178. Static.** The runtime loop found the loader's source: `r6 = char_struct + 0x10`, count at `char_struct+0x1A`, list bytes from `char_struct+0x1B`. Two live lists:

```
player    count=2  bytes=[7, 15]          -> 0x00008080   (measured 0x00008080)
opponent  count=4  bytes=[9, 25, 12, 14]  -> 0x02005200   (measured 0x02005200)
```

The player is `chr_b` 0 (Goku), the opponent is `chr_b` 12 (Luffy), so both are checkable against the file.

## The record holds the list — layout was wrong

`CONFIRMED_STATIC`. Not stride-4 `{kind, id}` pairs. A slot count sits at record `+0x02`, then up to six one-byte ability slots run from `+0x03`, with zero meaning empty:

```
chr_b  0 (Goku)   count@+0x02 = 3   slots = [7, 15, 0]           non-zero = [7, 15]
chr_b 12 (Luffy)  count@+0x02 = 5   slots = [9, 25, 0, 0, 12]    non-zero = [9, 25, 12]
chr_b 70 (dummy)  count@+0x02 = 5   slots = [0, 0, 0, 0, 0]      non-zero = []
```

Goku's non-zero slots match the live list `[7, 15]` exactly — count and order. Across all 74 records the count at `+0x02` falls in **2–6**, so the slot region is `+0x03`–`+0x08` and never overruns.

This also clears up a number that looked contradictory. `Ability-Bitset-Is-Not-Resistance.md` reports `chr_b[70]`'s ability array as *"count = 0 — verified by reading the array, not assumed"*. Its raw slot count is **5**, but all five slots are **zero**, so the effective count really is 0. Same structure, read from opposite ends.

## P177 correction: the refutation was right, the conclusion was wrong

At P177 I refuted my claim that the record's bytes are what the loader walks. That refutation holds — the loader dispatches through a `{kind, id}` table at `[global]+0x50`, and the record doesn't hold those pairs. Where I went wrong was deciding the record therefore wasn't the source at all, calling `r6` "a third structure." It isn't. The record holds the **index list**; the table holds the **`{kind, id}` pairs** those indices point into. Both are real and they're different objects.

The specific mistake: `r6+0x0A` reads `0x30` for Luffy's record, which I treated as "not a plausible count" and used to rule the record out. But `r6` is `char_struct+0x10`, not the record — the record's count lives at `+0x02`, and I was testing an offset that belongs to a different structure. Rule 3 again, broken in the same wake I invoked it: two structures with similar contents, and I resolved the conflict by throwing one away instead of asking whether both were real.

## Luffy has an ability his record doesn't contain

`CONFIRMED_STATIC`, and it's the important part. Luffy's live list is `[9, 25, 12, 14]`; his record's non-zero slots are `[9, 25, 12]`. **`14` is missing from the record entirely** — `0x0E` appears nowhere in those 60 bytes. The live order puts it last, appended after the record's three.

`PLAUSIBLE`: the char_struct list is the record's non-zero slots **plus abilities granted from elsewhere** — deck, koma, or support — appended at the end. Goku's list matching his record exactly is consistent: nothing was appended in that battle.

`not claimed`: what does the appending. This is now the sharpest open question in the ability system, and it matters beyond abilities — a deck-granted ability would be the first mechanical link found between the koma/deck side and battle behaviour, the bridge the reimplementation needs.

## Two corrections from the runtime loop

- The `arr=` field was garbage — ignore it. They printed `[r2+0x50]` at `0x0215FAE4`, but the array load is at `0x0215FB00`, so `r2` wasn't the global yet. Repeat captures should read **at or after `0x0215FB00`**.
- The before/after half never fired. The loader didn't re-run because the session started from `battle_rule` instead of `fight_base`, and the approach distance was calibrated for the latter, so the hit likely missed. Heartbeat confirms the session stayed live throughout — a **stimulus** failure, not an instrument one.

## Queued

1. **What appends the extra ability?** Find the writer of `char_struct+0x1A`/`+0x1B` (count and list). That names the append path, and it's the koma/deck→battle bridge if the source is there.
2. **Enumerate the `{kind, id}` table** at `[global]+0x50`. The list bytes are indices into it, making the table the actual ability dictionary. Its global loads from a pool near `0x0215FB30`–`0x0215FB40`.
3. The polled-KO discriminator, deferred three times.
