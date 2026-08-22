---
name: self-written-prompts-are-unreviewed
description: A prompt you write for your own next wake is unreviewed by construction — keep addressing detail in the shared ledger, and fix the prompt rather than out-ranking it
metadata:
  type: feedback
---

Instructions I write for my own next wake are read by nobody else and re-derived by nobody,
so a wrong address or register in one becomes measurements without ever being checked. The
shared ledger (beads) is visible to the partner loop, so a wrong register there gets caught
before it produces numbers.

Worked example, 2026-08-19: my own scheduled wake prompt told me to derive a JUS scratch
pointer as `[[r5+0x1A8]+0x10]` with the battleObj in r0. At the three bracket sites that was
wrong — those addresses ARE the `mov r0, r4` instructions, so r0 still held the previous
call's return value and the register is r4. The partner loop caught it. I first recorded the
correction only in the bead, reasoning the bead out-ranks the prompt; they pointed out that
leaves the wrong instruction in place and makes the fix depend on ingest ORDER. Correct move
is to edit both (ScheduleWakeup with a corrected prompt replaces the pending one).

**Why:** it's the stale-authoritative-instruction failure — text that reads as canon because
I wrote it. Worse than a bad number, because a bad derivation produces clean-looking,
mutually consistent, entirely void readings with no signal that anything is wrong. See
[[verification-must-not-agree-with-itself]] and
[[negative-control-needs-the-stimulus-first]] — same family.

**How to apply:** never rely on precedence between two sources that disagree; fix the wrong
one. Put addressing detail in beads, not in self-prompts. And when a derivation could be
wrong, carry a value check that fails loudly (here: the derived pointer must equal a value
confirmed at two independent sites, else every read is reported VOID).
