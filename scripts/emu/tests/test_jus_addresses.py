import unittest
from jus_addresses import ADDRESSES, CHAINS, WATCH_PRESETS, resolve_watch


class TestAddresses(unittest.TestCase):
    def test_known_hp_address(self):
        self.assertEqual(ADDRESSES["hp_player_active"], 0x021DF1D5)

    def test_player_chain(self):
        self.assertEqual(CHAINS["player"], [0x023D2A74, 0x10])

    def test_opponent_chain(self):
        self.assertEqual(CHAINS["opponent"], [0x023D2A74, 0x00, 0x10])

    def test_preset_expands_to_specs(self):
        specs = resolve_watch("hp_all")
        names = [s["name"] for s in specs]
        self.assertIn("hp_all.p1", names)
        spec = next(s for s in specs if s["name"] == "hp_all.p1")
        self.assertEqual(spec["addr"], 0x021DF1D5)
        self.assertEqual(spec["len"], 1)

    def test_struct_preset_uses_chain(self):
        specs = resolve_watch("player_struct")
        spec = next(s for s in specs if s["name"] == "player_struct.0x78")
        self.assertEqual(spec["chain"], [0x023D2A74, 0x10])
        self.assertEqual(spec["offset"], 0x78)

    def test_no_duplicate_names_within_preset(self):
        for preset in WATCH_PRESETS:
            names = [s["name"] for s in resolve_watch(preset)]
            self.assertEqual(len(names), len(set(names)), preset)

    def test_unknown_preset_raises(self):
        with self.assertRaises(KeyError):
            resolve_watch("nonsense")


if __name__ == "__main__":
    unittest.main()
