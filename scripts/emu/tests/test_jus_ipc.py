import json, os, tempfile, time, unittest
from jus_ipc import IpcClient, BridgeState, interpret_heartbeat


def write_hb(d, epoch="epoch1", state="idle", age=0.0):
    tmp = os.path.join(d, "hb.tmp")
    with open(tmp, "w") as f:
        json.dump({"session": epoch, "framecount": 100,
                   "wallclock": time.time() - age, "state": state}, f)
    os.replace(tmp, os.path.join(d, "heartbeat.json"))


class TestHeartbeat(unittest.TestCase):
    def hb(self, age_s, state="idle", alive=True):
        return interpret_heartbeat(
            {"session": "abc", "framecount": 100,
             "wallclock": time.time() - age_s, "state": state},
            emulator_alive=alive)

    def test_fresh_states(self):
        self.assertEqual(self.hb(0.5), BridgeState.IDLE)
        self.assertEqual(self.hb(0.5, "plan_running"), BridgeState.PLAN_RUNNING)
        self.assertEqual(self.hb(0.5, "loading_state"), BridgeState.LOADING_STATE)
        self.assertEqual(self.hb(0.5, "saving_state"), BridgeState.SAVING_STATE)

    def test_stale_alive_is_paused(self):
        self.assertEqual(self.hb(30, alive=True), BridgeState.PAUSED)

    def test_stale_dead_is_dead(self):
        self.assertEqual(self.hb(30, alive=False), BridgeState.DEAD)

    def test_unknown_state_is_dead(self):
        self.assertEqual(self.hb(0.5, "wat"), BridgeState.DEAD)


class TestClientNoBridge(unittest.TestCase):
    def test_status_without_heartbeat_is_dead(self):
        c = IpcClient(tempfile.mkdtemp())
        state, hb = c.state()
        self.assertEqual(state, BridgeState.DEAD)
        self.assertIsNone(hb)

    def test_publish_without_heartbeat_raises(self):
        c = IpcClient(tempfile.mkdtemp())
        with self.assertRaises(RuntimeError):
            c.publish_command("status", {})


class TestClient(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        write_hb(self.dir)
        self.c = IpcClient(self.dir)

    def ack(self, cid, epoch="epoch1", ok=True):
        tmp = os.path.join(self.dir, "ack", "t")
        with open(tmp, "w") as f:
            json.dump({"id": cid, "epoch": epoch, "ok": ok,
                       "result": {"state": "idle"}}, f)
        os.replace(tmp, os.path.join(self.dir, "ack", "%d.json" % cid))

    def test_ids_monotonic_across_instances(self):
        a = self.c.publish_command("status", {})
        self.ack(a)
        self.c.wait_ack(a, timeout=1)
        c2 = IpcClient(self.dir)
        b = c2.publish_command("status", {})
        self.assertGreater(b, a)

    def test_publish_writes_inbox_and_pending(self):
        cid = self.c.publish_command("status", {})
        self.assertTrue(os.path.exists(
            os.path.join(self.dir, "cmd", "inbox.lua")))
        self.assertTrue(os.path.exists(
            os.path.join(self.dir, "cmd", "pending.json")))
        with open(os.path.join(self.dir, "cmd", "inbox.lua")) as f:
            content = f.read()
        self.assertIn('"status"', content)
        self.assertIn("epoch1", content)
        self.assertIn(str(cid), content)

    def test_pending_blocks_even_after_inbox_consumed(self):
        self.c.publish_command("status", {})
        os.remove(os.path.join(self.dir, "cmd", "inbox.lua"))  # bridge ate it
        with self.assertRaises(RuntimeError):
            self.c.publish_command("status", {})

    def test_wait_ack_clears_pending(self):
        cid = self.c.publish_command("status", {})
        self.ack(cid)
        ack = self.c.wait_ack(cid, timeout=1)
        self.assertTrue(ack["ok"])
        self.assertFalse(os.path.exists(
            os.path.join(self.dir, "cmd", "pending.json")))

    def test_ack_with_wrong_epoch_rejected(self):
        cid = self.c.publish_command("status", {})
        self.ack(cid, epoch="old-epoch")
        with self.assertRaises(TimeoutError):
            self.c.wait_ack(cid, timeout=0.3)

    def test_stale_epoch_files_cleaned_on_new_epoch(self):
        cid = self.c.publish_command("status", {})
        # bridge restarts with a new session:
        write_hb(self.dir, epoch="epoch2")
        c2 = IpcClient(self.dir)
        c2.publish_command("status", {})  # must not raise: stale cleaned
        self.assertEqual(c2.epoch, "epoch2")

    def test_wait_ack_timeout_is_indeterminate(self):
        cid = self.c.publish_command("status", {})
        with self.assertRaises(TimeoutError):
            self.c.wait_ack(cid, timeout=0.2)


if __name__ == "__main__":
    unittest.main()
