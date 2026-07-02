"""Static memory-map loader for the FTC (Jump Ultimate Stars) NDS ROM.

This module reconstructs the flat NDS ARM9 address space used by the game's
overlay system, purely by reading the ripped ROM files on disk. It performs
no decompression and no emulation: it is a *static* loader for other
reverse-engineering tools (disassemblers, symbol resolvers, etc.) to import.

Inputs (read-only, never modified):
    <rom_dir>/arm9.bin        - the ARM9 main binary, mapped at 0x02000000
    <rom_dir>/y9.bin          - the overlay table (array of 32-byte records)
    <rom_dir>/overlay9_<N>    - one file per overlay table entry, where N is
                                 the entry's file_id

y9.bin record layout (32 bytes, little-endian, 8 x uint32):

    offset  field         meaning
    ------  ------------  --------------------------------------------------
    0x00    overlay_id    logical overlay index
    0x04    ram_addr      address the overlay is loaded to in RAM
    0x08    ram_size      number of bytes loaded from the overlay file
                           (the file's static ROM image may be larger; the
                           .bss tail is not stored on disk)
    0x0C    bss_size      zero-initialized bytes appended after ram_size
    0x10    sinit_start   start address of the static constructor table
    0x14    sinit_end     end address of the static constructor table
    0x18    file_id       index of the overlay9_<file_id> file to load
    0x1C    flags         bits 0-23: compressed size (if compressed);
                           bit 24: 1 if the overlay file is LZ-compressed

This loader does NOT decompress compressed overlays. If the compressed flag
is set, that fact is recorded on the Region (`compressed=True`) but the raw
(still-compressed) file bytes are what gets mapped. Callers that need the
decompressed image must do that themselves.

Reality check versus a naive "two overlays share an address" model: on this
ROM, address collisions are not limited to a single pair of overlays. Groups
of overlays share the exact same ram_addr (they are swapped in and out of
the same RAM window at runtime, e.g. per-character overlays in a fighting
game). The API below is built to support N-way overlap, not just 2-way.

Public API:
    Region           - one mapped byte range with provenance metadata.
    MemoryMap         - collection of Regions with address-lookup helpers.
    load_memory_map() - build a MemoryMap by reading rom_dir from disk.
    AddressNotMappedError, AmbiguousAddressError - lookup failure modes.

CLI:
    rom_loader.py --selftest [--rom-dir PATH]
    rom_loader.py --list     [--rom-dir PATH]
"""

from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

ARM9_BASE = 0x02000000

Y9_ENTRY_SIZE = 32
Y9_ENTRY_STRUCT = struct.Struct("<8I")  # overlay_id, ram_addr, ram_size,
# bss_size, sinit_start, sinit_end, file_id, flags

_COMPRESSED_FLAG_BIT = 24
_COMPRESSED_SIZE_MASK = (1 << 24) - 1

# Two parents up from this script file (scripts/analysis/rom_loader.py):
#   parents[0] = scripts/analysis
#   parents[1] = scripts
#   parents[2] = repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROM_DIR = _REPO_ROOT / "jus_files" / "ripped_jus_files" / "ftc"


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------


class AddressNotMappedError(Exception):
    """Raised when an address (or address+size range) has no mapped region."""

    def __init__(self, addr: int, size: int = 0, message: str | None = None) -> None:
        self.addr = addr
        self.size = size
        if message is None:
            if size:
                message = (
                    f"address 0x{addr:08X} (size {size}) is not mapped by any region"
                )
            else:
                message = f"address 0x{addr:08X} is not mapped by any region"
        super().__init__(message)


class AmbiguousAddressError(Exception):
    """Raised when an address falls inside more than one region and no
    explicit overlay context was given to disambiguate it.

    The offending candidate regions are attached as `.candidates` so callers
    can inspect them (and, e.g., re-issue the read with `overlay=...`).
    """

    def __init__(self, addr: int, candidates: list["Region"]) -> None:
        self.addr = addr
        self.candidates = candidates
        names = ", ".join(sorted(r.name for r in candidates))
        super().__init__(
            f"address 0x{addr:08X} is ambiguous across {len(candidates)} "
            f"overlapping regions: {names} (pass overlay=... to disambiguate)"
        )


# --------------------------------------------------------------------------
# y9.bin parsing
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Y9Entry:
    """One parsed 32-byte record from y9.bin."""

    overlay_id: int
    ram_addr: int
    ram_size: int
    bss_size: int
    sinit_start: int
    sinit_end: int
    file_id: int
    flags: int

    @property
    def compressed(self) -> bool:
        return bool(self.flags & (1 << _COMPRESSED_FLAG_BIT))

    @property
    def compressed_size(self) -> int:
        """Meaningful only when `compressed` is True."""
        return self.flags & _COMPRESSED_SIZE_MASK

    @property
    def filename(self) -> str:
        return f"overlay9_{self.file_id}"


def parse_y9(data: bytes) -> list[Y9Entry]:
    """Parse the full contents of y9.bin into a list of Y9Entry records.

    Any trailing bytes that don't make up a full 32-byte record are ignored
    (this has not been observed in practice, but parsing is defensive).
    """
    count = len(data) // Y9_ENTRY_SIZE
    entries = []
    for i in range(count):
        chunk = data[i * Y9_ENTRY_SIZE : (i + 1) * Y9_ENTRY_SIZE]
        values = Y9_ENTRY_STRUCT.unpack(chunk)
        entries.append(Y9Entry(*values))
    return entries


# --------------------------------------------------------------------------
# Region / MemoryMap
# --------------------------------------------------------------------------


@dataclass
class Region:
    """One mapped byte range: either the ARM9 binary or a single overlay."""

    name: str  # provenance: "arm9" or "ov<overlay_id>"
    base: int
    size: int
    data: bytes
    source_path: Path

    # Overlay-only metadata (None/0 defaults for the arm9 region).
    overlay_id: int | None = None
    file_id: int | None = None
    bss_size: int = 0
    sinit_start: int = 0
    sinit_end: int = 0
    flags: int = 0
    compressed: bool = False
    compressed_size: int = 0
    ram_size: int = 0  # ram_size declared in y9 (may exceed actual file size)
    file_size: int = 0  # actual size of the on-disk file

    @property
    def end(self) -> int:
        """First address past the end of this region (exclusive)."""
        return self.base + self.size

    def contains(self, addr: int) -> bool:
        return self.base <= addr < self.end

    def covers(self, addr: int, size: int) -> bool:
        return self.base <= addr and addr + size <= self.end


@dataclass
class MemoryMap:
    """A collection of mapped Regions with address-lookup helpers."""

    regions: list[Region]
    rom_dir: Path
    y9_entry_count: int = 0
    overlay_files_found: int = 0
    missing_overlay_files: list[str] = field(default_factory=list)

    def candidates(self, addr: int) -> list[Region]:
        """Return every region whose [base, end) range contains `addr`.

        Ordinarily this list has 0 or 1 elements. When overlays share a RAM
        address, it can have more.
        """
        return [r for r in self.regions if r.contains(addr)]

    def _resolve_overlay(self, overlay: int | str) -> Region | None:
        if isinstance(overlay, bool):
            raise TypeError("overlay must be an int overlay_id or a str name")
        if isinstance(overlay, int):
            name = f"ov{overlay}"
        elif isinstance(overlay, str):
            name = overlay if overlay.startswith("ov") else f"ov{overlay}"
        else:
            raise TypeError(
                f"overlay must be an int overlay_id or a str name, got {type(overlay)!r}"
            )
        for region in self.regions:
            if region.name == name:
                return region
        return None

    def read(self, addr: int, size: int, overlay: int | str | None = None) -> bytes:
        """Read `size` bytes starting at `addr`.

        overlay=None:
            - exactly one region contains `addr` -> read from it.
            - zero regions contain `addr` -> AddressNotMappedError.
            - more than one region contains `addr` -> AmbiguousAddressError
              (carrying the candidate list).
        overlay="ov1" or overlay=1:
            - read from that specific overlay's region regardless of
              overlap, provided `addr` (and the full requested range) falls
              inside it. Unknown overlay name/id, or a range outside the
              region's bounds, -> AddressNotMappedError.
        """
        if overlay is not None:
            region = self._resolve_overlay(overlay)
            if region is None or not region.covers(addr, size):
                raise AddressNotMappedError(addr, size)
            offset = addr - region.base
            return region.data[offset : offset + size]

        matches = self.candidates(addr)
        if not matches:
            raise AddressNotMappedError(addr, size)
        if len(matches) > 1:
            raise AmbiguousAddressError(addr, matches)

        region = matches[0]
        if not region.covers(addr, size):
            raise AddressNotMappedError(addr, size)
        offset = addr - region.base
        return region.data[offset : offset + size]


# --------------------------------------------------------------------------
# Loader
# --------------------------------------------------------------------------


def load_memory_map(rom_dir: Path | str | None = None) -> MemoryMap:
    """Build a MemoryMap by reading arm9.bin, y9.bin, and overlay9_* from
    `rom_dir` (defaults to DEFAULT_ROM_DIR).
    """
    resolved_dir = Path(rom_dir) if rom_dir is not None else DEFAULT_ROM_DIR

    arm9_path = resolved_dir / "arm9.bin"
    arm9_data = arm9_path.read_bytes()
    regions: list[Region] = [
        Region(
            name="arm9",
            base=ARM9_BASE,
            size=len(arm9_data),
            data=arm9_data,
            source_path=arm9_path,
            ram_size=len(arm9_data),
            file_size=len(arm9_data),
        )
    ]

    y9_path = resolved_dir / "y9.bin"
    y9_entries = parse_y9(y9_path.read_bytes())

    overlay_files_found = 0
    missing_overlay_files: list[str] = []
    for entry in y9_entries:
        overlay_path = resolved_dir / entry.filename
        if not overlay_path.exists():
            missing_overlay_files.append(entry.filename)
            continue

        raw = overlay_path.read_bytes()
        overlay_files_found += 1
        mapped_size = min(len(raw), entry.ram_size)

        regions.append(
            Region(
                name=f"ov{entry.overlay_id}",
                base=entry.ram_addr,
                size=mapped_size,
                data=raw[:mapped_size],
                source_path=overlay_path,
                overlay_id=entry.overlay_id,
                file_id=entry.file_id,
                bss_size=entry.bss_size,
                sinit_start=entry.sinit_start,
                sinit_end=entry.sinit_end,
                flags=entry.flags,
                compressed=entry.compressed,
                compressed_size=entry.compressed_size if entry.compressed else 0,
                ram_size=entry.ram_size,
                file_size=len(raw),
            )
        )

    return MemoryMap(
        regions=regions,
        rom_dir=resolved_dir,
        y9_entry_count=len(y9_entries),
        overlay_files_found=overlay_files_found,
        missing_overlay_files=missing_overlay_files,
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _format_table(mm: MemoryMap) -> str:
    header = f"{'PROV':<6} {'BASE':<10} {'END':<10} {'SIZE':>9}  {'FILE':<16} {'FLAGS'}"
    lines = [header, "-" * len(header)]
    for region in sorted(mm.regions, key=lambda r: (r.base, r.name)):
        flag_bits = []
        if region.compressed:
            flag_bits.append(f"compressed(comp_size=0x{region.compressed_size:X})")
        if region.bss_size:
            flag_bits.append(f"bss=0x{region.bss_size:X}")
        flags_str = " ".join(flag_bits)
        lines.append(
            f"{region.name:<6} 0x{region.base:08X} 0x{region.end:08X} "
            f"{region.size:>9}  {region.source_path.name:<16} {flags_str}"
        )
    return "\n".join(lines)


def _run_selftest(rom_dir: Path | str | None) -> bool:
    all_ok = True

    def check(label: str, ok: bool) -> None:
        nonlocal all_ok
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")

    mm = load_memory_map(rom_dir)

    # a. read(0x02000000, 16) == first 16 bytes of arm9.bin
    try:
        expected = (mm.rom_dir / "arm9.bin").read_bytes()[:16]
        got = mm.read(ARM9_BASE, 16)
        check("a. read(arm9 base, 16) matches arm9.bin head", got == expected)
    except Exception as exc:  # noqa: BLE001 - selftest must report, not raise
        check(f"a. read(arm9 base, 16) matches arm9.bin head (raised {exc!r})", False)

    # b. overlay 0's region base == 0x0214CD20
    ov0 = mm._resolve_overlay(0)
    check(
        "b. overlay 0 region base == 0x0214CD20",
        ov0 is not None and ov0.base == 0x0214CD20,
    )

    # c. an address inside the overlap of ov0 and ov1, overlay=None,
    #    raises AmbiguousAddressError; candidates() returns both ov0 and ov1.
    ov1 = mm._resolve_overlay(1)
    cand_names: list[str] = []
    c_ok = False
    if ov0 is not None and ov1 is not None:
        overlap_addr = max(ov0.base, ov1.base)
        cand_names = sorted(r.name for r in mm.candidates(overlap_addr))
        try:
            mm.read(overlap_addr, 1)
        except AmbiguousAddressError as exc:
            names_in_exc = {r.name for r in exc.candidates}
            c_ok = {"ov0", "ov1"} <= names_in_exc and {"ov0", "ov1"} <= set(cand_names)
        except Exception:
            c_ok = False
    check(
        f"c. overlap address is ambiguous and includes ov0+ov1 "
        f"(candidates={cand_names})",
        c_ok,
    )

    # d. read(0x00000000, 4) raises AddressNotMappedError cleanly
    try:
        mm.read(0x00000000, 4)
        d_ok = False
    except AddressNotMappedError:
        d_ok = True
    except Exception:
        d_ok = False
    check("d. read(0x00000000, 4) raises AddressNotMappedError", d_ok)

    # e. y9.bin entry count == number of overlay9_* files present
    on_disk = sorted(mm.rom_dir.glob("overlay9_*"))
    e_ok = mm.y9_entry_count == mm.overlay_files_found and not mm.missing_overlay_files
    check(
        f"e. y9 entries={mm.y9_entry_count}, overlay9_* files on disk={len(on_disk)}, "
        f"entries matched to a file={mm.overlay_files_found}",
        e_ok,
    )

    return all_ok


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Static memory-map loader for the FTC NDS ROM (arm9.bin + overlays)."
    )
    parser.add_argument(
        "--rom-dir",
        type=Path,
        default=None,
        help=f"Directory containing arm9.bin, y9.bin, overlay9_*. Default: {DEFAULT_ROM_DIR}",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run the acceptance selftest suite and exit 0 only if all checks pass.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the region table (provenance, base, end, size, file, flags).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.selftest:
        ok = _run_selftest(args.rom_dir)
        return 0 if ok else 1

    if args.list:
        mm = load_memory_map(args.rom_dir)
        print(_format_table(mm))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
