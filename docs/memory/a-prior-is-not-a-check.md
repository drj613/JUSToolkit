---
name: a-prior-is-not-a-check
description: Evidence that a region is unreliable is not evidence that it is irrelevant — a burn is a reason to look harder there, not a licence to skip it
metadata:
  type: feedback
---

I retired 30 scanner candidates with "ov12 is the UI overlay whose +0x172 field burned me at P171, so
+0xE8 there is almost certainly an unrelated widget field. Not chasing them." Examined ten iterations
later, **21 of the 30 were genuine Thumb stores to the target field.** The overlay that had already
fooled me once became my stated reason to skip it.

**Why:** a plausible-sounding prior feels like knowledge, and a past burn supplies the confidence. But
"this region produced a false positive before" says nothing about whether *these* hits are real — it
only says the region is hard to read, which is an argument for more care, not less. The dismissal also
hid behind a hedge: I wrote the hits "split mainly between ov12 and ov10", and "mainly" concealed six
more in four other overlays, two of them stores. Count, don't characterise.

**How to apply:** never retire a candidate on what a region is *for*. Retire it on a property of the
candidate — a named containing function, or a structural exclusion like an overlay-aliasing map (ov0–ov9
all load at the same address, so two of them cannot both be resident). When the usual check is
unavailable — `functions.json` did not cover these addresses at all — decode the bytes yourself in a
different representation rather than falling back on the prior. Related:
[[clean-evidence-skips-the-check]], [[a-correction-is-a-claim]], [[convergent-verification]].
