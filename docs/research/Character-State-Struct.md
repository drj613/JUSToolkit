# In-Battle Character State Struct

Comprehensive mapping of the character state structure in Jump Ultimate Stars
battle RAM.

**Source:** Action Replay code analysis + GDB memory research **Base Pointers:**
`0x021E2A7C`, `0x021E2A80`, `0x021E2A84`, `0x021E2A88` (4 players, wifi mode)
**Struct Size:** At least `0x102+` bytes (~260+ bytes) **Access Pattern:**
Pointer-relative offsets (fields are scattered, not contiguous)


## Fields established from the character-init copy (2026-08-14, Loop-Atlas K3)

The init function `0x02077C0C` copies `chr_b.bin` data into this struct. That fills part of the
`0x0000 - 0x003F` region this document lists as "Unknown", plus two fields in the `0x0040 - 0x0069`
gap. Source: `findings/k3-chr_b-to-battle-copy.md`.

| offset | source | contents | confidence |
|---|---|---|---|
| `+0x10` | `chr_b[0x02]` signed | 5 values `2..6`. **REFUTED as `tier`** (that's `+0x11`). Unknown. Lead: `chr_b-Complete-Mapping.md` says walk speed lives in `chr_b.bin` as a "`statC` field, threshold/tier-based" | unknown |
| `+0x11` | `chr_b[0x01]` signed | **the damage-formula `tier`**. Values `{1:11, 2:56, 3:7}`, and `chr_b-Complete-Mapping.md` independently documents tier `1`→−1, `2`→+0, `3`→+1. Goku and both damage targets read `2`, giving `tier-2 = 0` and `damage = damage1/5` exactly — matching B = 8.000 with `damage1 = 40` | **CONFIRMED** |
| `+0x13` | `chr_b[0x00]` | **base nature** (`0`=力, `1`=知, `2`=笑) | **CONFIRMED** |
| `+0x14` | per-size record `+0x2` | 3 values `{0,1,2}` over owned sizes | unknown |
| `+0x15` | per-size record `+0x3` | 3 values `{0,1,2}` over owned sizes | unknown |
| `+0x16` | per-size record `+0x0`, `<<6` | **max HP** | **CONFIRMED** |
| `+0x18` | copied from `+0x16` | **current HP** (starts at max) | **CONFIRMED** |
| `+0x2E` | `chr_b[0x30]` halfword | 56 distinct, `0..570` — looks like an ID | unknown |
| `+0x30` | per-size halfword at `chr_b[0x32]`, stride 2 | 133 distinct, `0..572` — per-size ID | unknown |
| `+0x34` | — | **pointer to the panel's `koma.bin` record**; its `+0x8` (size−1) drives all per-size indexing | **CONFIRMED** |
| `+0x41` | — | **`chr_b` index** | **CONFIRMED** |
| `+0x49` | per-size record `+0x1` | **regen rate**. Uniformly **1** across all 174 owned-size records; the init's "default to 4 if zero" branch never fires for a real panel | **CONFIRMED** |

> **Correction to the HP citation below.** This document cites `0x021DF1D5` as "Player 1 HP". Two
> problems, both since established: HP is a **u16** and that address is only its **high byte** (the
> 1/4-scale reading), and absolute battle addresses are **session-local** — the same struct was seen at
> `0x021DF19C` and `0x021DF1B4` in different sessions. Use the struct offset `+0x18`, and locate the
> struct with `scripts/emu/find_battle_structs.py`.

> **Struct identity caveat.** This document's map came from GDB on base pointers `0x021E2A7C`+ (wifi
> mode); the table above came from static analysis of the init function. They are **plausibly** the same
> struct type — the offsets don't collide and K3's fields land in regions this document marks unknown —
> but that identity is not proven. `Battle-Engine-Map.md`'s open question **B10** is the same question.

---

## Complete Struct Map

| Offset              | Size | Name                        | Research Status   | Notes                                                                                                                        |
| ------------------- | ---- | --------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **0x0000 - 0x003F** | 64   | ~~Physics Region~~          | ❌ **DISPROVEN**  | Old hypothesis (X/Y position + velocity in first 64 bytes). 2026-02-03 GDB session showed physics deltas live at +0x006A-0x00BA instead. |
| 0x0000 - 0x003F     | 64   | Unknown                     | ❓ Unknown        | Purpose unknown (NOT position/velocity)                                                                                       |
| **0x0040 - 0x0069** | 42   | Unknown                     | ❓ Unknown        | Gap before physics/velocity region                                                                                             |
| **0x006A - 0x00BA** | 81   | **Physics/Velocity Region** | ⚠️ **LIKELY**     | 2026-02-03 GDB: fields `+0x006A/6C`, `+0x0072/74`, `+0x007A/7C` show large deltas during knockback. Exact velocity field not yet isolated. |
| **0x0078**          | 1    | **Ground/Air/Hitstun State**| ✅ **KNOWN**      | `0x00` = In Air, `0x22` = On Ground, `0xC0` = **Launched/Hitstun** (state FLAG, not a timer; 2026-02-03 GDB)                   |
| **0x0079 - 0x0087** | 15   | Unknown                     | ❓ Unknown        | Within physics region - might contain fall velocity or air physics                                                             |
| **0x0088**          | 1    | **Positive Status ID**      | ✅ **KNOWN**      | `0x00` = Nothing, `0x09` = Invincibility (visual only?)                                                                        |
| **0x0089 - 0x0097** | 15   | Unknown                     | ❓ Unknown        | Gap before countdown timer region                                                                                              |
| **0x0098 - 0x00BA** | 35   | **Countdown Timer Region**  | ⚠️ **LIKELY**     | 2026-02-03 GDB: timers at `+0x0098/9A`, `+0x00A0/A2`, `+0x00A8/AA`, `+0x00B0/B2`, `+0x00B8/BA`. Decrement in -5/-3 alternating pattern (32-bit values read as 16-bit?). Run during hitstun/recovery. |
| **0x00A0**          | 1    | **Negative Status Flags**   | ✅ **KNOWN**      | Bit flags for negative status effects (immune to negative status cheat). NOTE: overlaps timer region above - needs reconciliation. |
| **0x00BB - 0x00D8** | 30   | **Combat State Region**     | 🔍 **CANDIDATE**  | Remaining unknown region - possibly attack frame counter, guard state                                                          |
| **0x00D9**          | 1    | **Jump Counter**            | ✅ **KNOWN**      | Number of jumps remaining (infinite jumps cheat)                                                                               |
| **0x00DA**          | 1    | **Air Action Counter**      | ✅ **KNOWN**      | Number of air actions remaining (infinite air actions cheat)                                                                   |
| **0x00DB - 0x00F1** | 23   | Unknown                     | ❓ Unknown        | Gap between air actions and defense timer                                                                                      |
| **0x00F0 - 0x0101** | 18   | **Timer Region**            | 🔍 **CANDIDATE**  | Around defense timer - might contain other timers (stun, guardstun, etc.)                                                      |
| **0x0102**          | 1    | **Defense Duration**        | ✅ **KNOWN**      | Defense timer (defense never wears cheat)                                                                                      |
| **0x0103+**         | ?    | Unknown                     | ❓ Unknown        | Struct continues beyond 0x102 (exact size unknown)                                                                             |

---

## Known Fields Detail

### Ground/Air/Hitstun State (`+0x0078`)

| Value  | Meaning              | Source                            |
| ------ | -------------------- | --------------------------------- |
| `0x00` | In Air               | "Always on Ground/Air" cheat code |
| `0x22` | On Ground            | "Always on Ground/Air" cheat code |
| `0xC0` | Launched/Hitstun     | 2026-02-03 GDB session            |

**Research Notes:**

- Single byte field
- Changes when character jumps or lands
- `0xC0` (192) is a state FLAG indicating launched/hitstun, NOT a timer
  (confirmed 2026-02-03 GDB session)
- Used by `jus-auto-snapshot-on-state` trigger

### Positive Status (`+0x0088`)

| Value  | Meaning                      | Source                            |
| ------ | ---------------------------- | --------------------------------- |
| `0x00` | No positive status           | "Have Positive Status" cheat code |
| `0x09` | Invincibility (visual only?) | "Have Positive Status" cheat code |

**Research Notes:**

- Single byte field
- May encode buffs, invulnerability states
- Other values unknown - need testing

### Negative Status Flags (`+0x00A0`)

| Value     | Meaning                         | Source                                 |
| --------- | ------------------------------- | -------------------------------------- |
| Bit flags | Various negative status effects | "Immune to negative status" cheat code |

**Research Notes:**

- Single byte field (bit flags)
- May encode debuffs, hitstun, stun states
- Bit meanings unknown - need testing

### Jump Counter (`+0x00D9`)

| Value | Meaning                   | Source                      |
| ----- | ------------------------- | --------------------------- |
| 0-255 | Number of jumps remaining | "Infinite Jumps" cheat code |

**Research Notes:**

- Decrements on each jump
- Resets on landing?
- Used to enforce jump limits

### Air Action Counter (`+0x00DA`)

| Value | Meaning                         | Source                            |
| ----- | ------------------------------- | --------------------------------- |
| 0-255 | Number of air actions remaining | "Infinite Air Actions" cheat code |

**Research Notes:**

- Decrements on air attacks/dashes
- Resets on landing?
- Used to enforce air action limits

### Defense Duration (`+0x0102`)

| Value | Meaning                 | Source                           |
| ----- | ----------------------- | -------------------------------- |
| 0-255 | Defense timer countdown | "Defense never wears" cheat code |

**Research Notes:**

- Timer that decrements while defending
- When reaches 0, defense ends?
- Exact behavior unknown

---

## Candidate Regions for Research

### ~~1. Physics Region (`0x0000 - 0x003F`)~~ - DISPROVEN

**Old hypothesis:** Contained position and velocity data in the first 64 bytes.

**DISPROVEN (2026-02-03 GDB session):** Movement/knockback snapshots showed no
physics deltas in this range. Physics/velocity data lives in the
`+0x006A - 0x00BA` region instead (see below).

### 1. Physics/Velocity Region (`0x006A - 0x00BA`) - LIKELY

**Finding (2026-02-03 GDB session):** Fields `+0x006A/6C`, `+0x0072/74`, and
`+0x007A/7C` show large deltas during knockback.

**Still open:**

- Exact velocity field not yet isolated (light vs heavy comparisons showed
  differences, but position/timing variations made isolation difficult)
- Which fields are position vs velocity vs derived values

**GDB Commands:**

```gdb
jus-char-dump 1 0x60 0x60      # Dump physics/velocity region
jus-velocity-watch 1           # Monitor physics region
jus-baseline-noise 1 5 idle    # Filter timer noise first
```

### 2. Air Physics Region (`0x0070 - 0x0088`)

**Hypothesis:** Contains fall velocity or air-specific physics near ground/air
state (overlaps the physics/velocity region above)

**Research Strategy:**

- Compare snapshots: ground idle vs air falling
- Look for values that correlate with fall speed
- May contain vertical velocity when airborne

**GDB Commands:**

```gdb
jus-auto-snapshot-on-state 1 air_physics
# Jump/land to trigger snapshots
jus-char-diff air_physics_state1 air_physics_state2
```

### 3. Countdown Timer Region (`0x0098 - 0x00BA`) - LIKELY

**Finding (2026-02-03 GDB session):** Contains countdown timers that run
during hitstun/recovery:

- Fields: `+0x0098/9A`, `+0x00A0/A2`, `+0x00A8/AA`, `+0x00B0/B2`, `+0x00B8/BA`
- Decrement in a -5/-3 alternating pattern (suggests 32-bit values read as
  16-bit halves)
- Heavier characters (Raoh) show longer timer activity than lighter (Nami)

**Still open:**

- Which specific timer controls hitstun vs recovery vs other states
- Mapping of jpower hitstun values to timer initial values
- Reconciling with the known Negative Status Flags byte at `+0x00A0`

**GDB Commands:**

```gdb
jus-auto-snapshot-on-hit 1 combat
# Take damage to trigger
jus-char-diff combat_hit1 combat_hit2
```

### 4. Timer Region (`0x00F0 - 0x0101`)

**Hypothesis:** Contains additional timers near defense timer

**Research Strategy:**

- Compare snapshots: different combat states
- Look for values that decrement over time
- May contain: guardstun timer, stun timer, recovery timer

**GDB Commands:**

```gdb
jus-char-dump 1 0xF0 0x20      # Dump timer region
jus-baseline-noise 1 5 idle    # Identify timer noise
```

---

## Research Workflow

### Step 1: Baseline Noise Filtering

**Goal:** Identify timer fields that change even when idle (noise to filter out)

```gdb
# 1. Get into battle, have characters stand still
# 2. Capture baseline snapshots
jus-baseline-noise 1 5 idle

# 3. Identify timer fields
jus-find-timers idle

# Result: Fields that always change are timers - ignore these in physics analysis
```

### Step 2: Velocity Discovery

**Goal:** Find position and velocity fields

```gdb
# 1. Capture snapshots during movement
jus-burst-snapshot 10 walking 1

# 2. Compare first and last snapshot
jus-char-diff walking_0 walking_9

# 3. Look for fields with large deltas (position) or consistent changes (velocity)
# Filter out timer fields identified in Step 1
```

### Step 3: Hitstun/Knockback Discovery

**Goal:** Find hitstun timer and knockback velocity

```gdb
# 1. Set up automated capture on hit
jus-auto-snapshot-on-hit 1 hit

# 2. Resume game and take damage
continue

# 3. Compare snapshots before/after hit
jus-char-diff hit_hit1 hit_hit2

# 4. Look for:
#    - Timer that appears/disappears (hitstun)
#    - Velocity spike (knockback)
#    - Status field changes
```

### Step 4: Status Field Decoding

**Goal:** Understand status flag meanings

```gdb
# 1. Watch status changes
jus-auto-snapshot-on-status 1 status both

# 2. Resume game, trigger various status effects
continue

# 3. Analyze snapshots to correlate status values with game state
jus-char-diff status_positive1 status_positive2
```

---

## Struct Size Analysis

**Minimum Size:** `0x102` bytes (258 bytes) - based on highest known offset

**Likely Size:** `0x120` bytes (288 bytes) - common struct alignment, matches
GDB dump size

**Maximum Size:** Unknown - may extend beyond 0x120

**Evidence:**

- Known offsets scattered: 0x78, 0x88, 0xA0, 0xD9, 0xDA, 0x102
- Large gaps suggest struct is not densely packed
- May contain padding or reserved fields

---

## Memory Access Pattern

### Local Battle Mode

- Direct memory addresses (e.g., `0x021DF1D5` for Player 1 HP)
- Character struct may be at fixed addresses

### Wifi Battle Mode

- Pointer-indirect access
- Base pointers at: `0x021E2A7C`, `0x021E2A80`, `0x021E2A84`, `0x021E2A88`
- Character struct accessed via: `[pointer] + offset`

**Example (Player 1, wifi mode):**

```python
ptr = read_dword(0x021E2A7C)  # Get character struct pointer
ground_state = read_byte(ptr + 0x0078)  # Read ground/air state
```

---

## Related Documentation

- `Cheat-Code-Analysis.md` - Source of known offsets
- `scripts/gdb/jus_gdb_watcher.py` - GDB tools for struct research
- `Combat-Mechanics-Reference.md` - Game mechanics context

---

## Research Status Summary

| Category              | Status        | Count    |
| --------------------- | ------------- | -------- |
| ✅ Known Fields       | Documented    | 6        |
| ⚠️ Likely Regions     | GDB-supported | 2        |
| 🔍 Candidate Regions  | Identified    | 2        |
| ❌ Disproven Regions  | Retired       | 1        |
| ❓ Unknown Regions    | Need Research | ~15 gaps |

**Next Steps:**

1. Isolate the exact velocity fields within `+0x006A - 0x00BA`
2. Map jpower hitstun values to the `+0x0098 - 0x00BA` countdown timers
3. Reconcile Negative Status Flags (`+0x00A0`) with the timer region overlap
4. Decode status flag bit meanings

---

_Last updated: 2026-07-01 (folded in 2026-02-03 GDB findings)_ _Research tool:
`scripts/gdb/jus_gdb_watcher.py`_
