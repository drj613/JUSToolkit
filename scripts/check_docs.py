#!/usr/bin/env python3
"""Check that docs and the beads ledger agree.

Beads is the system of record; docs explain. This catches the four ways that
breaks down:

  1. a doc cites a bead that does not exist
  2. a doc cites a bead that is retracted or tainted, without saying so
  3. a doc asserts CONFIRMED/VERIFIED in prose with no bead id anywhere near it
  4. a doc claims to supersede or be superseded by a file that isn't there

Exit 1 on errors, 0 otherwise. Warnings never fail the run -- legacy docs are
full of them and blocking on those would just get the check disabled.

Usage:
    python3 scripts/check_docs.py                # whole docs/ tree
    python3 scripts/check_docs.py --strict       # warnings fail too
    python3 scripts/check_docs.py docs/research  # narrow the scope
"""
import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, ".beads", "issues.jsonl")
BASELINE = os.path.join(REPO, "scripts", "check_docs_baseline.txt")
NOT_BEADS = os.path.join(REPO, "scripts", "check_docs_not_beads.txt")

# A real bead id is the prefix, an optional slug, a 3-4 char hash, and an
# optional dotted child suffix:
#   JUS-0co, jus-fun, jus-consolidate-loop-branches-m5i,
#   jus-wayfinder-map-digi.15, JUS-9lp.2.2
# The dotted suffix must be part of the match, or a child id truncates to a
# nonexistent parent slug (jus-wayfinder-map-digi.7 -> jus-wayfinder-map).
# This deliberately does NOT match most gdb/script command names that share
# the prefix (jus-watch-hp, jus-status) -- they are not citations. Command
# names it can't distinguish go in scripts/check_docs_not_beads.txt.
# The trailing lookahead stops a partial match: without it, jus-boot-navigation
# would yield "jus-boot" and jus-find-timers "jus-find".
BEAD_RE = re.compile(
    r"\b(jus-(?:[a-z0-9]+-)*[a-z0-9]{3,4}(?:\.\d+)*)(?![\w-])(?!\.\w)", re.I)
# Status words that mean "trust this" when written in prose.
STATUS_RE = re.compile(
    r"(?<![`\w-])(CONFIRMED|VERIFIED|CROSS[- ]CONFIRMED|PROVEN)(?![\w-])")
# Lines that are talking *about* the convention rather than asserting a status.
META_HINT = re.compile(
    r"(no bare|decorative|must not|do not|don't|never|refut|retract|supersed"
    r"|stale|wrong|is not a|treat any|linter|check_docs|example)", re.I)

DEAD_STATES = {"state:retracted", "state:tainted"}

# Placeholders that appear in example commands, not real citations.
PLACEHOLDER_RE = re.compile(
    r"^jus-(x+|n+|id|xxx+|upstream|downstream|new|old|foo|bar|abc|"
    r"<[^>]*>)$", re.I)

# Directories that are history by definition -- cite-a-bead is a warning there,
# not an error, because the entries are immutable.
JOURNAL_DIRS = ("docs/research/findings", "docs/research/archive")


def load_beads():
    """Return {id_lower: {"id": .., "labels": set(), "title": ..}}."""
    if not os.path.exists(LEDGER):
        sys.exit("no ledger at %s -- run `br sync --flush-only` first" % LEDGER)
    beads = {}
    with open(LEDGER) as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                print("warn: ledger line %d is not JSON" % lineno)
                continue
            bid = rec.get("id")
            if not bid:
                continue
            labels = rec.get("labels") or []
            if isinstance(labels, str):
                labels = [labels]
            beads[bid.lower()] = {
                "id": bid,
                "labels": {str(x).lower() for x in labels},
                "title": rec.get("title", ""),
            }
    return beads


def load_lines(path):
    """Read a config file, dropping comments and blanks."""
    if not os.path.exists(path):
        return set()
    out = set()
    with open(path) as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if line:
                out.add(line)
    return out


def markdown_files(roots):
    for root in roots:
        if os.path.isfile(root):
            yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
            for name in sorted(filenames):
                if name.endswith(".md"):
                    yield os.path.join(dirpath, name)


def rel(path):
    return os.path.relpath(path, REPO)


def check_file(path, beads, errors, warnings, not_beads):
    relpath = rel(path)
    is_journal = relpath.startswith(JOURNAL_DIRS)
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")

    # A banner at the top of the file can acknowledge a dead bead once, instead
    # of repeating the caveat beside every citation. Only counts if the header
    # names the bead AND says something cautionary about it.
    header = "\n".join(lines[:40])
    acknowledged = set()
    if META_HINT.search(header):
        for m in BEAD_RE.finditer(header):
            acknowledged.add(m.group(1).lower())

    cited = set()
    for n, line in enumerate(lines, 1):
        for m in BEAD_RE.finditer(line):
            bid = m.group(1).lower()
            if PLACEHOLDER_RE.match(bid) or bid in not_beads:
                continue
            cited.add(bid)
            bead = beads.get(bid)
            if bead is None:
                errors.append("%s:%d cites unknown bead %s" % (relpath, n, m.group(1)))
                continue
            dead = bead["labels"] & DEAD_STATES
            if dead and bid not in acknowledged:
                # A doc may cite a dead bead deliberately, but the surrounding
                # text has to say so -- otherwise a reader takes it as support.
                lo, hi = max(0, n - 3), min(len(lines), n + 2)
                context = "\n".join(lines[lo:hi])
                if not META_HINT.search(context):
                    msg = ("%s:%d cites %s which is %s, and the surrounding "
                           "text does not say so"
                           % (relpath, n, m.group(1), "/".join(sorted(dead))))
                    # Journal entries are frozen history; a bead that went bad
                    # later is expected there, so warn instead of failing.
                    (warnings if is_journal else errors).append(msg)

        sm = STATUS_RE.search(line)
        if sm and not META_HINT.search(line):
            # Look for a bead id within a few lines either side.
            lo, hi = max(0, n - 4), min(len(lines), n + 3)
            near = "\n".join(lines[lo:hi])
            if not BEAD_RE.search(near):
                msg = ("%s:%d says %s with no bead id nearby"
                       % (relpath, n, sm.group(1)))
                warnings.append(msg)

    # supersede / see-also pointers to files that don't exist
    for n, line in enumerate(lines, 1):
        for m in re.finditer(r"`([A-Za-z0-9._/-]+\.md)`", line):
            target = m.group(1)
            # A pointer may be written relative to the doc, relative to the repo,
            # or relative to docs/. Accept any of them before complaining.
            candidates = [
                os.path.join(os.path.dirname(path), target),
                os.path.join(REPO, target),
                os.path.join(REPO, "docs", target),
            ]
            if not any(os.path.exists(c) for c in candidates):
                warnings.append("%s:%d points at missing file %s"
                                % (relpath, n, target))
    return cited


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", default=None)
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as errors")
    ap.add_argument("--write-baseline", action="store_true",
                    help="record current errors as accepted debt and exit 0")
    ap.add_argument("--verbose", action="store_true",
                    help="list every warning instead of a per-file summary")
    args = ap.parse_args()

    roots = args.paths or [os.path.join(REPO, "docs")]
    roots = [r if os.path.isabs(r) else os.path.join(REPO, r) for r in roots]

    beads = load_beads()
    not_beads = {x.lower() for x in load_lines(NOT_BEADS)}
    baseline = load_lines(BASELINE)
    errors, warnings = [], []
    all_cited = set()
    count = 0
    for path in markdown_files(roots):
        count += 1
        all_cited |= check_file(path, beads, errors, warnings, not_beads)

    if args.write_baseline:
        with open(BASELINE, "w") as fh:
            fh.write("# Known documentation debt, accepted for now.\n"
                     "# check_docs.py fails on anything NOT listed here, so new\n"
                     "# violations are caught while this backlog is worked down.\n"
                     "# Regenerate with: python3 scripts/check_docs.py --write-baseline\n"
                     "# Shrinking this file is the goal. Do not grow it casually.\n\n")
            for e in sorted(errors):
                fh.write(e + "\n")
        print("wrote %d baselined error(s) to %s" % (len(errors), rel(BASELINE)))
        return 0

    new_errors = [e for e in errors if e not in baseline]
    baselined = len(errors) - len(new_errors)
    errors = new_errors

    print("checked %d markdown files against %d beads" % (count, len(beads)))
    if baselined:
        print("%d known error(s) baselined in %s" % (baselined, rel(BASELINE)))
    print("%d distinct beads cited by docs" % len(all_cited))

    if warnings:
        by_file = {}
        for w in warnings:
            by_file.setdefault(w.split(":", 1)[0], []).append(w)
        print("\n%d warning(s) across %d file(s). Worst offenders:"
              % (len(warnings), len(by_file)))
        ranked = sorted(by_file.items(), key=lambda kv: -len(kv[1]))
        for name, group in ranked[:12]:
            print("  %4d  %s" % (len(group), name))
        if len(ranked) > 12:
            tail = sum(len(g) for _, g in ranked[12:])
            print("  %4d  (across %d more files)" % (tail, len(ranked) - 12))
        print("\n  Run with --verbose to list every warning.")
        if args.verbose:
            for w in warnings:
                print("  warn: %s" % w)

    if errors:
        print("\n%d error(s):" % len(errors))
        for e in errors:
            print("  ERROR: %s" % e)

    if errors or (args.strict and warnings):
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
