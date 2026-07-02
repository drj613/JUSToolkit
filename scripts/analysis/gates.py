#!/usr/bin/env python3
"""
Gate-runner script for NDS static reverse-engineering toolchain.
Validates G1-G4 (tool selftests) and G5 (anchor plausibility).
Updates gates object in loop-state.json.
"""

import json
import subprocess
import sys
import re
import argparse
from pathlib import Path


def run_selftest(tool_path, timeout=600):
    """Run a tool's --selftest. Return (exit_code, tool_name)."""
    tool_name = Path(tool_path).stem.upper()
    try:
        result = subprocess.run(
            [sys.executable, tool_path, "--selftest"],
            capture_output=True,
            timeout=timeout,
            cwd=Path.cwd(),
        )
        return (result.returncode, tool_name)
    except subprocess.TimeoutExpired:
        return (1, tool_name)  # Timeout = fail
    except Exception as e:
        print(f"Error running {tool_path}: {e}", file=sys.stderr)
        return (1, tool_name)


def check_anchor_plausibility(query_py, timeout=600):
    """
    Gate G5: Run disasm query and validate output.
    Returns (pass: bool, lines_checked: list, data_processing_lines: list)
    """
    try:
        result = subprocess.run(
            [sys.executable, query_py, "disasm", "0x020784FC", "12"],
            capture_output=True,
            timeout=timeout,
            text=True,
            cwd=Path.cwd(),
        )

        lines = result.stdout.strip().split('\n')

        # Filter to instruction lines only (skip comments)
        instr_lines = [
            line for line in lines
            if line.strip() and line.startswith('0x')
        ]

        # Check line count requirement
        if len(instr_lines) < 10:
            return (False, instr_lines, [])

        # Parse instructions and check for invalid mnemonics
        data_processing_lines = []
        data_proc_pattern = re.compile(
            r'\b(add|sub|mov|cmp|and|orr|eor|rsb|mul|lsl|lsr)([a-z]{0,2})\b'
        )

        for line in instr_lines:
            # Extract mnemonic from format "0x<ADDR>: <hexbytes>  <mnemonic> <ops>"
            parts = line.split()
            if len(parts) >= 3:
                mnemonic = parts[2]

                # Check for forbidden mnemonics
                if mnemonic in ('.word', 'udf'):
                    return (False, instr_lines, [])

                # Check for data-processing mnemonics
                if data_proc_pattern.match(mnemonic):
                    data_processing_lines.append(line)

        # Check data-processing requirement
        if len(data_processing_lines) < 2:
            return (False, instr_lines, data_processing_lines)

        return (True, instr_lines, data_processing_lines)

    except subprocess.TimeoutExpired:
        return (False, [], [])
    except Exception as e:
        print(f"Error running gate G5: {e}", file=sys.stderr)
        return (False, [], [])


def update_gates_state(state_path, gates_results, dry_run=False):
    """
    Read JSON, update gates object, write back (unless dry_run).
    gates_results: dict of gate_name -> "pass" or "fail"
    Preserves original formatting by replacing only the gates line.
    """
    with open(state_path, 'r') as f:
        content = f.read()

    with open(state_path, 'r') as f:
        state = json.load(f)

    # Update only the gates object
    for gate_name, result in gates_results.items():
        state['gates'][gate_name] = result

    if not dry_run:
        # Build gates line preserving 2-space indent and formatting
        gates_json = json.dumps(state['gates'], separators=(', ', ': '))
        gates_line = f'  "gates": {gates_json},'

        # Replace the gates line in content
        import re as re_module
        new_content = re_module.sub(
            r'  "gates": \{[^}]+\},',
            gates_line,
            content
        )

        with open(state_path, 'w') as f:
            f.write(new_content)

    return state


def main():
    parser = argparse.ArgumentParser(
        description="Gate-runner for NDS static RE toolchain"
    )
    parser.add_argument(
        '--state',
        default='scripts/analysis/loop-state.json',
        help='Path to loop-state.json'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Do not write state, just print'
    )
    args = parser.parse_args()

    state_path = Path(args.state)
    analysis_dir = state_path.parent

    # Define tools and their gate numbers
    tools = [
        ('G1', analysis_dir / 'rom_loader.py'),
        ('G2', analysis_dir / 'disasm_db.py'),
        ('G3', analysis_dir / 'xref_db.py'),
        ('G4', analysis_dir / 'query.py'),
    ]

    gates_results = {}
    exit_codes = {}

    # Run G1-G4 selftests
    for gate_name, tool_path in tools:
        exit_code, tool_name = run_selftest(tool_path)
        exit_codes[gate_name] = exit_code
        gates_results[gate_name] = 'pass' if exit_code == 0 else 'fail'

    # Run G5 anchor plausibility check
    g5_pass, instr_lines, data_proc_lines = check_anchor_plausibility(
        analysis_dir / 'query.py'
    )
    gates_results['G5'] = 'pass' if g5_pass else 'fail'
    exit_codes['G5'] = 0 if g5_pass else 1

    # Update state
    update_gates_state(state_path, gates_results, dry_run=args.dry_run)

    # Print summary table
    print("\n" + "="*70)
    print(f"{'Gate':<8} {'Tool':<20} {'Exit Code':<12} {'Result':<10}")
    print("="*70)

    tool_map = {g: p.stem for g, p in tools}
    for gate_name in ['G1', 'G2', 'G3', 'G4', 'G5']:
        tool_name = tool_map.get(gate_name, 'anchor_plausibility')
        result = gates_results[gate_name]
        exit_code = exit_codes[gate_name]
        print(f"{gate_name:<8} {tool_name:<20} {exit_code:<12} {result:<10}")

    print("="*70)

    # Print G5 details if requested
    if 'G5' in gates_results:
        if gates_results['G5'] == 'pass':
            print(f"\nG5 anchor plausibility: PASS")
            print(f"  Instructions parsed: {len(instr_lines)}")
            print(f"  Data-processing lines with valid mnemonic:")
            for line in data_proc_lines:
                print(f"    {line}")
        else:
            print(f"\nG5 anchor plausibility: FAIL")
            if instr_lines:
                print(f"  Instructions parsed: {len(instr_lines)} (need >= 10)")
            else:
                print(f"  Could not parse instruction output")
            if data_proc_lines:
                print(f"  Data-processing lines found: {len(data_proc_lines)} (need >= 2)")

    print()

    # Exit with appropriate code
    all_pass = all(v == 'pass' for v in gates_results.values())
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
