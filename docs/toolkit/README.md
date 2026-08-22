# Toolkit docs

How to extract — the JUSToolkit C# project (containers, extractors, file-format
tooling). Trust rule: these docs describe tool usage, never what is true of the game
(see `../README.md`).

The user-facing toolkit documentation is the docfx site and stays under
`../articles/` because `docfx.json` builds from that path:

- `../articles/tool/install.md` — installing the toolkit
- `../articles/tool/usage.md` — JUS.CLI usage
- `../articles/tool/scripts.md` — helper scripts
- `../articles/tool/scenegate.md` — SceneGate integration
- `../api/` — generated API reference for `src/JUS.Tool`

Research-side CLI recipes (e.g. `jus combat export-collision`, `export-chr`) are
quoted where they are used; the commands themselves are defined in `src/JUS.CLI`.
New toolkit-usage docs that are not part of the docfx site belong in this directory.
