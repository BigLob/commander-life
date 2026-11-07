# Commander Life: project notes

Life counters for a Magic: The Gathering Commander group, played on everyone's phones and kept in
sync live. Plain HTML pages, no build step, no framework.

## Replies

End every reply about anything in this repo with icon-only links to the live pages, on one line:

[🃏](https://biglob.github.io/commander-life/) [😈](https://biglob.github.io/commander-life/archenemy.html) [🎉](https://biglob.github.io/commander-life/xenagos.html) [📚](https://biglob.github.io/commander-life/decks/) [🔊](https://biglob.github.io/commander-life/sounds/)

🎉 is the Xenagos, the Party Hugger card carousel (deck singles, suggestions, Fav, Bench and Trash
tabs). When we build a new page, add its icon link to this line. Its editable claude.ai artifact is
https://claude.ai/artifact/D3rxfusL2qGunJxamxqMa2 (private, for the user only; don't put it in the footer).
📚 is the deck list, `decks/`: a card carousel for every precon the group owns (see below).
🔊 is the clip list, `sounds/index.html`: every turn-button sound with its length, pool and source, each playable.

## Where things live

| What | Where |
| --- | --- |
| Live site (what the phones open) | https://biglob.github.io/commander-life/ |
| Archenemy page | https://biglob.github.io/commander-life/archenemy.html |
| Hosting | GitHub Pages, repo `BigLob/commander-life`, branch `main`, root folder |
| Source and history | repo `BigLob/Mtg` (see Branches below) |
| Live sync | Firebase Realtime Database `https://commander-life-39708-default-rtdb.firebaseio.com` |

**Buying cards:** `buying-guide.md` holds the group's price reference (booster packs, precons, the
Foundations beginner decks, precon win rates). When the user asks whether a price is good, check it
there, and update it when newer prices turn up. Its "Decks we own" table is the group's precon
collection (owned and preordered). Keep it current when the user mentions buying a deck.

**claude.ai artifact links can't sync.** Artifact pages block connections to Firebase, so they always
show "Offline, this phone only". The Commander Life artifact (claude.ai/artifact/LzFGUh29B93Zb2sjM7uEGU)
and the old Archenemy Table artifact (claude.ai/artifact/RuiCBfVWbVowusRFS4D5zc) are previews only.
Never send the group an artifact link to play on.

## Deploying

The site only changes when files land on `main` of `BigLob/commander-life`:

1. Make and test the change (in `BigLob/Mtg` or directly here).
2. Copy `index.html`, `archenemy.html`, `patterns/`, `fonts/`, `art/` and `sounds/` into this repo, commit, push to `main`.
   `decks/` is built here by `tools/carousel/make.py` (no copy from `BigLob/Mtg`).
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

### `index.html`: Commander Life (current v1.14; the user reset the version number from 3.41 to 1.0 at this release, so v3.x notes below are the old numbering)
- v1.14: **286 video game clips and more game events.** Mario (`mario-*`, `mario3-*`, `mario64-*`, `smw-*`, `luigi-*`, `smash-*`), Zelda (`zelda-*`), Final Fantasy (`ff*-*`), Mass Effect (`me-*`), Gears of War (`gears-*`, only 6: Myinstants has little), Mortal Kombat, Street Fighter, Halo, Unreal Tournament, Sonic, Pokémon, Metal Gear, Skyrim, Warcraft, StarCraft, GTA, Dark Souls and more (`sounds/CREDITS.md`). Sources: The Mushroom Kingdom's WAV rips (themushroomkingdom.net) and Myinstants (`myinstants.com/en/search/?name=...`; each sound's file is `/media/sounds/<name>.mp3`); both are reachable from the sandbox, khinsider, sounds-resource, 101soundboards and pixabay are not (403). Transcribed with faster-whisper to check the words (it hears "Thanks for watching!" in music, ignore that) and cut, loudness-matched to -16 LUFS, mono 64 kbps MP3. Not CC0. `EVENT_SOUNDS` now has six events, each dealt from its own shuffled bag (`events`, `deal()`): `out` (life 0 or concede), `cmdout` (21 commander damage: "Fatality", "Finish him!"), `big` (one player loses 10 or more in a turn: "Falcon PUNCH!", "Shoryuken!", "C-c-c-combo breaker!"; 14 clips added for it), `win`, `low` (life first drops to a quarter of starting life or less: Zelda's low-health beep, Metal Gear's alert) and `back` (a knocked-out player comes back: FF7's Life, a 1-up). A turn for `big` (`bigHit()`, `hits`) is the net life this phone enters for a player until the turn button is tapped on this phone, a new game, or 30 s without them losing life (`BIG_GAP`); it plays once per turn, and a big hit that also crosses into low life plays `big` then `low`. The knockout that ends a game plays a short `out` clip and then the `win` clip after it (`play(name, then)`, `playBuffer(buf, next)`); before, the two started together and one cut the other off. `settle()` now returns whether the game ended instead of playing the win itself. The clip list has event chips (`ev` in `clips.json`, read by `make_list.py` from `EVENT_SOUNDS`). **Halo announcer** (95 clips, the user asked for every Halo's kill-streak lines): `haloreach-*` (Myinstants' full Reach set), `halo3-*` (a SoundCloud compilation, probably Halo 3, cut at the gaps between lines; whisper's word starts run late, so cut at energy minima instead), `halo-*` (loose Myinstants uploads), `haloreach-unused-*` (41 unused Reach medals Bungie released, archive.org `Halo_Reach_Unused_MP_Announcer_2010-11`, renamed to what they say) and `long/halo-fake-medals` (a fan joke). Multi-kills, sprees and the odd unused ones are on `big`, Killjoy/Extermination/Betrayal/You suck on `out`. No Halo 2, 4, 5 or Infinite sets were reachable: YouTube asks the sandbox to sign in (yt-dlp is installed for SoundCloud).
- v1.13: **76 more clips and knockout/win sounds.** NASA's public-domain audio from soundcloud.com/nasa, fetched with yt-dlp (`nasa-*` Apollo and Mercury lines like "The Eagle has landed", "Houston, we've had a problem"; `space-*` 13 eerie planet and plasma recordings; `jfk-*` two moon-speech lines), 20 cuts from five 1922 to 1925 laughing records on archive.org (`laugh-*`, public domain), 3 effects (`sfx-*` goats, slide whistle, record scratch) and 26 text-to-speech announcer lines made with Piper (`tts-*`: "Counterspell!", "Resistance is futile", "Rand. Rand. It is your turn."). `EVENT_SOUNDS` in `index.html`: a player going out plays a random clip from the `out` list (sad trombones, game-over tunes, "Obama out", "Houston, we've had a problem") and the last player standing one from `win` (victory fanfares, "The Eagle has landed", "I am the chosen one"), instead of the synth toll and fanfare, which stay as the fallback. Like the other game sounds they play on the phone that made the change, Sound All only. Wikimedia Commons rate-limited the sandbox (HTTP 429) after a few files, and freesound.org is blocked (403), so more effects (sad trombone, air horns, drum roll, kazoo, gasp, crickets, cuckoo clock) went on the user's download list. The clip list's group chips are now built from the groups in `clips.json`.
- v1.12: the five Trump lines v1.11 had left out because they're aimed at groups of people, added at the user's request: `trump-fat-pigs`, `trump-we-love-puerto-rico`, `trump-black-community`, `trump-eating-the-dogs`, `trump-turn-black` (all in `sounds/long/`; 60 presidential quotes in all).
- v1.11: **presidential quotes** on the turn button: 55 lines from George W. Bush, Obama and Trump (`bush-*`, `obama-*`, `trump-*`; 20 in the short pool, 35 in `sounds/long/`). The user downloaded 25 YouTube clips on their PC (the sandbox can't reach YouTube's downloads) and sent them as a zip; they were transcribed with faster-whisper (small.en) for word timings, cut to one quote each (10 s at most, a few with pauses shortened), loudness-matched to -16 LUFS and saved as mono 64 kbps MP3. Each quote, length and YouTube link is in `sounds/CREDITS.md`. Not CC0 like the rest. Trump's health-care clip failed to download, and two downloads were the wrong video, so `bush-misunderestimated` comes from the Bush compilation and Strategery (an SNL line) was dropped. The user dropped Blazing Saddles, Drag Race and Rocky Mountain Way.
- **Clip list** (`sounds/index.html`, live at https://biglob.github.io/commander-life/sounds/): every clip with length, pool and source, filters, search and a play button. Built by `python3 tools/sounds/make_list.py` from `sounds/clips.json` (one entry per clip: file, pool, length, source and link, group, and the words for quotes). After adding clips, run it and fill in the new entries' sources in `clips.json`. Seven older clips (`castle-fanfare`, `squishpop`, `squishsplat-impact`, `stage-clear-1` to `-4`) have no recorded source page. Its claude.ai artifact copy (no playback there) is https://claude.ai/artifact/XKDkaimq128iz5n91fBda4.
- v1.10: **13 more backgrounds**: the face commander and alternate commander (the box's second foil, and the second card on Wizards' decklists) of every other deck the group owns or preordered. Keys and Scryfall cards: `le2` Pia Nalaar (drc/2, Living Energy's alternate), `em` Temmet (drc/4) and `em2` Hashaton (drc/1) for Eternal Might, `rt` Terra (fic/4) and `rt2` Celes (fic/1) for Revival Trance, and the Star Trek decks: `bq` The Borg Queen (trc/1) and `lo` Locutus of Borg (trc/97), `pi` Jean-Luc Picard (trc/3) and `ja` Captain Janeway (trc/84), `sp` Commander Spock (trc/2) and `ki` Captain Kirk (trc/85), `wo` Worf (trc/4) and `ko` Kor (trc/96). Each has `art/<key>.jpg` (art_crop), `art/<key>-card.jpg` (normal) and `.k-<key>` seat colors. Phones older than v1.10 reject the new keys (`validValue()`), so until they reload they keep their old background for that seat.
- v1.9: **Pick who goes first shows the winner** (the user: it "blanks out the winner"). The seat highlight used the class `pick`, which is also the menu's "This phone is" ring (a 40 px see-through circle), so the chosen seat vanished. Now the highlight runs round as `.lit` (gold frame), and the winner gets `.first` (thick pulsing gold frame, a big gold "Goes first" banner across the middle of the seat, a vibration) while everyone else is `.passed` (dimmed) for 8 s. Don't reuse menu class names on seats.
- v1.8: happy and sad clips, and **long clips**. 59 more short ones (victory and level-up stings, win jingles, cheers, sad trumpets; 415 short in all) and a second pool, `LONG_SOUNDS` in `sounds/long/` (73 clips, 5 to 12 s: victory, level-clear and game-over tunes, sad songs, and full-length cuts of earlier long sources like `laughing-fit` and `fart-symphony`). After every 3 to 10 short clips (`LONG_EVERY`, a new random count each time, per phone) the next tap plays a long one. Each pool has its own shuffled bag (`pools`). `sounds/` is now 16 MB, but phones only fetch the next few clips.
- v1.7: 226 more turn-button clips (356 in all, 5.9 MB in `sounds/`), all CC0 from OpenGameArt, found with the user's keywords (funny, silly, dumb, scary, gross, sexy, mature, adult): monsters, demon voice lines ("Feeble humans"), evil laughs, screams, zombies, ghosts, burps, splats, slime, sneezes, chants. OpenGameArt had nothing CC0 for sexy/adult. Big packs were sampled (a few of each), long clips cut to their first 5 s. `TURN_SOUNDS` is every file in `sounds/`; regenerate it from the folder when clips change.
- v1.6: **no deck picking for now; random backgrounds.** The user wants deck selection saved for later, so it's switched off, not deleted: `SHOW_DECKS = false` hides the menu's deck list (`#colorField`) and the seats' mana symbols; set it to true to bring both back. Each player's background (`state.bgs`, by edge, synced as `bgs/<edge>`, `bgOf()`) is dealt at random from `ARTS`, every commander art in `art/`: the five Starter decks plus `le`, Living Energy (Aetherdrift Commander, face commander Saheeli, Radiant Creator, Scryfall `drc/3`; `.k-le` seat colors). No two players share one. New game deals them again (`reroll()`, only for the players on this board), and so do changing Sitting out or the 1v1 ×2 pairs. A table from before v1.6 has no `bgs`, so the first new phone to see it sends its own. Attacker chips and Results swatches show the background; the log records `colors` as the background key and `deck` as '' (Results then shows no deck name).
- v1.5: **Sitting out** (menu, 3 players only): pick who sits out (`state.sitout`, synced as `sitout`, default Lenn as before); `PEOPLE[3]` is a getter that returns everyone else in edge order. Changing it starts the 3-player game over (logged first), two taps once it has begun, like the 1v1 ×2 pairs. Why: the user typed "Lenn" into Andrew's name box to play Lenn instead, and `badName()` silently reverted it. Now typing the sitting-out player's name into a box swaps them in (before the game has begun) or shows a note pointing to Sitting out (`#nameNote`); any other player's name still reverts, with a note. Older phones ignore `sitout` and keep showing Rand, Andrew, Trent.
- v1.4: louder. Every sound (clips and synth) goes through `out`: a 4× gain (+12 dB), a limiter (DynamicsCompressor, threshold −6 dB, ratio 20) and a tanh soft clipper, so peaks stay at full scale. Measured 6 to 11 dB louder (RMS) on the clips. To change the loudness, change `out.gain.value`.
- v1.3: **the turn tracker is gone** (the user asked for "just a turn button, not turn tracking"). One big gold button (`.turn-big`, the tap symbol) sits in the middle of the table, with the menu button beside it on the right; on a 4-player Table board both sit on the line above the bottom seat (`placeTurn()`), since the side seats' totals fill the middle, and in "Just me" it sits at the bottom. Tapping it plays a random goofy clip (`turnSound()`): 130 CC0 clips from OpenGameArt in `sounds/` (5 s max, mono MP3, 1.5 MB, credits in `sounds/CREDITS.md`), dealt from a shuffled bag so none repeats until all have played, the next 4 fetched ahead, a new tap cutting off the last. It plays on this phone only. Nothing sets `turns/` any more; the spotlight is always this phone's player, Pick who goes first only shows the "Goes first" badge, and the log's turn counts stay 0 (Results hides them). `turns/` and `clock/` stay in the synced paths for older phones, but nothing shows them. Menu → Sound is now All / Turn only / Off (`state.sound`; v1.2's true/false map to All/Off).
- v1.2: sound (`play()`, `SOUNDS`), all synthesized with Web Audio, no files. A knock for life lost, a tick for life gained (fuller for a hold's ±10), a two-note chime when the turn moves (also when another phone passes the turn to this phone's player), a falling toll when a player goes out, a fanfare when one player is left. Menu → Sound On/Off, kept on this phone only (`state.sound`, not synced). The first touch unlocks audio; an iPhone's silent switch mutes it.
- v1.1: side-by-side 1v1 ×2 on a player's own phone shows all four seats (`sideBySide4()`): their 1v1 in the bottom half upright, the other 1v1 grouped in the top half turned 180°. The top strip is now Classic only. The menu's "<name> plays" picks this phone's opponent (`pairsFor()`).
- v1.0: 1v1 ×2 on a player's own phone shows a strip on top with the other game's two totals (`paintMini()`). Tapping it opens "<name> plays": pick your opponent and the other two pair up (`pairsFor()`, `applyPairs()`; same two-tap confirm as the menu once a game has begun).
- v3.41: the menu button did nothing in 1v1 ×2 (v3.35's `syncMenu()` read `center` before declaring it, so opening the menu threw). Declared first.
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
  - Who plays (`PEOPLE`): 2 players Rand and Lenn (v3.19; it was Trent before); 3 players Rand, Andrew and Trent by default (v3.18; it was
    Lenn before; since v1.5 picked in Sitting out); 4 everyone. Where they sit (`EDGES`) is separate: 2 players use bottom and top, 3 players bottom, left, right.
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
- **Layout** (menu, 3 and 4 players, kept on that phone as `layout4`): **Spotlight** (v3.35, the
  default), **Table** (seats on the phone's edges) or **Quadrants** (v3.34, 4 players only).
  `layoutOf()` picks the one actually used: Quadrants at 3 players falls back to Spotlight, and a
  Center phone or 1v1 ×2 can't use Spotlight, so they get Table.
  - Spotlight (`.board.spot`, seats `sp-main`, `sp-1`..`sp-3`): whoever has the turn takes the bottom
    half (v3.36; v3.35 had it on top), the others share the top in turn order after them, all upright. Before anyone has the
    turn, this phone's player is in it (`spotPlayer()`). When the turn moves, `paintTurn()` rebuilds
    the board. `fitLife()` and `fitNames()` size the big seat apart from the rest (`groupBy()`), and
    the bottom row's names leave room for the spotlight player's name, so they keep one size as
    turns pass.
  - Quadrants (`.board.n4.quad`, a quarter each). Quadrants reuses the edge
  classes in a 2×2 grid (`"left top" "bottom right"`), so the seating order holds, going clockwise
  from this phone's player at bottom left, and each quadrant faces its owner: all upright on a
  player's phone, each turned to its owner's side on a Center phone. Shown for 4 players, and for a
  Center phone in 1v1 ×2.
- **1v1 layout** (v3.6, menu, 2 players only, kept on that phone): **Side by side** (default) or **Classic**.
  Side by side is a 2×2 grid. The bottom half faces this phone's player, the top half is turned to the
  opponent, and each half shows both totals with its viewer's own on the left, so each player's
  colors run down one side of the phone. Each player then has two seat elements (`seats[i]` is a list).
  - v3.7: − and + split each box left and right (the signs themselves were dropped in v3.26).
  - v3.7: each player's own box has a white flag in its bottom-left corner to concede or rejoin
    (two taps), since both players share the phone. The menu's Concede still works too.
- **Turn tracker** (removed in v1.3, see above; kept here as history) (v3.8; 33% bigger in v3.10): a button at the bottom center of every seat (not in "Just me").
  Since v3.27 it's Magic's tap symbol (`ICON_TAP`, from the Mana font's SVGs, github.com/andrewgioia/mana)
  instead of the pink circle the user hated: cream before anyone has the turn, then gold and glowing
  on the current player and dim on everyone else. The side-by-side turn bar is gold too.
  Since v3.37 the current player's seat also gets a gold frame and glow (`.table .seat.turn .turn-bar`,
  the turn bar stretched over the art as a border; every layout but side by side). v3.30 draws
  the symbol at 80% of the button and v3.32 at 54% (a third smaller again); the 3.2em tap target is
  unchanged.
  Tapping the current player's button passes the turn to their left, clockwise around the real
  table (v3.40: Rand → Lenn → Trent → Andrew, backwards through the edge order; before v3.40 it went
  Rand → Andrew, the wrong way), skipping anyone out. The spotlight's top row and Pick who goes
  first's highlight follow the same order. Tapping anyone else's makes it their turn. Once someone has
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
  Since v3.38 the deck's mana symbols sit in the bottom-left corner (`.seat-mana`, from `manaOf()`;
  not in "Just me"); taps pass through them, and side by side they sit above the concede flag.
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
- Back to game is white like New game (v3.22). Since v3.39 the menu also has a small untap-symbol
  button beside its title (`#closeMenuTop`) that goes back to the game, so nobody has to scroll down.
- The menu button in the middle of the table shows the Planeswalker flame (v3.20), an inline PNG
  in `ICON_MENU`.
- Version shows in the menu footer with the sync status. Bump `VERSION` on every release.

### `xenagos.html`: Xenagos, the Party Hugger card carousel
- Live at https://biglob.github.io/commander-life/xenagos.html (since it landed on `main`). A standalone copy of the claude.ai artifact; republish both when it changes. Not a game page; nothing here syncs.
- Card images are embedded as WebP data URIs (about 11 MB), so the page works offline. Bench, Trash and Fav marks are kept in that browser's localStorage only.
- Tabs: Deck, Suggested, Fav, Bench, Trash. Sort & filter covers type, color, cost, keyword and Fav only.

### `decks/`: precon card carousels
- Live at https://biglob.github.io/commander-life/decks/ (`decks/index.html`), one page per deck (`decks/<slug>.html`): the 12 precons in the "Decks we own" table of `buying-guide.md`. Not a game page; nothing syncs.
- Same carousel as Xenagos, minus Suggested (the user dropped it): Deck, Fav, Bench and Trash tabs, sort and filter, zoom, picks code. Marks are kept per deck in localStorage (`pc-<slug>-favs`, `pc-<slug>-marks`). The commander comes first, then the alternate commander (labelled), then spells by mana value, lands, basics.
- Built by `python3 tools/carousel/make.py [slug ...]` from `tools/carousel/template.html` and `index-template.html`. Decklists come from MTGJSON's deck files (exact printings) or, for decks MTGJSON doesn't have yet (Star Trek), Wizards' decklist article. Card data, prices (the precon printing's, else the cheapest paper printing) and image links come from Scryfall; images load from Scryfall's CDN, so the pages are small but need a connection. Brand-new cards with no price yet show "no price". `decks/decks.json` holds each deck's summary for the index.
- To add a deck, add a row to `DECKS` in `make.py` and run it for that slug.
- The claude.ai artifact copy of the Borg page is https://claude.ai/artifact/2iDTXny6HTaVnm5k5pwcZH (private). Artifacts can't load outside images, so `tools/carousel/embed.py <page> <out>` inlines them as WebP (about 6 MB) before publishing.

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
