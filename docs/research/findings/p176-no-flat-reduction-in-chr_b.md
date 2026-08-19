# P176 — The flat −2.0 has no code constant and no data source in `chr_b`

**Iteration 176. Static, no emulator.**

Jumped this ahead of the polled-KO search because it can settle open card `jus-f0v` from static evidence alone.

The question: if a flat **−2.0 displayed = 128 raw** damage reduction is real, and P175 found no hardcoded `sub #0x80` anywhere in the arm9 HP/damage region, it must be **table-loaded**. The doc's own fallback is a per-character defence value, and `chr_b` is where that would live.

## The file is the array

`CONFIRMED_STATIC`: `bin/chr_b.bin` is **4440 bytes = exactly 74 × `0x3C`**. Stride `0x3C`, 74 battle characters, matching the chrb-catalog map (`[0x0214BD80]+0x40`, stride `0x3C`) and the roster count. The on-disk file *is* the record array.

## Nothing distinguishes Luffy from the dummy by 128

`CONFIRMED_STATIC`. Comparing `chr_b` 12 (Luffy) against `chr_b` 70 (the empty-ability dummy measured as "unresisted"), all 60 bytes:

- **No byte is `0x80` for Luffy and `0x00` for the dummy.**
- **No `u16` at any alignment reads 128 for Luffy and 0 for the dummy.**
- The only bytes reading `0x02` for Luffy against `0x00` for the dummy are `+0x31`, `+0x33`, `+0x35`, `+0x37` — high halves of consecutive `u16`s `0x0218`–`0x021B` at `+0x30`–`+0x37`. An ascending run of four IDs, not a defence slot.

Full diff is in the map entry. The only field where the dummy exceeds Luffy is `+0x2C` (50 vs 100), and its ratio matches neither `0.6667` for B nor `0.6000` for DOWN+B.

**The flat −2.0 has neither an implementation nor a data source**: no constant subtraction in code (P175), no per-character value in the record that could supply 128.

`not claimed`: this rules out `chr_b` specifically. A defence value could still live in koma/deck data or be computed at load into a field of the `0x1F0` battle-character object. What it closes is the doc's *stated* fallback — "a per-character defence value" — in the one table where per-character combat values are known to live.

## Bonus: Luffy's two abilities are visible in the file

`PLAUSIBLE` — a three-way agreement nobody arranged. Luffy's record carries `0x09` at `+0x03` and `0x0C` at `+0x07`; the dummy carries `0x00` at both:

```
Luffy  00 02 05 09  19 00 00 0c  2e 01 30 01  52 00 09 02 ...
dummy  00 02 05 00  00 00 00 00  36 01 37 01  33 01 be 01 ...
```

Those are **exactly the two ability IDs** from `Ability-Bitset-Is-Not-Resistance.md` for Luffy, and exactly the emptiness it reports for `chr_b[70]`'s ability array — *"verified by reading the array, not assumed"*. Three independent representations agree: the runtime bitset (`bits {9, 12, ...}`), the on-disk record bytes, and that doc's reading of the live array.

`not claimed`: the record's ability-list layout. `+0x03` and `+0x07` are four apart, suggesting 4-byte entries, but `+0x0B` reads `0x01` in *both* records, so a clean stride-4 list doesn't hold. Naming the layout needs the loader — `0x0215FB3C`, which walks the list and caches each ID as a bit.

## What this does to `jus-f0v`

Doesn't close the card, but changes what a negative result would mean. Before: "the reduction didn't replicate, so something about the old session differed." Now: **the reduction has no known mechanism, no constant in code, and no source in the per-character table** — so if `jus-f0v` comes back with both targets at 6.000 in one clean session, the right move is to **retract `Damage-Reduction-Is-Flat.md`**, not re-explain it.

The doc's *negative* half — that ability `0x09` does not confer blunt resistance through the cached bitset — is unaffected, and has since been confirmed from the opposite direction by the runtime loop measuring a bit-9 holder taking full damage.

## Queued by this wake

1. **Polled-KO discriminator** (deferred): any read of `char_struct+0x18` that branches on zero outside the apply worker.
2. `0x0215FB3C` — the ability-list loader. Names the record's ability layout; the last unexamined half of the bitset story.
3. Auto-heal's flag and per-tick amount; `0x020781E4`; `0x0215911C`.
