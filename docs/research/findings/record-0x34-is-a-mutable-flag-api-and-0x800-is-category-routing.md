# Findings: `record+0x34` has a runtime flag API — which resolves the `0x6FF` puzzle — and `0x800` is category routing

Loop-Atlas iteration 146. Static. **Delegated:** two subagent traces plus an independent Codex arithmetic
review, all verified against the disassembly before publication.

Three open questions closed at once:

1. **`0x800`'s opposite polarity is not a contradiction.** The bit means one thing; the two sites are
   *include in your own bucket* versus *exclude from the generic pass*.
2. **`record+0x34` is NOT write-once** — it has a dedicated runtime set/clear API.
3. **Iteration 144's `0x6FF` puzzle is solved.** ov6 battle code ORs `[record+0x150] & 0xFF` into
   `record+0x34`, and `0x6FF` covers exactly bits 0–7. The construction seed was never what that test reads.

---

## 1. The `0x800` polarity, resolved

Iteration 143 recorded, unreconciled, that bit `0x800` of `record+0x38` makes execution *branch away* at
`0x0207FFD4`/`0x0207FFE4` but *proceed* at `0x0207F7A0`. Reading both branch targets settles it:

- **`0x020801D4` is the loop-continue point.** `ldr r7,[r7]; cmp r7,#0; bne #0x207fe88` advances the inner
  list, then `ldr fp,[fp]; cmp fp,#0; bne #0x207fe5c` advances the outer one. So every `bne #0x20801d4` in
  that loop — including several structurally identical single-bit tests — means **reject this pair, continue**.
  The loop's product is a filtered pair list built at `r8+0xA8`.
- **`0x0207F7C8` is simply the next category check.** The block it skips allocates a node and inserts the
  record into the list at `r6+0x88`. `0x0207F7C8` then runs the same pattern for the next category
  (`+0x34 & 0x800000` → `r6+0xC8`, then `& 0x80000` → `r6+0xD0`, …). So `0x0207F480` files each record into
  per-category lists.

Same meaning in both places — "this record is category `0x800`". One site **includes** it in that category's
bucket; the other **excludes** it from a generic pass that does not handle that category. That is ordinary
routing, not opposed semantics.

The two functions are directly connected: `0x0207F480` calls `0x0207FBD0` at `0x0207FA64`.

**One subagent claim I checked and rejected:** it reported `0x0207FBD0` as having 2 callers and called my
"0 callers" note wrong. `query.py` lists two *references* — a `functions.json` edge and a `bl` site — both
naming `0x0207F480`, so it is one caller, as iteration 143 recorded. And `0x0207F480` does have **0 callers**:
`xrefs-to` shows a single `literal_load` at `0x0207C5E8`, so it is installed as a function pointer.

## 2. `record+0x34` is a mutable flags word with a set/clear API

Four leaf functions form the API, each mirroring every change into `+0x38` **and** the `+0x08` node list:

| function | operation |
|---|---|
| `0x0207D064` | `+0x34 \|= arg1`, `+0x38 \|= arg2` |
| `0x0207D0BC` | `+0x34 &= ~arg1`, `+0x38 &= ~arg2` |
| `0x0207CF18` | same as `orr`, gated on node flag `0x20000000` |
| `0x0207CF78` | same as `bic`, gated likewise |

Verified directly:

```
0x0207D064  ldr r3, [r0, #0x34]
0x0207D068  orr r3, r3, r1
0x0207D06C  str r3, [r0, #0x34]
0x0207D070  ldr r3, [r0, #0x38]
0x0207D074  orr r3, r3, r2
0x0207D078  str r3, [r0, #0x38]
0x0207D07C  ldr ip, [r0, #8]        ; then propagate to the node list
```

And the destructor `0x0207CCD4` does `memset(record, 0, 0x188)` — the whole record, `+0x34` included — then
sets `+0x40` bit `0x200`, the free bit. Its identity is pinned by clearing `+0x5C` (the element) and `+0x60`
(the ColObj) and returning both to the pools at `[g+0xF0]`/`[g+0xEC]` off the manager global `0x0214BE10` —
the same pools the installer allocates from.

So the model is: **seeded at construction, mutated through a flag API at runtime, zeroed at destruction.**

## 3. Which solves iteration 144's puzzle

Iteration 144 found the reader at `0x0207F794` testing `record+0x34 & 0x6FF`, noted `0x6FF` excludes bit
`0x100`, and observed that the installer seeds exactly `0x100` — so the test failed on construction values.
I withheld a conclusion because a second writer might exist. It does, and it is the answer:

```
0x02165FB0  ldr r1, [r0, #0x150]
0x02165FB4  and r1, r1, #0xff       ; bits 0-7 of the record's own +0x150
0x02165FB8  bl  #0x207d064          ; OR them into +0x34
```

`0x6FF` covers bits 0–7 (plus 9 and 10). So the `0x6FF` test is reading **bits the ov6 battle code sets at
runtime from `record+0x150`**, not the installer's `0x100` seed. The apparent contradiction was an artefact of
only knowing the construction value.

Callers of the API sit in ov6 battle functions `0x02157114`, `0x02165ECC` and `0x02165FE8`, reaching the
record as `[wrapper+0x10]` — provable because `0x02083564` stores the installer's return value there
(`str r0,[r4,#0x10]`).

## 4. The `+0x5C` trap is systemic, not a one-off

Iteration 145 retracted one misattribution: a store I read as `record+0x34` was really
`[record+0x5C]+0x34`, the element's flags at the same offset. The trace found **seven** instances of that
exact shape (`0x0207EF1C`, `0x0207C0C8`, `0x0207BFD0`, `0x0207F1A4`, `0x0207F29C`, `0x020858C4`,
`0x0216FD88`, `0x0217069C`, `0x02083884`/`0x0208388C`), plus the element's own `+0x34` writers and three
unrelated structs with a field at `+0x34` (a ColObj halfword coordinate, an ov6 velocity pair, an animation
byte).

So my single retraction was catching one of a family. On an offset with ~1092 hits, the base register is the
*only* thing identifying the struct.

**The tool mis-binned the API family too.** `query.py func 0x0207D064` reports the container as `0x0207CFE0`
(396 bytes), but `0x0207D064`, `0x0207D0BC`, `0x0207CF18` and `0x0207CF78` are separate leaves. Another
instance of the merged-record hazard from iterations 125–126, now in a fourth module.

## 5. Independent arithmetic review

Seven load-bearing encoding/arithmetic claims from iterations 126–144 were re-derived from raw instruction
words by Codex, with no access to my notes or the ROM. **All seven confirmed**: the `pc+8` jump-table
indexing at `0x0207DF64`; `mvn r0,#0x3bc00` = `0xFFFC43FF` = `-(0x3C000 - 0x3FF)`; the `lsl #N`/`lsr #31`
rule extracting bit `31-N`; `smlabb` as base + index×stride; `0x6FF` excluding `0x100`; both stack-frame
argument offsets (`0x30` and `0x20`); and `0x648 + 128*0x40 = 0x2648`.

It also sharpened one claim I had blurred. On the element size I had cited two pieces of evidence as though
they supported one proposition. They do not:

- the tiling arithmetic proves the **region** divides into 128 × `0x40`;
- the `strb` to `+0x3E` proves only that **that struct** needs ≥ `0x3F` bytes.

Nothing yet proves the struct touched at `+0x3E` *is* the region's record type. So the `0x40` element size has
**two** gaps, not one — no `base + i*0x40` computation, and no link between that struct and the region.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x800`'s polarity difference is a semantic contradiction | **REFUTED** — one meaning; include-in-bucket vs exclude-from-generic-pass |
| `0x020801D4` is a loop-continue / reject point | **CONFIRMED_STATIC** — `ldr r7,[r7]` / `bne #0x207fe88`, then the outer advance |
| `0x0207F7C8` is the next category check in a chain | **CONFIRMED_STATIC** — same insert pattern for `0x800000` → `r6+0xC8`, `0x80000` → `r6+0xD0` |
| `0x0207F480` calls `0x0207FBD0` | **CONFIRMED_STATIC** — `bl` at `0x0207FA64` |
| `0x0207FBD0` has 2 callers | **REFUTED** *(subagent claim, checked)* — one caller, listed twice as an edge and a `bl` site |
| `0x0207F480` has 0 callers | **CONFIRMED_STATIC** — one `literal_load` at `0x0207C5E8`; a function pointer |
| `record+0x34` is write-once | **REFUTED** — a four-function set/clear API plus a destructor memset |
| A flag API mirrors `+0x34` changes into `+0x38` and the node list | **CONFIRMED_STATIC** — `0x0207D064`–`0x0207D07C` read directly |
| The destructor memsets the whole `0x188` record | **CONFIRMED_STATIC** — `0x0207CCD4`, then `+0x40 \|= 0x200` |
| The `0x6FF` test reads runtime bits from `record+0x150` | **CONFIRMED_STATIC** — `0x02165FB0`–`0x02165FB8` verified |
| The two ov6 objects are excluded by the `0x6FF` test | **REFUTED** *(iteration 144's withheld worry)* — the bits it tests are set later, not at construction |
| The `+0x5C` misattribution was a one-off | **REFUTED** — seven instances of the same shape |
| `query.py` bins the flag API correctly | **REFUTED** — `0x0207D064` reports as `0x0207CFE0`; four leaves merged |
| All seven audited arithmetic claims hold | **CONFIRMED_STATIC** — independently re-derived from raw encodings |
| The element is `0x40` bytes | **PLAUSIBLE** *(two gaps now named)* — no `base + i*0x40`, and no proof the `+0x3E` struct is the region's record |
| The ~90 untraced `+0x34` sites are not record writers | **not claimed** — containment argument only; Thumb, `stm`, register-offset stores and computed-`memset` blind spots all stand |

## Next angles, ranked

1. **Read `record+0x150`.** It now drives the `0x6FF` gate, so whatever writes `+0x150` decides which
   category a record lands in — the highest-value unknown in this chain.
2. **Find the consumer of the `r6+0x88` category list.** It would confirm what category-`0x800` records
   receive that the generic pass withholds.
3. **Ask the runtime side for the element stride** (already sent to `justoolkit-06`) — one memory read
   closes both gaps in the `0x40` claim.
4. **Audit `query.py`'s function binning in this module.** Four merged leaves here, eight in iteration 125,
   two in 126 — a systematic re-derivation would retire the hazard instead of rediscovering it.
