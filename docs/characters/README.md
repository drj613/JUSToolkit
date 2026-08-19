# Character documentation

**69 of the 71 per-character map files were deleted on 2026-08-19.** They were placeholders:
a long template — median 309 lines — filled mostly with `TBD`, "NEEDS VERIFICATION", and
plausible guesses. 489 literal `TBD`s across the set. The length read as substance, which is
exactly the failure mode this project has been bitten by before.

## What's here

| file | what it is |
|---|---|
| `character-index.md` | identity + file-linkage fields for **all 71** characters, extracted before deletion. The only part of those files that was real. |
| `character-index.json` | the same table, machine-readable |
| `Goku-Character-Map.md` | verified in-game data. **Has a refutation banner — read it.** |
| `Ichigo-Character-Map.md` | verified move lists (base and Bankai), buff and weight mechanics |
| `TEMPLATE.md` | the template, for if a character ever gets mapped properly |
| `BaseNaruto/sprites/` | 21 PNGs labelled by animation state — real reference material for hitstun/animation work |

## Rules

- **Identity fields are usable; numbers are not.** `character-index.md` tells you which
  `chr_b` entry, collision file and `jpower` block belong to a character. It contains no
  measurements and should never be cited as evidence for one.
- **Nothing new goes in a character map without a bead.** If you measure a move, the claim
  lives in beads (`br create … --label coord`) and the document cites the id. A bare
  `CONFIRMED` in a character file has already proved worthless once — Allen-Character-Map.md (now
  deleted) had a header reading "Move List (CONFIRMED)" directly above a `TBD`.
- **Don't regenerate the 69.** If per-character data is wanted at scale, generate it from the
  ROM into a table, the way `character-index.json` already is. Hand-writing 70 templates is
  what created this.

Deleted files are recoverable from git history:

```bash
git log --diff-filter=D --name-only -- 'docs/characters/*-Character-Map.md' | head
git show <commit>^:docs/characters/Zoro-Character-Map.md
```
