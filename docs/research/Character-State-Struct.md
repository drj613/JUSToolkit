# In-Battle Character State Struct

Comprehensive mapping of the character state structure in Jump Ultimate Stars battle RAM.

**Source:** Action Replay code analysis + GDB memory research  
**Base Pointers:** `0x021E2A7C`, `0x021E2A80`, `0x021E2A84`, `0x021E2A88` (4 players, wifi mode)  
**Struct Size:** At least `0x102+` bytes (~260+ bytes)  
**Access Pattern:** Pointer-relative offsets (fields are scattered, not contiguous)

---

## Complete Struct Map

| Offset | Size | Name | Research Status | Notes |
|--------|------|------|-----------------|-------|
| **0x0000 - 0x003F** | 64 | **Physics Region** | 🔍 **CANDIDATE** | Likely contains X/Y position and velocity. First 64 bytes of struct. |
| 0x0000 | 2 | Unknown (word) | ❓ Unknown | Potential X position (signed 16-bit) |
| 0x0002 | 2 | Unknown (word) | ❓ Unknown | Potential Y position (signed 16-bit) |
| 0x0004 | 2 | Unknown (word) | ❓ Unknown | Potential X velocity (signed 16-bit) |
| 0x0006 | 2 | Unknown (word) | ❓ Unknown | Potential Y velocity (signed 16-bit) |
| 0x0008 - 0x003F | 56 | Unknown | ❓ Unknown | Additional physics/position data (rotation? hitbox offsets?) |
| **0x0040 - 0x0077** | 56 | Unknown | ❓ Unknown | Gap between physics region and ground/air state |
| **0x0078** | 1 | **Ground/Air State** | ✅ **KNOWN** | `0x00` = In Air, `0x22` = On Ground |
| **0x0079 - 0x0087** | 15 | Unknown | ❓ Unknown | Near ground/air state - might contain fall velocity or air physics |
| **0x0088** | 1 | **Positive Status ID** | ✅ **KNOWN** | `0x00` = Nothing, `0x09` = Invincibility (visual only?) |
| **0x0089 - 0x009F** | 23 | Unknown | ❓ Unknown | Gap between positive and negative status fields |
| **0x00A0** | 1 | **Negative Status Flags** | ✅ **KNOWN** | Bit flags for negative status effects (immune to negative status cheat) |
| **0x00A1 - 0x00D8** | 56 | **Combat State Region** | 🔍 **CANDIDATE** | Large unknown region - likely contains hitstun timer, knockback state, attack state |
| 0x00A1 - 0x00D8 | 56 | Unknown | ❓ Unknown | Potential fields: hitstun timer, knockback velocity, attack frame counter, guard state |
| **0x00D9** | 1 | **Jump Counter** | ✅ **KNOWN** | Number of jumps remaining (infinite jumps cheat) |
| **0x00DA** | 1 | **Air Action Counter** | ✅ **KNOWN** | Number of air actions remaining (infinite air actions cheat) |
| **0x00DB - 0x00F1** | 23 | Unknown | ❓ Unknown | Gap between air actions and defense timer |
| **0x00F0 - 0x0101** | 18 | **Timer Region** | 🔍 **CANDIDATE** | Around defense timer - might contain other timers (stun, guardstun, etc.) |
| **0x0102** | 1 | **Defense Duration** | ✅ **KNOWN** | Defense timer (defense never wears cheat) |
| **0x0103+** | ? | Unknown | ❓ Unknown | Struct continues beyond 0x102 (exact size unknown) |

---

## Known Fields Detail

### Ground/Air State (`+0x0078`)

| Value | Meaning | Source |
|-------|---------|--------|
| `0x00` | In Air | "Always on Ground/Air" cheat code |
| `0x22` | On Ground | "Always on Ground/Air" cheat code |

**Research Notes:**
- Single byte field
- Changes when character jumps or lands
- Used by `jus-auto-snapshot-on-state` trigger

### Positive Status (`+0x0088`)

| Value | Meaning | Source |
|-------|---------|--------|
| `0x00` | No positive status | "Have Positive Status" cheat code |
| `0x09` | Invincibility (visual only?) | "Have Positive Status" cheat code |

**Research Notes:**
- Single byte field
- May encode buffs, invulnerability states
- Other values unknown - need testing

### Negative Status Flags (`+0x00A0`)

| Value | Meaning | Source |
|-------|---------|--------|
| Bit flags | Various negative status effects | "Immune to negative status" cheat code |

**Research Notes:**
- Single byte field (bit flags)
- May encode debuffs, hitstun, stun states
- Bit meanings unknown - need testing

### Jump Counter (`+0x00D9`)

| Value | Meaning | Source |
|-------|---------|--------|
| 0-255 | Number of jumps remaining | "Infinite Jumps" cheat code |

**Research Notes:**
- Decrements on each jump
- Resets on landing?
- Used to enforce jump limits

### Air Action Counter (`+0x00DA`)

| Value | Meaning | Source |
|-------|---------|--------|
| 0-255 | Number of air actions remaining | "Infinite Air Actions" cheat code |

**Research Notes:**
- Decrements on air attacks/dashes
- Resets on landing?
- Used to enforce air action limits

### Defense Duration (`+0x0102`)

| Value | Meaning | Source |
|-------|---------|--------|
| 0-255 | Defense timer countdown | "Defense never wears" cheat code |

**Research Notes:**
- Timer that decrements while defending
- When reaches 0, defense ends?
- Exact behavior unknown

---

## Candidate Regions for Research

### 1. Physics Region (`0x0000 - 0x003F`)

**Hypothesis:** Contains position and velocity data

**Research Strategy:**
- Use `jus-char-dump` to view raw bytes
- Compare snapshots during movement vs idle
- Look for signed 16-bit values that change smoothly during movement
- Filter out timer fields using `jus-baseline-noise` first

**Expected Fields:**
- X position (signed 16-bit, likely at 0x0000 or 0x0002)
- Y position (signed 16-bit)
- X velocity (signed 16-bit)
- Y velocity (signed 16-bit)
- Possibly: rotation angle, hitbox offsets

**GDB Commands:**
```gdb
jus-char-dump 1 0 0x40        # Dump physics region
jus-velocity-watch 1           # Monitor physics region
jus-baseline-noise 1 5 idle    # Filter timer noise first
```

### 2. Air Physics Region (`0x0070 - 0x0088`)

**Hypothesis:** Contains fall velocity or air-specific physics near ground/air state

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

### 3. Combat State Region (`0x00A1 - 0x00D8`)

**Hypothesis:** Contains hitstun timer, knockback velocity, attack state

**Research Strategy:**
- Compare snapshots: idle vs hit vs in hitstun
- Use `jus-auto-snapshot-on-hit` to capture on damage
- Look for:
  - Timer that decrements (hitstun countdown)
  - Velocity values that spike on hit (knockback)
  - Attack frame counter

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

**Likely Size:** `0x120` bytes (288 bytes) - common struct alignment, matches GDB dump size

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

| Category | Status | Count |
|----------|--------|-------|
| ✅ Known Fields | Documented | 6 |
| 🔍 Candidate Regions | Identified | 4 |
| ❓ Unknown Regions | Need Research | ~15 gaps |

**Next Steps:**
1. Run baseline noise filtering to identify timer fields
2. Capture movement snapshots to find velocity fields
3. Capture hit snapshots to find hitstun/knockback fields
4. Decode status flag bit meanings

---

_Last updated: 2026-01-31_  
_Research tool: `scripts/gdb/jus_gdb_watcher.py`_
