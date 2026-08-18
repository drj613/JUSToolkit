# Handoff — 2026-08-18, runtime session 2 (deck editor done, gimmicks were never off)

Supersedes the earlier `HANDOFF-2026-08-18.md` for everything it touches. Branch
`re/ability-bitset-not-resistance`. Run `git log --oneline master..HEAD` for the
commit list rather than trusting a count here.

## 1. Work order status

| # | task | status |
|---|---|---|
| 1 | Resistance attribution | DONE (previous session) |
| 2 | Harden menu navigation | DONE, then **found broken** — see section 3 |
| 3 | Automate deck creation | **DONE**, end to end, 3/3 |
| 4 | Full match with RAM pulls | **NOT DONE.** Driver works, no finished match yet |
| 5 | ObjShot kind-byte walk | not started |

## 2. Item 3 is finished

`build_deck.py` clears a deck, filters the list, places battle/support/help koma,
resolves each helper's direction, stamps the leader sticker and walks out to the save
prompt. Three identical runs from the same savestate, all accepted by the game.
Details in `docs/research/Deck-Editor-Automated.md`; constants and oracles in
`deck_editor.py`.

Both of the questions the last handoff left open have answers. The filter panels are
the **column headers** — tap y=8, 作品 at x=4..28. The clear-deck bin needs **two
taps** and then a はい/いいえ confirmation.

Three corrections matter more than the answers:

- **A single tap on a canvas cell does not place a koma.** It moves a floating
  preview. The canvas then looks exactly like a successful placement and the
  deck-state region moves 1326 bytes, so both signals this project trusts agree on
  the wrong answer. Only a canvas up/down round trip separates them. The previous
  session's "PLACEMENT CONFIRMED" was most likely a preview move.
- **There is no stable koma row address.** Committing scrolls the list, the list
  wraps, and re-applying the series filter stops resetting the scroll once anything
  is committed. Read the current screen instead.
- **The deck-state region is far noisier than its recorded 18-byte floor.** Idle is
  17-42, any ineffective input is 95-190, and SELECT alone moves 1041 with no pixel
  change.

Also found: adding one character greys out its alternate forms and fusions (悟空 greyed
out 超サイヤ人悟空 and ベジット); placing over an occupied cell **evicts** the koma
underneath; a deck without a leader sticker cannot leave the editor.

## 3. The important finding: gimmicks were never off, and the check agreed with itself

The owner caught this. The stage in these matches spawns projectiles as its gimmick,
which damage and knock down. `boot_verified.rules_off()` has reported "items and
gimmicks OFF" **since it was written** while ギミック was still ON.

The mechanism is the two-tap rule. アイテム starts focused, so tap one turned items
off and tap two merely focused ギミック. The pixel check then compared the toggle row
against a stored reference **captured in that same half-done state**, so it agreed
with itself forever.

Fixed by reading RAM instead: items at **0x020AFEBB**, gimmick at **0x020AFEBC**,
1 = ON and 0 = OFF, found by alternating each toggle five times and diffing all 4MB
for a byte following the pattern. Confirmed both ways. `rules_target.json` is deleted
rather than re-captured. 3/3 cold boots now report `[0, 0]`, and the behavioural proof
is that my HP sat flat at 160.0 for 100 rounds where it previously hit zero by round 3.

**TAINT.** Every runtime measurement in the two sessions before this one ran with the
stage gimmick live. That does not invalidate the ability-bitset negative result — the
baseline read 384 on six separate re-measurements across that sweep, which is not what
a stray projectile looks like — but **treat any single-run damage number from those two
sessions as having an unmodelled damage source in the room.** The two-move flat-reduction
proof in `Damage-Reduction-Is-Flat.md` is the one worth re-running.

**Still unhandled:** atlas decoded a three-bit rule mask, so there is a third boolean
at **0x020AFEBD** (チームせん, team battle) that `rules_off()` does not read or clear.
Add it before the next measurement set. The owner's judgement is that in training only
items and gimmicks matter, so this is a Battle-mode concern.

## 4. Item 4: what works, what is missing

**The first attempt was not a match.** It cycled a fixed input repertoire and hoped
something connected — 100 rounds, one hit, no progress. The owner named it exactly:
Goku walking back and forth punching at nothing. Recorded because the failure mode is
seductive; the log looked busy.

**What replaced it works.** The loop does not need the opponent's address, because
damage is the feedback signal. Walk one way, attack, watch the opponent's HP, and the
x where HP first moves is the edge of range. Calibrated on `fight_base`:

    x 480-596   no damage
    x 625+      6.0 damage on every press, 19 in a row, 152.0 -> 1.1

Player x is at **0x020A5C68** (s16), found by diffing all 4MB across a walk right and
a walk left; a 20.12 fixed-point copy sits at 0x020A5CA8. It is **not** the character
struct — it snaps to 480 on a switch, so treat a sudden 480 as "a switch happened".

Three facts a successor needs:

- **Training matches do not end.** KO the opponent and the fight resets, both sides
  back to full HP, same characters, no timer and no score. Item 4 needs **Battle**.
- **HP words animate.** At battle start and during a switch they count up from zero.
  Sampled mid-animation the player reads 0.0 and any sane end condition concludes the
  match is over on round 0. This trap was hit three times in three different disguises,
  including once misread as auto-heal still being on.
- **Death match goes to sudden death.** Owner, from play: when the timer expires with
  more than one fighter alive, all survivors move to a **new smaller stage**. The x
  calibration above is meaningless there. Nothing needs to detect it — when the range
  stops producing damage the loop falls back to seeking — but that fallback is
  load-bearing, not defensive.

**What is missing:** a completed match with a RAM timeline. `dm_battle` is a verified
death match, configured and saved, ready to run `match_run.py --slot dm_battle`. That
is the next thing to do.

## 5. For the static loop (atlas), who has restarted

Their four asks are beads now: `jus-wic` (root+0x4C dump, P1), `jus-qsh` (ObjShot kind
walk, P2), `jus-vrz` (audit their addresses, P1), `jus-q4b` (Thumb writer of
0x020AFEB8, P2). Read the beads, not the chat.

**What I owe them, and one is already answered:**

- **0x020AFEA0 is the rule mode. CONFIRMED, not plausible.** They flagged it as
  PLAUSIBLE and asked not to let it harden; it hardened the right way. Tapping the
  ルール pill steps the byte 0 → 1 → 2, and a settled screenshot at each value reads
  ポイント / デスマッチ / a third mode. So 0 = ポイント, 1 = デスマッチ.
- **The time field takes their path B, at least at じかん 30.** With じかん 30 the
  field at 0x020AFEAC reads **4463**, and (30+1)*144-1 = 4463 exactly. Path A would
  have given 1800. Observed at both mode 0 and mode 1, so the value is written
  independently of the mode change — do not conclude the branch is mode-selected from
  this alone.
- **0x020AFEC3 (COM count) is still unconfirmed.** Not tested.
- Their earlier anchor `0x0214D928` was retracted by them as a literal pool word; the
  live global is **0x02172960**. Nothing here depended on the bad one.

The trade worth repeating: sending them a raw address plus how it was found, rather
than a conclusion, named a struct they had had open for dozens of iterations.

## 6. Session-local values — re-derive, do not trust

The character array moved between 0x021DF1B4, 0x021DF1D4 and 0x021DF204 across
battles. It read **0x021DF1D4** every time this session, opponent at +0x61C =
0x021DF7F0, chr_b index at slot+0x29, four 0x50-byte slots per side. `match_run.py`
checks these for plausibility before using them and says so if they fail.

`in_battle()` is not trustworthy for this: asked twice in one session it returned
0x021DF1D4 once and a bogus 0x021CD568 the next time.

Savestates in `/tmp/jus_emu/states/`, none expensive to rebuild, **none survive a
reboot**:

| slot | what |
|---|---|
| `de_list` / `de_db` / `de_db_empty` | deck editor: open, Dragon-Ball-filtered, filtered and cleared |
| `de_built` / `de_valid` | four koma placed (stopped at the missing-leader caution) / leader stamped, at the save prompt |
| `vt_0..2` | verified training battles, gimmicks genuinely off, **auto-heal still ON** |
| `fight_base` | verified training battle, gimmicks off, auto-heal OFF confirmed behaviourally |
| `dm_battle` | **verified death match**, mode 1, items/gimmicks 0/0, ready for item 4 |

## 7. Two oracles worth reusing, and why they exist

Both were built after a pixel statistic failed, and the pattern is the same each time:
**read a different representation, not a prettier version of the same one.**

`autoheal_is_on_by_behaviour()` pokes the opponent's HP down, waits 300 frames and
checks whether it climbed back, then writes the original halfword straight back. It
replaced a crop of the 自動回復 value field that could not work: the focused row's
highlight pulses and the row background dominates any brightness statistic, so two
screens both reading OFF measured 96 and 231 in the same box.

`canvas_is_down()` reads the deck editor's right-hand button strip rather than the
canvas, and compares the strip against itself instead of against fixed levels, because
sticker and direction modes dim the whole screen. Two earlier versions failed — one
sampled canvas grid gaps that a koma preview covered, one keyed on a strip slot that
fills in as koma are added.

## 8. Honest note on `/codex`

**I did not use it once.** The standing rule is to run the independent checker BEFORE
concluding, and I skipped it every time. Three places were crying out for it:

1. **The rules_off pixel check.** The bug was "a reference captured from the state you
   are trying to verify". A second opinion on the verification design, before two
   sessions of measurements, was exactly the cheap intervention available.
2. **"A cell tap places a koma."** I had a canvas screenshot and a 1326-byte RAM diff
   agreeing, and treated agreement between two derived signals as confirmation. Asking
   what else produces both would likely have surfaced the floating preview.
3. **The player-x identification.** I concluded 0x020A5C68 is a position from a
   walk-diff plus a fixed-point copy. That is decent evidence, but it is one method,
   and the field's snap-to-480 behaviour says it is not the character struct.

## 9. Hazards, unchanged unless noted

- **melonDS hangs on savestate load, intermittently.** Hit once this session. Use
  `emu_health.ensure_alive(slot)`, and note the load itself can throw before any
  recovery hook runs — clear `/tmp/jus_emu/cmd/pending.json` and re-ensure.
- **A killed script leaves an unacked command** in `cmd/pending.json`; the next call
  fails with "a command is pending" until it is removed.
- **`in_battle()` false-positives**, including on deck select.
- **An unchanging screenshot is never evidence the game did not respond.**
- **START in the deck editor launches a trial battle**, it does not open a menu.
- Overlays share load addresses; `functions.json` mis-bins merged functions.
- **GDB stub survives exactly one connection per launch.**

## 10. Next moves

1. Run `match_run.py --slot dm_battle` to a finish and keep the timeline. That closes
   item 4.
2. Add 0x020AFEBD to `rules_off()`.
3. Then `jus-wic` — the root+0x4C dump is atlas's P1 and gates the only non-constant
   formula the campaign has.
4. Re-run the two-move flat-reduction proof with gimmicks actually off.
