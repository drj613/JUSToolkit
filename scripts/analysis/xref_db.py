#!/usr/bin/env python3
"""xref_db.py - cross-reference database builder for the FTC (Jump Ultimate
Stars) NDS ROM static reverse-engineering toolchain.

Builds on disasm_db.run_sweep() (which itself builds on
rom_loader.load_memory_map()) to get, per region (the arm9 binary plus every
overlay, each disassembled *independently* -- provenance keeps overlapping
overlay windows apart, they are never merged), a fully mixed Instr/DataWord
stream. This module re-walks that stream and extracts three cross-reference
indexes:

  1. literal_loads  (code -> data):  every pc-relative `ldr rX, [pc, #imm]`,
     resolved to the 32-bit value actually stored at the literal-pool slot it
     targets. This value is usually a RAM pointer -- a data table, a struct
     base, a function pointer loaded for an indirect call, etc. -- so it is
     the anchor for "what points at address X" queries.
  2. imm_offsets    (code -> struct-offset): every base-register-plus-
     immediate load/store (ldr/str/ldrb/strb/ldrh/strh/ldrsb/ldrsh with a
     non-zero immediate and a non-pc base register). This is the anchor for
     "who touches struct field +0x78" queries.
  3. branches       (code -> code): every direct b/bl/blx (any condition
     code) with a resolved immediate target.

Output: jus_files/analysis/xrefs.json, one flat JSON object:
    {"literal_loads": [...], "imm_offsets": [...], "branches": [...],
     "stats": {...}}

Reverse-lookup helpers (importable by later tool stages, also used by this
module's own --selftest):
    xrefs_to_value(addr)                 -> literal_loads whose value == addr
    funcs_touching_offset(imm, mnemonics=None) -> imm_offsets with that imm
    nearest_literal_values(addr, n=5)    -> n literal_loads closest to addr

CLI:
    xref_db.py [--rom-dir PATH] [--selftest]
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from disasm_db import (  # noqa: E402
    Instr,
    RegionAnalysis,
    _align4_down,
    _parse_branch_target,
    _PC_REL_LDR_RE,
    run_sweep,
)
from rom_loader import MemoryMap  # noqa: E402

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = _REPO_ROOT / "jus_files" / "analysis"
XREFS_JSON = ANALYSIS_DIR / "xrefs.json"
CHEAT_ADDRESSES_JSON = ANALYSIS_DIR / "cheat_addresses.json"

# Mechanical AC (a): RAM address of the collision file pointer table (ARM9
# file offset 0x0924B0), per disasm_db.KNOWN_ARM9_DATA_TABLES.
COLLISION_TABLE_ADDR = 0x020924B0

MAX_JSON_BYTES = 150 * 1024 * 1024

# Mechanical AC (d) floors.
LITERAL_LOADS_MIN = 5000
IMM_OFFSETS_MIN = 50000
BRANCHES_MIN = 50000

_RAM_LO = 0x02000000
_RAM_HI = 0x023FFFFF

# ARM condition-code mnemonic suffixes (order doesn't matter, membership
# test only).
_COND_CODES = {
    "eq", "ne", "cs", "hs", "cc", "lo", "mi", "pl",
    "vs", "vc", "hi", "ls", "ge", "lt", "gt", "le", "al",
}

# The 8 mechanical-AC load/store mnemonics, longest-prefix-first so e.g.
# "ldrb" is matched before the shorter "ldr" gets a chance to.
_LOAD_STORE_BASES = ["ldrsb", "ldrsh", "strb", "strh", "ldrb", "ldrh", "str", "ldr"]

# b / bl / blx, longest-prefix-first for the same reason.
_BRANCH_BASES = ["blx", "bl", "b"]

# Generic base+imm addressing: "rX, [rY, #imm]" or "rX, [rY, #imm]!"
# (register names are capstone's default ARM aliases: r0-r15, sp, lr, pc,
# fp, ip, sb, sl -- matched generically rather than enumerated).
_IMM_OFFSET_RE = re.compile(
    r"^\s*[a-z0-9]+\s*,\s*\[\s*([a-z0-9]+)\s*,\s*#(-?0x[0-9a-fA-F]+)\s*\]!?\s*$",
    re.IGNORECASE,
)


def _normalize_load_store_mnem(mnem: str) -> str | None:
    """Strip an ARM condition-code suffix from a load/store mnemonic and
    return the canonical base (one of the 8 mechanical-AC mnemonics), or
    None if `mnem` isn't one of those 8 (this also rejects the ldrt/strt
    "translate" variants and the ldrd/strd dual-register variants, since
    their addressing semantics differ and they aren't in the target set).
    """
    for base in _LOAD_STORE_BASES:
        if mnem.startswith(base):
            rest = mnem[len(base):]
            if rest == "" or rest in _COND_CODES:
                return base
    return None


def _branch_kind(mnem: str) -> str | None:
    """Strip an ARM condition-code suffix from a branch mnemonic and return
    the canonical kind ("b", "bl", or "blx"), or None if `mnem` isn't a
    direct branch (this rejects bx/bxeq/... since BX only ever takes a
    register operand, plus incidental prefix collisions like bic/bfi).
    """
    for base in _BRANCH_BASES:
        if mnem.startswith(base):
            rest = mnem[len(base):]
            if rest == "" or rest in _COND_CODES:
                return base
    return None


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------


def build_xrefs(mm: MemoryMap, analyses: list[RegionAnalysis]) -> dict:
    literal_loads: list[dict] = []
    imm_offsets: list[dict] = []
    branches: list[dict] = []

    skipped_literal_oob = 0
    skipped_imm_zero = 0
    total_instrs = 0

    for ra in analyses:
        region = ra.region
        data = region.data
        base = region.base
        size = region.size
        prov = ra.provenance

        for e in ra.entries:
            if not isinstance(e, Instr):
                continue
            total_instrs += 1
            mnem = e.mnem
            ops = e.ops

            # -- 1. literal loads (pc-relative `ldr`, exact mnemonic only,
            #    matching the convention disasm_db itself uses to carve
            #    literal-pool ranges out of the code stream). --------------
            if mnem == "ldr":
                m = _PC_REL_LDR_RE.search(ops)
                if m:
                    imm = int(m.group(1), 16)
                    if e.mode == "arm":
                        pool_addr = e.addr + 8 + imm
                    else:  # thumb
                        pool_addr = _align4_down(e.addr + 4) + imm
                    off = pool_addr - base
                    if 0 <= off <= size - 4:
                        (value,) = struct.unpack_from("<I", data, off)
                        literal_loads.append(
                            {
                                "insn_addr": f"0x{e.addr:08X}",
                                "provenance": prov,
                                "mode": e.mode,
                                "pool_addr": f"0x{pool_addr:08X}",
                                "value": f"0x{value:08X}",
                            }
                        )
                    else:
                        skipped_literal_oob += 1

            # -- 2. immediate offsets (base-register + immediate load/store,
            #    any of the 8 mechanical-AC mnemonics, any condition code).
            #    Excludes base_reg == pc (that's literal-load territory,
            #    handled above/separately) and imm == 0. --------------------
            base_mnem = _normalize_load_store_mnem(mnem)
            if base_mnem is not None:
                m2 = _IMM_OFFSET_RE.match(ops)
                if m2:
                    base_reg = m2.group(1).lower()
                    imm_val = int(m2.group(2), 16)
                    if base_reg == "pc":
                        pass  # counted under literal_loads instead
                    elif imm_val == 0:
                        skipped_imm_zero += 1
                    else:
                        imm_offsets.append(
                            {
                                "insn_addr": f"0x{e.addr:08X}",
                                "provenance": prov,
                                "mnemonic": base_mnem,
                                "base_reg": base_reg,
                                "imm": imm_val,
                            }
                        )

            # -- 3. direct branches (b/bl/blx, any condition code, resolved
            #    immediate target). ------------------------------------------
            kind = _branch_kind(mnem)
            if kind is not None:
                target = _parse_branch_target(ops)
                if target is not None:
                    branches.append(
                        {
                            "insn_addr": f"0x{e.addr:08X}",
                            "provenance": prov,
                            "kind": kind,
                            "target": f"0x{target:08X}",
                        }
                    )

    stats = {
        "literal_loads": len(literal_loads),
        "imm_offsets": len(imm_offsets),
        "branches": len(branches),
        "regions_swept": len(analyses),
        "total_instructions_scanned": total_instrs,
        "skipped_literal_pool_out_of_region": skipped_literal_oob,
        "skipped_imm_offset_zero": skipped_imm_zero,
        "dropped_for_size": {},
    }

    return {
        "literal_loads": literal_loads,
        "imm_offsets": imm_offsets,
        "branches": branches,
        "stats": stats,
    }


def _serialize(doc: dict) -> bytes:
    return json.dumps(doc, separators=(",", ":")).encode("utf-8")


def _shrink_to_fit(doc: dict) -> bytes:
    """Serialize `doc`; if it exceeds MAX_JSON_BYTES, progressively drop
    "small-common noise" imm_offsets (|imm| below an increasing threshold)
    and record exactly what was dropped in stats["dropped_for_size"].
    """
    blob = _serialize(doc)
    if len(blob) <= MAX_JSON_BYTES:
        return blob

    for threshold in (2, 4, 8, 16):
        before = len(doc["imm_offsets"])
        doc["imm_offsets"] = [r for r in doc["imm_offsets"] if abs(r["imm"]) > threshold]
        dropped = before - len(doc["imm_offsets"])
        if dropped:
            doc["stats"]["dropped_for_size"][f"imm_offsets_abs_imm_lte_{threshold}"] = dropped
            doc["stats"]["imm_offsets"] = len(doc["imm_offsets"])
        blob = _serialize(doc)
        if len(blob) <= MAX_JSON_BYTES:
            break
    return blob


def write_xrefs(doc: dict) -> int:
    """Serialize + write `doc` to XREFS_JSON; returns the byte size written."""
    blob = _shrink_to_fit(doc)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    XREFS_JSON.write_bytes(blob)
    return len(blob)


# --------------------------------------------------------------------------
# Reverse-lookup helpers
# --------------------------------------------------------------------------

_XREFS_CACHE: dict | None = None
_CACHE_PATH: Path | None = None


def _ensure_doc(doc: dict | None, path: Path | str | None) -> dict:
    """Return `doc` unchanged if given; otherwise lazily load (and cache)
    xrefs.json from `path` (defaults to XREFS_JSON). This is what lets a
    later tool stage just `from xref_db import xrefs_to_value` and call it
    with a bare address, no db object to carry around.
    """
    global _XREFS_CACHE, _CACHE_PATH
    if doc is not None:
        return doc
    resolved = Path(path) if path is not None else XREFS_JSON
    if _XREFS_CACHE is None or _CACHE_PATH != resolved:
        with open(resolved, "r", encoding="utf-8") as f:
            _XREFS_CACHE = json.load(f)
        _CACHE_PATH = resolved
    return _XREFS_CACHE


def _as_int(addr: int | str) -> int:
    return addr if isinstance(addr, int) else int(addr, 16)


def xrefs_to_value(
    addr: int | str, doc: dict | None = None, path: Path | str | None = None
) -> list[dict]:
    """Every literal_loads record whose resolved pool VALUE == addr."""
    d = _ensure_doc(doc, path)
    target = _as_int(addr)
    return [r for r in d["literal_loads"] if int(r["value"], 16) == target]


def funcs_touching_offset(
    imm: int,
    mnemonics: set[str] | list[str] | None = None,
    doc: dict | None = None,
    path: Path | str | None = None,
) -> list[dict]:
    """Every imm_offsets record with that exact immediate (optionally
    restricted to a set of mnemonics, e.g. {"ldrb", "strb"})."""
    d = _ensure_doc(doc, path)
    mset = set(mnemonics) if mnemonics else None
    return [
        r
        for r in d["imm_offsets"]
        if r["imm"] == imm and (mset is None or r["mnemonic"] in mset)
    ]


def nearest_literal_values(
    addr: int | str, n: int = 5, doc: dict | None = None, path: Path | str | None = None
) -> list[tuple[int, dict]]:
    """The `n` literal_loads records whose value is numerically closest to
    `addr`, as (abs_distance, record) pairs sorted ascending by distance.
    """
    d = _ensure_doc(doc, path)
    target = _as_int(addr)
    scored = [
        (abs(int(r["value"], 16) - target), r) for r in d["literal_loads"]
    ]
    scored.sort(key=lambda t: t[0])
    return scored[:n]


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------


def _load_cheat_addresses() -> list[int]:
    if not CHEAT_ADDRESSES_JSON.exists():
        return []
    with open(CHEAT_ADDRESSES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    out: list[int] = []
    seen: set[int] = set()
    for code in data.get("codes", []):
        for entry in code.get("addresses", []):
            addr_field = entry.get("address")
            if not addr_field:
                continue
            try:
                v = int(addr_field, 16)
            except (TypeError, ValueError):
                continue
            if _RAM_LO <= v <= _RAM_HI and v not in seen:
                seen.add(v)
                out.append(v)
    return out


def _check_ac_a(doc: dict) -> bool:
    hits = xrefs_to_value(COLLISION_TABLE_ADDR, doc=doc)
    if hits:
        sample = ", ".join(
            f"{h['insn_addr']}({h['provenance']})->pool {h['pool_addr']}" for h in hits[:5]
        )
        print(
            f"[PASS] a. xrefs_to_value(0x{COLLISION_TABLE_ADDR:08X}) "
            f"returned {len(hits)} hit(s): {sample}"
        )
        return True

    # Caveat fallback: nearest literal value(s) below the table address,
    # checked for base+offset arithmetic reconstructing it.
    candidates = [
        (COLLISION_TABLE_ADDR - int(r["value"], 16), r)
        for r in doc["literal_loads"]
        if 0 <= COLLISION_TABLE_ADDR - int(r["value"], 16) <= 0x1000
    ]
    candidates.sort(key=lambda t: t[0])
    if candidates:
        diff, rec = candidates[0]
        print(
            f"[near-miss] a. no direct hit; closest literal below target is "
            f"{rec['value']} (diff 0x{diff:X}) loaded at {rec['insn_addr']} "
            f"({rec['provenance']}) -- NOT independently verified against "
            f"disasm text arithmetic, so this does not count as a pass."
        )
    nearest = nearest_literal_values(COLLISION_TABLE_ADDR, n=5, doc=doc)
    for dist, rec in nearest:
        print(f"    nearest literal: {rec['value']} (dist 0x{dist:X}) @ {rec['insn_addr']}")
    print(f"[FAIL] a. xrefs_to_value(0x{COLLISION_TABLE_ADDR:08X}) returned 0 hits")
    return False


def _check_ac_b(doc: dict) -> bool:
    hits_78 = funcs_touching_offset(0x78, doc=doc)
    hits_98 = funcs_touching_offset(0x98, doc=doc)
    ok = len(hits_78) >= 1 and len(hits_98) >= 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] b. funcs_touching_offset(0x78)={len(hits_78)} hit(s), "
        f"funcs_touching_offset(0x98)={len(hits_98)} hit(s)"
    )
    if hits_78:
        r = hits_78[0]
        print(f"    e.g. {r['insn_addr']} {r['mnemonic']} [{r['base_reg']}, #0x78] ({r['provenance']})")
    if hits_98:
        r = hits_98[0]
        print(f"    e.g. {r['insn_addr']} {r['mnemonic']} [{r['base_reg']}, #0x98] ({r['provenance']})")
    return ok


def _check_ac_c(doc: dict) -> bool:
    cheat_addrs = _load_cheat_addresses()
    if not cheat_addrs:
        print("[FAIL] c. no in-range cheat addresses found in cheat_addresses.json")
        return False

    for addr in cheat_addrs:
        hits = xrefs_to_value(addr, doc=doc)
        if hits:
            h = hits[0]
            print(
                f"[PASS] c. cheat address 0x{addr:08X} has a direct xrefs_to_value hit: "
                f"loaded at {h['insn_addr']} ({h['provenance']}) from pool {h['pool_addr']}"
            )
            return True
        nearest = nearest_literal_values(addr, n=1, doc=doc)
        if nearest and nearest[0][0] <= 0x100:
            dist, rec = nearest[0]
            print(
                f"[PASS] c. cheat address 0x{addr:08X} has a literal-load value within "
                f"+/-0x100: {rec['value']} (dist 0x{dist:X}) @ {rec['insn_addr']} "
                f"({rec['provenance']})"
            )
            return True

    addr = cheat_addrs[0]
    print(f"[FAIL] c. no cheat address matched at all; nearest literals to 0x{addr:08X}:")
    for dist, rec in nearest_literal_values(addr, n=5, doc=doc):
        print(f"    {rec['value']} (dist 0x{dist:X}) @ {rec['insn_addr']} ({rec['provenance']})")
    return False


def _check_ac_d(doc: dict) -> bool:
    n_lit = len(doc["literal_loads"])
    n_imm = len(doc["imm_offsets"])
    n_br = len(doc["branches"])
    ok = n_lit >= LITERAL_LOADS_MIN and n_imm >= IMM_OFFSETS_MIN and n_br >= BRANCHES_MIN
    print(
        f"[{'PASS' if ok else 'FAIL'}] d. record counts: literal_loads={n_lit} "
        f"(>= {LITERAL_LOADS_MIN}), imm_offsets={n_imm} (>= {IMM_OFFSETS_MIN}), "
        f"branches={n_br} (>= {BRANCHES_MIN})"
    )
    return ok


def _check_ac_e(elapsed: float) -> bool:
    ok = elapsed < 600
    print(f"[{'PASS' if ok else 'FAIL'}] e. build wall time < 10 min (elapsed {elapsed:.1f}s)")
    return ok


def run_selftest(doc: dict, elapsed: float) -> bool:
    results = [
        _check_ac_a(doc),
        _check_ac_b(doc),
        _check_ac_c(doc),
        _check_ac_d(doc),
        _check_ac_e(elapsed),
    ]
    return all(results)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _print_summary(doc: dict, json_bytes: int) -> None:
    stats = doc["stats"]
    print("=== xref_db.py summary ===")
    print(f"literal_loads: {stats['literal_loads']}")
    print(f"imm_offsets:   {stats['imm_offsets']}")
    print(f"branches:      {stats['branches']}")
    print(f"regions swept: {stats['regions_swept']}")
    print(f"instructions scanned: {stats['total_instructions_scanned']}")
    print(f"skipped (literal pool target outside region): {stats['skipped_literal_pool_out_of_region']}")
    print(f"skipped (imm offset == 0): {stats['skipped_imm_offset_zero']}")
    if stats["dropped_for_size"]:
        print(f"dropped for size budget: {stats['dropped_for_size']}")
    print(f"xrefs.json size: {json_bytes} bytes ({json_bytes / (1024 * 1024):.2f} MiB)")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-reference database builder for the FTC NDS ROM "
        "(literal loads, struct-offset immediates, direct branches)."
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
        help="Run the mechanical acceptance selftest suite; exit 0 only if "
        "all checks pass.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    t0 = time.time()
    mm, analyses, sweep_elapsed = run_sweep(args.rom_dir)
    doc = build_xrefs(mm, analyses)
    build_elapsed = time.time() - t0
    doc["stats"]["sweep_elapsed_seconds"] = round(sweep_elapsed, 2)
    doc["stats"]["build_elapsed_seconds"] = round(build_elapsed, 2)

    json_bytes = write_xrefs(doc)

    # Invalidate the module-level lazy cache so any subsequent call to the
    # reverse-lookup helpers with no explicit doc= picks up what was just
    # written rather than a stale prior load.
    global _XREFS_CACHE, _CACHE_PATH
    _XREFS_CACHE = None
    _CACHE_PATH = None

    if args.selftest:
        ok = run_selftest(doc, build_elapsed)
        _print_summary(doc, json_bytes)
        return 0 if ok else 1

    _print_summary(doc, json_bytes)
    print(f"wrote {XREFS_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
