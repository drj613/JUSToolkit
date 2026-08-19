# Findings: the driver, not stage 1, is the primary bucket filler

Loop-Atlas iteration 63. Static.

Traced what inserts into bucket 6, the collision pipeline's input. **The driver itself** does it,
at arm9 `0x0207F6B4`. This also revealed the driver fills **ten** buckets — not zero, as I assumed
when calling stage 1 "the bucket filler" in iteration 61.

---

## 1. One link call in the ROM targets bucket 6

Censused every call to the list-link helper `0x02037B98` across all binaries, recovering `r0`'s origin at
each site: **145 link calls**, **exactly one** targeting `+0x58`.

```
arm9  0x0207F6B4   r0 <- add r0, r6, #0x58      <<< bucket 6
```

The other 144 target different offsets on other objects. One unambiguous producer — same
"match the computation, not the offset" approach that found the contact-array writer in iteration 56.

## 2. The driver fills ten buckets

`0x0207F6B4` sits inside `0x0207F480`, the per-frame driver. Iteration 57 established `r6` holds the
manager; re-verified here with **zero writes to `r6`** after `0x0207F490`.

Every link/unlink in the driver off `r6`:

| site | op | offset | target |
|---|---|---|---|
| `0x0207F4B8` | link | `+0x0D8` | free list |
| `0x0207F51C` | link | `+0x0D8` | free list |
| `0x0207F53C` | link | `+0x020` | (not a bucket head) |
| `0x0207F5C4` | link | `+0x080` | **bucket 11** |
| `0x0207F610` | link | `+0x098` | **bucket 14** |
| `0x0207F648` | link | `+0x028` | **bucket 0** |
| `0x0207F688` | link | `+0x090` | **bucket 13** |
| `0x0207F6B4` | link | `+0x058` | **bucket 6** |
| `0x0207F744` | link | `+0x070` | **bucket 9** |
| `0x0207F77C` | link | `+0x0B0` | **bucket 17** |
| `0x0207F7C4` | link | `+0x088` | **bucket 12** |
| `0x0207F7F0` | link | `+0x0C8` | **bucket 20** |
| `0x0207F81C` | link | `+0x0D0` | **bucket 21** |

Each bucket link is immediately preceded by an **unlink from the free list** (`0x0207F5B4`, `0x0207F600`,
`0x0207F638`, `0x0207F6A4`, `0x0207F734`, `0x0207F76C`, `0x0207F7B4`, `0x0207F7E0`, `0x0207F80C`).

Pattern: **take a node off the free list, file it into a bucket.** Ten times, in sequence.

Combined with iteration 55, the driver's per-frame shape is:

```
0x0207F480  drain all 22 buckets back to the free list at +0xD8   (the loop, iteration 55)
            allocate 10 nodes from the free list into buckets
              0, 6, 9, 11, 12, 13, 14, 17, 20, 21
            run the 8 stages
```

Buckets are rebuilt from scratch every frame, not maintained incrementally.

## 3. Correcting iteration 61

Iteration 61 called stage 1 "the bucket filler". **Incomplete**: stage 1 fills 4 buckets (5, 7,
15, 16) by redistributing bucket 6's contents, but the driver fills 10 before stage 1 ever runs.

The mistake: I scanned stages 1–8 for link calls and found them only in stage 1, without checking whether
the *driver* — the function that calls those stages — also links. It does, between the drain and the
stage calls, in code I had wrongly characterised (iteration 55) as just a reset.

Third time this function has been misread by looking at part of it. 440 instructions, three distinct jobs.

## 4. Producer coverage

| | buckets |
|---|---|
| filled by the driver | 0, 6, 9, 11, 12, 13, 14, 17, 20, 21 |
| filled by stage 1 | 5, 7, 15, 16 |
| **no producer found** | **1, 2, 3, 4, 8, 10, 18, 19** |

14 of 22 buckets now have a known producer.

Two of the remaining eight have known *consumers* but no producer: **bucket 1** (read by stage 8's callee
`0x02080F14`, iteration 60) and **bucket 8** (read by stage 3). Either something outside the driver fills
them, or they use a path that bypasses the `0x02037B98` helper.

## Predictions status

| Claim | Verdict |
|---|---|
| Exactly one ROM site links into bucket 6 | **CONFIRMED_STATIC** — `0x0207F6B4`, 1 of 145 link calls |
| Bucket 6's producer is outside the pipeline | **REFUTED** *(iteration 62)* — it is inside the driver |
| Stage 1 is the bucket filler | **REFUTED** *(my own, iteration 61)* — incomplete; the driver fills 10 first |
| The driver fills buckets 0, 6, 9, 11, 12, 13, 14, 17, 20, 21 | **CONFIRMED_STATIC** — 10 link calls off `r6`, 0 writes to `r6` |
| Each bucket fill is preceded by a free-list unlink | **CONFIRMED_STATIC** — 9 paired unlinks at `+0xD8` |
| Buckets are maintained incrementally across frames | **REFUTED** — drained wholesale, then rebuilt each frame |
| Buckets 1 and 8 have producers in the driver or stages | **REFUTED** — consumers exist, producers do not |
| Each driver link runs in a loop | **not claimed** — the sites are sequential, not obviously looped |

## Next angles, ranked

1. **Find producers for buckets 1 and 8** — both have consumers, so insertion paths exist but bypass
   `0x02037B98`. Likely direct pointer stores.
2. **Identify what the ten allocated nodes represent.** One node per bucket per frame suggests ten fixed
   roles, not a variable population.
3. **Identify stage 1's four branch conditions** (carried) that sort bucket 6 into 5, 7, 15, 16.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
