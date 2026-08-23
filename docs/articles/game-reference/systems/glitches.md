# Jump! Ultimate Stars — Glitches (distilled)

- Source: "Jump! Ultimate Stars Glitches FAQ" v1.13, by setyman (Rodrigo Medina), Nov 2013
- GameFAQs FAQ id: gf-47980
- Reliability: unverified community claim source — a fan-written glitch list, not verified against game code. Treat all mechanics implied below as hypotheses to confirm against the disassembly/behavior, not ground truth.

Each entry below: setup → observed result → what it implies about internal mechanics (useful for reverse engineering edge-case handling).

## 1. Infinite Time Stop

- Setup: 3-koma Piko (support) + 6-koma Dio or Jotaro (Time Stop special, Up+X), at least 1 SP bar (2 recommended).
- Procedure: Activate Piko support; the instant Piko offers his item bag, activate Dio/Jotaro's Time Stop. Touch Piko's bag, then keep chaining Time Stops.
- Result: SP regenerates *during* the Time Stop special, allowing it to be reactivated indefinitely.
- Side effect: each time Piko's bag is touched, own health decreases (even on failure).
- Variant: works with any support that "gives" something to the player, e.g. 2-koma Chopper (heals repeatedly until SP runs out).
- Implication: SP gauge regeneration is apparently not paused/locked during the "Time Stop" special's active state, and support-item pickup ("touch the bag") triggers can be re-entered while a special's freeze-effect is still resolving — suggests the special's hitstop/freeze state and the SP-regen tick run on independent timers, and support-interaction ("received item") events aren't gated by whether the player is in a special's locked animation.

## 2. Super Satsuki Heal

- Setup: 2-koma Satsuki (support) + a second heal source: another healing support (2-koma Sanji, 3-koma Sakura) or a self-healing battle character (7-koma Kinnikuman, 4-koma Piccolo). Needs 2 SP bars.
- Procedure: activate Satsuki, then trigger the other heal effect.
- Result: healing-over-time rate increases and duration extends ("huge" heal amount, exact multiplier not given).
- Note: also triggerable by 4-koma Nami's SP Steal (not just direct heals).
- Implication: healing is applied as a duration+rate buff/status effect, and multiple heal-effect instances can stack (rate and/or duration additively or multiplicatively) rather than being deduplicated per-target. Satsuki's effect appears to be a generic "amplify next heal status" rather than a heal itself, since it also interacts with an SP-drain effect (Nami's SP Steal).

## 3. Graphical Glitch (animation freeze)

- Setup: 2-koma Hisoka (support).
- Procedure: pick a character special/animation to "freeze" (e.g., 6-koma Allen's Up+X, 5-koma Goku's Kaioken aura, 5-koma Don Patch's Up+X, 8-koma Edajima's X). Activate Hisoka; have Hisoka use his "cape" hit on the character at the same moment the special is used.
- Result: the special's animation pose/effect persists indefinitely (until interrupted).
- Terminating conditions (author states, not "unconfirmed"): using UA, guarding, attacking, or falling through a platform (drop-through) all end the frozen animation.
- Implication: Hisoka's support move likely forces an animation-state override/interrupt onto the target at the same frame the special's animation state is set, causing the state machine to enter a "stuck" animation frame that isn't naturally timed out — only specific *state-transition* inputs (UA/guard/attack/platform-drop) force a state re-evaluation.

## 4. Invincibility Trick

- Setup: 2-player only (Wi-Fi works). Player 1 needs a stun-inducing attack (e.g., 8-koma Vegetto's "Spirit Sword", 5-koma Nami's Tornado Tempo, 6-koma Kenshin's X) and a shock-inducing attack (e.g., 5-koma Killua's Up+X). Player 2 needs any Naruto-series character *except* Kyuubi Naruto.
- Procedure: P2 repeatedly performs their UA. While P2's UA is active, P1 applies the shock effect to P2 with the shock attack. P1 then switches to their other character and, at the moment the shock effect is about to trigger on P2, lands the stun attack.
- Result: P2 becomes invincible to all attacks, supports, everything.
- Single-player variant: on the "Bo^7" stage with stage gimmicks ON, get struck by the stage's lightning gimmick (gives the same shock status), then get hit by a support that also hits you (e.g., 2-koma Josuke).
- Break condition: invincibility ends if the invincible player grabs a ledge.
- Implication: there's a "shock" status and a "stun" status that are apparently distinct hit-reaction states; landing a stun hit at the exact frame a shock status is about to apply (while the target is also mid-UA, an actionless/locked state) seems to corrupt the hit-reaction/invincibility-frame bookkeeping, leaving the character permanently flagged invulnerable until a ledge-grab state transition resets it. Kyuubi Naruto is explicitly excluded — his UA presumably differs enough (no vulnerable window / different state) to not trigger it.

## 5–7. Inside The Wall I / II / III (getting a hitbox/character model inside wall geometry)

Common requirement: Raoh (Hokuto no Ken), any koma — his oversized character model is the key ingredient.

- **Inside The Wall I**: Requires a wall configuration where the walls adjacent to a target wall are destroyed (pattern: destroyed-wall, target wall, destroyed-wall, stacked vertically). Jump toward the target wall as if to ledge-grab it from the "wrong" (opposite) side. Raoh ends up lodged inside a small part of the wall due to his large model/hitbox. Notes: works because Raoh's model is large relative to hit/collision volume; other characters (Zoro, Tsuna, Yoh) can then hide inside using their own UAs after swapping in — "some attacks will reach you though."
- **Inside The Wall II**: Easier variant. Wall configuration: a wall directly above, with the tile right below it destroyed. Stand under the wall as a non-Raoh character, jump, and switch to Raoh mid-air. Raoh ends up inside the wall. Notably easier/faster than method I.
- **Inside The Wall III**: Hardest variant — getting *fully* inside a wall (not just a corner). Needs a wall with destroyed walls above and below it (same pattern as #5). Demonstrated on the Bleach stage with all normal walls broken; ASCII map in source shows numbered platform positions ("1") as jump-off points near ledge walls ("G"). Jump at the "G" wall attempting a ledge-grab from the wrong side; Raoh grabs an edge he isn't meant to reach. With practice, ends up centered inside the wall. Once inside (especially swapped to a small character like Muhyo or Arale), the opponent reportedly "cannot attack you at all."
- Implication: ledge-grab/edge-detection logic can trigger from the "wrong" side of a wall when adjacent tiles are removed, and it doesn't validate that the character's collision volume ends up outside solid geometry afterward. Raoh's oversized hurtbox/model relative to his collision check is what allows partial or full clipping. Swapping characters mid-air preserves position but not collision-shape re-validation, letting other (small) characters land inside without being pushed out. Stage tile destructibility affects the geometry the edge-grab logic scans.

## 8. Hibari's Glitch I (move/attack while grabbed)

- Setup: 2 players. P1 has 3-koma Hibari (grab support). P2 has a Naruto-series character with the "replacement jutsu" UA (i.e., not Kyuubi Naruto).
- Procedure: P2 repeatedly uses their UA (select). P1 hits P2 with Hibari's grab. P2's replacement-jutsu (substitution) should trigger — the "log" swap animation plays — but P2 reappears back in Hibari's grabbing hands anyway. From there, P2 can move and attack while still visually/logically held by Hibari.
- Restrictions: P2 cannot jump while in this state. Hibari will still eventually toss the grabbed opponent off the stage edge as normal.
- Implication: the replacement-jutsu UA presumably de-spawns/repositions the character and spawns a substitute, but the "being grabbed" state (owned by Hibari's grab logic) isn't cleared by this substitution event — so the grab-state flag persists on the character independent of the UA's teleport/invincibility-swap outcome, producing a hybrid state where normal control inputs partially work (move/attack) but movement options tied to a "grounded/free" assumption (jump) are still blocked.

## 9. Hibari's Glitch II (auto ring-out KO)

- Setup: 3-koma Hibari, on the Black Cat stage with gimmicks OFF.
- Procedure: destroy the three walls closest to the ground on both sides of the stage. Push the opponent to the top platforms. Stand between the broken wall (ground area) and the opponent, facing them, then use Hibari's grab.
- Result: instead of throwing the opponent off normally, Hibari walks off the platform edge himself carrying the opponent, and continues "walking" downward through open air until the opponent is KO'd by ring-out.
- Implication: Hibari's throw/toss logic for a grabbed opponent must resolve a target position or an "off-stage" flag by checking for adjacent walkable ground; with the near-ground walls destroyed, the pathing/edge-check presumably fails to find a valid stopping point and Hibari's AI-driven grab-walk state keeps executing off the platform into the ring-out zone, which the grabbed opponent's hurtbox exits before Hibari's own does — meaning Hibari's ring-out check and the grabbed character's ring-out check are evaluated independently/asymmetrically.

## 10. Slashing Twister (infinite-hit kill combo)

- Setup: 4-koma Taikoubou (his X special has a chargeable "tornado" state) + 6-koma Dio (his X^ special is a time-stop attack, "THE WORLD"). At least 2 SP bars.
- Procedure: fully charge Taikoubou's X special and hit an adjacent opponent with it so they get caught in the tornado hit-loop. Immediately switch to Dio and use X^ (time stop) while the opponent is still stuck in the tornado.
- Result: the opponent keeps taking tornado hits repeatedly (the tornado's hit loop keeps re-triggering) while time is stopped and they cannot act, continuing until they die — described as "automatic" death.
- Note: easier against a wall (likely because the opponent can't be knocked out of the tornado's hit radius).
- Implication: Taikoubou's tornado state is a persistent multi-hit loop tied to opponent proximity/hitstun rather than a fixed-hit-count combo, and it isn't paused or removed by the global time-stop effect (Dio's X^ presumably freezes player input/physics but not existing active hit-loop effects already in progress) — this points to time-stop being implemented as an input/AI freeze layer rather than a full simulation freeze, allowing already-spawned effect objects (the tornado) to keep ticking damage.

## 11. Inside The Floor (pin opponent through the ground)

- Setup: 6-koma Naruto (his ^X launches a "shadow-clone throw"/Rasengan-charge move) + 2-koma Lenalee (support, grab move).
- Procedure: hit the opponent with Naruto's ^X. While Naruto is roughly halfway through his jump animation forming the Rasengan, activate Lenalee's support so she grabs the opponent that the shadow clones are currently holding (precise timing required). When Naruto lands and the opponent isn't at the expected drop location, the game snaps/pulls the opponent back to that spot and throws them into the ground — embedding them in the floor.
- Restriction: only works on the opponent, not on yourself.
- Implication: Naruto's ^X move likely stores a target reference to "resolve" (drop/throw) at the end of the jump animation regardless of the target's current actual position, and it doesn't validate whether the target has been repositioned/re-parented (via Lenalee's grab) in the interim — so the end-of-move "throw to floor" logic forcibly relocates the opponent's position to the original calculated drop point, which can be below the floor surface, and the engine's post-position ground-clamp doesn't fully correct the resulting standoff.

## Other Stuff (minor / cosmetic glitches)

- **Taikoubou's Platform Dance**: on the Yu Yu Hakusho stage with gimmicks off, standing at the very edge of the upper platform as Taikoubou triggers a repeating "dancing" animation loop. Purely cosmetic; implies edge-of-platform standing position can put a character in an oscillating ground/no-ground state that re-triggers a landing/balance animation repeatedly.
- **Yusuke's Spirit Aura**: with 5-koma Yusuke, charge the "Rei Gun" special while spinning the D-pad; once the blue aura appears, fire the Rei Gun. The aura visual persists forever afterward — functionally the same underlying bug as the Hisoka Graphical Glitch (#3), but triggered without Hisoka, implying the "stuck animation state" bug is general to certain charge-then-release specials, not exclusive to Hisoka's cape interaction.
- **Kagura's Bomb Glitch**: any battle-koma Kagura, find a stage bomb, get the opponent adjacent to the bomb, position yourself on the opposite side of the bomb, use Kagura's Y attack (grab). Kagura grabs the opponent and the bomb explodes without damaging either player, and Kagura's Y-attack animation then persists forever (same class of bug as #3/Yusuke's).
- **Sanji Doesn't Heal**: 2-koma Sanji (heal support) fails to actually restore health to some characters under certain movement states — example given: Nami, while running (her movement is fast), activating Sanji plays his heal animation but grants no HP. Implies heal-application is somehow tied to a state check that a fast-movement/run state can bypass or invalidate (author gives no root cause).
- **Lenalee's Slow Falling**: with any battle-koma Lenalee, need a stage wall segment with pattern (top to bottom): broken, cracked, broken, broken, broken, broken. Hit the wall 6 times with Lenalee's normal B attack to crack it, then from the cracked wall use her Up+X attack. If done correctly, the wall breaks and the player falls at a greatly reduced fall speed. Implies wall-break events can set a temporary player physics-state override (reduced gravity/fall speed) that isn't cleared immediately.
- **Pegasus Suicide**: as 6-koma Seiya, get the opponent near a ledge (where the stage floor ends and the ring-out zone begins), use his Up-B twice then Up-X. Both players fall off and are simultaneously KO'd. Edge case noted: if the user is touching the ground but the grabbed opponent is airborne far enough away when the user is KO'd, the game displays the opponent's sprite in a KO animation *at whatever ledge they were grabbed from* before they resume a normal KO sequence — i.e., the KO/ring-out resolution for a grabbed character can be spatially decoupled from the grabbing character's own KO position, producing a rendering discrepancy (author calls it "very weird," treat as (author unconfirmed) mechanism explanation, though the observed behavior itself is stated plainly).
- **Chidori/Raikiri Graphical Glitch**: Kakashi (5 or 6 koma) or Sasuke (any battle koma) using their X special (Chidori/Raikiri) at the same moment a second player's 7-koma Gintoki uses his X special (riding Sadaharu, the dog, as a charging attack) — timed so the Raikiri/Chidori is unleashed exactly as Gintoki's charge is about to connect. Result: Kakashi/Sasuke passes through Gintoki's attack entirely (no damage taken) while still holding the Raikiri/Chidori effect in hand persistently (same "stuck animation" class as #3). Implies a specific attack (a charging "pass-through" hit like Gintoki's Sadaharu charge) can fail to register a collision against a target whose own attack-startup animation is resolving on the same frame, suggesting hit-detection order/priority between two simultaneous attack state-transitions can result in a missed hit check for one side.
