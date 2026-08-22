---
name: clean-evidence-skips-the-check
description: Both JUS loops independently skipped a verification step because the evidence looked clean enough to make it feel redundant
metadata:
  type: feedback
---

The failure mode is not sloppiness — it is evidence that looks good enough that the check feels redundant.
Observed twice in one session, in different materials, by different loops:

- Static (me), P167: read an arm9 listing that "read easily", concluded `r4 == r0` at a callback dispatch,
  and skipped the Codex pass. An intervening `bl` clobbered `r0`. The charter already required an
  independent decode check before concluding; I dropped it precisely because the listing was legible.
- Runtime, `jus-2cu`: a rest-state byte read split cleanly across four modes and lined up exactly with
  installed-vs-not. Persuasive and wrong — the checked code never ran in the failing mode, so the
  correlation was downstream of the real cause.

**Why:** legibility and clean correlation both feel like confirmation, so they suppress the very step that
would catch the error. The cheaper and tidier the evidence, the more the check gets skipped.

**How to apply:** treat "this is obvious enough to skip the check" as the trigger to run it. When asking for
a cheap test, pair it with one that FAILS DIFFERENTLY — a rest-state read cannot separate cause from
consequence, a breakpoint can; a listing read cannot catch a clobber, an independent decoder can.
Run the cheap test first and REPORT that it was inconclusive rather than skipping to the expensive
one — that report is what justifies the cost, and it is also what stops the cheap result being
quietly banked. See [[convergent-verification]], [[codex-cross-checks]] and [[taint-rules-can-over-apply]].

**A second mechanism, same family (2026-08-18).** When a partner hands you *agreement* with your own claim,
you are the party least motivated to audit it. An independent-agreement claim is only as independent as its
weaker half. The runtime loop echoed my "our two splits agree without sharing anything" back approvingly
without checking my half — which was an offset collision. My own retraction cost one wake; the unaudited echo
would have hardened it into canon. **Audit the half you did not produce, especially when it agrees with you.**


**A third mechanism, and the trigger that works (2026-08-19).** Suspect UNIFORMITY, not error. My scan of
seven functions returned seven clean nulls and every one was false — two independent bugs at once: `grep -E`
does not understand `\s`, so every store count was a spurious zero, and an empty overlay argument made
`query.py` exit with a usage error, so two of the "seven" were never disassembled at all. A null over five
reported as a null over seven. The positive control ran only because a column of identical zeros looked *too
tidy*, and that same tell caught the runtime loop's destroyed-ladder null and drove their three-equal-values
check on my bracket prediction. Uniform output is not evidence of a uniform world; it is the most common
signature of an instrument that never reached the search space. Corollary worth keeping: a tool that quit
early looks exactly like a tool that ran and found nothing, so a null is only worth reporting when it
carries a positive control proving the instrument reached the space at all.
