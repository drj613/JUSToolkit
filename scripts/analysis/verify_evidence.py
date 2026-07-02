#!/usr/bin/env python3
"""verify_evidence.py - the anti-hallucination evidence verifier for the FTC
(Jump Ultimate Stars) NDS static reverse-engineering toolchain.

Downstream "tracer" agents submit findings JSON files that cite disassembly
quotes as evidence for claims about the game's code. This tool is the
project's defense against fabricated evidence: it machine-checks every
quoted instruction against the *actual* disassembly database and rejects
the whole file on any mismatch whatsoever. Strictness beats leniency on
every tradeoff here -- a claim with even one bad quote is worthless, so one
bad segment sinks the entire file.

The ONLY source of disassembly ground truth this tool trusts is a real,
separate subprocess invocation of query.py's `disasm` subcommand (never an
import of its internals, never a cached/mocked value): that keeps this
verifier independent of query.py's in-process state and matches how a human
reviewer would double-check a citation by hand.

    scripts/analysis/.venv/bin/python scripts/analysis/query.py \\
        disasm <addr> <n> [--overlay ovN]

CLI:
    verify_evidence.py <findings.json>
    verify_evidence.py --selftest

Exit codes:
    0   findings file ACCEPTED (or --selftest: every case behaved as spec'd)
    1   findings file REJECTED (or --selftest: some case misbehaved)
    2   usage error (bad CLI arguments)

Findings schema (one JSON file per run) -- see module-level docstring in the
task spec / README for the authoritative version; the short form:

    {
      "subsystem": "...", "round": 1,
      "claims": [
        {
          "claim": "prose statement",
          "addresses": ["0x0207850C", ...],
          "provenance": "arm9" | "ov<N>",   # required iff any address is
                                             # ambiguous without it
          "evidence_disasm": "0x...: ... | 0x...: ...",
          "confidence": "CONFIRMED_STATIC" | "PLAUSIBLE" | "SPECULATIVE",
          "gdb_check": "...",               # required for PLAUSIBLE/SPECULATIVE
          "open_questions": []
        }
      ],
      "no_progress_reason": null,
      "suggested_next_angles": []
    }

If `claims` is empty, `no_progress_reason` must be a non-empty string and
`suggested_next_angles` must be a non-empty list instead.

Verification algorithm (per claim, fail fast on the FIRST problem found,
which rejects the ENTIRE file):
  1. Schema check (claim/addresses/evidence_disasm/confidence/gdb_check).
  2. Parse `evidence_disasm` into " | "-separated segments, each of the
     form "0x<HEX>: <text>" with len(text) >= 4.
  3. For each segment, resolve its address via a real `query.py disasm
     <addr> 1 [--overlay <provenance>]` call and compare, whitespace/case
     -normalized, against the quoted text (substring match, so a segment
     may quote either "<hexbytes> <mnemonic ops>" or just "<mnemonic
     ops>"). Any mismatch (text OR address) rejects the whole file. If the
     address is ambiguous (overlay-shared) and no `provenance` was given,
     that is also a rejection, with a message pointing at the fix.
  4. Every address in `claim.addresses` must be backed by at least one
     verified evidence segment citing that exact address.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

# --------------------------------------------------------------------------
# Paths -- resolved relative to this file so the tool works from any cwd.
# --------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
QUERY_PY = _SCRIPT_DIR / "query.py"
VENV_PYTHON = _SCRIPT_DIR / ".venv" / "bin" / "python"

# --------------------------------------------------------------------------
# Constants / patterns
# --------------------------------------------------------------------------

CONFIDENCE_LEVELS = {"CONFIRMED_STATIC", "PLAUSIBLE", "SPECULATIVE"}
GDB_CHECK_REQUIRED_FOR = {"PLAUSIBLE", "SPECULATIVE"}

ADDR_HEX_RE = re.compile(r"^0x[0-9A-Fa-f]+$")
# "0x<HEX>: <text>" -- text captured greedily, length-checked by the caller.
SEGMENT_RE = re.compile(r"^0x([0-9A-Fa-f]+):\s*(.+)$")
# An actual query.py disasm output line: "0x<8-hex>: <hexbytes>  <mnemonic ops>"
LINE_RE = re.compile(r"^0x([0-9A-Fa-f]+):\s*(.*)$")
# A provenance value that is a bare overlay spec: "ov3", "OV3", or "3".
PROVENANCE_OV_RE = re.compile(r"^(?:ov)?(\d+)$", re.IGNORECASE)

MIN_SEGMENT_TEXT_LEN = 4

# Batch-fetch tuning: only ever a *performance* optimization -- correctness
# is enforced by re-checking every returned line's own address before using
# it, and anything not found in a batch falls back to an individual,
# authoritative single-address query.
MAX_BATCH_SPAN = 4096
MAX_BATCH_LINES = 2048

# Real, independently-verifiable anchors used by --selftest (never
# hardcoded expected *output* -- only addresses to build fixtures from,
# same spirit as query.py's own --selftest anchors).
_SELFTEST_FUNC_ANCHOR = 0x020784E4  # arm9, push {r4, lr}, unambiguous
_SELFTEST_OVERLAP_BASE = 0x0214CD20  # ov0-ov9 shared RAM base, ambiguous


# --------------------------------------------------------------------------
# query.py subprocess wrapper
# --------------------------------------------------------------------------


def run_disasm(addr: int, n: int, overlay: str | None = None) -> tuple[int, str, str]:
    """Invoke `query.py disasm <addr> <n> [--overlay <overlay>]` as a real
    subprocess and return (returncode, stdout, stderr). This is the ONLY
    function in this file that touches disassembly ground truth.
    """
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    cmd = [python, str(QUERY_PY), "disasm", f"0x{addr:X}", str(n)]
    if overlay:
        cmd += ["--overlay", overlay]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError as exc:
        return 127, "", f"failed to invoke query.py: {exc}"
    except subprocess.TimeoutExpired:
        return 124, "", f"query.py timed out after 60s: {' '.join(cmd)}"
    return proc.returncode, proc.stdout, proc.stderr


def _lines_by_addr(stdout: str) -> dict[int, str]:
    got: dict[int, str] = {}
    for line in stdout.splitlines():
        m = LINE_RE.match(line)
        if m:
            got[int(m.group(1), 16)] = line
    return got


class DisasmCache:
    """Memoizes (addr, overlay) -> (returncode, line_or_None, stderr) across
    the whole verification run, so a repeated citation of the same address
    never triggers a second subprocess call. Also opportunistically batches
    a group of nearby same-overlay addresses into a single ranged
    `disasm` call; any address the batch doesn't cover falls back to an
    individual, authoritative call, so batching can never change the
    result -- only how many subprocess calls it takes to get there.
    """

    def __init__(self) -> None:
        self._cache: dict[tuple[int, str | None], tuple[int, str | None, str]] = {}

    def get(self, addr: int, overlay: str | None) -> tuple[int, str | None, str]:
        return self._cache[(addr, overlay)]

    def resolve_many(self, addrs: list[int], overlay: str | None) -> None:
        need = sorted({a for a in addrs if (a, overlay) not in self._cache})
        if not need:
            return

        if len(need) > 1 and (need[-1] - need[0]) <= MAX_BATCH_SPAN:
            lo = need[0]
            n_guess = min(MAX_BATCH_LINES, (need[-1] - lo) // 2 + 4)
            rc, out, _err = run_disasm(lo, n_guess, overlay)
            if rc == 0:
                got = _lines_by_addr(out)
                for a in need:
                    if a in got:
                        self._cache[(a, overlay)] = (0, got[a], "")
            # else: the batch attempt itself failed (e.g. ambiguous, out of
            # range, misaligned) -- ignore it entirely and let the
            # individual per-address queries below surface the real error
            # for whichever address actually needs it.

        for a in need:
            if (a, overlay) in self._cache:
                continue
            rc, out, err = run_disasm(a, 1, overlay)
            line = None
            if rc == 0:
                lines = _lines_by_addr(out)
                line = lines.get(a)
            self._cache[(a, overlay)] = (rc, line, err)


def overlay_arg_for(provenance: str) -> str | None:
    """Return the --overlay value to pass to query.py for this claim's
    `provenance`, or None to call disasm with no --overlay flag at all.

    'arm9' (never ambiguous) maps to None. 'ov3' / 'OV3' / '3' all map to
    the canonical 'ov3'. Anything else is not a recognized provenance and
    raises ValueError (the caller turns that into a REJECT).
    """
    p = provenance.strip()
    if p.lower() == "arm9":
        return None
    m = PROVENANCE_OV_RE.match(p)
    if m:
        return f"ov{int(m.group(1))}"
    raise ValueError(
        f"provenance {provenance!r} is neither 'arm9' nor a valid overlay "
        f"spec ('ovN' or 'N')"
    )


# --------------------------------------------------------------------------
# Text normalization / matching
# --------------------------------------------------------------------------


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def segment_matches(seg_addr: int, seg_text: str, actual_line: str) -> tuple[bool, str]:
    """Compare one evidence segment against the real `disasm` output line
    query.py returned for that same address. Returns (ok, reason).
    """
    m = LINE_RE.match(actual_line)
    if not m:
        return False, f"actual disasm line has unexpected format: {actual_line!r}"
    actual_addr = int(m.group(1), 16)
    if actual_addr != seg_addr:
        return False, (
            f"address mismatch: evidence cites 0x{seg_addr:08X} but query.py "
            f"returned the line for 0x{actual_addr:08X}"
        )
    norm_evidence = normalize(seg_text)
    norm_actual = normalize(m.group(2))
    if norm_evidence not in norm_actual:
        return False, "quoted text does not substring-match the actual disassembly"
    return True, ""


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------


class Rejected(Exception):
    """Carries the human-readable rejection report (one or more lines)."""

    def __init__(self, lines: list[str]):
        self.lines = lines
        super().__init__(lines[0] if lines else "rejected")


def _check_top_schema(data: object) -> list:
    if not isinstance(data, dict):
        raise Rejected(["REJECT: top-level JSON must be an object"])

    claims = data.get("claims")
    if claims is None or not isinstance(claims, list):
        raise Rejected(["REJECT: 'claims' field must be present and be a list"])

    if len(claims) == 0:
        npr = data.get("no_progress_reason")
        sna = data.get("suggested_next_angles")
        if not (isinstance(npr, str) and npr.strip()):
            raise Rejected(
                [
                    "REJECT: 'claims' is empty, which requires a non-empty string "
                    "'no_progress_reason', but it is missing/empty "
                    f"(got {npr!r})"
                ]
            )
        if not (isinstance(sna, list) and len(sna) > 0):
            raise Rejected(
                [
                    "REJECT: 'claims' is empty, which requires a non-empty list "
                    "'suggested_next_angles', but it is missing/empty "
                    f"(got {sna!r})"
                ]
            )
    return claims


def _parse_segments(label: str, evidence_disasm: str) -> list[tuple[int, int, str, str]]:
    """Split evidence_disasm on ' | ' and validate each segment's shape.
    Returns a list of (segment_number, addr, text, raw_segment_string).
    """
    segments: list[tuple[int, int, str, str]] = []
    raw_segments = evidence_disasm.split(" | ")
    for seg_idx, raw_seg in enumerate(raw_segments, start=1):
        m = SEGMENT_RE.match(raw_seg)
        if not m:
            raise Rejected(
                [
                    f"REJECT: {label} segment {seg_idx}: does not match the "
                    f"required '0x<HEX>: <text>' shape: {raw_seg!r}"
                ]
            )
        seg_addr_str, seg_text_raw = m.group(1), m.group(2)
        seg_text = seg_text_raw.strip()
        if len(seg_text) < MIN_SEGMENT_TEXT_LEN:
            raise Rejected(
                [
                    f"REJECT: {label} segment {seg_idx}: quoted text is too short "
                    f"(< {MIN_SEGMENT_TEXT_LEN} chars): {raw_seg!r}"
                ]
            )
        try:
            seg_addr = int(seg_addr_str, 16)
        except ValueError:
            raise Rejected(
                [f"REJECT: {label} segment {seg_idx}: invalid hex address {seg_addr_str!r}"]
            ) from None
        segments.append((seg_idx, seg_addr, seg_text, raw_seg))
    return segments


def _verify_claim(idx: int, claim: object, cache: DisasmCache) -> None:
    label = f"claim {idx}"

    if not isinstance(claim, dict):
        raise Rejected([f"REJECT: {label} is not a JSON object"])

    claim_text = claim.get("claim")
    if not isinstance(claim_text, str) or not claim_text.strip():
        raise Rejected([f"REJECT: {label}: missing or empty 'claim' field"])

    addresses = claim.get("addresses")
    if not isinstance(addresses, list) or len(addresses) == 0:
        raise Rejected([f"REJECT: {label}: 'addresses' must be a non-empty list"])
    parsed_claim_addrs: list[tuple[str, int]] = []
    for a in addresses:
        if not isinstance(a, str) or not ADDR_HEX_RE.match(a):
            raise Rejected([f"REJECT: {label}: address {a!r} is not valid 0x-hex"])
        parsed_claim_addrs.append((a, int(a, 16)))

    confidence = claim.get("confidence")
    if confidence not in CONFIDENCE_LEVELS:
        raise Rejected(
            [
                f"REJECT: {label}: 'confidence' must be one of "
                f"{sorted(CONFIDENCE_LEVELS)}, got {confidence!r}"
            ]
        )

    if confidence in GDB_CHECK_REQUIRED_FOR:
        gdb_check = claim.get("gdb_check")
        if not isinstance(gdb_check, str) or not gdb_check.strip():
            raise Rejected(
                [
                    f"REJECT: {label}: 'gdb_check' must be a non-empty string when "
                    f"confidence={confidence}"
                ]
            )

    evidence_disasm = claim.get("evidence_disasm")
    if not isinstance(evidence_disasm, str) or not evidence_disasm.strip():
        raise Rejected([f"REJECT: {label}: 'evidence_disasm' must be a non-empty string"])

    segments = _parse_segments(label, evidence_disasm)

    # Resolve claim-level provenance -> the --overlay value (if any) to use
    # for every segment in this claim.
    overlay: str | None = None
    provenance = claim.get("provenance")
    if provenance is not None:
        if not isinstance(provenance, str) or not provenance.strip():
            raise Rejected(
                [f"REJECT: {label}: 'provenance' must be a non-empty string when present"]
            )
        try:
            overlay = overlay_arg_for(provenance)
        except ValueError as exc:
            raise Rejected([f"REJECT: {label}: {exc}"]) from None

    cache.resolve_many([seg_addr for _, seg_addr, _, _ in segments], overlay)

    for seg_idx, seg_addr, seg_text, raw_seg in segments:
        rc, line, err = cache.get(seg_addr, overlay)
        if rc != 0 or line is None:
            hint = ""
            if provenance is None and err and (
                "ambiguous" in err.lower() or "candidate" in err.lower()
            ):
                hint = (
                    " -- this address is AMBIGUOUS across overlapping overlays; "
                    "add a claim-level \"provenance\": \"ovN\" field to disambiguate"
                )
            overlay_desc = f" --overlay {overlay}" if overlay else ""
            raise Rejected(
                [
                    f"REJECT: {label} segment {seg_idx}: `query.py disasm "
                    f"0x{seg_addr:08X} 1{overlay_desc}` failed (exit={rc}){hint}",
                    f"  evidence quoted : {raw_seg!r}",
                    f"  query.py stderr : {err.strip()}",
                ]
            )

        ok, why = segment_matches(seg_addr, seg_text, line)
        if not ok:
            raise Rejected(
                [
                    f"REJECT: {label} segment {seg_idx}: {why}",
                    f"  expected (evidence) : {raw_seg!r}",
                    f"  actual   (query.py) : {line!r}",
                ]
            )

    verified_addrs = {seg_addr for _, seg_addr, _, _ in segments}
    for a_str, a_int in parsed_claim_addrs:
        if a_int not in verified_addrs:
            raise Rejected(
                [
                    f"REJECT: {label}: address {a_str} is listed in 'addresses' but "
                    f"is not backed by any quoted segment in 'evidence_disasm'"
                ]
            )

    print(f"OK {label} ({len(segments)} segments verified)")


def verify_path(path: Path) -> int:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"REJECT: cannot read {path}: {exc}", file=sys.stderr)
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"REJECT: {path} is not valid JSON: {exc}", file=sys.stderr)
        return 1

    try:
        claims = _check_top_schema(data)
    except Rejected as exc:
        for line in exc.lines:
            print(line, file=sys.stderr)
        return 1

    if not claims:
        print(
            "OK: 'claims' is empty but 'no_progress_reason' and "
            "'suggested_next_angles' are both valid"
        )
        return 0

    cache = DisasmCache()
    try:
        for idx, claim in enumerate(claims, start=1):
            _verify_claim(idx, claim, cache)
    except Rejected as exc:
        for line in exc.lines:
            print(line, file=sys.stderr)
        return 1

    return 0


# --------------------------------------------------------------------------
# --selftest
# --------------------------------------------------------------------------


REAL_LINE_SPLIT_RE = re.compile(r"^0x([0-9A-Fa-f]+):\s*(\S+)\s+(.*)$")


def _split_real_line(line: str) -> tuple[int, str, str]:
    """Split a verbatim query.py disasm output line into
    (addr, hexbytes_token, rest_of_line)."""
    m = REAL_LINE_SPLIT_RE.match(line)
    if not m:
        raise RuntimeError(f"unexpected disasm line format: {line!r}")
    return int(m.group(1), 16), m.group(2), m.group(3)


def _tamper_operand(raw_segment: str) -> str:
    """Given a real, currently-correct '0xADDR: text' segment, change
    exactly one operand-shaped token so the text stops matching the real
    disassembly, while leaving the address untouched."""
    m = SEGMENT_RE.match(raw_segment)
    assert m is not None
    addr_part, text = m.group(1), m.group(2)

    new_text, n = re.subn(r"\br0\b", "r7", text, count=1)
    if n == 0:
        new_text, n = re.subn(r"\br1\b", "r8", text, count=1)
    if n == 0:
        new_text, n = re.subn(
            r"#0x([0-9a-fA-F]+)",
            lambda mo: f"#0x{int(mo.group(1), 16) ^ 1:x}",
            text,
            count=1,
        )
    if n == 0:
        new_text, n = re.subn(
            r"#(\d+)\b", lambda mo: f"#{int(mo.group(1)) + 1}", text, count=1
        )
    if n == 0:
        # Last-resort fallback: flip the last nibble of a leading hexbytes
        # token, which is present on every "full" segment.
        def _flip(mo: re.Match) -> str:
            tok = mo.group(1)
            last = tok[-1]
            return tok[:-1] + ("0" if last != "0" else "1")

        new_text, n = re.subn(r"^([0-9a-fA-F]{8})\b", _flip, text, count=1)
    if n == 0:
        raise RuntimeError(f"could not find anything to tamper in: {text!r}")
    return f"0x{addr_part}: {new_text}"


def _shift_segment_addr(raw_segment: str, delta: int) -> str:
    m = SEGMENT_RE.match(raw_segment)
    assert m is not None
    addr = int(m.group(1), 16) + delta
    return f"0x{addr:08X}: {m.group(2)}"


def _invoke(argv: list[str]) -> tuple[int, str, str]:
    """Run `main(argv)` in-process, capturing stdout/stderr, normalizing
    SystemExit into a return code (mirrors query.py's own `_invoke`)."""
    out, err = io.StringIO(), io.StringIO()
    code = 0
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


def run_selftest() -> bool:
    all_ok = True

    def check(ok: bool, label: str) -> None:
        nonlocal all_ok
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")

    with tempfile.TemporaryDirectory(prefix="verify_evidence_selftest_") as tmp:
        tmp_path = Path(tmp)

        # ---------------------------------------------------------------
        # a. Build a VALID fixture from real disasm output and ACCEPT it.
        # ---------------------------------------------------------------
        rc, out, err = run_disasm(_SELFTEST_FUNC_ANCHOR, 6)
        base_findings: dict | None = None
        if rc != 0 or len(out.splitlines()) < 3:
            check(
                False,
                f"a. could not fetch real disasm lines to build fixture "
                f"(exit={rc}): {err.strip()}",
            )
        else:
            chosen = out.splitlines()[:3]
            parsed = [_split_real_line(l) for l in chosen]
            seg_strs = []
            for i, (addr, hexb, rest) in enumerate(parsed):
                if i == 1:
                    seg_strs.append(f"0x{addr:08X}: {rest}")  # mnemonic-only path
                else:
                    seg_strs.append(f"0x{addr:08X}: {hexb}  {rest}")  # hexbytes kept
            base_findings = {
                "subsystem": "selftest",
                "round": 1,
                "claims": [
                    {
                        "claim": "selftest fixture: valid quoted disassembly",
                        "addresses": [f"0x{addr:08X}" for addr, _, _ in parsed],
                        "evidence_disasm": " | ".join(seg_strs),
                        "confidence": "CONFIRMED_STATIC",
                        "gdb_check": "",
                        "open_questions": [],
                    }
                ],
                "no_progress_reason": None,
                "suggested_next_angles": [],
            }
            valid_path = tmp_path / "a_valid.json"
            valid_path.write_text(json.dumps(base_findings, indent=2))
            code, _vout, verr = _invoke([str(valid_path)])
            check(
                code == 0,
                f"a. valid fixture (real quoted disasm, mixed hexbytes/mnemonic-only) "
                f"accepted (exit={code})" + ("" if code == 0 else f" stderr={verr.strip()!r}"),
            )

        # ---------------------------------------------------------------
        # b. Tamper ONE operand in one segment -> REJECT.
        # ---------------------------------------------------------------
        if base_findings is not None:
            tampered_b = json.loads(json.dumps(base_findings))
            segs_b = tampered_b["claims"][0]["evidence_disasm"].split(" | ")
            segs_b[0] = _tamper_operand(segs_b[0])
            tampered_b["claims"][0]["evidence_disasm"] = " | ".join(segs_b)
            path_b = tmp_path / "b_tampered_operand.json"
            path_b.write_text(json.dumps(tampered_b, indent=2))
            code, _o, _e = _invoke([str(path_b)])
            check(code != 0, f"b. tampered operand rejected (exit={code})")
        else:
            check(False, "b. skipped (no base fixture from case a)")

        # ---------------------------------------------------------------
        # c. Shift one segment's address by +4, keep its text -> REJECT.
        # ---------------------------------------------------------------
        if base_findings is not None:
            tampered_c = json.loads(json.dumps(base_findings))
            segs_c = tampered_c["claims"][0]["evidence_disasm"].split(" | ")
            segs_c[0] = _shift_segment_addr(segs_c[0], 4)
            tampered_c["claims"][0]["evidence_disasm"] = " | ".join(segs_c)
            path_c = tmp_path / "c_tampered_addr.json"
            path_c.write_text(json.dumps(tampered_c, indent=2))
            code, _o, _e = _invoke([str(path_c)])
            check(code != 0, f"c. shifted-address (stale text) segment rejected (exit={code})")
        else:
            check(False, "c. skipped (no base fixture from case a)")

        # ---------------------------------------------------------------
        # d. Overlay ambiguity: without provenance -> REJECT (mentions
        #    overlay/ambiguity); with correct provenance + real text -> ACCEPT.
        # ---------------------------------------------------------------
        rc_ov, out_ov, err_ov = run_disasm(_SELFTEST_OVERLAP_BASE, 1, "ov1")
        if rc_ov != 0:
            check(
                False,
                f"d. could not fetch real ov1 disasm line for fixture "
                f"(exit={rc_ov}): {err_ov.strip()}",
            )
        else:
            ov_addr, ov_hexb, ov_rest = _split_real_line(out_ov.splitlines()[0])
            ov_seg = f"0x{ov_addr:08X}: {ov_hexb}  {ov_rest}"

            findings_no_prov = {
                "subsystem": "selftest",
                "round": 1,
                "claims": [
                    {
                        "claim": "selftest fixture: ambiguous address without provenance",
                        "addresses": [f"0x{ov_addr:08X}"],
                        "evidence_disasm": ov_seg,
                        "confidence": "CONFIRMED_STATIC",
                        "gdb_check": "",
                        "open_questions": [],
                    }
                ],
                "no_progress_reason": None,
                "suggested_next_angles": [],
            }
            path_d1 = tmp_path / "d_no_provenance.json"
            path_d1.write_text(json.dumps(findings_no_prov, indent=2))
            code1, _o1, err1 = _invoke([str(path_d1)])
            ok1 = code1 != 0 and (
                "ambig" in err1.lower() or "overlay" in err1.lower() or "candidate" in err1.lower()
            )
            check(
                ok1,
                f"d1. ambiguous address without provenance rejected, mentions "
                f"overlay/ambiguity (exit={code1})",
            )

            findings_with_prov = json.loads(json.dumps(findings_no_prov))
            findings_with_prov["claims"][0]["provenance"] = "ov1"
            path_d2 = tmp_path / "d_with_provenance.json"
            path_d2.write_text(json.dumps(findings_with_prov, indent=2))
            code2, _o2, err2 = _invoke([str(path_d2)])
            check(
                code2 == 0,
                f"d2. same address WITH provenance=ov1 + real text accepted "
                f"(exit={code2})" + ("" if code2 == 0 else f" stderr={err2.strip()!r}"),
            )

        # ---------------------------------------------------------------
        # e. Structural: empty claims needs no_progress_reason +
        #    suggested_next_angles; without them -> REJECT, with -> ACCEPT.
        # ---------------------------------------------------------------
        bad_empty = {
            "subsystem": "selftest",
            "round": 1,
            "claims": [],
            "no_progress_reason": None,
            "suggested_next_angles": [],
        }
        path_e1 = tmp_path / "e_bad_empty.json"
        path_e1.write_text(json.dumps(bad_empty, indent=2))
        code_e1, _o, _e = _invoke([str(path_e1)])
        check(code_e1 != 0, f"e1. empty claims without no_progress_reason rejected (exit={code_e1})")

        good_empty = {
            "subsystem": "selftest",
            "round": 1,
            "claims": [],
            "no_progress_reason": "no static evidence found for this subsystem in round 1",
            "suggested_next_angles": ["try dynamic tracing with gdb breakpoints"],
        }
        path_e2 = tmp_path / "e_good_empty.json"
        path_e2.write_text(json.dumps(good_empty, indent=2))
        code_e2, _o, err_e2 = _invoke([str(path_e2)])
        check(
            code_e2 == 0,
            f"e2. empty claims WITH no_progress_reason + suggested_next_angles "
            f"accepted (exit={code_e2})" + ("" if code_e2 == 0 else f" stderr={err_e2.strip()!r}"),
        )

    return all_ok


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_evidence.py",
        description=(
            "Machine-check every disassembly quote in a tracer agent's findings "
            "JSON against the real query.py disasm database. Rejects the whole "
            "file on any mismatch, missing provenance for an ambiguous address, "
            "or schema violation."
        ),
        epilog=(
            "Example:\n"
            "  verify_evidence.py findings/damage-pipeline-round1.json\n"
            "  verify_evidence.py --selftest\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "findings_json",
        nargs="?",
        help="Path to a findings JSON file to verify.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help=(
            "Run the built-in, self-generating acceptance tests (no committed "
            "fixtures -- they are built at runtime from real query.py output) "
            "and exit 0 only if every case behaves as specified. Ignores "
            "findings_json."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.selftest:
        return 0 if run_selftest() else 1

    if not args.findings_json:
        parser.print_help(sys.stderr)
        return 2

    return verify_path(Path(args.findings_json))


if __name__ == "__main__":
    sys.exit(main())
