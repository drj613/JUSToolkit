#!/usr/bin/env python3
"""query.py - the query CLI for the FTC (Jump Ultimate Stars) NDS static
reverse-engineering toolchain.

This is the ONLY interface downstream analysis agents use to read the
pre-built analysis databases. Its --help text is pasted verbatim into agent
prompts, so every subcommand's help includes a concise description plus a
worked example against a real, verified anchor address.

It is a pure *reader*: it never writes to jus_files, and it never re-runs the
disassembler. It lazily loads three read-only inputs (only what a given
subcommand actually needs, so startup stays fast):

  jus_files/analysis/functions.json        - via rom_loader-style JSON load
  jus_files/analysis/xrefs.json            - literal_loads / imm_offsets / branches
  jus_files/analysis/disasm/<prov>.txt     - verbatim per-region listings

...plus rom_loader.load_memory_map() (reused, not reimplemented) whenever a
subcommand needs to resolve an address to a specific region (arm9 or ovN),
including detecting the N-way overlaps documented there: ov0-ov9 all load at
0x0214CD20, ov10/ov11 share 0x02172A60, ov12/ov13 share 0x021AC1C0.

Design contract (read this before changing output formatting):
  - Every line of *data* output is self-describing: it names its own
    provenance so an agent (or a human) can quote a single line as evidence
    without needing the surrounding context.
  - Sort orders are always stable/deterministic (never dict/set iteration
    order) so re-running the exact same query string-matches the exact same
    output byte-for-byte -- this is required because a verifier agent
    re-runs the query to confirm quoted evidence.
  - Listing subcommands (callers, callees, xrefs-to, search-imm,
    search-op-imm, pool-values, strings) print a leading "# N ..."
    summary/count line, then N data lines (lines never start with "#", so
    grepping data lines is `grep -v '^#'`).
  - `disasm` is the one exception: its stdout is the verbatim listing-file
    text with **no** added header (any resolution context goes to stderr),
    because its whole job is byte-for-byte passthrough of already-provenance-
    scoped lines.
  - Resolution errors (unknown address, ambiguous overlay, unknown region)
    are printed to stderr and cause a non-zero exit; stdout is reserved for
    successful results.

CLI:
    query.py func <addr> [--overlay N]
    query.py callers <addr> [--overlay N]
    query.py callees <addr> [--overlay N]
    query.py xrefs-to <addr>
    query.py search-imm <val> [--all]
    query.py search-op-imm <val> [--mnemonic M] [--all]
    query.py disasm <addr> <n> [--overlay N]
    query.py strings <region> [--all]
    query.py pool-values <addr-lo> <addr-hi>
    query.py --selftest
"""

from __future__ import annotations

import argparse
import bisect
import io
import json
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rom_loader import MemoryMap, load_memory_map  # noqa: E402

# --------------------------------------------------------------------------
# Paths (mirrors disasm_db.py / xref_db.py layout conventions)
# --------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = _REPO_ROOT / "jus_files" / "analysis"
FUNCTIONS_JSON = ANALYSIS_DIR / "functions.json"
XREFS_JSON = ANALYSIS_DIR / "xrefs.json"
DISASM_DIR = ANALYSIS_DIR / "disasm"

# Output caps (spec mandates the search-imm cap; the same pattern is applied
# to `strings` since raw byte-run extraction over a whole region can produce
# thousands of hits and an agent-facing CLI should not dump unbounded text).
SEARCH_IMM_CAP = 200
STRINGS_CAP = 300

# Real, verified anchors used in --help worked examples and --selftest.
_ANCHOR_DAMAGE_FUNC = 0x020784E4  # push {r4, lr} prologue, GDB-proven
_ANCHOR_DAMAGE_INNER = 0x020784FC  # ldrsh inside the function above
_ANCHOR_COLLISION_TABLE = 0x020924B0  # collision_file_pointer_table (arm9)
_ANCHOR_OVERLAP_BASE = 0x0214CD20  # ov0-ov9 shared RAM base
_ANCHOR_MOV_IMM = 0x02078520  # arm9 "mov r0, #0x3c", GDB-proven present

# --------------------------------------------------------------------------
# Address / immediate parsing
# --------------------------------------------------------------------------


def parse_int(s: str) -> int:
    """Parse '0x1A2B', '-0x4', '1234', or '-386' -- hex (0x-prefixed) or
    plain decimal, optionally negative. Raises ValueError on anything else.
    """
    s = s.strip()
    if not s:
        raise ValueError("empty value")
    neg = s.startswith("-")
    body = s[1:] if neg else s
    if body[:2].lower() == "0x":
        v = int(body, 16)
    else:
        v = int(body, 10)
    return -v if neg else v


def _addr_type(s: str) -> int:
    try:
        return parse_int(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid address {s!r}: expected 0x-hex or decimal"
        ) from exc


def _imm_type(s: str) -> int:
    try:
        return parse_int(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid immediate {s!r}: expected 0x-hex or decimal (may be negative)"
        ) from exc


def _count_type(s: str) -> int:
    try:
        v = int(s, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid count {s!r}: expected a positive integer") from exc
    if v <= 0:
        raise argparse.ArgumentTypeError(f"count must be > 0, got {v}")
    return v


def normalize_overlay(spec: str) -> str:
    """Turn '3', 'ov3', or 'OV3' into the canonical provenance name 'ov3'."""
    s = spec.strip().lower()
    if s.startswith("ov"):
        s = s[2:]
    if not s or not s.lstrip("-").isdigit():
        raise ValueError(
            f"invalid --overlay value {spec!r}; expected an integer or 'ovN' (e.g. '3' or 'ov3')"
        )
    return f"ov{int(s)}"


# --------------------------------------------------------------------------
# Lazy-loaded data sources
# --------------------------------------------------------------------------

_FUNCTIONS_CACHE: list[dict] | None = None
_XREFS_CACHE: dict | None = None
_MM_CACHE: MemoryMap | None = None


def _load_functions() -> list[dict]:
    global _FUNCTIONS_CACHE
    if _FUNCTIONS_CACHE is None:
        if not FUNCTIONS_JSON.exists():
            raise FileNotFoundError(
                f"{FUNCTIONS_JSON} not found -- run disasm_db.py first to build it"
            )
        with open(FUNCTIONS_JSON, "r", encoding="utf-8") as f:
            doc = json.load(f)
        _FUNCTIONS_CACHE = doc["functions"]
    return _FUNCTIONS_CACHE


def _load_xrefs() -> dict:
    global _XREFS_CACHE
    if _XREFS_CACHE is None:
        if not XREFS_JSON.exists():
            raise FileNotFoundError(
                f"{XREFS_JSON} not found -- run xref_db.py first to build it"
            )
        with open(XREFS_JSON, "r", encoding="utf-8") as f:
            _XREFS_CACHE = json.load(f)
    return _XREFS_CACHE


def _load_memory_map() -> MemoryMap:
    global _MM_CACHE
    if _MM_CACHE is None:
        _MM_CACHE = load_memory_map()
    return _MM_CACHE


# --------------------------------------------------------------------------
# Function resolution ("the function containing addr", with --overlay)
# --------------------------------------------------------------------------


class AddressResolutionError(Exception):
    """Carries enough context to print a clean, actionable error message."""

    def __init__(self, kind: str, candidates: list[dict], addr: int, want: str | None = None):
        self.kind = kind  # "not_found" | "ambiguous" | "overlay_empty" | "bad_overlay"
        self.candidates = candidates
        self.addr = addr
        self.want = want
        super().__init__(kind)


def _functions_containing(functions: list[dict], addr: int) -> list[dict]:
    hits = []
    for f in functions:
        f_addr = parse_int(f["addr"])
        if f_addr <= addr < f_addr + f["size"]:
            hits.append(f)
    return hits


def resolve_function(addr: int, overlay: str | None = None) -> dict:
    """Return the single function dict whose [addr, addr+size) contains
    `addr`. Raises AddressResolutionError if zero, or more than one
    (without --overlay), match.
    """
    functions = _load_functions()
    hits = _functions_containing(functions, addr)

    if overlay is not None:
        try:
            want = normalize_overlay(overlay)
        except ValueError as exc:
            raise AddressResolutionError("bad_overlay", [], addr, want=str(exc)) from exc
        filtered = [f for f in hits if f["provenance"] == want]
        if not filtered:
            raise AddressResolutionError("overlay_empty", hits, addr, want=want)
        return filtered[0]

    if not hits:
        raise AddressResolutionError("not_found", [], addr)
    if len(hits) > 1:
        raise AddressResolutionError("ambiguous", hits, addr)
    return hits[0]


def format_func_line(f: dict) -> str:
    addr = parse_int(f["addr"])
    return (
        f"0x{addr:08X} ({f['provenance']}): size={f['size']} mode={f['mode']} "
        f"callees={len(f.get('callees', []))} callers={len(f.get('callers', []))}"
    )


def print_resolution_error(e: AddressResolutionError) -> None:
    if e.kind == "bad_overlay":
        print(f"error: {e.want}", file=sys.stderr)
        return

    if e.kind == "not_found":
        print(
            f"error: no known function contains address 0x{e.addr:08X} "
            f"(it may be inside a data table, literal pool, or an address not "
            f"covered by any mapped region -- functions.json only knows about "
            f"detected code)",
            file=sys.stderr,
        )
        try:
            mm = _load_memory_map()
            cands = mm.candidates(e.addr)
            if cands:
                names = ", ".join(sorted(r.name for r in cands))
                print(f"  note: address IS mapped by region(s): {names}", file=sys.stderr)
            else:
                print("  note: address is not mapped by any region either.", file=sys.stderr)
        except Exception:  # noqa: BLE001 - this is best-effort context, never fatal
            pass
        return

    if e.kind == "overlay_empty":
        print(
            f"error: overlay {e.want!r} has no function containing address 0x{e.addr:08X}",
            file=sys.stderr,
        )
        if e.candidates:
            print(
                "  address IS contained in a function in these other provenance(s) instead:",
                file=sys.stderr,
            )
            for f in sorted(e.candidates, key=lambda f: f["provenance"]):
                print(f"    {format_func_line(f)}", file=sys.stderr)
        else:
            print("  address is not contained in any known function in any provenance.", file=sys.stderr)
        return

    if e.kind == "ambiguous":
        print(
            f"error: address 0x{e.addr:08X} is ambiguous across {len(e.candidates)} "
            f"overlapping-region functions; pass --overlay ovN (or --overlay N) to "
            f"disambiguate. Candidates:",
            file=sys.stderr,
        )
        for f in sorted(e.candidates, key=lambda f: f["provenance"]):
            print(f"  {format_func_line(f)}", file=sys.stderr)
        return


# --------------------------------------------------------------------------
# func
# --------------------------------------------------------------------------


def cmd_func(args: argparse.Namespace) -> int:
    try:
        f = resolve_function(args.addr, args.overlay)
    except AddressResolutionError as e:
        print_resolution_error(e)
        return 2
    print(format_func_line(f))
    return 0


# --------------------------------------------------------------------------
# callers
# --------------------------------------------------------------------------


def cmd_callers(args: argparse.Namespace) -> int:
    try:
        f = resolve_function(args.addr, args.overlay)
    except AddressResolutionError as e:
        print_resolution_error(e)
        return 2

    prov = f["provenance"]
    f_addr = parse_int(f["addr"])

    rows: list[tuple[int, str, str]] = []
    for c in f.get("callers", []):
        c_addr = parse_int(c)
        rows.append(
            (
                c_addr,
                prov,
                f"0x{c_addr:08X} ({prov}) [functions.json: caller function, same-region]",
            )
        )

    xrefs = _load_xrefs()
    for b in xrefs["branches"]:
        if b["kind"] not in ("bl", "blx"):
            continue
        if parse_int(b["target"]) != f_addr:
            continue
        insn_addr = parse_int(b["insn_addr"])
        rows.append(
            (
                insn_addr,
                b["provenance"],
                f"0x{insn_addr:08X} ({b['provenance']}) [xrefs: {b['kind']} call site]",
            )
        )

    rows.sort(key=lambda t: (t[0], t[1]))
    print(f"# {len(rows)} caller reference(s) for function 0x{f_addr:08X} ({prov})")
    for _addr, _prov, text in rows:
        print(text)
    return 0


# --------------------------------------------------------------------------
# callees
# --------------------------------------------------------------------------


def cmd_callees(args: argparse.Namespace) -> int:
    try:
        f = resolve_function(args.addr, args.overlay)
    except AddressResolutionError as e:
        print_resolution_error(e)
        return 2

    prov = f["provenance"]
    f_addr = parse_int(f["addr"])
    mm = _load_memory_map()

    # Note: functions.json's "unmapped_callees" is a *subset flag* of
    # "callees" (disasm_db.py: "Callees whose target is not covered by any
    # region ... are additionally listed ... under unmapped_callees"), not a
    # separate list -- every address in it already appears in "callees" too.
    # Resolving each callee's provenance via the memory map directly (below)
    # naturally reproduces that same "unmapped" verdict, so there is nothing
    # extra to merge in here.
    rows: list[tuple[int, str]] = []
    for c in f.get("callees", []):
        c_addr = parse_int(c)
        cands = mm.candidates(c_addr)
        resolved = ", ".join(sorted(r.name for r in cands)) if cands else "unmapped"
        rows.append((c_addr, f"0x{c_addr:08X} ({resolved})"))

    rows.sort(key=lambda t: t[0])
    print(f"# {len(rows)} callee reference(s) for function 0x{f_addr:08X} ({prov})")
    for _addr, text in rows:
        print(text)
    return 0


# --------------------------------------------------------------------------
# xrefs-to
# --------------------------------------------------------------------------


def cmd_xrefs_to(args: argparse.Namespace) -> int:
    addr = args.addr
    xrefs = _load_xrefs()

    lit_hits = [r for r in xrefs["literal_loads"] if parse_int(r["value"]) == addr]
    br_hits = [r for r in xrefs["branches"] if parse_int(r["target"]) == addr]
    lit_hits.sort(key=lambda r: (parse_int(r["insn_addr"]), r["provenance"]))
    br_hits.sort(key=lambda r: (parse_int(r["insn_addr"]), r["provenance"]))

    functions = _load_functions()
    start_funcs = [f for f in functions if parse_int(f["addr"]) == addr]
    start_funcs.sort(key=lambda f: f["provenance"])

    caller_rows: list[tuple[int, str, str]] = []
    for f in start_funcs:
        for c in f.get("callers", []):
            c_addr = parse_int(c)
            caller_rows.append((c_addr, f["provenance"], c))
    caller_rows.sort(key=lambda t: (t[0], t[1]))

    total = len(lit_hits) + len(br_hits) + len(caller_rows)
    suffix = "" if start_funcs else " (address is not a known function start)"
    print(
        f"# {total} reference(s) to 0x{addr:08X}: {len(lit_hits)} literal_load, "
        f"{len(br_hits)} branch, {len(caller_rows)} functions.json-caller{suffix}"
    )
    for r in lit_hits:
        print(
            f"literal_load 0x{parse_int(r['insn_addr']):08X} ({r['provenance']}, {r['mode']}) "
            f"pool=0x{parse_int(r['pool_addr']):08X} value=0x{addr:08X}"
        )
    for r in br_hits:
        print(f"branch 0x{parse_int(r['insn_addr']):08X} ({r['provenance']}) {r['kind']} -> 0x{addr:08X}")
    for c_addr, prov, _raw in caller_rows:
        print(
            f"caller_function 0x{c_addr:08X} ({prov}) [functions.json: calls function 0x{addr:08X}]"
        )
    return 0


# --------------------------------------------------------------------------
# search-imm
# --------------------------------------------------------------------------


def cmd_search_imm(args: argparse.Namespace) -> int:
    val = args.val
    xrefs = _load_xrefs()
    hits = [r for r in xrefs["imm_offsets"] if r["imm"] == val]
    hits.sort(key=lambda r: (parse_int(r["insn_addr"]), r["provenance"]))

    total = len(hits)
    shown = hits if args.all else hits[:SEARCH_IMM_CAP]
    capped = (not args.all) and total > SEARCH_IMM_CAP
    print(
        f"# {total} hit(s) for imm == {val}"
        + (f" (showing first {SEARCH_IMM_CAP}, use --all for the rest)" if capped else "")
    )
    for r in shown:
        addr_i = parse_int(r["insn_addr"])
        imm_fmt = f"{r['imm']:#x}"
        print(f"0x{addr_i:08X} ({r['provenance']}) {r['mnemonic']} [{r['base_reg']}, #{imm_fmt}]")
    if capped:
        print(f"... {total - SEARCH_IMM_CAP} more (use --all)")
    return 0


# --------------------------------------------------------------------------
# search-op-imm
# --------------------------------------------------------------------------

# ARM condition-code mnemonic suffixes (same 17 suffixes xref_db.py's
# _COND_CODES tracks; duplicated here, not imported, to keep this reader CLI
# free of any dependency on the builder modules).
_COND_CODES = {
    "eq", "ne", "cs", "hs", "cc", "lo", "mi", "pl",
    "vs", "vc", "hi", "ls", "ge", "lt", "gt", "le", "al",
}

# The 12 data-processing mnemonics this subcommand searches, any condition
# code. The eight in _DP_BASES_WITH_S also have an optional flag-setting "S"
# infix (mnemonic order is always <base><S><cond>, e.g. "addseq"); the four
# compare/test mnemonics in _DP_BASES_NO_S always implicitly set flags and
# have no separate "S" form.
_DP_BASES_NO_S = ("cmp", "cmn", "tst", "teq")
_DP_BASES_WITH_S = ("mov", "mvn", "and", "orr", "eor", "add", "sub", "rsb")
_DP_MNEMONICS = _DP_BASES_NO_S + _DP_BASES_WITH_S

# A disasm listing line: "0xAAAAAAAA: <hexbytes>  <mnemonic> <operands>".
_DP_LINE_RE = re.compile(r"^0x([0-9A-F]{8}): [0-9a-f]+  (\S+)\s+(.*)$")
# A final comma-separated operand that is a bare immediate, e.g. "#0x3c" or
# "#0" -- deliberately excludes shifted-register operands like "lsl #2"
# (whose last comma-field is "lsl #2", not just "#2") so register-shifted
# instructions never masquerade as immediate ones.
_DP_IMM_OPERAND_RE = re.compile(r"^#(-?(?:0x[0-9a-fA-F]+|[0-9]+))$")


def _normalize_dp_mnem(mnem: str) -> str | None:
    """Strip an ARM condition-code suffix (and, for the eight mnemonics that
    support one, an optional flag-setting "S" infix) from a data-processing
    mnemonic and return one of the 12 canonical bases in _DP_MNEMONICS, or
    None if `mnem` isn't one of them. Exact-length-matched (never a bare
    prefix test) so lookalikes such as "movw"/"movt" (Thumb-2 wide-immediate
    moves -- a different instruction family, out of scope here) never match.
    """
    for base in _DP_BASES_NO_S:
        if mnem == base:
            return base
        if mnem.startswith(base) and mnem[len(base):] in _COND_CODES:
            return base
    for base in _DP_BASES_WITH_S:
        if not mnem.startswith(base):
            continue
        rest = mnem[len(base):]
        if rest == "" or rest in _COND_CODES:
            return base
        if rest.startswith("s") and (rest[1:] == "" or rest[1:] in _COND_CODES):
            return base
    return None


def _iter_disasm_files() -> list[Path]:
    """Every per-region listing file under DISASM_DIR, sorted by provenance
    name (plain lexicographic -- the same convention used everywhere else in
    this file that sorts a set of provenance names, e.g. print_resolution_error).
    """
    return sorted(DISASM_DIR.glob("*.txt"), key=lambda p: p.stem)


def cmd_search_op_imm(args: argparse.Namespace) -> int:
    val = args.val

    want_mnem = None
    if args.mnemonic is not None:
        want_mnem = args.mnemonic.strip().lower()
        if want_mnem not in _DP_MNEMONICS:
            print(
                f"error: unknown --mnemonic {args.mnemonic!r}; expected one of: "
                + ", ".join(_DP_MNEMONICS),
                file=sys.stderr,
            )
            return 2

    if not DISASM_DIR.is_dir():
        print(
            f"error: {DISASM_DIR} not found -- run disasm_db.py first to build it",
            file=sys.stderr,
        )
        return 2

    hits: list[tuple[str, int, str]] = []  # (provenance, addr, formatted line)
    for path in _iter_disasm_files():
        prov = path.stem
        for line in path.read_text().splitlines():
            m = _DP_LINE_RE.match(line)
            if not m:
                continue
            addr_hex, mnem_raw, rest = m.groups()
            base_mnem = _normalize_dp_mnem(mnem_raw.lower())
            if base_mnem is None:
                continue
            if want_mnem is not None and base_mnem != want_mnem:
                continue
            last_op = rest.rsplit(",", 1)[-1].strip()
            om = _DP_IMM_OPERAND_RE.match(last_op)
            if om is None:
                continue
            if parse_int(om.group(1)) != val:
                continue
            addr = int(addr_hex, 16)
            hits.append((prov, addr, f"0x{addr:08X} ({prov}) {mnem_raw} {rest}"))

    hits.sort(key=lambda t: (t[0], t[1]))

    total = len(hits)
    shown = hits if args.all else hits[:SEARCH_IMM_CAP]
    capped = (not args.all) and total > SEARCH_IMM_CAP
    mnem_note = f" mnemonic=={want_mnem}" if want_mnem else ""
    print(
        f"# {total} hit(s) for op-imm == {val}{mnem_note}"
        + (f" (showing first {SEARCH_IMM_CAP}, use --all for the rest)" if capped else "")
    )
    for _prov, _addr, text in shown:
        print(text)
    if capped:
        print(f"... {total - SEARCH_IMM_CAP} more (use --all)")
    return 0


# --------------------------------------------------------------------------
# disasm
# --------------------------------------------------------------------------


def cmd_disasm(args: argparse.Namespace) -> int:
    addr = args.addr
    n = args.n
    mm = _load_memory_map()

    if args.overlay is not None:
        try:
            want = normalize_overlay(args.overlay)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        region = next((r for r in mm.regions if r.name == want), None)
        if region is None:
            print(
                f"error: unknown overlay {args.overlay!r} (expected e.g. --overlay ov1 or --overlay 1)",
                file=sys.stderr,
            )
            return 2
        if not region.contains(addr):
            print(
                f"error: address 0x{addr:08X} is not within {region.name} "
                f"(0x{region.base:08X}-0x{region.end - 1:08X})",
                file=sys.stderr,
            )
            return 2
    else:
        cands = mm.candidates(addr)
        if not cands:
            print(f"error: address 0x{addr:08X} is not mapped by any region", file=sys.stderr)
            return 2
        if len(cands) > 1:
            names = ", ".join(sorted(r.name for r in cands))
            print(
                f"error: address 0x{addr:08X} is ambiguous across {len(cands)} "
                f"overlapping regions ({names}); pass --overlay ovN to disambiguate.",
                file=sys.stderr,
            )
            print("  candidates:", file=sys.stderr)
            for r in sorted(cands, key=lambda r: r.name):
                print(f"    {r.name} base=0x{r.base:08X} end=0x{r.end:08X}", file=sys.stderr)
            return 2
        region = cands[0]

    path = DISASM_DIR / f"{region.name}.txt"
    if not path.exists():
        print(f"error: no disassembly listing for {region.name} at {path}", file=sys.stderr)
        return 2

    lines = path.read_text().splitlines()
    addrs = [int(line[2:10], 16) for line in lines]
    i = bisect.bisect_left(addrs, addr)
    if i >= len(lines) or addrs[i] != addr:
        print(
            f"error: address 0x{addr:08X} has no disassembly record in {region.name}.txt "
            f"(not aligned to a decoded instruction/data-word start)",
            file=sys.stderr,
        )
        return 2

    print(
        f"# resolved region={region.name} ({'--overlay ' + region.name if args.overlay else 'unambiguous'})",
        file=sys.stderr,
    )
    chunk = lines[i : i + n]
    for line in chunk:
        print(line)
    if len(chunk) < n:
        print(
            f"# warning: only {len(chunk)} of {n} requested lines available "
            f"(reached end of {region.name}.txt)",
            file=sys.stderr,
        )
    return 0


# --------------------------------------------------------------------------
# strings
# --------------------------------------------------------------------------


def _sjis_lead(b: int) -> bool:
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC


def _valid_sjis_pair(b0: int, b1: int) -> bool:
    try:
        s = bytes((b0, b1)).decode("shift_jis")
    except UnicodeDecodeError:
        return False
    return len(s) == 1 and s.isprintable()


def _extract_strings(data: bytes, base: int, min_len: int = 6) -> list[tuple[int, str]]:
    """Scan `data` for runs (>= min_len bytes) of printable ASCII (0x20-0x7E)
    and/or valid Shift-JIS double-byte characters, greedily, non-overlapping.
    This is a byte-heuristic (like the classic Unix `strings` tool extended
    for Shift-JIS) -- it WILL include false positives where machine code
    bytes happen to form a valid-looking run; that is an inherent limitation
    of scanning raw code+data for text, not something this tool can fully
    eliminate.
    """
    n = len(data)
    i = 0
    out: list[tuple[int, str]] = []
    while i < n:
        start = i
        j = i
        while j < n:
            b = data[j]
            if 0x20 <= b <= 0x7E:
                j += 1
                continue
            if j + 1 < n and _sjis_lead(b) and _valid_sjis_pair(b, data[j + 1]):
                j += 2
                continue
            break
        run_len = j - start
        if run_len >= min_len:
            out.append((base + start, data[start:j].decode("shift_jis", errors="replace")))
            i = j
        else:
            i = j + 1 if j == start else j
    return out


def cmd_strings(args: argparse.Namespace) -> int:
    mm = _load_memory_map()
    region = next((r for r in mm.regions if r.name == args.region), None)
    if region is None:
        valid = ", ".join(sorted(r.name for r in mm.regions))
        print(f"error: unknown region {args.region!r}; valid regions: {valid}", file=sys.stderr)
        return 2

    found = _extract_strings(region.data, region.base)
    total = len(found)
    shown = found if args.all else found[:STRINGS_CAP]
    capped = (not args.all) and total > STRINGS_CAP
    print(
        f"# {total} string(s) (len>=6, ASCII/Shift-JIS heuristic) found in {region.name}"
        + (f" (showing first {STRINGS_CAP}, use --all for the rest)" if capped else "")
    )
    for addr, text in shown:
        print(f"0x{addr:08X} ({region.name}): {text}")
    if capped:
        print(f"... {total - STRINGS_CAP} more (use --all)")
    return 0


# --------------------------------------------------------------------------
# pool-values
# --------------------------------------------------------------------------


def cmd_pool_values(args: argparse.Namespace) -> int:
    lo, hi = args.lo, args.hi
    if lo > hi:
        lo, hi = hi, lo

    xrefs = _load_xrefs()
    hits = [r for r in xrefs["literal_loads"] if lo <= parse_int(r["value"]) <= hi]
    hits.sort(key=lambda r: (parse_int(r["value"]), parse_int(r["insn_addr"]), r["provenance"]))

    print(f"# {len(hits)} literal_load(s) with value in [0x{lo:08X}, 0x{hi:08X}]")
    for r in hits:
        print(
            f"0x{parse_int(r['insn_addr']):08X} ({r['provenance']}, {r['mode']}) "
            f"pool=0x{parse_int(r['pool_addr']):08X} value=0x{parse_int(r['value']):08X}"
        )
    return 0


# --------------------------------------------------------------------------
# Argument parser
# --------------------------------------------------------------------------

_TOP_EPILOG = f"""\
OVERLAY AMBIGUITY:
  ov0-ov9 all load at the same RAM base 0x0214CD20 (only one is resident in
  that window at a time at runtime). Likewise ov10/ov11 share 0x02172A60,
  and ov12/ov13 share 0x021AC1C0. Any address in one of these windows is
  ambiguous by itself: it could belong to any overlay sharing that base.
  Commands that resolve an address to one specific region/function (func,
  callers, callees, disasm) detect this, print every candidate to stderr,
  and exit non-zero -- pass --overlay ovN (or --overlay N) to pick one.
  Example: `query.py func 0x0214CD20` is ambiguous; `query.py func
  0x0214CD20 --overlay ov1` is not. arm9 never overlaps with anything.

ADDRESSES: 0x-prefixed hex (0x020784FC) or plain decimal. Case-insensitive.

OUTPUT CONTRACT:
  Listing subcommands print a leading "# N ..." summary line, then N data
  lines, each one self-describing (it names its own provenance) and safe to
  quote standalone as evidence. Errors and ambiguity candidate listings go
  to stderr with a non-zero exit; stdout carries only successful results.
  `disasm` is the exception: its stdout is byte-for-byte verbatim listing
  text with no added header, by design (see `query.py disasm --help`).

DATA SOURCES (read-only, pre-built; this CLI never rebuilds them):
  jus_files/analysis/functions.json        (8712 functions, disasm_db.py)
  jus_files/analysis/xrefs.json            (~146k records, xref_db.py)
  jus_files/analysis/disasm/<provenance>.txt

SEED ANCHORS used throughout this --help text (all independently verified):
  0x{_ANCHOR_DAMAGE_FUNC:08X}  arm9 function (push {{r4, lr}}), GDB-proven damage code
  0x{_ANCHOR_DAMAGE_INNER:08X}  an instruction inside that same function
  0x{_ANCHOR_COLLISION_TABLE:08X}  collision_file_pointer_table (arm9), 8 literal refs
  0x{_ANCHOR_OVERLAP_BASE:08X}  ov0-ov9 shared base (overlay-ambiguity demo)
  0x{_ANCHOR_MOV_IMM:08X}  arm9 "mov r0, #0x3c" (search-op-imm demo)

Run `query.py --selftest` to verify this installation end-to-end.
"""


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="query.py",
        description=(
            "Read-only query CLI over the FTC NDS ROM's pre-built static "
            "reverse-engineering databases (functions.json, xrefs.json, and "
            "the per-region disassembly listings). Every subcommand accepts "
            "-h/--help for a worked example."
        ),
        epilog=_TOP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the built-in acceptance smoke tests (each via its own argparse "
        "path) and exit 0 only if every one passes. Ignores any subcommand.",
    )

    subparsers = parser.add_subparsers(dest="command")

    overlay_parent = argparse.ArgumentParser(add_help=False)
    overlay_parent.add_argument(
        "--overlay",
        default=None,
        metavar="OVERLAY",
        help="Disambiguate an address that falls in an overlapping overlay "
        "window (e.g. 'ov1' or '1'). See OVERLAY AMBIGUITY below.",
    )

    p_func = subparsers.add_parser(
        "func",
        parents=[overlay_parent],
        description=(
            "Show the function that contains ADDR: start address, provenance, "
            "size, mode, and callee/caller counts. If ADDR falls inside more "
            "than one overlapping region and --overlay is not given, every "
            "candidate function is listed (to stderr) and the command exits "
            "non-zero."
        ),
        epilog=(
            "Example:\n"
            f"  query.py func 0x{_ANCHOR_DAMAGE_INNER:08X}\n"
            f"  -> 0x{_ANCHOR_DAMAGE_FUNC:08X} (arm9): size=84 mode=arm callees=1 callers=0\n"
            f"  (0x{_ANCHOR_DAMAGE_INNER:08X} is an instruction inside this function; it is\n"
            "  the GDB-proven damage-code function, returned as the containing func.)\n\n"
            "Ambiguity example:\n"
            f"  query.py func 0x{_ANCHOR_OVERLAP_BASE:08X}              # error: lists ov0..ov9 candidates, exit != 0\n"
            f"  query.py func 0x{_ANCHOR_OVERLAP_BASE:08X} --overlay ov1  # ok, one function line"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Show the function containing ADDR (start, provenance, size, mode, counts).",
    )
    p_func.add_argument("addr", type=_addr_type, help="Address inside the function (0x-hex or decimal).")
    p_func.set_defaults(handler=cmd_func)

    p_callers = subparsers.add_parser(
        "callers",
        parents=[overlay_parent],
        description=(
            "List every known caller of the function containing ADDR: "
            "same-region callers from functions.json's call graph, plus every "
            "direct bl/blx instruction anywhere in the ROM (any region, "
            "including cross-overlay calls that functions.json's per-region "
            "call graph cannot see) whose immediate target lands on that "
            "function's start, from xrefs.json. Each line names its source "
            "and provenance."
        ),
        epilog=(
            "Example:\n"
            f"  query.py callers 0x{_ANCHOR_DAMAGE_FUNC:08X}\n"
            "  -> a '# N caller reference(s) ...' summary line, then one line per\n"
            "     caller (function-start address from functions.json, and/or exact\n"
            "     call-site instruction addresses from xrefs.json)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="List callers of the function containing ADDR.",
    )
    p_callers.add_argument("addr", type=_addr_type, help="Address inside the function (0x-hex or decimal).")
    p_callers.set_defaults(handler=cmd_callers)

    p_callees = subparsers.add_parser(
        "callees",
        parents=[overlay_parent],
        description=(
            "List every function called BY the function containing ADDR "
            "(functions.json's callees list for that function), each "
            "resolved to the region(s) that map its target address (or "
            "'unmapped' if disasm_db.py could not map it to any region)."
        ),
        epilog=(
            "Example:\n"
            f"  query.py callees 0x{_ANCHOR_DAMAGE_FUNC:08X}\n"
            "  -> a '# N callee reference(s) ...' summary line, then one line per\n"
            "     callee target address with its resolved provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="List callees of the function containing ADDR.",
    )
    p_callees.add_argument("addr", type=_addr_type, help="Address inside the function (0x-hex or decimal).")
    p_callees.set_defaults(handler=cmd_callees)

    p_xrefs_to = subparsers.add_parser(
        "xrefs-to",
        description=(
            "Show everything in xrefs.json (and, if ADDR is itself a function "
            "start, functions.json) that references ADDR: literal-pool loads "
            "whose resolved value == ADDR, direct branches (b/bl/blx) whose "
            "target == ADDR, and that function's known callers. (imm_offsets "
            "struct-field immediates are never matched here -- comparing a "
            "small offset like 0x78 against a full 32-bit address makes no "
            "sense; use search-imm for that axis instead.)"
        ),
        epilog=(
            "Example:\n"
            f"  query.py xrefs-to 0x{_ANCHOR_COLLISION_TABLE:08X}\n"
            "  -> the collision_file_pointer_table; at least 8 literal_load hits\n"
            "     (8 different call sites across arm9/ov0/ov3/ov5/ov6 all load its\n"
            "     address out of a literal pool)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Show every literal_load/branch/caller reference to ADDR.",
    )
    p_xrefs_to.add_argument("addr", type=_addr_type, help="Target address to search for (0x-hex or decimal).")
    p_xrefs_to.set_defaults(handler=cmd_xrefs_to)

    p_search_imm = subparsers.add_parser(
        "search-imm",
        description=(
            "Find every base-register+immediate load/store (ldr/str/ldrb/"
            "strb/ldrh/strh/ldrsb/ldrsh, any condition code) anywhere in the "
            "ROM whose immediate operand equals VAL -- the way to answer "
            "'who touches struct field +0xNN'. Output is capped at "
            f"{SEARCH_IMM_CAP} lines by default; pass --all to see every hit."
        ),
        epilog=(
            "Example:\n"
            "  query.py search-imm 0x78\n"
            "  -> '# 442 hit(s) for imm == 120', then up to 200 lines like:\n"
            "     0x0200ABCD (arm9) ldr [r4, #0x78]\n"
            "  query.py search-imm 0x78 --all   # all 442, no cap"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Find load/store instructions with a given immediate offset.",
    )
    p_search_imm.add_argument("val", type=_imm_type, help="Immediate value to match (0x-hex or decimal, may be negative).")
    p_search_imm.add_argument("--all", action="store_true", help=f"Show every hit instead of capping at {SEARCH_IMM_CAP}.")
    p_search_imm.set_defaults(handler=cmd_search_imm)

    p_search_op_imm = subparsers.add_parser(
        "search-op-imm",
        description=(
            "Find every data-processing instruction (cmp/cmn/tst/teq/mov/"
            "mvn/and/orr/eor/add/sub/rsb, any condition code, and for the "
            "eight that support it the flag-setting 'S' form) anywhere in "
            "the ROM whose #immediate operand equals VAL -- the way to "
            "answer 'who compares/moves/masks against constant K', which "
            "search-imm cannot see (search-imm only covers load/store "
            "base+offset immediates, not data-processing operands). Scans "
            "the pre-built disasm/<provenance>.txt listings directly rather "
            "than xrefs.json. Output is capped at "
            f"{SEARCH_IMM_CAP} lines by default; pass --all to see every hit."
        ),
        epilog=(
            "Example:\n"
            "  query.py search-op-imm 0x3c\n"
            "  -> a '# N hit(s) ...' summary line including:\n"
            f"     0x{_ANCHOR_MOV_IMM:08X} (arm9) mov r0, #0x3c\n"
            "  query.py search-op-imm 0x3c --mnemonic cmp   # only cmp hits\n"
            "  query.py search-op-imm 0x3c --all            # every hit, no cap"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Find data-processing instructions with a given #immediate operand.",
    )
    p_search_op_imm.add_argument(
        "val", type=_imm_type, help="Immediate value to match (0x-hex or decimal, may be negative)."
    )
    p_search_op_imm.add_argument(
        "--mnemonic",
        default=None,
        metavar="M",
        help="Only match this base mnemonic, e.g. 'cmp' (condition code/'S' suffix ignored). "
        "One of: " + ", ".join(_DP_MNEMONICS) + ".",
    )
    p_search_op_imm.add_argument(
        "--all", action="store_true", help=f"Show every hit instead of capping at {SEARCH_IMM_CAP}."
    )
    p_search_op_imm.set_defaults(handler=cmd_search_op_imm)

    p_disasm = subparsers.add_parser(
        "disasm",
        parents=[overlay_parent],
        description=(
            "Print N consecutive lines, verbatim, from the pre-built "
            "disassembly listing starting at ADDR. stdout is exactly the "
            "listing-file text (no header, no reformatting) so it can be "
            "quoted directly as evidence; any resolution context (which "
            "region was used) is printed to stderr instead."
        ),
        epilog=(
            "Example:\n"
            f"  query.py disasm 0x{_ANCHOR_DAMAGE_FUNC:08X} 10\n"
            f"  -> 0x{_ANCHOR_DAMAGE_FUNC:08X}: 10402de9  push {{r4, lr}}\n"
            "     ...9 more lines, verbatim from disasm/arm9.txt\n\n"
            "Ambiguity example:\n"
            f"  query.py disasm 0x{_ANCHOR_OVERLAP_BASE:08X} 5              # error: ov0..ov9 all match, exit != 0\n"
            f"  query.py disasm 0x{_ANCHOR_OVERLAP_BASE:08X} 5 --overlay ov1  # ok, 5 verbatim lines from disasm/ov1.txt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Print N verbatim disassembly lines starting at ADDR.",
    )
    p_disasm.add_argument("addr", type=_addr_type, help="Start address (0x-hex or decimal).")
    p_disasm.add_argument("n", type=_count_type, help="Number of listing lines to print.")
    p_disasm.set_defaults(handler=cmd_disasm)

    p_strings = subparsers.add_parser(
        "strings",
        description=(
            "Extract printable ASCII / Shift-JIS text runs (>= 6 bytes) from "
            "REGION's raw bytes, with their mapped address. This is a byte-"
            "heuristic like the classic Unix `strings` tool (extended for "
            "Shift-JIS double-byte characters): it WILL include false "
            "positives where code/data bytes happen to form a valid-looking "
            "run -- treat hits as candidates, not guaranteed text. Output is "
            f"capped at {STRINGS_CAP} lines by default; pass --all to see every hit."
        ),
        epilog=(
            "Example:\n"
            "  query.py strings arm9\n"
            "  -> '# N string(s) ... found in arm9', then lines like:\n"
            "     0x02000B7B (arm9): ![SDK+NINTENDO:BACKUP]\n\n"
            "Valid REGION values: arm9, ov0, ov1, ... ov13."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Extract printable ASCII/Shift-JIS strings from REGION.",
    )
    p_strings.add_argument("region", help="arm9 or ov0..ov13.")
    p_strings.add_argument("--all", action="store_true", help=f"Show every hit instead of capping at {STRINGS_CAP}.")
    p_strings.set_defaults(handler=cmd_strings)

    p_pool_values = subparsers.add_parser(
        "pool-values",
        description=(
            "Find every literal_loads record (xrefs.json) whose resolved "
            "value falls within [ADDR-LO, ADDR-HI] inclusive -- useful for "
            "finding pointers into a known table's address range, or nearby "
            "table entries."
        ),
        epilog=(
            "Example:\n"
            f"  query.py pool-values 0x{_ANCHOR_COLLISION_TABLE:08X} 0x{_ANCHOR_COLLISION_TABLE + 4:08X}\n"
            "  -> literal loads whose value lands on the first two words of\n"
            "     collision_file_pointer_table."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Find literal_load values within [ADDR-LO, ADDR-HI].",
    )
    p_pool_values.add_argument("lo", type=_addr_type, help="Range low bound, inclusive (0x-hex or decimal).")
    p_pool_values.add_argument("hi", type=_addr_type, help="Range high bound, inclusive (0x-hex or decimal).")
    p_pool_values.set_defaults(handler=cmd_pool_values)

    return parser


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------


def _invoke(argv: list[str]) -> tuple[int, str, str]:
    """Run `main(argv)` through its own argparse path, capturing stdout/
    stderr, and normalizing any SystemExit (e.g. from --help or an argparse
    usage error) into an exit code instead of letting it propagate.
    """
    out, err = io.StringIO(), io.StringIO()
    code: int = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            result = main(argv)
        code = 0 if result is None else result
    except SystemExit as exc:
        if exc.code is None:
            code = 0
        elif isinstance(exc.code, int):
            code = exc.code
        else:
            code = 1
    return code, out.getvalue(), err.getvalue()


def _count_from_summary(out: str) -> int:
    """Pull the leading integer out of a '# N ...' summary line, or -1 if
    no such line is present.
    """
    m = re.match(r"#\s*(\d+)\s", out)
    return int(m.group(1)) if m else -1


def run_selftest() -> bool:
    all_ok = True

    def check(label: str, ok: bool) -> None:
        nonlocal all_ok
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")

    # a. func 0x020784FC -> returns the arm9 function 0x020784E4
    code, out, _err = _invoke(["func", f"0x{_ANCHOR_DAMAGE_INNER:08X}"])
    ok = code == 0 and f"0x{_ANCHOR_DAMAGE_FUNC:08X}" in out and "(arm9)" in out
    check(f"a. func 0x{_ANCHOR_DAMAGE_INNER:08X} -> arm9 function 0x{_ANCHOR_DAMAGE_FUNC:08X} (exit={code}, out={out.strip()!r})", ok)

    # b. callers 0x020784E4 -> >= 1 caller
    code, out, _err = _invoke(["callers", f"0x{_ANCHOR_DAMAGE_FUNC:08X}"])
    n = _count_from_summary(out)
    ok = code == 0 and n >= 1
    check(f"b. callers 0x{_ANCHOR_DAMAGE_FUNC:08X} -> {n} caller(s) (exit={code})", ok)

    # c. callees 0x020784E4 -> runs clean (>= 0, no crash)
    code, out, _err = _invoke(["callees", f"0x{_ANCHOR_DAMAGE_FUNC:08X}"])
    n = _count_from_summary(out)
    ok = code == 0 and n >= 0
    check(f"c. callees 0x{_ANCHOR_DAMAGE_FUNC:08X} -> runs clean, {n} callee(s) (exit={code})", ok)

    # d. xrefs-to 0x020924B0 -> >= 8 hits
    code, out, _err = _invoke(["xrefs-to", f"0x{_ANCHOR_COLLISION_TABLE:08X}"])
    n = _count_from_summary(out)
    ok = code == 0 and n >= 8
    check(f"d. xrefs-to 0x{_ANCHOR_COLLISION_TABLE:08X} -> {n} hit(s) (exit={code})", ok)

    # e. search-imm 0x78 -> >= 400 hits reported
    code, out, _err = _invoke(["search-imm", "0x78"])
    n = _count_from_summary(out)
    ok = code == 0 and n >= 400
    check(f"e. search-imm 0x78 -> {n} hit(s) reported (exit={code})", ok)

    # e2. search-op-imm 0x3c -> finds "mov r0, #0x3c" at 0x02078520
    code, out, _err = _invoke(["search-op-imm", "0x3c"])
    ok = code == 0 and f"0x{_ANCHOR_MOV_IMM:08X} (arm9) mov r0, #0x3c" in out
    check(f"e2. search-op-imm 0x3c -> finds mov r0, #0x3c at 0x{_ANCHOR_MOV_IMM:08X} (exit={code})", ok)

    # f. disasm 0x020784E4 10 -> 10 lines, first line starts "0x020784E4:"
    code, out, _err = _invoke(["disasm", f"0x{_ANCHOR_DAMAGE_FUNC:08X}", "10"])
    lines = out.splitlines()
    ok = code == 0 and len(lines) == 10 and lines[0].startswith(f"0x{_ANCHOR_DAMAGE_FUNC:08X}:")
    check(
        f"f. disasm 0x{_ANCHOR_DAMAGE_FUNC:08X} 10 -> {len(lines)} line(s), "
        f"first={lines[0] if lines else '<none>'!r} (exit={code})",
        ok,
    )

    # g. disasm 0x0214CD20 5 (no --overlay) -> nonzero exit + candidate list;
    #    with --overlay ov1 -> 5 lines.
    code1, _out1, err1 = _invoke(["disasm", f"0x{_ANCHOR_OVERLAP_BASE:08X}", "5"])
    ok1 = code1 != 0 and ("ambiguous" in err1.lower() or "candidate" in err1.lower())
    code2, out2, _err2 = _invoke(["disasm", f"0x{_ANCHOR_OVERLAP_BASE:08X}", "5", "--overlay", "ov1"])
    lines2 = out2.splitlines()
    ok2 = code2 == 0 and len(lines2) == 5
    check(
        f"g. disasm 0x{_ANCHOR_OVERLAP_BASE:08X} 5 ambiguous without --overlay "
        f"(exit={code1}) and 5 lines with --overlay ov1 (exit={code2}, lines={len(lines2)})",
        ok1 and ok2,
    )

    # h. strings arm9 -> >= 50 strings
    code, out, _err = _invoke(["strings", "arm9"])
    n = _count_from_summary(out)
    ok = code == 0 and n >= 50
    check(f"h. strings arm9 -> {n} string(s) (exit={code})", ok)

    # i. pool-values 0x020924B0 0x020924B4 -> >= 1
    code, out, _err = _invoke(
        ["pool-values", f"0x{_ANCHOR_COLLISION_TABLE:08X}", f"0x{_ANCHOR_COLLISION_TABLE + 4:08X}"]
    )
    n = _count_from_summary(out)
    ok = code == 0 and n >= 1
    check(f"i. pool-values 0x{_ANCHOR_COLLISION_TABLE:08X} 0x{_ANCHOR_COLLISION_TABLE + 4:08X} -> {n} hit(s) (exit={code})", ok)

    # j. --help and every subcommand --help exit 0 and are non-empty
    help_argvs = [
        ["--help"],
        ["func", "--help"],
        ["callers", "--help"],
        ["callees", "--help"],
        ["xrefs-to", "--help"],
        ["search-imm", "--help"],
        ["search-op-imm", "--help"],
        ["disasm", "--help"],
        ["strings", "--help"],
        ["pool-values", "--help"],
    ]
    j_ok = True
    j_details = []
    for argv in help_argvs:
        code, out, _err = _invoke(argv)
        this_ok = code == 0 and len(out.strip()) > 0
        j_ok = j_ok and this_ok
        j_details.append(f"{' '.join(argv)}={'ok' if this_ok else f'FAIL(exit={code})'}")
    check("j. --help / every subcommand --help exit 0 and non-empty: " + ", ".join(j_details), j_ok)

    return all_ok


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.selftest:
        return 0 if run_selftest() else 1

    if not getattr(args, "command", None):
        parser.print_help()
        return 1

    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
