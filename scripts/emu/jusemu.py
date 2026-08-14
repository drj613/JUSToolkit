"""Claude-facing CLI for driving melonDS via agent_bridge.lua.

Usage examples:
  python3 jusemu.py status
  python3 jusemu.py selftest
  python3 jusemu.py peek 0x021DF1D5 1
  python3 jusemu.py peek 0x78 2 --chain player
  python3 jusemu.py state save training
  python3 jusemu.py run plans/example_walk_and_b.json
  python3 jusemu.py screenshot /tmp/shot.png
"""
import argparse, hashlib, json, os, subprocess, sys, time

from jus_addresses import CHAINS
from jus_ipc import IpcClient, BridgeState, DEFAULT_DIR
from jus_plan import validate_plan, validate_watches, plan_to_lua

MAX_DUMP_BYTES = 0x400000  # 4 MB (all of main RAM)

SMOKE_ARGS = {  # minimal valid argv per subcommand, used by tests
    "run": ["p.json"], "peek": ["0x02000000", "1"],
    "poke": ["0x02000000", "ff"], "state": ["save", "s"],
    "dump": ["0x02000000", "0x02000010", "out.bin"],
    "watch": ["set", "w.json"], "screenshot": ["out.png"],
    "status": [], "stop": [], "selftest": [],
}


def build_parser():
    p = argparse.ArgumentParser(prog="jusemu")
    p.add_argument("--ipc-dir", default=DEFAULT_DIR)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run"); r.add_argument("plan")
    pk = sub.add_parser("peek")
    pk.add_argument("addr"); pk.add_argument("length", type=int)
    pk.add_argument("--chain", choices=sorted(CHAINS))
    po = sub.add_parser("poke")
    po.add_argument("addr"); po.add_argument("hexbytes")
    st = sub.add_parser("state")
    st.add_argument("action", choices=["save", "load"])
    st.add_argument("slot")
    d = sub.add_parser("dump")
    d.add_argument("start"); d.add_argument("end"); d.add_argument("outfile")
    w = sub.add_parser("watch")
    w.add_argument("action", choices=["set"]); w.add_argument("spec")
    sc = sub.add_parser("screenshot")
    sc.add_argument("outfile")
    sc.add_argument("--interactive", action="store_true",
                    help="fall back to manual window selection")
    for name in ("status", "stop", "selftest"):
        sub.add_parser(name)
    return p


def die(msg):
    print("error: %s" % msg, file=sys.stderr)
    raise SystemExit(2)


def parse_hexbytes(s):
    if len(s) == 0 or len(s) % 2 != 0 or not all(
            c in "0123456789abcdefABCDEF" for c in s):
        die("hexbytes must be even-length hex, got %r" % s)
    return [int(s[i:i+2], 16) for i in range(0, len(s), 2)]


def validate_dump_range(start, end):
    if end <= start:
        die("dump end must be > start")
    if end - start > MAX_DUMP_BYTES:
        die("dump larger than %d bytes" % MAX_DUMP_BYTES)
    return start, end


def build_peek(addr, length, chain):
    a = int(addr, 0)
    target = ({"chain": CHAINS[chain], "offset": a} if chain
              else {"addr": a})
    validate_watches([{"name": "peek", "len": length} | target])
    return "peek", dict(target, len=length)


def run_timeout(total_frames):
    return total_frames / 30.0 + 15.0  # emulated speed >=30fps + slack


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path):
    with open(path) as f:
        return json.load(f)


def make_run_dir(ipc_dir, plan, cmd_id, epoch):
    rd = os.path.join(ipc_dir, "runs", "%s-%d" % (plan["name"], cmd_id))
    os.makedirs(rd, exist_ok=True)
    with open(os.path.join(rd, "plan.json"), "w") as f:
        json.dump(plan, f, indent=1)
    meta = {"epoch": epoch, "cmd_id": cmd_id, "created": time.time(),
            "plan_sha256": hashlib.sha256(
                json.dumps(plan, sort_keys=True).encode()).hexdigest(),
            "reproducible": False}
    here = os.path.dirname(os.path.abspath(__file__))
    build_info = os.path.join(here, "build_info.json")
    hashes = os.path.join(here, "hashes.json")  # rom/bios/fw/save/config
    if os.path.exists(build_info) and os.path.exists(hashes):
        meta["build"] = _read_json(build_info)
        meta["hashes"] = _read_json(hashes)
        cfg = meta["hashes"].get("melonds_config_path")
        if cfg and os.path.exists(os.path.expanduser(cfg)):
            meta["config_sha256"] = _sha(os.path.expanduser(cfg))
        meta["reproducible"] = True
    if plan.get("load_state"):
        sidecar = os.path.join(ipc_dir, "states",
                               plan["load_state"] + ".meta.json")
        if os.path.exists(sidecar):
            meta["state"] = _read_json(sidecar)
    with open(os.path.join(rd, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return rd


def do_screenshot(outfile, interactive):
    script = ('tell application "System Events" to tell (first process '
              'whose name contains "melonDS") to get id of first window')
    win = subprocess.run(["osascript", "-e", script],
                         capture_output=True, text=True)
    if win.returncode != 0:
        if interactive:
            return subprocess.run(["screencapture", "-w", outfile]).returncode
        print("error: melonDS window not found (permissions? running?); "
              "use --interactive to pick a window manually", file=sys.stderr)
        return 1
    return subprocess.run(
        ["screencapture", "-l", win.stdout.strip(), outfile]).returncode


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "screenshot":
        raise SystemExit(do_screenshot(args.outfile, args.interactive))

    client = IpcClient(args.ipc_dir)

    if args.command == "status":
        state, hb = client.state()
        print(json.dumps({"state": state.value, "heartbeat": hb}, indent=1))
        return
    if args.command == "stop":
        client.request_stop()
        print("stop requested")
        return

    if args.command == "run":
        plan = validate_plan(_read_json(args.plan))
        cid = client.next_id()
        rd = make_run_dir(args.ipc_dir, plan, cid, client.epoch)
        lua_path = os.path.join(rd, "plan.lua")
        with open(lua_path, "w") as f:
            f.write(plan_to_lua(plan))
        client.publish_command(
            "run_plan", {"plan_path": lua_path, "run_dir": rd}, cmd_id=cid)
        try:
            ack = client.wait_ack(cid, timeout=run_timeout(plan["total_frames"]))
        except TimeoutError:
            state, _ = client.state()
            if state == BridgeState.PAUSED:
                print("emulator paused (GDB?) — plan frozen, not failed. "
                      "Resume the emulator, then `jusemu status`.")
                return
            raise
        print(json.dumps(ack, indent=1))
        print("log: %s" % os.path.join(rd, "log.jsonl"))
        return

    if args.command == "peek":
        op, a = build_peek(args.addr, args.length, args.chain)
        timeout = 10.0
    elif args.command == "poke":
        op, a = "poke", {"addr": int(args.addr, 0),
                         "bytes": parse_hexbytes(args.hexbytes)}
        timeout = 10.0
    elif args.command == "state":
        op, a = "state_" + args.action, {"slot": args.slot}
        timeout = 30.0  # save/load are multi-frame state machines
    elif args.command == "dump":
        s, e = validate_dump_range(int(args.start, 0), int(args.end, 0))
        op, a = "dump", {"start": s, "end": e,
                         "outfile": os.path.abspath(args.outfile)}
        timeout = 60.0
    elif args.command == "watch":
        specs = validate_watches(_read_json(args.spec))
        op, a = "set_watches", {"specs": specs}
        timeout = 10.0
    elif args.command == "selftest":
        op, a = "selftest", {}
        timeout = 30.0
    else:
        die("unhandled command %r" % args.command)
    cid = client.publish_command(op, a)
    print(json.dumps(client.wait_ack(cid, timeout=timeout), indent=1))


if __name__ == "__main__":
    main()
