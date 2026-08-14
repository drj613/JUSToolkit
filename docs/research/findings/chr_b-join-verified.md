# Findings: the chr_b → character-name join is verified

The harness session raised a doubt worth taking seriously: several of my conclusions ride on the
join `koma.bin abilityId → chr_b index → komatxt.bin name`, and their RAM showed a HUD character
that didn't match `chr_b[0]`. If that join were scrambled, the whole 74-character HP table would be
mislabelled.

**It holds.** Three checks.

## 1. Self-consistency across 74 entries

Every `chr_b` index is reached by battle panels from **exactly one manga series** — 0 of 74 entries
span more than one. A scrambled join would produce indices whose panels came from unrelated series,
because `seriesIdx` is an independent field in the same record.

## 2. Two live RAM identifications match exactly

| chr_b | my join says | base HP (slot 0) | harness observed in RAM |
|---|---|---|---|
| `0` | 悟空 (Goku), series `db` | `152` | Goku at `160.0` = `152 + 8` ✓ |
| `12` | ルフィ (Luffy), series `op` | `144` | Luffy at `152.0` = `144 + 8` ✓ |
| `20` | ナルト (Naruto), series `na` | `144` | Naruto at `144.0`, benched, no bonus ✓ |

Three independent characters, three matching base values, with names and series both consistent.

## 3. The apparent discrepancy has a different cause

Their HUD showed a character other than 悟空 while slot 0's `chr_b` index was unchanged. That is
explained by their own second finding — **a battle slot is a deck slot, not the active fighter** —
not by a bad join. The join and the slot semantics were two separate questions and only one was
wrong.

## A check that did not apply

I tried cross-referencing `docs/research/battle-chars-passives.json` (66 entries) and got **zero**
name overlap. That's not a failure of either source: that file uses English uppercase romanisations
(`GINTOKI SAKATA`) while `komatxt.bin` holds Japanese (`銀時`). The check was inapplicable, not
negative. Matching them would need a romanisation table, which doesn't exist yet — worth building
if anyone wants to join the two datasets.
