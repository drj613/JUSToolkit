---
name: koma-system-observed-behavior
description: Koma nature system is 4 values (Power/Knowledge/Laughter/Neutral) per-panel; owner captured live-play ground truth
metadata: 
  node_type: memory
  type: project
  originSessionId: 0a7773fe-cf57-42c6-b4b3-d4a6ffae4404
  modified: 2026-08-14T14:24:10.304Z
---

As of 2026-08-14 the koma/deckbuilding system has an **OBSERVED** ground-truth doc from a live
melonDS play session the owner walked personally:
`docs/research/Koma-System-Observed-Behavior.md`, with 25 screenshots in
`docs/research/assets/koma-ui/`. Designer-facing twin:
`docs/design/Koma-Deckbuilder-UX-Spec.md`.

Headline facts that static RE had *no* evidence for beforehand: natures are a 4-value enum
(力 Power / 知 Knowledge / 笑 Laughter / なし Neutral) in a triangle, and they are **per-panel,
not per-character** — Naruto has a 4-koma in both 力 and 笑. Panel type is *derived* from size
(Battle 4–8, Support 2–3, Helper 1), not stored separately.

**Why:** the owner can supply live-play evidence on request, which is faster and more reliable
than static analysis for behavior questions. Ask rather than guess.

**How to apply:** treat OBSERVED as outranking CONFIRMED-from-disassembly for *behavior*, but
as silent on byte layout. The doc carries 7 falsifiable predictions for decoding `koma.bin`;
check a decode against the Naruto reference table before believing it.
Related: [[loop-wakeup-pacing]], [[character-mapping-completeness]]
