---
name: verification-must-not-agree-with-itself
description: A check whose reference was captured in the state it should detect will pass forever — and the owner will call out proxy work that looks busy
metadata:
  type: feedback
---

Two related corrections from the owner on 2026-08-18, both about mistaking activity for progress.

**A verification cannot use a reference captured from the state it is meant to detect.** The boot harness confirmed "items and gimmicks are OFF" against a stored screenshot taken while gimmicks were still on, so it agreed with itself on every run for two sessions and quietly contaminated every damage measurement. The owner spotted it from play, not from the logs. The fix that works is to read a *different representation* — a RAM flag instead of a rendered label, or behaviour instead of a label (poke a value and see whether the game restores it).

**The owner will say plainly when work is proxy work.** A "full match playthrough" that cycled random inputs and hoped something connected got named for what it was: "you're kind of just making goku walk back and forth and throw a B punch randomly at nothing." The log looked busy — 100 rounds of output — and had one landed hit in it.

**Why:** Both failures produce output that reads like progress, so neither is caught by looking harder at your own results. They are caught by an independent representation or an independent observer.

**How to apply:** Before trusting a check, ask what state its reference came from. Before reporting a loop as working, state the outcome it achieved, not the number of iterations it ran. When two signals agree, ask what else would produce both — see [[codex-cross-checks]], and note that agreement between two *derived* signals (a screenshot and a RAM diff of the same buffer) is not convergent verification. Contrast with [[convergent-verification]].
