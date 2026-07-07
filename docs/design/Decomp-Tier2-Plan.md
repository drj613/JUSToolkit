# JUS Tier-2 Decompilation Plan (Non-Matching)

> **For agentic workers:** This is a long-horizon roadmap, not a one-shot implementation plan.
> Execute one task per session using the existing loop workflow (`RE-Session-Playbook.md` session
> checklist + `bd ready`). Steps use checkbox (`- [ ]`) syntax for tracking. Update checkboxes
> in this file as tasks complete.

**Goal:** Produce readable, behaviorally-validated C source for the JUS battle engine — no
byte-matching requirement — building directly on the existing static-RE database and GDB
validation workflow.

**Architecture:** Per-function pipeline: static-RE DB (`query.py`) → Ghidra decompiler draft →
hand-cleaned C in `decomp/src/` with types from shared headers → semantic validation against
the live game (melonDS GDB) or differential testing (Unicorn). A canonical `symbols.json` is
the single source of truth for names, module assignment, and per-function state.

**Tech Stack:** Python 3 + capstone (existing `scripts/analysis/` DB), Ghidra (headless, new),
arm-none-eabi toolchain (gdb already in use; gcc for syntax-checking drafts), melonDS GDB stub
(port 3333, existing), Unicorn engine (new, differential testing), decomp.me `nds_arm9`
platform (optional community help).

---

## What "Tier 2" means here

| Tier | Output | This plan? |
|------|--------|------------|
| 1 | RE docs (current `Battle-Engine-Map.md` etc.) | Done / ongoing — input to this plan |
| 2 | Readable C per function, semantics verified, **no** byte-match | **Yes — this plan** |
| 3 | Byte-identical rebuild (pokediamond-style, mwccarm) | No. See "Tier-3 upgrade path" at end |

**Non-goals:** full-ROM matching decomp; rebuilding a playable ROM from the C; decompiling
menus, netplay, sound, or the arm7 binary; decompiling all 14 overlays.

**Function lifecycle** (tracked per function in `decomp/symbols.json`):

```
NAMED → DRAFTED → CLEANED → VALIDATED
```

- `NAMED` — address + name + module assigned, semantics summarized in RE docs
- `DRAFTED` — raw Ghidra/m2c output saved, compiles as C (syntax/type check only)
- `CLEANED` — hand-rewritten with real types/names, control flow restructured, reviewed against disasm
- `VALIDATED` — behavior confirmed vs live game (GDB) or differential test (Unicorn)

## Ground truth (facts this plan builds on, as of 2026-07-02)

- Extracted ROM at `jus_files/ripped_jus_files/ftc/`: `arm9.bin` (676 KB, decompressed, loads
  at `0x02000000`), `overlay9_0`–`overlay9_13` (ov9 and ov13 are 32-byte stubs), `y9.bin`
  overlay table, `rom.nds`.
- Static-RE DB at `jus_files/analysis/`: `functions.json` (1.7 MB), `xrefs.json` (12 MB),
  `disasm/`, `arm9_tables_ram.json` (842 rows). Read via
  `scripts/analysis/query.py` (subcommands: `func`, `callers`, `callees`, `xrefs-to`,
  `search-imm`, `search-op-imm`, `disasm`, `strings`, `pool-values`).
- ~130–150 named addresses across 11 subsystems in `docs/research/Battle-Engine-Map.md`.
- Runtime character struct in `docs/research/Character-State-Struct.md` (player base pointers
  `0x021E2A7C/80/84/88`).
- Debugger: melonDS GDB stub (ARM9 port 3333) + `arm-none-eabi-gdb`, watcher at
  `scripts/gdb/jus_gdb_watcher.py`. No hardware watchpoints in melonDS stub.
- **No Ghidra project exists. Compiler and NitroSDK version unidentified.** Battle code spans
  arm9 + at least ov5 (jpower, `0x02165xxx`) and ov6 (hit resolution, `0x02158B20`).
- Legal posture: educational; `jus_files/` lives outside the repo via symlink and stays out of
  git. The decomp tree contains only self-written C, names, and addresses — never original
  binaries or assets.

---

## Phase D0 — Denominator & environment

Everything else needs a countable scope and a decompiler. Exit criterion: a published function
count (total and per-overlay), overlay memory map, and a working headless Ghidra project.

### Task D0.1: Overlay memory map

**Files:**
- Create: `scripts/decomp/overlay_map.py`
- Create: `docs/research/Overlay-Map.md` (generated output, committed)

- [ ] **Step 1: Write the y9.bin parser**

```python
#!/usr/bin/env python3
"""Parse y9.bin overlay table -> markdown memory map."""
import struct, sys, pathlib

FTC = pathlib.Path("jus_files/ripped_jus_files/ftc")

def main():
    data = FTC.joinpath("y9.bin").read_bytes()
    rows = []
    for i in range(0, len(data), 32):
        oid, ram, size, bss, si0, si1, fid, flag = struct.unpack("<8I", data[i:i+32])
        comp = bool((flag >> 24) & 1)
        rows.append((oid, ram, size, bss, fid, comp))
    print("| Overlay | RAM start | RAM end | Size | BSS | Compressed |")
    print("|---|---|---|---|---|---|")
    for oid, ram, size, bss, fid, comp in rows:
        print(f"| ov{oid} | 0x{ram:08X} | 0x{ram+size:08X} | 0x{size:X} | 0x{bss:X} | {comp} |")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run and capture**

Run from repo root: `python3 scripts/decomp/overlay_map.py | tee /tmp/overlay_map.txt`
Expected: 14 rows; ov9 and ov13 tiny; note which overlays overlap the same RAM range
(NDS overlays commonly share address space — two overlays mapped at the same address are
mutually exclusive at runtime).

- [ ] **Step 3: Write `docs/research/Overlay-Map.md`** — paste the table, then annotate each
  overlay with what's known (ov5 = jpower, ov6 = hit resolution, from Battle-Engine-Map.md).
  Flag every RAM-range collision explicitly: **any documented address inside a shared range
  must always be recorded as (overlay, address), never a bare address.**

- [ ] **Step 4: Commit** — `git add scripts/decomp/overlay_map.py docs/research/Overlay-Map.md && git commit -m "decomp: overlay memory map from y9.bin"`

### Task D0.2: Function denominator

**Files:**
- Create: `scripts/decomp/denominator.py`

- [ ] **Step 1: Inspect `functions.json` schema**

Run: `python3 -c "import json; d=json.load(open('jus_files/analysis/functions.json')); print(type(d).__name__, len(d)); import itertools; print(list(itertools.islice(iter(d.items() if isinstance(d,dict) else d), 2)))"`

- [ ] **Step 2: Write `denominator.py`** — count functions total and bucketed by address range
  using the overlay map from D0.1 (arm9 = `0x02000000`–`0x02000000+0xA9000` per existing scan
  range; each overlay by its y9 range). Output one summary block:

```
total functions:        N
  arm9:                 N1
  ov5:                  N2
  ov6:                  N3
  other overlays:       ...
  unattributed:         ...
```

- [ ] **Step 3: Record the numbers** in `docs/research/Overlay-Map.md` under a "Denominator"
  heading. This is the progress denominator for the whole effort.

- [ ] **Step 4: Commit.**

### Task D0.3: Ghidra project (the draft engine)

**Files:**
- Create: `scripts/decomp/ghidra/` (project dir, gitignored — add `scripts/decomp/ghidra/` to `.gitignore`)
- Create: `scripts/decomp/import_ghidra.sh`

- [ ] **Step 1: Install Ghidra** — `brew install --cask ghidra` (or download from
  https://ghidra-sre.org). Record the installed version in `import_ghidra.sh` header comment.

- [ ] **Step 2: Import arm9 + battle overlays headless**

```bash
#!/usr/bin/env bash
# Ghidra headless import for JUS decomp. Ghidra version: <record on install>
set -euo pipefail
FTC=jus_files/ripped_jus_files/ftc
PROJ=scripts/decomp/ghidra
GHIDRA_HEADLESS="$(ls /opt/homebrew/Caskroom/ghidra/*/ghidra_*/support/analyzeHeadless | head -1)"

mkdir -p "$PROJ"
"$GHIDRA_HEADLESS" "$PROJ" JUS \
  -import "$FTC/arm9.bin" \
  -processor ARM:LE:32:v5t \
  -loader BinaryLoader -loader-baseAddr 0x02000000 \
  -analysisTimeoutPerFile 3600
# Repeat -import for each battle overlay at its y9 RAM address (from Overlay-Map.md), e.g.:
# -import "$FTC/overlay9_5" ... -loader-baseAddr 0x<ov5 ram>
```

Note: if an overlay's y9 entry says compressed, decompress first (BLZ backwards-LZ; the
extraction pipeline already produced a decompressed arm9 — check whether overlays were also
decompressed by Ekona; if not, `ndspy` or Ekona can decompress).
Alternative: the **NTRGhidra** loader plugin (https://github.com/pedro-javierf/NTRGhidra)
imports `rom.nds` whole with overlays placed automatically — use it if manual overlay
placement proves fiddly, but headless scripting is easier with plain BinaryLoader.

- [ ] **Step 3: Smoke-test decompiler output** — open the project (or headless
  `-postScript DecompileHeadless.java`), decompile `0x02078488` (`ApplyDeltaToCurrent`, the
  smallest well-understood function), and compare against
  `python3 scripts/analysis/query.py disasm 0x02078488`. The C must show the clamped-add
  semantics documented in Battle-Engine-Map.md. If it doesn't, the import (base address /
  processor) is wrong — fix before proceeding.

- [ ] **Step 4: Commit** the script + .gitignore entry (never the project dir).

---

## Phase D1 — Compiler/SDK identification & scope subtraction

A large fraction of arm9 is NitroSDK/libc, not game code. Tag it and subtract it so the
denominator counts only game code. Exit criterion: every function in `functions.json` tagged
`game | sdk | libc | unknown`; game-only denominator published.

### Task D1.1: Build-string hunt

- [ ] **Step 1:** `strings -a jus_files/ripped_jus_files/ftc/arm9.bin | grep -iE 'sdk|nitro|metrowerks|codewarrior|mwcc|build|gcc' | sort -u`
- [ ] **Step 2:** Repeat for each overlay binary.
- [ ] **Step 3:** Record findings (SDK version string, compiler hints, or their absence) in a
  new `docs/research/Compiler-SDK-Notes.md`. Even for tier 2 this is worth recording — it is
  the first question anyone asks if the project later attracts matching-decomp contributors.

### Task D1.2: SDK bucketing by hardware-register fingerprint

SDK code talks to hardware; game code talks to SDK. Functions referencing I/O registers
(`0x04000000` range) are near-certainly SDK/low-level.

- [ ] **Step 1:** For each canonical NDS register constant, list functions touching it:

```bash
for reg in 0x04000000 0x04000004 0x040000B0 0x04000180 0x040001A4 0x04000208 0x04000210; do
  echo "== $reg =="
  python3 scripts/analysis/query.py search-imm $reg
done
```

(DISPCNT, DISPSTAT, DMA0SAD, IPCSYNC, ROMCTRL, IME, IE respectively.)

- [ ] **Step 2:** Seed-tag those functions `sdk`, then propagate: a function whose callees are
  all `sdk` and which no documented game subsystem references is `sdk` too (write this as
  `scripts/decomp/tag_sdk.py` using `query.py callers`/`callees` output; iterate to fixpoint;
  anything reachable FROM documented game addresses stays `game`-eligible).

- [ ] **Step 3:** Cross-check a sample of 10 tagged-`sdk` functions in Ghidra — do they look
  like OS/FS/SND plumbing (register soup, no game constants)? Reference for what NitroSDK code
  looks like: the pokeheartgold / pokediamond repos (github.com/pret) carry decompiled
  NitroSDK — same SDK family JUS almost certainly uses.

- [ ] **Step 4:** Publish counts in `Compiler-SDK-Notes.md`:
  `game-eligible: N, sdk: N, libc: N, unknown: N`. **The `game-eligible` number is the real
  tier-2 scope.** Expect it to be a fraction of the D0.2 total.

---

## Phase D2 — Symbols & types from existing RE

Convert the RE corpus into machine-readable decomp inputs. Exit criterion: `symbols.json`
seeded with every documented address; C headers compile; Ghidra shows the imported names.

### Task D2.1: Canonical symbols file

**Files:**
- Create: `decomp/symbols.json`
- Create: `scripts/decomp/symbols_export.py`

- [ ] **Step 1: Define the schema** (one array of entries):

```json
{
  "addr": "0x020784E4",
  "overlay": null,
  "name": "Gauge_IsCurrentBelowPercentOfMax",
  "module": "gauge",
  "state": "NAMED",
  "source": "Battle-Engine-Map.md#damage-pipeline",
  "notes": "25%-of-max check; GDB seed anchor 0x020784FC inside"
}
```

`overlay` is an integer for overlay-resident functions (per D0.1 rule: never a bare address in
a shared range), `null` for arm9. `state` ∈ NAMED/DRAFTED/CLEANED/VALIDATED. VALIDATED
entries additionally carry `"evidence": "<difftest run or GDB session log pointer>"` (set in
Phase D5).

- [ ] **Step 2: Seed from Battle-Engine-Map.md** — transcribe all ~130–150 documented
  addresses. Naming convention: `Module_Verb` (`Gauge_ApplyDelta`, `Entity_PoolAlloc`,
  `Projectile_SpawnDispatch`, `JPower_Create`, `MoveInfo_Alloc`, `Hit_Resolve`). Keep the
  doc's semantic label in `notes`. Known seeds include:

  | Addr | Name | Module |
  |---|---|---|
  | 0x02078488 | Gauge_ApplyDelta | gauge |
  | 0x020784B8 | Gauge_GrowMax | gauge |
  | 0x020784E4 | Gauge_IsCurrentBelowPercentOfMax | gauge |
  | 0x020783CC | Gauge_HpTrampoline | gauge |
  | 0x020783B8 | Gauge_DrainTrampoline | gauge |
  | 0x0200D12C | Math_SignedDiv | libmath |
  | 0x02158DC4 (ov6) | Damage_AttackBoostScale | damage |
  | 0x02158ED0 (ov6) | Hitstun_RecomputeDuration | damage |
  | 0x02158B20 (ov6) | Hit_Resolve | damage |
  | 0x020834D4 | Entity_PoolAlloc | entity |
  | 0x02083648 | Entity_PoolFree | entity |
  | 0x021574CC | Projectile_SpawnDispatch | projectile |
  | 0x02168CF4 | Projectile_SpawnOwned | projectile |
  | 0x0216C958 | Projectile_Despawn | projectile |
  | 0x021652E8 (ov5) | JPower_Create | jpower |
  | 0x02165398 (ov5) | JPower_GetEntry | jpower |
  | 0x02156A38 | MoveInfo_Alloc | moveinfo |
  | 0x021570EC | MoveInfo_Set | moveinfo |
  | 0x0214BD80 | g_BattleResourceMgr (data) | resmgr |

  (Verify each overlay attribution against the D0.1 map while transcribing — the ov5/ov6
  assignments above come from Battle-Engine-Map.md prose and must be confirmed.)

- [ ] **Step 3: Write `symbols_export.py`** with two output formats:
  - `--ghidra` → `Name Address` lines for Ghidra's `ImportSymbolsScript.py`
  - `--gdb` → a GDB script of `set $Gauge_ApplyDelta = 0x02078488`-style convenience vars,
    so live sessions and decomp share one namespace

- [ ] **Step 4: Import into Ghidra** (headless `-postScript ImportSymbolsScript.py <file>`)
  and verify names appear on the right functions.

- [ ] **Step 5: Commit** (`decomp/symbols.json` + exporter).

### Task D2.2: Type headers

**Files:**
- Create: `decomp/include/jus/types.h` (u8/u16/u32/s8/s16/s32/fx16/fx32 typedefs)
- Create: `decomp/include/jus/battle_char.h`
- Create: `decomp/include/jus/gauge.h`

- [ ] **Step 1: `battle_char.h`** from Character-State-Struct.md, gaps as explicit pad bytes:

```c
#pragma once
#include "types.h"

/* In-battle character state. Runtime base pointers (per player):
 * 0x021E2A7C / 0x021E2A80 / 0x021E2A84 / 0x021E2A88.
 * Size >= 0x102, likely 0x120. Field widths marked (?) are unverified.
 * NOTE: this is the *runtime/GDB* offset space. The static-RE docs also use a
 * resource-manager-relative space (char+0x56c gauge, +0x1a4/+0x1a8) — different struct,
 * do NOT merge offsets across the two spaces. */
typedef struct BattleChar {
    u8  _pad00[0x78];
    u8  groundState;        /* +0x78: 0x00 air, 0x22 ground, 0xC0 launched */
    u8  _pad79[0x88 - 0x79];
    u8  positiveStatus;     /* +0x88 (?) width unverified */
    u8  _pad89[0xA0 - 0x89];
    u8  negativeStatusFlags;/* +0xA0 (?) width unverified */
    u8  _padA1[0xD9 - 0xA1];
    u8  jumpCounter;        /* +0xD9 */
    u8  airActionCounter;   /* +0xDA */
    u8  _padDB[0x102 - 0xDB];
    u8  defenseTimer;       /* +0x102 (?) width unverified */
    u8  _pad103[0x120 - 0x103];
} BattleChar;
```

- [ ] **Step 2: `gauge.h`** — the gauge struct implied by the four gauge functions (current /
  max fields, cap `0x4000`); derive exact offsets from the `disasm` of `Gauge_ApplyDelta`
  before writing it down.

- [ ] **Step 3: Syntax-check** — `arm-none-eabi-gcc -fsyntax-only -I decomp/include decomp/include/jus/battle_char.h`
  (install toolchain if only gdb is present: `brew install --cask gcc-arm-embedded`).
  Add a static assert once size is confirmed: `_Static_assert(sizeof(BattleChar) == 0x120, "");`

- [ ] **Step 4: Commit.**

---

## Phase D3 — The per-function pipeline

Define the repeatable loop once; Phase D4 just runs it N times. Exit criterion: pipeline
documented, exercised end-to-end on the 5 gauge functions, all 5 reach CLEANED.

### Task D3.1: Decomp tree layout

- [ ] **Step 1: Create the tree:**

```
decomp/
  symbols.json            # canonical (from D2.1)
  include/jus/*.h         # shared types (from D2.2)
  src/<module>/<module>.c # cleaned functions, grouped by module
  drafts/<addr>.c         # raw Ghidra/m2c output, one file per function, never edited
  PROGRESS.md             # generated, see D6.1
```

- [ ] **Step 2: Document style rules** in `decomp/README.md`:
  - every function opens with `/* 0x020784E4 (arm9) | state: CLEANED | Battle-Engine-Map.md#... */`
  - real names from symbols.json only; no `uVar3`-style residue in CLEANED code
  - restructure control flow (no goto unless the asm genuinely demands it)
  - unknown callees stay as `UNK_02xxxxxx()` externs — they become the work queue
  - C is documentation: comment WHY (game rule), not WHAT (the code shows what)

### Task D3.2: The loop (run per function)

- [ ] **Step 1 — Pick:** next NAMED function in the current module (Phase D4 order).
- [ ] **Step 2 — Context:** `python3 scripts/analysis/query.py func <addr>`, `callers <addr>`,
  `callees <addr>`, `disasm <addr>`. Read the relevant Battle-Engine-Map.md section.
- [ ] **Step 3 — Draft:** export Ghidra decompiler output to `decomp/drafts/<addr>.c`.
  For functions where Ghidra produces goto-soup, try m2c (https://github.com/matt-kempster/m2c,
  ARM supported) on the disasm as a second opinion.
- [ ] **Step 4 — Clean:** rewrite into `decomp/src/<module>/<module>.c` using headers +
  symbols.json names. Mark DRAFTED→CLEANED only after re-reading the disasm side-by-side and
  confirming every branch/constant is represented.
- [ ] **Step 5 — Syntax gate:** `arm-none-eabi-gcc -c -Os -ffreestanding -I decomp/include decomp/src/<module>/<module>.c -o /tmp/check.o`
  Expected: compiles clean. This is a type/syntax gate only — output bytes are irrelevant (tier 2).
- [ ] **Step 6 — Update state** in symbols.json; append newly-discovered callees as NAMED
  entries (name them or leave `UNK_<addr>`).
- [ ] **Step 7 — Commit** per function or small batch:
  `git commit -m "decomp(gauge): Gauge_ApplyDelta CLEANED"`.
- **Stuck?** Post the function to decomp.me (platform `nds_arm9`,
  https://decomp.me/platform/nds_arm9 — 10k+ scratches, active NDS community) and move on.

### Task D3.3: Pilot — gauge module end-to-end

- [ ] Run D3.2 on all 5 gauge functions (`Gauge_ApplyDelta`, `Gauge_GrowMax`,
  `Gauge_IsCurrentBelowPercentOfMax`, both trampolines). Best-understood code in the whole
  map — if the pipeline fights you here, fix the pipeline before scaling.
- [ ] Retro: adjust D3.2 steps from what you learned, update this file.

---

## Phase D4 — Battle-engine modules (the bulk of the work)

Run the D3.2 loop module by module. Order chosen so each module's outputs (types, named
callees) feed the next. Each module is a milestone; each is independently valuable even if
the effort stops there. Module scope = seed functions + their callee closure within
game-tagged code (enumerate with `query.py callees`, breadth-first, stopping at `sdk` tags).

- [ ] **M1 — gauge** (pilot, from D3.3; ~5 functions)
- [ ] **M2 — damage + hitstun** (ov6: `Hit_Resolve`, `Damage_AttackBoostScale`,
      `Hitstun_RecomputeDuration` + closure). The documented hitstun formula
      (`floor(d/10) * table[0x4c] * 2 + d`) is the first VALIDATED target — it's already
      GDB-testable via the existing 30-card queue.
- [ ] **M3 — entity pool + projectiles** (`Entity_PoolAlloc/Free`,
      `Projectile_SpawnDispatch` 13-way switch, `Projectile_SpawnOwned`, `Projectile_Despawn`)
- [ ] **M4 — jpower** (ov5: `JPower_Create`, `JPower_GetEntry` stride 0x130 + closure;
      pairs with existing `jpower-Mapping.md`)
- [ ] **M5 — MoveInfo lifecycle** (`MoveInfo_Alloc` size 0x1F0, `MoveInfo_Set` + closure)
- [ ] **M6 — character state machine / physics** (BattleChar struct writers; hitstun/velocity
      region `+0x6A–0xBA` — coordinate with the live Phase-1 GDB hitstun research, it names
      these fields for free)
- [ ] **M7 — resource manager + chrb load path** (`g_BattleResourceMgr` `0x0214BD80`,
      chr_b array `+0x40` stride `0x3C`; pairs with `chr_b-Complete-Mapping.md`)

After M7: re-run the denominator (D0.2) against symbols.json states and decide whether to
extend scope (collision, input, koma/deck) or consolidate. New modules get added HERE, not
improvised.

---

## Phase D5 — Behavioral validation (tier 2's correctness story)

Matching decomps prove correctness with byte-identity. Tier 2 must prove it with behavior.
Two oracles, cheapest first. Exit criterion per function: VALIDATED state with a recorded
evidence pointer.

### Task D5.1: Unicorn differential harness (primary oracle — no human in the loop)

**Files:**
- Create: `scripts/decomp/difftest.py`

Idea: run the ORIGINAL machine code of one function in an emulated CPU, run the C
reimplementation compiled natively, compare outputs over many inputs.

- [ ] **Step 1:** `pip install unicorn` (record version in the script header).
- [ ] **Step 2: Core harness:**

```python
#!/usr/bin/env python3
"""Differential test: original ARM function (Unicorn) vs decompiled C (compiled to a
native shared lib via clang, called through ctypes)."""
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)
import ctypes, pathlib

ARM9 = pathlib.Path("jus_files/ripped_jus_files/ftc/arm9.bin").read_bytes()
BASE, RETURN_MAGIC, STACK_TOP = 0x02000000, 0x0FFFFFF0, 0x027E0000

def run_original(func_addr, r0, r1=0, r2=0):
    mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    mu.mem_map(BASE, 0x100000)               # arm9 image
    mu.mem_write(BASE, ARM9)
    mu.mem_map(0x027C0000, 0x40000)          # stack + scratch RAM
    mu.mem_map(RETURN_MAGIC & ~0xFFF, 0x1000)
    mu.reg_write(UC_ARM_REG_R0, r0)
    mu.reg_write(UC_ARM_REG_R1, r1)
    mu.reg_write(UC_ARM_REG_R2, r2)
    mu.reg_write(UC_ARM_REG_SP, STACK_TOP)
    mu.reg_write(UC_ARM_REG_LR, RETURN_MAGIC)
    mu.emu_start(func_addr, RETURN_MAGIC, count=1_000_000)
    return mu.reg_read(UC_ARM_REG_R0)
```

Struct-taking functions: map a scratch page, write a candidate struct, pass its address in
r0, read the struct back after — compare full struct, not just r0.

- [ ] **Step 3:** Compile the C side per module:
  `clang -shared -O0 -I decomp/include decomp/src/gauge/gauge.c -o /tmp/gauge.dylib`,
  load with ctypes, sweep inputs (edge values: 0, 1, 0x3FFF, 0x4000, 0x4001, negatives,
  plus a few thousand random u32s), assert equality.
- [ ] **Step 4:** Wire as `python3 scripts/decomp/difftest.py gauge` → per-function PASS/FAIL.
  PASS ⇒ flip state to VALIDATED with `"evidence": "difftest gauge 2026-07-xx"`.
- [ ] **Caveats to respect:** overlay functions need the overlay binary mapped at its y9
  address too; functions calling into unmapped code will fault — either stub callees (Unicorn
  hook on RETURN_MAGIC-style trampolines) or validate leaf functions first and work upward.

### Task D5.2: Live GDB validation (for state-dependent behavior)

For functions whose behavior depends on live game state (state machine, physics), Unicorn
input-sweeping is impractical — use the existing dynamic workflow instead.

- [ ] **Step 1:** Extend `docs/research/GDB-Validation-Queue.md` card format with a
  `decomp:` field pointing at the C function under test.
- [ ] **Step 2:** Per function: derive one falsifiable prediction FROM THE C ("break at
  0x02158ED0, read r0/r1, computed duration must equal C-function output for the same
  inputs"), run it in the standard melonDS session (Phase1-GDB-Guide.md), record evidence.
- [ ] **Step 3:** Match ⇒ VALIDATED with a pointer to the session log in
  `jus_files/analysis/gdb/`. Mismatch ⇒ the C is wrong (or the RE claim was) — file a `bd`
  issue, downgrade to DRAFTED, fix.

---

## Phase D6 — Progress tracking & publication

### Task D6.1: Generated progress report

**Files:**
- Create: `scripts/decomp/progress.py`
- Create: `decomp/PROGRESS.md` (generated)

- [ ] **Step 1: Write `progress.py`:**

```python
#!/usr/bin/env python3
"""Generate decomp/PROGRESS.md from decomp/symbols.json."""
import json, collections, pathlib

syms = json.load(open("decomp/symbols.json"))
by_mod = collections.defaultdict(collections.Counter)
for s in syms:
    by_mod[s["module"]][s["state"]] += 1

STATES = ["NAMED", "DRAFTED", "CLEANED", "VALIDATED"]
lines = ["# Decomp Progress (generated — do not edit)", "",
         "| Module | " + " | ".join(STATES) + " | Total |", "|---|" + "---|" * 5]
total = collections.Counter()
for mod in sorted(by_mod):
    c = by_mod[mod]
    total.update(c)
    lines.append(f"| {mod} | " + " | ".join(str(c[s]) for s in STATES)
                 + f" | {sum(c.values())} |")
lines.append("| **all** | " + " | ".join(str(total[s]) for s in STATES)
             + f" | {sum(total.values())} |")
pathlib.Path("decomp/PROGRESS.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
```

- [ ] **Step 2:** Run after every session (add to the RE-Session-Playbook session-end
  checklist next to `bd sync && git push`). Commit the regenerated file with the session's work.

### Task D6.2: Project bookkeeping

- [ ] Create one `bd` epic per phase (D0…D6) and one issue per task; dependencies mirror the
  phase order. Modules M1–M7 are issues under a D4 epic.
- [ ] Add a "Decompilation (Tier 2)" section to `docs/research/README.md` linking this plan,
  `Overlay-Map.md`, and `decomp/PROGRESS.md`.
- [ ] When M2 (damage) reaches VALIDATED, write a short public-facing note (repo README or
  blog) — first externally interesting milestone, and the point where decomp.me/GBAtemp
  contributors could plausibly join.

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Overlay RAM overlap → wrong-overlay disasm silently decompiled | D0.1 rule: (overlay, addr) pairs everywhere; Ghidra project imports battle overlays at verified y9 addresses only |
| Ghidra drafts are goto-soup on ARM | m2c second opinion (D3.2); decomp.me for community help; drafts are never the deliverable |
| Unicorn harness faults on non-leaf functions | Validate leaves first; stub callees via hooks; fall back to D5.2 GDB oracle |
| melonDS stub lacks hardware watchpoints | Already known; watcher script + Unicorn cover most needs |
| Static-RE claims later refuted (has happened — see 0x08D4A0 case-fold) | VALIDATED state requires fresh evidence, never inherits trust from NAMED |
| Solo-pacing burnout | Module milestones each independently useful; stopping after any M-milestone still leaves a coherent artifact |
| Scope creep into menus/netplay | Non-goals section is binding; new modules only via explicit D4 list edit |

## Tier-3 upgrade path (preserve optionality, spend nothing now)

Everything this plan produces is reusable if a matching decomp ever starts:
`symbols.json` → symbols/splat config; module boundaries → translation units; VALIDATED
semantics → review baseline. The tier-3 entry point would be
[dsd / ds-decomp](https://github.com/AetiasHax/ds-decomp) (Rust toolkit: extracts, delinks
NDS ROM + overlays into relocatable objects, generates a matching build skeleton, integrates
objdiff) plus mwccarm (fetched via pokeheartgold-style `tools/get_mwccarm.sh` scripts) and
[decomp.me](https://decomp.me/platform/nds_arm9) scratches. The only tier-3 prep worth doing
early is D1.1 (record compiler/SDK evidence while you're looking anyway).

## References

- [ds-decomp (dsd) toolkit](https://github.com/AetiasHax/ds-decomp)
- [decomp.me NDS platform](https://decomp.me/platform/nds_arm9)
- [Decompedia: Nintendo DS](https://decomp.wiki/platforms/nintendo-ds)
- [m2c decompiler (MIPS/PPC/ARM)](https://github.com/matt-kempster/m2c)
- [NTRGhidra loader](https://github.com/pedro-javierf/NTRGhidra)
- [Starcube Labs: Reverse Engineering a DS Game](https://www.starcubelabs.com/reverse-engineering-ds/)
- In-repo: `docs/research/Battle-Engine-Map.md`, `Character-State-Struct.md`,
  `RE-Session-Playbook.md`, `Phase1-GDB-Guide.md`, `docs/design/ARM9-Analysis-Pipeline.md`
