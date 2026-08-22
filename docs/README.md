# docs/ — how this tree is split

Restructured 2026-08-21 (bead `jus-wayfinder-map-digi.15`). Five directories, split by
trust and purpose:

| Directory | What it holds |
|---|---|
| `confirmed-facts/` | Portable specs of how the game works. Every claim carries a bead. |
| `research/` | The live lab notebook: canon docs plus the append-only `findings/` journal. Superseded material is in `research/archive/`. |
| `harness/` | The agentic melonDS harness: `scripts/emu` usage, the melonDS-lua fork, GDB session guides. |
| `toolkit/` | The JUSToolkit C# project itself: extractors and file-format tooling usage. The docfx site sources stay in `articles/` for the build. |
| `orchestration/` | Process: coordination protocol, loop charters, handoffs. Retired memory notes are in `orchestration/archive/memory/`. |

## The trust rule

- `confirmed-facts/` cites `research/`, **never the reverse**.
- `harness/` and `toolkit/` describe **how to measure or extract** — never what is
  true of the game. A game fact belongs in `research/` (and, once bead-backed, in
  `confirmed-facts/`).
- Beads (`br`) is the system of record; documents explain, they do not decide.
  Lint with `python3 scripts/check_docs.py`.

Other directories (`articles/`, `api/`, `images/`, `template/`, `toc.yml`,
`docfx.json`) belong to the docfx site. `design/`, `characters/`, and `formats/`
predate the split and are unsorted legacy; treat their claims as unverified unless
bead-backed.
