## P192 — the residency card was the wrong shape, and 9 stores stay open

Runtime ran the P191 residency card. It cleared 12 of the 21 stores, not 19, and my expected outcome for ov12 was wrong.

The positive control landed first, which is what makes the nulls meaningful: ov6 — known resident because the damage code runs there — matched 768/768 bytes at three offsets. The method works.

| Overlay | Stores | Sampled match | Verdict |
|---|---|---|---|
| ov10 | 10 | 10/768 = 1.3% | NOT RESIDENT — cleared |
| ov01 | 2 | 19/768 = 2.5% | NOT RESIDENT — cleared, and independently excluded by the aliasing map |
| ov12 | 9 | **mixed** | not cleanly excluded |

ov12 is **partially resident**. Its head reads all zeros in RAM while the file holds ARM code, but at `+0x20000` — `0x021CC1C0`, inside ov12's own span, not another overlay aliasing the address — runtime measured 128/128 with 55 distinct byte values and a recognisable 16-byte prefix identical in file and RAM. Real image content at its correct address with the head zeroed out: a stale remnant partially overwritten. Neither resident nor absent.

### Why the card was wrong, not just imprecise

I wrote a **binary** failure signature — "a match means the overlay IS resident, so its `+0xE8` stores are live candidates" — for something that isn't a property of an overlay at all. Residency here is per-address. The card would have given a confident wrong answer either way: a head-region read clears ov12 falsely, a `+0x20000` read condemns all nine falsely. Same root cause.

**Rule 17: when you write a binary failure signature, check that the underlying property is binary.** Mine assumed overlays are loaded or not loaded.

Runtime caught their own near-miss too: 128/128 is exactly what a zero-filled region produces, so a full match and nothing-there share a signature until you inspect byte content. They ran that check before reporting. Note the shape — a **negative** control on a **positive** result, the reverse of how we've been using controls.

### A correction to my own handoff

`0x021B461C`, the single address I gave them, is a **LOAD** (`0x6801`), not a store (`0x6001`). Their byte-check cleared a load, and **none of ov12's 9 stores has been individually checked**. The tally is 12 cleared, 9 open — not 8.

### The 9 ov12 stores

| Address | File halfwords | Encoding |
|---|---|---|
| `0x021B4622` | `30e8 6001 1c20 30ec` | `adds r0,#0xE8` / `str r1,[r0]` |
| `0x021B4876` | `30e8 6001 1c20 30ec` | same |
| `0x021B4CCC` | `31e8 6008 1c29 31ec` | `adds r1,#0xE8` / `str r0,[r1]` |
| `0x021B4EC8` | `31e8 6008 1c29 31ec` | same |
| `0x021C6032` | `30e8 6001 1c20 30ec` | same as the first |
| `0x021C628E` | `30e8 6001 1c20 30ec` | same as the first |
| `0x021C6666` | `31e8 6008 1c20 6801` | `adds r1,#0xE8` / `str r0,[r1]` |
| `0x021C6B60` | `30e8 6001 4770 0000` | store then `bx lr` |
| `0x021CC29A` | `31e8 6008 2066 490d` | store; **sits at `+0x2010DA`, inside the measured 128/128 window** |

`0x021CC29A` is the highest-value single check of the nine — the one I'd expect to be present.

The four repeated `30e8 6001 1c20 30ec` sequences look like one inlined accessor duplicated, which suggests a compiler-generated setter family. That's a prior, and rule 16 says don't retire candidates on it. Recorded, not acted on.

### State of `+0xE8`

Narrower than P191, not closed: **12 cleared, 9 open.** A failed runtime trace still wouldn't finish the static side.
