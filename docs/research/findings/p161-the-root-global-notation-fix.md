# P161 — `0x0214D928` is a pool word, not a global; three new root slots; and repeated process failure

**Iteration 161. Static only.** Goal was to find `0x0214D928`'s writer and allocation size, and decide whether `[0x02172960]` is the battle root. It is — but our own records already said so.

## The fact

`CONFIRMED_STATIC`: **`0x0214D928` is a literal pool word inside ov6, not a global.** It sits at file offset `0xC08` of `ov06.bin`, and the four bytes there are `60 29 17 02` — the value **`0x02172960`**.

The disassembler comment `ldr r0,[pc,#0x198]  ; = 0x0214D928` prints the **address of the pool word**, not its contents. Every note saying "the global `0x0214D928`" actually means "the pool word at `0x0214D928`, whose value is the global `0x02172960`".

`base_offset_scan.py` against `0x0214D928` returns **zero load sites** — correct and telling. Nothing loads that value because it isn't a value; it's a slot things load *from*. The P155 discipline of never accepting a clean negative without checking turned an empty scan into the answer.

Verified in three independent representations:

1. **Raw bytes** at the file offset: `60 29 17 02`.
2. **Encoding arithmetic**, absolute: the Thumb formula `Align(pc+4,4) + imm8*4` from both cited sites — `0x0214D78E` with `imm 0x198`, `0x0214D81C` with `imm 0x108` — both land on `0x0214D928`.
3. **Cold Codex, address-free**: given only a byte blob with offsets and no addresses, it computed the literal at blob offset `0x019A` from PC alignment (deducing the blob must load at `A ≡ 2 (mod 4)`), read out `0x02172960`, and confirmed both loads hit the same word. Blob offset `0x019A` + `0x0214D78E` = `0x0214D928`. It also found a **third** site sharing the pool word that I hadn't listed. Earlier in the same exchange it refused to answer when I mangled the prompt and omitted the data, rather than inventing a decode.

`[0x02172960]` **is** the battle root, and the root **is** the 368-byte object P160 found the allocation for. P160's `PLAUSIBLE` is promoted to `CONFIRMED_STATIC`.

## The process failure

`findings/battle-add-root-object-map.md` already says it plainly: *"`0x0214D668` and `0x0214D928` both hold `0x02172960` — both literal pools reach the same global."* That finding already calls `[0x02172960]` the root object, already knows the allocation is `0x170`, and already maps **11** subsystem slots inside it.

P160 spent a wake reaching `PLAUSIBLE` on something our record had at `CONFIRMED_STATIC`, then queued a "cheap decisive discriminator" for something already decided. The three-way verification above is worth keeping — it genuinely cross-checks a claim the whole root map rests on — but it should have been framed as *confirming a known result*, not resolving an open one.

**Second time in five wakes.** P157 drafted a census of the HP-delta path as new before checking `Battle-Engine-Map.md`, where most of it was already documented. Same failure, same five-second fix skipped twice.

**New hard rule, added to the charter's evidence discipline:** before writing up anything as new, `grep -rl` the claim's key address through `docs/research/findings/` **and** `Battle-Engine-Map.md`. Not the state file — it's 200-plus keys of my own summaries, and it's where I keep re-finding my own uncertainty instead of the record's answers.

## What is actually new: three root slots

`battle-add-root-object-map.md` had 11 offsets, all subsystem pointers in `+0x0D0`–`+0x128`. These three are new, bringing the root map to 14 known offsets:

| offset | what the code does with it | source |
|---|---|---|
| `+0x4C` | base of a per-character word array, stride 4, indexed by a character index | ov6 `0x02158F78`, arm9 `0x0208552C` |
| `+0x158` | character count; used as `count - 1` to clamp a character index | arm9 `0x0208550C`, and P151's setup-loop bound |
| `+0x15C` | an index into the `+0x4C` array | arm9 `0x02085524` |

`+0x158` matching P151's independently-found setup-loop bound is now a cross-check, not a coincidence — both sides are confirmed to reference the same object.

## The `+0x4C` contradiction, unresolved

Two sites read `root+0x4C` and disagree about what's in it.

- ov6 `0x02158F78` uses it as a **multiplier**: `duration = base + (base/10) * (V*2)`, the only non-constant scaling formula this campaign has found.
- arm9 `0x0208552C` **compares an entry for equality** against a character index clamped to `[root+0x158] - 1`, then makes a vtable call with `1` or `0`.

A magnitude doesn't fit the second use; an index doesn't sensibly fit the first. One reading is wrong and I can't tell which statically. `not claimed` either way — P160's retraction of the "per-character stat" label stands, no replacement offered.

**Sent to `justoolkit-ed`** for a runtime read — live values settle it in one shot. Small values in `0..N-1` mean it's an index array and the duration formula is stranger than it looks; stat-shaped values mean I've misread the arm9 site. Reachability was verified before asking, per standing agreement — 255 pc-relative loads in ov6 plus the two-write lifecycle from P160.

Also **corrected the anchor previously sent them**: `[0x0214D928] → root → [root+0x110] → ObjShot manager`. The pointer chain is right; the global was not. Corrected to `[0x02172960]`. Passed on the P160 caution that "N literal loads" figures are severe floors wherever Thumb code touches an address.

## Record normalised

Fixed misleading phrasing in `Battle-Engine-Map.md`, `HANDOFF-Loop-Atlas-P156.md`, and `findings/chara-setup-loop-has-three-descriptor-paths.md`. Left the raw disassembly comments in `findings/objshot-manager-and-the-27-kind-dispatch-table.md` alone — `; = 0x0214D928` is the tool's own output and is correct on its own terms; the prose built on it was what needed fixing.
