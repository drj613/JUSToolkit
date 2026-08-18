# Deck Editor, Fully Automated

Session of 2026-08-18, runtime arm. Branch `re/ability-bitset-not-resistance`.

`build_deck.py` clears a deck, filters the koma list, places battle/support/help koma, resolves each helper's direction, stamps the leader sticker, and walks out to the save prompt. Three identical runs from the same savestate, all accepted by the game.

## Everything was measured off the framebuffer

The methodological change that made this work: read geometry from the emulator's own `screendump`, a 256x384 PPM where the bottom screen occupies rows 192-383. An image row maps to a DS touch y by subtracting 192, with no window scaling or capture path in between. That explains why the previous session's canvas row centres were low by up to 8 pixels while the columns were correct -- the columns had been measured on something that happened to scale right.

Bottom-screen layout in the editor's list view:

| DS y | what |
|---|---|
| 0-18 | column headers 作 / 名前 / 数 形 / 種 / 属 / sparkle / sort |
| 23-188 | the koma list, nine visible rows |
| 190-192 | the button-hint bar |

Right-hand button strip sits at DS x 238-256.

Koma row n spans y 23+16n to 40+16n, centre 31+16n, adjacent rows sharing a 2px border. The canvas grid, measured on a freshly cleared deck, has columns spanning x 2-45, 50-93, 98-141, 146-189, 194-237 and rows spanning y 3-44, 51-92, 99-140, 147-188 -- both pitches exactly 48, so centres are (24, 72, 120, 168, 216) by (24, 72, 120, 168).

## The rule the whole editor runs on: two taps

Nearly every control takes two taps. The first moves focus, the second activates. This holds for koma rows, deck slots, rule toggles, series icons, the clear-deck bin, and the yes/no buttons in its confirmation. When a tap looks like a no-op, suspect it only moved focus. The exceptions found so far are the 編集 menu item and the column headers, which act on the first tap.

## Open question 1: what opens the series filter

The column headers do. Tapping the header band at y=8 opens the filter panel for whichever column was hit:

| DS x | panel |
|---|---|
| 4-28 | 作品, series, an icon grid with the focused series named across the top |
| 36-140 | 名前, kana rows あかさたな / はまやらわ |
| 145-160 | 数, koma sizes 1-8 |
| 164-176 | 形, koma shapes |
| 185-195 | 種類, バトル / サポート / ヘルプ |
| 205-215 | 属性, カ / 知 / 笑 / なし |
| ~222 | the sparkle icon, a no-op |
| 236-252 | the same ならびかえ sort menu the R button opens |

The previous session tapped (7, 8), measured a no-op, then found the panel open anyway and recorded the attribution as unknown. (4, 8) opens it reliably; (7, 8) is a pixel or two outside the 作 cell.

Inside the series panel the icon grid is 11 columns at a 19.6px pitch by 4 rows, with row centres at y 63, 87, 111, 135. Dragon Ball is row 2 column 0, at (23, 111). That independently matches the coordinate the previous session found by a different measurement -- two paths to the same pixel, the cross-check worth having.

Applying the filter takes two taps, and the first is easy to misread as success: the panel's title changes to the new series while the list behind it stays the same.

Two other buttons on this screen, recorded so nobody has to find them again: R opens ならびかえ (sort by 作品 / 名前 / 数 / 種類 / 属性), and START does not open a menu -- it launches a trial battle with the deck as it stands.

## Open question 2: the clear-deck confirmation

The bin in the right-hand strip, at (248, 87) on the canvas view, needs two taps. The second raises 「コマを全てリストに戻しますか？」 with いいえ focused, so はい needs two taps as well: (88, 103), twice.

The previous session's reading -- "one tap emptied the deck, 107 bytes of deck state changed" -- was a false positive, and an instructive one. 107 bytes is exactly what an ineffective tap costs in that region. Details under the RAM oracle below.

## Three corrections that mattered more than the answers

### A cell tap does not place a koma

It moves a floating preview onto the cell. Nothing is committed. The canvas looks exactly like a successful placement, and the deck-state region moves 1326 bytes, so both signals this project normally trusts agree on the wrong answer. The tell: toggling the canvas up and back down leaves the grid empty.

Committing needs a second tap on the same cell. Measured:

| step | canvas after | survives a round trip |
|---|---|---|
| tap koma row, 1st | list highlight only | -- |
| tap koma row, 2nd | canvas comes down holding the koma | -- |
| tap target cell, 1st | koma drawn at the target | no, grid comes back empty |
| tap target cell, 2nd | koma drawn at the target | yes |

The previous session's "PLACEMENT CONFIRMED" was very likely just a preview move. Its two pieces of evidence -- a canvas screenshot showing the koma in the cell, and a deck-state diff well above the noise floor -- are both produced by an uncommitted preview.

### There is no stable row address

Committing a koma scrolls the list. The list also wraps, so saturating with UP does not reach the top: 20 UP presses from index 4 landed deep in the list, the same trap the top-menu grid sets. Re-applying the series filter resets the scroll while the deck is empty and stops doing so once anything is committed.

So the list has to be driven off the current screen rather than off remembered indices. `available_rows()` reports which of the nine visible rows the game will still accept, from row-background brightness: greyed rows read a mean of 105-120 across the name column against 203 for a usable one.

Rows grey out per character, and the grouping is wider than it looks. After 悟空 went into the deck, every 悟空 koma greyed out -- and so did 超サイヤ人悟空 and ベジット. The alternate form and the fusion count as the same character. A deck cannot be built out of one character's koma, which broke the first attempt at a multi-koma build here.

### The deck-state region is much noisier than recorded

Deck state lives at 0x020A0C00-0x020B0000. The recorded 18-byte noise floor only holds for a genuinely idle screen. Measured on the editor:

| what | bytes changed |
|---|---|
| idle, after a savestate load | 17-42 |
| a tap or press that does nothing | 95-190 |
| SELECT, with no pixel change at all | 1041 |
| clearing a full deck | 361 |
| placing one 4-koma | 1326 |

The region confirms that something large happened and nothing finer. That makes the old 107-byte clear-deck reading a false positive, and it is why occupancy is now read off the framebuffer instead: `canvas_cells()` samples 81 points per cell and reports 1.00 for empty against 0.00 for occupied -- as clean a separation as this project has measured.

## Three mechanics found on the way

**Helper koma ask for a direction.** After a helper is committed the canvas dims from salmon (235, 154, 121) to brown (117, 77, 60) and orange arrows appear on the helper's free edges, one focused. A accepts the focused arrow. This matters beyond helpers: while the canvas is dimmed every cell fails the "looks empty" test, so `canvas_cells()` reports a full 20/20 deck and a build loop without a check for this concludes the deck is full after one koma.

**Placing over an occupied cell evicts what was underneath.** It does not fail. A 2-koma dropped on a free cell whose neighbour belonged to a koma already there silently returned that 4-koma to the list. Since a koma's footprint is not known before it lands, the placer aims at whichever free cell has the most free space around it and re-derives occupancy from the canvas after every attempt.

**A deck needs a leader sticker.** Without one, leaving the editor raises 「リーダーが居ません。バトルコマにリーダーシールを貼ってください。」 and no amount of correct placement gets past it. The sequence: one tap on a battle koma's cell to move the cell cursor onto it, R to pick the sticker up (a LEADER badge with L and R beside it appears in the corner and the canvas dims), A to stamp it, then A until the dim clears. Pressing B instead of that second A cancels the stamp while still drawing the badge, and the failure only shows up on exit.

One tap on the cell, not two: two taps on an occupied cell pick the koma up out of the deck.

## Knowing which screen you are on

Two pixel tests carry the whole flow, both keyed on chrome rather than content.

`canvas_is_down()` reads the right-hand button strip at x=246. With the canvas down the L-R / X / Y / SEL buttons are three equal bright values with the bin's darker core below them; on the list view the same column is the scrollbar, 0/0/73. Sticker and direction modes dim the strip along with everything else (buttons 251 to 146, bin 48 to 113), so the test compares the strip against itself instead of against fixed levels. An earlier version sampled the canvas grid's gaps and broke the moment a koma preview covered one of them; another keyed on a slot further down the strip that fills in as koma are added.

`save_prompt_open()` keys on the exit prompt being a BLACK dialog: the band it occupies reads a mean brightness of 54 against 151-154 for the white caution dialog or the plain list view behind it. Colour cannot be used -- the caution's red text and the list's red row backgrounds are indistinguishable.

Getting this wrong is expensive rather than loud. One desynced view turned every later tap into a tap on the other screen's widgets and reported an 18-cell placement.

## The final check is the game's own verdict

`exit_editor()` returns whether the game raised a caution on the way out. That is stronger than any pixel check: the game itself deciding whether the deck is playable. It stops at the save prompt without answering -- confirming セーブ writes the deck into the cartridge save, whose SHA-256 is recorded in hashes.json, so that decision belongs to the owner, not the script.

## Route in, and the savestates left behind

    top_menu -> tap (33, 96) デッキメイク + A  -> デッキセレクト (ov01, DeckSelect)
    tap a deck slot, tap it again              -> options submenu
    tap (208, 58) 編集                         -> the editor (ov05, KomaEdit)

The submenu offers 編集 / 名前へんこう / コピー / いれかえ / けす / とじる, and 編集 enters on a single tap.

Savestates in `/tmp/jus_emu/states/`, none expensive to rebuild: `de_list` (editor open on deck slot 3), `de_db` (the same with the Dragon Ball filter applied), `de_db_empty` (filtered and cleared), `de_built` (four koma placed, stopped at the missing-leader caution) and `de_valid` (leader stamped, stopped at the save prompt).
