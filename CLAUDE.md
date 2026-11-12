# Commander Life: project notes

Life counters for a Magic: The Gathering Commander group, played on everyone's phones and kept in
sync live. Plain HTML pages, no build step, no framework.

## Replies

End every reply about anything in this repo with two icon-only links, on one line:

[🃏](https://biglob.github.io/commander-life/) [🗂️](https://biglob.github.io/commander-life/links.html)

🃏 is the Commander Life board. 🗂️ is `links.html`, a tappable list of every page, carousel, guide and
claude.ai artifact we've made (the user dropped the per-page icons, sounds included, for this). The Xenagos
editable artifact is https://claude.ai/artifact/D3rxfusL2qGunJxamxqMa2 (private; listed in
`links.html` under claude.ai artifacts, which only open for the account that made them).

## Commander legality (always)

The user's rule: **call out or mark any card that isn't Commander-legal**, everywhere.

- In replies: whenever a card comes up (a suggestion, a list, a price check), say so if it isn't legal in
  Commander (banned, an Un-card or playtest card, Arena/MTGO only, or not released yet). Check Scryfall's
  `legalities.commander` rather than memory.
- On pages: every card page marks such cards. The rodent pages show a red "Not Commander-legal" chip
  (and the legends page only lists legal ones); `make.py` and `brew.py` set the card's note to
  "Not Commander-legal"; the lands page says "not Commander-legal yet (not out)" for unreleased lands.
  Any new card page must do the same.
- Pages that list cards meant to be played (decks, brews, commander lists) default to legal cards only,
  unless the user asks for everything.

## Keep `links.html` current (always)

`links.html` is the group's table of contents. Every time we build or gather something, update it in
the same commit, without being asked:

- a new page, carousel, guide or tool on the site: add a row in the right section;
- a new claude.ai artifact (even a preview or a copy): add it under claude.ai artifacts;
- new info gathered into a file (a price list, primer, deck list, research notes): add or update its row;
- something renamed, moved or deleted: fix or remove its row; a changed count (say "All 13 decks"): update it.

Never add icons to the reply footer for these; the footer stays 🃏 and 🗂️.

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

**Always deploy, never ask.** Once a change is tested, commit it, push it to the session's branch
and push the same commit to `main` (`git push origin HEAD:main`) in the same turn, without asking
first. The user always wants changes live. This standing permission covers pushing to `main`.

The site only changes when files land on `main` of `BigLob/commander-life`:

1. Make and test the change (in `BigLob/Mtg` or directly here).
2. Copy `index.html`, `archenemy.html`, `patterns/`, `fonts/`, `art/` and `sounds/` into this repo, commit, push to `main`.
   `decks/` and `lands/` are built here by `tools/carousel/make.py` and `lands.py`, and `links.html` is kept here (no copy from `BigLob/Mtg`).
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

### `index.html`: Commander Life (current v1.59; the user reset the version number from 3.41 to 1.0 at this release, so v3.x notes below are the old numbering)
- v1.59: **Gears of War clips (7, 896 in all)**, group Gears of War (`gow-*`): Marcus's "NICE!", "It's a goddamn Leviathan!", cog tag, Boomer, reload, the theme and the Locust theme (long). Myinstants had little: only those; no Cole Train, Dom or Baird lines turned up. Not CC0 (credits in `sounds/CREDITS.md`).
- v1.58: **announcer lines in female, more human voices** (the user's ask). All 60 `tts-*` lines remade with Kokoro (82M, Apache 2.0, via `pip install kokoro-onnx soundfile` and the model files from github.com/thewh1teagle/kokoro-onnx releases, `model-files-v1.0`), voices af_heart and af_bella on alternate lines, by `python3 tools/sounds/make_tts.py [name ...]` from each clip's `quote` in `clips.json` (then run `make_list.py`). No pitch shift or echo any more; trimmed, high-passed at 80 Hz, -16 LUFS. 23 lines got contractions ("It's your turn") so they read like speech. `SAY` in the script respells words Kokoro gets wrong (mana read as "Mona", now "manna"). Each line was checked by transcribing it back with faster-whisper. Same file names, so nothing else changed.
- v1.57: **menu button at the top junction** (the user's ask, with a screenshot): on every 4-player Table board, Big button and the Spotify dock included, on a player's phone or a Center phone, the menu button sits where the top seat's bottom edge meets the two side seats' top corners (`menuAtTop()`, measured from the seats' boxes, run from `placeTurn()`). It replaces v1.52's spot on the bottom seam, Big button's rim spot and plain Table's spot beside the turn button. Other layouts (Spotlight, Quadrants, 1v1s, 3 players, the Spotify bars) are unchanged.
- v1.56: **AI voice lines remade, Star Trek and XCOM.** The user's rules for announcer lines (`tts-*`): **every line starts with a player's name** (Rand, Andrew, Lenn or Trent), **no commander names** (the app doesn't know who plays what), and **nothing that hints at Lenn's gift deck** (no squirrels, tokens or going wide: the Camellia brew is a surprise). All 70 old lines were deleted and 60 new ones made (12 each for Rand, Andrew and Lenn, 24 for Trent); none are in `out`/`win` any more (a named line would be wrong for whoever went out). 40 Star Trek clips (group Star Trek, `trek-*`), mostly TOS and TNG: KHAAAN!, the Borg (We are the Borg… Resistance is futile), Picard (The line must be drawn here, Shut up Wesley, Captain's log), Kirk, Spock, McCoy, Scotty, Qapla', and effects from **TrekCore** (trekcore.com/audio, reachable with a browser User-Agent: transporters, red alerts, doors, tribbles, bosun whistle, Borg sounds, TOS voice clips). **No Q clip exists on any site the sandbox reaches** (myinstants, soundboardguy, TrekCore, archive.org); the user would have to send files. XCOM: only 2 Enemy Unknown soldier lines exist on myinstants (`xcom-*`), nothing from XCOM 2: War of the Chosen. 889 clips in all.
- v1.55: **96 more turn-button clips (857 in all).** 52 from myinstants uploads, screened by faster-whisper, each in its own group in `clips.json`: Halo, Zelda, Mario, Pokémon (four cries; no fainting cry was found), Metal Gear, Street Fighter, Mortal Kombat, Unreal and Quake, Skyrim, Portal, StarCraft, WarCraft, Lord of the Rings, Monty Python, The Office, The Simpsons, Star Trek, Jurassic Park, Game shows (Price Is Right horn, Jeopardy think music, Law & Order). Nelson's "Ha-ha!" left out (laughs cut in v1.50). 44 more Piper announcer lines (`tts-*`, group Announcer, `who` "Announcer (at <player>)"): Magic calls (Sol Ring, Cyclonic Rift, commander tax, pay the one), each of our 14 decks' face commanders (`tts-cmd-*`), and player jabs, 3 each at Rand, Andrew and Lenn and 12 at Trent (the user: "be especially sassy to Trent"). Piper: `pip install piper-tts`, voices en_US-ryan-high and en_GB-alan-medium from huggingface.co/rhasspy/piper-voices, then asetrate ×0.93, atempo 1.04, a short aecho and loudnorm -16. `out` gained Mario's death, Fatality, the Price Is Right horn, the turret's Goodbye, Humiliation, D'oh and No God please no; `win` gained Godlike, Monster kill, Excellent, Impressive, Killtacular and Zelda's item get.
- v1.54: the Spotify remote's explainer note ("Play, pause and skip…") is gone while the remote is off (the empty note is hidden), and **This phone is** is folded by default like Sound and Speaker (its summary names the owner).
- v1.53: **menu reordered, Concede cut, footer trimmed** (the user's ask). Menu order: Players (with its AE, Schemes, pairs and Sitting out fields), Layout and 1v1 layout, Starting life, New game, Pick who goes first, then Spotify, Sound, Speaker, This phone is, deck, Results, Back to game. The menu's Concede (`#concede`, `toggleConcede()`) is gone, so nothing can concede now; a `conceded` flag from an older phone still counts. The footer shows only the version (`v1.53`; " · offline" when the phone has lost the table); "Sharing live with this table" and the round-trip time are gone (`trips` is still collected). Tapping it still shows Results.
- v1.52: **menu button centered on the seam** in 4-player Table with Spotify (the dock layout): it sits under the turn button, its middle on the gap between the side seats and the bottom seat, in line with the side seats' own seam (`placeTurn()`; v1.37 hung it 10 px into the bottom seat). `.menu-btn` keeps `translateY(-50%)` there, so the code checks the computed transform.
- v1.51: **long clips half as often, steady weights, and four new groups.** `LONG_FACTOR` (0.5) weights the long pools so long clips come up half as often as their share of the library (about 18% of taps); the weight is worked out from the clip counts at load, so it holds as clips are added. `turnSound()` now picks a pool by its size times its weight on every tap (the round counter `left` is gone), so the weights (presidents too) hold all night instead of only delaying clips to the end of a round. Each pool's shuffled bag lives in the page until it reloads; New game doesn't reset it. 87 clips from myinstants uploads, screened by faster-whisper: **Duke Nukem** (14, `duke-*`), **Doom** (12, `doom-*`), **Dark Souls** (24, `souls-*`), **Star Wars** (37, `sw-*`), 761 clips in all; groups of the same names in `clips.json`, credits in `sounds/CREDITS.md`. Left out: French Duke lines, remixes, meme edits, Lego Star Wars, Elden Ring, Palpatine's laugh. `out` gained YOU DIED, Doomguy's death, Vader's Nooo, the Wilhelm scream, Shit happens and You were the chosen one; `win` gained VICTORY ACHIEVED, Hail to the king, Hell yeah, Most impressive and Praise the sun. faster-whisper isn't preinstalled: `pip install faster-whisper`, and decode audio with ffmpeg to a numpy array (its own decoder fails with this PyAV).
- v1.50: **every laughing clip cut** (the user's ask): 46 clips (the 1920s laughing records, `laugh-*`, evil laughs, cackles, giggles, `hihihihihihihihing`, `demon-snigger-1`), 674 clips left; `long/laugh-okeh-1` left the win list. The **Sound map** artifact (https://claude.ai/artifact/HPPNAAMu8io4Pn8Kg9HzC6, built from `sounds/clips.json` with a genre per clip by file-name rules and a simulation of `turnSound()` over a 150-tap night) shows each genre, its clips and its share per trigger, for the user to plan bigger changes. Note: `PRES_WEIGHT` only delays presidents within a round (a round is every clip once), it doesn't remove them.
- v1.49: **backgrounds crop round the character's face** (the user's ask: the crop changes with the device and layout). `FACES` holds a face point per art key (fractions of the 626 × 457 art_crop, picked by eye from a gridded contact sheet); `placeArt()` (run from `centerLife()`, so on every resize and rebuild) sets each seat's `--artpos` so the point sits as near the middle of the seat as `cover` allows, measured in the face's unturned layout. A seat only moves the picture the way it has spare picture: tall tiles slide sideways, wide ones up and down. **A new background needs a `FACES` entry** (without one it stays centered).
- v1.48: **"Pick who goes first" popup after New game** (the user's ask). Only on the phone that tapped New game (each phone's pick is its own random draw, so others would disagree), and not in 1 or AE. A gold pill over the middle of the screen (`#firstAsk`, `.first-go`) with a small × (not now); the seats stay tappable under it. Tapping it runs `pickFirst()` and hides it; so does any change to a total or commander damage, here or from another phone (`update()` checks `askKeys`, the games it asked about, against `untouched()`). The menu's Pick who goes first hides it too.
- v1.47: **next is the big Spotify button** (54 px, the user: it's tapped most), play/pause the small green one (46 px), same places, in every Spotify layout. **Spotify text in the card-text font everywhere**: MPlantin's non-ASCII Unicode map was scrambled (’ drew Ê, – drew ·), so accents, curly quotes and dashes fell back to Georgia. `fonts/Mplantin-text.woff` (replaces `Mplantin.woff`; a new name so phones don't keep the old file under the wider range) has its Unicode map rebuilt from the font's Mac Roman table, keeping only the 98 characters checked by eye (Latin-1 letters, Œœ, ’‘“”„, – —, …, •, †‡, ™ and a few more; not ·, ×, ÷, ¬ or Ò, which are blank). The page-wide `unicode-range` lists them, so the menu gets them too. Also: the 4-player dock's play and next had wrapped onto two lines (the dock may only take half the seat's width); a song's buttons now stay on one line.
- v1.46: **new middle Spotify bar** (Classic, 3-player Table, Quadrants, any Center phone; the user's sketch): the turn button takes the right 36%, full height, up to 200 px (was 96); on the left the song and artist fill the top and a row under them holds play/pause, next and the menu button, left to right. The menu button is placed by `placeTurn()` over `.sfy-mspot`, a spacer `sfyPaint()` adds at the end of every state's buttons (shown only in the middle bar), so it also follows Connect Spotify or the device list.
- v1.45: **the menu button sits in the button box's bottom-right corner** (10 px in), not beside the turn button.
- v1.44: **button box in Classic and Side by side** (the user's ask: seats pulled in to the short edges by a third, room for a bigger, better-looking button box). Without the Spotify bar, 2-player Classic and Side by side (also 1v1 ×2's, and the four-seat Side by side) put each seat in a third of the phone (board class `boxed`, rows `1fr 1fr 1fr`, area `mid`) with a dark rounded box between them (`.btn-box`). `placeTurn()` sizes the turn button to fit it (76% of its height, 48% of its width, 96 to 200 px) and the menu button (46 to 64 px) in the room to its right, at most 28 px out on a wide screen. Couch and the Spotify layouts are unchanged.
- v1.43: **bigger song and artist in the middle bar** (the user's ask: fill the space). The song grows first, up to 3× (`--sfb`), as big as fits with no word broken while leaving one artist line; then the artist grows into what's left (`--sfs`), never bigger than the song. Neither goes below its normal size (17px, 14px); below that it's cut by whole lines as in v1.42. Width is usually the limit: the text column is only about 116 px on a phone.
- v1.42: **the middle Spotify bar's song and artist fill their box** (left of the turn button, above the menu button): they wrap instead of cutting to one line, grow up to 1.6× when there's room (no word broken), and when they don't fit stop at whole lines with an ellipsis, song first, artist keeping one line (`sfyFit()`, run from `placeTurn()`; `.sfy-text` keeps the menu button's room as a margin so overflow clips above it).
- v1.41: **the Spotify dock's play/pause sits at the middle of the seat**, next to its right: an invisible spacer the width of next on the dock's left (`.sfy-dock .sfy-text.song ~ .sfy-ctl::before`, only while a song shows) balances it.
- v1.40: **installable app.** `app/manifest.json` (display `fullscreen`, start and scope the site root) and the Planeswalker flame icon (`app/icon-192.png`, `app/icon-512.png`, the menu button's `ICON_MENU` on the page's dark background), linked from `index.html`. Without a manifest, Chrome on Android's Install opened the page with an address bar. Chrome reports no installability errors. A phone that installed it before has to remove that icon and install again to pick up the manifest; later updates arrive by themselves.
- v1.39: **the soundboard moved out of the game** (the user: not in Commander Life). v1.38's menu field, `BOARD`, `boardSound()` and the `sb-` pings are gone; it's its own page now (see `sounds/soundboard.html` below).
- v1.38: **Soundboard** at the top of the menu (`#sbField`, `.sb`): a gold button per kind of sound, starting with **Presidents** (every presidential clip, both lengths, from the `pres-*` pools). Each kind is its own shuffled bag (`BOARD`, `boardSound()`), so nothing repeats until all have played. Plays whatever the Sound setting (the tap is the ask), and on the speaker phone when there is one (`ring('sb-<kind>')`, handled in `hearPing()`; phones older than v1.38 ignore it). To add a kind: a `data-sb` button and a `BOARD` entry.
- v1.37: **4-player Table with Spotify is Big button plus a dock** (the user picked it from two mockups over v1.35/v1.36's middle column). With the remote on, 4-player Table and Big button (also a Center phone in 1v1 ×2) draw as Big button (`dock` in `build()`, board class `sfyp`, no `sfy`): the huge turn button where the side seats meet, play/pause and next in a dock at the bottom of the bottom seat (`.sfy-dock`, appended to `.seat.s0`: this phone's player, Rand on a Center phone; only messages show there, never the song), and the menu button at the top middle of that seat (`placeTurn()`). The bottom seat's total keeps clear of the dock (`DOCK_H` in `centerLife()` and a cap in `fitLife()`). The middle-column CSS is gone.
- v1.36: **Side by side with Spotify drops the turned top half** (the user: nobody sits at that end when the bar is up). 2-player Side by side with the bar on shows the bar, then only the upright half, this phone's player left and the opponent right (`.board.duel.half`, `duelSpots()` filtered to `d-bl`/`d-br`), turn button at 79% like Couch. 1v1 ×2's four-seat Side by side keeps its top half (the other pair sits there). Without the bar, Side by side is unchanged. **The 4-player Table / Big button column shows only play/pause and next**: the song and artist are hidden there (`.sfy-text.song`); messages and the device list still show.
- v1.35: **Spotify remote in every layout, fewer controls.** Where the seats face one way (Side by side, Couch, Spotlight, 1) the bar is across the top (Couch's turn button moves to 79%, Spotlight's follows the seam above the big seat); where they sit round the edges (Classic, Table, Big button, Quadrants, any Center phone) it's in the middle, so every total stays on the outside: a middle row (Classic, 3 players, Quadrants) or a middle column between the side seats (4-player Table and Big button; Big button then has no huge button). In the middle the turn button sits in the bar's hole (`.sfy-hole`, placed by `placeTurn()`). The bar has only the song, artist, play/pause and next: album art, volume, previous ("start over") and the "On <device> · 76%" line are gone (the device list still opens when nothing plays or Spotify has no device). The menu button lives in a corner of the bar while it shows (bottom-right on top and in the column, bottom-left in the middle row). The menu's Spotify field shows in every mode.
- v1.34: **no concede flag on any seat** (the white flag of v3.7 and Couch; `bindFlag()`, `.flag`, `ICON_FLAG` gone). The menu's Concede is the only way now, and only for this phone's seat. **No commander damage dagger in 2-player games** (2, and each 1v1 of 1v1 ×2, every 1v1 layout): `makeSeat()` leaves out the tray when the seat's game has 2 players or fewer (`SIZE[players[i].k] > 2`).
- v1.33: **no speaker-phone banner.** v1.20's yellow "Speaker phone: tap anywhere to turn its sound on" note (`.speaker-wake`, `speakerWake()`) is gone. Sound is on by default: `unlock()` runs at load (works where the browser allows sound without a touch) and on any first pointerdown, touchend, click or keydown. Phones still need one touch before they can play (browser rule), but nothing asks for it.
- v1.32: Players labels are now **1** (was Solo) and **AE** (was Archenemy; the field picking the archenemy is labelled AE too). **Sound** and **Speaker** fold away (`<details>`, closed by default), their summary showing the current setting (`#soundNow`, `#speakerNow`). Every phone is put back on Sound All once (`state.sound132`); All stays the default.
- v1.31: **Spotify remote** (menu → Spotify remote → On, kept on that phone in localStorage `cl-spotify`, never synced). In Side by side (1v1 and 1v1 ×2) the top 20% of the phone becomes a bar (`.board.duel.sfy`, `.sfy-bar`, rows `1fr 2fr 2fr`; the turn and menu buttons follow the halves' seam in `placeTurn()`) that controls whatever the signed-in Spotify account is playing on any device: album art, title, artist, play/pause, previous, next, volume ±10, and the device (tap "On <device>" to list devices and move playback). Spotify Web API with PKCE sign-in, no server: needs Premium, and a Spotify developer app (developer.spotify.com/dashboard, Web API) whose redirect URI is exactly `https://biglob.github.io/commander-life/`, with each account that signs in added under User Management. The app's client ID is built in (`SPOTIFY_CLIENT_ID`, a public value, not a secret), so the menu's ID field stays hidden; phones only tap On and Connect. Polls `/me/player` every 5 s while the bar shows (`sfyPoll()`). Tested in Playwright with the Spotify API mocked (the sandbox can't sign in for real). Same release: Concede in the menu had been pulled to the top of the panel since v1.0, because the 1v1 ×2 strip's `.mini` rule also matched `.action.mini`; the strip's rule is now `div.mini`.
- v1.29: the one-player option is labelled **Solo** (was "Just me").
- v1.28: **Couch, a third 1v1 layout** (menu → 1v1 layout → Couch, `layout2 = 'couch'`, kept on that phone). Two people sit side by side behind one phone: one upright seat each, full height, Rand (edge 0) on the left and Lenn on the right (`.board.couch`, spots `d-cl`, `d-cr`), each with their own concede flag. The turn and menu buttons sit lower (74%) clear of the totals. In 1v1 ×2 (v1.30) a player's phone shows only their own 1v1, their seat on the left, with no strip or turned seats on top.
- v1.27: **fewer presidential lines.** They were 19% of taps (Trump alone 10%). Each president's clips now sit in their own pool per length (`pres-<name>`, split out of the talk pool by file name in `index.html`), weighted `PRES_DEFAULT` 0.35 and Trump `PRES_WEIGHT` 0.1 in `turnSound()`'s draw: presidents about 5% of taps, Trump about 1%. Raise those weights to hear them more.
- v1.26: **our scheme cards in the builder.** The group owns Archenemy: Nicol Bolas (2017, 20 schemes; see `buying-guide.md`). The deck builder's first row, "The cards we own", picks all 20 in one tap (`OURS`), and it's the default pick (v1.25's untouched Jump Scare default moves over once, `pick.ours126`).
- v1.25: **Archenemy in Commander Life** (menu → Players → Archenemy, `ARCH = 6`, its own game key `6`, so it never touches a 4-player game). One archenemy at 40 (`AE_LIFE`) against three heroes at 20 (`HERO_LIFE`), whatever Starting life says (`startOf(k, j)`; the Starting life field and Pick who goes first are hidden, the archenemy goes first). Seat j is edge j. Menu → **Archenemy** picks who (`state.ae`, synced as `ae`, Rand by default; changing it starts the game over, logged first, two taps once begun, like Sitting out). The archenemy's name is gold with a crown (`.seat.arch`). Heroes' daggers offer only the archenemy (`oppsOf()` keeps each chip's cmd slot); the archenemy's offers all three. The game ends when the archenemy is out (the heroes win together, all three get the gold frame and confetti, even ones already out) or every hero is (`winners(k)`, which `finished()`, the party and `record()` use). Results log `mode: 'archenemy'`, `schemes`, and `ae` per seat, and show "The heroes beat Rand" or "Rand, the archenemy, won". Menu → **Schemes** (synced as `schemes`): **App's deck** (`'app'`) or **Our cards** (`'cards'`, the group's physical scheme cards: no scheme button, the app only keeps totals). With App's deck the archenemy's seat has a scheme button in its bottom-left corner (`.sch-btn`, naming the scheme in motion, gold while one is; icon only in the spotlight's small seats) that opens the scheme sheet (`#schemeSheet`) on any phone: the deck builder (deal 20 at random from the sets picked, a Duskmourn Commander deck's ten, or tick by hand; 10 minimum; picks kept on this phone in `state.pick`), then Set in motion, Done (to the bottom) or Keep it in play (ongoing), Abandon, Undo (this phone's own moves), New scheme deck (two taps mid-game) and History. The deck is synced whole as `scheme` (`normScheme()`; Firebase turns arrays into objects and drops empty ones), skipped by `adopt()` while this phone's own write is in flight (`held('scheme')`). A scheme set in motion pops up on every phone (`schemeArrived()`), not on a reload. New game shuffles every scheme back into the deck (`reshuffled()`). The schemes (`SETS`, `PRESETS`, `CARDS`: 102 with full text) come from `archenemy.html`, which stays live as the old page. Older phones reject mode 6 and keep their own mode.
- v1.24: **winner celebration.** When a game is down to one player, every phone (not just the one that made the last change) shows it: a gold flash from the winner's seat, confetti bursts from it then a shower from the top (one canvas, `.confetti`, removed when the last piece falls), a crowned shining "Winner" banner (`.win-badge`) and a pulsing gold frame for 10 s (`.cheer`, `CHEER_MS`), and a long vibration. After that the winner keeps a gold frame and a gold total (`.won`) until New game. `watchWins()` (run from `update()`) watches `finished(k)` per game: a game already won when the phone first sees it (a reload) gets the frame but no party, and a mistap that brings someone back ends it. Reduced motion: flash and banner only, no confetti.
- v1.23: **Big button without the empty middle** (the user disliked the black void). The side seats run up to the middle again (Table's grid, rows `1fr 1.4fr 1fr`), so it's all tap area, and the button sits over where they meet: radius `min(21% of the screen's short side, 40% of the middle row)` (`hubGeom()`, about 344 px across on an iPad), the menu button on its lower-right rim (above it, `z-index: 11`). `hubFree()` gives each side seat the room the button leaves it: on a player's phone its inner side is cut off (readout padding), on a Center phone its top (which faces the middle), with the name moved to the bottom by the player's own edge. `hubLife()` (run from `centerLife()`) sets that padding and `fitLife()` caps every total to fit it. The `.hub-spot` cell is gone.
- v1.22: **Big button layout** (menu → Layout, 4 players, made for an iPad on the table). Table's seats on the edges, with a middle cell of their own (`.hub-spot`, grid area `hub`: 40vmin wide, rows `1fr minmax(40vmin, 1.4fr) 1fr`) so the turn button can be huge without covering the side seats' totals. `placeTurn()` sizes the turn button to 86% of that cell (about 280 px on an iPad) and puts the menu button in its bottom-right corner. Works on a Center phone and a player's phone; at 3 players it falls back like Quadrants. `layout4` value `'hub'`.
- v1.21: **no more bouncing totals (the "lag").** The user found an iPad plus phones too laggy to use. Measured: rendering isn't it (a remote change takes about 3 ms to apply even on a 6× slowed CPU). The stream echoes each write back a round trip later, and `adopt()` took it over newer local taps, so during fast taps totals jumped back (40, 39, 38, 37, then 39 again) on every phone. Now `send()` counts each path's writes in flight (`pending`), `adopt()` leaves a path alone while it has any and for `HOLD` (700 ms) after the last one lands (`held()`), then takes the table's value (by then every phone's taps). Tested with 1.2 s round trips and two phones tapping one total at once: each counts its own taps smoothly, both settle on the right total. The footer now shows the median round trip of this phone's writes (`showVer()`, `trips`), to see each device's real sync speed. If that number is high on real phones, the next step is the Firebase JS SDK (one WebSocket for reads and writes) instead of REST PATCH plus EventSource.
- v1.20: **speaker phone.** Usually only one phone is on the soundbar. Menu → Speaker: **Each phone** (as before) or **This phone**. Synced as `speaker/id` (a random per-phone id, `state.phone`, kept on that phone), `speaker/me` (its owner, for "Rand's phone" in the menu) and `speaker/at` (it checks in every 30 s while visible, and holds the screen wake lock). While another phone is the speaker, fresh (checked in within 90 s) and this phone is live, the turn button and the knockout/win sounds (`EVENT_SOUNDS`) don't play here: `ring()` sends `ping/n` (a server increment), `ping/k` ('turn', 'out' or 'win') and `ping/by`, and the speaker phone's `hearPing()` plays a clip from its own pools (so no repeats across the table). Life ticks still play on the tapped phone. A connection's first look at `ping/n` is only noted (`pingSeen`), so a reload never replays an old ping. A stale speaker or an offline phone falls back to playing locally. `ping/` isn't in `allPaths()` (it isn't state); `speaker/` is, and changes to it only refresh the menu, not the board. Older phones ignore both and play their own.
- v1.19: **dialogue louder.** Talk clips (any clip in a `talk` pool, also when `EVENT_SOUNDS` plays one) go through a 120 Hz high-pass, a +4 dB peak at 3 kHz, a hard compressor (threshold -30 dB, 6:1) and `TALK_GAIN` (3×) before `out`'s limiter, in `playBuffer(buf, name)`. The files are unchanged: talk and sound clips were already matched at about -16.5 LUFS, but speech sounded quieter on phone speakers. Plain gain barely helps (`out` runs near full scale, so its limiter squashes it: +1 dB measured); the compression raises the average level instead: +2.2 dB on six lines, about 1.4 dB above the sounds (was 0.8 dB below). For more contrast the next lever is turning the sounds down, not dialogue up.
- v1.18: **Mega Man 1 to 3 sounds and the spoken-lines page.** 20 NES effects and jingles (`megaman-*`, `megaman2-*`, `megaman3-*`; group "Mega Man" in `clips.json`): 10 from archive.org's "Mega Man sound effects" upload (death, teleport in and out, landing, boss door, enemy hit and explode, Met shot, big energy, thrust; shared by Mega Man 1 to 3), 10 from myinstants uploads named for the game (1-up, Mega Man 2 buster, teleport, game over and boss-defeated jingle, Mega Man 3 stage clear, spawn, Proto Man's whistle full and short). Capcom's, not CC0. Left out: Mega Man 4 and later (charge shots), Mega Man X, the cartoon, and uploads that don't name the game. sounds-resource.com and KHInsider are blocked from the sandbox (Cloudflare 403). **Spoken lines** (`sounds/lines.html`, built by `make_list.py` from `lines-template.html`): every `talk` clip grouped by speaker, with its words, original occasion and source. `clips.json` gained `who` (speaker) and `from` (occasion, filled only where well documented: debates, speeches, the Correspondents' Dinners, Apollo and Mercury flights; 124 of 211), and YouTube sources now carry the upload's title and channel (from YouTube's oEmbed, which the sandbox can reach). The 35 OpenGameArt voice lines got their words.
- **Pool ratios follow the content.** Since v1.17 there's no ratio to keep up: each tap is weighted by the clips each pool has left, so adding sounds or dialogue shifts the mix by itself. What matters is tagging each new clip's `kind` right (`talk` for anything with words) and giving talk clips `quote`, `who` and, when known, `from`.
- v1.17: **dialogue as often as its share too.** Dialogue was a flat 30% of taps (`TALK_SHARE`, gone), though it's 26% of short clips and 35% of long ones, so short lines repeated before long ones had all played. Now each tap picks one of the four pools (short or long, sound or talk) weighted by the clips it has left this round (`left`, one count per pool in `all`), so all four run out together. Dialogue is about 30% of the clips, so it's still about 30% of taps.
- v1.16: **long clips as often as their share.** A long clip used to come after every 3 to 10 short ones (about 13% of taps), though long clips are 43% of the library, so they took three times as long to come round. Now each tap is long with the chance long clips have among those not yet played this round (`left`, reset when both run out), so short and long run out together, with natural runs of either. `LONG_EVERY` is gone.
- v1.15: **how turn-button clips are picked.** Short is now 3 s at most and long anything over 3 s (it was 5 s), set by each clip's length, not its folder (`sounds/long/` still holds only the over-5 s cuts; the root has both). Every clip is also a `sound` or `talk` (dialogue: anything with words, from the quote field or a faster-whisper screen of the rest, checked by hand) in `sounds/clips.json`. Each tap still plays a long clip after every 3 to 10 short ones (until v1.16), and is dialogue 30% of the time (`TALK_SHARE`) and a sound otherwise. Four pools, each its own shuffled bag (`TURN_POOLS`, written into `index.html` by `tools/sounds/make_list.py`, which replaced the hand-kept `TURN_SOUNDS` and `LONG_SOUNDS`). The clip list shows each clip's kind and filters by it.
- v1.14: **76 more presidential lines and noises** (138 presidential clips in all): Trump's bing bing bong in five cuts, China (once and a 10-time compilation), Obamna, You're fired, Wrong, Sad, I love cows, hot dogs, tired of winning; Biden (come on man, will you shut up man, Corn Pop, I-was-in-the-foot, gibberish, hairy legs, 300 million billion); Obama (come on man, come on people); Bush's shoe dodge; Clinton's "sexual relations"; Nixon's "not a crook"; Reagan's "Oh, shut up"; JFK's "Ich bin ein Berliner". From meme uploads on myinstants.com (reachable from the sandbox; YouTube downloads are blocked by its bot check), searched by president and famous moment, screened by faster-whisper transcript; remixes, songs, impressions, AI voices and slurs left out, and Trump's trans-athlete "aagh" impression too (ask before adding). `out` gained You're fired, And we say bye-bye, Sad and Biden's Come on man; `win` gained Tired of winning. The clip list's Random president names Biden, Clinton, Nixon and Reagan too.
- v1.13: **76 more clips and knockout/win sounds.** NASA's public-domain audio from soundcloud.com/nasa, fetched with yt-dlp (`nasa-*` Apollo and Mercury lines like "The Eagle has landed", "Houston, we've had a problem"; `space-*` 13 eerie planet and plasma recordings; `jfk-*` two moon-speech lines), 20 cuts from five 1922 to 1925 laughing records on archive.org (`laugh-*`, public domain), 3 effects (`sfx-*` goats, slide whistle, record scratch) and 26 text-to-speech announcer lines made with Piper (`tts-*`: "Counterspell!", "Resistance is futile", "Rand. Rand. It is your turn."). `EVENT_SOUNDS` in `index.html`: a player going out plays a random clip from the `out` list (sad trombones, game-over tunes, "Obama out", "Houston, we've had a problem") and the last player standing one from `win` (victory fanfares, "The Eagle has landed", "I am the chosen one"), instead of the synth toll and fanfare, which stay as the fallback. Like the other game sounds they play on the phone that made the change, Sound All only. Wikimedia Commons rate-limited the sandbox (HTTP 429) after a few files, and freesound.org is blocked (403), so more effects (sad trombone, air horns, drum roll, kazoo, gasp, crickets, cuckoo clock) went on the user's download list. The clip list's group chips are now built from the groups in `clips.json`.
- v1.12: the five Trump lines v1.11 had left out because they're aimed at groups of people, added at the user's request: `trump-fat-pigs`, `trump-we-love-puerto-rico`, `trump-black-community`, `trump-eating-the-dogs`, `trump-turn-black` (all in `sounds/long/`; 60 presidential quotes in all).
- v1.11: **presidential quotes** on the turn button: 55 lines from George W. Bush, Obama and Trump (`bush-*`, `obama-*`, `trump-*`; 20 in the short pool, 35 in `sounds/long/`). The user downloaded 25 YouTube clips on their PC (the sandbox can't reach YouTube's downloads) and sent them as a zip; they were transcribed with faster-whisper (small.en) for word timings, cut to one quote each (10 s at most, a few with pauses shortened), loudness-matched to -16 LUFS and saved as mono 64 kbps MP3. Each quote, length and YouTube link is in `sounds/CREDITS.md`. Not CC0 like the rest. Trump's health-care clip failed to download, and two downloads were the wrong video, so `bush-misunderestimated` comes from the Bush compilation and Strategery (an SNL line) was dropped. The user dropped Blazing Saddles, Drag Race and Rocky Mountain Way.
- **Soundboard** (`sounds/soundboard.html`, live at https://biglob.github.io/commander-life/sounds/soundboard.html; claude.ai artifact copy https://claude.ai/artifact/9NNymZFnYgRqhgqrFGhEe9, which plays because its clips are embedded, 7 MB): a big gold button per kind of sound, each dealing a random clip from its own shuffled bag, with the words and speaker shown. Only **Presidents** (all 138 Presidents-group clips) so far. Built by `python3 tools/sounds/make_soundboard.py [artifact-out.html]` from `tools/sounds/soundboard-template.html` and `sounds/clips.json`; to add a kind, add it to `KINDS` in the script and a `data-k` button in the template, rebuild, and republish the artifact from the embedded output. Rebuild it after adding clips.
- **Clip list** (`sounds/index.html`, live at https://biglob.github.io/commander-life/sounds/): every clip with length, pool and source, filters, search and a play button. Built by `python3 tools/sounds/make_list.py` from `sounds/clips.json` (one entry per clip: file, pool, length, kind, source and link, group, and the words for quotes); the same run writes the turn button's `TURN_POOLS` into `index.html`. After adding clips, run it, fill in the new entries' sources and check their `kind` in `clips.json`, and run it again. Seven older clips (`castle-fanfare`, `squishpop`, `squishsplat-impact`, `stage-clear-1` to `-4`) have no recorded source page. A **Random president** button at the top plays one random quote from the Presidents group (Bush, Obama, Trump, Biden, Clinton, Nixon, Reagan, JFK), dealt from a shuffled bag so all of them play before any repeats, and shows its words and speaker. Its claude.ai artifact copy (no playback there) is https://claude.ai/artifact/XKDkaimq128iz5n91fBda4.
- v1.10: **13 more backgrounds**: the face commander and alternate commander (the box's second foil, and the second card on Wizards' decklists) of every other deck the group owns or preordered. Keys and Scryfall cards: `le2` Pia Nalaar (drc/2, Living Energy's alternate), `em` Temmet (drc/4) and `em2` Hashaton (drc/1) for Eternal Might, `rt` Terra (fic/4) and `rt2` Celes (fic/1) for Revival Trance, and the Star Trek decks: `bq` The Borg Queen (trc/1) and `lo` Locutus of Borg (trc/97), `pi` Jean-Luc Picard (trc/3) and `ja` Captain Janeway (trc/84), `sp` Commander Spock (trc/2) and `ki` Captain Kirk (trc/85), `wo` Worf (trc/4) and `ko` Kor (trc/96). Each has `art/<key>.jpg` (art_crop), `art/<key>-card.jpg` (normal) and `.k-<key>` seat colors. Phones older than v1.10 reject the new keys (`validValue()`), so until they reload they keep their old background for that seat.
- v1.9: **Pick who goes first shows the winner** (the user: it "blanks out the winner"). The seat highlight used the class `pick`, which is also the menu's "This phone is" ring (a 40 px see-through circle), so the chosen seat vanished. Now the highlight runs round as `.lit` (gold frame), and the winner gets `.first` (thick pulsing gold frame, a big gold "Goes first" banner across the middle of the seat, a vibration) while everyone else is `.passed` (dimmed) for 8 s. Don't reuse menu class names on seats.
- v1.8: happy and sad clips, and **long clips**. 59 more short ones (victory and level-up stings, win jingles, cheers, sad trumpets; 415 short in all) and a second pool, `LONG_SOUNDS` in `sounds/long/` (73 clips, 5 to 12 s: victory, level-clear and game-over tunes, sad songs, and full-length cuts of earlier long sources like `laughing-fit` and `fart-symphony`). After every 3 to 10 short clips (`LONG_EVERY`, a new random count each time, per phone) the next tap plays a long one. Each pool has its own shuffled bag (`pools`). `sounds/` is now 16 MB, but phones only fetch the next few clips.
- v1.7: 226 more turn-button clips (356 in all, 5.9 MB in `sounds/`), all CC0 from OpenGameArt, found with the user's keywords (funny, silly, dumb, scary, gross, sexy, mature, adult): monsters, demon voice lines ("Feeble humans"), evil laughs, screams, zombies, ghosts, burps, splats, slime, sneezes, chants. OpenGameArt had nothing CC0 for sexy/adult. Big packs were sampled (a few of each), long clips cut to their first 5 s. `TURN_SOUNDS` was every file in `sounds/` (since v1.15 `make_list.py` writes `TURN_POOLS` instead).
- v1.6: **no deck picking for now; random backgrounds.** The user wants deck selection saved for later, so it's switched off, not deleted: `SHOW_DECKS = false` hides the menu's deck list (`#colorField`) and the seats' mana symbols; set it to true to bring both back. Each player's background (`state.bgs`, by edge, synced as `bgs/<edge>`, `bgOf()`) is dealt at random from `ARTS`, every commander art in `art/`: the five Starter decks plus `le`, Living Energy (Aetherdrift Commander, face commander Saheeli, Radiant Creator, Scryfall `drc/3`; `.k-le` seat colors). No two players share one. New game deals them again (`reroll()`, only for the players on this board), and so do changing Sitting out or the 1v1 ×2 pairs. A table from before v1.6 has no `bgs`, so the first new phone to see it sends its own. Attacker chips and Results swatches show the background; the log records `colors` as the background key and `deck` as '' (Results then shows no deck name).
- v1.5: **Sitting out** (menu, 3 players only): pick who sits out (`state.sitout`, synced as `sitout`, default Lenn as before); `PEOPLE[3]` is a getter that returns everyone else in edge order. Changing it starts the 3-player game over (logged first), two taps once it has begun, like the 1v1 ×2 pairs. Why: the user typed "Lenn" into Andrew's name box to play Lenn instead, and `badName()` silently reverted it. Now typing the sitting-out player's name into a box swaps them in (before the game has begun) or shows a note pointing to Sitting out (`#nameNote`); any other player's name still reverts, with a note. Older phones ignore `sitout` and keep showing Rand, Andrew, Trent.
- v1.4: louder. Every sound (clips and synth) goes through `out`: a 4× gain (+12 dB), a limiter (DynamicsCompressor, threshold −6 dB, ratio 20) and a tanh soft clipper, so peaks stay at full scale. Measured 6 to 11 dB louder (RMS) on the clips. To change the loudness, change `out.gain.value`.
- v1.3: **the turn tracker is gone** (the user asked for "just a turn button, not turn tracking"). One big gold button (`.turn-big`, the tap symbol) sits in the middle of the table, with the menu button beside it on the right; on a 4-player Table board both sit on the line above the bottom seat (`placeTurn()`), since the side seats' totals fill the middle, and in "Solo" it sits at the bottom. Tapping it plays a random goofy clip (`turnSound()`): 130 CC0 clips from OpenGameArt in `sounds/` (5 s max, mono MP3, 1.5 MB, credits in `sounds/CREDITS.md`), dealt from a shuffled bag so none repeats until all have played, the next 4 fetched ahead, a new tap cutting off the last. It plays on this phone only. Nothing sets `turns/` any more; the spotlight is always this phone's player, Pick who goes first only shows the "Goes first" badge, and the log's turn counts stay 0 (Results hides them). `turns/` and `clock/` stay in the synced paths for older phones, but nothing shows them. Menu → Sound is now All / Turn only / Off (`state.sound`; v1.2's true/false map to All/Off).
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
  default), **Table** (seats on the phone's edges), **Quadrants** (v3.34, 4 players only) or **Big button** (v1.22, 4 players only).
  `layoutOf()` picks the one actually used: Quadrants at 3 players falls back to Spotlight, and a
  Center phone or 1v1 ×2 can't use Spotlight, so they get Table.
  - Spotlight (`.board.spot`, seats `sp-main`, `sp-1`..`sp-3`): whoever has the turn takes the bottom
    half (v3.36; v3.35 had it on top), the others share the top in turn order after them, all upright. Before anyone has the
    turn, this phone's player is in it (`spotPlayer()`). When the turn moves, `paintTurn()` rebuilds
    the board. `fitLife()` and `fitNames()` size the big seat apart from the rest (`groupBy()`), and
    the bottom row's names leave room for the spotlight player's name, so they keep one size as
    turns pass.
  - Big button (v1.22, `.board.n4.hub`): Table with a huge turn button over the middle, see v1.23.
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
- **Turn tracker** (removed in v1.3, see above; kept here as history) (v3.8; 33% bigger in v3.10): a button at the bottom center of every seat (not in "Solo").
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
  plain ASCII (plus Matrix's minus; since v1.47 MPlantin also covers the checked non-ASCII characters), because their other symbols are blank or wrongly mapped
  (×, ·, … fall back to Georgia). `Matrix-Bold.woff` has patched line metrics: the original's
  positive descent made the line box half height and clipped the names.
- Life totals and names are white with a black outline; names are large (v3.13: up to 34px, 13% of the seat's height). Since v3.18 a name that's too wide for
  its seat shrinks to fit (`fitNames()`, via `--fit`), so every name shows in full on one line. Since
  v3.24 every name on the board is drawn at one shared size, the largest at which all of them fit;
  an "out" line too wide for its seat shrinks on its own (`--wfit`).
  The dagger has a black outline, no ring, and sits in the seat's bottom-right corner as its player sees it.
  Since v3.38 the deck's mana symbols sit in the bottom-left corner (`.seat-mana`, from `manaOf()`;
  not in "Solo"); taps pass through them, and side by side they sit above the concede flag.
- **Concede** (removed in v1.53; was in the menu under Pick who goes first): only this phone's seat, two taps to confirm.
  It became Rejoin. A new game clears all concessions.
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
- Version shows in the menu footer (since v1.53 without the sync status, except "offline"). Bump `VERSION` on every release.

### `xenagos.html`: Xenagos, the Party Hugger card carousel
- Live at https://biglob.github.io/commander-life/xenagos.html (since it landed on `main`). A standalone copy of the claude.ai artifact; republish both when it changes. Not a game page; nothing here syncs.
- Card images are embedded as WebP data URIs (about 11 MB), so the page works offline. Bench, Trash and Fav marks are kept in that browser's localStorage only.
- Tabs: Deck, Suggested, Fav, Bench, Trash. Sort & filter covers type, color, cost, keyword and Fav only.

### `xenagos-to-buy.html`: Xenagos cards still to buy
- Live at https://biglob.github.io/commander-life/xenagos-to-buy.html. The deck carousel cut to the cards we don't own yet: 16 spells, 16 nonbasic lands and 18 basics (50 cards, about $161 at the cheapest paper printings, Nov 10, 2026). The other 50 spells came from 19 TCGplayer orders placed Oct 28, 2026, all received by Nov 10. Built by `python3 tools/carousel/xenagos_buy.py` (lists in the script, `template.html`, back link to `xenagos.html`); when cards arrive, take them out of the script's lists and rebuild.
- **Printable copy**: `xenagos-to-buy-print.html` and `xenagos-to-buy.pdf`, one US Letter page with a checkbox per card (spells by mana value, nonbasic lands in two columns, basics, total). Built by `python3 tools/carousel/xenagos_print.py` from the carousel's data (rebuild the carousel first); the PDF is printed from that page with Playwright (`page.pdf({format: 'Letter', preferCSSPageSize: true})`). Check it stays one page after changes.
- **Proxies**: `xenagos-proxies.html` and `xenagos-proxies.pdf` (about 5 MB), the 32 non-basic cards still to buy as print-and-cut proxies, 9 per Letter page at 2.5 × 3.5 in with grey cut lines, Scryfall's large scans. Built by `python3 tools/carousel/xenagos_proxies.py`; the PDF is printed with Playwright through the proxy (images load from Scryfall's CDN), Letter, no margins. Print at 100% (Actual size), not Fit to page.

### `xenagos-tokens.pdf`: Xenagos tokens to print
- `xenagos-tokens.html` and `xenagos-tokens.pdf` (live at https://biglob.github.io/commander-life/xenagos-tokens.pdf): the Xenagos deck's tokens as **double-sided** cards for clear sleeves (the user's ask), 14 cards on 2 Letter sheets, 4 PDF pages alternating front and back; each back page is mirrored left to right so it lines up when printed on both sides, flip on long edge, at 100%. 9 per sheet at 2.5 × 3.5 in, Scryfall's large scans. The user's counts (a die covers big stacks): Eldrazi Spawn 5, Plant 5, Copy 9, Elephant 3, Lightning Rager 2 (only one is out at a time; the second is for Strionic Resonator), Beast 1, deathtouch Wurm 1, lifelink Wurm 1, Garruk emblem 1. Pairs: Spawn/Plant ×5, and Copy on the back of everything else; tokens that arrive together (the two Wurms, the three Elephants) sit on separate cards. Each token comes from one card (Copy from two: Dual Nature, Blade of Selves), so faces only clash when both their cards are out. Built by `python3 tools/carousel/xenagos_tokens.py`; PDF printed with Playwright through the proxy, Letter, no margins.

### `decks/`: precon card carousels
- Live at https://biglob.github.io/commander-life/decks/ (`decks/index.html`), one page per deck (`decks/<slug>.html`): the 14 precons in the "Decks we own" table of `buying-guide.md`. Not a game page; nothing syncs.
- Same carousel as Xenagos, minus Suggested (the user dropped it): Deck, Fav, Bench and Trash tabs, sort and filter, zoom, picks code. Marks are kept per deck in localStorage (`pc-<slug>-favs`, `pc-<slug>-marks`). The commander comes first, then the alternate commander (labelled), then spells by mana value, lands, basics.
- Built by `python3 tools/carousel/make.py [slug ...]` from `tools/carousel/template.html` and `index-template.html`. Decklists come from MTGJSON's deck files (exact printings) or, for decks MTGJSON doesn't have yet (Star Trek), Wizards' decklist article. Card data, prices (the precon printing's, else the cheapest paper printing) and image links come from Scryfall; images load from Scryfall's CDN, so the pages are small but need a connection. Brand-new cards with no price yet show "no price". `decks/decks.json` holds each deck's summary for the index.
- To add a deck, add a row to `DECKS` in `make.py` and run it for that slug, then add the deck to `links.html` (and its count), and rerun `tools/carousel/lands.py` so the lands Ours tab and primer include it.
- The claude.ai artifact copy of the Borg page is https://claude.ai/artifact/2iDTXny6HTaVnm5k5pwcZH (private). Artifacts can't load outside images, so `tools/carousel/embed.py <page> <out>` inlines them as WebP (about 6 MB) before publishing.

### `decks/tokens.html`: tokens in our decks
- Live at https://biglob.github.io/commander-life/decks/tokens.html. Every token each deck we own makes (the 14 in `make.py`'s `DECKS`, Archenemy: Nicol Bolas with its 20 schemes, and the Xenagos group hug deck, read from `xenagos.html`'s Deck tab, so rerun after the Xenagos list changes), with stats and the cards that make it; under each deck its copy effects (embalm, eternalize, encore, squad, replicate, populate, "token that's a copy"), emblems, and Monarch or energy. A fold-out lists tokens shared by more than one deck. Not a game page; nothing syncs.
- Built by `python3 tools/carousel/tokens.py` from `tools/carousel/tokens-template.html` (`TOKENS_CACHE=<file>` reuses the download). Tokens come from Scryfall's `all_parts`; every card mentioning a token was read by hand in Nov 2026 and the fixes are in the script (`FIX_COLORS`: Scryfall's Tribble token is colorless, the cards say white; `WHO`: tokens that go to another player). Rerun it after adding a deck to `make.py`, and read any new token-making card it lists.

### `cuts/`: most-cut cards per precon
- Live at https://biglob.github.io/commander-life/cuts/ (`cuts/index.html`), one carousel per deck we own (`cuts/<slug>.html`): the 15 cards players most often take out of that precon, each with "#N most cut · cut from X% of N decks" and links to EDHREC and the card. Not a game page; nothing syncs. Marks are kept apart from the deck pages' (`pc-cuts-<slug>-`).
- Source: EDHREC's precon page (json.edhrec.com/pages/precon/<slug>.json; the Borg is `we-are-the-borg`), its "Cards to Cut" and "Lands to Cut" lists merged and sorted by `unpopularity` (the share of decks EDHREC matched to the precon with its face commander that cut the card). Alt-commander builds are counted separately by EDHREC and left out. The fold-out on each page cites the source, the date and the sample size, and flags Star Trek (built before release) and samples under 300 decks.
- Built by `python3 tools/carousel/cuts.py [slug ...]` from `tools/carousel/cuts-template.html` (the brew template with a cut line under each card); card data comes from `decks/<slug>.html`, so run `make.py` first for a new deck. Rerun it now and then (Star Trek's numbers will move after release); a new deck in `make.py`'s `DECKS` gets picked up automatically.

### `lands/`: nonbasic lands carousel and primer
- Live at https://biglob.github.io/commander-life/lands/ (carousel) and `lands/primer.html` (the primer: an exec-summary brief on land cycles, most played, prices, how to build a mana base, and the cheapest untapped-dual fixes for each of our decks; written by hand, so update its numbers when decks are added). Not game pages; nothing syncs.
- The carousel holds every Commander-legal nonbasic land (1,227 in Nov 2026, plus this year's unreleased ones such as the Star Trek planets), grouped because the user found 1,227 cards too many: the Types tab shows one card per category (40, most played first) with its one-line description, price range and a chip per color combo it comes in (tap a chip to see that land). "See all" opens a category as one card per cycle (lands whose rules text matches once names, colors, basic types and creature types are blanked: `cycle()` in `lands.py`), each with a chip per land. Single-cycle categories (shocks, fetches) have no "See all". Ours (lands in our precons) and Fav tabs, and a name search, list single lands. Filters: name, colors, price; sorts: most played, land family, price, name. Favorites in localStorage (`pc-lands-favs`); no Bench or Trash.
- Built by `python3 tools/carousel/lands.py` from `tools/carousel/lands-template.html` (a copy of the deck carousel with land filters). `cat()` puts each land in one of 40 categories by its type line and rules text (order matters); `FAMILIES` groups them and `DESC` holds each category's one-liner. `LANDS_CACHE=<file>` reuses the Scryfall download while working on the page. Price is the cheapest paper printing. It also writes `lands/summary.json` (per category: count, median price, most played) for the primer. Rerun it after adding a deck so the Ours tab picks it up.

### `rodents/`: rodent cards carousel
- Live at https://biglob.github.io/commander-life/rodents/. Every Magic card (673 in Nov 2026; Arena/MTGO-only ones included and labelled "Arena only"; no tokens, the user dropped them, nor Alchemy Bounty/Event cards) with a rodent in its creature type (Rat, Mouse, Squirrel, Hamster, Beaver, Porcupine, Capybara), name, rules text, flavor text (any printing) or art (Scryfall Tagger art tags: `art:rat`, `art:mouse`, `art:squirrel` and the rarer ones). Rabbits, hedgehogs, moles, shrews and otters aren't rodents and are left out. Not a game page; nothing syncs.
- Tabs All, Rats, Mice, Squirrels, Other, Fav; filters for where it was found (type, name, text, flavor, art, art only), card type, Legendary (any, only, none), Printed (paper only hides the Arena-only cards), colors, price. Sorts: most played, card type (front face's main type, creature first, then by popularity), newest, oldest, price, name. A card found by its art shows a rodent printing, with a chip per other rodent illustration. Price is the cheapest matching paper printing. Favorites in localStorage (`pc-rodents-favs`).
- **`rodents/legends.html`** (live at https://biglob.github.io/commander-life/rodents/legends.html): the same data cut to Commander-legal legendary creatures only (68 in Nov 2026; 84 before the user asked for legal only), for picking a commander. Default order puts rodents by creature type first, then ones with a rodent in name or rules text, then art or flavor only, each by popularity (`rel()`). Card type and Legendary filters are hidden there (`data-all`, `PAGE.legends`). Both pages link to each other and share favorites. Both have Printed → Commander-legal (`l`); on the main page, cards that aren't legal show a red "Not Commander-legal" chip (Un-cards, playtest cards, Arena-only).
- Compact top (the user: the top took half the phone): one-line summary, tabs on one scrolling row. Cards are sized by measuring (`fit()` runs after each render: the tallest caption's height, then the image fits what's left; 150px minimum, below which the rail scrolls down).
- Built by `python3 tools/carousel/rodents.py` (writes both pages) from `tools/carousel/rodents-template.html` (`RODENTS_CACHE=<file>` reuses the download). Scryfall times out on one long regex, so each field is searched in three chunks (`CHUNKS`). Rerun it to pick up new sets and newly tagged art.

### `brews/`: brewed decks with a reason per card
- `brews/chatterfang.html` (live at https://biglob.github.io/commander-life/brews/chatterfang.html): Chatterfang, Squirrel General, 100 cards, about $300 in singles. The user asked for sources cited for why every card was chosen.
- `brews/marrow-gnawer.html` (Marrow-Gnawer, mono-black Rats, 17 Rat Colony, about $470) and `brews/vren.html` (Vren, the Relentless, blue-black: edicts and wipes exile opponents' creatures into Rats, about $290). The user asked for a rat brew like Chatterfang's and picked both. Same build; roles gained Rat (Rat bodies), Recursion and Counter. Each `BREWS` entry has `colors` for the synergy line ("other mono-black decks").
- `brews/chatterfang-lenn.html` (live at https://biglob.github.io/commander-life/brews/chatterfang-lenn.html): **Lenn's Chatterfang Tokens**, a gift deck for Lenn, who likes token builds. Hand-picked, not EDHREC's average (`LENN` in `brew.py`, `pick` in its `BREWS` entry: the list is the dict in order, basics counted in `pick`). **Bracket 3**: exactly three Game Changers (Gaea's Cradle, Demonic Tutor, Seedborn Muse) and no two-card infinite combo, checked with Commander Spellbook's `find-my-combos` and `estimate-bracket` API (backend.commanderspellbook.com, reachable from the sandbox). Pitiless Plunderer is out because with Chatterfang it loops by itself; Earthcraft (with Squirrel Nest) and Ivy Lane Denizen (with Scurry Oak) are out for the same reason. Camellia + Peregrin Took loops of three or four cards remain (allowed in Bracket 3). It will be proxied, so price didn't limit picks (about $2,900 in singles). Check both again after any change to the list.
- **Bracket 2 version**: `brews/chatterfang-lenn-b2.html`, the same list with four swaps (`LENN_B2_SWAPS`, card for card: Gaea's Cradle → Golgari Rot Farm, Demonic Tutor → Sylvan Library, Seedborn Muse → Drey Keeper, Peregrin Took → Bastion of Remembrance). No Game Changers and no infinite combos of any size (Spellbook finds none). Both pages show the swap list and link `brews/chatterfang-lenn-proxies.txt` (every card both versions need, one of each, no basics; the user is proxying both at once), all written by `python3 tools/carousel/brew.py chatterfang-lenn chatterfang-lenn-b2`.
- `brews/camellia-lenn.html` (live at https://biglob.github.io/commander-life/brews/camellia-lenn.html): **Lenn's Camellia Squirrels**, Bracket 2, the replacement for Lenn's Chatterfang after r/mtg's review (Chatterfang plays far above a table of new players on precons; the user picked Camellia, the Seedmiser). The user's rule: **almost every card makes Squirrels**, anything else needs a good reason. Camellia turns each Food sacrificed into a Squirrel, so roles are Squirrel maker, Food maker, Food eater, Squirrel payoff; the rest (Sol Ring, Heroic Intervention, lands) say why. Roles can be `'A/B'` (filter role, second job). Unlike the other brews this page shows each card's reason (`show_why`, field `w`). Left out on purpose: Chatterfang, Peregrin Took and Tippy-Toe (Tippy-Toe + Ninja Pizza + Camellia is infinite), doublers, Craterhoof, fetches. Spellbook: no combos, no Game Changers. About $200 in singles. `brews/camellia-lenn-moxfield.txt` and `brews/chatterfang-lenn-b2-moxfield.txt` are Moxfield import lists (for Reddit reviews), written by `brew.py`.
- The list is EDHREC's average deck for the commander (json.edhrec.com/pages/average-decks/<slug>.json, reachable from the sandbox; Moxfield's API is blocked). Under each card, one line: its role (Token maker, Token doubler, Payoff, Drain, Sac outlet, Draw, Ramp, Tutor, Removal, Protection, Land), then EDHREC's numbers from the commander page (share of the commander's decks that play it, and synergy) with links to EDHREC and the card's Scryfall page. A "Sources and how cards were chosen" fold-out explains it. The user cut the per-card reason sentence; the hand-written reasons stay in `brew.py` as notes (only the role is shown). The Role filter is the template's Keyword filter (roles go in `k`); sorts add Most played and Synergy.
- Built by `python3 tools/carousel/brew.py [slug]` from `tools/carousel/brew-template.html` (a copy of the deck template). Roles and reasons live in the script (`CHATTERFANG`, `MARROW`, `VREN`); it stops if EDHREC's average deck has a card with none, so add one when EDHREC's list shifts. To add a brew: a reasons dict and a `BREWS` entry, then a row in `links.html`.

### Every other page in the app
- Every page but `index.html` and `archenemy.html` links `app/manifest.json` and, when opened inside the installed app (display-mode fullscreen/standalone), shows a gold **🃏 Board** button bottom-left back to the board (snippet marked `app-board-link`, right after `<title>`, also in every template under `tools/`). Why: the app has no address bar, and the deck pages had no way back; installing from a deck page without a manifest also made the icon open that page. New pages need the same snippet.

### `furniture/stools.html`: bar-height chairs for the game/kitchen table
- Live at https://biglob.github.io/commander-life/furniture/stools.html. 13 chair-like, mid-century bar-height seats (the user found the first version's picks "too stoolish" and wants bar-height chairs: tall padded backs, most with arms), for a 4×4 ft bar-height table that's also the kitchen table: 3 chairs plus a backless bench. 7 mid tier (up to $720), 6 "Step up" ($749 to $900). Each card: price each and ×3, seat height, back height above the seat, width, wipe-clean, arms, comfort out of 5 (from the specs) and a store link. Tabs All, Mid tier, Arms, Wipe-clean, Fav (localStorage `stools-favs`).
- Data written by hand into the page from each store's Shopify feed (`/products.json`) and product-page specs, Nov 10, 2026: TOV, Modway, Blu Dot, Sunpan and 2Modern (which carries Four Hands, Urbia, Eichholtz). Images hotlink Shopify's CDN. Wayfair, AllModern, West Elm, Pottery Barn, Crate & Barrel and CB2 return 403/429 to the sandbox.

### `links.html`: all our pages
- Live at https://biglob.github.io/commander-life/links.html, the 🗂️ footer link. Hand-kept list in sections: Play, Card carousels (with every deck, each with small mana symbols for its colors, `<symbol>`s from `index.html`'s `MANA`), Guides, Sounds, claude.ai artifacts. The user cut the Chatterfang brews (all of Lenn's Chatterfang rows too), Marrow-Gnawer, Vren, the Xenagos buy list, print list and proxies, the bar-height chairs and the two old preview artifacts from the list; their pages are still on the site.

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
| `tables/t7q2xm4k` | Commander Life live table (Archenemy mode too, since v1.25: `ae`, `schemes`, `scheme`, `games/6`) |
| `tables/t7q2xm4k-ae` | the old `archenemy.html` page's live table |
| `tables/t7q2xm4k-results/<gameId>` | Commander Life game log |

The REST API is used directly: an EventSource stream comes in, and PATCH writes go out with
server-side increments so taps on two phones both count.

The database rules only open `tables/` to the pages. v3.2 to v3.4 kept the log under `results/`, and
the log failed with "Couldn't reach the shared log", so keep every new node under `tables/`.

## Code conventions (both pages)
- Anything new we build or gather gets a row in `links.html` (see "Keep `links.html` current").
- Single file, inline CSS and JS, and comments that explain why.
- Every synced path must be in `allPaths()` and checked in `validValue()`.
- A new synced field must tolerate older phones that don't send it (see the `conceded` and `meta`
  handling in `adopt()`).
- Destructive actions take two taps (New game, Concede, Delete a result, changing the archenemy).
- Commit messages: `vX.Y: <what changed, in plain words>`.

## Decisions so far
- Poison was dropped on purpose.
- 3v1 didn't belong in Commander Life (v2.9's 3v1 mode was reverted), but in v1.25 the user asked for Archenemy built in, and it is now a Players option. `archenemy.html` is the older separate page.
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
