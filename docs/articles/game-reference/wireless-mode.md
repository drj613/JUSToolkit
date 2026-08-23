# Wi-Fi Menu Guide (Wireless Mode)

- Source: "JUMP! ULTIMATE STARS - WI-FI MENU GUIDE", by ChaosAlert
- Version: 2.0 (19/06/08)
- GameFAQs FAQ id: gf-46526
- Reliability: unverified community claim source — a fan-written menu/options walkthrough, not a technical spec. Treat all numbers as (author unconfirmed) unless cross-checked elsewhere.

This guide covers menu structure and match-setup options for wireless/Wi-Fi
multiplayer. It has essentially no battle-mechanic numbers; it's included for
completeness of match-setup rules that could constrain a netplay/battle-setup
reimplementation.

## 1. DS Wireless Communication (local multi-cart)

- **DS Wireless Battle**: up to 4 players, multi-cart. The player acting as
  Leader configures match rules (see Rule Setup below).
- **Pass-by Communication** (すれちがい通信): background deck-trading via
  local wireless standby. Player selects one deck to expose for random
  transfer to another nearby DS with the same mode active. Requires free
  space in the Rival Deck storage area before use (a Caution message appears
  if the storage is full, prompting the player to clear a deck slot).
- **Download Battle**: single-cart play. The player who starts the session
  becomes Leader automatically; all others join via "Download Play" on the DS
  menu. Up to 4 players. All players, including the Leader, get a pre-made
  (not custom) deck for this mode — custom decks are not usable.
- **Data Exchange**: manual deck trading between two players. Requires free
  Rival Deck space before trading.
- **Quiz Battle**: J-Quiz minigame mode, up to 4 players, scored by
  button-mashing correct answers (not a combat battle mode).

## 2. Wi-Fi Connection

- **Login**: opt-in connection to the Nintendo Wi-Fi service; leads to the
  Battle Select screen.
- **Friend Management**: hub for friend list / friend codes.
- **Wi-Fi Configuration**: DS network connection setup (not game-mechanic
  relevant).

## 3. Battle Select (online)

- **Battle (Within) Japan** (日本国内対戦): random matchmaking, finds up to 3
  opponents (max 4 players total). First player found becomes host/Leader.
  Players can view the Leader's rule setup by pressing Y at match setup.
  - **Post-match gem rewards by placement** (author unconfirmed exact values,
    example given for a 4-player match):
    - 1st: 50 Red, 50 Green, 50 Yellow, 10 Blue, 10 Pink, 10 White
    - 2nd: 30 Red, 30 Green, 30 Yellow
    - 3rd: 20 Red, 20 Green, 20 Yellow
    - 4th: 10 Red, 10 Green, 10 Yellow
    - Gem totals scale with player count in the match (fewer players →
      different/lower reward tiers, not specified numerically).
  - If any player leaves mid-match, the match ends immediately for
    all remaining players.
  - After a match, players can download decks from opponents; requires free
    Rival Deck space (prompts to overwrite an existing slot if full).
  - Team Selection option is NOT available in this mode (see Rule Setup).
- **Friend Battle** (フレンド対戦): up to 3 friends (4 players total). Voice
  Chat can be toggled on by pressing X before the match starts.

## 4. Friend Management

- **Friend List**: registered friends; view profiles or remove entries to
  free slots.
- **Friend Record**: stores decks obtained via download/trade; Y button
  shows the associated player's profile.
- **Friend Code Confirmation**: requires at least one successful Wi-Fi
  connection before a Friend Code is generated/viewable.
- **Friend Code Input**: both players must enter each other's code to
  register as friends (mutual confirmation required).

## 5. Rule Setup (match configuration, set by the Leader)

Rule setup applies to Wireless Battle, Download Battle, and the online
Battle Select modes. Stage is chosen first, then rules.

- **ルール (Rule)** — win-condition mode, 3 choices:
  - ポイント (Point)
  - デスマッチ (Deathmatch)
  - Jシンボル (J-Symbol)
- **じかん (Time)** — match length, 3 choices: **30, 60, or 90 seconds**.
- **アイテム (Items)** — on/off toggle for item spawns.
- **ギミック (Gimmick)** — on/off toggle; when OFF, removes stage
  objects/collision geometry from the stage (i.e., stage hazards/terrain
  interactables are stripped, presumably simplifying collision to a flat
  arena).
- **COM (Computer)** — toggle for CPU-controlled players; not usable in
  online play (local/offline only).
- **チームせん (Team Selection)** — 2v2-style team play toggle. Teams
  configured via a side panel with **3 team slots: A, B, C**.
  - **Not available** in the "Battle (Within) Japan" random-matchmaking mode.

## 6. Password System

- Every built deck has an associated randomly-generated password string that
  can recreate that exact deck when re-entered as a new deck.
- Password character set: lowercase letters, capital letters, numbers,
  symbols, and Japanese hiragana/katakana characters.
- Requires free Rival Deck space before a password-entry can create a new
  deck.

## Notes for implementation

- No damage/stat/gauge numbers are present in this source; it's purely
  menu/match-setup/UI documentation.
- Relevant hard constraints to preserve if reimplementing match setup:
  max 4 players across all multiplayer modes; time options limited to
  {30, 60, 90} seconds; 3 team slots (A/B/C); Team Selection disallowed in
  random-matchmaking Battle Japan mode; COM players disallowed in any online
  mode; Gimmick toggle affects stage collision/object presence.
