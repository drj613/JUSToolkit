# Loop-Atlas 224 — the ability list has two sources, and eight ids never join it

Claims in beads: [`jus-second-ability-source-0x558-5rp`],
[`jus-ondisk-ability-list-at-chrb-0x03-kfc`].

The question "what appends `0x0E` to Luffy's live ability list" has been open since before this session. The answer: the list is built from **two** sources, and only one is the character record.

## Two callers to the append primitive

`arm9 0x02077A74` is `AddAbility(char, id)` — skips `0`, caps at 15, writes count to `char+0x1A` and id to `char+0x1B + count`. Both call sites live inside `0x02077768`.

The first is the five-slot loop over the `chr_b` record. The second walks a linked list:

```
0x02077830  ldr  sb, [sl, #0x558]   ; list head at battleObj+0x558
0x02077844  ldrb r0, [sb, #0x40]    ; node type
0x02077848  cmp  r0, #2             ; type-2 nodes only
0x02077854  ldrb r1, [sb, #0x41]    ; the node's ability id
0x02077858  ldr  r2, [r0, #0x50]    ; the same kind table the slot loop uses
0x02077884  bl   0x020779CC         ; eligibility gate — returns 0 or a pointer
0x02077890  ldrb r1, [sb, #0x41]
0x02077894  bl   0x02077A74         ; append
```

Luffy's `0x0E` is in his live list but **not** in his record slots — it came through here. `+0x558` already appears in `Battle-Engine-Map.md` as "the `+0x558` dynamic Meter-node list," the leading candidate for the second gauge. Same list, different consumer.

## `ability.bin` is the kind table

228 bytes, 57 entries of 4, indexed by ability id. Byte 0 is the kind:

| kind | ids | count | behaviour |
|---|---|---|---|
| 0 | 0–37 | 38 | append |
| 1 | 38–48 | 11 | append |
| 2 | 49–56 | 8 | **never append** — call a handler from `0x0209F544` |

Handlers: ids 49/50/51 all → `0x0207793C`; 52 → `0x02077974`; 53 → `0x020779A4`; 54 → `0x02077944`; 55 → `0x02077954`; 56 → `0x02077964`. Byte 1 of each entry is the handler index; byte 2 is non-zero for ids 52, 54, 55, and 56 (`0x08`, `0x01`, `0x03`, `0xFD`) — likely a parameter.

**Eight ability ids are not abilities in the list sense.** They dispatch to handlers and never reach `char+0x1B`. This supersedes "the loader compacts non-zero slots" — some slots go elsewhere entirely. Ability id 14 is kind 0 and appends normally, so Luffy's `0x0E` needs no exotic explanation beyond identifying which node carried it.

## The eligibility gate (and a koma-shaped lead, unasserted)

```
0x020779D0  ldrb r2, [r1, #0x0f]
0x020779D4  ands r2, r2, #0x0f      ; reject 0
0x020779E0  cmp  r2, #4             ; reject > 4
0x020779EC  ldrb lr, [r1, #0x0e]
0x020779F8  and  r2, lr, #0xf0
```

Then two table lookups. A field constrained to `1..4` gating whether a node's ability applies has the same cardinality as the nature enum (力/知/笑/なし) and as a koma panel count. Suggestive, nothing more — `[node+0x0E]` and `[node+0x0F]` remain unidentified.

## What runtime could settle in one read

Walk `battleObj+0x558`, print each node's `+0x40` and `+0x41`, confirm a type-2 node carrying `0x0E` exists for Luffy. The same read dumps the entire second ability source.

## Provenance

Static only. `jus_files/arm9/arm9.bin`, listing `jus_files/analysis/disasm/arm9.txt`, and `jus_files/ripped_jus_files/bin/ability.bin`. Handler pointers read from `arm9.bin` at `addr − 0x02000000`, independent of the listing — two artifacts. No codex pass: the load-bearing claims are a call-site enumeration and a loop bound, both read directly from instructions. Handing codex the same listing would be one artifact twice.
