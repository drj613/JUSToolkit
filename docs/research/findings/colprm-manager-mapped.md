# Findings: the ColPrm manager mapped, and a false positive in my own guard

Loop-Atlas iteration 53. Static. Tool: `scripts/decomp/struct_fields.py` (fixed this wake).

Mapped the BattleColPrm manager (the collision subsystem's runtime home, named last wake) from **16
type-verified anchors** in arm9 `BattleColPrm.cpp`. 40 fields, all below `+0x158`.

The tool dropped a known field, which exposed a **false positive in guard 5** (the vtable check) — it was
silently discarding real fields at 7 of the 16 anchors.

---

## 1. Finding the anchors

Every anchor is derived mechanically. For each of the 7 literal pools holding `0x0214BE10`, find the
`ldr Rd,[pc]` that loads it, then the `ldr Ry,[Rd,#0]` that dereferences it — `Ry` now provably holds the
manager. That yields **16 anchors**, including one *write* site (`0x0207C844 str r4,[r1,#0]`), where `r4`
is the manager being installed.

Guard 3 (know the base register's type) is satisfied by construction, not judgement — a first for a struct
this large.

## 2. The map

```
BattleColPrm manager   (*(0x0214BE10))
  +0x00 .. +0x24   ten consecutive words, written in order at 0x0207C4F0..0x0207C514
                     NOT uniform init data: +0x20 is a LIST HEAD (linked at 0x0207CBB8) -- iteration 67
                     +0x18 is the only one later read as well as written
  +0x70            list head          (ldr, 0x0207D89C)
  +0xD0            list head          (ldr, 0x0207D3A8)
  +0xD8, +0xDC     written once each
  +0xE0            x6  ldr+str        the hot fields — read and written repeatedly
  +0xE4            x5  ldr+str
  +0xE8            x5  ldr+str
  +0xEC            x3  ldr+str
  +0xF0            x3  ldr+str
  +0xF4            written once
  +0xFC .. +0x148  a second init block, stores only
  +0x14C           byte field, ldrb+strb
  +0x158           contact array  (iteration 52): rows 0xC0, elements 0x30, 4 per row
```

40 distinct offsets, 59 accesses.

`+0xE0`/`+0xE4`/`+0xE8` stand out: three adjacent words read *and* written six, five, and five times, while
almost everything else is write-once init. Whatever the manager does per-frame, it runs through those three.

### Mutual validation with iteration 52

**Every field found is below `+0x158`.** Iteration 52 concluded the contact array starts there, from a
completely different argument (query 71's `+0x158` and `+0x170` reads land inside one `0x30` element). Two
independent derivations agree; no header field overlaps the array.

## 3. The bug: guard 5 was discarding real fields

The first map was missing `+0x70` — a field iteration 52 already established from
`0x0207D89C ldr r5,[r2,#0x70]`. That's the only reason I noticed.

**Cause.** Guard 5 suppresses an access when the base register was loaded by `ldr Rd,[Rm,#0]`, because
that's how a vtable pointer is fetched. But `ldr Rd,[Rm,#0]` is byte-identical to dereferencing a
pointer-to-pointer — exactly how every singleton global in this engine is read:

```
ldr r0, [pc]      ; r0 = &g_colprm
ldr r2, [r0, #0]  ; r2 = the manager      <- indistinguishable from a vtable load
ldr r5, [r2, #0x70]                        <- real field, wrongly suppressed
```

Every anchor here is "the instruction after a dereference", so the guard suppressed the first access at
**7 of 16 anchors**, losing `+0x70`, `+0x18`, `+0xEC`, `+0xF0` and `+0x14C` reads.

**Fix.** Discriminate on what happens to the *loaded value*. A vtable slot is called; a struct field is
not. Guard 5 now requires both the preceding `[Rm,#0]` load **and** a `blx`/`bx` on the result, within
six instructions.

**Validated three ways.** Selftest still passes (same 12 NoteTrack fields). The four known vtable sites
from iteration 48 (`0x0215F1C4`, `0x0215F318`, `0x02168FEC`, `0x0216FF6C`) are still suppressed. The
ColPrm map went from 52 to 59 accesses, recovering exactly the missing fields.

### The lesson is about how the bug was caught

The selftest passed both before and after the fix — its NoteTrack anchors aren't dereference-based. A
green selftest meant the tool was correct *on the cases the selftest covers*, nothing more. What actually
caught this was **cross-checking a new map against a field known from earlier, unrelated work**.

Rule: when mapping a struct, list its known fields first. Treat any known field the tool fails to
reproduce as a tool bug until proven otherwise. This is now the third check that has caught a wrong
result, after the struct-size bound and the constructor-store invariant.

## Predictions status

| Claim | Verdict |
|---|---|
| 16 anchors can be derived mechanically from the global's literal pools | **CONFIRMED** — 7 pools, 16 dereference sites |
| The ColPrm manager has 40 mapped fields, all below `+0x158` | **CONFIRMED_STATIC** |
| No header field overlaps the contact array | **CONFIRMED_STATIC** — highest header field is `+0x14C` |
| `+0xE0`/`+0xE4`/`+0xE8` are the per-frame mutable state | **PLAUSIBLE** — 6/5/5 read-write accesses vs write-once elsewhere |
| Guard 5 as written only suppressed vtable loads | **REFUTED** — it also suppressed singleton-global dereferences, at 7 of 16 anchors |
| The `blx`-discriminator fix preserves vtable suppression | **CONFIRMED** — all 4 known vtable sites still excluded, selftest unchanged |
| A passing selftest means the tool is correct | **REFUTED** — it passed before and after a real bug |

## Next angles, ranked

1. **Read the `+0xE0`/`+0xE4`/`+0xE8` accessors.** Five or six read-write sites each in a small module —
   per-frame collision state and the likeliest place the contact matrix gets populated.
2. **Find what writes the contact array at `+0x158`.** The other half of iteration 52: query 71 reads it,
   something fills it, and that writer is the actual collision test.
3. **Add a "known fields" argument to `struct_fields.py`** so the cross-check from §3 is automatic.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
