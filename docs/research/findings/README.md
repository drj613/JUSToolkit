# `findings/` is an append-only journal, not a reference

193 files, one per static-loop iteration, each titled "Loop-Atlas iteration N".

**An entry was true when it was written and was never revised afterwards.** Some are
superseded by later iterations, and a few are outright refuted. Nothing in here has been
re-audited.

## Rules

- **Never cite a `findings/` file as the current answer.** Current answers live in beads
  (`br show <id>`); current explanations live in `docs/research/*.md`.
- **Do not rewrite history here.** If an entry turns out wrong, add a banner at the top
  pointing to the bead that overturned it, and leave the body alone. The wrong reasoning is
  the useful part — it records what looked convincing and why.
- **When you write a new entry**, cite the bead your finding lives in. 14 of 193 currently
  do, which is why this directory is hard to trust.

## Known-bad entries

| file | problem |
|---|---|
| `defence-candidates-ruled-out.md` | attributes the reduction to ability `0x09`; refuted twice over |

If you find another, add a banner and a row here rather than deleting the file.
