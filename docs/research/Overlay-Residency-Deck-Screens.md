# Overlay residency on the deck screens: ov05 is the editor, ov01 is the list

**Result:** on the pixel-verified deck-make **editor** (`KomaEdit`), **ov05 matches live RAM at 99.5%** and ov01 drops to 4.8%. On the deck-make **list** screen it flips: **ov01 99.6%**, ov05 8.0%. Measured 2026-08-18.

This closes the `ov05_mode_UNIDENTIFIED` contradiction the atlas session has carried for dozens of iterations — and closes it in their favour. They predicted ov05 above 90% on the real deck-make screen, with ov01 dropping. Both predictions held.

## Why the old measurement disagreed

An earlier residency run reported ov01 at 99.8% on what it called "the deck editor." That number was almost certainly right — for the screen it actually sampled. The *label* was wrong.

The old navigation assumed the top menu's cursor starts on Jギャラクシー and that one RIGHT press reaches Jアリーナ. The top menu is actually a 4x2 icon grid whose cursor was found sitting on デッキメイク, so that route entered the deck-make section by accident and stopped at its deck list — `DeckSelect.cpp`, i.e. ov01. The screen is even titled デッキセレクト. Nobody measured wrong; the run measured a different screen than its label claimed.

See `../harness/Menu-Nav-Verified-From-Pixels.md` for the corrected route. Both screens here were confirmed from the framebuffer before sampling, and the editor was identified by its contents: the deck canvas on the top screen and a koma list on the bottom with 名前 / 数 / 形 / 種 / 属 columns.

## The measurements

Overlays share load addresses, so only the resident one matches:

| overlay | load | size | list screen | editor screen |
|---|---|---|---|---|
| ov00 | `0x0214CD20` | 85,760 | 5.8% | 9.9% |
| **ov01** | `0x0214CD20` | 135,456 | **99.6%** | 4.8% |
| ov02 | `0x0214CD20` | 65,152 | 4.9% | 9.8% |
| ov03 | `0x0214CD20` | 73,472 | 5.1% | 10.2% |
| ov04 | `0x0214CD20` | 86,208 | 5.4% | 9.6% |
| **ov05** | `0x0214CD20` | 152,928 | 8.0% | **99.5%** |
| ov06 | `0x0214CD20` | 154,688 | 6.5% | 8.7% |
| ov07 | `0x0214CD20` | 122,816 | 4.0% | 6.4% |
| ov08 | `0x0214CD20` | 128,160 | 1.8% | 1.8% |
| ov10 | `0x02172A60` | 215,264 | 100.0% | 100.0% |
| ov11 | `0x02172A60` | 61,440 | 1.8% | 1.8% |
| ov12 | `0x021AC1C0` | 167,776 | 100.0% | 100.0% |

ov09 and ov13 are 32 bytes each and both read 6.2%; a tiny mostly-zero blob matches almost anything, so those numbers are meaningless.

ov12 at 100% on both screens is expected — it holds the `ALWidget` / `ALTextDS` UI library, which every menu needs. ov10 at 100% on both is the WiFi overlay and less obviously expected; worth noting rather than explaining away.

## Independent support from the symbol tables

`modules.json` lists the source files, and it agrees without any runtime data:

- **ov1**: `DeckSelect.cpp`, `StageSelect.cpp`, `RuleSelect.cpp`, `JArenaRankingList.cpp`
- **ov5**: `DeckMake.cpp`, `KomaList.cpp`, `KomaEdit.cpp`, `KomaState.cpp`,
  `KomaHelp.cpp`, `KomaIBook.cpp`, `Database.cpp`, `JPower.cpp`

The deck *select* list belongs to ov1 and the deck *make* editor to ov5, from static symbols alone. Two representations — filenames in the symbol table and byte-for-byte overlay matching against live RAM — give the same answer. That kind of agreement cannot come from a shared mistake.

## A consequence worth chasing: the nature resolver may be the wrong one

The nature resolver at `0x0214E480` was found in **ov05**, and that address sits inside the shared `0x0214CD20` window. During a battle the resident overlay there is **ov06**, not ov05. So `0x0214E480` in battle points to ov06 code, and the resolver found in ov05 is only reachable on the deck-make screens — where natures are displayed and deck totals are computed — not on the battle damage path.

If that holds, it offers a clean explanation for a result this project has confirmed twice: **nature does not affect battle damage** (`Nature-System-Consolidated.md`). The resolver everyone has been reasoning about may simply be the editor's, and the battle code may not consult it at all.

Stated as a hypothesis, not a finding. Testing it means locating whatever reads nature during a battle with ov06 resident, which is atlas's territory.

## Reproducing

```bash
cd scripts/emu
python3 boot_verified.py                 # or navigate to the screen you want
python3 overlay_residency.py --label deck_editor_KomaEdit
```

Always confirm the screen from the framebuffer before sampling, and put the screen in the label. A label is a claim and needs the same evidence as a number — that is the whole lesson of the disagreement above.
