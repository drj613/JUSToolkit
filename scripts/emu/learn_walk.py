#!/usr/bin/env python3
"""Walk boot -> training battle, learning a fingerprint for each screen.

The button/tap sequence here is the CORRECTED one. The old sequence in
boot_to_battle.py was wrong in two places, and both were found by looking at the
screen rather than by reasoning:

  * The top menu is a 4x2 icon GRID whose cursor does not start on
    Jギャラクシー -- it was found sitting on デッキメイク. "One RIGHT to reach
    Jアリーナ" therefore walked into the deck editor, which is where the mystery
    編集/コピー submenu came from.
  * The grid WRAPS, so you cannot saturate to a corner to get a known position:
    UP x3 then LEFT x5 landed on オプション (bottom-right), not the top-left.

So this taps targets by absolute touchscreen coordinate instead of walking a
cursor. A tap names where it is going and does not care where the cursor was,
which is the only approach that scales to a 20-step deck-editor flow.

Tap coordinates are DS bottom-screen pixels (256x192).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nav          # noqa: E402
import screenlib as SL  # noqa: E402

# (label, action) where action is ("tap",x,y) | ("btn",[buttons]) | ("wait",)
WALK = [
    ("top_menu",     [("btn", ["START"])] * 5),
    ("arena_menu",   [("tap", 93, 49), ("btn", ["A"])]),
    ("deck_select",  [("tap", 180, 142), ("btn", ["A"])]),
    ("stage_select", [("btn", ["A"])]),
    ("rule_select",  [("btn", ["A"])]),
    ("battle",       [("btn", ["START"])]),
]


def do(action, settle):
    if action[0] == "tap":
        nav.tap(action[1], action[2], settle=settle)
    else:
        nav.advance(1, action[1])
        nav.advance(settle)


def main():
    sys.stdout.reconfigure(line_buffering=True)
    settle = 240
    for label, actions in WALK:
        for a in actions:
            do(a, settle)
        p, _ = nav.shot("walk_" + label)
        e = SL.learn(label)
        print("  %-14s -> %s" % (label, p))
    print("\nlearned: %s" % ", ".join(l for l, _ in WALK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
