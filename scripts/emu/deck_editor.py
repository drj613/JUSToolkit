#!/usr/bin/env python3
"""Verified building blocks for driving the deck-make editor (ov05 / KomaEdit).

WORK IN PROGRESS. What is confirmed is recorded here; what is not is marked as such,
because the expensive mistake in this project is treating a plausible reading as a
measured one.

HOW TO GET HERE (all pixel-verified, see Menu-Nav-Verified-From-Pixels.md):
    top_menu -> tap (33, 96) デッキメイク + A -> deck list  (ov01, DeckSelect.cpp)
    tap a deck slot to focus it, tap again -> options submenu
    tap (208, 58) 編集 -> the editor           (ov05 99.5%, KomaEdit)

CONFIRMED MECHANICS
  * The DS touchscreen is the BOTTOM screen only, and the deck canvas starts on the
    TOP screen, so the canvas cannot be tapped until it comes down.
  * X brings the canvas down to the bottom screen (fingerprint moves 69.35).
    Y does not (1.42).
  * Tapping a koma row in the list focuses it and brings the canvas down
    (fingerprint moves 65.18).
  * Canvas cells are ~40x35 DS pixels; the right-hand button strip (L-R / X / Y /
    SEL) occupies roughly DS x 240-255, so avoid tapping there.

THE RAM ORACLE, which matters more than the pixels here.
Deck state lives in 0x020A0C00-0x020B0000 (Deck-Memory-Structure.md). Diffing that
region across an action gives a definitive "did the deck actually change", which the
screen does not: a canvas tap moved the bottom-screen fingerprint by only 0.33 while
changing 121 bytes of deck state. Measured on this screen:

    idle drift over 120 frames      18 bytes   <- the noise floor
    tap an empty canvas cell       121 bytes
    then press A                  1097 bytes

NOT YET CONFIRMED -- the placement interaction.
The tap-then-A sequence above changed 1097 bytes of deck state, but a screenshot
afterwards shows the target cell still EMPTY, with the placement cursor sitting
exactly where it was tapped and a black marker appearing on a DIFFERENT, already-
placed koma. So that sequence did something real and it was probably not "place the
selected koma here" -- possibly a removal. Do not build on it until the actual
placement gesture is pinned down and confirmed by BOTH a canvas screenshot showing
the koma present and a deck-region diff.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nav  # noqa: E402

# Navigation targets, DS bottom-screen coordinates.
TAP_DECKMAKE_ICON = (33, 96)     # top menu, row 2 col 1
TAP_EDIT_MENU_ITEM = (208, 58)   # 編集, top entry of the deck options submenu
DECK_SLOT_X = 120
DECK_SLOT_Y = [56, 80, 105, 130, 154]   # deck slots 1..5

KOMA_ROW_X = 75
KOMA_ROW_Y0, KOMA_ROW_DY = 29, 20       # first koma row, then every 20px

DECK_STATE_START = 0x020A0C00
DECK_STATE_END = 0x020B0000
IDLE_DRIFT = 18          # measured; treat anything at or below this as noise


def koma_row(n):
    return KOMA_ROW_X, KOMA_ROW_Y0 + n * KOMA_ROW_DY


def deck_state(path="/tmp/jus_deck_state.bin"):
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "dump",
                        hex(DECK_STATE_START), hex(DECK_STATE_END), path],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("deck dump failed: %s%s" % (r.stdout, r.stderr))
    with open(path, "rb") as f:
        return f.read()


def deck_changed(before, after):
    """Bytes of deck state that changed, and whether that beats the noise floor."""
    n = sum(1 for x, y in zip(before, after) if x != y)
    return n, n > IDLE_DRIFT


def canvas_down():
    """Bring the deck canvas to the bottom screen so it can be tapped."""
    nav.advance(1, ["X"])
    nav.advance(150)


def main():
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
