#!/usr/bin/env python3
"""Drive the deck-make editor (ov05 / KomaEdit) end to end.

Every constant here was measured off the emulator's own framebuffer -- a 256x384
PPM from `jusemu.py screendump`, where the bottom screen is rows 192..383, so an
image row maps to a DS touch y by subtracting 192. That directly-measured mapping
is why the geometry below can be trusted: no window scaling, no capture path, no
guessing.

ROUTE IN (pixel-verified, see Menu-Nav-Verified-From-Pixels.md):
    top_menu -> tap (33, 96) デッキメイク + A -> デッキセレクト (ov01, DeckSelect)
    tap a deck slot, tap it again          -> options submenu
    tap (208, 58) 編集                      -> the editor (ov05, KomaEdit)

The submenu offers 編集 / 名前へんこう / コピー / いれかえ / けす / とじる. One tap on
編集 enters the editor; there is no second tap, unlike almost everything else here.

THE ONE RULE THAT EXPLAINS THIS UI: nearly every control takes TWO TAPS. The first
tap moves focus, the second activates whatever is focused. It holds for koma rows,
deck slots, rule toggles, series icons, the clear-deck bin and the yes/no buttons in
its confirmation. Whenever a tap looks like a no-op here, the likeliest reason is
that it only moved focus. The exceptions found so far are the 編集 menu item and the
column headers, which act on the first tap.

SCREEN LAYOUT, list view (bottom screen):
    y 0..18     column headers: 作 | 名前 | 数 形 | 種 | 属 | (sparkle) | (sort)
    y 23..188   the koma list, nine visible rows
    y 190..192  the button-hint bar
    x 238..256  the right-hand button strip; never tap through it

KOMA ROWS. Row n spans y 23+16n .. 40+16n and its centre is y = 31+16n; adjacent
rows share their 2px border. `koma_row()` returns the centre. The row highlight is a
border that PULSES from bright red to pale pink, so a detector tuned to saturated red
misses it half the time -- see `highlighted_row()`, which keys on red-vs-green
dominance instead of absolute redness.

CANVAS GRID, measured on a freshly cleared deck: columns span x 2..45, 50..93,
98..141, 146..189, 194..237 and rows span y 3..44, 51..92, 99..140, 147..188. Both
pitches are exactly 48, giving the centres in CANVAS_COL_X / CANVAS_ROW_Y. (An
earlier session had the columns right but the rows drifting low by up to 8px.)

The canvas starts on the TOP screen and the touchscreen is the bottom screen only,
so it cannot be tapped until X brings it down. X toggles: canvas down, canvas up.

FILTER PANELS -- this was the open question, and the answer is the column headers.
Tapping a header at y=8 opens that column's filter panel:

    x   4..28   作品   series, an icon grid, focused series named across the top
    x  36..140  名前   kana rows あかさたな / はまやらわ
    x 145..160  数     koma sizes 1..8
    x 164..176  形     koma shapes
    x 185..195  種類   バトル / サポート / ヘルプ
    x 205..215  属性   カ / 知 / 笑 / なし
    x     ~222  (sparkle) no-op
    x 236..252  opens the same ならびかえ sort menu as the R button

A previous session tapped (7, 8) and measured a no-op, then found the panel open
anyway and recorded the attribution as unknown. (4, 8) opens it reliably; (7, 8) is
a pixel or two outside the 作 cell.

R opens ならびかえ (sort by 作品 / 名前 / 数 / 種類 / 属性). START does NOT open a
menu -- it launches a trial battle with the deck as it stands, so avoid it here.

LIST ADDRESSING, and this is the subtle part -- there is NO stable row address.
Committing a koma scrolls the list, and the list WRAPS, so saturating with UP does
not reach the top: 20 UP presses from index 4 landed deep in the list, the same trap
the top-menu grid sets. Re-applying the series filter does reset the scroll while the
deck is empty, but stops doing so once a koma is committed, so it cannot be relied on
as an addressing reset either.

The way to drive the list is therefore to read the CURRENT screen and act on what is
visible: `available_rows()` reports which visible rows can still be added, and rows
are selected by position on screen. Anything that assumes "list index n" survives
across a placement is wrong.

Both selection paths work: tap a row twice, or move the cursor with UP/DOWN and
press A.

THE RAM ORACLE, and a correction. Deck state lives in 0x020A0C00-0x020B0000. It is
much noisier than an earlier session recorded: an 18-byte "noise floor" only holds
for a truly idle screen. Measured here, a savestate load plus 200 idle frames moves
17-42 bytes, but ANY input -- a tap on empty space, a d-pad press, opening a menu --
moves 95-190 bytes, and SELECT alone moves 1041 with no pixel change at all. So
treat this region as confirmation of a big change, not as a fine-grained detector:

    idle after a state load          17-42 bytes
    a tap or press that does nothing 95-190 bytes
    clearing a full deck                361 bytes
    placing one 4-koma                 1326 bytes

That noise is why the earlier "one tap on the bin cleared the deck, 107 bytes
changed" reading was a false positive: 107 bytes is what an ineffective tap costs,
and the bin in fact needs two taps and a confirmation. Use `canvas_cells()` for
anything finer -- it reads occupancy straight off the framebuffer and separates
cleanly, 1.00 for an empty cell against 0.00 for an occupied one.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nav  # noqa: E402

# --- route in ---------------------------------------------------------------
TAP_DECKMAKE_ICON = (33, 96)     # top menu, row 2 col 1
TAP_EDIT_MENU_ITEM = (208, 58)   # 編集, top entry of the deck options submenu
DECK_SLOT_X = 120
DECK_SLOT_Y = [56, 80, 105, 130, 154]   # deck slots 1..5

# --- koma list --------------------------------------------------------------
KOMA_ROW_X = 75
KOMA_ROW_Y0, KOMA_ROW_DY = 31, 16
KOMA_ROWS_VISIBLE = 9

# --- canvas -----------------------------------------------------------------
CANVAS_COL_X = [24, 72, 120, 168, 216]
CANVAS_ROW_Y = [24, 72, 120, 168]

# --- right-hand strip, canvas view only -------------------------------------
TAP_CLEAR_DECK = (248, 87)       # the bin; two taps, then confirm
TAP_CONFIRM_YES = (88, 103)      # はい in 「コマを全てリストに戻しますか？」
TAP_CONFIRM_NO = (168, 103)      # いいえ, which is the focused default

# Exit prompt 「デッキメイクを終了します。セーブしますか？」, measured off its own frame.
TAP_SAVE_YES = (53, 110)
TAP_SAVE_NO = (124, 110)
TAP_SAVE_CLOSE = (198, 110)      # とじる, the focused default -- back to editing

# --- filter panels ----------------------------------------------------------
HEADER_Y = 8
HEADER_X = {"series": 4, "name": 76, "size": 150, "shape": 170,
            "kind": 190, "nature": 210, "sort": 240}
# Series icon grid, measured from the 作品 panel: 11 columns at a 19.6px pitch,
# 4 rows. Dragon Ball is row 2 col 0 -- (23, 111), which is also where an earlier
# session found it, from a different measurement.
SERIES_COL_X = [23 + round(19.6 * i) for i in range(11)]
SERIES_ROW_Y = [63, 87, 111, 135]
SERIES_DRAGONBALL = (2, 0)       # (row, col)

# 種類 panel, measured off its own framebuffer: three pills in a row at y=39.
KIND_TAP = {"battle": (126, 39), "support": (170, 39), "help": (209, 39)}
KIND_CLOSE = (172, 61)           # とじる

DECK_STATE_START = 0x020A0C00
DECK_STATE_END = 0x020B0000
IDLE_DRIFT = 42          # measured after a savestate load; input alone costs ~100-190


def koma_row(n):
    return KOMA_ROW_X, KOMA_ROW_Y0 + n * KOMA_ROW_DY


# --- framebuffer reading ----------------------------------------------------
def read_ppm(path):
    """(width, height, rgb bytes) from the P6 screendump."""
    with open(path, "rb") as f:
        assert f.readline().strip() == b"P6", "not a P6 PPM: %s" % path
        w, h = (int(v) for v in f.readline().split())
        f.readline()
        return w, h, f.read(w * h * 3)


def _shot_ppm(tag="de"):
    p, _ = nav.shot(tag)
    return read_ppm(p)


def _px(buf, w, x, ds_y):
    """A bottom-screen pixel by DS coordinates. Bottom screen starts at row 192."""
    i = ((192 + ds_y) * w + x) * 3
    return buf[i], buf[i + 1], buf[i + 2]


def canvas_cells(tag="de_canvas"):
    """4x5 grid of "how empty each canvas cell looks", 1.0 empty to 0.0 occupied.

    Requires the canvas to be DOWN. Empty cells are a flat salmon-orange, so this
    samples an 81-point patch per cell and reports the orange fraction. Measured:
    1.00 for every cell of a cleared deck and 0.00 for every cell a koma covers,
    which is as clean a separation as this project has. A lone value near 0.8 is
    the cell cursor sitting on an otherwise empty cell.
    """
    w, _, buf = _shot_ppm(tag)
    grid = []
    for cy in CANVAS_ROW_Y:
        row = []
        for cx in CANVAS_COL_X:
            hits = total = 0
            for dy in range(-12, 13, 3):
                for dx in range(-12, 13, 3):
                    r, g, b = _px(buf, w, cx + dx, cy + dy)
                    total += 1
                    if r > 180 and 100 < g < 190 and 90 < b < 180:
                        hits += 1
            row.append(round(hits / float(total), 2))
        grid.append(row)
    return grid


EMPTY = 0.6      # above this a cell counts as empty; measured values are 0.0 or 1.0


def empty_cells(grid):
    """Row-major list of (row, col) for cells that look empty."""
    return [(r, c) for r, row in enumerate(grid)
            for c, v in enumerate(row) if v >= EMPTY]


# Cell centres read (235, 154, 121) normally and (117, 77, 60) dimmed.
DIRECTION_BROWN = (95, 150, 55, 110, 40, 90)   # r, g, b windows, measured


def direction_mode(tag="de_dir"):
    """True if the canvas is waiting for a HELPER koma's direction.

    Helper koma carry a passive that applies to one battle character, so after a
    helper is committed the editor asks which way it points: the canvas dims from
    salmon to brown and orange arrows appear on the helper's free edges, one of them
    focused. A is enough to accept the focused arrow.

    This matters beyond helpers, because while the canvas is dimmed every cell fails
    the "looks empty" test and `canvas_cells()` reports a full 20/20 deck. A build
    loop that does not check for this concludes the deck is full after one koma --
    which is exactly what happened here before this existed.
    """
    w, _, buf = _shot_ppm(tag)
    r0, r1, g0, g1, b0, b1 = DIRECTION_BROWN
    hits = total = 0
    for cy in CANVAS_ROW_Y:
        for cx in CANVAS_COL_X:
            r, g, b = _px(buf, w, cx, cy)
            total += 1
            if r0 < r < r1 and g0 < g < g1 and b0 < b < b1:
                hits += 1
    # Two dimmed cells is enough: no cell reads brown outside this mode, and
    # requiring a fraction of the grid would fail on a nearly full deck.
    return hits >= 2


def confirm_direction():
    """Accept the focused direction for a just-placed helper koma."""
    nav.advance(1, ["A"])
    nav.advance(240)


def highlighted_row(tag="de_row"):
    """Which koma row the cursor is on, or None.

    Keys on the highlight border being red-DOMINANT rather than saturated red: the
    border pulses between bright red and pale pink, and a saturated-red test sees
    it only during the bright phase. That cost an earlier calibration run its
    results -- it read "highlight gone" when the highlight had merely faded.
    """
    w, _, buf = _shot_ppm(tag)
    bands = []
    for y in range(19, 190):
        n = 0
        for x in range(10, 230):
            r, g, b = _px(buf, w, x, y)
            if r > 140 and r - g > 45 and r - b > 45:
                n += 1
        if n > 60:
            bands.append(y)
    if not bands:
        return None
    mid = (bands[0] + bands[-1]) / 2.0
    n = int(round((mid - KOMA_ROW_Y0) / float(KOMA_ROW_DY)))
    return n if 0 <= n < KOMA_ROWS_VISIBLE else None


AVAILABLE = 160   # row-background mean; greyed rows read 105-120, usable ones 203


def available_rows(tag="de_avail"):
    """Visible koma rows that can still be added, by row-background brightness.

    A row greys out when its koma cannot go in the current deck. The rule found so
    far: adding 悟空 greyed out every 悟空 koma AND 超サイヤ人悟空 and ベジット -- the
    alternate form and the fusion count as the same character. So a deck cannot be
    built from one character's koma, which is what broke the first attempt at a
    multi-koma build here.

    Greyed and usable separate cleanly: mean brightness across the name column is
    105-120 against 203.
    """
    w, _, buf = _shot_ppm(tag)
    out = []
    for n in range(KOMA_ROWS_VISIBLE):
        y = KOMA_ROW_Y0 + KOMA_ROW_DY * n
        vals = [sum(_px(buf, w, x, y)) // 3 for x in range(30, 110, 4)]
        if sum(vals) / float(len(vals)) >= AVAILABLE:
            out.append(n)
    return out


# --- RAM oracle -------------------------------------------------------------
def deck_state(path="/tmp/jus_deck_state.bin"):
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "dump",
                        hex(DECK_STATE_START), hex(DECK_STATE_END), path],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("deck dump failed: %s%s" % (r.stdout, r.stderr))
    with open(path, "rb") as f:
        return f.read()


def deck_changed(before, after):
    """Bytes of deck state that changed, and whether that beats idle drift."""
    n = sum(1 for x, y in zip(before, after) if x != y)
    return n, n > IDLE_DRIFT


# --- actions ----------------------------------------------------------------
# WHICH VIEW AM I ON. This has to be content-independent, so it reads the right-hand
# button STRIP rather than the canvas itself. With the canvas down the strip shows the
# L-R / X / Y / SEL buttons as white boxes, then the bin, then flat grey filler; on the
# list view the same column is the scrollbar. An earlier version sampled the canvas
# grid's gaps instead and broke the moment a koma preview covered one of them.
#
# Measured at x=246: canvas view has 251 at y=32/48/63 and the bin's dark core, 48, at
# y=87. The list view reads 73 there and an open filter panel reads 251, so both are
# rejected. The bin is the right landmark because it never changes -- the rounded slots
# further down DO fill in as koma are added, and keying on one of those was wrong.
VIEW_BUTTON_YS = (32, 48, 63)
VIEW_BIN_Y = 87
VIEW_X = 246


def canvas_is_down(tag="de_view"):
    w, _, buf = _shot_ppm(tag)
    buttons = [min(_px(buf, w, VIEW_X, y)) for y in VIEW_BUTTON_YS]
    bin_core = min(_px(buf, w, VIEW_X, VIEW_BIN_Y))
    # Sticker and direction modes DIM the whole screen, strip included: the buttons
    # drop from 251 to 146 and the bin from 48 to 113. So this compares the strip
    # against itself instead of against fixed levels -- three equal bright buttons
    # with a distinctly darker bin below them. On the list view the same pixels are
    # scrollbar, 0/0/73, and an open filter panel puts white over the bin too.
    return (min(buttons) > 140 and max(buttons) - min(buttons) <= 5
            and bin_core < min(buttons) - 25)


def toggle_canvas():
    """X swaps the canvas between the top screen and the touch screen."""
    nav.advance(1, ["X"])
    nav.advance(220)


def ensure_canvas(down, tag="de_ensure"):
    """Get the canvas onto the side we need, pressing X only if it is on the wrong one.

    Asserting instead of assuming is the point. Several editor actions end on a view
    the caller did not choose, and a blind X then lands the next tap on the other
    screen's widgets.
    """
    for _ in range(3):
        if canvas_is_down(tag) == down:
            return
        toggle_canvas()
    raise RuntimeError("could not get the canvas %s; see %s/%s.ppm"
                       % ("down" if down else "up", nav.SHOT_DIR, tag))


def open_filter(column):
    """Open one column's filter panel. Acts on a single tap, unusually."""
    nav.tap(HEADER_X[column], HEADER_Y, settle=220)


def filter_series(row, col):
    """Filter the koma list to one series, and reset the list scroll to the top.

    Two taps on the icon: the first only moves the panel's focus (the title
    changes to the new series while the list behind it does not), the second
    applies the filter and closes the panel.

    Resetting the scroll is the reason to call this before addressing rows by
    index. Placing a koma scrolls the list, and the list wraps, so there is no
    other cheap way back to a known position.
    """
    open_filter("series")
    x, y = SERIES_COL_X[col], SERIES_ROW_Y[row]
    nav.tap(x, y, settle=200)
    nav.tap(x, y, settle=260)


def filter_kind(kind):
    """Restrict the list to バトル, サポート or ヘルプ koma. Stacks with the series
    filter -- both header cells stay highlighted."""
    open_filter("kind")
    x, y = KIND_TAP[kind]
    nav.tap(x, y, settle=200)
    nav.tap(x, y, settle=260)


def set_leader(cell_row, cell_col):
    """Stamp the leader sticker on the battle koma covering a cell.

    A deck without a leader is rejected: leaving the editor raises
    「リーダーが居ません。バトルコマにリーダーシールを貼ってください。」 and no
    amount of correct koma placement gets past it. So this is part of building a
    deck, not a flourish.

    The sequence is one tap on the koma's cell to move the cell cursor onto it, then
    R to pick the sticker up -- a LEADER badge with L and R beside it appears in the
    corner and the canvas dims -- then A to stamp it and A again to leave sticker
    mode. B instead of the second A CANCELS the stamp, which looks like it worked
    (the badge is drawn) and then fails on exit.

    One tap, not two: two taps on an occupied cell pick the koma up out of the deck.
    """
    nav.tap(CANVAS_COL_X[cell_col], CANVAS_ROW_Y[cell_row], settle=220)
    nav.advance(1, ["R"])
    nav.advance(240)
    nav.advance(1, ["A"])
    nav.advance(280)
    # Then leave sticker mode. The number of A presses is not fixed, so press until
    # the dim clears rather than counting -- and never press B, which cancels the
    # stamp while still showing the badge.
    for _ in range(4):
        if not direction_mode("de_leader_dim"):
            return
        nav.advance(1, ["A"])
        nav.advance(280)
    raise RuntimeError("the canvas stayed dimmed after stamping the leader; see "
                       "%s/de_leader_dim.ppm" % nav.SHOT_DIR)


# The exit prompt is a BLACK dialog box, and that is what identifies it: the band it
# occupies reads a mean brightness of 54 with the prompt up, against 151-154 for the
# white caution dialog or for the plain list view behind it. Colour cannot be used --
# the caution's red text and the list's red row backgrounds are indistinguishable.
PROMPT_BAND = (24, 232, 62, 78)
PROMPT_DARK = 90


def save_prompt_open(tag="de_prompt"):
    w, _, buf = _shot_ppm(tag)
    x0, x1, y0, y1 = PROMPT_BAND
    vals = [sum(_px(buf, w, x, y)) // 3
            for y in range(y0, y1) for x in range(x0, x1)]
    return sum(vals) / float(len(vals)) < PROMPT_DARK


def exit_editor():
    """Leave the editor, stopping at the save prompt. Returns True if the deck is valid.

    "Valid" here means the game raised no caution on the way out, which is a stronger
    statement than any pixel check on the canvas: it is the game's own verdict on
    whether the deck is playable. An invalid deck interposes the missing-leader
    caution, which only A dismisses -- B does nothing to it.

    Deliberately stops at the prompt rather than answering it. Confirming セーブ
    writes the deck into the cartridge save, whose SHA-256 is recorded in
    hashes.json, so that is the caller's decision to make.
    """
    # From the canvas view B only swaps back to the list, so make sure we are already
    # there or the exit silently does nothing.
    ensure_canvas(False, "de_exit_view")
    nav.advance(1, ["B"])
    nav.advance(340)
    if save_prompt_open("de_exit"):
        return True
    nav.advance(1, ["A"])
    nav.advance(300)
    if not save_prompt_open("de_exit2"):
        raise RuntimeError("pressed B and then A leaving the editor and never got "
                           "the save prompt; see %s/de_exit2.ppm" % nav.SHOT_DIR)
    return False


def clear_deck():
    """Empty the deck. Requires the canvas to be DOWN.

    Two taps on the bin raise 「コマを全てリストに戻しますか？」 with いいえ focused,
    so はい also needs two taps. Returns the cell grid afterwards, which the caller
    should check is all-empty -- that is the only trustworthy confirmation, since
    the deck-state byte count cannot separate a real clear from an ignored tap.
    """
    nav.tap(*TAP_CLEAR_DECK, settle=200)
    nav.tap(*TAP_CLEAR_DECK, settle=220)
    nav.tap(*TAP_CONFIRM_YES, settle=200)
    nav.tap(*TAP_CONFIRM_YES, settle=260)
    return canvas_cells("de_cleared")


def scroll_list(steps=KOMA_ROWS_VISIBLE):
    """Move the list cursor down, which drags the visible window with it.

    Needed because `available_rows()` only sees the nine visible rows. After one
    character's koma go grey the whole visible page can be unusable while the rest
    of the series is still fine, so a build loop has to be able to page down. The
    list wraps, so this must always be bounded by the caller.
    """
    for _ in range(steps):
        nav.advance(1, ["DOWN"])
        nav.advance(8)
    nav.advance(160)


def select_koma(index):
    """Focus and select koma `index`, which brings the canvas down holding it.

    `index` counts from the top of the list, so this is only correct with the
    scroll at the top -- call filter_series() first. Rows past the ninth are
    reached by moving the cursor to row 0 with a single tap (focus only, no
    selection) and then pressing DOWN.
    """
    if index < KOMA_ROWS_VISIBLE:
        x, y = koma_row(index)
        nav.tap(x, y, settle=170)
        nav.tap(x, y, settle=240)
        if not canvas_is_down("de_select"):
            raise RuntimeError(
                "selecting koma row %d did not bring the canvas down, so the koma "
                "is not held and every later tap would hit the list instead. See "
                "%s/de_select.ppm" % (index, nav.SHOT_DIR))
        return
    x, y = koma_row(0)
    nav.tap(x, y, settle=170)
    for _ in range(index):
        nav.advance(1, ["DOWN"])
        nav.advance(8)
    nav.advance(160)
    nav.advance(1, ["A"])
    nav.advance(240)


def place_at(cell_row, cell_col, settle=260):
    """Move the floating koma preview to a canvas cell. Does NOT commit it."""
    nav.tap(CANVAS_COL_X[cell_col], CANVAS_ROW_Y[cell_row], settle=settle)


def commit_at(cell_row, cell_col):
    """Place the held koma at a cell: move the preview there, then commit it.

    Two taps, like everything else here, and this one was worth chasing down. A
    single tap moves the floating preview onto the tapped cell and nothing more --
    the canvas then LOOKS exactly like a successful placement, and the deck-state
    region moves by over a thousand bytes, so both of the signals this project
    normally trusts agree on the wrong answer. The give-away is that toggling the
    canvas up and back down leaves the grid empty: the koma was never committed,
    only carried. `verified_commit()` is the check that catches it.
    """
    place_at(cell_row, cell_col)
    place_at(cell_row, cell_col)


def committed_cells(tag="de_committed"):
    """Occupancy after a canvas up/down round trip, so a floating preview is gone.

    This is the only occupancy read that means "actually in the deck".
    """
    ensure_canvas(False, tag + "_up")
    ensure_canvas(True, tag + "_down")
    return canvas_cells(tag)


def main():
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
