---
name: record-check-spans-branches
description: Check-the-record must search other git branches, not just the current worktree — loops and the owner work on separate branches
metadata:
  type: feedback
---

A worktree-local `grep docs/` is a check against a fraction of the record. Three loops plus the owner each work
on their own branch, so a finding can be runtime-confirmed on another branch and invisible to me.

**Why:** at P172 I derived the effect-cancel gate's bitset from disassembly and asked the owner what it was. It
was already documented and runtime-confirmed two days earlier in
`docs/research/Ability-Bitset-Is-Not-Resistance.md` — which exists **only** on `re/ability-bitset-not-resistance`.
No amount of local grepping could have found it. (Whether it describes the *same object* is still unsettled —
an offset match is not an identification — but I could not even weigh that without knowing the doc existed.)
The same rule had already saved me three times *within* my worktree, which is exactly why I trusted it too far.

**How to apply:** before drafting anything as new, add
`git log --all --diff-filter=A -- "**/<keyword>*"` and `git show <branch>:<path>`, plus
`git grep <term> $(git branch -r --format='%(refname:short)')` for terms rather than filenames. Then read the
other branch's version before writing your own. Related: [[clean-evidence-skips-the-check]].
