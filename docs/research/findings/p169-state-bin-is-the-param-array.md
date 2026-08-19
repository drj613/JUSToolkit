# P169 — The param array is `bin/state.bin`, and `V` can be read instead of timed

**Iteration 169. Static.** The status-duration formula (P158) is `duration = base + (base/10) * (V*2)`, with `base = paramArray[id]+0x2` and `V = [[0x02172960] + charIdx*4 + 0x4C]`. `V` has been unidentified for a dozen wakes, with the runtime loop's dumps showing it reading zero across four states and two boots.

Two results this wake: the param array is a shipped data file, so all 42 base durations are known. And the experiment to settle `V` needs no timing — the formula's result is *stored*, so it can be read directly.

## The param array is `bin/state.bin`

`CONFIRMED_STATIC`. The dispatcher reads `paramArray = [[0x02172984]+4]`. `0x02172984` sits in ov6's BSS, and the pool words around the ov6 loader that populates it are `0x02172364` → `"bin/state.bin"` and `0x02172374` → `"bin/exadd.bin"` — the same shape as `RuleData_Create` in P165, where `[ctx+4]` is a loaded file's data pointer.

`jus_files/ripped_jus_files/bin/state.bin` is **336 bytes = 42 × 8 exactly**, and parses cleanly against P158's record layout (derived from the consuming code before this file was found):

| offset | width | P158's reading | what the file shows |
|---|---|---|---|
| `+0x0` | halfword | flags; bit `0x10` picks one of two `0x18`-byte slots | only `0x0001`, `0x0002`, `0x0012`, `0x0032` occur — bit `0x10` set exactly on ids 20–34 |
| `+0x2` | halfword | base duration | `0` for every `flags & 1` entry, non-zero for every `flags & 2` entry |
| `+0x4` | **signed** halfword | per-tick amount; signed so one field covers drain and fill | positives (`10`…`60`) on instant entries, negatives (`-2`, `-4`, `-5`) on timed ones |
| `+0x6` | halfword | `not claimed` | `0x0000` in all 42 entries |

Three independent supports: P157 got 42 entries from a permutation that only closes at stride 8; the dispatcher gets stride 8 from code (`add r4, r3, r8, lsl #3`); and the file is 336 bytes — 42 × 8, nothing left over. The `flags & 1` ⇄ `base == 0` split is a fourth: a one-shot effect has no duration to scale, and the data agrees without being asked to.

## All 42 base durations

`base` is in frames. The last two columns show what the formula predicts if `V` is 1 or 2 rather than 0.

| id | flags | base | amount | ×1.2 (V=1) | ×1.4 (V=2) |
|---|---|---|---|---|---|
| 0 (`0x00`) | `0x0000` | **0** | 0 | 0 | 0 |
| 1 (`0x01`) | `0x0001` | **0** | 10 | 0 | 0 |
| 2 (`0x02`) | `0x0001` | **0** | 20 | 0 | 0 |
| 3 (`0x03`) | `0x0001` | **0** | 40 | 0 | 0 |
| 4 (`0x04`) | `0x0002` | **700** | 5 | 840 | 980 |
| 5 (`0x05`) | `0x0002` | **700** | 5 | 840 | 980 |
| 6 (`0x06`) | `0x0001` | **0** | 0 | 0 | 0 |
| 7 (`0x07`) | `0x0002` | **800** | 0 | 960 | 1120 |
| 8 (`0x08`) | `0x0002` | **800** | 0 | 960 | 1120 |
| 9 (`0x09`) | `0x0002` | **120** | 0 | 144 | 168 |
| 10 (`0x0a`) | `0x0002` | **480** | 0 | 576 | 672 |
| 11 (`0x0b`) | `0x0002` | **240** | 0 | 288 | 336 |
| 12 (`0x0c`) | `0x0002` | **120** | 0 | 144 | 168 |
| 13 (`0x0d`) | `0x0002` | **300** | 0 | 360 | 420 |
| 14 (`0x0e`) | `0x0002` | **240** | 0 | 288 | 336 |
| 15 (`0x0f`) | `0x0002` | **300** | 0 | 360 | 420 |
| 16 (`0x10`) | `0x0002` | **600** | 0 | 720 | 840 |
| 17 (`0x11`) | `0x0002` | **240** | 0 | 288 | 336 |
| 18 (`0x12`) | `0x0032` | **100** | 0 | 120 | 140 |
| 19 (`0x13`) | `0x0032` | **600** | -4 | 720 | 840 |
| 20 (`0x14`) | `0x0012` | **360** | 0 | 432 | 504 |
| 21 (`0x15`) | `0x0012` | **480** | 0 | 576 | 672 |
| 22 (`0x16`) | `0x0012` | **540** | 0 | 648 | 756 |
| 23 (`0x17`) | `0x0012` | **600** | 0 | 720 | 840 |
| 24 (`0x18`) | `0x0012` | **480** | 0 | 576 | 672 |
| 25 (`0x19`) | `0x0012` | **480** | 0 | 576 | 672 |
| 26 (`0x1a`) | `0x0032` | **240** | 0 | 288 | 336 |
| 27 (`0x1b`) | `0x0032` | **240** | 0 | 288 | 336 |
| 28 (`0x1c`) | `0x0012` | **180** | 0 | 216 | 252 |
| 29 (`0x1d`) | `0x0012` | **180** | 0 | 216 | 252 |
| 30 (`0x1e`) | `0x0032` | **480** | -2 | 576 | 672 |
| 31 (`0x1f`) | `0x0032` | **240** | 0 | 288 | 336 |
| 32 (`0x20`) | `0x0032` | **60** | 0 | 72 | 84 |
| 33 (`0x21`) | `0x0012` | **700** | -5 | 840 | 980 |
| 34 (`0x22`) | `0x0032` | **300** | 0 | 360 | 420 |
| 35 (`0x23`) | `0x0002` | **600** | 0 | 720 | 840 |
| 36 (`0x24`) | `0x0002` | **360** | 0 | 432 | 504 |
| 37 (`0x25`) | `0x0001` | **0** | 50 | 0 | 0 |
| 38 (`0x26`) | `0x0001` | **0** | 30 | 0 | 0 |
| 39 (`0x27`) | `0x0001` | **0** | 60 | 0 | 0 |
| 40 (`0x28`) | `0x0001` | **0** | 30 | 0 | 0 |
| 41 (`0x29`) | `0x0001` | **0** | 15 | 0 | 0 |

`flags & 1` entries are instant — `base` is `0`, so the formula can't move them and they're useless for this test. `flags & 2` entries are timed. `0x20` only appears alongside `0x10`; `not claimed` what either bit means beyond the slot selection P158 proved for `0x10`.

## The experiment: read the duration, don't time it

This is the part that matters. `0x02158F88` **stores** the formula's result as an unsigned halfword at `node+0xE` at apply time. `V` doesn't need a stopwatch — it needs one 16-bit read.

```
node = battleObj + 0x7C + slot*0x18        slot = (flags & 0x10) ? 1 : 0
node+0xC  = the effect id      (halfword)
node+0xE  = the duration       (halfword, unsigned) <- the formula's output
node+0x14, node+0x15 = both 1 on apply
```

`V = 0` predicts `node+0xE == base` exactly for every timed effect. Any other value means `V != 0`, and the ×1.2 / ×1.4 columns say which.

Three properties worth stating, because each dodges a constraint the runtime loop raised:

- **The ~400-frame timeline resolution doesn't apply.** This is a single read, not a span. Timing the difference between 800 and 960 would need 160-frame resolution and would have failed; reading `node+0xE` doesn't.
- **No HP baseline is involved**, so `jus-5kf` — the unexplained HP recovery on the Battle path — can't contaminate it. Either path works.
- **No clean-rules run is needed.** Items can only *add* effect nodes, and every node carries its own id at `+0xC`, so an extra node is independently readable rather than confounding. If items turn out to be what inflicts these ids, having them on is a requirement, not contamination.

**Finding the node without `battleObj`.** `battleObj` is still unresolved at runtime — it's the dispatcher's `r0`, not established to be `[0x02172960]`. But the node doesn't need it: the 42 base values are a **fingerprint set**. Scan for a halfword pair whose first member is a plausible id and whose second is one of the 42 bases (or a ×1.2 / ×1.4 multiple of one), with two `0x01` bytes six bytes later. The runtime loop already proved this technique when it recovered a slot address from the value side alone.

## What I still can't say

`not claimed`: **which in-play action inflicts which id.** P159 placed ids `0x12`–`0x22` (18–34) as status opcodes (nearly unreachable from script operands) and ids `0x01`–`0x11` as gauge effects. So the long-duration entries plausibly reachable in ordinary play are the timed gauge effects — ids 4–5 (`700`), 7–8 (`800`), and 9–17 (`120`–`600`). Mapping actions to ids is the move-script question, and it's the next static task.

Until that lands, the experiment is a **survey rather than a targeted test**: inflict anything status-like, find any node, report the `(id, duration)` pair. Whatever id turns up, the table says what `base` should have been, so a single hit settles `V` for that character.

## Queued by this wake

1. **Runtime:** the node survey above. One `(id, duration)` pair settles `V`.
2. **Static:** the move-script opcode → effect-id mapping, so the survey can become a targeted test.
3. Still open: the rest of `0x0214DADC` (the mode-12 discriminator), the code-side enumeration of callback-slot states, and the writers of `root+0x08`, `root+0x118`/`+0x11C`, and `root+0x4C`.
