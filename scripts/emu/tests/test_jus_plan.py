import unittest
from jus_plan import (validate_plan, validate_watches, plan_to_lua,
                      lua_literal, PlanError)

GOOD = {
    "name": "walk_and_b",
    "load_state": "training",
    "segments": [
        {"from": 0, "to": 20, "buttons": ["RIGHT"]},
        {"from": 21, "to": 23, "buttons": ["B"]},
    ],
    "tail_frames": 120,
    "watches": ["hp_all"],
}


class TestValidatePlan(unittest.TestCase):
    def test_good_plan_passes(self):
        p = validate_plan(GOOD)
        self.assertEqual(p["total_frames"], 24 + 120)

    def test_overlapping_segments_rejected(self):
        bad = dict(GOOD, segments=[
            {"from": 0, "to": 10, "buttons": ["A"]},
            {"from": 10, "to": 20, "buttons": ["B"]},
        ])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_unsorted_segments_rejected(self):
        bad = dict(GOOD, segments=[
            {"from": 21, "to": 23, "buttons": ["B"]},
            {"from": 0, "to": 20, "buttons": ["RIGHT"]},
        ])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_negative_frames_rejected(self):
        for seg in ({"from": -1, "to": 3, "buttons": ["A"]},
                    {"from": 0, "to": -3, "buttons": ["A"]}):
            with self.assertRaises(PlanError):
                validate_plan(dict(GOOD, segments=[seg]))

    def test_negative_tail_rejected(self):
        with self.assertRaises(PlanError):
            validate_plan(dict(GOOD, tail_frames=-5))

    def test_reversed_range_rejected(self):
        bad = dict(GOOD, segments=[{"from": 5, "to": 3, "buttons": ["A"]}])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_bad_button_rejected(self):
        bad = dict(GOOD, segments=[{"from": 0, "to": 1, "buttons": ["Z"]}])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_opposite_dpad_rejected(self):
        bad = dict(GOOD, segments=[
            {"from": 0, "to": 1, "buttons": ["LEFT", "RIGHT"]}])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_touch_segment_ok(self):
        p = dict(GOOD, segments=[
            {"from": 0, "to": 5, "touch": {"x": 128, "y": 96}}])
        validate_plan(p)  # should not raise

    def test_touch_out_of_bounds_rejected(self):
        for xy in ({"x": 256, "y": 96}, {"x": -1, "y": 0}, {"x": 0, "y": 192}):
            with self.assertRaises(PlanError):
                validate_plan(dict(GOOD, segments=[
                    {"from": 0, "to": 1, "touch": xy}]))


class TestValidateWatches(unittest.TestCase):
    def test_limit_32_watches(self):
        specs = [{"name": "w%d" % i, "addr": 0x02000000 + i, "len": 1}
                 for i in range(32)]
        validate_watches(specs)  # exactly at limit: ok
        specs.append({"name": "w32", "addr": 0x02000100, "len": 1})
        with self.assertRaises(PlanError):
            validate_watches(specs)

    def test_byte_budget_512(self):
        validate_watches([{"name": "b", "addr": 0x02000000, "len": 512}])
        with self.assertRaises(PlanError):
            validate_watches([{"name": "b", "addr": 0x02000000, "len": 513}])

    def test_read_crossing_ram_boundary_rejected(self):
        with self.assertRaises(PlanError):
            validate_watches([{"name": "x", "addr": 0x023FFFFC, "len": 8}])

    def test_duplicate_names_rejected(self):
        with self.assertRaises(PlanError):
            validate_watches([
                {"name": "a", "addr": 0x02000000, "len": 1},
                {"name": "a", "addr": 0x02000004, "len": 1}])

    def test_chain_depth_limit(self):
        with self.assertRaises(PlanError):
            validate_watches([{"name": "c", "len": 1, "offset": 0,
                               "chain": [0x02000000, 0, 0, 0, 0]}])


class TestLuaEmit(unittest.TestCase):
    def test_emits_loadable_lua_table(self):
        lua = plan_to_lua(validate_plan(GOOD))
        self.assertTrue(lua.startswith("return {"))
        self.assertIn('walk_and_b', lua)
        self.assertIn("Right", lua)  # RIGHT normalized to fork casing

    def test_control_chars_escaped(self):
        self.assertEqual(lua_literal("a\nb"), '"a\\nb"')
        self.assertEqual(lua_literal('q"\\'), '"q\\"\\\\"')
        self.assertEqual(lua_literal("x\r\ty"), '"x\\r\\ty"')

    def test_watch_preset_expanded(self):
        lua = plan_to_lua(validate_plan(GOOD))
        self.assertIn("hp_all.p1", lua)
        self.assertIn("0x21DF1D5".lower(), lua.lower())


if __name__ == "__main__":
    unittest.main()
