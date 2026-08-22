---
name: dream-attack-and-touch-mechanics
description: "Touch-screen tapping drives dream attacks, character switching, and support summons; chained taps scale a finishing special's damage"
metadata: 
  node_type: memory
  type: project
  originSessionId: 329d0fef-b7f8-4c51-a5ce-144e785cd796
  modified: 2026-08-20T02:44:51.633Z
---

Owner-supplied live-play ground truth for in-battle touch controls (not derivable from the repo).

**Tapping the currently-active character** makes it perform a **dream attack** — typically a different, quicker version of another move already in that character's base moveset.

**Chaining.** After a dream attack, tapping a *different* character in your deck switches to that character and *they* perform a dream attack. This can continue across characters. When the chain returns to the **original** character, tapping them produces a **special attack** instead — an **up-special if you hold up while tapping**.

**Damage scaling.** That finishing special deals **more damage the more characters were tapped in between**. So the chain length is a damage input, which makes this a multiplier-like mechanic distinct from the flat/resistance behaviour recorded elsewhere.

**Support characters.** Tapping a support character summons it to do something — attack, heal, displacement, or apply a status effect.

**Confirmed 2026-08-19, owner direct answer:** it's an instant tap on any battle or support character panel — there is no cursor or highlight to move first, and no separate select-then-confirm step. This rules out the "the cycling red-border animation is a selection cursor you tap against" hypothesis raised during the touch-input investigation — that animation is unrelated to input entirely (see the retracted red-border evidence in `[[dream-attack-and-touch-mechanics]]`'s own history / bead `jus-nature-menu-not-in-these-modes-43m`). Since instant taps at multiple guessed coordinates (owner-outlined and screenshot-derived) have all nulled on opponent HP so far, the remaining open question is pure coordinate/target-identification, not timing or a cursor mechanic.

Research implications: the chain counter is state the battle engine must hold somewhere, and the dream-attack variant of a move implies a per-move variant selector. Both are static-analysis targets. Related: [[koma-system-observed-behavior]] (owner supplies live-play ground truth on request).

**RETRACTED 2026-08-19 (was wrong):** I originally wrote that the manga-panel strip on the bottom screen was static decorative border art because it looked pixel-identical between `fight_base` and `m4_clean`. That comparison doesn't prove what I thought — two savestates built from the same test deck would show identical panel art regardless of whether the region is interactive, so "identical across saves" only shows "same deck," not "inert UI." justoolkit-09 (runtime loop) refuted it directly: on the same savestate, before/after screenshots show two koma panels acquiring red selection borders after a DOWN+DOWN+A sequence, and on `dm_battle` the pause menu renders on top of exactly that region. Neither happens to static art. The region IS live. See bead `jus-nature-menu-not-in-these-modes-43m`.

**Better oracle found 2026-08-19 (runtime loop, end-of-day handoff):** a benched/reserve character regenerates at +1 raw HP unit per frame, so a tap that causes a character SWITCH is detectable from HP data alone — no input log, no screenshot needed. On `m4_clean`, the player's HP starts at 153.0/160.0 (below max), so the regen oracle is live immediately: start a tail, tap, watch for regen onset on whichever slot just got benched. Two limits: only works while that character is below max HP, and it goes dead during sudden death. Also: DJ's actual goal is for an agent session to reproduce a panel tap ITSELF (not have him tap for us) — the touch capability already exists (`input.NDSTapDown` via a plan's `touch` segment), the missing piece was always a success signal, and this regen-onset check is that signal. Candidate coordinate sources not yet fully read: `docs/research/Deck-Editor-Automated.md`, `docs/research/Battle-Engine-Map.md`, and `nav.py:117` (existing DS-coordinate conversion helper).

So the HP-based null from my two tap experiments (6-frame and 90-frame holds at DS(140,90) on `fight_base`, proper baseline-vs-tap-window control, zero HP change either way) still stands as a measurement, but the "wrong target" explanation for it does not — it's back to being a delivery-or-mechanism question. DJ had already outlined the actual candidate region on a screenshot for jus-3aw: x~50-150, y~47-175, specific points (100,100), (95,150), (110,60), (120,120). My (140,90) guess was outside that x-range. Prefer owner-provenance coordinates over screenshot-derived guesses next time.

**Two more corrections, same day.** First, my original HP watch used the wrong address (`0x021DF7EE`, max HP, not `0x021DF7F0`, current HP — see `[[jus-hp-address-current-vs-max]]`), which would have masked a landed hit; a rerun with the corrected address, owner coordinates (100,100), and a live-regen sanity check (player HP visibly climbing in the same window, proving the read wasn't dead) still showed a clean null on opponent HP. Second, the red-selection-border is NOT a reliable positive control after all — a zero-input test (load state, let ~900 frames pass with nothing pressed, screenshot every ~90 frames) showed the border move on its own from one deck panel to another with no input at all, then hold there for 700+ more frames. It's an ambient cycling animation. Any before/after pair that straddles one of its natural transitions will look exactly like "input caused this" whether or not it did — that's what happened with the DOWN+A observation on jus-nature-menu-not-in-these-modes-43m. **Bottom line as of 2026-08-19: touch during battle, at owner-provided coordinates, with a correctly-addressed and regen-sanity-checked HP watch, still produces no observable opponent damage.** Don't trust the border as a control without a matched no-input baseline of the same length.
