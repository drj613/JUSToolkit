Here's the rewrite:

---

# C6e — accumulator refuted; constrained scan finds the real HP-writer set

Loop-Atlas iteration 25.

## The accumulator is dead

A breakpoint at `0x0215A30C` logged `r1 = 0` on all 8 unconditional hits during a run where two **6.000** hits landed. The site fires; it never carries damage. The melee hypothesis is dead. Details and the harness caveat are in `c6c-damage-accumulator.md`.

## The constrained scan — and what it actually found

Fallback approach: filter `strh [rN,#0x18]` writers by requiring a `ldrsh [SAME rN,#0x16]` within ±8 instructions. A real HP writer has to read max HP to clamp, and requiring the **same base register** ties both accesses to one struct.

**226 sites down to 17.** That's the constraint working. This is the discipline I should have used from the start.

One hit in ov6: `0x02160738`. It's not damage — it's a **serialiser**:

```asm
0x0216071C  ldrsh r0,[r9,#0x16] ; ldrb r1,[r9,#0x4E] ; bl 0x0200D12C ; strh r0,[r9,#0x16]
0x0216072C  ldrh  r0,[r9,#0x18] ; ldrb r1,[r9,#0x4E] ; bl 0x0200D338 ; strh r0,[r9,#0x18]
0x0216073C  ldrh  r0,[r9,#0x1A] ; ldrb r1,[r9,#0x4E] ; bl 0x0200D338 ; strh r0,[r9,#0x1A]
```

Every field from `+0xE` to `+0x1C` runs through the same transform with `[r9+0x4E]` as a mode byte — an endian-swap or save/load walker. The "clamp read" my filter matched was just `+0x16` taking its turn in the sequence.

**No melee-specific HP writer exists in the battle overlay.**

## What this means

HP can only change through a store to `+0x18`. All 17 constrained hits resolve to **8 distinct arm9 functions**:

| function | writes at | ov6 callers |
|---|---|---|
| `0x020772E4` | `0x0207738C` | 0 |
| `0x02077768` | `0x0207799C` | 0 |
| `0x02077C0C` | `0x02077C64` | 0 |
| `0x02077CB8` | `0x02077CFC` | 0 |
| `0x02077D40` | 6 sites (`0x02077DA4`–`0x02077E60`) | 0 |
| `0x02078428` | `0x0207845C`, `0x02078474`, `0x020784A0` | 2 |
| `0x020785B8` | `0x02078604` | 1 |
| **`0x02078660`** | `0x02078754`, `0x02078778` | **9** |

Note: `0x02078428` *contains* `0x02078488` — the core apply is a **mid-function entry point**, not a function start. That's why the thunk has 14 callers while the enclosing function has 2.

**`0x02078660` has 9 ov6 call sites I'd never looked at**: `0x02150516`, `0x02150592`, `0x02150906`, `0x02157D44`, `0x0215AC4C`, `0x0215CAA8`, `0x0215CAF0`, `0x0215CCE8`, `0x0215CE40` (4 Thumb, 5 ARM).

## New lead: the +0x558 node list

Both unexamined functions open the same way:

```asm
0x02078660  push {...} ; sub sp,sp,#8 ; ldr r3,[r0,#0x558]   ; null-check, bail
0x0207867C  ldrb r12,[r3,#0x40]  ; test
0x02078688  ldr  r12,[r3,#0x3C]  ; tst r12,#0x1000
```

```asm
0x020785B8  push {...} ; ldr r5,[r0,#0x558] ; mov r6,r1 ; null-check
0x020785CC  mov r4,#0x64          ; 100 — a percentage divide
```

They **walk a list at `+0x558`**, checking a byte flag at node `+0x40` and bit-testing a word at node `+0x3C`. The list-variant apply `0x020783DC` also opens with `ldr r4,[r0,#0x558]`.

`Battle-Engine-Map.md` already names `+0x558` as "the `+0x558` Meter-node list" — the leading candidate for the guard/SP-gauge subsystem (campaign item B12, marked DONE). So this is a known structure being used by HP-modifying code nobody had connected to it.

**A list walk fits melee**: a hitbox can strike several entities, so hit resolution could build a node list and this function could apply the result to each. It also matches the repeated finding that the delta arrives pre-computed.

Confidence: **SPECULATIVE.** I haven't read the 9 call sites, and a `+0x558` walker with a divide-by-100 could just as easily be a meter/gauge routine — which is what B12 concluded the list was for.

## Next

Classify the 9 ov6 callers of `0x02078660`, and read the `0x0215CBEC` caller of the multiplicative `0x020785B8`. Both are static, both are bounded, and neither needs the emulator.

## Method note, third time

Two of my three scans this session produced confident false positives from **offset-only matching** (`+0x18` → 226 hits, `+0x140` → a vtable initialiser). The constrained version cut 226 to 17 and was still wrong about its single ov6 hit — but wrong in a way I could *see*, because 17 sites are readable and 226 aren't. The lesson isn't just "constrain the scan" — it's **constrain it enough that you can read every hit**.
