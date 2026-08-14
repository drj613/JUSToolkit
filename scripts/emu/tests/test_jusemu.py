import json, os, tempfile, time, unittest
from unittest import mock
import jusemu


class TestArgBuilding(unittest.TestCase):
    def test_parser_has_all_subcommands(self):
        p = jusemu.build_parser()
        for cmd in ["run", "peek", "poke", "state", "dump", "watch",
                    "screenshot", "status", "stop", "selftest"]:
            args = p.parse_args([cmd] + jusemu.SMOKE_ARGS[cmd])
            self.assertEqual(args.command, cmd)

    def test_peek_with_chain(self):
        op, args = jusemu.build_peek(addr="0x78", length=2, chain="player")
        self.assertEqual(args["chain"], [0x023D2A74, 0x10])
        self.assertEqual(args["offset"], 0x78)

    def test_poke_rejects_odd_hex(self):
        with self.assertRaises(SystemExit):
            jusemu.parse_hexbytes("fff")

    def test_dump_range_validated(self):
        with self.assertRaises(SystemExit):
            jusemu.validate_dump_range(0x02000010, 0x02000000)  # reversed
        with self.assertRaises(SystemExit):
            jusemu.validate_dump_range(0x02000000, 0x02000000 + 0x500000)  # too big

    def test_run_timeout_scales(self):
        self.assertGreater(jusemu.run_timeout(3600), jusemu.run_timeout(60))


class TestMain(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.dir, "runs"))
        self.client = mock.Mock()
        self.client.epoch = "e1"
        self.client.next_id.return_value = 42
        self.client.publish_command.return_value = 42
        self.client.wait_ack.return_value = {"id": 42, "epoch": "e1",
                                             "ok": True, "result": {}}
        patcher = mock.patch("jusemu.IpcClient", return_value=self.client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_run_uses_one_id_everywhere(self):
        plan_path = os.path.join(self.dir, "p.json")
        with open(plan_path, "w") as f:
            json.dump({"name": "t", "segments":
                       [{"from": 0, "to": 1, "buttons": ["A"]}]}, f)
        jusemu.main(["--ipc-dir", self.dir, "run", plan_path])
        # publish_command called with the pre-reserved id
        _, kwargs = self.client.publish_command.call_args
        self.assertEqual(kwargs.get("cmd_id"), 42)
        rd = os.path.join(self.dir, "runs", "t-42")
        self.assertTrue(os.path.isdir(rd))
        with open(os.path.join(rd, "meta.json")) as f:
            meta = json.load(f)
        self.assertEqual(meta["cmd_id"], 42)

    def test_run_meta_marks_missing_hashes(self):
        plan_path = os.path.join(self.dir, "p.json")
        with open(plan_path, "w") as f:
            json.dump({"name": "t", "segments":
                       [{"from": 0, "to": 1, "buttons": ["A"]}]}, f)
        jusemu.main(["--ipc-dir", self.dir, "run", plan_path])
        with open(os.path.join(self.dir, "runs", "t-42", "meta.json")) as f:
            meta = json.load(f)
        self.assertIn("reproducible", meta)  # False when hashes.json absent

    def test_selftest_invokes_bridge(self):
        jusemu.main(["--ipc-dir", self.dir, "selftest"])
        args, kwargs = self.client.publish_command.call_args
        self.assertEqual(args[0], "selftest")

    def test_paused_run_reports_frozen_not_failed(self):
        self.client.wait_ack.side_effect = TimeoutError("x")
        self.client.state.return_value = (jusemu.BridgeState.PAUSED, {})
        plan_path = os.path.join(self.dir, "p.json")
        with open(plan_path, "w") as f:
            json.dump({"name": "t", "segments":
                       [{"from": 0, "to": 1, "buttons": ["A"]}]}, f)
        jusemu.main(["--ipc-dir", self.dir, "run", plan_path])  # must not raise


if __name__ == "__main__":
    unittest.main()
