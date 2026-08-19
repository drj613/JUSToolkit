# Character maps — read this before trusting any file in here

**70 files. Two are complete.** The rest are a filled-in template, and the template is
long enough to look like data.

| Map status | files |
|---|---|
| COMPLETE | 2 |
| PARTIAL | 57 |
| STUB | 11 |

Median length is 309 lines and there are 489 literal `TBD`s across the directory. The
owner's summary (2026-08-19) is that **most of these are placeholders**: the identity
fields (name, series, `chr_b` index, collision file, `charId`, `classId`, `jpower` block)
are generally real, and almost everything below them — move damages, koma data, frame
data — is unverified or absent.

Absence of the word `TBD` does **not** mean a file is finished. 45 files contain no `TBD`
at all, while only 2 claim COMPLETE; the others simply didn't use the marker.

## What this means in practice

- **Do not cite a character map as evidence.** Check the `Map status` line, then check
  whether the specific field you want is verified. If it isn't backed by a claim bead or
  a measurement doc, it's a guess.
- **A `(CONFIRMED)` section header in these files is decorative.** At least one file
  (`Allen-Character-Map.md`) has a header reading "Move List (CONFIRMED)" sitting directly
  above a `TBD` value.
- **Don't hand-edit these to fix the sprawl.** The identity fields are data, not prose —
  they belong in a generated table (see `docs/research/battle-chars-passives.json` for the
  shape that already exists). Regenerating them is the fix; editing 70 templates is not.

## Where the real record is

- Verified claims live in beads (`br list --label coord`), with a lifecycle label.
- Measurements and derivations live in `docs/research/`.
- `docs/research/findings/` is an append-only journal, not a reference.

See `docs/research/README.md` for how the layers fit together.
