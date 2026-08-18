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

PLACEMENT, per the project owner: tapping the target cell alone works, as do
tap-then-A, tap-dpad-A and A-dpad-A. There is no dragging.

IMPORTANT and it explains a confusing early result: HELPER koma need a DIRECTION.
After placing a helper you must point it at a battle character to say who receives its
passive. The only exception is a helper granting +1 SP, since SP is shared across the
team. The first placement attempt here used セナ's 1-koma, which the list shows as
ヘルプ -- so it changed 1097 bytes of deck state, left the target cell looking empty,
and put a marker on an already-placed koma. That was an incomplete helper placement
waiting for a direction, not a failure to place. Prefer a バトル koma when testing the
basic flow.

PLACEMENT CONFIRMED, and the missing piece was a SECOND TAP. A koma row needs two
taps, exactly like the deck slots and the rule toggles: the first highlights the row,
the second selects it and brings the canvas down. One tap alone looks like nothing
happened (fingerprint moved 3.96) and misled an earlier attempt here.

The measured sequence, on 悟空's 4-koma (バトル) after filtering to Dragon Ball:

    tap koma row  (1st)   fingerprint  3.96   highlight only
    tap koma row  (2nd)   fingerprint 64.59   canvas comes down, koma preview floating
    tap canvas cell       fingerprint 22.41   placed; deck state +212 bytes

Confirmed by both signals, which is the standard this project holds itself to: a canvas
screenshot showing the 悟空 koma sitting in the top-left cell, AND a deck-state diff
well above the 18-byte noise floor.
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
# Measured from a 512x384 render of the 256x192 bottom screen: row 1 centre sits at
# DS y~31 with ~16px spacing. An earlier guess of DY=20 was wrong.
KOMA_ROW_Y0, KOMA_ROW_DY = 31, 16

# Canvas cell centres once the canvas is down (X), from a cleared 5x4 grid.
CANVAS_COL_X = [24, 71, 119, 166, 214]
CANVAS_ROW_Y = [24, 66, 114, 160]

# Clears the whole deck: the small tray button under SEL in the right-hand strip.
# CONFIRMED -- one tap emptied the canvas to a clean 5x4 grid, 107 bytes of deck
# state changed. (The owner describes a confirmation step; the canvas came back empty
# without one being visible here, so treat that detail as unverified.)
TAP_CLEAR_DECK = (248, 88)

# Series filter. The panel lists series as an icon grid with the focused series named
# across the top. Tapping the focused DRAGON BALL icon applied the filter -- CONFIRMED,
# fingerprint moved 81.68 and the list changed to 悟空 / 超サイヤ人悟空 / ベジット.
# Dragon Ball is a good default because it has many バトル koma.
# NOT confirmed: what opens the panel. A tap at (7, 8) on the 作 header and an L press
# both measured as no-ops (0.12 and 0.10), yet the panel was open immediately after --
# so something else opened it and the attribution is unknown.
TAP_SERIES_HEADER = (7, 8)
TAP_SERIES_DRAGONBALL = (23, 111)

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


def place_koma(row, col_x, row_y, settle=220):
    """Place koma list entry `row` at a canvas cell. Returns bytes of deck state changed.

    Two taps on the row, not one: the first only highlights it. Then a tap on the
    target cell commits the placement.

    Caller must already be in the editor with the intended series filter applied.
    Verify the result from BOTH the returned byte count and a canvas screenshot --
    a helper koma will change deck state and still not look placed, because it is
    waiting for a direction.
    """
    before = deck_state()
    x, y = koma_row(row)
    nav.tap(x, y, settle=150)     # highlight
    nav.tap(x, y, settle=settle)  # select; canvas drops to the bottom screen
    nav.tap(col_x, row_y, settle=settle)
    n, _ = deck_changed(before, deck_state())
    return n


def canvas_down():
    """Bring the deck canvas to the bottom screen so it can be tapped."""
    nav.advance(1, ["X"])
    nav.advance(150)


def main():
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
