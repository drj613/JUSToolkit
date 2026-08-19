#!/usr/bin/env python3
"""disasm_db.py - linear-sweep + heuristic disassembler / function-boundary
detector / call-graph extractor for the FTC (Jump Ultimate Stars) NDS ROM.

Builds on rom_loader.load_memory_map() to get every mapped Region (the arm9
binary plus each of the 14 overlays -- ov0..ov9 all sharing RAM base
0x0214CD20, ov10/ov11 sharing 0x02172A60, ov12/ov13 sharing 0x021AC1C0). Each
region is disassembled *independently*: provenance keeps overlapping regions
apart, they are never merged.

Pipeline per region:
  1. Mark known ARM9 data tables (mechanical AC, arm9 only) as data upfront.
  2. Pass 1: quick ARM linear sweep to discover pc-relative `ldr rX,[pc,#imm]`
     literal-pool targets (these must not be treated as code in pass 2).
  3. Merge (known tables) + (literal pool words) -> a coalesced set of data
     byte-ranges. The complement of that set (within the region) is the set
     of "code spans" that pass 2 is allowed to disassemble.
  4. Pass 2: for each code span, do a restart-on-invalid ARM linear sweep
     (capstone stops decoding at the first undecodable word, so we advance
     4 bytes and retry -- any word that never decodes is recorded as a data
     word / "nonsense" gap). Along the way, note `blx <imm>` targets as
     Thumb-mode function candidates (BLX immediate always switches ARM<->
     Thumb state, per ARMv5T semantics) and attempt a small bounded Thumb
     sweep at each one.
  5. Function boundaries: starts = push-with-lr prologues, plus bl/blx
     targets that land exactly on an already-decoded instruction address in
     the same region. Ends = bx lr / pop{...,pc} terminator closest to (but
     before) the next start, else the next start itself, else the end of
     the code span.
  6. Call graph: callees = bl/blx immediate targets found inside a
     function's own [addr, addr+size) range. callers = inverse of callees,
     restricted to the same region/provenance (cross-overlay resolution is
     ambiguous since ov0..ov9 etc. share address windows). Callees whose
     target is not covered by *any* region in the whole memory map are
     additionally listed per-function under "unmapped_callees".

Outputs (written under jus_files/analysis/, which is fine to write through
even though it's a symlink):
  jus_files/analysis/functions.json
  jus_files/analysis/disasm/<provenance>.txt   (one per region)

CLI:
  disasm_db.py [--rom-dir PATH] [--selftest]
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import capstone
from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rom_loader import MemoryMap, Region, load_memory_map  # noqa: E402

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = _REPO_ROOT / "jus_files" / "analysis"
DISASM_DIR = ANALYSIS_DIR / "disasm"
FUNCTIONS_JSON = ANALYSIS_DIR / "functions.json"

# Mechanical-AC data tables: (addr, size, label). ARM9 only.
KNOWN_ARM9_DATA_TABLES = [
    (0x020924B0, 0x100, "collision_file_pointer_table"),
    (0x0208D4A0, 0x100, "chr_b_identity_map"),
    (0x0209E780, 0x100, "koma_name_table"),
]

# GDB-proven damage-code address used as a sweep-quality sanity check.
GDB_PROVEN_ADDR = 0x020784FC

FUNC_COUNT_MIN = 1000
FUNC_COUNT_MAX = 20000

# Regex helpers over capstone's op_str text (disasm_lite has no operand
# detail, so we parse the rendered text -- deliberately simple/robust).
_PC_REL_LDR_RE = re.compile(r"\[\s*pc\s*,\s*#(-?0x[0-9a-fA-F]+)\s*\]")
_IMM_TARGET_RE = re.compile(r"^#(-?0x[0-9a-fA-F]+)$")


def _reg_in_list(ops: str, reg: str) -> bool:
    return re.search(rf"\b{reg}\b", ops) is not None


def _parse_branch_target(ops: str) -> int | None:
    """bl/blx immediate operand text is exactly '#0x...' (no register form
    reaches here since indirect blx/bx targets can't be resolved statically
    and are intentionally skipped, per the "do not over-engineer" guidance).
    """
    m = _IMM_TARGET_RE.match(ops.strip())
    if not m:
        return None
    return int(m.group(1), 16)


def _align4_down(addr: int) -> int:
    return addr & ~0x3


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------


@dataclass
class Instr:
    addr: int
    size: int
    mnem: str
    ops: str
    mode: str  # "arm" | "thumb"
    raw: bytes


@dataclass
class DataWord:
    addr: int
    size: int
    raw: bytes


@dataclass
class Func:
    addr: int
    size: int
    mode: str
    provenance: str
    callees: set[int] = field(default_factory=set)
    callers: set[int] = field(default_factory=set)
    unmapped_callees: set[int] = field(default_factory=set)


# --------------------------------------------------------------------------
# Interval helpers
# --------------------------------------------------------------------------


def _coalesce(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge a list of (start, end) half-open byte-offset ranges."""
    if not ranges:
        return []
    ranges = sorted(ranges)
    out = [list(ranges[0])]
    for s, e in ranges[1:]:
        if s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [(s, e) for s, e in out]


def _complement(ranges: list[tuple[int, int]], total: int) -> list[tuple[int, int]]:
    """Complement of coalesced `ranges` within [0, total)."""
    out = []
    cur = 0
    for s, e in ranges:
        if s > cur:
            out.append((cur, s))
        cur = max(cur, e)
    if cur < total:
        out.append((cur, total))
    return out


# --------------------------------------------------------------------------
# Linear sweep primitives
# --------------------------------------------------------------------------


def _sweep_arm_span(cs_arm: capstone.Cs, data: bytes, base: int, start: int, end: int):
    """Restart-on-invalid ARM sweep bounded to byte offsets [start, end) of
    `data`. Yields Instr for every valid decode and DataWord (4 bytes) for
    every undecodable word encountered along the way. ARM instructions are
    always 4 bytes, so a failed decode always advances by exactly 4.
    """
    mv = memoryview(data)
    pos = start
    while pos < end:
        decoded_any = False
        for a, size, mnem, ops in cs_arm.disasm_lite(mv[pos:end], base + pos):
            decoded_any = True
            yield Instr(a, size, mnem, ops, "arm", bytes(data[pos : pos + size]))
            pos += size
        if not decoded_any:
            word_end = min(pos + 4, end)
            yield DataWord(base + pos, word_end - pos, bytes(data[pos:word_end]))
            pos = word_end


# --------------------------------------------------------------------------
# Per-region analysis
# --------------------------------------------------------------------------


class RegionAnalysis:
    def __init__(self, region: Region):
        self.region = region
        self.provenance = region.name
        # Address-ordered mixture of Instr / DataWord covering [0, size).
        self.entries: list[Instr | DataWord] = []
        self.functions: list[Func] = []

    def data_word_bytes(self) -> int:
        return sum(e.size for e in self.entries if isinstance(e, DataWord))

    def instr_count(self) -> int:
        return sum(1 for e in self.entries if isinstance(e, Instr))


def _known_table_ranges(region: Region) -> list[tuple[int, int]]:
    if region.name != "arm9":
        return []
    ranges = []
    for addr, size, _label in KNOWN_ARM9_DATA_TABLES:
        off = addr - region.base
        if 0 <= off < region.size:
            ranges.append((off, min(off + size, region.size)))
    return ranges


def _pass1_literal_pool_ranges(
    cs_arm: capstone.Cs, region: Region, known_ranges: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Quick ARM sweep of the whole region (skipping known tables) purely to
    collect pc-relative `ldr rX,[pc,#imm]` literal targets so pass 2 can
    exclude them from the code stream before function detection runs.
    """
    data = region.data
    base = region.base
    size = region.size
    code_spans = _complement(_coalesce(known_ranges), size)

    literal_ranges: list[tuple[int, int]] = []
    for start, end in code_spans:
        for item in _sweep_arm_span(cs_arm, data, base, start, end):
            if isinstance(item, Instr) and item.mnem == "ldr":
                m = _PC_REL_LDR_RE.search(item.ops)
                if m:
                    imm = int(m.group(1), 16)
                    target = _align4_down(item.addr + 8 + imm)
                    off = target - base
                    if 0 <= off < size - 3:
                        literal_ranges.append((off, off + 4))
    return literal_ranges


def _arm_pass(region: Region, cs_arm: capstone.Cs) -> tuple[RegionAnalysis, set[int]]:
    """Phase A (per region, independent): known-table exclusion + literal
    pool pass 1 + the real ARM pass 2 sweep. Returns the region's ARM-only
    entries plus the set of `blx <imm>` targets discovered while sweeping it
    (used later, globally, to seed Thumb candidates -- see _arm_pass note on
    why this must not be limited to same-region targets).
    """
    ra = RegionAnalysis(region)
    data = region.data
    base = region.base
    size = region.size

    known_ranges = _known_table_ranges(region)
    literal_ranges = _pass1_literal_pool_ranges(cs_arm, region, known_ranges)
    data_ranges = _coalesce(known_ranges + literal_ranges)
    code_spans = _complement(data_ranges, size)

    entries: list[Instr | DataWord] = []
    span_iter = iter(code_spans)
    range_iter = iter(data_ranges)
    next_span = next(span_iter, None)
    next_range = next(range_iter, None)
    blx_targets: set[int] = set()

    while next_span is not None or next_range is not None:
        if next_range is not None and (
            next_span is None or next_range[0] <= next_span[0]
        ):
            s, e = next_range
            off = s
            while off < e:
                w_end = min(off + 4, e)
                entries.append(DataWord(base + off, w_end - off, bytes(data[off:w_end])))
                off = w_end
            next_range = next(range_iter, None)
        else:
            s, e = next_span
            for item in _sweep_arm_span(cs_arm, data, base, s, e):
                entries.append(item)
                if isinstance(item, Instr) and item.mnem in ("bl", "blx"):
                    target = _parse_branch_target(item.ops)
                    if target is not None and item.mnem == "blx":
                        blx_targets.add(target)
            next_span = next(span_iter, None)

    ra.entries = entries
    return ra, blx_targets


def _try_thumb_function(
    cs_thumb: capstone.Cs, data: bytes, base: int, start_off: int, limit_off: int
) -> list[Instr] | None:
    """Attempt to decode a *complete* Thumb function starting at byte offset
    `start_off`, stopping no later than `limit_off`. Accept/reject gate: a
    single capstone disasm_lite call already stops dead at the first
    undecodable halfword (proven empirically -- capstone does not skip-and-
    resync on its own), so if the generator runs out (hits invalid bytes, or
    exhausts the [start_off, limit_off) window) *before* reaching an explicit
    `bx lr` / `pop {...,pc}` terminator, this is rejected outright: no
    partial/low-confidence splice. This is deliberately strict because ARM's
    encoding space is dense enough that "some Thumb instructions decoded"
    is weak evidence on its own -- only "cleanly decodes all the way to a
    return" is treated as proof the target is real Thumb code.
    """
    mv = memoryview(data)
    items: list[Instr] = []
    for a, size, mnem, ops in cs_thumb.disasm_lite(mv[start_off:limit_off], base + start_off):
        off = a - base
        items.append(Instr(a, size, mnem, ops, "thumb", bytes(data[off : off + size])))
        if (mnem == "bx" and _reg_in_list(ops, "lr")) or (
            mnem == "pop" and _reg_in_list(ops, "pc")
        ):
            return items
    return None  # invalid decode or ran out of budget before a terminator


# Cap how far a single candidate Thumb function is allowed to run before we
# give up looking for its terminator (bounds pathological cases; cheap to
# raise since capstone is fast and rejected attempts are discarded anyway).
_THUMB_CANDIDATE_MAX_BYTES = 0x4000


def _excise_and_splice(
    entries: list[Instr | DataWord], accepted: list[list[Instr]]
) -> list[Instr | DataWord]:
    """Remove any entries overlapping an accepted Thumb function's byte
    range, then splice the Thumb instructions in, re-sorted by address.
    """
    if not accepted:
        return entries
    ranges = [(items[0].addr, items[-1].addr + items[-1].size) for items in accepted]
    kept = [
        e
        for e in entries
        if not any(e.addr < hi and e.addr + e.size > lo for lo, hi in ranges)
    ]
    for items in accepted:
        kept.extend(items)
    kept.sort(key=lambda e: e.addr)
    return kept


def analyze_all(
    mm: MemoryMap, cs_arm: capstone.Cs, cs_thumb: capstone.Cs
) -> list[RegionAnalysis]:
    # Phase A: ARM-only pass per region (independent), collecting each
    # region's own local blx-immediate targets along the way.
    analyses: list[RegionAnalysis] = []
    blx_by_region: dict[str, set[int]] = {}
    for region in mm.regions:
        ra, blx_targets = _arm_pass(region, cs_arm)
        analyses.append(ra)
        blx_by_region[ra.provenance] = blx_targets

    # Phase B: union every region's local blx targets into one global set.
    # This matters a lot in practice: e.g. arm9 issues `blx 0x0214CD20` to
    # call into "whichever per-character overlay is currently loaded" --
    # that target is *outside* arm9's own byte range, so it would never be
    # found by scoping detection to "blx targets found within this same
    # region". Overlays also blx into each other's bodies. Using the global
    # union lets every region be seeded by blx calls issued from anywhere.
    global_blx: set[int] = set()
    for targets in blx_by_region.values():
        global_blx |= targets

    # Phase C: for each region, gather every candidate Thumb start (local +
    # global targets landing inside this region), try a strict clean-decode-
    # to-terminator sweep at each, and splice in whatever is accepted.
    for ra in analyses:
        region = ra.region
        base, end, size = region.base, region.end, region.size
        candidates = set(blx_by_region[ra.provenance])
        candidates |= {t for t in global_blx if base <= t < end}

        accepted: list[list[Instr]] = []
        for target in sorted(candidates):
            off = target - base
            if not (0 <= off < size):
                continue
            limit_off = min(size, off + _THUMB_CANDIDATE_MAX_BYTES)
            items = _try_thumb_function(cs_thumb, region.data, base, off, limit_off)
            if items:
                accepted.append(items)

        ra.entries = _excise_and_splice(ra.entries, accepted)
        ra.functions = _detect_functions(ra)

    return analyses


# --------------------------------------------------------------------------
# Function boundary detection
# --------------------------------------------------------------------------

_TERMINATOR_MNEMS_LR = {"bx"}  # bx lr
_TERMINATOR_MNEMS_PC = {"pop", "ldmfd", "ldmia"}  # pop/ldm{...,pc}


def _is_prologue(instr: Instr) -> bool:
    if instr.mnem == "push" and _reg_in_list(instr.ops, "lr"):
        return True
    if instr.mnem in ("stmdb", "stmfd") and "sp!" in instr.ops and _reg_in_list(
        instr.ops, "lr"
    ):
        return True
    return False


def _is_terminator(instr: Instr) -> bool:
    if instr.mnem in _TERMINATOR_MNEMS_LR and _reg_in_list(instr.ops, "lr"):
        return True
    if instr.mnem in _TERMINATOR_MNEMS_PC and _reg_in_list(instr.ops, "pc"):
        return True
    return False


def _detect_functions(ra: RegionAnalysis) -> list[Func]:
    all_instrs = [e for e in ra.entries if isinstance(e, Instr)]
    if not all_instrs:
        return []

    all_addr_set = {i.addr for i in all_instrs}

    # bl/blx targets that land exactly on a decoded instruction anywhere in
    # this region -> additional function-start candidates (covers leaf /
    # tail-call functions that don't have a push-lr prologue).
    bl_target_starts: set[int] = set()
    for instr in all_instrs:
        if instr.mnem in ("bl", "blx"):
            target = _parse_branch_target(instr.ops)
            if target is not None and target in all_addr_set:
                bl_target_starts.add(target)

    funcs: list[Func] = []

    # Process contiguous runs of instructions ("spans" in the *decoded*
    # sense -- i.e. runs separated by DataWord entries) independently, so a
    # function's size can never cross into a data range.
    i = 0
    n = len(ra.entries)
    while i < n:
        if not isinstance(ra.entries[i], Instr):
            i += 1
            continue
        j = i
        run: list[Instr] = []
        while j < n and isinstance(ra.entries[j], Instr):
            run.append(ra.entries[j])
            j += 1
        funcs.extend(_detect_functions_in_run(run, bl_target_starts, ra.provenance))
        i = j

    return funcs


def _detect_functions_in_run(
    run: list[Instr], bl_target_starts: set[int], provenance: str
) -> list[Func]:
    if not run:
        return []

    starts = sorted(
        {instr.addr for instr in run if _is_prologue(instr)}
        | {instr.addr for instr in run if instr.addr in bl_target_starts}
    )
    if not starts:
        return []

    terminators = [
        (instr.addr, instr.addr + instr.size) for instr in run if _is_terminator(instr)
    ]
    terminators.sort()

    run_end = run[-1].addr + run[-1].size
    funcs: list[Func] = []
    t_idx = 0
    for k, start in enumerate(starts):
        next_start = starts[k + 1] if k + 1 < len(starts) else run_end
        # advance t_idx to the first terminator >= start
        while t_idx < len(terminators) and terminators[t_idx][0] < start:
            t_idx += 1
        best_end = None
        p = t_idx
        while p < len(terminators) and terminators[p][0] < next_start:
            best_end = terminators[p][1]
            p += 1
        size = (best_end - start) if best_end is not None else (next_start - start)
        mode = next(instr.mode for instr in run if instr.addr == start)
        funcs.append(Func(addr=start, size=size, mode=mode, provenance=provenance))
    return funcs


# --------------------------------------------------------------------------
# Call graph
# --------------------------------------------------------------------------


def _build_call_graph(ra: RegionAnalysis, mm: MemoryMap) -> None:
    instrs = [e for e in ra.entries if isinstance(e, Instr)]
    instrs.sort(key=lambda e: e.addr)
    addrs = [e.addr for e in instrs]

    func_by_addr = {f.addr: f for f in ra.functions}

    for f in ra.functions:
        lo = bisect.bisect_left(addrs, f.addr)
        hi = bisect.bisect_left(addrs, f.addr + f.size)
        for instr in instrs[lo:hi]:
            if instr.mnem not in ("bl", "blx"):
                continue
            target = _parse_branch_target(instr.ops)
            if target is None:
                continue
            f.callees.add(target)
            if not mm.candidates(target):
                f.unmapped_callees.add(target)

    for f in ra.functions:
        for target in f.callees:
            callee_func = func_by_addr.get(target)
            if callee_func is not None:
                callee_func.callers.add(f.addr)


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def _format_disasm_line(entry: Instr | DataWord) -> str:
    hexbytes = entry.raw.hex()
    if isinstance(entry, Instr):
        text = f"{entry.mnem} {entry.ops}".strip() if entry.ops else entry.mnem
    else:
        value = int.from_bytes(entry.raw.ljust(4, b"\x00"), "little")
        text = f".word 0x{value:08X}"
    return f"0x{entry.addr:08X}: {hexbytes}  {text}"


def _write_disasm_text(ra: RegionAnalysis) -> Path:
    DISASM_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DISASM_DIR / f"{ra.provenance}.txt"
    lines = [_format_disasm_line(e) for e in sorted(ra.entries, key=lambda e: e.addr)]
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""))
    return out_path


def _write_functions_json(
    analyses: list[RegionAnalysis], mm: MemoryMap, elapsed: float
) -> None:
    regions_meta = [
        {
            "provenance": r.name,
            "base": f"0x{r.base:08X}",
            "size": r.size,
        }
        for r in mm.regions
    ]

    functions_out = []
    for ra in analyses:
        for f in ra.functions:
            entry = {
                "addr": f"0x{f.addr:08X}",
                "provenance": f.provenance,
                "size": f.size,
                "mode": f.mode,
                "callees": [f"0x{t:08X}" for t in sorted(f.callees)],
                "callers": [f"0x{c:08X}" for c in sorted(f.callers)],
            }
            if f.unmapped_callees:
                entry["unmapped_callees"] = [
                    f"0x{t:08X}" for t in sorted(f.unmapped_callees)
                ]
            functions_out.append(entry)

    functions_out.sort(key=lambda e: (e["provenance"], int(e["addr"], 16)))

    doc = {
        "generated_by": "disasm_db.py",
        "elapsed_seconds": round(elapsed, 2),
        "regions": regions_meta,
        "functions": functions_out,
    }

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    FUNCTIONS_JSON.write_text(json.dumps(doc, indent=1))


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def run_sweep(rom_dir) -> tuple[MemoryMap, list[RegionAnalysis], float]:
    t0 = time.time()
    mm = load_memory_map(rom_dir)

    cs_arm = capstone.Cs(CS_ARCH_ARM, CS_MODE_ARM + CS_MODE_LITTLE_ENDIAN)
    cs_thumb = capstone.Cs(CS_ARCH_ARM, CS_MODE_THUMB + CS_MODE_LITTLE_ENDIAN)

    analyses = analyze_all(mm, cs_arm, cs_thumb)

    for ra in analyses:
        _build_call_graph(ra, mm)

    elapsed = time.time() - t0
    return mm, analyses, elapsed


def _find_function_containing(
    analyses: list[RegionAnalysis], provenance: str, addr: int
) -> Func | None:
    for ra in analyses:
        if ra.provenance != provenance:
            continue
        for f in ra.functions:
            if f.addr <= addr < f.addr + f.size:
                return f
    return None


def _selftest(mm: MemoryMap, analyses: list[RegionAnalysis], elapsed: float) -> bool:
    all_ok = True

    def check(label: str, ok: bool) -> None:
        nonlocal all_ok
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")

    total_funcs = sum(len(ra.functions) for ra in analyses)
    check(
        f"a. total function count in [{FUNC_COUNT_MIN}, {FUNC_COUNT_MAX}] (got {total_funcs})",
        FUNC_COUNT_MIN <= total_funcs <= FUNC_COUNT_MAX,
    )

    hit = _find_function_containing(analyses, "arm9", GDB_PROVEN_ADDR)
    check(
        f"b. 0x{GDB_PROVEN_ADDR:08X} falls inside some discovered arm9 function"
        + (f" (found 0x{hit.addr:08X}, size {hit.size})" if hit else " (no containing function found)"),
        hit is not None,
    )

    c_ok = True
    offenders = []
    for addr, _size, label in KNOWN_ARM9_DATA_TABLES:
        f = _find_function_containing(analyses, "arm9", addr)
        if f is not None:
            c_ok = False
            offenders.append((label, hex(addr), hex(f.addr)))
    check(
        f"c. none of the known data tables is inside any arm9 function"
        + (f" (offenders: {offenders})" if offenders else ""),
        c_ok,
    )

    d_ok = True
    for ra in analyses:
        for f in ra.functions:
            if not (ra.region.base <= f.addr < ra.region.end):
                d_ok = False
    check("d. every functions.json entry has a valid hex addr within its region", d_ok)

    check(f"e. full run wall time < 10 minutes (elapsed {elapsed:.1f}s)", elapsed < 600)

    return all_ok


def _print_summary(mm: MemoryMap, analyses: list[RegionAnalysis], elapsed: float) -> None:
    total_funcs = sum(len(ra.functions) for ra in analyses)
    total_instrs = sum(ra.instr_count() for ra in analyses)
    total_data_bytes = sum(ra.data_word_bytes() for ra in analyses)
    thumb_funcs = sum(1 for ra in analyses for f in ra.functions if f.mode == "thumb")

    print("=== disasm_db.py summary ===")
    print(f"regions swept: {len(analyses)}")
    print(f"total functions: {total_funcs} (thumb: {thumb_funcs})")
    print(f"total instructions decoded: {total_instrs}")
    print(f"total data bytes marked: {total_data_bytes}")
    print("per-region breakdown:")
    for ra in analyses:
        print(
            f"  {ra.provenance:<6} base=0x{ra.region.base:08X} size={ra.region.size:>8} "
            f"functions={len(ra.functions):>6} instrs={ra.instr_count():>7} "
            f"data_bytes={ra.data_word_bytes():>7}"
        )
    print(f"elapsed: {elapsed:.2f}s")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Linear-sweep disassembler / function-boundary detector "
        "/ call-graph extractor for the FTC NDS ROM."
    )
    parser.add_argument(
        "--rom-dir",
        type=Path,
        default=None,
        help="Directory containing arm9.bin, y9.bin, overlay9_*. "
        "Defaults to rom_loader.DEFAULT_ROM_DIR.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the sweep then assert the mechanical acceptance criteria; "
        "exit 0 only if all pass.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    mm, analyses, elapsed = run_sweep(args.rom_dir)

    if args.selftest:
        ok = _selftest(mm, analyses, elapsed)
        _print_summary(mm, analyses, elapsed)
        return 0 if ok else 1

    for ra in analyses:
        _write_disasm_text(ra)
    _write_functions_json(analyses, mm, elapsed)
    _print_summary(mm, analyses, elapsed)
    print(f"wrote {FUNCTIONS_JSON}")
    print(f"wrote {DISASM_DIR}/<provenance>.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
