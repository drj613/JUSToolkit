---
name: prediction-must-be-single-mechanism
description: A pre-registered prediction only tests something if the predicted value is reachable by exactly one mechanism; enumerate the lattice before the run
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9114733f-1275-45a1-a6f1-898e950b4c12
  modified: 2026-08-19T20:15:16.471Z
---

Writing a prediction down in advance does not make it a test. It is only a test if the
predicted value is reachable by **one** mechanism. Enumerate the full lattice of outcomes
*before* the run, and if two mechanisms land on the same number, add a reading that
separates them or change the conditions until they do not.

Concretely, in the JUS damage work: I pre-registered "a slash against this target reads
10.000" as confirmation of the ability-to-gate mask table. But nature and the class gates
land in the *same* accumulator additively, so 10.000 is also what "blunt attack plus a
1.5x nature term" produces — and 6.000 was degenerate two ways as well. I would have
claimed a confirmation off a value that supports the alternative equally well, using a
number I had pre-registered, which is exactly what pre-registration is supposed to prevent.

**Why:** degeneracy is invisible from inside a single hypothesis. You check whether your
mechanism predicts the value, not whether anything *else* also predicts it. The pre-
registration ritual feels like rigour and supplies none.

**How to apply:** before any measurement, write out every combination of the live terms and
the value each produces. Collisions are the finding. Prefer a test that is *invariant*
across an unknown over one that pins the unknown down — e.g. row 3 of both nature tables is
all 1.0, so a row byte of 3 forces the nature term to zero regardless of which column
selector or which table applies, which beats resolving the selector.

Related: [[negative-control-needs-the-stimulus-first]],
[[verification-must-not-agree-with-itself]], [[convergent-verification]],
[[record-points-one-representation-away]].
