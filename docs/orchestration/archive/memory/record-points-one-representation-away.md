---
name: record-points-one-representation-away
description: "This project's recurring failure is a confidently-written record that is one representation off — wrong offset, wrong byte, wrong units"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9114733f-1275-45a1-a6f1-898e950b4c12
  modified: 2026-08-20T02:10:00.000Z
---

The JUS record's characteristic error is not being vague — it is being confident and off by
one *representation*. Three instances inside one week (2026-08-19):

- the ±25% damage gate word recorded at `[r8+0x40]` when the gates read `[r8+0x44]`
- `scripts/emu/README.md`'s HP read documented as "2 bytes at addr−1" when the 16-bit
  1/64 value is at addr−2; the wrong read returns a plausible small number, not an error
- the HP floor recorded as "1 HP" when that was *display* units and the raw floor is 0
- element pointers spanning three heap blocks read as **one array from a common base**, yielding
  "entry 44" for what is entry 4 of `na_b_01.bin` — the wrong representation was the *container*

**Why:** every one of these still lands on something real — a valid instruction, a readable
byte, a sane-looking number — so nothing complains and no check fires. Same family as the
`JUS_WATCH` pc being instruction+8. A wrong address that faulted would be harmless; a wrong
address that reads cleanly is what costs weeks.

All four are the same error in different clothes: a value **stated in one representation and
read in another** — offset, address, units, or *which structure the base belongs to*. The fourth
adds a container flavour worth naming on its own: contiguous addresses do not imply one array. The
indices came out plausible, small, and monotonic, because a stride divides a span whether or not
the span is a single object. The predecessor's handoff already carried "the
unit is part of the search term" from the 128-versus-512 hunt, so with three more instances in
a week this is not a gotcha, it is the dominant failure mode in this codebase.

**How to apply:** *not* by restating the value in both forms — that was my first answer and
it is refuted. The runtime handoff already wrote "`scratch+0x40`… for the opponent that is
`0x0220FDC4+0x40 = 0x0220FE04`", relative and absolute, both present, both wrong, plus a
caution to re-derive it. Restating an offset as base+offset is **one claim twice**: both forms
come off the same wrong premise, and a doc that satisfies a both-forms check reads as *more*
verified while being exactly as wrong. Same family as the pixel oracle whose reference came
from the system under test.

What works is a second derivation that starts from a **different artifact**: raw ROM/RAM bytes
versus a disassembly listing, a live register versus a static enumeration of what can write
it. Two reads of the same listing are one representation twice, however independent the
readers. The concrete review question is "name the two artifacts" — if both derivations trace
back to one, there is no cross-check. This is semantic and no text linter can do it; the
both-forms linter I proposed would have caught **zero** of the three instances above.

The one textually checkable defect in the set is a **missing scale qualifier** on a magnitude —
"1 HP" with no raw-or-displayed (`docs/research/Battle-Engine-Map.md`, and it was display units
while the raw floor is 0). That is a different rule from a missing *unit*, since the unit-noun
is present. It catches one of the three, diff-scoped and failing rather than warning; a warning
would join the ~293 nobody reads.

Both catches this week came from one loop re-deriving something the other had already written
down — so duplicated derivation between loops is not waste, it is the only mechanism that has
actually caught these. Stop apologising for it.

Related: [[convergent-verification]], [[prediction-must-be-single-mechanism]],
[[a-correction-is-a-claim]].
