---
name: stale-claim-above-its-own-correction
description: "The JUS record's worst error shape is a stale claim sitting ABOVE its own correction in the same document — the fix makes the doc look maintained"
metadata:
  type: project
---

Three instances in one week (2026-08-19), all in JUS research docs:

- `Battle-Engine-Map.md` asserts the poison/burn floor is "1 HP" at lines 1272, 1291 and 1409,
  and corrects it at line 1836 ("displayed HP is raw / 64… the constant to look for is `0x40`").
- `docs/HANDOFF-2026-08-19-runtime-shutdown.md:62` gives the gate word as `scratch+0x40` /
  `0x0220FDC4+0x40` **and** says "re-derive it in-session from the anchor before trusting the
  absolute" — the caution sits beside the wrong value.
- `Overlay-Residency-By-Mode.md` says the `0x021AC1C0` window is unresolved and "don't rely on
  either reading", then resolves it 30 lines below in the deck-editor section.

**Why:** this is worse than an uncorrected error. A reader hits the stale claim first, and the
nearby correction signals the document is maintained, so the claim reads as current *and*
vetted. Both halves are individually well-formed, so no linter can see it — I checked, and
proposed rule after proposed rule fails on all three (see
[[record-points-one-representation-away]] for why the both-forms version is worse than
useless).

**How to apply:** when correcting a doc, search the whole file for the old claim before adding
the new one — the fix goes *at* every instance, not once at the bottom. When reading, a
correction late in a long doc means earlier passages are suspect, not that the doc is healthy.
And a caution printed next to a value ("verify this before trusting it") is not a substitute
for the value being right; it reads as diligence and changes nothing.

Related: [[record-points-one-representation-away]], [[clean-evidence-skips-the-check]],
[[a-correction-is-a-claim]].
