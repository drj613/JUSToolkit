# Findings: the six scan guards, encoded in a tool instead of a note

Loop-Atlas iteration 51. Tooling. New tool: `scripts/decomp/struct_fields.py`.

Six wakes produced wrong offset-scan results, each from a different cause. Each time the fix was
documented. **Iteration 49 documented the reassignment guard; iteration 50 scanned without it** —
reporting three phantom NoteTrack fields, caught only because they exceeded the struct's known size.

Writing a rule down does not apply it. This wake encodes all six guards in one tool with a selftest.

---

## 1. The six guards

| # | failure | wake | guard |
|---|---|---|---|
| 1 | offset-only scans returning hundreds of unreadable hits | early | count hits, warn above 200 |
| 2 | chain scan stepped over `bx lr`, joining two functions | 44 | stop at unconditional returns and branches |
| 3 | offset matched with no idea what the base register held | 45 | require an anchor that proves the type |
| 4 | `Rn = r15` hits were pc-relative literal loads, not fields | 47 | never accept r15 as a base |
| 5 | vtable slot index read as a struct field | 48 | skip if the base was just loaded from `[Rm,#0]` |
| 6 | register reassigned mid-function, so later offsets were a different object | 49, 50 | stop at any write to the anchor register |

Plus a size check: with `--size`, any offset at or beyond the struct size is flagged **CONTAMINATED**.
This caught iteration 50's error, so it runs automatically now.

## 2. A guard that was too aggressive

The first version failed its own selftest — only `+0x70` and `+0x74` of 12 known NoteTrack fields.
Guard 2 masked off the condition nibble, so `(x & 0x0F000000) == 0x0A000000` matched **conditional**
branches too. `beq` is normal in-block control flow; stopping there killed the walk almost immediately.

Fix: require `cond == 0xE` and bit 24 clear — a genuinely unconditional `b`. A guard that's too strict
loses real fields just as a missing guard invents fake ones. Only the selftest told the difference.

## 3. Validation

**Selftest** (`--selftest`) walks the 12 verified NoteTrack callback anchors and checks three things:
every real field is found, no phantom offset appears, and nothing exceeds `0xA8`.

```
selftest: 12 offsets found: ['0x1', '0x70', '0x74', '0x7c', '0x88', '0x90',
                             '0x98', '0x9c', '0x9e', '0xa0', '0xa1', '0xa2']
selftest PASSED
```

The phantom set it must never report is `{0x10, 0x28, 0x40, 0x5C, 0xDF, 0xE0, 0x158}` — every false
field iterations 49 and 50 produced by hand.

**Cross-validation.** Iteration 50 hand-derived that the dispatcher reads NoteTrack `+0x7C`, `+0x80`,
`+0x84` and `+0x88`. Given the four dispatcher anchors, the tool returns exactly that set, nothing else.

**Negative control.** Anchoring at `0x02157E70` — the `ldrsb r0,[r0,#0xdf]` *after* query 66 reassigns
`r0` — correctly flags `+0xDF` as CONTAMINATED. That phantom fooled me last wake; now caught
automatically.

## 4. What this does not fix

- **Thumb is not handled.** ARM only, like most tooling here.
- **Guard 3 is still human judgement.** The tool can't verify that an anchor register actually holds the
  struct — it just applies mechanical guards once you assert it. A wrong anchor gives wrong fields;
  the size check is the only backstop, and only works when the size is known.
- **Cross-block flow is not tracked.** The walk is straight-line from the anchor, so fields after a
  conditional join are missed. Under-reports, not over-reports — the right direction.

## Predictions status

| Claim | Verdict |
|---|---|
| All six guards can be applied mechanically | **CONFIRMED** — selftest passes with 12 real fields, 0 phantoms |
| The tool reproduces iteration 50's hand-derived field set | **CONFIRMED** — exactly `+0x7C`, `+0x80`, `+0x84`, `+0x88` |
| The size check catches a deliberately bad anchor | **CONFIRMED** — `+0xDF` flagged CONTAMINATED |
| My first version of guard 2 was correct | **REFUTED** — it stopped at conditional branches and lost 10 of 12 fields |
| The tool handles Thumb | **not claimed** — ARM only |

## Next angles, ranked

1. **Map the entity table behind query 71** using the new tool — strides `0xC0` and `0x30`, count at
   `[global+0x158]`, fields `+0x158` and `+0x170`.
2. **Identify the NoteTrack `+0x7C`/`+0x80`/`+0x84` objects.** Three pointer fields, each backing a query;
   each is a fresh anchor for this tool.
3. Still open: `prmData+0x0C/+0x10/+0x14`, the 68-entry table at `0x02171FEC`, the 24 positive
   `ProjectileId` values, the `34-63` no-op band, and the harness watchpoint recipe for the collision walker.
