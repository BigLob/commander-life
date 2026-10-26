# Commander Life: project notes

Life counters for a Magic: The Gathering Commander group, played on everyone's phones and kept in
sync live. Plain HTML pages, no build step, no framework.

## Replies

End every reply about anything in this repo with icon-only links to both live pages, on one line:

[🃏](https://biglob.github.io/commander-life/) [😈](https://biglob.github.io/commander-life/archenemy.html)

## Where things live

| What | Where |
| --- | --- |
| Live site (what the phones open) | https://biglob.github.io/commander-life/ |
| Archenemy page | https://biglob.github.io/commander-life/archenemy.html |
| Hosting | GitHub Pages, repo `BigLob/commander-life`, branch `main`, root folder |
| Source and history | repo `BigLob/Mtg` (see Branches below) |
| Live sync | Firebase Realtime Database `https://commander-life-39708-default-rtdb.firebaseio.com` |

**claude.ai artifact links can't sync.** Artifact pages block connections to Firebase, so they always
show "Offline, this phone only". The Commander Life artifact (claude.ai/artifact/LzFGUh29B93Zb2sjM7uEGU)
and the old Archenemy Table artifact (claude.ai/artifact/RuiCBfVWbVowusRFS4D5zc) are previews only.
Never send the group an artifact link to play on.

## Deploying

The site only changes when files land on `main` of `BigLob/commander-life`:

1. Make and test the change (in `BigLob/Mtg` or directly here).
2. Copy `index.html`, `archenemy.html`, `patterns/`, `fonts/` and `art/` into this repo, commit, push to `main`.
3. GitHub Pages republishes in a minute or two. Phones may need a reload.

The cloud sandbox can't reach firebaseio.com or github.io (the proxy returns 403), so test in
Playwright with the network mocked (route `firebaseio` requests, replace `EventSource`).
`index.html` loads all its fonts from `fonts/` (since v3.31), so route the page's own files to the
local checkout. `archenemy.html` uses Google Fonts, which is reachable: launch Chromium with
`proxy: { server: process.env.HTTPS_PROXY }` and `ignoreHTTPSErrors: true` so text is measured in the
real fonts (the fallbacks are much wider).
After a deploy, ask the user to check the version in the menu footer.
Run test scripts from the scratchpad, not the repo: screenshots saved with a relative path land in
the repo and `git add -A` picks them up (v3.17 to v3.29 shipped 21 test PNGs this way; v3.30 removed
them and `.gitignore` now ignores PNGs at the root).

## Pages

### `index.html`: Commander Life (current v3.33)
- Names (v3.23, v3.24): a name box left blank, or holding another player's default name (v3.24:
  the shared table once had "Lenn" in Trent's box and a blank in Lenn's), goes back to that player's
  default (`badName()`). Such names are fixed on load, rejected from other phones, and each phone
  writes the fix back to the table when it sees one.
- 4-player totals are bigger (v3.23), and the top and bottom rows got more height (rows 1.2fr 1.6fr
  1.2fr). v3.24 trimmed them a little: up to 52% of the seat's height or 56% of its width. v3.30
  moved totals nearer the middle of each seat. v3.33 makes them 10% bigger (`fitLife()` takes 1.1×
  the smallest seat's size) and centers each one by measurement (`centerLife()`): the readout gets
  padding so its middle is halfway between the bottom of the seat's name and the top of its turn
  symbol, in the face's unturned layout (padding, not top/bottom, because the name sits inside the
  readout). `.life { top: .09em }` corrects for Beleren's digits riding high in their line box. The
  CSS readout lifts are only the starting point now.
- **One size for every total** (v3.26, `fitLife()`): each seat's own largest size comes from the
  styles, and all totals on the board take the smallest of them (`.board.fitted`, `--life`), so the
  iPad's side seats no longer dwarf the top and bottom ones. 3 or 4 digits shrink (`--ls`). Side
  seats place theirs differently: upright ones lower (clear of the name), turned ones (Center) off
  the menu button.
- **No − or + on the seats** (v3.26; the user asked to drop them). The tap zones are unchanged: the
  left half of a seat, as its player sees it, loses life and the right half gains it.
- 1 to 4 players. Seats sit on the phone's edges, clockwise from the bottom: edge 0 bottom, 1 left,
  2 top, 3 right. Default names are Rand, Andrew, Trent, Lenn. Each person is known by their default
  edge (names and colors are stored by it).
  - Who plays (`PEOPLE`): 2 players Rand and Lenn (v3.19; it was Trent before); 3 players Rand, Andrew and Trent (v3.18; it was
    Lenn before); 4 everyone. Where they sit (`EDGES`) is separate: 2 players use bottom and top, 3 players bottom, left, right.
- **Seating** (v3.32): around the real table, Lenn is on Rand's left, Trent across and Andrew on his
  right. `posOf()` turns the table so this phone's player is at the bottom and swaps left and right
  (`flipSide()`) on every phone. Before v3.32 Rand's phone and Center skipped the swap, so they
  showed Andrew and Lenn the other way round from everyone else's phone.
- **This phone is**: each phone picks its owner (kept on that phone only).
  - A named player: their seat goes at the bottom and every seat faces them, upright.
  - **Center**: the phone lies in the middle of the table and each seat faces its own edge.
    Center has no seat of its own, so its colors and Concede are hidden.
- Picking a player count sets starting life to its default (v3.6): 2 players 20, 3 players 30,
  4 players 40. Starting life can still be changed by hand afterwards.
- **1v1 layout** (v3.6, menu, 2 players only, kept on that phone): **Side by side** (default) or **Classic**.
  Side by side is a 2×2 grid. The bottom half faces this phone's player, the top half is turned to the
  opponent, and each half shows both totals with its viewer's own on the left, so each player's
  colors run down one side of the phone. Each player then has two seat elements (`seats[i]` is a list).
  - v3.7: − and + split each box left and right (the signs themselves were dropped in v3.26).
  - v3.7: each player's own box has a white flag in its bottom-left corner to concede or rejoin
    (two taps), since both players share the phone. The menu's Concede still works too.
- **Turn tracker** (v3.8; 33% bigger in v3.10): a button at the bottom center of every seat (not in "Just me").
  Since v3.27 it's Magic's tap symbol (`ICON_TAP`, from the Mana font's SVGs, github.com/andrewgioia/mana)
  instead of the pink circle the user hated: cream before anyone has the turn, then gold and glowing
  on the current player and dim on everyone else. The side-by-side turn bar is gold too. v3.30 draws
  the symbol at 80% of the button and v3.32 at 54% (a third smaller again); the 3.2em tap target is
  unchanged.
  Tapping the current player's button passes the turn clockwise in edge order (Rand → Andrew →
  Trent → Lenn), skipping anyone out. Tapping anyone else's makes it their turn. Once someone has
  the turn, everyone else's button goes dark (v3.9; no ring on the seat). In side-by-side 1v1, a
  bar runs along the current player's two tiles where they meet the middle of the phone.
  Pick who goes first sets the turn, and New game clears it.
  Synced as `turns/<n>` (2 to 4) in the live table; older phones ignore it.
- **1v1 ×2** (v3.16, the fifth Players option): all four play two 1v1s at once, starting at 20.
  "Rand plays" in the menu sets the pairs (default Rand v Lenn, Andrew v Trent since v3.20); once either 1v1
  has started, changing it takes two taps and starts both over. Each 1v1 is its own game, synced as
  `games/a` (Rand and his opponent) and `games/b` (the other two), with its own `meta`, `turns` and
  `clock` under the same keys, so each is timed and logged on its own as a 2-player result.
  - A player's phone shows only their own 1v1, in the 1v1 layout (side by side or classic).
  - A Center phone shows all four seats at their edges, each with only its opponent's chip;
    Pick who goes first picks for both 1v1s.
  - New game restarts only the 1v1s this phone shows, so the other pair plays on.
  - Code: `players` (built by `viewPlayers()`) maps each seat on screen to `{ k: game key, j: seat
    in that game, e: edge }`; `SIZE` lists every game key and its player count.
- Tap a side for ±1, hold for ±10. Commander damage: the dagger button opens the attacker chips;
  while one is marked, life lost also counts as their commander damage. 21 from one commander is lethal.
  Since v3.29 each attacker chip (and each player in Results) is marked with a round crop of their
  commander's art (`swatch()`) instead of the old two-color dot.
- Each player picks a deck, and their seat always shows that deck's commander art (v3.25: the only
  background; the 50 pattern masks and the deck-card picker were removed from Commander Life.
  `patterns/` stays for `archenemy.html`). Seat colors still paint the seat while the art loads.
- **Decks** (v3.21): the group plays the five Starter Commander Decks (2022, set code SCD), and each is
  exactly one of the seat color pairs, so picking a deck ("Rand's deck" in the menu) sets the seat's
  colors: First Flight `uw` (Isperia, Supreme Judge), Grave Danger `bu` (Gisa and Geralf), Chaos
  Incarnate `rb` (Kardur, Doomscourge), Draconic Destruction `gr` (Atarka, World Render), Token
  Triumph `gw` (Emmara, Soul of the Accord). `DECKS` holds each deck's name, commander, the
  commander's collector number in SCD, and its 99 other cards (from Forge's
  `forge-gui/res/quest/commanderprecons/*.dck` on GitHub). Since v3.28 tapping a deck only opens it
  (`openDeck`, one at a time): its commander card, a **Play <deck>** button, and its decklist folded
  under "Decklist · 100 cards". Only Play changes this player's deck, so anyone can look at every
  commander without switching. The current deck has the white border (no "Playing" label), and each
  row ends with one mana symbol per color, like a card's mana cost (`manaOf()`, symbols in `MANA`
  from the Mana font's SVGs on its cost-circle colors). The yin-yang tried before was dropped. Since v3.22 the images are saved in `art/` (`<pair>.jpg` is
  Scryfall's art_crop, `<pair>-card.jpg` the normal card image), fetched once from
  `api.scryfall.com/cards/scd/<n>?format=image&version=art_crop|normal`.
  - Commander art background (v3.22 as an option, v3.25 the only one): `.face::before` shows
    `art/<pair>.jpg`, turned with the face and dimmed slightly. v3.23's deck-card wallpaper (any card's
    top half, from `cards.scryfall.io`) was removed in v3.25; `patterns/<n>` and `cards/<n>` are no
    longer synced. The log saves each seat's `deck`, and Results
  shows deck names (older results map their colors to the deck).
- **Fonts** (v3.17, from AlexandreArpin/mtg-font, served from `fonts/`): Matrix Bold (`--f-name`)
  for names and the menu title; MPlantin for everything else. Life totals and other numbers
  (`--f-num`): Matrix (v3.17, old-style digits the user disliked), Big Shoulders Display from Google
  Fonts (v3.24 to v3.30), then **Beleren Bold** (v3.31, the card-name font; the user owns the cards
  and asked for it). `fonts/Beleren-Bold-digits.woff` is Beleren2016 Bold from Card Conjurer's repo
  (github.com/Investigamer/cardconjurer, `fonts/beleren-b.ttf`), subset to space, digits, + and −
  only (4 KB), so the page doesn't carry the whole Wizards font. Both are limited by `unicode-range` to
  plain ASCII (plus Matrix's minus), because their other symbols are blank or wrongly mapped
  (×, ·, … fall back to Georgia). `Matrix-Bold.woff` has patched line metrics: the original's
  positive descent made the line box half height and clipped the names.
- Life totals and names are white with a black outline; names are large (v3.13: up to 34px, 13% of the seat's height). Since v3.18 a name that's too wide for
  its seat shrinks to fit (`fitNames()`, via `--fit`), so every name shows in full on one line. Since
  v3.24 every name on the board is drawn at one shared size, the largest at which all of them fit;
  an "out" line too wide for its seat shrinks on its own (`--wfit`).
  The dagger has a black outline, no ring, and sits in the seat's bottom-right corner as its player sees it.
- **Concede** (menu, under Pick who goes first): only this phone's seat, two taps to confirm.
  It becomes Rejoin. A new game clears all concessions.
- **Game log** (v3.2; automatic since v3.14): an invisible clock starts at a game's first life change
  or first turn-tracker tap and stops the moment one player is left. The phone that made that change
  logs the game right then. If a later change brings someone back (a mistap), the entry is deleted
  until the real finish. The end time is synced (`meta/<n>/end`), so New game, which still logs
  too, writes the same entry and time. A game is logged only if:
  - the table had 2 to 4 players,
  - exactly one player was still alive,
  - and its clock ran at least 15 minutes.

  v3.15 adds an invisible turn timer (synced as `clock/<n>`: `at`, `count`, and per player `t/<i>`
  ms and `c/<i>` turns, all increments). Each turn-tracker change counts a turn and gives the time
  since the last one to whoever had it. New game clears it. The log saves `turns` (total) and per
  seat `turns` and `turnSecs`, and Results shows "N turns" and each player's turn minutes.

  The log saves the date, how long the game took, the winner, and each player's name, color pair,
  deck and final life. The Results list is hidden: tapping the version line at the foot of the
  menu shows it (tap again to hide). Each result has a two-tap Delete.
- Back to game is white like New game (v3.22).
- The menu button in the middle of the table shows the Planeswalker flame (v3.20), an inline PNG
  in `ICON_MENU`.
- Version shows in the menu footer with the sync status. Bump `VERSION` on every release.

### `archenemy.html`: Archenemy (v1.2)
- Separate page, because its interface differs a lot from Commander Life.
- Rules:
  - One archenemy at 40 life against three heroes at 20 each, with no shared total.
  - The archenemy goes first.
  - Heroes take commander damage only from the archenemy; the archenemy takes it from each hero.
- Scheme deck: 102 schemes with full card text, Set in Motion, ongoing schemes, Abandon, and Undo.
- Same seat styling as Commander Life: large white names with a black outline (the archenemy's is
  gold), and the dagger in each seat's bottom-right corner.
- Built in the "Archenemy page development" chat, branch `ccr-b9949e35-ihpa80` of `BigLob/Mtg`
  (v1.0). From v1.1 on it lives with Commander Life on `ccr-d009fee8-fnaynu`.

## Firebase layout

| Path | Used by |
| --- | --- |
| `tables/t7q2xm4k` | Commander Life live table |
| `tables/t7q2xm4k-ae` | Archenemy live table |
| `tables/t7q2xm4k-results/<gameId>` | Commander Life game log |

The REST API is used directly: an EventSource stream comes in, and PATCH writes go out with
server-side increments so taps on two phones both count.

The database rules only open `tables/` to the pages. v3.2 to v3.4 kept the log under `results/`, and
the log failed with "Couldn't reach the shared log", so keep every new node under `tables/`.

## Code conventions (both pages)
- Single file, inline CSS and JS, and comments that explain why.
- Every synced path must be in `allPaths()` and checked in `validValue()`.
- A new synced field must tolerate older phones that don't send it (see the `conceded` and `meta`
  handling in `adopt()`).
- Destructive actions take two taps (New game, Concede, Delete a result, changing the archenemy).
- Commit messages: `vX.Y: <what changed, in plain words>`.

## Decisions so far
- Poison was dropped on purpose.
- 3v1 does not belong in Commander Life. It lives in `archenemy.html` (v2.9's 3v1 mode was reverted).
- Seat colors are what the game log records as each player's "color combo", and since v3.21 each
  color pair is a deck.

## Branches in `BigLob/Mtg` (history, oldest to newest)
- `claude/mtg-commander-health-counter-m75zne`, `ccr-31ae3957-dadntz`, `ccr-b66a7c9b-cywcix`:
  early versions (`ccr-b66a7c9b-cywcix` is an abandoned side branch).
- `ccr-67e82241-afli68`: v1.0 to v2.7.
- `ccr-d009fee8-fnaynu`: Commander Life v2.8 to v3.5 and Archenemy v1.1 to v1.2, the latest source for both.
- `ccr-b9949e35-ihpa80`: `archenemy.html` v1.0 (branched from v2.8).

`BigLob/Mtg` has no `main`, so a new chat may start on an old branch. Start from the newest branch
above, or work here in `BigLob/commander-life`, where `main` is always what's live.
