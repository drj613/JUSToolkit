#!/usr/bin/env python3
"""RAM-dump differential analyzer for live GDB sessions (Phase 1).

Works on raw binary dumps of NDS main RAM (default base 0x02000000,
size 4 MiB), produced in GDB via e.g.:

    dump binary memory pre_hit.bin 0x02000000 0x02400000

Workflow:
  1. Take TWO dumps of the same paused/idle state -> build a churn mask:
       ramdiff.py baseline idle1.bin idle2.bin -o mask.json
  2. Take pre/post dumps around one event (a hit, a jump) -> diff them,
     churn-masked:
       ramdiff.py diff pre_hit.bin post_hit.bin --mask mask.json
  3. Hunt planted values:
       ramdiff.py find post_hit.bin --u16 8 --near 0x023D0000 --radius 0x8000
  4. Walk a pointer chain inside a dump:
       ramdiff.py chain post_hit.bin 0x023D2A74 0x0 0x4

All addresses printed are absolute RAM addresses. Output is deterministic
and capped so it can be pasted into a Claude session verbatim.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

BASE_DEFAULT = 0x02000000
RAM_MIN, RAM_MAX = 0x02000000, 0x02400000


def load(path: str) -> bytes:
    data = Path(path).read_bytes()
    if not data:
        sys.exit(f"error: {path} is empty")
    return data


def q12(v: int) -> str:
    s = v - 0x100000000 if v >= 0x80000000 else v
    return f"{s / 4096.0:.3f}"


def diff_ranges(a: bytes, b: bytes, masked: set[int]) -> list[tuple[int, int]]:
    """Return [start, end) offset ranges where a and b differ, skipping masked offsets."""
    n = min(len(a), len(b))
    ranges: list[tuple[int, int]] = []
    i = 0
    while i < n:
        if a[i] != b[i] and i not in masked:
            j = i
            while j < n and (a[j] != b[j] or (j - i < 4 and j + 1 < n and a[j + 1] != b[j + 1])) and j not in masked:
                j += 1
            ranges.append((i, j))
            i = j
        else:
            i += 1
    return ranges


def cmd_baseline(args: argparse.Namespace) -> int:
    a, b = load(args.dump_a), load(args.dump_b)
    n = min(len(a), len(b))
    churn = [i for i in range(n) if a[i] != b[i]]
    extra = []
    if args.extra:
        c = load(args.extra)
        m = min(n, len(c))
        churn_set = set(churn)
        extra = [i for i in range(m) if b[i] != c[i] and i not in churn_set]
        churn.extend(extra)
    churn.sort()
    out = {"size": n, "base": args.base, "churn_offsets": churn}
    Path(args.output).write_text(json.dumps(out))
    print(f"baseline: {len(churn)} churn bytes / {n} total "
          f"({100.0 * len(churn) / n:.2f}%) -> {args.output}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    a, b = load(args.pre), load(args.post)
    masked: set[int] = set()
    if args.mask:
        masked = set(json.loads(Path(args.mask).read_text())["churn_offsets"])
    ranges = [r for r in diff_ranges(a, b, masked) if r[1] - r[0] >= args.min_run]
    print(f"# {len(ranges)} changed run(s), pre={args.pre} post={args.post}, "
          f"masked={len(masked)} churn bytes")
    for start, end in ranges[: args.limit]:
        addr = args.base + start
        width = end - start
        pre_b, post_b = a[start:end], b[start:end]
        line = f"0x{addr:08X} +{width:<3d} {pre_b.hex()} -> {post_b.hex()}"
        if width in (1, 2, 4):
            fmt = {1: "<B", 2: "<H", 4: "<I"}[width]
            pv = struct.unpack(fmt, pre_b)[0]
            nv = struct.unpack(fmt, post_b)[0]
            line += f"  | u{width*8}: {pv} -> {nv}"
            if width == 4:
                line += f"  | q12: {q12(pv)} -> {q12(nv)}"
            elif width == 2:
                sp = pv - 0x10000 if pv >= 0x8000 else pv
                sn = nv - 0x10000 if nv >= 0x8000 else nv
                line += f"  | s16: {sp} -> {sn}"
        print(line)
    if len(ranges) > args.limit:
        print(f"... {len(ranges) - args.limit} more run(s) suppressed (--limit {args.limit})")
    return 0


def cmd_find(args: argparse.Namespace) -> int:
    data = load(args.dump)
    targets: list[tuple[str, bytes]] = []
    if args.u8 is not None:
        targets.append(("u8", struct.pack("<B", args.u8 & 0xFF)))
    if args.u16 is not None:
        targets.append(("u16", struct.pack("<H", args.u16 & 0xFFFF)))
    if args.u32 is not None:
        targets.append(("u32", struct.pack("<I", args.u32 & 0xFFFFFFFF)))
    if not targets:
        sys.exit("error: give at least one of --u8/--u16/--u32")
    lo, hi = 0, len(data)
    if args.near is not None:
        lo = max(0, args.near - args.base - args.radius)
        hi = min(len(data), args.near - args.base + args.radius)
    hits = 0
    for label, needle in targets:
        i = data.find(needle, lo)
        while i != -1 and i < hi and hits < args.limit:
            if label == "u8" or i % 2 == 0:  # align u16/u32 hits
                print(f"0x{args.base + i:08X}  {label} == {needle.hex()}")
                hits += 1
            i = data.find(needle, i + 1)
    print(f"# {hits} hit(s) shown (limit {args.limit})")
    return 0


def cmd_chain(args: argparse.Namespace) -> int:
    data = load(args.dump)
    addr = args.root
    print(f"root 0x{addr:08X}")
    for off_s in args.offsets:
        off = int(off_s, 0)
        p = addr + off - args.base
        if not (0 <= p <= len(data) - 4):
            print(f"  +0x{off:X}: out of dump range at 0x{addr + off:08X}")
            return 1
        val = struct.unpack("<I", data[p: p + 4])[0]
        note = "" if RAM_MIN <= val < RAM_MAX else "  (NOT a main-RAM pointer)"
        print(f"  [0x{addr:08X}+0x{off:X}] = 0x{val:08X}{note}")
        addr = val
    return 0


def cmd_selftest(_args: argparse.Namespace) -> int:
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        base = bytearray(0x1000)
        idle2 = bytearray(base)
        idle2[0x10] ^= 0xFF          # churn byte
        post = bytearray(base)
        post[0x10] ^= 0xAA           # churn (must be masked out)
        post[0x100:0x102] = struct.pack("<H", 8)      # planted u16
        post[0x200:0x204] = struct.pack("<I", 0x2001)  # planted q12 ~2.0 (first byte nonzero)
        (t / "a.bin").write_bytes(base)
        (t / "b.bin").write_bytes(idle2)
        (t / "post.bin").write_bytes(post)
        ns = argparse.Namespace(dump_a=str(t / "a.bin"), dump_b=str(t / "b.bin"),
                                extra=None, output=str(t / "mask.json"), base=BASE_DEFAULT)
        cmd_baseline(ns)
        mask = json.loads((t / "mask.json").read_text())
        ok &= mask["churn_offsets"] == [0x10]
        print(f"[{'PASS' if ok else 'FAIL'}] baseline masks exactly the churn byte")
        masked = set(mask["churn_offsets"])
        ranges = diff_ranges(base, post, masked)
        starts = [r[0] for r in ranges]
        good = 0x100 in starts and 0x200 in starts and 0x10 not in starts
        ok &= good
        print(f"[{'PASS' if good else 'FAIL'}] diff finds planted values, skips churn")
        ptr = bytearray(0x1000)
        ptr[0x0:0x4] = struct.pack("<I", BASE_DEFAULT + 0x500)
        ptr[0x500:0x504] = struct.pack("<I", 0x1234)
        (t / "c.bin").write_bytes(ptr)
        ns2 = argparse.Namespace(dump=str(t / "c.bin"), root=BASE_DEFAULT,
                                 offsets=["0x0"], base=BASE_DEFAULT)
        rc = cmd_chain(ns2)
        ok &= rc == 0
        print(f"[{'PASS' if rc == 0 else 'FAIL'}] chain walk resolves in-dump pointer")
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", type=lambda s: int(s, 0), default=BASE_DEFAULT,
                   help="RAM address of dump byte 0 (default 0x02000000)")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("baseline", help="build churn mask from 2-3 idle dumps")
    b.add_argument("dump_a"); b.add_argument("dump_b")
    b.add_argument("--extra", help="optional third idle dump to widen the mask")
    b.add_argument("-o", "--output", default="churn_mask.json")
    b.set_defaults(fn=cmd_baseline)

    d = sub.add_parser("diff", help="diff pre/post dumps, churn-masked")
    d.add_argument("pre"); d.add_argument("post")
    d.add_argument("--mask", help="churn mask from `baseline`")
    d.add_argument("--min-run", type=int, default=1)
    d.add_argument("--limit", type=int, default=200)
    d.set_defaults(fn=cmd_diff)

    f = sub.add_parser("find", help="search a dump for planted known values")
    f.add_argument("dump")
    f.add_argument("--u8", type=lambda s: int(s, 0))
    f.add_argument("--u16", type=lambda s: int(s, 0))
    f.add_argument("--u32", type=lambda s: int(s, 0))
    f.add_argument("--near", type=lambda s: int(s, 0),
                   help="center address to restrict the search window")
    f.add_argument("--radius", type=lambda s: int(s, 0), default=0x10000)
    f.add_argument("--limit", type=int, default=100)
    f.set_defaults(fn=cmd_find)

    c = sub.add_parser("chain", help="walk a pointer chain inside a dump")
    c.add_argument("dump")
    c.add_argument("root", type=lambda s: int(s, 0))
    c.add_argument("offsets", nargs="+", help="hex offsets, dereferenced left to right")
    c.set_defaults(fn=cmd_chain)

    s = sub.add_parser("selftest", help="run built-in synthetic-fixture tests")
    s.set_defaults(fn=cmd_selftest)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
