# Brief: writing the rules for "top 15 adds" (for Opus)

Goal: turn the two methods we have used into written rules anyone can rerun, then add a weight that favours **on-theme** cards over meta staples. The user's priority is theme, not popularity. Silverquill picks are paused; Silverquill (Killian, Decisive Mentor, "all-in Auras") is only the worked example.

## Method A: the original (sources first), how the 15 in `tools/carousel/angles.py` `PICKS` were chosen
1. The user picks one direction per deck (Silverquill: all-in Auras). Direction is a human choice, never computed.
2. Gather written and filmed sources for that deck: EDHREC precon and commander theme pages, the Command Zone's 10-in/10-out lists (Archidekt account `GameKnights`), creators' Archidekt/Moxfield lists, store and guide articles (Draftsim, Card Kingdom, CoolStuffInc, MTGGoldfish and others), and upgrade/how-to-play videos read from their transcripts. The user wants sources, not Claude's own memory.
3. Match cards source by source. Guide pages are read card by card; videos by transcript; lists by exact cuts. Each add is recorded with the source keys that add it (`gf-sq`, `ds-sq`, `cz738`...). Box cards are never picks.
4. Take 15 cards that fit the chosen direction, each backed by at least one source key. A card with no key is allowed only as "EDHREC only" and says so.
5. EDHREC's add share is fetched live and shown beside each pick; it informs but does not choose.
6. Commander legality and Game Changer flags come from Scryfall.
Known gap: the script records the result and sources but not an explicit scoring rule for choosing among candidates. Opus should read the `PICKS` comments and the angle prose, then state the rule as it was actually applied (apparently: fits the direction, most sources agree, enchantment/Aura-engine cards ahead of generic staples), and flag anything that was judgement.

## Method B: the chain (data first), built Nov 17, 2026 (`tools/carousel/chain.py`, `decks/chain.html`)
Data: Archidekt decks for the commander (`/api/decks/v3/?commanderName=...&page=N`, then `/api/decks/<id>/`), 818 distinct after dropping decks with other card counts and exact duplicates; Scryfall `cards/collection` for type, legality, Game Changer flag.
1. Candidate cards are those the precon lacks; drop basics, lands, and anything not Commander-legal.
2. Start set = decks with the theme (Silverquill: 10 or more added enchantments, 513 decks), or all decks.
3. Step 1 = card in the most start-set decks. Step 2 = most common among decks that also have step 1, and so on (greedy conditional counting). Show 8 runner-ups per step.
4. Stop when fewer than 50 decks remain (about +/-14 points at 95%); the chain ended at step 7 (66 decks).
5. Take the first 5 steps whose share is at least 60% as **core**, then fill to 15 by ranking the rest by share among the decks that have all the core (n = 131, about +/-9 points).
6. Caveats to write into the rules: decks are not independent (copies and tweaks), many comparisons, early step order is mostly noise (cards within about 5 points are ties), popularity is not quality. EDHREC cannot do conditional "decks with A also play B", hence Archidekt.
Result vs Method A on Silverquill: 10 of 15 matched; data-only adds were Kaya's Ghostform, Sphere of Safety, Spirit Link, Spellbook Vendor, Swords to Plowshares (Swords has EDHREC synergy -0.25: a meta staple, not a theme card).

## Task 3: add a weight toward staying on theme
Problem: pure popularity pulls in staples (Swords, Sol Ring, signets). Proposed scoring; Opus should test, tune and write it as rules:
- **Theme fit T (0 to 3)**, set per commander from its oracle text. Silverquill/Killian rewards enchantments entering and Aura-enchanted attackers, so: 3 = engine (makes enchantments each turn, or pays off enchantment count/Auras attacking); 2 = on-theme piece (an enchantment, especially a cheap Aura or Role); 1 = supports the plan (protection, goad, draw for the strategy); 0 = generic staple (removal, ramp, rocks).
- **Automatic theme proxy**: EDHREC `synergy` (share in this commander's decks minus share in all decks of the colours). Negative or near zero means meta, not theme.
- **Score** = 0.5 x T/3 + 0.25 x conditional share (Method B) + 0.25 x normalised synergy; add 0.1 per independent source key from Method A (cap 0.3). Weights are a starting point to tune against the Silverquill list.
- **Quotas**: at least 11 of 15 with T >= 2; at most 3 with T = 1; at most 1 with T = 0 (the user wants a theme list). Drop any card with T = 0 and synergy <= 0 unless the user asks for utility.
- Tie rule: within the margin of error (the conditional share +/- 1/sqrt(n)), prefer higher T, then more sources, then lower mana value.
- Lands: handled separately (the chain excluded them; Hall of Heliod's Generosity is a land and plays in 31% of Killian decks); say whether lands may fill slots.
- Always call out cards that are not Commander-legal; default to legal only.

## Deliverable
A rules document (plain steps, inputs, outputs, formulas, caveats) covering Method A, Method B and the weighted blend, plus a check: run the blend on Silverquill and report which of our 15 and the chain's 15 it keeps. Do not change the Silverquill picks. If new pages result, add rows to `links.html`.
