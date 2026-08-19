# Findings: the query CLI already existed — 25 wakes of duplicated tooling

Loop-Atlas iteration 66. Process. New tool: `scripts/analysis/prior_art.py`.

Iteration 65 found five collision symbols sitting unread in `symbols.json` for 24 wakes. Digging deeper
turned up something worse: **`scripts/analysis/query.py` already does caller scans, cross-reference
lookup, immediate-offset search, literal-pool resolution, and disassembly** — every scan this phase
hand-rolled since iteration 17.

An *earlier phase of this same campaign* built it. The git history's first line:
`query.py search-op-imm added (selftest+gates pass)`.

---

## 1. What already existed

`jus_files/analysis/` holds eight generated artefacts, ~15 MB total:

| artefact | contents |
|---|---|
| `xrefs.json` | 12.7 MB: **16,648** literal_loads, **60,259** imm_offsets, **69,034** branches |
| `functions.json` | 1.8 MB: function inventory with caller/callee edges |
| `symbols.json` | 275 named functions from assert strings |
| `modules.json` | per-function (name, source `.cpp`) pairs |
| `arm9_tables.json` / `_ram.json` | detected pointer tables, index tables, struct arrays |
| `arm9_regions.json` | 18-region map |
| `cheat_addresses.json` | known cheat addresses by category |

And `query.py` exposes: `func`, `callers`, `callees`, `xrefs-to`, `search-imm`, `search-op-imm`,
`pool-values`, `disasm`, `strings`.

## 2. The duplication, measured

| what I built | wake | what already existed |
|---|---|---|
| `find_callers.py` — ARM+Thumb BL scan | ~17 | `query.py callers` |
| hand-rolled word-reference censuses (iterations 41, 47, 52, 63, 64) | many | `query.py xrefs-to` |
| hand-rolled literal-pool arithmetic, **every wake** | many | `query.py pool-values` |
| `struct_fields.py` immediate-offset walks | 51 | `query.py search-imm` over 60,259 prebuilt entries |
| `find_jump_tables.py --ldrsb` | 40 | `query.py search-imm` |

Verified against three hand-derived results:

1. **`xrefs-to 0x0214BE0C`** — returns the exact 9 sites I spent part of iteration 65 scripting.
2. **`callers 0x0207BD40`** — returns 2 callers, including a `functions.json` edge my
   `find_callers.py` **cannot see** (it only scans BL/BLX). The old tool is *better*.
3. **`pool-values 0x0214BE00 0x0214BE20`** — revealed **`0x0214BE08`**, a fifth manager global
   I had not found, referenced from `0x0207AE70`, `0x0207B29C`, `0x0207BC3C`, `0x0207BCC4`.

Point 3 is the sharpest: one command I never ran produced a new finding as a side effect.

## 3. Why the loose-ends rule failed

The rule was "before opening a binary, grep the docs directory." It fired correctly several times, but it
was scoped to **prose**. The misses were in:

- generated JSON artefacts (`symbols.json`, `xrefs.json`)
- an executable query interface (`query.py`)

Neither is a doc, so neither was searched. The rule's wording drew the search space too
narrowly, and every refinement (iteration 38's "grep `docs/` as a whole, for the concept as
well as the filename") stayed inside that same space.

## 4. The fix: `prior_art.py`

One command that searches everything at once: `docs/`, `symbols.json`, `modules.json`, the loop state's
61 `confirmed_constants` and 48 `lessons`, and for an address, `query.py xrefs-to`. `--inventory`
lists every artefact and every `query.py` subcommand with a one-line description.

Per iteration 51's lesson: **the guard goes in a tool, not a note.** Writing "grep symbols.json
first" as lesson 49 would have done exactly what lessons 1–48 did for this failure — nothing.

Validated two ways:

- `prior_art.py ColJoint` surfaces `Battle_ColJointManCreate` from `symbols.json` and `modules.json`
  directly, with no help from my prose. At iteration 52, it would have shown all five collision
  names and cut most of iterations 52–65's structural derivation.
- Control test on an uninvestigated subsystem — `prior_art.py Pursuer` — returns
  `Battle_PursuerCreate` `0x02161608` in `BattleCharaPursuer.cpp` from the artefacts, proving it does not
  just echo documents I wrote.

`--inventory` also warns that several `scripts/decomp` tools duplicate `query.py`
subcommands.

## Predictions status

| Claim | Verdict |
|---|---|
| `query.py` provides caller/xref/imm-offset/pool lookups | **CONFIRMED** — 9 subcommands, verified against 3 hand-derived results |
| My hand-rolled scans were necessary | **REFUTED** — all duplicated pre-existing capability |
| `find_callers.py` is at least as complete as `query.py callers` | **REFUTED** — misses `functions.json` caller edges |
| The loose-ends rule covered the generated artefacts | **REFUTED** — scoped to prose only |
| `prior_art.py` would have caught the iteration-52 miss | **CONFIRMED** — `ColJoint` resolves from artefacts alone |
| `prior_art.py` only echoes my own docs | **REFUTED** — control term `Pursuer` resolves from artefacts |
| `0x0214BE08` is a fifth manager global in that block | **PLAUSIBLE** — 4 literal loads, all in the collision modules; contents unread |

## Next angles, ranked

1. **Redo the bucket-producer search with `query.py search-imm`.** 60,259 prebuilt immediate-offset
   entries. The buckets-1-and-8 question (six manual checks over two wakes) becomes one
   command against a complete index.
2. **Run `prior_art.py` on every open question** before touching a binary: NoteTrack `+0x7C`/`+0x80`/
   `+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at `0x02171FEC`, the 24 positive
   `ProjectileId` values.
3. **Map `BattleCol.cpp`** (carried), starting from `prior_art.py BattleCol`.
4. **`0x0214BE08`** — the fifth global, found for free.
