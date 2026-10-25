# Commander Life: project notes

Life counters for a Magic: The Gathering Commander group, played on everyone's phones and kept in
sync live. Plain HTML pages, no build step, no framework.

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
2. Copy `index.html`, `archenemy.html` and `patterns/` into this repo, commit, push to `main`.
3. GitHub Pages republishes in a minute or two. Phones may need a reload.

The cloud sandbox can't reach firebaseio.com or github.io (the proxy returns 403), so test in
Playwright with the network mocked (route `firebaseio` requests, replace `EventSource`).
After a deploy, ask the user to check the version in the menu footer.

## Pages

### `index.html`: Commander Life (current v3.3)
- 1 to 4 players. Seats sit on the phone's edges, clockwise from the bottom: edge 0 bottom, 1 left,
  2 top, 3 right. Default names are Rand, Andrew, Trent, Lenn.
- **This phone is**: each phone picks its owner (kept on that phone only).
  - A named player: their seat goes at the bottom and every seat faces them, upright.
    At 4 players the tall side seats use top half = +, bottom half = −.
  - **Center**: the phone lies in the middle of the table and each seat faces its own edge.
    Center has no seat of its own, so its colors and Concede are hidden.
- Tap a side for ±1, hold for ±10. Commander damage: the dagger button opens the attacker chips;
  while one is marked, life lost also counts as their commander damage. 21 from one commander is lethal.
- Each player picks a two-color pair and one of 50 pattern masks (`patterns/*.png`) for their seat.
- Life totals and names have a black outline; names are large, and long ones end in an ellipsis.
  The dagger has a black outline, no ring, and sits in the seat's bottom-right corner as its player sees it.
- **Concede** (menu, under Pick who goes first): only this phone's seat, two taps to confirm.
  It becomes Rejoin. A new game clears all concessions.
- **Game log** (v3.2): tapping New game quietly logs the game before it, but only if:
  - the table had 2 to 4 players,
  - exactly one player was still alive,
  - and at least 15 minutes passed since its first change.

  The log saves the date, how long the game took, the winner, and each player's name, color pair,
  pattern and final life. Results are listed in the menu with a two-tap Delete.
- Version shows in the menu footer with the sync status. Bump `VERSION` on every release.

### `archenemy.html`: Archenemy (v1.1)
- Separate page, because its interface differs a lot from Commander Life.
- Rules:
  - One archenemy at 40 life against three heroes at 20 each, with no shared total.
  - The archenemy goes first.
  - Heroes take commander damage only from the archenemy; the archenemy takes it from each hero.
- Scheme deck: 102 schemes with full card text, Set in Motion, ongoing schemes, Abandon, and Undo.
- Same seat styling as Commander Life: large outlined names, and the dagger in each seat's
  bottom-right corner (v1.1).
- Built in the "Archenemy page development" chat, branch `ccr-b9949e35-ihpa80` of `BigLob/Mtg`
  (v1.0). From v1.1 on it lives with Commander Life on `ccr-d009fee8-fnaynu`.

## Firebase layout

| Path | Used by |
| --- | --- |
| `tables/t7q2xm4k` | Commander Life live table |
| `tables/t7q2xm4k-ae` | Archenemy live table |
| `results/t7q2xm4k/<gameId>` | Commander Life game log |

The REST API is used directly: an EventSource stream comes in, and PATCH writes go out with
server-side increments so taps on two phones both count.

**Unverified:** whether the database rules allow writes to `results/`. If the Results list says
"this phone only", the rules need to allow `results` the same way as `tables`.

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
- Seat colors are what the game log records as each player's "color combo".

## Branches in `BigLob/Mtg` (history, oldest to newest)
- `claude/mtg-commander-health-counter-m75zne`, `ccr-31ae3957-dadntz`, `ccr-b66a7c9b-cywcix`:
  early versions (`ccr-b66a7c9b-cywcix` is an abandoned side branch).
- `ccr-67e82241-afli68`: v1.0 to v2.7.
- `ccr-d009fee8-fnaynu`: Commander Life v2.8 to v3.3 and Archenemy v1.1, the latest source for both.
- `ccr-b9949e35-ihpa80`: `archenemy.html` v1.0 (branched from v2.8).

`BigLob/Mtg` has no `main`, so a new chat may start on an old branch. Start from the newest branch
above, or work here in `BigLob/commander-life`, where `main` is always what's live.
