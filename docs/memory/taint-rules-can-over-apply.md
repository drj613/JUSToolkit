---
name: taint-rules-can-over-apply
description: An instrument/taint rule applied one step too far silently retires real findings — the mirror of a check that agrees with itself
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 707184ff-a9e3-4276-9508-edf2109deda4
  modified: 2026-08-19T00:16:42.062Z
---

When a measurement artifact is discovered and turned into a rule ("never interpret X"), the
rule itself must be scoped, or it quietly kills valid findings. Applying it one step too far
looks like diligence and produces no error.

Worked example, 2026-08-18: runtime found that reading the JUS battle root the moment
`[0x02172960]` goes non-zero returns an all-zero object, so "early reads are meaningless"
became a rule. That rule would also have dissolved the `root+0x4C..+0x6C` all-zero finding —
except the same dumps showed `+0x10C`/`+0x110` holding main-RAM pointers, `+0x158` = 2, and
`+0x000` a live handler. A freshly memset object cannot show populated siblings, so those
zeros were real data, not an artifact.

**Why:** this is the mirror image of [[verification-must-not-agree-with-itself]]. That failure
accepts something false; this one discards something true. Both are invisible because neither
produces a wrong number — one produces false confidence, the other a silent deletion.

**How to apply:** when a new taint rule would invalidate an existing finding, look for an
in-sample discriminator before retracting — a sibling field, a neighbouring read, anything from
the *same* capture that the artifact could not have produced. State explicitly which findings
the rule does and does not reach. Prefer a positive control on a known-good case run through
the identical protocol: twice this session that control was what separated artifact from
finding (see [[convergent-verification]]).
