# Findings: auditing three scanners for the condition-suffix flaw

Loop-Atlas iteration 82. Static.

Iteration 81 found that a regex over ARM mnemonics silently drops every predicated
instruction, hiding 40% of one sweep's hits. This wake audited the three remaining
text-matching tools.

**No output changed.** `alloc_census.py` had the flaw in three patterns but zero
conditional calls exist ROM-wide. `find_jump_tables.py` was never vulnerable.
`prior_art.py` matches no mnemonics at all.

A different bug turned up: `find_jump_tables.py` **silently dropped** every dispatch
with no guarding `cmp`. Two real ones were missing from every run.

---

## 1. `alloc_census.py` — flaw present, output unchanged

Three patterns listed bare opcodes: `mov r0-r2,#imm`, `ldr r0-r2,[pc,…]`, and
`bl #addr`. All three now accept an optional condition suffix.

A conditional writer is tagged **CONDITIONAL**, not resolved. `movgt r0,#0x20` /
`movle r0,#0x40` is a real idiom; picking one value would invent a size the call may
never use. That is distinct from COMPUTED.

Result, measured:

| | before | after |
|---|---|---|
| allocator calls | 494 | **494** |
| unconditional immediate size | 431 | **431** |
| resolved names | 469 | **469** |
| computed or unresolved | 63 | **63** |
| conditional size | — | **0** |

**Zero conditional `bl` to `0x0201A21C` exist ROM-wide**, and no conditional `mov` or
`ldr` falls inside any allocator call's back-scan window. Iteration 77's census figures
stand, and with them the `Battle_CharaCreate` naming from iteration 73.

The fix is still worth keeping: the flaw was real, and the next conditional-size site
would have been misfiled.

## 2. `find_jump_tables.py` — never vulnerable

Its patterns are word masks. `0x0FFFFFF0` leaves bits 31–28 unmasked, so the condition
nibble is ignored by construction. All **127** sites it reports are conditional
(`cond=ls`, the bounds-checked idiom) and it finds them.

A text census counts 129 `addCC pc,pc,rN,lsl #2`, 5 `addCC pc,pc,rN` unshifted, and 5
assorted `ldrCC pc,[pc…]`. The ten non-`lsl #2` forms are **data misdecoded as
instructions**, not missed dispatches:

```
0x021695B0  andseq sp, r6, #252, #26     <- ov1 pointer table
0x021695B4  addeq pc, pc, r0             <- "dispatch"
0x021695B8  andseq sb, r6, #0x16400
```

The tool's tighter mask rejects them correctly. Same for `ldreq pc,[pc],#0xaf` at
`0x02090FA8`, inside arm9's table region between two equally nonsensical words.

## 3. The real bug: dispatches with no guarding `cmp`

The remaining gap (127 of 129) is a genuine defect, unrelated to condition codes:

```python
if n is None or not (args.min_cases <= n + 1 <= args.max_cases):
    continue                    # dropped, with no filter requested and no mention
```

A dispatch whose index is computed arithmetically has no `cmp` to recover a case count
from, so `cases` is `None` — and it vanished from the report even with no filter
active. Both victims are real code:

```
0x0200D194  add r2, r2, r2, lsl #1     ; r2 *= 3
0x0200D198  add pc, pc, r2, lsl #2     ; unconditional, unbounded
```

Same shape at `0x0200D38C`. These are the **only two unconditional** `add pc,pc`
dispatches in the ROM — a clean cross-check against the census count of 2.

Now reported as `NO GUARDING CMP -> case count unknown (index computed)`, and the
summary line always states how many there were.

## Predictions status

| Claim | Verdict |
|---|---|
| `alloc_census.py` had the condition-suffix flaw | **CONFIRMED_STATIC** — in `MOV_IMM`, `LDR_PC` and `BL_ALLOC` |
| Fixing it changes the census figures | **REFUTED** — 494 / 431 / 469 / 63 all identical; 0 conditional sizes |
| Conditional calls to the allocator exist | **REFUTED** — 0 ROM-wide |
| `find_jump_tables.py` has the condition-suffix flaw | **REFUTED** — word masks ignore bits 31–28 by construction |
| The 10 non-`lsl #2` `pc` writes are missed dispatches | **REFUTED** — data misdecoded as instructions, correctly rejected |
| `find_jump_tables.py` silently dropped dispatches with no guarding `cmp` | **CONFIRMED_STATIC** — `if n is None: continue`, no filter required, no mention |
| `0x0200D198` and `0x0200D38C` are real dispatches | **CONFIRMED_STATIC** — `add r2,r2,r2,lsl#1` then `add pc,pc,r2,lsl#2`, unconditional |
| They are the only two unconditional `add pc,pc` sites in the ROM | **CONFIRMED_STATIC** — text census: 2 unconditional, 132 conditional |
| `prior_art.py` is affected | **REFUTED** — it matches no mnemonics; it greps docs and shells out to `query.py` |

## Next angles, ranked

1. **Resolve `record+0x68`** (carried) — the object whose `+0x20` list holds this
   record's bucket nodes. Tooling audited; back to the engine.
2. **Re-run the record map** (carried) with anchors from the eight per-frame collision
   stages, both decoders now corrected.
3. **Re-audit the map's `char+0xNN` offsets** (carried) across the three objects.
4. **Name the arm9 `+0x56c` struct** (carried) — candidate `memset(r7+0x8, 0x5e0)` at
   `0x02076C2C`.
