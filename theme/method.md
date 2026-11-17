# Theme picks: how we choose 15 in and 15 out for a precon

Goal: swap 15 cards into each precon so it plays its chosen theme better, staying in Bracket 3. Theme and synergy
come first. Power is allowed when it arrives naturally (sources or data bring it), but it is never a reason to rank a
card higher. Every number on a page comes from a rerunnable script: `tools/carousel/theme_picks.py`.

Replaces the earlier methods brief (`pick-methods-brief.md`), whose weighted blend mixed a hand-graded theme score
with shares on different scales and then tuned it against our own picks.

## Inputs (per deck)

1. **Direction**: chosen by the user, never computed (Silverquill: all-in Auras).
2. **Theme tests**: written from the direction and the commander's rules text, kept in `THEMES` in the script, and
   approved by the user once. Each test is a regex over Scryfall's rules text and/or type line, with a role:
   - **engine**: pays off or multiplies the theme (enchantress triggers, cost reducers, "for each enchantment you control");
   - **piece**: the theme's fuel (any Aura, Role and enchantment-token makers);
   - **support**: helps the theme run (enchantment recursion and tutors, attach effects, other enchantments, since
     each one still triggers Killian);
   - **off**: passes no test (removal, ramp, staples).
   A card takes the first test it passes. The tests make "on theme" checkable, not Claude's opinion.
3. **Data**:
   - Archidekt: every public deck with the commander (`tools/carousel/archidekt.py`), 98 to 102 cards, exact
     duplicates dropped.
   - EDHREC: the commander's theme page for the direction (`/commanders/<slug>/<theme>`) and the precon page (cut shares).
   - Scryfall: every Commander-legal paper card in the colors (text, type, Game Changer flag, price).
4. **Written sources**: the guides and lists for the deck (the same ones `decks/angles.html` cites). Each article is
   read for card names; a card the article names that isn't in the box counts as that source adding it. Videos and
   Moxfield lists can't be read from the cloud sandbox (YouTube and Moxfield refuse it), so they count only when a run
   is made from the desktop app, which can read transcripts.

## Steps

1. **Candidates**: every card in the colors that isn't in the box, is Commander-legal (Scryfall
   `legalities.commander`) and isn't a basic land. Not-legal cards never appear.
2. **Decks built this way**: the third of Archidekt's decks with the most engine and piece cards. This is the data
   version of "what do people who build this direction play". The other two thirds are the comparison.
3. **Evidence, kept apart and shown on every card:**
   - A = share of decks built this way that play the card;
   - B = share of EDHREC's theme decks that play it (0 if EDHREC doesn't list it);
   - S = how many written sources add it;
   - lift = A divided by the card's share in the other decks (above 1 means it's specific to this direction).
4. **Rank**: on-theme cards (engine, piece, support) by (A + B) / 2 + 0.03 × S. Each source counts as 3 points of
   share, so a card well ahead in the data stays ahead, and sources settle near-ties.
5. **Off-theme cards** are allowed but never sought: one gets a slot only if A is at least the 15th on-theme card's A
   and two or more sources add it.
6. **Bracket 3**:
   - at most 3 Game Changers in the finished 100, the box's included; a fourth is skipped for the next option;
   - Commander Spellbook (`find-my-combos`, `estimate-bracket`) runs on the finished 100. An add that completes a
     two-card infinite, or brings mass land denial or extra turns, is dropped and the list rebuilt. Longer combos are
     allowed (Bracket 3).
7. **Cuts**: box cards that aren't engine or piece cards (and never the commander), ranked by the mean of (share of
   decks built this way that leave the card out) and EDHREC's cut share. For each land added, a land is cut instead of
   a spell, so the land count holds.
8. **More options**: the next 12 cards for each role and 10 more cuts are shown under the 15, in the same order, so
   the user can swap any pick by hand.

## Caveats

- Archidekt decks aren't independent (copies and small tweaks of the same list), so shares within a few points are ties.
- "Built this way" depends on the theme tests; a test that's too wide (every enchantment) would pull in decks that
  aren't really doing the direction.
- Name-matching articles counts a card the guide only mentions; a guide that says "don't play X" would still count
  as adding X. One-word names (6+ letters, never used as an ordinary word in that article) are checked to cut
  menu words and split-card halves.
- Popularity isn't quality. The theme tests and lift are what keep staples out, not the shares.
- Our earlier picks (`PICKS` in `angles.py`) are never an input, so the two lists can be compared.

## Rerun

```
python3 tools/carousel/archidekt.py "Killian, Decisive Mentor" <cache>/decks.json
python3 tools/carousel/theme_picks.py silverquill-influence <cache>
```

A new deck needs a `THEMES` entry (commander, color identity, direction, EDHREC theme slug, tests, sources), the
user's sign-off on its tests, and a row in `links.html`.
