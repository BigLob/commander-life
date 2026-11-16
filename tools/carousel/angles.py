"""Build decks/angles.html: for our 10 non-Star Trek precons (5 newer ones and the 5 Starters), the directions
("angles") upgraders take each deck and what they steer clear of, from EDHREC's numbers plus upgrade videos and articles.

The angles, cuts and who-said-what are written by hand below from sources read Nov 16, 2026 (listed in SOURCES).
Videos were read from their YouTube transcripts in the desktop app's built-in browser, plus the creators' own
Moxfield/Archidekt lists for cut lists. Reddit was blocked from both browsers, so nothing here comes from Reddit.
An angle's optional 6th field is a "From play" line: how a direction actually played, per a source that played it.
A deck's 'videos' lists only videos found but not read; 'also' lists sources cited only in 'split' or notes.
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
 'gtm-sq': ('Guys That Magic, "Silverquill Influence Upgrade, $100" (video)', V + 'k7JqL9fDJSc', '13 in, 13 out, read from the transcript. List: https://moxfield.com/decks/nPJn13u23Ueece1s_C13Jw'),
 'sc-sq': ('Space Coconut MTG, "10 Weird Upgrades for the Silverquill Influence Precon" (video)', V + 'WJN1wOBGv5U', '10 in, 10 out, read from the transcript.'),
 'jm-sq': ('Jurassic Magic, "Silverquill Precon Upgrade Guide: 22 Changes" (video)', V + 'GzrxPRh7O9w', 'Read from the transcript. Only the adds are discussed; the description\'s Moxfield link is broken, so its cuts are unknown.'),
 'dt-sq': ('DeckTechsForDecks, "We Broke Killian, Decisive Mentor" (video)', V + 'uMRjh28a3mE', 'A ground-up Bracket 3 build rather than a 10-card upgrade, read from the transcript. List: https://moxfield.com/decks/BowoO7qpSU-oguHjXtba0w'),
 'mh-sq': ('MaldhoundVODs, "A Darn Good Killian Deck" (video)', V + 'noduuHCTtpc', 'A review of a viewer\'s upgraded Killian deck (Bracket 2) with a goldfish playtest, read from the transcript.'),
 'yf-sq': ('Yawgfather Reborn EDH, "5 Keys to Winning with the Silverquill Influence Precon" (video)', V + '_uD8hAL3K-Y', 'How to play the stock deck; no card swaps.'),
 # Lorehold Spirit
 'cz735': ('The Command Zone #735 (video)', V + 'rNUv0ZWrJeE', 'Its 10 in, 10 out list, from the GameKnights Archidekt account: ' + A + '21533404'),
 'gf-ls': ('MTGGoldfish, "These Swaps Make Lorehold Spirit Absolutely Busted" (video + article)', 'https://www.mtggoldfish.com/articles/these-swaps-make-lorehold-spirit-absolutely-busted', 'Video: ' + V + 'lNsesVdLvFI'),
 'edh-ls': ('EDHREC upgrade guide, Andy Zupke, Apr 13 2026', 'https://edhrec.com/articles/lorehold-spirit-precon-upgrade/', ''),
 'ck-ls': ('Card Kingdom, $50 upgrade guide', 'https://blog.cardkingdom.com/secrets-of-strixhaven-lorehold-spirit-commander-deck-upgrade-guide/', ''),
 'ds-ls': ('Draftsim upgrade guide (20 in, 20 out)', 'https://draftsim.com/lorehold-spirit-upgrade-guide/', ''),
 'lab-ls': ('EDHLAB, "Reconstructing" upgrade guide', 'https://blog.edhlab.gg/reconstructing-white-red-lorehold-spirit-precon-upgrade-guide/', ''),
 'gtm-ls': ('Guys That Magic, "Lorehold Spirit Upgrade, $100" (video)', V + 'LIex2D3xReU', 'Read from the transcript. List: https://moxfield.com/decks/9ygsANj5mUa1H8J7fYHxuQ'),
 'cp-ls': ('Command Priority, "I fixed the Lorehold Precon" (video)', V + 'pbZOT4z8HFE', '15 in, 15 out for $30, Bracket 3, read from the transcript.'),
 'dt-ls': ('DeckTechsForDecks, "These 12 cards break this precon!" (video)', V + 'tk3dti_ax2Q', '12 in, 12 out for $35, read from the transcript; the cuts from its Moxfield list: https://moxfield.com/decks/ZRZGO8KDmUuNBHER0TkcGg'),
 'jm-ls': ('Jurassic Magic, "Lorehold Precon Upgrade Guide: 21 Card Changes" (video)', V + 'm1tQbgIvDl4', 'Read from the transcript (adds only). List: https://moxfield.com/decks/TOYhNUUtHk6lMyPbi9hjDw'),
 'zg-ls': ('ZombiesGoNomNom MTG, "Lorehold Spirit $10 Upgrades" (video)', V + 'R4H5ad-HEmM', '$10, $25 and Strixhaven-only tiers, read from the transcript; cuts from its Archidekt list: https://archidekt.com/decks/21462545'),
 'yf-ls': ('Yawgfather Reborn EDH, "Turn-by-turn strategy guide: Lorehold Spirits" (video)', V + 'TfYW9phviX4', 'A goldfish game with the stock deck; no card swaps.'),
 # Living Energy
 'cz653': ('The Command Zone #653 (video)', V + 'km1f1W0Tl6k', 'Its 10 in, 10 out list, from the GameKnights Archidekt account: ' + A + '11021591'),
 'edh-le': ('EDHREC upgrade guide, Andy Zupke, Jan 29 2025', 'https://edhrec.com/articles/living-energy-precon-upgrade-guide-aetherdrift', ''),
 'ck-le': ('Card Kingdom, $50 upgrade', 'https://blog.cardkingdom.com/aetherdrift-living-energy-precon-upgrade/', ''),
 'ds-le': ('Draftsim upgrade guide', 'https://draftsim.com/living-energy-upgrade-guide/', ''),
 'gg-le': ('Gathering Games upgrade guide', 'https://gatheringgames.co.uk/community/blog/living-energy-precon-upgrade-guide-mtg-aetherdift-commander-decks', ''),
 'gtm-le': ('Guys That Magic, "Living Energy Upgrade, $100" (video)', V + 'KDsaA8ajtJo', 'Read from the transcript. List: https://moxfield.com/decks/13o8Ko7fE0-C1M5lE-KhcQ'),
 'dt-le': ('DeckTechsForDecks, "Massive Living Energy Precon Upgrade" (video)', V + '8edIkUO0W6I', 'No budget, read from the transcript; cuts from its Moxfield list: https://moxfield.com/decks/2HLv8KrKJ0OFOeYMak_KOQ'),
 'pz-le': ('Panzer MTG, "This Energy Commander Is Broken" (video)', V + 't2g9W-O99qA', 'A no-budget, ground-up Saheeli list (70 minutes), read from the transcript; he says he played it 50 games. List: https://moxfield.com/decks/iMbOFZFKpkq2-aGfS24ruQ'),
 'tmg-le': ('ThatMillGuy, "Living Energy Precon Upgrade, EDH Discussion Guide" (video)', V + 'nB49xPe8NdE', 'Key cards only, no cut list; read from the transcript.'),
 'cm-le': ('Commander Mechanic, "Living Energy Commander Precon BUDGET Upgrade" (video)', V + '27VAUxChqVc', 'Upgrades the deck with Pia Nalaar as commander; read from the transcript. List: https://moxfield.com/decks/kI1vAQ1320qUM9g8mbQdKA'),
 'yf-le': ('Yawgfather Reborn EDH, "5 Keys to Winning with the Living Energy Precon" (video)', V + 'ReRtGYBrups', 'Playtests the stock deck; no card swaps.'),
 # Eternal Might
 'cz654': ('The Command Zone #654 (video)', V + '8J9lOe-NhZg', 'Its 10 in, 10 out list plus a 2-card "combo upgrade", from the GameKnights Archidekt account: ' + A + '11039235'),
 'fw': ('Farwater MTG (YouTube), upgraded Temmet list', A + '11257428', 'The channel\'s Archidekt list (19 in, 19 out), 6,900 views. The channel\'s video: ' + V + 'S1p1_6RZjUE'),
 'ck-em': ('Card Kingdom, $30 upgrade guide', 'https://blog.cardkingdom.com/aetherdrift-eternal-might-precon-upgrade-guide/', ''),
 'ds-em': ('Draftsim, 15 upgrades, Mar 2026', 'https://draftsim.com/eternal-might-upgrade-guide/', ''),
 'csi-em': ('CoolStuffInc, $50 upgrade guide, Feb 2025', 'https://www.coolstuffinc.com/a/briansmith-seo-02122025-aetherdrifts-eternal-might-precon-upgrade-guide', ''),
 'br-em': ('EDHREC, "Bracketeering: Eternal Might", John Sherwood, Mar 17 2025', 'https://edhrec.com/articles/bracketeering-eternal-might', ''),
 'gtm-em': ('Guys That Magic, "Eternal Might Upgrade, $100" (video)', V + 'c5E5Fb7_nDw', 'Read from the transcript. List: https://moxfield.com/decks/-LASEd5-B0isA2_VVGZCHw'),
 'cq-em': ('The Commander\'s Quarters, "The Eternal Might Budget Upgrade Guide" (video)', V + 'vHDuI47uet0', 'Every add under $1, read from the transcript.'),
 'dt-em': ('DeckTechsForDecks, "Massive 21 Card Eternal Might Precon Upgrade Guide" (video)', V + 'Kd0RaiDd6yM', 'No budget, read from the transcript; cuts from its Moxfield list: https://moxfield.com/decks/y7A_Ujgyg0qe0FF_E5QOBA'),
 'pz-em': ('Panzer MTG, "The Ultimate Budget Zombie Deck, Temmet" (video)', V + 'MMYsTLPzcaA', 'A ground-up €150 Bracket 2 list, read from the transcript. List: https://moxfield.com/decks/SUSqp1-XMESCask9_YZJgA'),
 'ss-em': ('Salubrious Snail, "Eternal Might is the Messiest Zombie Deck I\'ve Ever Seen" (video)', V + 'N-dlT70doB8', 'A critique plus a 15-card upgrade, read from the transcript and its Archidekt list: https://archidekt.com/decks/11251533'),
 'cm-em': ('Commander Mechanic, "Upgrading Eternal Might into a Hashaton Deck" (video)', V + 'De9wu99uUHk', 'Read from the transcript. List: https://moxfield.com/decks/3Ha8CLlDwkyvEQzokVAQyA'),
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
 # Starter videos (read from their transcripts)
 'scg-ff': ('Star City Games, "First Flight Upgrade Guide" (video)', V + 'oIwcrj8ncDQ', 'Adds only, about $5 each.'),
 'nw-ff': ('Nerds of the West, "First Flight Deck Upgrade Guide" (video)', V + 'Q3sI5REGJ-4', '14 in, 14 out; tested in games on stream before and after. Adds: https://moxfield.com/decks/2OVegcbOR0-UVwW35p3K1A, cuts: https://moxfield.com/decks/k3_6iEAW2U-NGZWOCMc1bA'),
 'tm-ff': ('Triple Mango Threat, "First Flight Upgrades for $10" (video)', V + 'Cqv-ahRvm5w', 'Adds only.'),
 'wit-ff': ('Wizard\'s Institute of Technology, "The hardest starter pre-con to upgrade?" (video)', V + 'ocnNhW3DGOI', 'A 97-minute rebuild with goldfish playtests.'),
 'scg-gd': ('Star City Games, "Grave Danger Upgrade Guide" (video)', V + 'gH6UP2j_f8Y', 'Adds only, under $5 each.'),
 'tm-gd': ('Triple Mango Threat, "Grave Danger Upgrades for $20" (video)', V + 'GwQ07X7lwrU', 'Adds only.'),
 'wit-gd': ('Wizard\'s Institute of Technology, "How to Play Grave Danger" (video)', V + 'a-StTvcBUrc', 'How to play the stock deck; no swaps.'),
 'sq-gd': ('Squirrel commander, "Grave Danger precon upgrade guide" (video)', V + 'UZDJSjb0IE4', 'Found by searching YouTube; adds and cuts with reasons.'),
 'scg-ci': ('Star City Games, "Chaos Incarnate Upgrade Guide" (video)', V + 'lPZzfNQ6PHQ', 'Adds only, about $5 each (Conjurer\'s Closet about $10).'),
 'tm-ci': ('Triple Mango Threat, "Chaos Incarnate Upgrades for $15" (video)', V + 'EwMHrzbJBsY', 'Adds and cuts.'),
 'jm-ci': ('Jurassic Magic, "The Goad Goat! Kardur deck tech" (video)', V + 'GOO8TvHBBeI', 'Adds only; the host has played the commander "a couple of times".'),
 'dt-ci': ('DeckTechsForDecks, "Who Needs Friends: Kardur, Doomscourge" (video)', V + 'UUxV1qSi3B4', 'A ground-up Kardur list. List: https://moxfield.com/decks/BTQYuScg30KJr3TIfMVIMg'),
 'scg-dd': ('Star City Games, "Draconic Destruction Upgrade Guide" (video)', V + 'Vv8tJ5uC5So', 'Adds only, about $5 to $7 each.'),
 'nw-dd': ('Nerds of the West, "Draconic Destruction Deck Upgrade Guide" (video)', V + 'uqo5IsdtMME', '30 in, 30 out for about AU$27; tested in games on stream first. Adds: https://moxfield.com/decks/VOGuImh-FkiXadUZ2ZPo6Q, cuts: https://moxfield.com/decks/UQCqtsIKJkOaC8ofpZB02Q'),
 'tm-dd': ('Triple Mango Threat, "Draconic Destruction Upgrades for $10" (video)', V + '_rcZSyf-IHE', 'Adds and cuts.'),
 'jm-dd': ('Jurassic Magic, "Never laugh at Live Dragons! Atarka deck tech" (video)', V + '06SArG3GTEI', 'Adds only.'),
 'scg-tt': ('Star City Games, "Token Triumph Upgrade Guide" (video)', V + 'M0zy6Ygl8Po', 'Adds only.'),
 'tm-tt': ('Triple Mango Threat, "Token Triumph Upgrades for $20" (video)', V + 'lD_CMysnwzw', 'Adds only.'),
 'wit-tt': ('Wizard\'s Institute of Technology, "Don\'t sleep on these budget upgrades for Token Triumph" (video)', V + 'UFvlASnj7Ao', '12 in, 12 out.'),
 'mb-tt': ('MTG Basics, "Token Triumph Deck Deconstruction" (video)', V + 'canf79YKDXY', 'Found by searching YouTube; a walkthrough of the stock deck, no swaps.'),
 # Revival Trance (Final Fantasy VI)
 'cz677': ('The Command Zone #677 (video)', V + 'ZqI_-DH7lBc', 'Its 10 in, 10 out for $50 (read from the transcript and the show\'s Archidekt list): https://archidekt.com/decks/13139894'),
 'dt-rt': ('DeckTechsForDecks, "Revival Trance Massive 16 Card Precon Upgrade" (video)', V + 'ReuawwVtU5s', 'Read from the transcript; cuts from its Moxfield list: https://moxfield.com/decks/K5Bqv16dp0WqNobaquipkg'),
 'gz-rt': ('Grazzet MTG, "Cut-Rate Commander: Revival Trance" (video)', V + '-4RlRqj02Nc', '$30, one-for-one swaps with reasons, read from the transcript. List: https://archidekt.com/decks/13722104'),
 'yf-rt': ('Yawgfather Reborn EDH, "5 Keys to Winning with the Revival Trance Precon" (video)', V + 'XCpI9aERwFQ', 'How to play the stock deck; no swaps.'),
 'ds-rt': ('Draftsim, "Revival Trance Upgrade Guide: 23 Easy Changes", May 20 2025', 'https://draftsim.com/revival-trance-upgrade-guide/', 'Swaps the commander to Celes, Rune Knight.'),
 'ub-rt': ('UNIVERSES BEYOND, "A Fun Upgrade for Revival Trance with Celes, Rune Knight: Bracket 3" (video)', V + 'NBMEctPBt2w', '15 in, 15 out with Celes as commander, read from the transcript; played four games with it.'),
 'cp-rt': ('The Commander Pod, "A Closer Look at Celes, Rune Knight Plus Budget Upgrades" (video)', V + 'yLvSGoWh81E', 'Played the box in a precon league, first with Terra, then with Celes; $27 of upgrades. Read from the transcript. List: https://moxfield.com/decks/bvf6K2Gre0KUIaa_6z44rQ'),
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
    ['Mesa Enchantress', 'Light-Paws, Emperor\'s Voice', 'Danitha Capashen, Paragon', 'Codsworth, Handy Helper', 'Delney, Streetwise Lookout', 'Feather of Flight', 'Angelic Gift', 'Rune of Mortality', 'Unquestioned Authority', 'Scourgemark', 'Hero of Iroas', 'Sigarda\'s Aid', 'Retether', 'Tempest Technique', 'Hall of Heliod\'s Generosity'],
    ['gf-sq', 'fs-sq', 'ds-sq', 'edh-sq', 'cz738', 'gtm-sq', 'sc-sq', 'jm-sq'],
    'MTGGoldfish calls the one-mana draw Auras the "secret sauce". EDHREC\'s Auras theme (the biggest) plays Mesa Enchantress and Hall of Heliod\'s Generosity more than average. Guys That Magic calls Codsworth (ward 2 for Killian plus Aura mana) "the engine"; Delney doubles Killian\'s triggers since he has 2 power.'),
   ('One huge evasive attacker (Voltron)',
    'Stack the scaling Auras on one flyer or on Killian and win through commander-style damage. Shares most cards with the Aura plan; the difference is the payoffs.',
    ['Ethereal Armor', 'All That Glitters', 'Mantle of the Ancients', 'Twinblade Blessing', 'Brilliant Wings', 'Open the Armory', 'Duelist\'s Heritage', 'Boon of the Spirit Realm', 'Rashel, Fist of Torm', 'Super State'],
    ['gf-sq', 'edh-sq', 'ds-sq', 'fs-sq', 'jm-sq', 'sc-sq'],
    'Ethereal Armor and All That Glitters are the #1 and #2 adds overall. EDHREC\'s Voltron decks add Duelist\'s Heritage and Open the Armory about twice as often as the rest.'),
   ('Auras on their creatures (goad and removal)',
    'Put the Auras on opponents\' creatures: they goad, draw you cards when those creatures attack, and drain or lock them down. Removal moves from instants to Auras (or enchantments like Dimensional Exile) so it also triggers Killian. The videos favour "forever" Auras that return when the creature dies, so there is always another goad.',
    ['Eye of Nidhogg', 'Ghoulish Impetus', 'Glistening Oil', 'Nurgle\'s Rot', 'Vampiric Link', 'Visions of Brutality', 'Spirit Loop', 'Dimensional Exile', 'Authority of the Consuls', 'Grievous Wound', 'Minimus Containment', 'Reprobation', 'Spectral Grasp', 'Nowhere to Run'],
    ['edh-sq', 'gf-sq', 'cz738', 'ds-sq', 'gtm-sq', 'dt-sq', 'sc-sq'],
    'Eye of Nidhogg is the #3 add (half of all decks) and in the Command Zone\'s 10. EDHREC\'s Forced Combat theme plays it in 73%. Guys That Magic\'s $100 list is built on Glistening Oil, Nurgle\'s Rot and Vampiric Link; Space Coconut calls Visions of Brutality its favourite Aura.'),
   ('Keep the politics as a fort (the Command Zone\'s take)',
    'Keep Ghostly Prison and the "don\'t attack me" pieces and add more, so opponents swing at each other while you build. Phase two is one big swing once they\'re low.',
    ['Sphere of Safety', 'Grasp of Fate', 'Dawn\'s Truce', 'Umbra Mystic', 'Restoration Magic', 'Spellbook Vendor', 'Ondu Spiritdancer', 'Immortal Obligation', 'Norn\'s Decree', 'Tenuous Truce', 'Trespasser\'s Curse'],
    ['cz738', 'lab-sq', 'jm-sq', 'sc-sq', 'yf-sq', 'mh-sq'],
    'Sphere of Safety is added by a third of decks; Jurassic Magic and Space Coconut add it too. Jurassic Magic calls Duelist\'s Heritage "a great political piece" (offer double strike to whoever attacks someone else). EDHREC\'s small Pillow Fort theme (about 100 decks) adds the Vow cycle and Windborn Muse.',
    'MaldhoundVODs reviewed a viewer\'s upgraded deck that played well in person but badly in online games where nobody took deals. The advice: stop asking for deals and just tap down a threat so attacking someone else is free; Scriv\'s contracts work without any talking. Yawgfather adds: goad the creature of the player whose turn comes last, so everyone gets to hit them.'),
   ('Enchantment tokens',
    'Enchantment creature tokens that grow with your enchantment count, so each Aura also builds a board.',
    ['Sigil of the Empty Throne', 'Hallowed Haunting', 'Daxos the Returned', 'Ghostly Dancers', 'Soaring Lightbringer', 'Anointed Procession'],
    ['gf-sq', 'fs-sq', 'edh-sq', 'lab-sq', 'dt-sq', 'jm-sq', 'sc-sq'],
    'Sigil of the Empty Throne is added by 29% of decks.'),
   ('Aura loops with a sacrifice outlet (Bracket 3)',
    'Recursive Auras plus a free sacrifice outlet and a token maker loop for endless enchantment triggers. DeckTechsForDecks builds Killian this way: Screams from Within on a token, or Raffine\'s Guidance recast from the graveyard, or Caretaker\'s Talent copied by Ondu Spiritdancer.',
    ['Phyrexian Altar', 'Warren Soultrader', 'Caretaker\'s Talent', 'Ondu Spiritdancer', 'Cloudstone Curio', 'Screams from Within', 'Raffine\'s Guidance'],
    ['dt-sq'],
    'Only DeckTechsForDecks goes this way, and calls them "combos of synergy" (three or four pieces) rather than two-card combos.'),
   ('Card draw that doesn\'t need Killian',
    'Nearly all of the deck\'s card advantage comes from Killian plus an enchanted attacker. Add some that works without him, and recursion for the key creatures rather than for Auras.',
    ['Decorum Dissertation', 'Phyrexian Arena', 'Necromancy', 'Restoration Seminar', 'Chains of Custody'],
    ['mh-sq'],
    'MaldhoundVODs rates Decorum Dissertation "9 out of 10" in Bracket 2. Chains of Custody is removal that triggers Killian; most players just take their commander back.',
    'In MaldhoundVODs\' goldfish games of the viewer\'s deck, a wipe left "perilously few outs", because almost every card draw needed Killian on the battlefield.'),
  ],
  'avoid': [
   ('The Inkling subtheme', ['Intermediate Chirography', 'Combat Calligrapher', 'Forum Filibuster'],
    'Killian doesn\'t care about tokens, and the Inklings are small. Every guide that names cuts drops these; Guys That Magic: Chirography "does a whole lot of nothing".', ['edh-sq', 'gf-sq', 'ds-sq', 'lab-sq', 'fs-sq', 'cz738', 'gtm-sq', 'sc-sq', 'mh-sq']),
   ('Gifts that help opponents', ['Secret Rendezvous', 'Keen Duelist', 'Firemane Commando', 'Mangara, the Diplomat', 'Breena, the Demagogue'],
    'They hand cards to the table without adding an Aura. Secret Rendezvous and Keen Duelist are cut by about 4 in 5 decks. Space Coconut: Breena does little when opponents just avoid the highest life total.', ['edh-sq', 'gf-sq', 'ds-sq', 'lab-sq', 'fs-sq', 'cz738', 'gtm-sq', 'sc-sq']),
   ('Weak deterrents', ['Tomik, Wielder of Law', 'Nils, Discipline Enforcer'],
    'Opponents just pay or attack with one creature; once you have real "don\'t attack me" effects they add nothing. Space Coconut swaps Nils for Sphere of Safety.', ['edh-sq', 'gf-sq', 'lab-sq', 'cz738', 'gtm-sq', 'sc-sq']),
   ('Combat-only and slow cards', ['Armored Skyhunter', 'Defacing Duskmage', 'Songbirds\' Blessing', 'Doomwake Giant', 'Eldrazi Conscription'],
    'Once-per-attack triggers and seven-drops can\'t keep up with several Auras a turn. Guys That Magic: Doomwake Giant is five mana for a −1/−1.', ['gf-sq', 'lab-sq', 'fs-sq', 'cz738', 'gtm-sq', 'sc-sq']),
   ('Sacrifice fodder', ['Fallen Ideal', 'Screams from Within'],
    'The deck isn\'t aristocrats, and Screams is dead without small creatures to kill.', ['edh-sq', 'gf-sq', 'lab-sq', 'cz738', 'gtm-sq', 'sc-sq', 'mh-sq']),
   ('Mild recursive Auras', ['Raffine\'s Guidance', 'Sentinel\'s Eyes'],
    'Cheap and they come back, but too weak on their own once there are better Auras.', ['edh-sq', 'gf-sq', 'lab-sq', 'fs-sq', 'gtm-sq']),
   ('Bodies and pricey Auras for your own side', ['Ajani\'s Chosen', 'Angelic Destiny'],
    'You mostly put Auras on their creatures, so a Cat per Aura adds little (Guys That Magic); "bodies isn\'t our problem" (MaldhoundVODs). Space Coconut: Angelic Destiny is five mana for one Angel when Sigil of the Empty Throne makes one per enchantment.', ['gtm-sq', 'mh-sq', 'sc-sq']),
   ('Tapped lands', ['Silverquill Campus', 'Temple of Silence', 'Terramorphic Expanse', 'Path of Ancestry'],
    'Guys That Magic swaps them for Godless Shrine, Reliquary Tower and Shattered Sanctum; Space Coconut swaps Path of Ancestry for Hall of Heliod\'s Generosity.', ['gtm-sq', 'sc-sq']),
  ],
  'split': [
   'Politics: MTGGoldfish and Flipside cut Ghostly Prison and every politics card; the Command Zone keeps Ghostly Prison, Mangara and Breena and adds Sphere of Safety and Grasp of Fate. On EDHREC, 74% of decks still play Ghostly Prison.',
   'Removal: MTGGoldfish and EDHREC swap the instants (Vanishing Verse, Anguished Unmaking) for Aura removal; the Command Zone adds Path to Exile, and Swords to Plowshares is a top-15 add.',
   'Kaya\'s Ghostform: MTGGoldfish adds it as protection, Draftsim leaves it out ("it reanimates instead of protecting"); 29% of decks add it.',
   'Goad does nothing once it\'s down to two players (EDHLAB), so the Aura-on-their-creatures plan needs a closer. DeckTechsForDecks\' answer is Ardenn, Intrepid Archaeologist moving every Aura onto one of your creatures; Yawgfather warns goad points back at you in a two-player game.',
   'Screams from Within and Raffine\'s Guidance: most guides cut them, but DeckTechsForDecks\' Bracket 3 build keeps both as loop pieces with a sacrifice outlet.',
   'Secret Rendezvous and Keen Duelist: cut nearly everywhere, yet MaldhoundVODs would put them back as card draw that doesn\'t need Killian.',
   'Ajani\'s Chosen: Guys That Magic and MaldhoundVODs cut it; DeckTechsForDecks plays it as an enchantment-triggered token maker.',
   'Killian vs Scriv: Jurassic Magic and Guys That Magic keep Killian for the card draw and the tapped-down blockers; Guys That Magic also suggests Eriette at the helm.',
  ],
  'alts': 'Alternate commanders on EDHREC: Eriette of the Charmed Apple (653 decks) is played from this box more than the printed alternate, Scriv (503). Scriv decks lean into blink (Ephemerate, Teleportation Circle, Skybind).',
  'videos': [],
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
    ['Bag of Holding', 'Banon, the Returners\' Leader', 'Joshua, Phoenix\'s Dominant', 'Tersa Lightshatter', 'Monument to Endurance', 'Surly Badgersaur', 'Goblin Engineer', 'Inti, Seneschal of the Sun', 'Hardened Academic', 'Cool but Rude', 'Brass\'s Tunnel-Grinder', 'Thrilling Discovery', 'Decaying Time Loop', 'Big Score', 'Cathartic Pyre', 'Seasoned Pyromancer'],
    ['gf-ls', 'ds-ls', 'edh-ls', 'cz735', 'ck-ls', 'dt-ls', 'cp-ls', 'gtm-ls', 'jm-ls', 'zg-ls'],
    'Banon, Bag of Holding, Joshua and Hardened Academic are all top-7 adds; Bag of Holding is in three of the five upgrade videos. EDHREC\'s Discard theme plays Monument to Endurance, Cool but Rude and Inti far more than average. DeckTechsForDecks uses Goblin Engineer to fetch and recur the Bag.'),
   ('Graveyard as a second library',
    'Cards that exile or replay from the graveyard on their own, so Quintorius triggers on every turn, not just yours.',
    ['Ark of Hunger', 'Ghost Vacuum', 'Relic of Progenitus', 'Pursue the Past', 'Restoration Seminar', 'Antiquities on the Loose', 'Summoner\'s Sending', 'Recommission', 'Reconstruct History', 'Court of Ardenvale', 'Phlage, Titan of Fire\'s Fury', 'Garrison Excavator', 'Crucible of Worlds', 'Idol of Oblivion'],
    ['edh-ls', 'ck-ls', 'ds-ls', 'lab-ls', 'gf-ls', 'gtm-ls', 'cp-ls', 'jm-ls', 'zg-ls', 'dt-ls'],
    'Ark of Hunger is the #1 add (62%). EDHREC\'s Graveyard and Self-mill themes add Restoration Seminar and Pursue the Past most. Ghost Vacuum is in four of the five upgrade videos: it triggers Quintorius at instant speed, is graveyard hate, and late on brings back every exiled creature as a Spirit.'),
   ('Go wide with Spirits',
    'Make lots of 3/2s, pump them and alpha strike. Token doublers are Card Kingdom\'s top big-budget priority.',
    ['Intangible Virtue', 'On Wings of Gold', 'Drogskol Reinforcements', 'Renewed Solidarity', 'Neyali, Suns\' Vanguard', 'Caretaker\'s Talent', 'Professional Face-Breaker', 'Warleader\'s Call', 'Shared Animosity', 'Waves of Aggression', 'Bond of Discipline', 'Akroma\'s Will', 'Anointed Procession', 'Mondrak, Glory Dominus', 'Elspeth, Storm Slayer'],
    ['edh-ls', 'ck-ls', 'ds-ls', 'cp-ls', 'dt-ls', 'gtm-ls', 'jm-ls', 'zg-ls', 'yf-ls'],
    'EDHREC\'s Tokens theme adds On Wings of Gold, Renewed Solidarity and Caretaker\'s Talent more than average. Command Priority narrows the deck to Spirits ("it felt split"); Drogskol Reinforcements gives each Spirit +3/+3 when you attack all three players. Guys That Magic: "low-key a token deck".',
    'Yawgfather\'s goldfish game with the stock deck: build Spirits for a few turns, then −4 for double strike and vigilance, so they swing and still guard Quintorius. If he dies at 1 loyalty, recast him for a fresh −4.'),
   ('Reanimate and flicker (value creatures)',
    'Bring back creatures with enter-the-battlefield effects and blink them. This is also how the alternate commander, Excava, is built.',
    ['Angel of Indemnity', 'Serra Paragon', 'Lorehold Archivist', 'Loran of the Third Path', 'Teleportation Circle', 'Eerie Interlude', 'Court of Ardenvale', 'Loyal Retainers'],
    ['lab-ls', 'cz735'],
    'Only EDHLAB builds mostly this way; most of these cards are already in the box. Card Kingdom says $50 isn\'t enough for a good Excava flicker deck.'),
   ('Faster start',
    'Cast Quintorius on turn 3, not 4: two-mana ramp, more cheap permanents, fewer pricey instants and sorceries, and cycling lands so you can play more lands without flooding.',
    ['Talisman of Conviction', 'Boros Signet', 'Fellwar Stone', 'Ornithopter of Paradise', 'Knight of the White Orchid', 'Liquimetal Torque', 'Shenanigans', 'Witch Enchanter', 'Sundown Pass', 'Sacred Foundry'],
    ['gf-ls', 'ck-ls', 'dt-ls', 'zg-ls', 'cp-ls', 'gtm-ls'],
    'Sundown Pass (32%) and Sacred Foundry (24%) are the most added lands. DeckTechsForDecks and ZombiesGoNomNom add Boros Signet and Talisman of Conviction for a turn-3 Quintorius.'),
   ('Keep the planeswalker alive',
    'Quintorius is a planeswalker, so he dies to attacks. Make him hard to kill, or copy his +1.',
    ['Deification', 'Onakke Oathkeeper', 'Elspeth\'s Talent', 'Rowan\'s Talent', 'Elspeth, Sun\'s Champion', 'Voice of Victory'],
    ['jm-ls', 'zg-ls', 'cp-ls', 'gtm-ls'],
    'Deification (hexproof, and he keeps 1 loyalty while you control a creature) is in two videos; ZombiesGoNomNom: with it "it\'s going to be really hard to kill Quintorius". Elspeth, Sun\'s Champion\'s −3 kills power 4 and up and spares your 3/2s.',
    'Guys That Magic: Voice of Victory "came in clutch" in several of their games, since the deck does its graveyard casting on its own turn.'),
  ],
  'avoid': [
   ('The death-trigger dragons', ['Ao, the Dawn Sky', 'Atsushi, the Blazing Sky'],
    'Their value comes when they die, and discard sends cards to the graveyard without dying. Cut by about two thirds of decks; Command Priority and Guys That Magic also call them too heavy for Boros.', ['edh-ls', 'ds-ls', 'lab-ls', 'cz735', 'cp-ls', 'gtm-ls', 'zg-ls']),
   ('A sweeper that kills your own team', ['Wave of Reckoning', 'Tragic Arrogance'],
    'Your board is mostly 3/2 Spirits. Wave of Reckoning is cut by 75% of decks and every guide and video that names cuts; Command Priority also cuts Tragic Arrogance ("we\'re making tokens").', ['gf-ls', 'ds-ls', 'lab-ls', 'cz735', 'cp-ls', 'gtm-ls', 'dt-ls', 'zg-ls']),
   ('Spirits only for the creature type', ['Drumbellower', 'Balefire Liege', 'Kami of Ancient Law', 'Remorseful Cleric', 'Spirit of Resilience', 'Augusta, Order Returned', 'Venerable Warsinger'],
    'They do little beyond being Spirits; Quintorius\'s −4 already gives the team vigilance. Guys That Magic on Kami of Ancient Law: "this is bad".', ['gf-ls', 'edh-ls', 'ds-ls', 'lab-ls', 'cz735', 'cp-ls', 'gtm-ls', 'dt-ls', 'zg-ls']),
   ('Cards that feed opponents', ['Secret Rendezvous', 'Naktamun Lorespinner'],
    'Three cards to an opponent, or a Wheel of Fortune that refills everyone. Secret Rendezvous is the #1 cut (81%) and is cut in all four videos with cut lists. Lorespinner rarely flips: casual players seldom empty their hands (Command Priority, Guys That Magic).', ['edh-ls', 'ds-ls', 'lab-ls', 'cz735', 'cp-ls', 'gtm-ls', 'dt-ls', 'zg-ls']),
   ('Narrow or taxing cards', ['White Orchid Phantom', 'Monologue Tax', 'Bitterthorn, Nissa\'s Animus', 'Claim Jumper', 'Lorehold Charm', 'Fateful Tempest', 'Perpetual Timepiece', 'Staff of the Storyteller'],
    'Land destruction and a tax effect don\'t advance the plan; Bitterthorn and Claim Jumper are slow ramp. Guys That Magic on Fateful Tempest after playtesting: three mana to "mill four lands and do nothing", since opponents vote "past"; Ark of Hunger replaces Perpetual Timepiece.', ['edh-ls', 'ds-ls', 'lab-ls', 'cp-ls', 'gtm-ls', 'dt-ls', 'zg-ls']),
   ('Expensive top end', ['Sun Titan'],
    'Command Priority: six mana for what cheaper recursion already does.', ['cp-ls']),
   ('Spells-matter and big flashback', ['Lorehold, the Historian', 'Advanced Reconstruction'],
    'Only about 12 instants and sorceries; heavy flashback empties the graveyard Quintorius needs.', ['ds-ls', 'lab-ls']),
  ],
  'split': [
   'Bag of Holding: a top-5 add and in MTGGoldfish\'s and EDHREC\'s lists, but Draftsim leaves it out because its graveyard exile is mandatory and can strand your own recursion.',
   'Flashback: EDHREC\'s Flashback theme (300 decks) adds Pursue the Past and the Flashback card; Draftsim and EDHLAB warn it eats the graveyard.',
   'The Command Zone also cuts Moonshaker Cavalry and Squee from the box; most others keep both.',
   'Flashback the card: Guys That Magic adds it (it makes a Spirit as the spell leaves the graveyard), against Draftsim\'s and EDHLAB\'s warning about flashback eating the graveyard.',
   'Balefire Liege, Karmic Guide and Spirit of Resilience: cut by several guides, but Yawgfather\'s stock-deck game leans on Balefire Liege and Karmic Guide.',
   'Big reanimation: ZombiesGoNomNom thinks Quintorius finally makes Boros reanimator workable and offers a ground-up "Quintorius Reanimation Chaser" list; everyone else stays with Spirits and discard.',
   'ZombiesGoNomNom found cuts "significantly harder" than usual because the box\'s card quality is high.',
  ],
  'alts': 'Excava, the Risen Past is barely played (101 decks vs 6,525 for Quintorius). EDHREC\'s guide cuts it, and Card Kingdom calls Quintorius "without a doubt the better option"; Jurassic Magic agrees, since Excava only returns mana value 3 or less.',
  'videos': [],
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
    ['Izzet Generatorium', 'Aether Refinery', 'Gonti\'s Aether Heart', 'Roil Cartographer', 'Aether Revolt', 'Electrosiphon', 'Tune the Narrative', 'Amped Raptor', 'Volatile Stormdrake', 'Galvanic Discharge', 'Aether Spike', 'Primal Prayers', 'Stone Idol Generator', 'HELIOS One'],
    ['cz653', 'ds-le', 'edh-le', 'ck-le', 'gg-le', 'gtm-le', 'tmg-le', 'yf-le'],
    'The top 6 adds are all energy cards (Izzet Generatorium 67%). Energy is EDHREC\'s biggest theme for Saheeli (1,321 decks). The Command Zone\'s 10 are nearly all energy. Guys That Magic calls Gonti\'s Aether Heart a "must have" and notes energy cards are cheap.',
    'Yawgfather\'s playtest of the stock deck: a hand of mana rocks stalls at two energy, so keep hands with an energy maker (Rogue Refiner and the like), and hold Saheeli until you have three energy so she copies the turn she lands.'),
   ('Bigger copy targets',
    'Saheeli\'s copy is a 5/5 haste that dies at end of turn, so pick things whose value is on entering or attacking, or that make more bodies. Gathering Games\' combo: Threefold Thunderhulk copied by Saheeli and Brudiclad, about nineteen tokens in one swing.',
    ['Threefold Thunderhulk', 'Brudiclad, Telchor Engineer', 'Blaster Hulk', 'The Motherlode, Excavator', 'Octomancer', 'Goldvein Hydra', 'Wurmcoil Engine', 'Balor', 'Magmatic Galleon', 'Coveted Jewel', 'Aurora Shifter', 'Behemoth of Vault 0', 'Robobrain War Mind', 'Garruk\'s Uprising', 'Esoteric Duplicator', 'Saheeli, the Sun\'s Brilliance', 'Hoarding Dragon'],
    ['gg-le', 'ds-le', 'cz653', 'edh-le', 'dt-le', 'pz-le', 'gtm-le', 'tmg-le'],
    'EDHREC\'s Clones theme plays Garruk\'s Uprising, Octomancer, Esoteric Duplicator and Threefold Thunderhulk about twice as often as other Saheeli decks. DeckTechsForDecks builds around value on entering and on dying, since the copy is sacrificed: Behemoth of Vault 0 and Balor trigger again when it goes, Wurmcoil Engine (Guys That Magic) leaves two 3/3s.'),
   ('Copy the copy-makers (no budget)',
    'Panzer MTG\'s 50-game list treats energy as a means, not the plan: three energy a turn is enough, so the weak energy cards go and the slots go to copy doublers. Copying Parallel Lives with Saheeli snowballs every turn.',
    ['Parallel Lives', 'Determined Iteration', 'Worldwalker Helm', 'Radiant Performer', 'Sundial of the Infinite', 'Lumbering Worldwagon', 'Simulacrum Synthesizer', 'Decoction Module'],
    ['pz-le', 'dt-le', 'gtm-le'],
    'Panzer calls Parallel Lives "the best card in the entire deck". Guys That Magic: Sundial of the Infinite ends the turn with Saheeli\'s sacrifice trigger on the stack, so you keep the 5/5 copies.'),
   ('Artifact tokens and Artificers',
    'Make and double artifact tokens, so Saheeli\'s energy flows and Artificer payoffs grow. EDHREC\'s non-budget list builds this way.',
    ['Adrix and Nev, Twincasters', 'Parallel Lives', 'Roaming Throne', 'Kappa Cannoneer', 'Arcbound Crusher', 'Simulacrum Synthesizer', 'Scrap Welder', 'Daretti, Scrap Savant', 'Jhoira, Weatherlight Captain', 'Padeem, Consul of Innovation', 'Encroaching Mycosynth', 'Etherium Sculptor', 'Foundry Inspector'],
    ['edh-le', 'gtm-le', 'tmg-le', 'cm-le'],
    'EDHREC\'s Artifacts theme (828 decks) and Artificers theme add Jhoira, Padeem and Oviya, Automech Artisan. ThatMillGuy\'s "classical" take is an artificer toolbox with cost reducers; he warns Saheeli pays only once a combat, so don\'t overbuild energy without other payoffs. Guys That Magic warns Encroaching Mycosynth exposes everything to artifact wipes.'),
   ('Blue value and big ETBs (Card Kingdom\'s take)',
    'Card Kingdom keeps the energy core but adds bounce-and-replay value and top-end blue threats rather than artifacts.',
    ['Clement, the Worrywort', 'Words of Wind', 'Tidespout Tyrant', 'Hullbreaker Horror', 'Doubling Season', 'Inexorable Tide', 'Eternal Witness'],
    ['ck-le'],
    'Card Kingdom also says energy and vehicles "lack natural synergy". Saheeli\'s Vehicles theme is tiny (34 decks); vehicles belong to the alternate commander, Pia Nalaar.'),
  ],
  'avoid': [
   ('The Thopter subtheme', ['Whirler Rogue', 'Sai, Master Thopterist', 'Stridehangar Automaton', 'Loyal Apprentice'],
    'Draftsim: "no one buys this precon to play around Thopter tokens". These go first when going big on energy or copies; Guys That Magic: the Thopters belong to the backup commander.', ['ds-le', 'edh-le', 'gg-le', 'ck-le', 'gtm-le', 'dt-le']),
   ('Legendary copy targets', ['Pia and Kiran Nalaar'],
    'Saheeli\'s copy keeps the original\'s legendary status, so the legend rule kills one of them. The #2 cut (63%).', ['gg-le', 'ds-le', 'edh-le', 'ck-le', 'gtm-le', 'dt-le']),
   ('Too pricey for the ramp', ['Triplicate Titan', 'Duplicant', 'Elder Gargaroth', 'Aethertide Whale'],
    'Six to nine mana, and not worth copying at that cost. Guys That Magic: Duplicant is removal you hold for turns waiting for a target.', ['ds-le', 'gg-le', 'ck-le', 'cz653', 'gtm-le', 'dt-le']),
   ('Slow mana sinks', ['Bootleggers\' Stash', 'Retrofitter Foundry', 'Conjurer\'s Closet', 'Midnight Clock', 'Cultivator\'s Caravan'],
    'Bootleggers\' Stash is the #1 cut (70%); Guys That Magic: "better on paper than in practice". Gathering Games: if you\'re using Retrofitter Foundry, "something has gone wrong".', ['edh-le', 'gg-le', 'ds-le', 'cz653', 'ck-le', 'gtm-le', 'dt-le']),
   ('The planeswalker Saheeli', ['Saheeli, Sublime Artificer'],
    'The deck doesn\'t make enough tokens for it; Guys That Magic: it can\'t gain loyalty, so it just dies.', ['ds-le', 'edh-le', 'gtm-le', 'dt-le']),
   ('Counters that help opponents, and tapped lands', ['Arcane Denial', 'Soul-Guide Lantern', 'Temple of Epiphany', 'Frostboil Snarl', 'Vineglimmer Snarl'],
    'Guys That Magic swaps Arcane Denial for Electrosiphon ("not here to help our opponents") and the tapped lands for bond lands and HELIOS One.', ['gtm-le', 'dt-le', 'cm-le']),
  ],
  'split': [
   'Counterspells: EDHREC\'s budget list and the Command Zone cut Disallow (and EDHREC Arcane Denial), but Electrosiphon and Tune the Narrative are top-10 adds, so the counters change rather than vanish.',
   'Thopters: EDHREC\'s small Artificers theme still plays Sai in 64% of decks, so the artifact-token angle keeps what the energy angle cuts.',
   'Ramp: Explosive Vegetation is cut by 44% of decks, while Cards Realm adds Cultivate and Kodama\'s Reach.',
   'How much energy: the Command Zone and EDHREC fill the deck with energy cards; Panzer MTG and DeckTechsForDecks cut the weaker ones (DeckTechsForDecks drops Aetherwind Basker, Era of Innovation, Attune with Aether and Whirler Virtuoso) because Saheeli only needs three a turn.',
   'Triplicate Titan and Bootleggers\' Stash: most cut them, but Yawgfather\'s playtest liked copying Triplicate Titan (the sacrificed copy leaves three 3/3 fliers) and found an Adaptive Omnitool plus Bootleggers\' Stash turn worth +14/+14.',
   'Jeskai vs Temur: Guys That Magic thinks white energy is faster, but this deck is better at copying.',
  ],
  'alts': 'Pia Nalaar, Chief Mechanic (the box\'s alternate, 305 decks) is the vehicles build; Saheeli has 4,215. Commander Mechanic\'s budget upgrade runs Pia: cut the non-artifact creatures and one-shot energy, add evasive artifact creatures (Kappa Cannoneer, Thought Monitor) and cost reducers, and keep Lightning Runner.',
  'videos': [],
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
    ['Varina, Lich Queen', 'Zul Ashur, Lich Lord', 'Diregraf Colossus', 'Death Baron', 'Diregraf Captain', 'Lord of the Undead', 'Undead Warchief', 'Wilhelt, the Rotcleaver', 'Necroduality', 'Zombie Apocalypse', 'Endless Ranks of the Dead', 'Tainted Adversary', 'Renewed Solidarity', 'Liliana, Dreadhorde General', 'Living Death'],
    ['cz654', 'fw', 'csi-em', 'ck-em', 'ds-em', 'gtm-em', 'dt-em', 'pz-em', 'cq-em', 'ss-em'],
    'Varina (51%), Zul Ashur (47%), Necroduality and Diregraf Colossus are top-5 adds and all in the Command Zone\'s 10. Zombies is EDHREC\'s biggest Temmet theme (1,016 decks). Wilhelt is in three videos (DeckTechsForDecks: it "should have been in this precon"); Guys That Magic says the same of Undead Warchief. Salubrious Snail: the box has too few small-token makers, and 4/4 tokens don\'t suit Temmet.'),
   ('Draw bursts to pump the team',
    'Temmet pumps on draws, so draw several cards right before combat and swing.',
    ['Kindred Discovery', 'Windfall', 'Titan of Littjara', 'Teferi\'s Ageless Insight', 'Distant Melody', 'Read the Runes', 'Graveborn Muse', 'God-Eternal Bontu', 'Brainstorm', 'Village Rites', 'Deadly Dispute', 'Military Intelligence', 'Black Market Connections', 'Keep Watch', 'Midnight Clock', 'Cephalid Coliseum', 'Stinging Study'],
    ['ck-em', 'ds-em', 'csi-em', 'cz654', 'gtm-em', 'cq-em', 'dt-em', 'pz-em', 'ss-em'],
    'CoolStuffInc counts only four burst-draw cards in the box, "a deficit"; Salubrious Snail agrees, and notes the box\'s draw (Midnight Reaper, Undead Augur) doesn\'t land before combat. EDHREC\'s Wheels theme plays Windfall in 80% of decks. Guys That Magic and the Commander\'s Quarters treat instant-speed draw as a combat trick: each card is +1/+1 to every Zombie. Panzer on Brainstorm: "you must play this card".',
    'Panzer MTG says Graveborn Muse "already lost me three games": at 5 life under attack, its upkeep draw killed him. He is on the verge of cutting it.'),
   ('Gravecrawler loops (Bracket 3)',
    'Rooftop Storm makes Zombies free; with Gravecrawler and a sacrifice outlet it loops for drain and cards. The Command Zone lists it as a separate "combo upgrade".',
    ['Rooftop Storm', 'Warren Soultrader', 'Carrion Feeder', 'Phyrexian Altar', 'Ashnod\'s Altar', 'Grimgrin, Corpse-Born', 'Bolas\'s Citadel'],
    ['cz654', 'ck-em', 'br-em', 'dt-em'],
    'Rooftop Storm is the #1 add (58%). EDHREC\'s Bracketeering article uses this package to move the deck from Bracket 2 to 3, so it\'s a power jump for our table. DeckTechsForDecks wins off the loop with the box\'s Wayward Servant or God-Eternal Oketra and suggests Varina as the commander instead.'),
   ('Discard and loot',
    'Lean into Temmet\'s loot: make Zombies or value whenever you discard. Draftsim builds this way; CoolStuffInc says discard only suits the alternate commander, Hashaton.',
    ['Cryptcaller Chariot', 'Monument to Endurance', 'Bone Miser', 'Cursecloth Wrappings', 'Frantic Search', 'Oskar, Rubbish Reclaimer', 'Master of Death'],
    ['ds-em'],
    'EDHREC\'s Discard theme (278 decks) plays Monument to Endurance and Cryptcaller Chariot well above average.'),
   ('Blue interaction',
    'Counterspells and instant-speed answers in place of the box\'s sorcery-speed removal.',
    ['Counterspell', 'Arcane Denial', 'An Offer You Can\'t Refuse', 'Anguished Unmaking', 'Supreme Verdict', 'Everything Comes to Dust', 'Long River\'s Pull'],
    ['fw', 'csi-em', 'gtm-em', 'pz-em', 'ss-em'],
    'Counterspell is added by 18% of decks. Salubrious Snail: "a blue deck that\'s vulnerable to removal and board wipes runs no counterspells". Guys That Magic swaps Dusk // Dawn for Supreme Verdict.'),
  ],
  'avoid': [
   ('Non-Zombie embalm and eternalize creatures', ['Timeless Dragon', 'Angel of Sanctions', 'Champion of Wits', 'Vizier of Many Faces'],
    'They don\'t get Temmet\'s pump or the lords. Timeless Dragon is cut by 80% of decks, the highest cut rate in any of our precons; Guys That Magic calls it "the most pointless card in the deck".', ['cz654', 'fw', 'csi-em', 'ds-em', 'gtm-em', 'cq-em', 'dt-em', 'ss-em']),
   ('Typal enablers in a deck that\'s already all Zombies', ['Maskwood Nexus'],
    'Its type-changing does nothing when nearly everything is a Zombie (74% cut); cut in every video that lists cuts.', ['fw', 'csi-em', 'ds-em', 'gtm-em', 'cq-em', 'dt-em', 'ss-em', 'cm-em']),
   ('Cycling that doesn\'t draw', ['Twisted Abomination'],
    'Swampcycling doesn\'t trigger Temmet, and the body is rarely worth casting (79% cut). The Commander\'s Quarters: "this one I really don\'t understand".', ['cz654', 'fw', 'csi-em', 'ds-em', 'cq-em', 'dt-em', 'ss-em', 'cm-em']),
   ('Keyword filler and slow graveyard cards', ['Never // Return', 'Gate to the Afterlife', 'God-Pharaoh\'s Gift', 'Commence the Endgame', 'Dread Summons', 'Cast Out'],
    'In the box for a word on the card more than for what it does. Draftsim calls Never // Return "abysmal"; Guys That Magic says Commence the Endgame "should probably be the first card you remove".', ['cz654', 'fw', 'csi-em', 'ds-em', 'gtm-em', 'cq-em', 'dt-em', 'ss-em', 'cm-em']),
   ('Amass and other "tall" Zombie makers', ['Lazotep Chancellor', 'Eternal Skylord', 'Dreadhorde Invasion'],
    'Amass grows one Army token instead of adding bodies, and Temmet wants many bodies (the Commander\'s Quarters). Guys That Magic: Eternal Skylord is five mana for flying on one Army.', ['cq-em', 'gtm-em', 'dt-em', 'ss-em']),
   ('Weak value cards', ['Priest of the Crossing', 'Corpse Augur', 'Liliana, Death\'s Majesty'],
    'Corpse Augur needs a sacrifice outlet the deck lacks (the Commander\'s Quarters); Priest of the Crossing is four mana for a few counters and Liliana is five mana for a 2/2 (Guys That Magic).', ['cq-em', 'gtm-em']),
   ('A wipe your own board survives poorly', ['Dusk // Dawn'],
    'Temmet\'s pumped team is usually too big for Dusk to be one-sided; Guys That Magic swaps it for Supreme Verdict.', ['fw', 'csi-em', 'ds-em', 'gtm-em', 'cm-em']),
   ('Tapped Deserts and mana rocks', ['Desert of the True', 'Desert of the Mindful', 'Desert of the Glorified', 'Commander\'s Sphere'],
    'They enter tapped and the deck has few desert payoffs; Card Kingdom would rather cast a turn-3 Zombie than a rock.', ['br-em', 'ck-em', 'ds-em', 'csi-em']),
  ],
  'split': [
   'Sacrifice: Draftsim drops the death and sacrifice cards (Corpse Augur, Fleshbag Marauder, Priest of the Crossing); the combo builds add sacrifice outlets instead.',
   'Discard: Draftsim leans into it, CoolStuffInc cuts it (Archfiend of Ifnir, Twisted Abomination) as Hashaton\'s theme.',
   'Land count: Draftsim and CoolStuffInc go down to 37 lands; Card Kingdom stays at 38 or more because of the constant discard.',
   'Gravecrawler: the combo builds loop it with Rooftop Storm, but Salubrious Snail cuts it: "with no sacrifice, this card just doesn\'t really do anything".',
   'Dreadhorde Invasion, On Wings of Gold and Rhet-Tomb Mystic: Panzer MTG keeps all three and Commander Mechanic the last two; DeckTechsForDecks cuts all three, and Guys That Magic and the Commander\'s Quarters also cut Dreadhorde Invasion.',
   'Murderous Rider: the Commander\'s Quarters cuts it ("not really good at either"), Panzer keeps it as removal on a Zombie.',
   'Who leads: DeckTechsForDecks thinks Varina is "probably a better" commander for this deck, and Commander Mechanic calls Temmet "one-note"; Salubrious Snail still respects Temmet as a different, draw-based Zombie deck.',
  ],
  'alts': 'Hashaton, Scarab\'s Fist (1,523 decks from this box) is a different, stronger deck: discard and reanimator with cEDH-style staples (Esper Sentinel, Rhystic Study, Psychic Frog). Card Kingdom says it isn\'t a budget build. Commander Mechanic rebuilds the box around Hashaton (discard outlets like Putrid Imp and Skirge Familiar, big ETB targets like Massacre Wurm), while Salubrious Snail says the box has too little discard to make him work. Varina (690) is also played as the commander.',
  'videos': [],
 },
 {
  'group': 'Our newer precons',
  'slug': 'revival-trance', 'name': 'Revival Trance: Terra', 'cmd': 'Terra, Herald of Hope', 'colors': 'R/W/B',
  'gist': 'Terra mills two and flies each combat, and when she hits a player you pay two to return a creature with power 3 or less. '
          'The box mixes that with big reanimation targets she can\'t return and a thin sacrifice theme. Terra builds cut the big creatures for small ones with strong enter effects plus ways to sacrifice them. Decks led by the box\'s other commander, Celes, are built differently; they have their own section below.',
  'themes': ['reanimator', 'graveyard', 'self-mill', 'aggro', 'aristocrats', 'extra-combats'],
  'angles': [
   ('Small creatures with big enter effects',
    'Fill the deck with creatures of power 3 or less whose value is on entering, so every Terra hit replays removal, card draw or another reanimation.',
    ['Alesha, Who Laughs at Fate', 'Karmic Guide', 'Joshua, Phoenix\'s Dominant', 'Sister Hospitaller', 'Redemption Choir', 'Braids, Arisen Nightmare', 'Loran of the Third Path', 'Primaris Eliminator', 'Ravenous Chupacabra', 'Havoc Eater', 'Angel of Sanctions', 'Seasoned Dungeoneer', 'Fury', 'Dihada, Binder of Wills', 'Pinnacle Monk', 'Witch Enchanter'],
    ['cz677', 'gz-rt', 'dt-rt'],
    'Joshua (45%), Alesha, Who Laughs at Fate (44%) and Karmic Guide (41%) are the top 3 adds; Alesha and Braids are in the Command Zone\'s and Grazzet\'s lists. The Command Zone counts 14 creatures in the box that Terra can\'t return.'),
   ('Sacrifice them yourself',
    'Creatures that sacrifice themselves (edicts that hit you too) and free outlets, so you choose when a value creature goes back to the graveyard for Terra.',
    ['Accursed Marauder', 'Plaguecrafter', 'Fleshbag Marauder', 'Merciless Executioner', 'Demon\'s Disciple', 'Priest of Forgotten Gods', 'Viscera Seer', 'Selfless Spirit', 'Luminous Broodmoth', 'Ruthless Technomancer', 'Ashnod\'s Altar'],
    ['dt-rt', 'gz-rt', 'yf-rt'],
    'Selfless Spirit (24%), Luminous Broodmoth (23%) and Accursed Marauder (21%) are top-20 adds. Grazzet counts only two sacrifice effects in the box. Yawgfather\'s stock-deck loop: Shadow, Mysterious Assassin sacrifices Solemn Simulacrum on combat damage, then Terra returns it.'),
   ('More combats and double strike',
    'Each extra combat or double-strike hit is another mill and another reanimation.',
    ['Aurelia, the Warleader', 'Fear of Missing Out', 'Blade Historian', 'Professional Face-Breaker'],
    ['dt-rt', 'gz-rt', 'cz677'],
    'Aurelia (32%) has exactly 3 power, so Terra can return her. Fear of Missing Out (27%) is in all three upgrade videos.'),
   ('Fill the graveyard on purpose',
    'Terra\'s mill is random; discard outlets and entomb effects put the right creature there.',
    ['Faithless Looting', 'Thrill of Possibility', 'Buried Alive', 'Ripples of Undeath', 'Stitcher\'s Supplier'],
    ['gz-rt', 'dt-rt', 'ds-rt'],
    'Faithless Looting (33%) and Buried Alive (32%) are top-10 adds.'),
  ],
  'avoid': [
   ('Big creatures Terra can\'t return', ['Ruin Grinder', 'Angel of the Ruins', 'Combustible Gearhulk', 'Sepulchral Primordial', 'Flayer of the Hatebound', 'Archfiend of Depravity', 'Umaro, Raging Yeti', 'Sun Titan'],
    'Power above 3, so the commander can\'t bring them back. Ruin Grinder is the #1 cut (80%); Angel of the Ruins and Combustible Gearhulk are cut by about two thirds of decks.', ['cz677', 'gz-rt', 'dt-rt']),
   ('Off-theme legends', ['Setzer, Wandering Gambler', 'Interceptor, Shadow\'s Hound', 'Sabin, Master Monk', 'Strago and Relm', 'Edgar, Master Machinist', 'Kefka, Dancing Mad', 'Cyan, Vengeful Samurai'],
    'In the box for Final Fantasy VI flavour. Grazzet: Setzer\'s vehicles and coin flips don\'t fit, Edgar needs more artifacts, and Strago and Relm and Kefka belong in a theft deck.', ['gz-rt', 'dt-rt', 'ds-rt']),
   ('Weak reanimation and removal', ['Coin of Fate', 'The Falcon, Airship Restored', 'Espers to Magicite', 'Crackling Doom', 'Legions to Ashes', 'Tragic Arrogance'],
    'Coin of Fate lets an opponent pick what you get back (Grazzet); the Command Zone never cast Espers to Magicite in their game, and Crackling Doom hits the biggest creature, not the flyer that can block Terra.', ['cz677', 'gz-rt', 'dt-rt', 'ds-rt']),
   ('Slow mana', ['Commander\'s Sphere', 'Anger'],
    'The Command Zone: two-mana ramp is what a three-mana commander wants; Anger needs a Mountain, and the box has six.', ['cz677', 'gz-rt']),
  ],
  'split': [
   'Keep Terra or not: the Command Zone, Grazzet and DeckTechsForDecks build around her; Draftsim swaps to Celes and keeps the big creatures (Angel of the Ruins, Combustible Gearhulk, Sepulchral Primordial, Archfiend of Depravity) that the others cut. See the Celes section.',
   'The sacrifice theme: for Terra, DeckTechsForDecks and Grazzet build it up with self-sacrificing edict creatures; the Celes builds either cut it (Draftsim, UNIVERSES BEYOND) or turn it into persist combos (the Commander Pod).',
   'Graveyard hate is the deck\'s weak spot: Yawgfather says to go after green, white and black players who can exile graveyards.',
  ],
  'alts': 'Celes, Rune Knight (832 decks from this box) is the alternate; Terra has 7,436. On EDHREC, 80% of all Terra decks also play Celes. The Commander Pod ran the box with Terra for its first four league games and won half of them, "super shocked by how resilient the deck is", before switching to Celes.',
  'also': ['cp-rt'],
  'videos': [],
 },
 {
  'group': 'Our newer precons',
  'slug': 'revival-trance-celes', 'precon': 'revival-trance', 'mode': 'commander',
  'name': 'Revival Trance: Celes', 'cmd': 'Celes, Rune Knight', 'colors': 'R/W/B',
  'gist': 'Celes wheels as she enters (discard any number, draw that many plus one), and puts a +1/+1 counter on each of your creatures whenever creatures come back from the graveyard. '
          'Celes decks split three ways: persist loops for combo (her counter cancels persist\'s −1/−1, so a persist creature with a sacrifice outlet loops forever), a "fair" Bracket 3 reanimator that goes tall with counters, and Draftsim\'s big reanimator. All re-trigger her wheel by blinking her.',
  'themes': ['reanimator', 'combo', 'p1-p1-counters', 'graveyard', 'aristocrats', 'blink'],
  'angles': [
   ('Persist loops (the combo build)',
    'Celes plus a persist creature plus a free sacrifice outlet loops forever; a drain or damage payoff wins. The Commander Pod\'s lines: Murderous Redcap with Saw in Half, or any persist creature with Goblin Bombardment.',
    ['Murderous Redcap', 'Putrid Goblin', 'Persist', 'Saw in Half', 'Goblin Bombardment', 'Viscera Seer', 'Umbral Collar Zealot', 'Blood Artist', 'Lively Dirge'],
    ['cp-rt'],
    'Combo is EDHREC\'s second Celes theme (686 decks), something only 220 Terra decks are tagged with. Murderous Redcap is in 61% of all Celes decks and Putrid Goblin in 52%. The Commander Pod calls Lively Dirge "probably one of the most powerful cards in the deck".',
    'The Commander Pod\'s precon league: the deck won half its first four games under Terra, then "has not lost a game" in its first weeks under Celes, and her wheel drew the whole deck. Caveat: the persist and sacrifice pieces "do very little" until you switch to Celes.'),
   ('Re-trigger the wheel',
    'Blink or flicker Celes to wheel again: each time you discard reanimation targets and dig for the next piece.',
    ['Ephemerate', 'Cloudshift', 'Conjurer\'s Closet', 'Touch the Spirit Realm', 'Mardu Siegebreaker', 'Sevinne\'s Reclamation'],
    ['ub-rt', 'cp-rt'],
    'Ephemerate is in 55% of Celes decks and Cloudshift in 49%; Blink is a Celes theme (228 decks). UNIVERSES BEYOND: Conjurer\'s Closet lets her wheel every turn. The Commander Pod: Mardu Siegebreaker exiling Celes gives three wheels on one attack.'),
   ('Fair reanimator that goes tall (Bracket 3)',
    'UNIVERSES BEYOND skips the persist combos ("very boring") and builds to bring back several creatures at once, each return pumping the whole team. Terra stays in the 99 as another engine.',
    ['Smile at Death', 'Marshal\'s Anthem', 'Ever After', 'Coiling Rebirth', 'Unearth', 'Ratadrabik of Urborg', 'Flowering of the White Tree', 'Merry, Esquire of Rohan', 'Syr Konrad, the Grim', 'Drana and Linvala', 'United Battlefront', 'Mirror of Galadriel', 'Terra, Herald of Hope'],
    ['ub-rt'],
    'Terra is in 38% of all Celes decks. UNIVERSES BEYOND calls Ratadrabik "an auto include"; Smile at Death returns two small creatures every upkeep, triggering Celes each time.',
    'UNIVERSES BEYOND has played this build four times and won two: "incredibly fun".'),
   ('Big reanimator (Draftsim\'s take)',
    'Draftsim thinks Celes suits the box\'s big reanimation cards better than Terra does: her wheel dumps big targets in the graveyard and digs for mass reanimation.',
    ['Reanimate', 'Animate Dead', 'Necromancy', 'Victimize', 'Entomb', 'Buried Alive', 'Breach the Multiverse', 'Living Death', 'Incarnation Technique', 'Too Greedily, Too Deep', 'Will of the Abzan', 'Archon of Cruelty', 'Kroxa and Kunoros', 'Summon: Bahamut', 'Toxic Deluge'],
    ['ds-rt'],
    'Reanimate is in 77% of Celes decks, Animate Dead 56%, Victimize 43%, Entomb 42%. Draftsim made 23 changes, including cutting Terra.'),
  ],
  'avoid': [
   ('Sacrifice payoffs in a fair build', ['Pitiless Plunderer', 'Morbid Opportunist', 'Shadow, Mysterious Assassin'],
    'Draftsim: the sacrifice theme "barely exists"; UNIVERSES BEYOND: "we\'re not going to be doing much sacrificing". The combo build keeps Pitiless Plunderer.', ['ds-rt', 'ub-rt']),
   ('Big, random or narrow cards', ['Ruin Grinder', 'Umaro, Raging Yeti', 'Meteor Golem', 'Gogo, Mysterious Mime', 'Palace Jailer', 'Angel of the Ruins'],
    'UNIVERSES BEYOND: Umaro\'s mode is random, Ruin Grinder refills opponents too, Palace Jailer is "the weirdest inclusion ever". Draftsim also cuts Ruin Grinder and Meteor Golem.', ['ub-rt', 'ds-rt']),
   ('One-shot card draw', ['Laughing Mad', 'Night\'s Whisper', 'Big Score'],
    'UNIVERSES BEYOND: Celes already gives card selection; spend the slots on reanimation.', ['ub-rt']),
  ],
  'split': [
   'Persist combos: the Commander Pod builds Celes around them; UNIVERSES BEYOND calls them "very boring" and builds the fair version for a Bracket 2-3 table.',
   'Summon: Esper Valigarmanda and Phoenix Down: UNIVERSES BEYOND cuts Valigarmanda as unreliable; the Commander Pod says it "overperformed" and kept Phoenix Down after playing it.',
   'Angel of the Ruins: Draftsim keeps it as a big target; UNIVERSES BEYOND doesn\'t know "why this is in this deck".',
   'Terra in the 99: UNIVERSES BEYOND keeps her as a second engine; Draftsim cuts her.',
  ],
  'alts': 'Most EDHREC Celes decks (13,115) weren\'t built from the box; they look like combo decks, with Dark Ritual (46%) and tutors among their staples.',
  'videos': [],
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
    ['Watcher of the Spheres', 'Ornithopter of Paradise', 'Archetype of Imagination', 'Kastral, the Windcrested', 'Wingmate Roc', 'The Lord of the Eagles', 'Air Nomad Legacy', 'Thraben Watcher', 'Serra the Benevolent', 'Donal, Herald of Wings', 'Selfless Spirit', 'Unbreakable Formation', 'Serra\'s Emissary'],
    ['edh-ff', 'cgb-ff', 'cr-ff', 'wit-ff', 'scg-ff', 'tm-ff'],
    'Watcher of the Spheres is the #2 add (22%) and in two videos; Wizard\'s Institute of Technology says it "should have been in the precon". Flying is the biggest theme on both Isperia and Kangee decks. Wizard\'s Institute goes up from 7 Birds to 17 and cuts the 6- and 7-drop Sphinxes (average mana value 3.75 to 3.45).',
    'Wizard\'s Institute\'s goldfish games: a turn-6 Storm Herd with Gravitational Shift and Kangee\'s +2/+0 was lethal; one mulligan showed the risk of hands with no Plains.'),
   ('A different flyer commander',
    'Isperia only rewards being attacked, so guides swap her out: Kangee (Cardgamebase, Wizard\'s Institute of Technology), Dragonlord Ojutai (EDHREC\'s guide, hexproof while untapped), or Errant and Giada.',
    ['Kangee, Sky Warden', 'Dragonlord Ojutai', 'Errant and Giada'],
    ['cgb-ff', 'edh-ff', 'wit-ff'],
    'EDHREC: 724 decks from this box run Kangee and 704 Isperia; 189 run Errant and Giada and 158 Ojutai. Wizard\'s Institute: Isperia is passive, "we don\'t want our opponents attacking us".'),
   ('Cheap, steady card draw',
    'Replace the expensive Sphinxes and X-spells with cheap draw that doesn\'t need you to be attacked.',
    ['Reconnaissance Mission', 'Loyal Drake', 'Military Intelligence', 'Keep Watch', 'Wizard Class', 'Court of Grace', 'Dream Trawler', 'Medomai the Ageless'],
    ['edh-ff', 'cgb-ff', 'cr-ff', 'tm-ff', 'scg-ff', 'wit-ff'],
    'Reconnaissance Mission (9%) and Loyal Drake (8%) are the cheap draw most often added. Wizard Class is in two videos (Isperia fills your hand, so no hand size limit).'),
   ('Make them attack you (keep Isperia)',
    'Keep Isperia and lean in: removal that hands the opponent a creature, things that force attacks, so they swing at you and you draw.',
    ['Crib Swap', 'Pongify', 'Rapid Hybridization', 'Valorous Stance', 'Bloodthirsty Blade', 'Pursued Whale'],
    ['cr-ff', 'tm-ff', 'scg-ff'],
    'Cards Realm and Triple Mango Threat build this way; Star City Games keeps the box\'s Angler Turtle and Bident of Thassa for the same reason.'),
   ('Control and pillow fort',
    'Wraths, tax effects and life gain, then win late. Nerds of the West rebuilt the deck this way after testing it, with Approach of the Second Sun as the finish.',
    ['Propaganda', 'Ghostly Prison', 'Windborn Muse', 'Magus of the Moat', 'Supreme Verdict', 'Austere Command', 'Approach of the Second Sun', 'Alhammarret\'s Archive', 'Sunset Revelry', 'Spirit Link', 'Dovin\'s Veto'],
    ['nw-ff', 'wit-ff'],
    'Control decks (44) play Supreme Verdict 68% vs 28% for all Isperia decks; Pillow Fort decks (27) Ghostly Prison and Propaganda 63% vs about 20%. Wizard\'s Institute adds Propaganda, Windborn Muse and Magus of the Moat to its flyers deck.',
    'Nerds of the West played the stock deck on stream first: too much single-target removal and three counterspells with little card draw "just leads to a bad time and being overrun".'),
  ],
  'avoid': [
   ('Creatures that don\'t fly', ['Angler Turtle', 'Hanged Executioner'],
    'Angler Turtle is the #1 cut (59%): no flying and nothing for this plan. Wizard\'s Institute of Technology won\'t pay seven mana for a creature that doesn\'t fly.',['edh-ff', 'cgb-ff', 'wit-ff']),
   ('The expensive Sphinxes and ten-drops', ['Sharding Sphinx', 'Diluvian Primordial', 'Storm Herd', 'Sphinx of Enlightenment', 'Inspired Sphinx'],
    'Slow and costly for what they do; Sphinx of Enlightenment also gives an opponent a card.', ['edh-ff', 'cgb-ff', 'cr-ff', 'wit-ff', 'nw-ff']),
   ('Removal that needs them to attack', ['Condemn', 'Soul Snare'],
    'Dead without forced combat, and it punishes the attacks Isperia wants.', ['edh-ff', 'cr-ff', 'nw-ff', 'wit-ff']),
   ('Slow artifact ramp', ['Sky Diamond', 'Pilgrim\'s Eye', 'Cartographer\'s Hawk'],
    'Cards Realm: Hawk-style ramp is too slow.', ['cr-ff', 'cgb-ff', 'wit-ff']),
   ('Clunky cards', ['Vow of Duty', 'Gideon Jura', 'Aven Gagglemaster', 'Winged Words', 'Skyscanner'],
    'Vow of Duty is cut by half of all decks; Gideon is mediocre in multiplayer. Wizard\'s Institute also cuts one-shot draw (Winged Words, Skyscanner, Sphinx\'s Revelation) for repeatable draw.', ['edh-ff', 'cgb-ff', 'cr-ff', 'wit-ff', 'nw-ff']),
   ('Single-target answers in a deck short on cards', ['Absorb', 'Negate', 'Disenchant', 'Banishing Light'],
    'Nerds of the West cut these after testing: one-for-one answers with little draw leave you behind.', ['nw-ff', 'cr-ff']),
   ('Tapped lands', ['Meandering River', 'Coastal Tower'],
    'Weaker than even a gate; replace once better duals are in.', ['cgb-ff', 'cr-ff', 'nw-ff']),
  ],
  'split': [
   'Being attacked: EDHREC\'s guide and Wizard\'s Institute of Technology drop the forced-combat package and Isperia with it; Cards Realm and Triple Mango Threat keep Isperia and add ways to make opponents attack.',
   'Counterspells: Cards Realm and Nerds of the West cut single-target counters (Absorb) as card disadvantage; Cardgamebase adds Mana Drain, and Dovin\'s Veto is a 10% add.',
   'Storm Herd and Windreader Sphinx: guides cut the ten-drops, but Wizard\'s Institute keeps Storm Herd and Windreader Sphinx as its finishers.',
   'Swords to Plowshares: Nerds of the West cut it with the rest of the single-target removal; no other source does.',
   'Lands: Cards Realm goes down to 35, Wizard\'s Institute to 38, Cardgamebase up to 42.',
  ],
  'alts': 'Isperia isn\'t even the most-played commander from her own box (see above).',
  'videos': [],
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
    ['Death Baron', 'Diregraf Colossus', 'Necroduality', 'Endless Ranks of the Dead', 'Wilhelt, the Rotcleaver', 'Undead Warchief', 'Lord of the Undead', 'Cleaver Skaab', 'Hordewing Skaab', 'Noosegraf Mob', 'Kindred Discovery', 'Herald\'s Horn', 'Geralf, Visionary Stitcher'],
    ['cgb-gd', 'scg-gd', 'tm-gd', 'sq-gd', 'wit-gd'],
    'Death Baron (31%), Diregraf Colossus and Necroduality are top-5 adds. Zombies is the biggest theme (789 decks). Wilhelt is in all three upgrade videos; Star City Games calls Endless Ranks of the Dead a staple.'),
   ('Value Zombies on a loop',
    'Fewer, better Zombies that do something when they enter or die, recast from the graveyard every turn. EDHREC\'s guide trades width for this.',
    ['Undead Butler', 'Crow of Dark Tidings', 'Forgotten Creation', 'Tomebound Lich', 'Corpse Augur', 'Ravenous Rotbelly', 'Tainted Adversary', 'Overcharged Amalgam', 'Secrets of the Dead', 'Patriarch\'s Bidding', 'Accursed Marauder', 'Headless Rider'],
    ['edh-gd', 'tm-gd', 'sq-gd'],
    'Headless Rider (21%) and Accursed Marauder (20%) are the most added of these; Headless Rider is also in two videos.'),
   ('Fill the graveyard on purpose',
    'Self-mill and Entomb effects to put the right Zombie in the yard for Gisa and Geralf.',
    ['Stitcher\'s Supplier', 'Vile Entomber', 'Corpse Connoisseur', 'Buried Alive', 'Repository Skaab', 'Forbidden Alchemy'],
    ['edh-gd', 'cgb-gd', 'scg-gd'],
    'EDHREC\'s Mill theme plays Stitcher\'s Supplier 58% vs 37% for all Gisa and Geralf decks. Squirrel commander wants to choose what goes to the graveyard, not mill at random (so it cuts Geralf\'s Mindcrusher).'),
   ('Gravecrawler loops (Bracket 3)',
    'Rooftop Storm makes Zombies free; Gravecrawler plus a free sacrifice outlet then loops for drain and cards.',
    ['Rooftop Storm', 'Gravecrawler', 'Carrion Feeder', 'Ghoulcaller Gisa', 'Nantuko Husk', 'Ashnod\'s Altar', 'Phyrexian Altar', 'Warren Soultrader', 'Plague Belcher'],
    ['cgb-gd', 'edh-gd', 'scg-gd', 'tm-gd', 'sq-gd'],
    'Rooftop Storm is the #1 add (53%), Gravecrawler #2. EDHREC\'s Combo decks play Gravecrawler 92% and Phyrexian Altar 54% (vs 12%). Star City Games and Triple Mango Threat both add Carrion Feeder: the deck needs sacrifice outlets so Zombies with enter effects can be recast. Star City Games warns Rooftop Storm and Living Death can feel "salty" to new players.'),
   ('Blue interaction',
    'Instant-speed counters and answers instead of the box\'s sorcery-speed removal; Squirrel commander adds counters mainly to stop graveyard exile (Rest in Peace and the like), the deck\'s real weakness.',
    ['Counterspell', 'Dimir Charm', 'Fact or Fiction', 'Negate'],
    ['cgb-gd', 'edh-gd', 'tm-gd', 'sq-gd'],
    'Counterspell is added by 19% of decks.'),
  ],
  'avoid': [
   ('Narrow or clunky removal', ['Murder', 'Cruel Revival', 'Syphon Flesh', 'Undermine'],
    'Outclassed by removal on Zombies you can recast (Ravenous Rotbelly). Squirrel commander also cuts Feed the Swarm for being sorcery speed.', ['edh-gd', 'cgb-gd', 'sq-gd']),
   ('Slow or expensive cards', ['Unstable Obelisk', 'Josu Vess, Lich Knight', 'Gravespawn Sovereign', 'Geralf\'s Mindcrusher', 'Spark Reaper', 'Grimoire of the Dead', 'Army of the Damned', 'Overseer of the Damned'],
    'Unstable Obelisk is the #1 cut (64%); Josu\'s value is a ten-mana kicker. Squirrel commander: Army of the Damned is eight mana that should win the game and doesn\'t.', ['edh-gd', 'cgb-gd', 'sq-gd']),
   ('Low-impact creatures', ['Withered Wretch', 'Lazotep Reaver', 'Lotleth Giant', 'Vela the Night-Clad', 'Liliana\'s Devotee'],
    'Cut on power level; Vela and Liliana\'s Devotee aren\'t Zombies, so Gisa and Geralf can\'t cast them from the graveyard.', ['cgb-gd', 'edh-gd', 'sq-gd']),
   ('Off-plan card draw', ['Vampiric Rites', 'Pilfered Plans', 'Deep Analysis', 'Wayfarer\'s Bauble'],
    'Deep Analysis and Wayfarer\'s Bauble are cut by about half of decks. Squirrel commander drops one-off draw (Deep Analysis, Distant Melody, Pilfered Plans).', ['edh-gd', 'cgb-gd', 'sq-gd']),
  ],
  'split': [
   'Lords: EDHREC\'s guide cuts Cemetery Reaper and Lord of the Accursed (no enter or death value, "we\'re not going wide"); Cardgamebase adds Death Baron, Undead Warchief and Lord of the Undead, and Star City Games calls the three box lords the core of the deck.',
   'Crippling Fear: Star City Games praises it as a one-sided wipe (name Zombie); Squirrel commander cuts it as "too small".',
   'Josu Vess, Grimoire of the Dead and Lotleth Giant: cut by the guides, but Wizard\'s Institute of Technology\'s how-to-play video uses all three (cast Josu early, recur him kicked later).',
   'Vampiric Rites: Star City Games and Wizard\'s Institute value it as one of the box\'s few sacrifice outlets; EDHREC\'s guide and Cardgamebase cut it.',
  ],
  'alts': 'Commander swaps are common: The Scarab God (470 decks from this box) and Wilhelt, the Rotcleaver (416) against 2,432 for Gisa and Geralf. Star City Games also suggests Wilhelt as a commander option.',
  'videos': [('xm5W4i0b-ls', 'Grave Danger Flavourful Upgrade Guide & Combo', 'Prospo, EDH Scout')],
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
    ['Disrupt Decorum', 'Shiny Impetus', 'Parasitic Impetus', 'Bloodthirsty Blade', 'Agitator Ant', 'Vengeful Ancestor', 'Spectacular Showdown', 'Bothersome Quasit', 'Baeloth Barrityl, Entertainer', 'Komainu Battle Armor', 'Goblin Spymaster', 'Frenzied Saddlebrute', 'Curse of Opulence', 'Alexios, Deimos of Kosmos', 'Rite of the Raging Storm'],
    ['edh-ci', 'cr-ci', 'scg-ci', 'tm-ci', 'jm-ci'],
    'Disrupt Decorum is the #1 add (39%) and in two videos. Forced Combat is by far the biggest theme (663 decks). Bothersome Quasit and Vengeful Ancestor are each in two videos; Star City Games\' advice is to "lean into" goad.'),
   ('Re-trigger Kardur',
    'Blink, copy or recast him for a fresh goad every turn.',
    ['Conjurer\'s Closet', 'Blade of Selves', 'Helm of the Host', 'Sword of Hearth and Home', 'Mirage Phalanx', 'Golden Argosy', 'Sanctum of Eternity', 'Flamerush Rider', 'Undying Malice', 'Supernatural Stamina', 'Feign Death', 'Jaxis, the Troublemaker'],
    ['edh-ci', 'cr-ci', 'scg-ci', 'jm-ci', 'dt-ci'],
    'Conjurer\'s Closet is the #2 add (39%) and in three videos; Star City Games calls it "insanely good with your commander". EDHREC\'s Blink decks play it in 88%. DeckTechsForDecks: Blade of Selves copies of Kardur die to the legend rule while attacking, and each death drains.'),
   ('Paid when they die',
    'Draw or drain off the creatures that die in the fights you start.',
    ['Morbid Opportunist', 'Harvester of Souls', 'Karazikar, the Eye Tyrant', 'Blood Artist', 'Garna, Bloodfist of Keld', 'Death Tyrant', 'Calculating Lich', 'Blast-Furnace Hellkite', 'Emberwilde Captain', 'Slaughter Specialist'],
    ['edh-ci', 'cr-ci', 'scg-ci', 'tm-ci', 'jm-ci', 'dt-ci'],
    'Morbid Opportunist (26%) is the most added, and in two videos; Karazikar is in three. EDHREC\'s Aristocrats decks add sac outlets (Viscera Seer, Goblin Bombardment).'),
   ('Give them creatures to fight with',
    'Hand opponents bodies, then force them to attack each other with them. DeckTechsForDecks calls it a "group hug" deck that ends with you the last one standing.',
    ['Clackbridge Troll', 'Hunted Horror', 'Hunted Dragon', 'Varchild, Betrayer of Kjeldor', 'Akroan Horse', 'Life of the Party', 'Captive Audience'],
    ['tm-ci', 'dt-ci', 'jm-ci'],
    'Triple Mango Threat would rather give opponents more creatures to attack with than run spell payoffs; every attacker that dies drains them through Kardur.'),
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
    'The deck doesn\'t cast enough instants and sorceries. Thermo-Alchemist is the #1 cut (58%).', ['edh-ci', 'cr-ci', 'tm-ci']),
   ('Expensive top end', ['Explosion of Riches', 'Magmatic Force', 'Sunbird\'s Invocation', 'Scythe Specter', 'Sepulchral Primordial', 'Reign of the Pit', 'Breath of Malfegor', 'Combustible Gearhulk', 'Kaervek the Merciless'],
    'Cut to lower the curve; Scythe Specter also needs to connect. Triple Mango Threat: powerful cards, but not for this deck.', ['edh-ci', 'cr-ci', 'tm-ci']),
   ('Gifts to opponents', ['Coveted Jewel'],
    'Cards Realm: it can hand an opponent three cards and three mana. Cut by 51%.', ['cr-ci']),
   ('Slow or off-plan cards', ['Stensia Bloodhall', 'Titan Hunter', 'Profane Command', 'Hate Mirage'],
    'EDHREC\'s guide: Stensia Bloodhall "has no business being in a multiplayer deck".', ['edh-ci']),
  ],
  'split': [
   'Coveted Jewel: Cards Realm calls it a good fit for a goad deck (opponents attack each other to steal it) but risky; half of all decks cut it.',
   'Sepulchral Primordial: EDHREC\'s guide cuts it; Cards Realm keeps it as a Kardur-style enter-the-battlefield target.',
   'Profane Command and Hate Mirage: EDHREC\'s guide cuts them; Star City Games highlights both (Hate Mirage "massively underplayed", Profane Command good for closing games).',
   'Mana Geyser: Star City Games likes it for the deck\'s expensive cards but gives it a "salt warning" for casual tables.',
  ],
  'alts': 'Kaervek the Merciless (178 decks from this box) is the main swap; Kardur has 1,444. Triple Mango Threat cuts Kaervek from the 99.',
  'videos': [],
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
    ['Thrakkus the Butcher', 'Lathliss, Dragon Queen', 'Utvara Hellkite', 'Dragonborn Champion', 'Old Gnawbone', 'Ryusei, the Falling Star', 'Scourge of the Throne', 'Earthquake Dragon', 'Territorial Hellkite', 'Chaos Dragon', 'Terror of the Peaks', 'Sarkhan\'s Triumph'],
    ['edh-dd', 'cgb-dd', 'nw-dd', 'tm-dd', 'scg-dd', 'jm-dd'],
    'Thrakkus (48%) and Lathliss (45%) are the top 2 adds; Thrakkus is also in two videos (Triple Mango Threat: with Atarka it quadruples damage), Lathliss in two. EDHREC\'s guide went from 21 to 24 Dragons and wanted 30.'),
   ('Cheap ramp and cost reduction',
    'Dragons cost five or more, so two- and three-mana ramp and Dragon cost reducers.',
    ['Scaled Nurturer', 'Goblin Anarchomancer', 'Kodama\'s Reach', 'Rampant Growth', 'Ganax, Astral Hunter', 'Jade Orb of Dragonkind', 'Orb of Dragonkind', 'Urza\'s Incubator', 'Monster Manual', 'Dracogenesis'],
    ['edh-dd', 'cgb-dd', 'nw-dd', 'tm-dd', 'scg-dd', 'jm-dd'],
    'Five of the top 10 adds are ramp. EDHREC\'s guide calls cheap ramp "especially important"; Kodama\'s Reach is in two videos. Nerds of the West cut from 40 lands to 36 and leaned on cheap ramp creatures instead.'),
   ('Haste and extra combats',
    'Double strike is best twice: haste so a new Dragon swings at once, and extra combat steps.',
    ['Rhythm of the Wild', 'Xenagos, God of Revels', 'Fires of Yavimaya', 'Carnelian Orb of Dragonkind', 'Hellkite Charger', 'Aggravated Assault', 'Lightning Greaves', 'Goldspan Dragon'],
    ['cgb-dd', 'nw-dd', 'jm-dd', 'scg-dd', 'tm-dd'],
    'EDHREC\'s Extra Combats decks play Aggravated Assault 64% (vs 13%) and Hellkite Charger 75% (vs 28%). Carnelian Orb is in three videos. Jurassic Magic calls Xenagos "the highest recommended card"; its infinite-combat line is Aggravated Assault or Hellkite Charger plus Old Gnawbone\'s treasure.',
    'Nerds of the West played the stock deck on stream first: "big and strong doesn\'t mean good"; it was too slow and got outpaced "by even the slowest midrange", so haste was one of their four fixes.'),
   ('Card flow',
    'The box has little draw; add draw that scales with big creatures.',
    ['Return of the Wildspeaker', 'Realmwalker', 'Rishkar\'s Expertise', 'Greater Good', 'Court of Bounty', 'The Great Henge'],
    ['edh-dd', 'cgb-dd', 'tm-dd', 'scg-dd', 'jm-dd', 'nw-dd'],
    'Return of the Wildspeaker is added by 20% of decks; Rishkar\'s Expertise and Greater Good are in two videos each.'),
   ('Get through and stay alive',
    'Evasion for the ground Dragons and protection from wipes.',
    ['Bower Passage', 'Kessig Wolf Run', 'Wrap in Vigor', 'Heroic Intervention'],
    ['edh-dd', 'cgb-dd', 'nw-dd', 'jm-dd'],
    'Kessig Wolf Run (16%) is the most added utility land. Nerds of the West calls Bower Passage "the best card put into this deck".'),
  ],
  'avoid': [
   ('Weak small Dragons', ['Furnace Whelp', 'Rapacious Dragon', 'Dragonkin Berserker', 'Dragon Mage', 'Demanding Dragon'],
    'Furnace Whelp is the #1 cut (78%): "4 mana for a 2/2 is not keepable". Cut in both videos that list cuts.', ['edh-dd', 'cgb-dd', 'nw-dd', 'tm-dd']),
   ('Non-Dragon creatures', ['Loaming Shaman', 'Drumhunter', 'Draconic Disciple'],
    'Room for more Dragons.', ['edh-dd', 'cgb-dd', 'nw-dd']),
   ('Some of the removal', ['Provoke the Trolls', 'Sweltering Suns', 'Chain Reaction', 'Magmaquake', 'Spit Flame'],
    'Provoke the Trolls "does something, but at a very bad rate" (75% cut, and in both video cut lists); one-sided damage sweepers that miss flyers were swapped for Klauth\'s Will.', ['edh-dd', 'cgb-dd', 'nw-dd', 'tm-dd']),
   ('Win-more and weak draw', ['Unleash Fury', 'Shamanic Revelation', 'Sarkhan, the Dragonspeaker', 'Atarka Monument'],
    'Shamanic Revelation needs a wide board this deck doesn\'t make; Sarkhan costs too much (Triple Mango Threat: "not impressed").', ['edh-dd', 'cgb-dd', 'nw-dd', 'tm-dd']),
   ('Overcosted Dragons', ['Akoum Hellkite', 'Foe-Razer Regent', 'Demanding Dragon', 'Hoard-Smelter Dragon', 'Flameblast Dragon', 'Verix Bladewing'],
    'Nerds of the West and Triple Mango Threat swap them for better-value Dragons like Territorial Hellkite and Chaos Dragon.', ['nw-dd', 'tm-dd']),
  ],
  'split': [
   'Lands: Cardgamebase goes up to 43 for the expensive Dragons; EDHREC\'s guide only rebalances the basics; Nerds of the West goes down to 36.',
   'Sarkhans: Cardgamebase, Nerds of the West and Triple Mango Threat cut Sarkhan, the Dragonspeaker, but Cardgamebase and Jurassic Magic add Sarkhan the Masterless and Sarkhan, Fireblood.',
   'Savage Ventmaw: Star City Games and Jurassic Magic value it as mana for a second Dragon (and an infinite-combat piece); no source cuts it.',
  ],
  'alts': 'Atarka is the clear pick (2,742 decks from this box); Ganax, Astral Hunter is next with 181.',
  'videos': [],
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
    ['Cryptolith Rite', 'Springleaf Drum', 'Nature\'s Chosen', 'Instill Energy', 'Honor-Worn Shaku', 'Loam Dryad', 'Relic of Legends', 'Glare of Subdual', 'Smuggler\'s Copter', 'Bennie Bracks, Zoologist', 'Saryth, the Viper\'s Fang', 'Halo Fountain', 'Drumbellower', 'Seedborn Muse', 'Quest for Renewal', 'Wylie Duke, Atiin Hero'],
    ['cgb-tt', 'edh-tt', 'tm-tt', 'scg-tt', 'wit-tt'],
    'Cardgamebase\'s #1 pick is Cryptolith Rite (15% add). EDHREC\'s Tap/Untap decks play Wylie Duke 61% (vs 27%) and Drumbellower 63% (vs 33%). Triple Mango Threat\'s one must-buy is Nature\'s Chosen (about $1); Saryth and Drumbellower are each in two videos (Star City Games: Drumbellower is "less salty" than Seedborn Muse).'),
   ('Token doublers and more-token payoffs',
    'Make each token count twice, and turn the 1/1s into a real army.',
    ['Queen Allenal of Ruadach', 'King Darien XLVIII', 'Cadira, Caller of the Small', 'Doomed Artisan', 'Doubling Season', 'Parallel Lives', 'Anointed Procession', 'Divine Visitation', 'Intangible Virtue', 'Harmonious Archon', 'Elspeth, Sun\'s Champion'],
    ['edh-tt', 'cgb-tt', 'scg-tt', 'wit-tt', 'tm-tt'],
    'Queen Allenal is the #1 add (40%) and in two videos, Intangible Virtue #2, King Darien #3 (Wizard\'s Institute of Technology: "a no-brainer").',
    'Wizard\'s Institute of Technology calls this "probably the best designed of all the starter decks" and has "seen this deck take out more than a couple of games"; Emmara costs two and rarely draws removal.'),
   ('Draw off the army',
    'The box is short on cards; turn tokens into draws.',
    ['Skullclamp', 'Welcoming Vampire', 'Tocasia\'s Welcome', 'Rumor Gatherer', 'Bess, Soul Nourisher', 'Shamanic Revelation', 'Kutzil, Malamet Exemplar', 'Ohran Frostfang'],
    ['edh-tt', 'cgb-tt', 'tm-tt', 'scg-tt', 'wit-tt'],
    'Welcoming Vampire (20%) and Skullclamp (16%) are the most added draw. Shamanic Revelation is in two videos.'),
   ('Protect the board, then finish',
    'Board-wipe insurance and one big swing.',
    ['Unbreakable Formation', 'Heroic Intervention', 'Flawless Maneuver', 'Grand Crescendo', 'Craterhoof Behemoth', 'Beastmaster Ascension', 'Mirror Entity', 'Martial Coup', 'Horn of Valhalla', 'Triumph of the Hordes'],
    ['edh-tt', 'cgb-tt', 'wit-tt', 'tm-tt', 'scg-tt'],
    'EDHREC\'s guide names board protection as the deck\'s biggest gap. Craterhoof is a 12% add; Wizard\'s Institute calls Beastmaster Ascension "the ultimate pump effect".'),
  ],
  'avoid': [
   ('Slow, mana-hungry token makers', ['Jade Mage', 'Selesnya Guildmage', 'Sporemound', 'Verdant Force'],
    'Activation costs too high or over-costed. Selesnya Guildmage (64%) and Jade Mage (63%) are the top cuts; Wizard\'s Institute: Guildmage needs 8 to 12 mana to matter, and Verdant Force is "far too slow" at eight.', ['edh-tt', 'cgb-tt', 'wit-tt']),
   ('Weak card draw', ['Voice of Many', 'Slate of Ancestry', 'Dawn of Hope', 'Collective Unconscious'],
    'Redundant once real draw is in. Wizard\'s Institute: Slate is eight mana in all, and Shamanic Revelation is "infinitely better".', ['edh-tt', 'cgb-tt', 'wit-tt']),
   ('Off-theme cards', ['Ajani, Caller of the Pride', 'Scavenging Ooze', 'Talisman of Unity'],
    'Cardgamebase: they don\'t work with the theme. Wizard\'s Institute: Ajani\'s −8 is unreachable, and green should ramp with land spells rather than a Talisman.', ['cgb-tt', 'edh-tt', 'wit-tt']),
   ('One-turn or conditional buffs', ['Valor in Akros', 'Overwhelming Instinct', 'Overrun', 'Great Oak Guardian'],
    'Too much setup for a temporary effect; better finishers exist. Wizard\'s Institute: Great Oak Guardian is six mana for a one-time pump.', ['edh-tt', 'cgb-tt', 'wit-tt']),
  ],
  'split': [
   'Populate: EDHREC\'s Populate decks (65) keep Felidar Retreat, Scatter the Seeds and Valor in Akros, which both guides cut; Star City Games calls Felidar Retreat a card it has suggested many times.',
   'Removal: Cardgamebase says single-target removal is weak in Commander, yet Swords to Plowshares is the #4 add (23%) and Wizard\'s Institute adds it with Generous Gift and Stroke of Midnight.',
   'Slate of Ancestry and Scavenging Ooze: Star City Games praises both; EDHREC\'s guide, Cardgamebase and Wizard\'s Institute cut Slate.',
   'Jade Mage, Verdant Force and Overrun: cut by the guides, but MTG Basics\' walkthrough of the stock deck counts on them (Jade Mage for empty-hand turns, Overrun as the closer).',
  ],
  'alts': 'Emmara stays the commander in nearly every deck from this box (1,903; the next, Rhys the Redeemed, has 73).',
  'also': ['mb-tt'],
  'videos': [('hTFSMMPmKFE', 'Tokens Triumph precon deck upgrade guide', 'Squirrel commander')],
 },
]

THEME_NAME = {'auras': 'Auras', 'enchantress': 'Enchantress', 'forced-combat': 'Forced combat', 'voltron': 'Voltron', 'pillow-fort': 'Pillow fort',
              'politics': 'Politics', 'reanimator': 'Reanimator', 'tokens': 'Tokens', 'graveyard': 'Graveyard', 'self-mill': 'Self-mill',
              'discard': 'Discard', 'flashback': 'Flashback', 'spirits': 'Spirits', 'energy': 'Energy', 'artifacts': 'Artifacts', 'clones': 'Clones',
              'artificers': 'Artificers', 'vehicles': 'Vehicles', 'zombies': 'Zombies', 'card-draw': 'Card draw', 'wheels': 'Wheels', 'aristocrats': 'Aristocrats',
              'flying': 'Flying', 'control': 'Control', 'sphinxes': 'Sphinxes', 'mill': 'Mill', 'combo': 'Combo', 'group-slug': 'Group slug', 'chaos': 'Chaos',
              'burn': 'Burn', 'blink': 'Blink', 'dragons': 'Dragons', 'ramp': 'Ramp', 'extra-combats': 'Extra combats', 'tap-untap': 'Tap/untap',
              'lifegain': 'Lifegain', 'populate': 'Populate', 'convoke': 'Convoke', 'aggro': 'Aggro', 'p1-p1-counters': '+1/+1 counters'}

def esc(s): return html.escape(s, quote=True)

def edhrec(d):
    """(decks from the box with this commander, add shares, cut shares, theme counts, all decks for this commander).
    A deck with 'mode': 'commander' (the box's alternate commander, built very differently) gets its card numbers from
    the commander's own EDHREC page instead: the share of all that commander's decks that play the card, and no cuts,
    since the precon page's add/cut shares mix both commanders' decks."""
    pre = json.loads(get(f'https://json.edhrec.com/pages/precon/{d.get("precon", d["slug"])}.json'))
    L = {l['tag']: l['cardviews'] for l in pre['container']['json_dict']['cardlists']}
    adds = {c['name']: c['num_decks'] / c['potential_decks'] for t in ('cardstoadd', 'landstoadd') for c in L.get(t, []) if c.get('potential_decks')}
    cuts = {c['name']: c['unpopularity'] for t in ('cardstocut', 'landstocut') for c in L.get(t, []) if c.get('unpopularity')}
    n = {c['value']: c['count'] for c in pre['precon_commander_counts']}[d['cmd']]
    slug = d['cmd'].lower().replace(',', '').replace("'", '').replace(' ', '-')
    cp = json.loads(get(f'https://json.edhrec.com/pages/commanders/{slug}.json'))
    # '+1/+1 Counters' -> 'p1-p1-counters', '-1/-1 Counters' -> 'm1-m1-counters' (they'd collide once signs are stripped)
    tags = {re.sub(r'[^a-z0-9]+', '-', t['value'].lower().replace('+', 'p').replace('-1', 'm1')).strip('-'): t['count']
            for t in cp.get('panels', {}).get('taglinks', [])}
    total = cp['container']['json_dict'].get('card', {}).get('num_decks', 0)
    if d.get('mode') == 'commander':
        adds = {c['name']: c['num_decks'] / c['potential_decks'] for l in cp['container']['json_dict']['cardlists']
                for c in l['cardviews'] if c.get('potential_decks')}
        cuts = {}
    time.sleep(0.5)
    return n, adds, cuts, tags, total

def main():
    today = datetime.date.today()
    names = sorted({c for d in DECKS for a in d['angles'] for c in a[2]} | {c for d in DECKS for a in d['avoid'] for c in a[1]})
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

    def chip(n, adds, cuts, mode, cmdmode=False):
        legal, gc, url = flags[n]
        pct = adds.get(n) if mode == 'add' else cuts.get(n)
        num = (f'<span class="p pc">{round(pct * 100)}%</span>' if cmdmode else
               f'<span class="p">{"+" if mode == "add" else "−"}{round(pct * 100)}%</span>') if pct else ''
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
        n, adds, cuts, tags, total = edhrec(d)
        cm = d.get('mode') == 'commander'
        th = ' · '.join(f'{THEME_NAME[t]} {tags[t]:,}' for t in d['themes'] if t in tags)
        # An angle is (title, what, cards, source keys, data note) plus an optional "From play" line: how the direction
        # actually played, as reported by a source that played it (a creator's playtest or a reviewed player's deck).
        ang = ''.join(f'''<div class="ang"><h4>{esc(a[0])}</h4><p>{esc(a[1])}</p><div class="cards">{''.join(chip(c, adds, cuts, 'add', cm) for c in a[2])}</div>
<p class="data">{esc(a[4])}</p>{f'<p class="play"><b>From play:</b> {esc(a[5])}</p>' if len(a) > 5 else ''}<p class="src">Pushed by: {who(a[3])}</p></div>''' for a in d['angles'])
        av = ''.join(f'''<div class="ang av"><h4>{esc(t)}</h4><div class="cards">{''.join(chip(c, adds, cuts, 'cut') for c in cs)}</div>
<p>{esc(w)}</p><p class="src">Cut by: {who(ks)}</p></div>''' for t, cs, w, ks in d['avoid'])
        sp = ''.join(f'<li>{esc(s)}</li>' for s in d['split'])
        vids = ''.join(f'<li><a href="{V}{i}" target="_blank" rel="noopener">{esc(t)}</a> <span class="who">{esc(ch)}</span></li>' for i, t, ch in d['videos'])
        # 'also' lists sources cited only in the disagreements or notes (no angle or cut of their own)
        srcs = sorted({k for a in d['angles'] for k in a[3]} | {k for a in d['avoid'] for k in a[3]} | set(d.get('also', [])), key=list(SOURCES).index)
        sl = ''.join(f'<li id="src-{k}"><a href="{SOURCES[k][1]}" target="_blank" rel="noopener">{esc(SOURCES[k][0])}</a>'
                     + (f'<br><span class="who">{esc(SOURCES[k][2])}</span>' if SOURCES[k][2] else '') + '</li>' for k in srcs)
        toc.append(f'<a href="#{d["slug"]}">{esc(d["name"])}</a>')
        who1 = esc(d['cmd'].split(',')[0])
        box = d.get('precon', d['slug'])
        data = (f'EDHREC: {total:,} {who1} decks in all, {n:,} of them built from this box. The number after a card here is the share of all {who1} decks that play it (no cut shares: EDHREC\'s cut numbers for this box mostly come from the other commander\'s decks). Themes {who1} decks are tagged with: {th}.'
                if cm else f'EDHREC: {n:,} decks built from this box with {who1}. Themes {who1} decks are tagged with: {th}.')
        secs.append(f'''<section id="{d['slug']}"><h2 class="dk">{esc(d['name'])} <small>{esc(d['cmd'])} · {d['colors']}</small></h2>
<p>{esc(d['gist'])}</p>
<p class="data">{data} <a href="../adds/{box}.html">Most added ›</a> <a href="../cuts/{box}.html">Most cut ›</a></p>
<h3>Directions people take it</h3>{ang}
<h3>What people stay away from</h3>{av}
<h3>Where the sources disagree</h3><ul>{sp}</ul>
<p class="data">{esc(d['alts'])}</p>
<details><summary>Sources for {esc(d['name'])}</summary><ul class="srcs">{sl}</ul>
{f'<p class="data">Also found, not read:</p><ul class="srcs">{vids}</ul>' if vids else ''}</details>
</section>''')

    page = open(os.path.join(HERE, 'angles-template.html'), encoding='utf-8').read()
    page = (page.replace('<!--TOC-->', ' '.join(toc)).replace('<!--DECKS-->', '\n'.join(secs))
                .replace('<!--DATE-->', f'{today:%b} {today.day}, {today.year}'))
    open(os.path.join(ROOT, 'decks', 'angles.html'), 'w', encoding='utf-8', newline='\n').write(page)
    print('wrote decks/angles.html,', len(names), 'cards,', sum(f[1] for f in flags.values()), 'Game Changers')

if __name__ == '__main__':
    main()
