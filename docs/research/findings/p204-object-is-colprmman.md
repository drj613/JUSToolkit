## P204 — Retracting P203: `0x0220DDE0` is the `Battle_ColPrmMan`, and 19 is the constructed count

Third name for this object. First one backed by a test that could actually fail.

### The `ColMan`'s constructor accounts for every byte — and has no `0x188` stride

`0x0207AD3C` initializes its object across three loops:

| Region | Elements | From |
|---|---|---|
| `+0x010`–`+0x090` | 16 × `8` | loop `0x0207AD74`–`0x0207AD90`, stride `8` |
| `+0x09C`–`+0xF9C` | 192 × `0x14` | loop `0x0207AE38`–`0x0207AE58`, bound `r6 < 0xC0` |
| `+0xF9C`–`+0x219C` | 384 × `0xC` | loop `0x0207AD94`–`0x0207ADB4`, stride `0xC` |

That lands exactly at `0x219C`, the allocation size — no gap, no `0x188`-stride array anywhere. The object runtime scanned can't be the `ColMan`.

### The discriminator: slot arithmetic that actually constrains

| | `Battle_ColMan` `0x219C` | `Battle_ColPrmMan` `0xFB54` |
|---|---|---|
| 128 slots at `+0x454` stride `0x188` need `0xC854` | **does not fit** | fits |
| `0x188`-stride array in constructor | **absent** | present, `0x0207C788`–`0x0207C7B4` |
| `0x022100D4` = `+0x22F4`, slot 20 exact | **outside** | inside |

Every address hits an exact boundary: player `+0x1E5C` = slot **17**, opponent `+0x1FE4` = slot **18**, `0x022100D4` = `+0x22F4` = slot **20** — all zero remainder. The term source `+0x2088` is slot 18 `+ 0xA4`, independently reproducing the `+0xA4` sub-array offset we already had.

`CONFIRMED_STATIC`: **`0x0220DDE0` is the `Battle_ColPrmMan`** — `0xFB54`, `BattleColPrm.cpp` / `Battle_ColPrmManCreate`, line `0x132`, allocated by `0x0207C4C0`. The causal chain agrees: `0x0207F480`, the pipeline's caller, is installed at `0x0207C5E8` inside `0x0207C4C0`, whose `r4` is that allocation — so the pipeline receives the `ColPrmMan`.

### Retracted: "19 is the declared length"

P203 argued 19 was declared because 20 slots would overflow `0x219C`. That used the wrong size. Against `0xFB54` the array holds **128 declared slots**, of which **19 are constructed**. The runtime loop's original caveat was correct. Both the P203 answer and its confidence label are withdrawn.

### Un-withdrawn: `0x022100D4` is manager-internal after all

We both withdrew this — they at my prompting. Against the true size it's inside, and it's slot 20's base exactly. The original reading was right; both withdrawals were wrong.

`PLAUSIBLE`: since each element is `0x188` bytes, `scratch+0x188` is the next element's first word. Slot 19's first word holding slot 20's base suggests the 128 slots are chained through `+0x00` as a **free list**, with player→opponent→null being the **active** list. That fits `+0x00` as a link rather than a vtable, which we established independently.

### The rule this cost three wakes to learn

A containment test can't tell objects apart — it passes for anything large enough, and automating it changes nothing. Both of us ran that non-check and both called it verification. What settled it was **exactness**: slot indices with zero remainder, a constructor that covers every byte, and an array that fits one candidate but not the other. Each of those could have come out differently.

**Rule 34: scripting a check doesn't make it a check. What makes it one is that it could have failed.**
