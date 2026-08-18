#!/usr/bin/env python3
"""Build a multi-koma deck in the editor, verifying every step from pixels.

Usage:
    python3 build_deck.py --slot de_db          # from a saved editor savestate
    python3 build_deck.py --enter               # route in from the top menu
    python3 build_deck.py --slot de_db --koma 3 # stop after 3 koma

WHY IT IS GREEDY RATHER THAN SCRIPTED. The obvious design -- name the koma you want
by list index -- does not survive contact with the editor. Committing a koma scrolls
the list, the list wraps, and re-applying the series filter only resets the scroll
while the deck is still empty. Worse, adding one koma GREYS OUT every other koma of
the same character, including alternate forms and fusions: after 悟空 went in, all
悟空, 超サイヤ人悟空 and ベジット rows went grey. A fixed plan of indices therefore
aims at the wrong rows and at koma the game will not accept.

So this reads the current screen every time: take the first row that is still
available, drop it on the first cell that will hold it, confirm, repeat.

WHAT COUNTS AS CONFIRMATION. Neither the canvas nor the deck-state RAM region can
tell a committed koma from the floating preview a single cell tap leaves behind --
the canvas looks identical and the RAM region moves by over a thousand bytes either
way. Only a canvas up/down round trip separates them, because the preview is
dropped and a committed koma is not. Every placement here is confirmed that way.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nav                  # noqa: E402
import deck_editor as DE    # noqa: E402
import emu_health as EH     # noqa: E402
import screenlib as SL      # noqa: E402
import boot_verified as BV  # noqa: E402


def cells(grid):
    """Row-major (row, col) of every occupied cell."""
    return [(r, c) for r, row in enumerate(grid)
            for c, v in enumerate(row) if v < DE.EMPTY]


def enter_editor(deck_slot=2):
    """top menu -> デッキセレクト -> slot options -> 編集."""
    n, d = BV.reach_top_menu()
    print("  top_menu after %d START presses (%.2f)" % (n, d))
    nav.advance(90)
    nav.tap(*DE.TAP_DECKMAKE_ICON, settle=240)
    nav.advance(1, ["A"])
    nav.advance(240)
    y = DE.DECK_SLOT_Y[deck_slot]
    nav.tap(DE.DECK_SLOT_X, y, settle=150)
    nav.tap(DE.DECK_SLOT_X, y, settle=240)
    nav.tap(*DE.TAP_EDIT_MENU_ITEM, settle=260)
    d = SL.wait_for("deck_editor", max_frames=900)
    print("  deck_editor verified (%.2f)" % d)


def free_score(cell, occupied):
    """How much empty room a cell has around it, for choosing a placement target.

    Needed because a koma's footprint is not known in advance and a placement that
    overlaps an existing koma does not fail -- it EVICTS the koma underneath, back
    to the list. That is how an early run silently lost a 4-koma: it dropped a
    2-koma on a free cell whose neighbour belonged to the koma already there. So
    aim at whichever free cell has the most free space around it.
    """
    r, c = cell
    return sum(1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
               if 0 <= r + dr < 4 and 0 <= c + dc < 5
               and (r + dr, c + dc) not in occupied)


def place_one(committed, tag):
    """Commit one koma. Starts and ends on the LIST view. Returns the new set.

    Returns None when nothing more can be placed -- no row is still available, or
    no attempt grew the deck.
    """
    rows = DE.available_rows("bd_%s_avail" % tag)
    for page in range(4):
        if rows:
            break
        # Every visible row is greyed out, but the rest of the series may be fine --
        # one character's koma greying out can cover the whole visible page.
        print("  page %d is all greyed out, scrolling" % page)
        DE.scroll_list()
        rows = DE.available_rows("bd_%s_avail%d" % (tag, page))
    if not rows:
        print("  no koma rows are still available")
        return None

    targets = sorted([(r, c) for r in range(4) for c in range(5)
                      if (r, c) not in committed],
                     key=lambda cell: (-free_score(cell, committed), cell))
    for row in rows:
        for target in targets[:6]:
            DE.ensure_canvas(False, "bd_%s_pre" % tag)   # list view to pick from
            DE.select_koma(row)            # canvas comes down holding the koma
            DE.commit_at(*target)
            if DE.direction_mode("bd_%s_dir" % tag):
                # A helper koma landed and wants a direction. Accept the focused
                # arrow; without this the dimmed canvas reads as a full 20/20 deck.
                print("    helper koma: accepting the focused direction")
                DE.confirm_direction()
            now = set(cells(DE.committed_cells("bd_%s" % tag)))
            DE.ensure_canvas(False, "bd_%s_post" % tag)  # back to the list either way
            if len(now) > len(committed):
                if not now > committed:
                    print("    row %d at %s evicted %s and placed %s"
                          % (row, target, sorted(committed - now),
                             sorted(now - committed)))
                else:
                    print("  row %d -> cell %s: +%d cells %s, %d/20 used"
                          % (row, target, len(now - committed),
                             sorted(now - committed), len(now)))
                return now
            print("    cell %s did not grow the deck (%d -> %d cells), trying again"
                  % (target, len(committed), len(now)))
            committed = now              # the canvas is the truth, whatever happened
        print("  row %d would not go in, trying the next available row" % row)
    return None


def main():
    sys.stdout.reconfigure(line_buffering=True)
    slot, enter, want = None, False, 4
    a = sys.argv[1:]
    for i, x in enumerate(a):
        if x == "--slot":
            slot = a[i + 1]
        elif x == "--koma":
            want = int(a[i + 1])
        elif x == "--enter":
            enter = True
    if slot:
        r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"),
                            "state", "load", slot], capture_output=True, text=True,
                           cwd=HERE)
        if r.returncode != 0:
            raise SystemExit("could not load %r: %s%s" % (slot, r.stdout, r.stderr))
        EH.ensure_alive(slot)
        nav.advance(150)
        print("loaded savestate %r" % slot)
    elif enter:
        enter_editor()

    # The canvas must be DOWN for both the bin and any occupancy read, and X is
    # what brings it down.
    DE.ensure_canvas(True, "bd_start_view")
    grid = DE.canvas_cells("bd_start")
    if cells(grid):
        print("clearing %d occupied cells" % len(cells(grid)))
        grid = DE.clear_deck()
        if cells(grid):
            raise SystemExit("clear_deck left %d cells occupied: %s"
                             % (len(cells(grid)), grid))
        print("  deck cleared, all 20 cells empty")
    DE.ensure_canvas(False, "bd_list_view")   # back to the list to pick koma

    DE.filter_series(*DE.SERIES_DRAGONBALL)
    print("filtered the list to DRAGON BALL")

    # Battle koma first, and that ordering is not cosmetic: a helper koma has to
    # point at a battle character, so placing helpers first leaves them pointing at
    # nothing. Support and help come after.
    plan = (["battle"] * max(1, want - 2) + ["support", "help"])[:want]
    committed = set()
    for i, kind in enumerate(plan):
        DE.filter_kind(kind)
        got = place_one(committed, "k%d" % i)
        if got is None:
            print("  nothing more would go in; stopped after %d koma" % i)
            break
        committed = got

    # A deck without a leader will not leave the editor. The last committed cell is
    # used because battle koma go in first and are the largest, so the bottom-right
    # of the used area belongs to one; the exit check below is what actually proves
    # the stamp landed on a battle koma.
    DE.ensure_canvas(True, "bd_leader_view")
    grid = DE.canvas_cells("bd_before_leader")
    here = cells(grid)
    if here:
        leader = here[-1]
        print("stamping the leader sticker on the koma at %s" % (leader,))
        DE.set_leader(*leader)

    DE.ensure_canvas(True, "bd_final_view")
    grid = DE.canvas_cells("bd_final")
    print("\nfinal deck, 1.0 empty and 0.0 used:")
    for row in grid:
        print("  ", row)
    print("%d of 20 cells used" % len(cells(grid)))
    subprocess.run(["magick", os.path.join(nav.SHOT_DIR, "bd_final.ppm"),
                    os.path.join(nav.SHOT_DIR, "bd_final.png")])

    # The game's own verdict, which beats any pixel check we could invent: exiting
    # raises a caution if the deck is not playable. Stops at the save prompt without
    # answering it -- saving writes the cartridge save file.
    valid = DE.exit_editor()
    print("the game accepted the deck: %s (stopped at the save prompt)" % valid)
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
