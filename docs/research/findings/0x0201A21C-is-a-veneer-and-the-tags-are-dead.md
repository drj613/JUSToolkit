# Findings: `0x0201A21C` is a linker veneer, the real allocator is `0x0201A228`, and the tags are dead at runtime

Loop-Atlas iteration 133. Static.

All three overridden vtable slots from iteration 132 resolved. Chasing one of them revealed something
larger about the allocator every previous iteration relied on.

1. **Slot `+0x18` is `Clone`, confirmed at both levels.** The parent version allocates `0x80`; the derived
   version allocates `0x84` — consistent with the derived class adding a halfword at `+0x80`.
2. **Slots `+0x00` and `+0x04` are the destructor pair.** Standard ARM C++ vtable layout.
3. **`0x0201A21C` is a 12-byte linker veneer.** The real allocator is `0x0201A228`, and it **discards** the
   `__FILE__`/`__FUNCTION__`/`__LINE__` arguments — they are computed at every call site and thrown away.
4. Iteration 129's "notify" label for vtable `+0x18` is **dropped**: wrong under either reading.

---

## 1. `+0x18` is Clone, at both levels

```
0x0204B0C8  push {r4, lr}          ; the PARENT's +0x18
0x0204B0CC  mov  r4, r0            ; r4 = this
0x0204B0D0  mov  r0, #0x80         ; allocate 0x80
0x0204B0D4  bl   #0x201a228
0x0204B0D8  cmp  r0, #0
0x0204B0DC  popeq {r4, pc}         ; failed -> NULL
0x0204B0E0  mov  r1, r4            ; src = this
0x0204B0E4  bl   #0x2015e14        ; copy-construct(new, this)
0x0204B0E8  pop  {r4, pc}
```

Allocate, copy-construct from `this`, return the new object. That is a clone. It also settles iteration
132's naming question at the parent level.

**The sizes match the layout.** The parent clones `0x80` bytes; `CloneMain` clones `0x84` (iteration 131).
The derived class adds a halfword at `+0x80`, so `0x80` + 2 bytes rounds up to `0x84`. Two
independently-read allocation sizes agree with a member offset found through a different path.

## 2. `+0x00` and `+0x04` are the destructor pair

```
0x0206D010  push {r4, lr}          ; slot +0x00
0x0206D014  mov  r4, r0
0x0206D018  bl   #0x2015ed8        ; base destructor
0x0206D01C  mov  r0, r4
0x0206D020  pop  {r4, pc}          ; return this

0x0206CFA4  push {r4, lr}          ; slot +0x04
0x0206CFA8  mov  r4, r0
0x0206CFAC  bl   #0x2015ed8        ; the SAME base destructor
0x0206CFB0  mov  r0, r4
0x0206CFB4  bl   #0x201b244        ; then free
0x0206CFB8  mov  r0, r4
0x0206CFBC  pop  {r4, pc}          ; return this
```

Same body, except `+0x04` also calls `0x0201B244`. This is exactly the C++ ABI pair: **`+0x00` =
destructor, `+0x04` = deleting destructor**, with `0x0201B244` (36 bytes, 40 callers) as `operator delete`.
Both return `this`, per the ABI convention.

CommonEffect's entire override set is now named: **destructor, deleting destructor, clone.**

## 3. `0x0201A21C` is a veneer, not the allocator

Every iteration so far has treated `0x0201A21C` as the tagged allocator. It is 12 bytes:

```
0x0201A21C  ldr ip, [pc]     ; loads the word at 0x0201A224
0x0201A220  bx  ip
0x0201A224  .word 0x0201A228
```

`ldr ip,[pc]; bx ip; .word target` is the standard ARM **long-branch veneer** the linker inserts when a
`bl` cannot reach its target. It does nothing but jump to `0x0201A228`.

`0x0201A228` (72 bytes) is the real allocator:

```
0x0201A228  push {r3, lr}
0x0201A22C  ldr  r1, [pc, #0x3c]   ; a global  <-- r1 CLOBBERED
0x0201A230  mov  r2, r0            ; size      <-- r2 CLOBBERED
0x0201A234  cmp  r2, #0x100        ; small vs large split
0x0201A238  ldr  r0, [r1, #0x1a4]  ; the manager
0x0201A23C  bhi  #0x201a264
```

It splits on size against `0x100` and loads the manager from `[global+0x1A4]`.

**The tag arguments are dead.** `r1` and `r2` — `__FILE__` and `__FUNCTION__` at the call site — are
overwritten in the allocator's first two instructions before anything reads them. `r3` (`__LINE__`,
iteration 131) is never read either. This is the familiar pattern of a debug allocator macro left in a
retail build: the strings are still generated at every call site, and the allocator ignores them.

**This does not weaken the census.** The census evidence has always been the **call site**, not the
allocator's behavior — and the census docstring already argues the call site is the stronger binding.
What changes is the runtime model, not the naming.

## 4. Reframing iteration 130's boundary

Iteration 130 found that nothing below `0x0206ADB8` carries an allocation tag, and read that as a
library/game split. Sampling six direct callers of `0x0201A228` shows the mechanism:

| caller | how it sets up |
|---|---|
| `0x02010984` | `mul r0, r1, r0` — size only |
| `0x02010DA4` | `mov r0, #0x78` — size only |
| `0x02011BA8` | `mov r0, #8` — size only |
| `0x02011BC4` | `mov r0, #8` — size only |
| `0x02011C40` | `mov r0, #0x14` — size only |
| `0x02011C7C` | `mov r0, #0x14` — size only |

All six pass **only a size**, and all six sit below the boundary. The split is a **compilation** boundary:
those translation units were built without the tagging macro and call the allocator directly, while
game-side units pass four arguments through the veneer. Two entry points, one allocator.

**A gap in the census, recorded:** `alloc_census.py` scans `ALLOC = 0x0201A21C` only. Any tagged call that
reached `0x0201A228` directly — close enough not to need a veneer — is invisible to it. Whether such sites
exist is **not claimed** (the six sampled are all untagged), but the scan should cover both entry points
before the census is treated as complete.

**An old map note is wrong.** `Battle-Engine-Map.md` line 165 calls `0x0201A228` a "resource-loader thunk",
in a round-1 next-angle already marked a dead end. It is the allocator. Corrected in place.

## Predictions status

| Claim | Verdict |
|---|---|
| Vtable slot `+0x18` is `Clone` at the parent level too | **CONFIRMED_STATIC** — `0x0204B0C8` allocates then copy-constructs from `this` |
| The parent object is `0x80` bytes and the derived `0x84` | **CONFIRMED_STATIC** — `mov r0,#0x80` at `0x0204B0D0` vs `mov r0,#0x84` at `0x0206CFD0` |
| The size difference matches the derived halfword at `+0x80` | **CONFIRMED_STATIC** — `0x80` + 2 rounds to `0x84`, from two independent readings |
| Slot `+0x00` is the destructor, `+0x04` the deleting destructor | **CONFIRMED_STATIC** — identical bodies, `+0x04` adds `bl #0x201b244` |
| `0x0201B244` is `operator delete` | **PLAUSIBLE** — called only in the deleting variant; body not read |
| `0x0201A21C` is the allocator | **REFUTED** — 12-byte veneer: `ldr ip,[pc]; bx ip; .word 0x0201A228` |
| `0x0201A228` is the real allocator | **CONFIRMED_STATIC** — 72 bytes, size split at `0x100`, manager from `[global+0x1A4]` |
| The `__FILE__`/`__FUNCTION__`/`__LINE__` arguments are used at runtime | **REFUTED** — `r1` and `r2` clobbered at `0x0201A22C`/`0x0201A230`; `r3` never read |
| The census's call-site evidence is affected | **not affected** — the binding is at the call site, which is unchanged |
| Library-region callers pass only a size | **CONFIRMED_STATIC** — six sampled, all size-only, all below `0x0206ADB8` |
| Tagged calls also reach `0x0201A228` directly | **not claimed** — none seen in the six sampled; the census should scan both entries to find out |
| `0x0201A228` is a resource-loader thunk | **REFUTED** *(old map note, line 165)* — it is the allocator |
| Iteration 129's vtable `+0x18` is a notify | **REFUTED** — `+0x18` is `Clone` in this family, and the label was never evidenced; dropped either way |

## Next angles, ranked

1. **Extend `alloc_census.py` to scan `0x0201A228` as well as the veneer**, and report which entry each site
   used. This is the one change that could meaningfully grow the census.
2. **Dump the base vtables** set by `0x02021960` and `0x020240A4` (carried) — with `+0x00`/`+0x04`/`+0x18`
   now named, a four-level diff would name every overridden slot.
3. **Read `0x0201B244`** (36 bytes) to confirm `operator delete`, retiring a PLAUSIBLE.
4. **Trace the remaining `+0x24` sites** (carried), now with `0x02021960` as a known-relevant base class.
