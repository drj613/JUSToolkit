"""Known JUS memory addresses and pointer chains.

Ported from scripts/gdb/README.md (the GDB watcher is the historical
source; this file is the go-forward single source of truth).
HP values are stored at 1/4 scale (160 displayed = 40 stored).
"""

ADDRESSES = {
    # Battle state
    "battle_timer": 0x021DEA71,
    "special_meter_1": 0x021DF731,
    # HP, your side (active + deck slots, 0x50 apart)
    "hp_player_active": 0x021DF1D5,
    "hp_player_deck1": 0x021DF225,
    "hp_player_deck2": 0x021DF275,
    "hp_player_deck3": 0x021DF2C5,
    # HP, opponent side (+0x61C from yours)
    "hp_opp_active": 0x021DF7F1,
    "hp_opp_deck1": 0x021DF841,
    "hp_opp_deck2": 0x021DF891,
    "hp_opp_deck3": 0x021DF8E1,
    # Deck builder
    "deck_state_flag": 0x020A0C98,
    "deck_leader_bool": 0x020A2289,
    "deck_active_slot": 0x020AFEB4,
    # Code
    "fn_health_calc": 0x020784FC,
}

# Pointer chains: [base, off1, off2...] means read u32 at base, add off1,
# read u32, add off2... final value is the struct base address.
# Verified for offline/training mode (scripts/gdb/README.md, 2026-02-03).
CHAINS = {
    "player": [0x023D2A74, 0x10],
    "opponent": [0x023D2A74, 0x00, 0x10],
}

# Character-struct offsets worth watching (scripts/gdb/README.md).
_STRUCT_OFFSETS = {
    "0x78": (0x78, 1),   # ground/air state (0x22 ground, 0xC0 hitstun)
    "0x88": (0x88, 1),   # positive status id
    "0xA0": (0xA0, 2),   # negative status flags / timer pair 2
    "0x98": (0x98, 2),   # timer pair 1
    "0xD9": (0xD9, 1),   # jump counter
    "0x102": (0x102, 2), # defense timer
}

WATCH_PRESETS = {
    "hp_all": [
        {"name": "hp_all.p1", "addr": ADDRESSES["hp_player_active"], "len": 1},
        {"name": "hp_all.o1", "addr": ADDRESSES["hp_opp_active"], "len": 1},
    ],
    "player_struct": [
        {"name": "player_struct.%s" % k, "chain": CHAINS["player"],
         "offset": off, "len": ln}
        for k, (off, ln) in _STRUCT_OFFSETS.items()
    ],
    "opponent_struct": [
        {"name": "opponent_struct.%s" % k, "chain": CHAINS["opponent"],
         "offset": off, "len": ln}
        for k, (off, ln) in _STRUCT_OFFSETS.items()
    ],
    "battle": [
        {"name": "battle.timer", "addr": ADDRESSES["battle_timer"], "len": 1},
        {"name": "battle.special1", "addr": ADDRESSES["special_meter_1"], "len": 1},
    ],
}


def resolve_watch(name):
    """Expand a preset name into a list of concrete watch specs.

    Raises KeyError for unknown names.
    """
    return [dict(s) for s in WATCH_PRESETS[name]]
