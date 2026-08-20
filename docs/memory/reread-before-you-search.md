---
name: reread-before-you-search
description: When a question touches a function already in the record, re-read that whole function before searching for a new one — and never filter a listing you will reason from
metadata:
  type: feedback
---

When a question touches a function already quoted in the record, re-read **that whole
function** before going looking for a new one.

**Why:** we re-read *documents* at wake time and it pays constantly. We don't re-read
*disassembly* we already pulled, because extracting a listing once feels like having read
it. It isn't. Extraction is bounded by the question you had at the time; the listing
routinely answers questions you hadn't thought to ask. Three times in one week the answer
sat inside something one seat had already quoted — most sharply, the `kshape.bin` record
base was open for a full wake while `ldr r0, [r0, #0x14]` (which yields the base by
subtraction from any known bitmap) sat in `0x02076D30`, a function quoted verbatim in the
very finding doc that posed the question.

**The corollary, which is where it actually goes wrong:** don't filter or truncate a
listing you're about to reason from. Two instances within one hour —
`grep -iE "0x1f|lsl|cmp|tst|and|bic|add"` on a 34-line function (no `ldr` in the pattern,
so it would have hidden the answer; I only escaped because the command errored on a bad
flag), and a peer's `git remote -v | head -2` yielding "the only remote is fork", which was
false. Both narrow output using a guess about what the answer looks like, and neither warns
when the answer isn't in the set.

**How to apply:** if the output is short enough to read whole, read it whole — a 34-line
function has no business going through a filter. This is [[circular-search-constraints]]
one level down: not a search space over addresses, but the pipe used to read the search's
output. Same move either way — deciding in advance which shapes the answer may take.

Related: [[circular-search-constraints]], [[falsifiable-but-dead-on-this-claim]],
[[record-check-spans-branches]], [[filing-a-lead-discharges-owing-it]]
