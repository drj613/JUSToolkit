# Findings: the census now scans both allocator entries — 732 → 1135 sites, and the ARM pass had no size bound

Loop-Atlas iteration 134. Static. Tooling.

Iteration 133 found that `0x0201A21C` is only a linker veneer and the real allocator is `0x0201A228`, and
left one question open: *do any tagged calls reach `0x0201A228` directly?* Extending
`alloc_census.py` to scan both entries answers it and turned up a bug that had nothing to do with the
veneer.

1. **732 → 1135 sites.** 403 previously-invisible calls, all through the direct entry.
2. **Zero of those 403 carry a source filename.** Iteration 133's open question is now answered: **no.**
3. **The ARM pass had no plausibility bound on sizes** — only the Thumb pass did. One direct site reported a
   34 MB allocation.

---

## 1. The change

`ALLOC = 0x0201A21C` became a pair, and every row records which entry it used:

```python
ALLOC_ENTRIES = {0x0201A21C: 'veneer', 0x0201A228: 'direct'}
```

Both the ARM and the Thumb scanners look up the branch target in that table instead of comparing against
one address. Output gains an `entry` column and a header line reporting the split.

```
entry points: 732 via the 0x0201A21C veneer + 403 direct to 0x0201A228 = 1135;
of the direct ones 0 carry a resolved name
869 ARM + 266 Thumb = 1135 allocator calls; 981 with an unconditional immediate size
```

## 2. The open question, answered: the direct entry is untagged

| entry | sites | with a real source filename |
|---|---|---|
| veneer `0x0201A21C` | 732 | **572** |
| direct `0x0201A228` | 403 | **0** |

Not one of the 403 resolves to a `.cpp` or `.h`. So iteration 130's boundary is clean in both directions:
tagged code always goes through the veneer, untagged library code always goes direct. Two entry points,
one allocator, no overlap.

## 3. What the direct sites *did* report, and why it is suppressed

Before suppression, direct rows printed things like:

```
0x58  0x02041be0  arm9  arm  direct  <0x020a0f3c>   <0x020a0c34>
0x14  0x02011c40  arm9  arm  direct  <0x020a1a84>   <0x020a0c34>
```

Those are **stale registers**, not data. Library callers set only `r0`; whatever `r1`/`r2` happen to hold
is left over from earlier code — and the allocator clobbers them itself in its first two instructions
(iteration 133). The recurring `<0x020a0c34>` in the *file* column is the instance counter found in
iteration 131.

The census already declines to invent a name — it prints `<address>` when the value is not in the strings
table — but printing a bare address in a column headed "file" still reads like a finding. Direct-entry rows
are now reported as `UNTAGGED`, with the measurement above as the justification, and a selftest assertion
that fires if a direct site ever *does* resolve to a real filename (which would mean the suppression is
hiding something real).

## 4. The bug this surfaced: no size bound on the ARM pass

With the direct entry included, the largest "allocation" in the ROM became:

```
0x2096568  0x020462ec  arm9  arm  direct  UNTAGGED  UNTAGGED
```

`0x2096568` is 34 MB — on a console with 4 MB of RAM. It is a stale pc-relative literal read as a size.

The Thumb pass has guarded against exactly this since iteration 101, rejecting sizes above `0x100000`. **The
ARM pass never had that check.** It went unnoticed because no veneer-entry ARM site happened to trip it;
the direct entry simply reached code where it does. The bound is now applied to both passes, and the
selftest's implausible-size assertion was widened from `thumb` to all rows.

The largest genuine allocation in the ROM is `0x4000C`, so `0x100000` leaves plenty of headroom.

## 5. Regression check

The concern with widening a scan is silently changing what it already reported. Comparing every row the
previous version printed against the new version's veneer rows:

```
659 old rows, 659 new veneer rows, diff empty
```

Byte-identical. The change is purely additive, apart from the bogus 34 MB row the new bound removes — and
that row only existed because of the new entry.

## Predictions status

| Claim | Verdict |
|---|---|
| Scanning `0x0201A228` finds sites the census missed | **CONFIRMED_STATIC** — 403 new sites, 732 → 1135 |
| Some tagged calls reach `0x0201A228` directly | **REFUTED** *(iteration 133's open question)* — 0 of 403 resolve to a real filename |
| Tagged code always uses the veneer | **CONFIRMED_STATIC** — 572 of 732 veneer sites resolve, 0 of 403 direct ones do |
| The `<0x...>` values on direct rows are file/function data | **REFUTED** — stale registers; `<0x020a0c34>` is iteration 131's instance counter |
| The ARM pass bounded its sizes for plausibility | **REFUTED** — only the Thumb pass did; `0x020462EC` reported `0x2096568` |
| Widening the scan changed existing output | **REFUTED** — 659 old rows vs 659 new veneer rows, diff empty |
| The `0x100000` bound could drop a real allocation | **not claimed** — the largest genuine size is `0x4000C`, but the bound is a heuristic |
| The 403 direct sites' sizes are trustworthy | **PLAUSIBLE** — `r0` is the only argument the direct entry takes, and the anchor `0x02010DA4` resolves to `0x78` as hand-read in iteration 133 |

## Next angles, ranked

1. **Dump the base vtables** set by `0x02021960` and `0x020240A4` (carried) — with `+0x00`/`+0x04`/`+0x18`
   named in iteration 133, a four-level diff would name every overridden slot.
2. **Sweep the 403 new direct sites for large allocations** in the library region. They are untagged, but a
   size and a call site are still enough to identify a manager.
3. **Read `0x0201B244`** (36 bytes) to confirm `operator delete`, retiring a PLAUSIBLE.
4. **Trace the remaining `+0x24` sites** (carried), now with `0x02021960` as a known-relevant base class.
