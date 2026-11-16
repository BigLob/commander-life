"""Build decks/angles.html: for our four newer non-Starter, non-Star Trek, non-Final Fantasy precons, the directions
("angles") upgraders take each deck and what they steer clear of, from EDHREC's numbers plus upgrade videos and articles.

The angles, cuts and who-said-what are written by hand below from sources read Nov 16, 2026 (listed in SOURCES).
The numbers are fetched live: EDHREC's precon page (share of decks adding or cutting each card), the commander page's
theme counts, and Scryfall (Commander legality, Game Changer flag). So reruns refresh the numbers, not the prose.
Run from the repo root:  python3 tools/carousel/angles.py
"""
import datetime, html, json, os, re, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE)
from make import get, scryfall

V = 'https://www.youtube.com/watch?v='
A = 'https://archidekt.com/decks/'
SOURCES = {
 # Silverquill Influence
 'cz738': ('The Command Zone #738 (video)', V + 'W1-msyO9yQQ', 'Its 10 in, 10 out list, read from the show\'s own Archidekt account (GameKnights): ' + A + '21970344'),
 'gf-sq': ('MTGGoldfish, "Silverquill Influence Has An Upgrade Dilemma" (video + article)', 'https://www.mtggoldfish.com/articles/silverquill-influence-precon-upgrade', 'Video: ' + V + 'oF9xfCAVwg0'),
 'edh-sq': ('EDHREC upgrade guide, Andy Zupke, Apr 8 2026', 'https://edhrec.com/guides/silverquill-influence-precon-upgrade-guide', ''),
 'ds-sq': ('Draftsim upgrade guide, May 2026', 'https://draftsim.com/silverquill-influence-upgrade-guide/', ''),
 'lab-sq': ('EDHLAB, "Debate Prep" upgrade guide', 'https://blog.edhlab.gg/debate-prep-silverquill-influence-precon-upgrade-guide', ''),
 'fs-sq': ('Flipside Gaming, "Table for Four" budget upgrade', 'https://flipsidegaming.com/blogs/magic-blog/table-for-four-silverquill-influence-budget-upgrade-guide', ''),
 # Lorehold Spirit
 'cz735': ('The Command Zone #735 (video)', V + 'rNUv0ZWrJeE', 'Its 10 in, 10 out list, from the GameKnights Archidekt account: ' + A + '21533404'),
 'gf-ls': ('MTGGoldfish, "These Swaps Make Lorehold Spirit Absolutely Busted" (video + article)', 'https://www.mtggoldfish.com/articles/these-swaps-make-lorehold-spirit-absolutely-busted', 'Video: ' + V + 'lNsesVdLvFI'),
 'edh-ls': ('EDHREC upgrade guide, Andy Zupke, Apr 13 2026', 'https://edhrec.com/articles/lorehold-spirit-precon-upgrade/', ''),
 'ck-ls': ('Card Kingdom, $50 upgrade guide', 'https://blog.cardkingdom.com/secrets-of-strixhaven-lorehold-spirit-commander-deck-upgrade-guide/', ''),
 'ds-ls': ('Draftsim upgrade guide (20 in, 20 out)', 'https://draftsim.com/lorehold-spirit-upgrade-guide/', ''),
 'lab-ls': ('EDHLAB, "Reconstructing" upgrade guide', 'https://blog.edhlab.gg/reconstructing-white-red-lorehold-spirit-precon-upgrade-guide/', ''),
 # Living Energy
 'cz653': ('The Command Zone #653 (video)', V + 'km1f1W0Tl6k', 'Its 10 in, 10 out list, from the GameKnights Archidekt account: ' + A + '11021591'),
 'edh-le': ('EDHREC upgrade guide, Andy Zupke, Jan 29 2025', 'https://edhrec.com/articles/living-energy-precon-upgrade-guide-aetherdrift', ''),
 'ck-le': ('Card Kingdom, $50 upgrade', 'https://blog.cardkingdom.com/aetherdrift-living-energy-precon-upgrade/', ''),
 'ds-le': ('Draftsim upgrade guide', 'https://draftsim.com/living-energy-upgrade-guide/', ''),
 'gg-le': ('Gathering Games upgrade guide', 'https://gatheringgames.co.uk/community/blog/living-energy-precon-upgrade-guide-mtg-aetherdift-commander-decks', ''),
 # Eternal Might
 'cz654': ('The Command Zone #654 (video)', V + '8J9lOe-NhZg', 'Its 10 in, 10 out list plus a 2-card "combo upgrade", from the GameKnights Archidekt account: ' + A + '11039235'),
 'fw': ('Farwater MTG (YouTube), upgraded Temmet list', A + '11257428', 'The channel\'s Archidekt list (19 in, 19 out), 6,900 views. The channel\'s video: ' + V + 'S1p1_6RZjUE'),
 'ck-em': ('Card Kingdom, $30 upgrade guide', 'https://blog.cardkingdom.com/aetherdrift-eternal-might-precon-upgrade-guide/', ''),
 'ds-em': ('Draftsim, 15 upgrades, Mar 2026', 'https://draftsim.com/eternal-might-upgrade-guide/', ''),
 'csi-em': ('CoolStuffInc, $50 upgrade guide, Feb 2025', 'https://www.coolstuffinc.com/a/briansmith-seo-02122025-aetherdrifts-eternal-might-precon-upgrade-guide', ''),
 'br-em': ('EDHREC, "Bracketeering: Eternal Might", John Sherwood, Mar 17 2025', 'https://edhrec.com/articles/bracketeering-eternal-might', ''),
 # Starter decks
 'edh-ff': ('EDHREC upgrade guide, Scrap Trawlers, Dec 2 2022', 'https://edhrec.com/articles/first-flight-precon-upgrade-guide/', 'Their list on Archidekt: ' + A + '4465023'),
 'cgb-ff': ('Cardgamebase, First Flight upgrade guide', 'https://cardgamebase.com/?p=32232', ''),
 'cr-ff': ('Cards Realm, Upgrading First Flight', 'https://mtg.cardsrealm.com/en-gb/articles/upgrading-precon-commander-first-flight-isperia-supreme-judge', 'Its in/out lists are images that didn\'t load; only the cards named in the text are used.'),
 'edh-gd': ('EDHREC upgrade guide, Scrap Trawlers, Dec 2 2022', 'https://edhrec.com/articles/grave-danger-upgrade-guide/', 'Their list on Archidekt: ' + A + '4465276'),
 'cgb-gd': ('Cardgamebase, Grave Danger upgrade guide', 'https://cardgamebase.com/?p=32230', ''),
 'edh-ci': ('EDHREC upgrade guide, Scrap Trawlers, Dec 2 2022', 'https://edhrec.com/articles/chaos-incarnate-upgrade-guide', 'Their list on Archidekt: ' + A + '4467252'),
 'cr-ci': ('Cards Realm, Upgrading Chaos Incarnate', 'https://mtg.cardsrealm.com/en-ie/articles/upgrading-commander-precon-chaos-incarnate-kardur-doomscourge', 'Its in/out lists didn\'t load; only the cards named in the text are used.'),
 'edh-dd': ('EDHREC upgrade guide, Scrap Trawlers, Dec 2 2022', 'https://edhrec.com/articles/draconic-destruction-upgrade-guide/', 'Their list on Archidekt: ' + A + '4465326'),
 'cgb-dd': ('Cardgamebase, Draconic Destruction upgrade guide', 'https://cardgamebase.com/?p=32233', ''),
 'edh-tt': ('EDHREC upgrade guide, Scrap Trawlers, Dec 2 2022', 'https://edhrec.com/articles/token-triumph-upgrade-guide/', 'Their list on Archidekt: ' + A + '4469324'),
 'cgb-tt': ('Cardgamebase, Token Triumph upgrade guide', 'https://cardgamebase.com/?p=31874', ''),
}

DECKS = [
 {
  'group': 'Our newer precons',
  'slug': 'silverquill-influence', 'name': 'Silverquill Influence', 'cmd': 'Killian, Decisive Mentor', 'colors': 'W/B',
  'gist': 'Killian goads a creature whenever an enchantment of yours enters and draws when a creature you enchanted attacks. '
          'The box is half Auras, half politics ("don\'t attack me", gifts to opponents, Inklings). Almost every upgrader keeps the Auras and drops the gifts and Inklings; they split on whether to keep the defensive politics.',
  'themes': ['auras', 'enchantress', 'forced-combat', 'voltron', 'pillow-fort', 'politics'],
  'angles': [
   ('All-in Auras ("Aura storm")',
    'Cast several cheap Auras a turn: cantrip Auras keep the hand full, cost reducers and enchantress creatures turn each one into a card, and Killian goads with every one. The most common direction by far.',
    ['Mesa Enchantress', 'Light-Paws, Emperor\'s Voice', 'Danitha Capashen, Paragon', 'Feather of Flight', 'Angelic Gift', 'Rune of Mortality', 'Unquestioned Authority', 'Scourgemark', 'Hero of Iroas', 'Sigarda\'s Aid', 'Retether', 'Tempest Technique', 'Hall of Heliod\'s Generosity'],
    ['gf-sq', 'fs-sq', 'ds-sq', 'edh-sq', 'cz738'],
    'MTGGoldfish calls the one-mana draw Auras the "secret sauce". EDHREC\'s Auras theme (the biggest) plays Mesa Enchantress and Hall of Heliod\'s Generosity more than average.'),
   ('One huge evasive attacker (Voltron)',
    'Stack the scaling Auras on one flyer or on Killian and win through commander-style damage. Shares most cards with the Aura plan; the difference is the payoffs.',
    ['Ethereal Armor', 'All That Glitters', 'Mantle of the Ancients', 'Twinblade Blessing', 'Brilliant Wings', 'Open the Armory', 'Duelist\'s Heritage', 'Boon of the Spirit Realm', 'Rashel, Fist of Torm', 'Super State'],
    ['gf-sq', 'edh-sq', 'ds-sq', 'fs-sq'],
    'Ethereal Armor and All That Glitters are the #1 and #2 adds overall. EDHREC\'s Voltron decks add Duelist\'s Heritage and Open the Armory about twice as often as the rest.'),
   ('Auras on their creatures (goad and removal)',
    'Put the Auras on opponents\' creatures: they goad, draw you cards when those creatures attack, and drain or lock them down. Removal moves from instants to Auras so it also triggers Killian.',
    ['Eye of Nidhogg', 'Visions of Brutality', 'Spirit Loop', 'Grievous Wound', 'Minimus Containment', 'Reprobation', 'Spectral Grasp', 'Nowhere to Run'],
    ['edh-sq', 'gf-sq', 'cz738', 'ds-sq'],
    'Eye of Nidhogg is the #3 add (half of all decks) and in the Command Zone\'s 10. EDHREC\'s Forced Combat theme plays it in 73%.'),
   ('Keep the politics as a fort (the Command Zone\'s take)',
    'Keep Ghostly Prison and the "don\'t attack me" pieces and add more, so opponents swing at each other while you build. Phase two is one big swing once they\'re low.',
    ['Sphere of Safety', 'Grasp of Fate', 'Dawn\'s Truce', 'Umbra Mystic', 'Restoration Magic', 'Spellbook Vendor', 'Ondu Spiritdancer', 'Norn\'s Decree', 'Tenuous Truce', 'Trespasser\'s Curse'],
    ['cz738', 'lab-sq'],
    'Sphere of Safety is added by a third of decks. EDHREC\'s small Pillow Fort theme (about 100 decks) adds the Vow cycle and Windborn Muse.'),
   ('Enchantment tokens',
    'Enchantment creature tokens that grow with your enchantment count, so each Aura also builds a board.',
    ['Sigil of the Empty Throne', 'Hallowed Haunting', 'Daxos the Returned', 'Ghostly Dancers', 'Soaring Lightbringer', 'Anointed Procession'],
    ['gf-sq', 'fs-sq', 'edh-sq', 'lab-sq'],
    'Sigil of the Empty Throne is added by 29% of decks.'),
  ],
  'avoid': [
   ('The Inkling subtheme', ['Intermediate Chirography', 'Combat Calligrapher', 'Forum Filibuster'],
    'Killian doesn\'t care about tokens, and the Inklings are small. Every guide that names cuts drops these.', ['edh-sq', 'gf-sq', 'ds-sq', 'lab-sq', 'fs-sq', 'cz738']),
   ('Gifts that help opponents', ['Secret Rendezvous', 'Keen Duelist', 'Firemane Commando', 'Mangara, the Diplomat', 'Breena, the Demagogue'],
    'They hand cards to the table without adding an Aura. Secret Rendezvous and Keen Duelist are cut by about 4 in 5 decks.', ['edh-sq', 'gf-sq', 'ds-sq', 'lab-sq', 'fs-sq', 'cz738']),
   ('Weak deterrents', ['Tomik, Wielder of Law', 'Nils, Discipline Enforcer'],
    'Opponents just pay or attack with one creature; once you have real "don\'t attack me" effects they add nothing.', ['edh-sq', 'gf-sq', 'lab-sq', 'cz738']),
   ('Combat-only and slow cards', ['Armored Skyhunter', 'Defacing Duskmage', 'Songbirds\' Blessing', 'Doomwake Giant', 'Eldrazi Conscription'],
    'Once-per-attack triggers and seven-drops can\'t keep up with several Auras a turn.', ['gf-sq', 'lab-sq', 'fs-sq', 'cz738']),
   ('Sacrifice fodder', ['Fallen Ideal', 'Screams from Within'],
    'The deck isn\'t aristocrats, and Screams is dead without small creatures to kill.', ['edh-sq', 'gf-sq', 'lab-sq', 'cz738']),
   ('Mild recursive Auras', ['Raffine\'s Guidance', 'Sentinel\'s Eyes'],
    'Cheap and they come back, but too weak on their own once there are better Auras.', ['edh-sq', 'gf-sq', 'lab-sq', 'fs-sq']),
  ],
  'split': [
   'Politics: MTGGoldfish and Flipside cut Ghostly Prison and every politics card; the Command Zone keeps Ghostly Prison, Mangara and Breena and adds Sphere of Safety and Grasp of Fate. On EDHREC, 74% of decks still play Ghostly Prison.',
   'Removal: MTGGoldfish and EDHREC swap the instants (Vanishing Verse, Anguished Unmaking) for Aura removal; the Command Zone adds Path to Exile, and Swords to Plowshares is a top-15 add.',
   'Kaya\'s Ghostform: MTGGoldfish adds it as protection, Draftsim leaves it out ("it reanimates instead of protecting"); 29% of decks add it.',
   'Goad does nothing once it\'s down to two players (EDHLAB), so the Aura-on-their-creatures plan needs a closer.',
  ],
  'alts': 'Alternate commanders on EDHREC: Eriette of the Charmed Apple (653 decks) is played from this box more than the printed alternate, Scriv (503). Scriv decks lean into blink (Ephemerate, Teleportation Circle, Skybind).',
  'videos': [('_uD8hAL3K-Y', '5 KEYS to WINNING with the SILVERQUILL INFLUENCE PRECON', 'Yawgfather Reborn EDH'),
             ('uMRjh28a3mE', 'WE BROKE KILLIAN, DECISIVE MENTOR', 'DeckTechsForDecks'),
             ('k7JqL9fDJSc', 'Silverquill Influence Upgrade, $100', 'Guys That Magic'),
             ('GzrxPRh7O9w', 'Silverquill Precon Upgrade Guide: 22 Changes', 'Jurassic Magic'),
             ('noduuHCTtpc', 'A Darn Good Killian Deck', 'MaldhoundVODs'),
             ('WJN1wOBGv5U', '10 Weird Upgrades for the Silverquill Influence Precon', 'Space Coconut MTG')],
 },
 {
  'group': 'Our newer precons',
  'slug': 'lorehold-spirit', 'name': 'Lorehold Spirit', 'cmd': 'Quintorius, History Chaser', 'colors': 'R/W',
  'gist': 'Quintorius makes a 3/2 Spirit whenever cards leave your graveyard, and his loyalty ability discards to draw. '
          'Upgraders agree the engine is "put cards in the graveyard, then make them leave", and that discard is the cleanest way in. They pull out the Spirit cards that are only there for the creature type and the death-trigger dragons.',
  'themes': ['reanimator', 'tokens', 'graveyard', 'self-mill', 'discard', 'flashback', 'spirits'],
  'angles': [
   ('Discard engine',
    'Rummage and loot every turn: each discard fills the graveyard for Quintorius and the payoffs fire on top. MTGGoldfish calls it "the best area to expand".',
    ['Bag of Holding', 'Banon, the Returners\' Leader', 'Joshua, Phoenix\'s Dominant', 'Tersa Lightshatter', 'Monument to Endurance', 'Inti, Seneschal of the Sun', 'Hardened Academic', 'Cool but Rude', 'Brass\'s Tunnel-Grinder', 'Thrilling Discovery', 'Cathartic Pyre', 'Seasoned Pyromancer'],
    ['gf-ls', 'ds-ls', 'edh-ls', 'cz735', 'ck-ls'],
    'Banon, Bag of Holding, Joshua and Hardened Academic are all top-7 adds. EDHREC\'s Discard theme plays Monument to Endurance, Cool but Rude and Inti far more than average.'),
   ('Graveyard as a second library',
    'Cards that exile or replay from the graveyard on their own, so Quintorius triggers on every turn, not just yours.',
    ['Ark of Hunger', 'Ghost Vacuum', 'Pursue the Past', 'Restoration Seminar', 'Antiquities on the Loose', 'Summoner\'s Sending', 'Garrison Excavator', 'Crucible of Worlds', 'Idol of Oblivion'],
    ['edh-ls', 'ck-ls', 'ds-ls', 'lab-ls', 'gf-ls'],
    'Ark of Hunger is the #1 add (62%). EDHREC\'s Graveyard and Self-mill themes add Restoration Seminar and Pursue the Past most.'),
   ('Go wide with Spirits',
    'Make lots of 3/2s, pump them and alpha strike. Token doublers are Card Kingdom\'s top big-budget priority.',
    ['Intangible Virtue', 'On Wings of Gold', 'Drogskol Reinforcements', 'Renewed Solidarity', 'Neyali, Suns\' Vanguard', 'Caretaker\'s Talent', 'Professional Face-Breaker', 'Bond of Discipline', 'Akroma\'s Will', 'Anointed Procession', 'Mondrak, Glory Dominus', 'Elspeth, Storm Slayer'],
    ['edh-ls', 'ck-ls', 'ds-ls'],
    'EDHREC\'s Tokens theme adds On Wings of Gold, Renewed Solidarity and Caretaker\'s Talent more than average.'),
   ('Reanimate and flicker (value creatures)',
    'Bring back creatures with enter-the-battlefield effects and blink them. This is also how the alternate commander, Excava, is built.',
    ['Angel of Indemnity', 'Serra Paragon', 'Lorehold Archivist', 'Loran of the Third Path', 'Teleportation Circle', 'Eerie Interlude', 'Court of Ardenvale', 'Loyal Retainers'],
    ['lab-ls', 'cz735'],
    'Only EDHLAB builds mostly this way; most of these cards are already in the box. Card Kingdom says $50 isn\'t enough for a good Excava flicker deck.'),
   ('Faster start',
    'Cast Quintorius on turn 3, not 4: two-mana ramp, more cheap permanents, fewer pricey instants and sorceries, and cycling lands so you can play more lands without flooding.',
    ['Talisman of Conviction', 'Boros Signet', 'Fellwar Stone', 'Ornithopter of Paradise', 'Knight of the White Orchid', 'Liquimetal Torque', 'Shenanigans', 'Sundown Pass', 'Sacred Foundry'],
    ['gf-ls', 'ck-ls'],
    'Sundown Pass (32%) and Sacred Foundry (24%) are the most added lands.'),
  ],
  'avoid': [
   ('The death-trigger dragons', ['Ao, the Dawn Sky', 'Atsushi, the Blazing Sky'],
    'Their value comes when they die, and discard sends cards to the graveyard without dying. Cut by about two thirds of decks.', ['edh-ls', 'ds-ls', 'lab-ls', 'cz735']),
   ('A sweeper that kills your own team', ['Wave of Reckoning'],
    'Your board is mostly 3/2 Spirits. Cut by 75% of decks and every guide.', ['gf-ls', 'ds-ls', 'lab-ls', 'cz735']),
   ('Spirits only for the creature type', ['Drumbellower', 'Balefire Liege', 'Kami of Ancient Law', 'Remorseful Cleric', 'Spirit of Resilience', 'Venerable Warsinger'],
    'They do little beyond being Spirits; Quintorius\'s −4 already gives the team vigilance.', ['gf-ls', 'edh-ls', 'ds-ls', 'lab-ls', 'cz735']),
   ('Cards that feed opponents', ['Secret Rendezvous', 'Naktamun Lorespinner'],
    'Three cards to an opponent, or a Wheel of Fortune that refills everyone. Secret Rendezvous is the #1 cut (81%).', ['edh-ls', 'ds-ls', 'lab-ls', 'cz735']),
   ('Narrow or taxing cards', ['White Orchid Phantom', 'Monologue Tax', 'Bitterthorn, Nissa\'s Animus', 'Claim Jumper', 'Lorehold Charm', 'Fateful Tempest'],
    'Land destruction and a tax effect don\'t advance the plan; Bitterthorn and Claim Jumper are slow ramp.', ['edh-ls', 'ds-ls', 'lab-ls']),
   ('Spells-matter and big flashback', ['Lorehold, the Historian', 'Advanced Reconstruction'],
    'Only about 12 instants and sorceries; heavy flashback empties the graveyard Quintorius needs.', ['ds-ls', 'lab-ls']),
  ],
  'split': [
   'Bag of Holding: a top-5 add and in MTGGoldfish\'s and EDHREC\'s lists, but Draftsim leaves it out because its graveyard exile is mandatory and can strand your own recursion.',
   'Flashback: EDHREC\'s Flashback theme (300 decks) adds Pursue the Past and the Flashback card; Draftsim and EDHLAB warn it eats the graveyard.',
   'The Command Zone also cuts Moonshaker Cavalry and Squee from the box; most others keep both.',
  ],
  'alts': 'Excava, the Risen Past is barely played (101 decks vs 6,525 for Quintorius). EDHREC\'s guide cuts it, and Card Kingdom calls Quintorius "without a doubt the better option".',
  'videos': [('tk3dti_ax2Q', 'These 12 cards break this precon!', 'DeckTechsForDecks'),
             ('pbZOT4z8HFE', 'I fixed the Lorehold Precon (And It\'s Actually Dangerous)', 'Command Priority'),
             ('LIex2D3xReU', 'Lorehold Spirit Upgrade, $100', 'Guys That Magic'),
             ('m1tQbgIvDl4', 'Lorehold Precon Upgrade Guide: 21 Card Changes', 'Jurassic Magic'),
             ('R4H5ad-HEmM', 'Lorehold Spirit $10 Upgrades', 'ZombiesGoNomNom MTG'),
             ('TfYW9phviX4', 'Turn-by-turn strategy guide: Lorehold Spirits', 'Yawgfather Reborn EDH')],
 },
 {
  'group': 'Our newer precons',
  'slug': 'living-energy', 'name': 'Living Energy', 'cmd': 'Saheeli, Radiant Creator', 'colors': 'U/R/G',
  'gist': 'Saheeli gives energy for each artifact or Artificer spell and, each combat, pays three energy for a 5/5 hasty copy of one of your permanents. '
          'Upgraders split three ways: more energy and energy finishers, bigger things to copy, or more artifact tokens. The Thopter cards, the legendary copy targets and the slow mana sinks are what they drop.',
  'themes': ['energy', 'artifacts', 'clones', 'tokens', 'artificers', 'vehicles'],
  'angles': [
   ('Big energy (more energy, energy finishers)',
    'Double the energy you make and spend it to win: damage equal to energy gained, energy-fed threats, counters paid with energy.',
    ['Izzet Generatorium', 'Aether Refinery', 'Gonti\'s Aether Heart', 'Roil Cartographer', 'Aether Revolt', 'Electrosiphon', 'Amped Raptor', 'Volatile Stormdrake', 'Galvanic Discharge', 'Aether Spike', 'Primal Prayers', 'Stone Idol Generator', 'HELIOS One'],
    ['cz653', 'ds-le', 'edh-le', 'ck-le', 'gg-le'],
    'The top 6 adds are all energy cards (Izzet Generatorium 67%). Energy is EDHREC\'s biggest theme for Saheeli (1,321 decks). The Command Zone\'s 10 are nearly all energy.'),
   ('Bigger copy targets',
    'Saheeli\'s copy is a 5/5 haste that dies at end of turn, so pick things whose value is on entering or attacking, or that make more bodies. Gathering Games\' combo: Threefold Thunderhulk copied by Saheeli and Brudiclad, about nineteen tokens in one swing.',
    ['Threefold Thunderhulk', 'Brudiclad, Telchor Engineer', 'Blaster Hulk', 'The Motherlode, Excavator', 'Octomancer', 'Aurora Shifter', 'Behemoth of Vault 0', 'Robobrain War Mind', 'Garruk\'s Uprising', 'Esoteric Duplicator', 'Saheeli, the Sun\'s Brilliance', 'Hoarding Dragon'],
    ['gg-le', 'ds-le', 'cz653', 'edh-le'],
    'EDHREC\'s Clones theme plays Garruk\'s Uprising, Octomancer, Esoteric Duplicator and Threefold Thunderhulk about twice as often as other Saheeli decks.'),
   ('Artifact tokens and Artificers',
    'Make and double artifact tokens, so Saheeli\'s energy flows and Artificer payoffs grow. EDHREC\'s non-budget list builds this way.',
    ['Adrix and Nev, Twincasters', 'Parallel Lives', 'Roaming Throne', 'Kappa Cannoneer', 'Arcbound Crusher', 'Simulacrum Synthesizer', 'Scrap Welder', 'Daretti, Scrap Savant', 'Jhoira, Weatherlight Captain', 'Padeem, Consul of Innovation', 'Encroaching Mycosynth'],
    ['edh-le'],
    'EDHREC\'s Artifacts theme (828 decks) and Artificers theme add Jhoira, Padeem and Oviya, Automech Artisan.'),
   ('Blue value and big ETBs (Card Kingdom\'s take)',
    'Card Kingdom keeps the energy core but adds bounce-and-replay value and top-end blue threats rather than artifacts.',
    ['Clement, the Worrywort', 'Words of Wind', 'Tidespout Tyrant', 'Hullbreaker Horror', 'Doubling Season', 'Inexorable Tide', 'Eternal Witness'],
    ['ck-le'],
    'Card Kingdom also says energy and vehicles "lack natural synergy". Saheeli\'s Vehicles theme is tiny (34 decks); vehicles belong to the alternate commander, Pia Nalaar.'),
  ],
  'avoid': [
   ('The Thopter subtheme', ['Whirler Rogue', 'Sai, Master Thopterist', 'Stridehangar Automaton', 'Loyal Apprentice'],
    'Draftsim: "no one buys this precon to play around Thopter tokens". These go first when going big on energy or copies.', ['ds-le', 'edh-le', 'gg-le', 'ck-le']),
   ('Legendary copy targets', ['Pia and Kiran Nalaar'],
    'Saheeli\'s copy keeps the original\'s legendary status, so the legend rule kills one of them. The #2 cut (63%).', ['gg-le', 'ds-le', 'edh-le', 'ck-le']),
   ('Too pricey for the ramp', ['Triplicate Titan', 'Duplicant', 'Elder Gargaroth', 'Aethertide Whale'],
    'Six to nine mana, and not worth copying at that cost.', ['ds-le', 'gg-le', 'ck-le', 'cz653']),
   ('Slow mana sinks', ['Bootleggers\' Stash', 'Retrofitter Foundry', 'Conjurer\'s Closet', 'Midnight Clock', 'Cultivator\'s Caravan'],
    'Bootleggers\' Stash is the #1 cut (70%). Gathering Games: if you\'re using Retrofitter Foundry, "something has gone wrong".', ['edh-le', 'gg-le', 'ds-le', 'cz653', 'ck-le']),
   ('The planeswalker Saheeli', ['Saheeli, Sublime Artificer'],
    'The deck doesn\'t make enough tokens for it.', ['ds-le', 'edh-le']),
  ],
  'split': [
   'Counterspells: EDHREC\'s budget list and the Command Zone cut Disallow (and EDHREC Arcane Denial), but Electrosiphon and Tune the Narrative are top-10 adds, so the counters change rather than vanish.',
   'Thopters: EDHREC\'s small Artificers theme still plays Sai in 64% of decks, so the artifact-token angle keeps what the energy angle cuts.',
   'Ramp: Explosive Vegetation is cut by 44% of decks, while Cards Realm adds Cultivate and Kodama\'s Reach.',
  ],
  'alts': 'Pia Nalaar, Chief Mechanic (the box\'s alternate, 305 decks) is the vehicles build; Saheeli has 4,215.',
  'videos': [('t2g9W-O99qA', 'THIS ENERGY COMMANDER IS BROKEN', 'Panzer MTG'),
             ('8edIkUO0W6I', 'Massive Living Energy Precon Upgrade', 'DeckTechsForDecks'),
             ('KDsaA8ajtJo', 'Living Energy Upgrade, $100', 'Guys That Magic'),
             ('nB49xPe8NdE', 'Living Energy Precon Upgrade, EDH Discussion Guide', 'ThatMillGuy'),
             ('ReRtGYBrups', '5 KEYS to WINNING with the Living Energy PRECON', 'Yawgfather Reborn EDH'),
             ('27VAUxChqVc', 'Living Energy Commander Precon BUDGET Upgrade', 'Commander Mechanic')],
 },
 {
  'group': 'Our newer precons',
  'slug': 'eternal-might', 'name': 'Eternal Might', 'cmd': 'Temmet, Naktamun\'s Will', 'colors': 'W/U/B',
  'gist': 'Temmet loots when attacking and pumps your Zombies when you draw. The box mixes Zombies with non-Zombie embalm and eternalize cards and a discard theme for the alternate commander. '
          'Upgraders make it a real Zombie deck: lords, mass recursion and bursts of card draw. The non-Zombie embalm creatures are the most-cut cards of any of our decks.',
  'themes': ['zombies', 'tokens', 'card-draw', 'reanimator', 'discard', 'wheels', 'aristocrats'],
  'angles': [
   ('Pure Zombie typal',
    'Lords and anthems, Zombies that make more Zombies, and mass recursion to rebuild after a wipe.',
    ['Varina, Lich Queen', 'Zul Ashur, Lich Lord', 'Diregraf Colossus', 'Death Baron', 'Diregraf Captain', 'Lord of the Undead', 'Undead Warchief', 'Wilhelt, the Rotcleaver', 'Necroduality', 'Zombie Apocalypse', 'Endless Ranks of the Dead', 'Liliana, Dreadhorde General', 'Living Death'],
    ['cz654', 'fw', 'csi-em', 'ck-em', 'ds-em'],
    'Varina (51%), Zul Ashur (47%), Necroduality and Diregraf Colossus are top-5 adds and all in the Command Zone\'s 10. Zombies is EDHREC\'s biggest Temmet theme (1,016 decks).'),
   ('Draw bursts to pump the team',
    'Temmet pumps on draws, so draw several cards right before combat and swing.',
    ['Kindred Discovery', 'Windfall', 'Titan of Littjara', 'Teferi\'s Ageless Insight', 'Distant Melody', 'Read the Runes', 'Graveborn Muse', 'God-Eternal Bontu', 'Brainstorm', 'Stinging Study'],
    ['ck-em', 'ds-em', 'csi-em', 'cz654'],
    'CoolStuffInc counts only four burst-draw cards in the box, "a deficit". EDHREC\'s Wheels theme plays Windfall in 80% of decks.'),
   ('Gravecrawler loops (Bracket 3)',
    'Rooftop Storm makes Zombies free; with Gravecrawler and a sacrifice outlet it loops for drain and cards. The Command Zone lists it as a separate "combo upgrade".',
    ['Rooftop Storm', 'Warren Soultrader', 'Carrion Feeder', 'Phyrexian Altar', 'Ashnod\'s Altar', 'Grimgrin, Corpse-Born', 'Bolas\'s Citadel'],
    ['cz654', 'ck-em', 'br-em'],
    'Rooftop Storm is the #1 add (58%). EDHREC\'s Bracketeering article uses this package to move the deck from Bracket 2 to 3, so it\'s a power jump for our table.'),
   ('Discard and loot',
    'Lean into Temmet\'s loot: make Zombies or value whenever you discard. Draftsim builds this way; CoolStuffInc says discard only suits the alternate commander, Hashaton.',
    ['Cryptcaller Chariot', 'Monument to Endurance', 'Bone Miser', 'Cursecloth Wrappings', 'Frantic Search', 'Oskar, Rubbish Reclaimer', 'Master of Death'],
    ['ds-em'],
    'EDHREC\'s Discard theme (278 decks) plays Monument to Endurance and Cryptcaller Chariot well above average.'),
   ('Blue interaction',
    'Counterspells and instant-speed answers in place of the box\'s sorcery-speed removal.',
    ['Counterspell', 'Arcane Denial', 'An Offer You Can\'t Refuse', 'Anguished Unmaking', 'Everything Comes to Dust', 'Long River\'s Pull'],
    ['fw', 'csi-em'],
    'Counterspell is added by 18% of decks.'),
  ],
  'avoid': [
   ('Non-Zombie embalm and eternalize creatures', ['Timeless Dragon', 'Angel of Sanctions', 'Champion of Wits', 'Vizier of Many Faces'],
    'They don\'t get Temmet\'s pump or the lords. Timeless Dragon is cut by 80% of decks, the highest cut rate in any of our precons.', ['cz654', 'fw', 'csi-em', 'ds-em']),
   ('Typal enablers in a deck that\'s already all Zombies', ['Maskwood Nexus'],
    'Its type-changing does nothing when nearly everything is a Zombie (74% cut).', ['fw', 'csi-em', 'ds-em']),
   ('Cycling that doesn\'t draw', ['Twisted Abomination'],
    'Swampcycling doesn\'t trigger Temmet, and the body is rarely worth casting (79% cut).', ['cz654', 'fw', 'csi-em', 'ds-em']),
   ('Keyword filler and slow graveyard cards', ['Never // Return', 'Gate to the Afterlife', 'God-Pharaoh\'s Gift', 'Commence the Endgame', 'Dread Summons', 'Cast Out'],
    'In the box for a word on the card more than for what it does. Draftsim calls Never // Return "abysmal".', ['cz654', 'fw', 'csi-em', 'ds-em']),
   ('A wipe your own board survives poorly', ['Dusk // Dawn'],
    'Temmet\'s pumped team is usually too big for Dusk to be one-sided.', ['fw', 'csi-em', 'ds-em']),
   ('Tapped Deserts and mana rocks', ['Desert of the True', 'Desert of the Mindful', 'Desert of the Glorified', 'Commander\'s Sphere'],
    'They enter tapped and the deck has few desert payoffs; Card Kingdom would rather cast a turn-3 Zombie than a rock.', ['br-em', 'ck-em', 'ds-em', 'csi-em']),
  ],
  'split': [
   'Sacrifice: Draftsim drops the death and sacrifice cards (Corpse Augur, Fleshbag Marauder, Priest of the Crossing); the combo builds add sacrifice outlets instead.',
   'Discard: Draftsim leans into it, CoolStuffInc cuts it (Archfiend of Ifnir, Twisted Abomination) as Hashaton\'s theme.',
   'Land count: Draftsim and CoolStuffInc go down to 37 lands; Card Kingdom stays at 38 or more because of the constant discard.',
  ],
  'alts': 'Hashaton, Scarab\'s Fist (1,523 decks from this box) is a different, stronger deck: discard and reanimator with cEDH-style staples (Esper Sentinel, Rhystic Study, Psychic Frog). Card Kingdom says it isn\'t a budget build. Varina (690) is also played as the commander.',
  'videos': [('vHDuI47uet0', 'The Eternal Might Budget Upgrade Guide', 'The Commander\'s Quarters'),
             ('MMYsTLPzcaA', 'THE ULTIMATE BUDGET ZOMBIE DECK, Temmet', 'Panzer MTG'),
             ('c5E5Fb7_nDw', 'Eternal Might Upgrade, $100', 'Guys That Magic'),
             ('Kd0RaiDd6yM', 'MASSIVE 21 Card Eternal Might Precon upgrade guide', 'DeckTechsForDecks'),
             ('N-dlT70doB8', 'Eternal Might is the Messiest Zombie Deck I\'ve Ever Seen', 'Salubrious Snail'),
             ('De9wu99uUHk', 'Upgrading Eternal Might into a Hashaton Deck', 'Commander Mechanic')],
 },
 # Starter Commander Decks (2022). Fewer, older sources: EDHREC's Scrap Trawlers series (Dec 2022), Cardgamebase,
 # Cards Realm. Star City Games' "Upgrades" articles for all five are video embeds with no text, and Vault Games'
 # budget series returned 503, so neither is used.
 {
  'group': 'Starter Commander Decks (2022)',
  'slug': 'first-flight', 'name': 'First Flight', 'cmd': 'Isperia, Supreme Judge', 'colors': 'W/U',
  'gist': 'Isperia draws you a card whenever a creature attacks you, and the box is flyers plus Sphinxes plus cards that want to be attacked. '
          'Upgraders mostly turn it into a lean flyers deck and often change the commander: on EDHREC more decks from this box run Kangee, Sky Warden than Isperia.',
  'themes': ['flying', 'control', 'pillow-fort', 'sphinxes'],
  'angles': [
   ('Flyers with anthems and cost reducers',
    'Cheap flyers, flyers that make other flyers cheaper or bigger, and protection for the team. Most guides\' main direction.',
    ['Watcher of the Spheres', 'Ornithopter of Paradise', 'Archetype of Imagination', 'The Lord of the Eagles', 'Air Nomad Legacy', 'Thraben Watcher', 'Serra the Benevolent', 'Donal, Herald of Wings', 'Selfless Spirit', 'Unbreakable Formation', 'Serra\'s Emissary'],
    ['edh-ff', 'cgb-ff', 'cr-ff'],
    'Watcher of the Spheres is the #2 add (22%). Flying is the biggest theme on both Isperia and Kangee decks.'),
   ('A different flyer commander',
    'Isperia only rewards being attacked, so guides swap her out: Kangee (Cardgamebase), Dragonlord Ojutai (EDHREC\'s guide, hexproof while untapped), or Errant and Giada.',
    ['Kangee, Sky Warden', 'Dragonlord Ojutai', 'Errant and Giada'],
    ['cgb-ff', 'edh-ff'],
    'EDHREC: 724 decks from this box run Kangee and 704 Isperia; 189 run Errant and Giada and 158 Ojutai.'),
   ('Cheap, steady card draw',
    'Replace the expensive Sphinxes and X-spells with cheap draw that doesn\'t need you to be attacked.',
    ['Reconnaissance Mission', 'Loyal Drake', 'Keep Watch', 'Wizard Class', 'Court of Grace', 'Dream Trawler', 'Medomai the Ageless'],
    ['edh-ff', 'cgb-ff', 'cr-ff'],
    'Reconnaissance Mission (9%) and Loyal Drake (8%) are the cheap draw most often added.'),
   ('Make them attack you (Cards Realm\'s take)',
    'Keep Isperia and lean in: removal that hands the opponent a creature (so they attack you and you draw), removal that also protects.',
    ['Crib Swap', 'Pongify', 'Rapid Hybridization', 'Valorous Stance'],
    ['cr-ff'],
    'Only Cards Realm builds this way.'),
   ('Control and pillow fort',
    'Wraths, tax effects and counters, then win late. No guide builds it, but it is EDHREC\'s second and third theme for Isperia.',
    ['Propaganda', 'Ghostly Prison', 'Windborn Muse', 'Supreme Verdict', 'Austere Command', 'Dovin\'s Veto'],
    [],
    'Control decks (44) play Supreme Verdict 68% vs 28% for all Isperia decks; Pillow Fort decks (27) Ghostly Prison and Propaganda 63% vs about 20%.'),
  ],
  'avoid': [
   ('Creatures that don\'t fly', ['Angler Turtle', 'Hanged Executioner'],
    'Angler Turtle is the #1 cut (59%): no flying and nothing for this plan.', ['edh-ff', 'cgb-ff']),
   ('The expensive Sphinxes and ten-drops', ['Sharding Sphinx', 'Diluvian Primordial', 'Storm Herd', 'Sphinx of Enlightenment', 'Inspired Sphinx'],
    'Slow and costly for what they do; Sphinx of Enlightenment also gives an opponent a card.', ['edh-ff', 'cgb-ff', 'cr-ff']),
   ('Removal that needs them to attack', ['Condemn', 'Soul Snare'],
    'Dead without forced combat, and it punishes the attacks Isperia wants.', ['edh-ff', 'cr-ff']),
   ('Slow artifact ramp', ['Sky Diamond', 'Pilgrim\'s Eye', 'Cartographer\'s Hawk'],
    'Cards Realm: Hawk-style ramp is too slow.', ['cr-ff', 'cgb-ff']),
   ('Clunky cards', ['Vow of Duty', 'Gideon Jura', 'Aven Gagglemaster'],
    'Vow of Duty is cut by half of all decks; Gideon is mediocre in multiplayer.', ['edh-ff', 'cgb-ff', 'cr-ff']),
   ('Tapped lands', ['Meandering River', 'Coastal Tower'],
    'Weaker than even a gate; replace once better duals are in.', ['cgb-ff', 'cr-ff']),
  ],
  'split': [
   'Being attacked: EDHREC\'s guide drops the forced-combat package and Isperia with it; Cards Realm keeps Isperia and adds removal that gives opponents creatures to attack with.',
   'Counterspells: Cards Realm cuts single-target counters (Absorb) as card disadvantage; Cardgamebase adds Mana Drain, and Dovin\'s Veto is a 10% add.',
   'Lands: Cards Realm goes down to 35, Cardgamebase up to 42.',
  ],
  'alts': 'Isperia isn\'t even the most-played commander from her own box (see above).',
  'videos': [('oIwcrj8ncDQ', 'First Flight Upgrade Guide', 'Star City Games'),
             ('Q3sI5REGJ-4', 'First Flight Deck Upgrade Guide', 'Nerds of the West'),
             ('Cqv-ahRvm5w', 'First Flight Upgrades for $10', 'Triple Mango Threat'),
             ('ocnNhW3DGOI', 'The hardest starter pre-con to upgrade?', 'Wizard\'s Institute of Technology')],
 },
 {
  'group': 'Starter Commander Decks (2022)',
  'slug': 'grave-danger', 'name': 'Grave Danger', 'cmd': 'Gisa and Geralf', 'colors': 'U/B',
  'gist': 'Gisa and Geralf mill four and let you cast one Zombie from your graveyard each turn. '
          'Upgraders agree on more Zombies and more self-mill; they split on lords and width versus Zombies with enter and death value. The free-casting Rooftop Storm loops are the big power jump.',
  'themes': ['zombies', 'reanimator', 'graveyard', 'mill', 'combo', 'aristocrats'],
  'angles': [
   ('Zombie lords, go wide',
    'More Zombies, lords and Zombie makers, so every graveyard cast grows the army.',
    ['Death Baron', 'Diregraf Colossus', 'Necroduality', 'Endless Ranks of the Dead', 'Wilhelt, the Rotcleaver', 'Undead Warchief', 'Lord of the Undead', 'Cleaver Skaab', 'Hordewing Skaab', 'Geralf, Visionary Stitcher'],
    ['cgb-gd'],
    'Death Baron (31%), Diregraf Colossus and Necroduality are top-5 adds. Zombies is the biggest theme (789 decks).'),
   ('Value Zombies on a loop',
    'Fewer, better Zombies that do something when they enter or die, recast from the graveyard every turn. EDHREC\'s guide trades width for this.',
    ['Undead Butler', 'Crow of Dark Tidings', 'Forgotten Creation', 'Tomebound Lich', 'Corpse Augur', 'Ravenous Rotbelly', 'Overcharged Amalgam', 'Secrets of the Dead', 'Patriarch\'s Bidding', 'Accursed Marauder', 'Headless Rider'],
    ['edh-gd'],
    'Headless Rider (21%) and Accursed Marauder (20%) are the most added of these.'),
   ('Fill the graveyard on purpose',
    'Self-mill and Entomb effects to put the right Zombie in the yard for Gisa and Geralf.',
    ['Stitcher\'s Supplier', 'Vile Entomber', 'Corpse Connoisseur', 'Buried Alive', 'Repository Skaab'],
    ['edh-gd', 'cgb-gd'],
    'EDHREC\'s Mill theme plays Stitcher\'s Supplier 58% vs 37% for all Gisa and Geralf decks.'),
   ('Gravecrawler loops (Bracket 3)',
    'Rooftop Storm makes Zombies free; Gravecrawler plus a free sacrifice outlet then loops for drain and cards.',
    ['Rooftop Storm', 'Gravecrawler', 'Carrion Feeder', 'Nantuko Husk', 'Ashnod\'s Altar', 'Phyrexian Altar', 'Warren Soultrader', 'Plague Belcher'],
    ['cgb-gd', 'edh-gd'],
    'Rooftop Storm is the #1 add (53%), Gravecrawler #2. EDHREC\'s Combo decks play Gravecrawler 92% and Phyrexian Altar 54% (vs 12%).'),
   ('Blue interaction',
    'Instant-speed counters and answers instead of the box\'s sorcery-speed removal.',
    ['Counterspell', 'Dimir Charm', 'Fact or Fiction', 'Negate'],
    ['cgb-gd', 'edh-gd'],
    'Counterspell is added by 19% of decks.'),
  ],
  'avoid': [
   ('Narrow or clunky removal', ['Murder', 'Cruel Revival', 'Syphon Flesh', 'Undermine'],
    'Outclassed by removal on Zombies you can recast (Ravenous Rotbelly).', ['edh-gd', 'cgb-gd']),
   ('Slow or expensive cards', ['Unstable Obelisk', 'Josu Vess, Lich Knight', 'Gravespawn Sovereign', 'Geralf\'s Mindcrusher', 'Spark Reaper', 'Grimoire of the Dead'],
    'Unstable Obelisk is the #1 cut (64%); Josu\'s value is a ten-mana kicker.', ['edh-gd', 'cgb-gd']),
   ('Low-impact creatures', ['Withered Wretch', 'Lazotep Reaver', 'Lotleth Giant', 'Vela the Night-Clad', 'Liliana\'s Devotee'],
    'Cut on power level; Vela and Liliana\'s Devotee aren\'t Zombies, so Gisa and Geralf can\'t cast them from the graveyard.', ['cgb-gd', 'edh-gd']),
   ('Off-plan card draw', ['Vampiric Rites', 'Pilfered Plans', 'Deep Analysis', 'Wayfarer\'s Bauble'],
    'Deep Analysis and Wayfarer\'s Bauble are cut by about half of decks.', ['edh-gd', 'cgb-gd']),
  ],
  'split': [
   'Lords: EDHREC\'s guide cuts Cemetery Reaper and Lord of the Accursed (no enter or death value, "we\'re not going wide"); Cardgamebase adds Death Baron, Undead Warchief and Lord of the Undead.',
  ],
  'alts': 'Commander swaps are common: The Scarab God (470 decks from this box) and Wilhelt, the Rotcleaver (416) against 2,432 for Gisa and Geralf.',
  'videos': [('gH6UP2j_f8Y', 'Grave Danger Upgrade Guide', 'Star City Games'),
             ('GwQ07X7lwrU', 'Grave Danger Upgrades for $20', 'Triple Mango Threat'),
             ('a-StTvcBUrc', 'How to Play Grave Danger', 'Wizard\'s Institute of Technology')],
 },
 {
  'group': 'Starter Commander Decks (2022)',
  'slug': 'chaos-incarnate', 'name': 'Chaos Incarnate', 'cmd': 'Kardur, Doomscourge', 'colors': 'B/R',
  'gist': 'Kardur makes every opponent\'s creature attack someone else when he enters, and drains when attackers die. The box also has a spells-matter burn package. '
          'Upgraders drop the spells cards and go all-in on goad: more forcing, more ways to re-trigger Kardur, and payoffs for the creatures dying in the fights.',
  'themes': ['forced-combat', 'group-slug', 'chaos', 'burn', 'aristocrats', 'blink'],
  'angles': [
   ('Goad everything',
    'Cheap, repeatable goad so opponents fight each other every turn.',
    ['Disrupt Decorum', 'Shiny Impetus', 'Parasitic Impetus', 'Bloodthirsty Blade', 'Agitator Ant', 'Vengeful Ancestor', 'Spectacular Showdown', 'Bothersome Quasit', 'Frenzied Saddlebrute', 'Curse of Opulence', 'Alexios, Deimos of Kosmos', 'Rite of the Raging Storm'],
    ['edh-ci', 'cr-ci'],
    'Disrupt Decorum is the #1 add (39%). Forced Combat is by far the biggest theme (663 decks).'),
   ('Re-trigger Kardur',
    'Blink or recast him for a fresh goad every turn.',
    ['Conjurer\'s Closet', 'Mirage Phalanx', 'Golden Argosy', 'Sanctum of Eternity', 'Flamerush Rider', 'Undying Malice', 'Supernatural Stamina', 'Feign Death', 'Jaxis, the Troublemaker'],
    ['edh-ci', 'cr-ci'],
    'Conjurer\'s Closet is the #2 add (39%); EDHREC\'s Blink decks play it in 88%.'),
   ('Paid when they die',
    'Draw or drain off the creatures that die in the fights you start.',
    ['Morbid Opportunist', 'Harvester of Souls', 'Karazikar, the Eye Tyrant', 'Blood Artist', 'Calculating Lich', 'Blast-Furnace Hellkite', 'Slaughter Specialist'],
    ['edh-ci', 'cr-ci'],
    'Morbid Opportunist (26%) is the most added. EDHREC\'s Aristocrats decks add sac outlets (Viscera Seer, Goblin Bombardment).'),
   ('Keep attacks off you',
    'Deterrents so the one creature that can still attack picks someone else, and a fix for the last-opponent endgame.',
    ['Revenge of Ravens', 'Blood Reckoning', 'Sudden Spoiling'],
    ['edh-ci'],
    'Both guides note goad stops working once it\'s one-on-one.'),
   ('Group slug',
    'Hurt everyone a little every turn. No guide builds it, but it\'s EDHREC\'s second-biggest theme for Kardur.',
    ['Spiteful Visions', 'Underworld Dreams', 'Descent into Avernus', 'Stormfist Crusader', 'Dictate of the Twin Gods'],
    [],
    'Group Slug decks (162) play Spiteful Visions and Stormfist Crusader well above average.'),
  ],
  'avoid': [
   ('The spells-matter cards', ['Thermo-Alchemist', 'Guttersnipe', 'Wildfire Devils'],
    'The deck doesn\'t cast enough instants and sorceries. Thermo-Alchemist is the #1 cut (58%).', ['edh-ci', 'cr-ci']),
   ('Expensive top end', ['Explosion of Riches', 'Magmatic Force', 'Sunbird\'s Invocation', 'Scythe Specter', 'Sepulchral Primordial', 'Reign of the Pit'],
    'Cut to lower the curve; Scythe Specter also needs to connect.', ['edh-ci', 'cr-ci']),
   ('Gifts to opponents', ['Coveted Jewel'],
    'Cards Realm: it can hand an opponent three cards and three mana. Cut by 51%.', ['cr-ci']),
   ('Slow or off-plan cards', ['Stensia Bloodhall', 'Titan Hunter', 'Profane Command', 'Hate Mirage'],
    'EDHREC\'s guide: Stensia Bloodhall "has no business being in a multiplayer deck".', ['edh-ci']),
  ],
  'split': [
   'Coveted Jewel: Cards Realm calls it a good fit for a goad deck (opponents attack each other to steal it) but risky; half of all decks cut it.',
   'Sepulchral Primordial: EDHREC\'s guide cuts it; Cards Realm keeps it as a Kardur-style enter-the-battlefield target.',
  ],
  'alts': 'Kaervek the Merciless (178 decks from this box) is the main swap; Kardur has 1,444.',
  'videos': [('lPZzfNQ6PHQ', 'Chaos Incarnate Upgrade Guide', 'Star City Games'),
             ('EwMHrzbJBsY', 'Chaos Incarnate Upgrades for $15', 'Triple Mango Threat'),
             ('GOO8TvHBBeI', 'THE GOAD GOAT! Kardur deck tech', 'Jurassic Magic'),
             ('UUxV1qSi3B4', 'WHO NEEDS FRIENDS You have Kardur Doomscourge now!', 'DeckTechsForDecks')],
 },
 {
  'group': 'Starter Commander Decks (2022)',
  'slug': 'draconic-destruction', 'name': 'Draconic Destruction', 'cmd': 'Atarka, World Render', 'colors': 'R/G',
  'gist': 'Atarka gives your attacking Dragons double strike. The box has only 21 Dragons, weak small ones, and a lot of removal. '
          'Upgraders add better Dragons and cheap ramp, then haste and extra combats; they cut the small Dragons, the non-Dragons and some removal.',
  'themes': ['dragons', 'flying', 'ramp', 'extra-combats'],
  'angles': [
   ('More and better Dragons',
    'Dragons that pay you when Dragons enter or hit, so the double-strike swings matter more.',
    ['Thrakkus the Butcher', 'Lathliss, Dragon Queen', 'Utvara Hellkite', 'Dragonborn Champion', 'Old Gnawbone', 'Ryusei, the Falling Star', 'Scourge of the Throne', 'Earthquake Dragon', 'Terror of the Peaks', 'Sarkhan\'s Triumph'],
    ['edh-dd', 'cgb-dd'],
    'Thrakkus (48%) and Lathliss (45%) are the top 2 adds. EDHREC\'s guide went from 21 to 24 Dragons and wanted 30.'),
   ('Cheap ramp and cost reduction',
    'Dragons cost five or more, so two- and three-mana ramp and Dragon cost reducers.',
    ['Scaled Nurturer', 'Goblin Anarchomancer', 'Kodama\'s Reach', 'Rampant Growth', 'Ganax, Astral Hunter', 'Jade Orb of Dragonkind', 'Urza\'s Incubator', 'Monster Manual', 'Dracogenesis'],
    ['edh-dd', 'cgb-dd'],
    'Five of the top 10 adds are ramp. EDHREC\'s guide calls cheap ramp "especially important".'),
   ('Haste and extra combats',
    'Double strike is best twice: haste so a new Dragon swings at once, and extra combat steps.',
    ['Rhythm of the Wild', 'Carnelian Orb of Dragonkind', 'Hellkite Charger', 'Aggravated Assault', 'Lightning Greaves', 'Goldspan Dragon'],
    ['cgb-dd'],
    'EDHREC\'s Extra Combats decks play Aggravated Assault 64% (vs 13%) and Hellkite Charger 75% (vs 28%).'),
   ('Card flow',
    'The box has little draw; add draw that scales with big creatures.',
    ['Return of the Wildspeaker', 'Realmwalker', 'Rishkar\'s Expertise', 'The Great Henge'],
    ['edh-dd', 'cgb-dd'],
    'Return of the Wildspeaker is added by 20% of decks.'),
   ('Get through and stay alive',
    'Evasion for the ground Dragons and protection from wipes.',
    ['Bower Passage', 'Kessig Wolf Run', 'Wrap in Vigor', 'Heroic Intervention'],
    ['edh-dd', 'cgb-dd'],
    'Kessig Wolf Run (16%) is the most added utility land.'),
  ],
  'avoid': [
   ('Weak small Dragons', ['Furnace Whelp', 'Rapacious Dragon', 'Dragonkin Berserker', 'Dragon Mage', 'Demanding Dragon'],
    'Furnace Whelp is the #1 cut (78%): "4 mana for a 2/2 is not keepable".', ['edh-dd', 'cgb-dd']),
   ('Non-Dragon creatures', ['Loaming Shaman', 'Drumhunter', 'Draconic Disciple'],
    'Room for more Dragons.', ['edh-dd', 'cgb-dd']),
   ('Some of the removal', ['Provoke the Trolls', 'Sweltering Suns', 'Chain Reaction', 'Magmaquake'],
    'Provoke the Trolls "does something, but at a very bad rate" (75% cut); one-sided damage sweepers that miss flyers were swapped for Klauth\'s Will.', ['edh-dd', 'cgb-dd']),
   ('Win-more and weak draw', ['Unleash Fury', 'Shamanic Revelation', 'Sarkhan, the Dragonspeaker', 'Atarka Monument'],
    'Shamanic Revelation needs a wide board this deck doesn\'t make; Sarkhan costs too much.', ['edh-dd', 'cgb-dd']),
  ],
  'split': [
   'Lands: Cardgamebase goes up to 43 for the expensive Dragons; EDHREC\'s guide only rebalances the basics.',
   'Sarkhans: both cut Sarkhan, the Dragonspeaker, but Cardgamebase adds Sarkhan the Masterless and Sarkhan, Fireblood.',
  ],
  'alts': 'Atarka is the clear pick (2,742 decks from this box); Ganax, Astral Hunter is next with 181.',
  'videos': [('Vv8tJ5uC5So', 'Draconic Destruction Upgrade Guide', 'Star City Games'),
             ('uqo5IsdtMME', 'Draconic Destruction Deck Upgrade Guide', 'Nerds of the West'),
             ('_rcZSyf-IHE', 'Draconic Destruction Upgrades for $10', 'Triple Mango Threat'),
             ('06SArG3GTEI', 'Never laugh at Live Dragons! Atarka deck tech', 'Jurassic Magic')],
 },
 {
  'group': 'Starter Commander Decks (2022)',
  'slug': 'token-triumph', 'name': 'Token Triumph', 'cmd': 'Emmara, Soul of the Accord', 'colors': 'G/W',
  'gist': 'Emmara makes a 1/1 lifelink Soldier whenever she becomes tapped, and the box has convoke to tap her. '
          'Upgraders add more ways to tap and untap her, token doublers, and draw off the tokens; they cut the slow token makers and the weak draw.',
  'themes': ['tokens', 'tap-untap', 'lifegain', 'populate', 'convoke'],
  'angles': [
   ('Tap and untap Emmara',
    'Every extra tap is a token: tap outlets, then untap effects so she taps on opponents\' turns too.',
    ['Cryptolith Rite', 'Springleaf Drum', 'Relic of Legends', 'Glare of Subdual', 'Smuggler\'s Copter', 'Bennie Bracks, Zoologist', 'Saryth, the Viper\'s Fang', 'Halo Fountain', 'Drumbellower', 'Seedborn Muse', 'Quest for Renewal', 'Wylie Duke, Atiin Hero'],
    ['cgb-tt', 'edh-tt'],
    'Cardgamebase\'s #1 pick is Cryptolith Rite (15% add). EDHREC\'s Tap/Untap decks play Wylie Duke 61% (vs 27%) and Drumbellower 63% (vs 33%).'),
   ('Token doublers and more-token payoffs',
    'Make each token count twice, and turn the 1/1s into a real army.',
    ['Queen Allenal of Ruadach', 'King Darien XLVIII', 'Cadira, Caller of the Small', 'Doubling Season', 'Parallel Lives', 'Anointed Procession', 'Divine Visitation', 'Intangible Virtue', 'Harmonious Archon', 'Elspeth, Sun\'s Champion'],
    ['edh-tt', 'cgb-tt'],
    'Queen Allenal is the #1 add (40%), Intangible Virtue #2, King Darien #3.'),
   ('Draw off the army',
    'The box is short on cards; turn tokens into draws.',
    ['Skullclamp', 'Welcoming Vampire', 'Tocasia\'s Welcome', 'Rumor Gatherer', 'Bess, Soul Nourisher'],
    ['edh-tt', 'cgb-tt'],
    'Welcoming Vampire (20%) and Skullclamp (16%) are the most added draw.'),
   ('Protect the board, then finish',
    'Board-wipe insurance and one big swing.',
    ['Unbreakable Formation', 'Heroic Intervention', 'Flawless Maneuver', 'Grand Crescendo', 'Craterhoof Behemoth', 'Beastmaster Ascension', 'Triumph of the Hordes'],
    ['edh-tt', 'cgb-tt'],
    'EDHREC\'s guide names board protection as the deck\'s biggest gap. Craterhoof is a 12% add.'),
  ],
  'avoid': [
   ('Slow, mana-hungry token makers', ['Jade Mage', 'Selesnya Guildmage', 'Sporemound', 'Verdant Force'],
    'Activation costs too high or over-costed. Selesnya Guildmage (64%) and Jade Mage (63%) are the top cuts.', ['edh-tt', 'cgb-tt']),
   ('Weak card draw', ['Voice of Many', 'Slate of Ancestry', 'Dawn of Hope'],
    'Redundant once real draw is in.', ['edh-tt', 'cgb-tt']),
   ('Off-theme cards', ['Ajani, Caller of the Pride', 'Scavenging Ooze'],
    'Cardgamebase: they don\'t work with the theme.', ['cgb-tt', 'edh-tt']),
   ('One-turn or conditional buffs', ['Valor in Akros', 'Overwhelming Instinct', 'Overrun'],
    'Too much setup for a temporary effect; better finishers exist.', ['edh-tt', 'cgb-tt']),
  ],
  'split': [
   'Populate: EDHREC\'s Populate decks (65) keep Felidar Retreat, Scatter the Seeds and Valor in Akros, which both guides cut.',
   'Removal: Cardgamebase says single-target removal is weak in Commander, yet Swords to Plowshares is the #4 add (23%).',
  ],
  'alts': 'Emmara stays the commander in nearly every deck from this box (1,903; the next, Rhys the Redeemed, has 73).',
  'videos': [('M0zy6Ygl8Po', 'Token Triumph Upgrade Guide', 'Star City Games'),
             ('lD_CMysnwzw', 'Token Triumph Upgrades for $20', 'Triple Mango Threat'),
             ('UFvlASnj7Ao', 'Don\'t sleep on these budget upgrades for Token Triumph', 'Wizard\'s Institute of Technology')],
 },
]

THEME_NAME = {'auras': 'Auras', 'enchantress': 'Enchantress', 'forced-combat': 'Forced combat', 'voltron': 'Voltron', 'pillow-fort': 'Pillow fort',
              'politics': 'Politics', 'reanimator': 'Reanimator', 'tokens': 'Tokens', 'graveyard': 'Graveyard', 'self-mill': 'Self-mill',
              'discard': 'Discard', 'flashback': 'Flashback', 'spirits': 'Spirits', 'energy': 'Energy', 'artifacts': 'Artifacts', 'clones': 'Clones',
              'artificers': 'Artificers', 'vehicles': 'Vehicles', 'zombies': 'Zombies', 'card-draw': 'Card draw', 'wheels': 'Wheels', 'aristocrats': 'Aristocrats',
              'flying': 'Flying', 'control': 'Control', 'sphinxes': 'Sphinxes', 'mill': 'Mill', 'combo': 'Combo', 'group-slug': 'Group slug', 'chaos': 'Chaos',
              'burn': 'Burn', 'blink': 'Blink', 'dragons': 'Dragons', 'ramp': 'Ramp', 'extra-combats': 'Extra combats', 'tap-untap': 'Tap/untap',
              'lifegain': 'Lifegain', 'populate': 'Populate', 'convoke': 'Convoke'}

def esc(s): return html.escape(s, quote=True)

def edhrec(d):
    pre = json.loads(get(f'https://json.edhrec.com/pages/precon/{d["slug"]}.json'))
    L = {l['tag']: l['cardviews'] for l in pre['container']['json_dict']['cardlists']}
    adds = {c['name']: c['num_decks'] / c['potential_decks'] for t in ('cardstoadd', 'landstoadd') for c in L.get(t, []) if c.get('potential_decks')}
    cuts = {c['name']: c['unpopularity'] for t in ('cardstocut', 'landstocut') for c in L.get(t, []) if c.get('unpopularity')}
    n = {c['value']: c['count'] for c in pre['precon_commander_counts']}[d['cmd']]
    slug = d['cmd'].lower().replace(',', '').replace("'", '').replace(' ', '-')
    cp = json.loads(get(f'https://json.edhrec.com/pages/commanders/{slug}.json'))
    tags = {re.sub(r'[^a-z0-9]+', '-', t['value'].lower()).strip('-'): t['count'] for t in cp.get('panels', {}).get('taglinks', [])}
    time.sleep(0.5)
    return n, adds, cuts, tags

def main():
    today = datetime.date.today()
    names = sorted({c for d in DECKS for a in d['angles'] + d['avoid'] for c in (a[2] if len(a) == 5 else a[1])})
    found = {}
    for qty, c in scryfall([(1, {'name': n}, n) for n in names]):
        found[c['name']] = c; found[c['name'].split(' // ')[0]] = c
    flags = {}
    for n in names:
        c = found.get(n) or found.get(n.split(' // ')[0])
        if c is None: raise SystemExit('Scryfall has no card named ' + n)
        flags[n] = (c['legalities'].get('commander') == 'legal', bool(c.get('game_changer')),
                    'https://scryfall.com/search?q=' + urllib.parse.quote(f'!"{c["name"]}"'))
    bad = [n for n, f in flags.items() if not f[0]]
    if bad: print('Not Commander-legal:', ', '.join(bad))

    def chip(n, adds, cuts, mode):
        legal, gc, url = flags[n]
        pct = adds.get(n) if mode == 'add' else cuts.get(n)
        num = f'<span class="p">{"+" if mode == "add" else "−"}{round(pct * 100)}%</span>' if pct else ''
        tag = ('' if legal else '<span class="bad">Not Commander-legal</span>') + ('<span class="gc" title="Game Changer: counts toward the bracket limit">GC</span>' if gc else '')
        return f'<a class="c" href="{url}" target="_blank" rel="noopener">{esc(n)}{num}{tag}</a>'

    def who(keys):
        if not keys: return '<span class="who">no guide; EDHREC\'s theme numbers only</span>'
        return '<span class="who">' + ' · '.join(f'<a href="#src-{k}">{esc(SHORT[k])}</a>' for k in keys) + '</span>'

    SHORT = {k: (v[0].split(',')[0].split(' (')[0].replace('The Command Zone', 'Command Zone')) for k, v in SOURCES.items()}
    secs, toc, group = [], [], None
    for d in DECKS:
        if d['group'] != group:
            group = d['group']
            secs.append(f'<h2 class="grp">{esc(group)}</h2>')
            toc.append(f'<b>{esc(group)}:</b>')
        n, adds, cuts, tags = edhrec(d)
        th = ' · '.join(f'{THEME_NAME[t]} {tags[t]:,}' for t in d['themes'] if t in tags)
        ang = ''.join(f'''<div class="ang"><h4>{esc(t)}</h4><p>{esc(w)}</p><div class="cards">{''.join(chip(c, adds, cuts, 'add') for c in cs)}</div>
<p class="data">{esc(note)}</p><p class="src">Pushed by: {who(ks)}</p></div>''' for t, w, cs, ks, note in d['angles'])
        av = ''.join(f'''<div class="ang av"><h4>{esc(t)}</h4><div class="cards">{''.join(chip(c, adds, cuts, 'cut') for c in cs)}</div>
<p>{esc(w)}</p><p class="src">Cut by: {who(ks)}</p></div>''' for t, cs, w, ks in d['avoid'])
        sp = ''.join(f'<li>{esc(s)}</li>' for s in d['split'])
        vids = ''.join(f'<li><a href="{V}{i}" target="_blank" rel="noopener">{esc(t)}</a> <span class="who">{esc(ch)}</span></li>' for i, t, ch in d['videos'])
        srcs = sorted({k for a in d['angles'] for k in a[3]} | {k for a in d['avoid'] for k in a[3]}, key=list(SOURCES).index)
        sl = ''.join(f'<li id="src-{k}"><a href="{SOURCES[k][1]}" target="_blank" rel="noopener">{esc(SOURCES[k][0])}</a>'
                     + (f'<br><span class="who">{esc(SOURCES[k][2])}</span>' if SOURCES[k][2] else '') + '</li>' for k in srcs)
        toc.append(f'<a href="#{d["slug"]}">{esc(d["name"])}</a>')
        secs.append(f'''<section id="{d['slug']}"><h2 class="dk">{esc(d['name'])} <small>{esc(d['cmd'])} · {d['colors']}</small></h2>
<p>{esc(d['gist'])}</p>
<p class="data">EDHREC: {n:,} decks built from this box with {esc(d['cmd'].split(',')[0])}. Themes those decks are tagged with: {th}. <a href="../adds/{d['slug']}.html">Most added ›</a> <a href="../cuts/{d['slug']}.html">Most cut ›</a></p>
<h3>Directions people take it</h3>{ang}
<h3>What people stay away from</h3>{av}
<h3>Where the sources disagree</h3><ul>{sp}</ul>
<p class="data">{esc(d['alts'])}</p>
<details><summary>Sources for {esc(d['name'])}</summary><ul class="srcs">{sl}</ul>
<p class="data">More upgrade videos found but not read (YouTube blocks transcripts from here, so only titles were seen):</p><ul class="srcs">{vids}</ul></details>
</section>''')

    page = open(os.path.join(HERE, 'angles-template.html')).read()
    page = (page.replace('<!--TOC-->', ' '.join(toc)).replace('<!--DECKS-->', '\n'.join(secs))
                .replace('<!--DATE-->', f'{today:%b %-d, %Y}'))
    open(os.path.join(ROOT, 'decks', 'angles.html'), 'w').write(page)
    print('wrote decks/angles.html,', len(names), 'cards,', sum(f[1] for f in flags.values()), 'Game Changers')

if __name__ == '__main__':
    main()
