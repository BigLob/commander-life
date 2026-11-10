"""Build a brewed deck carousel: brews/<slug>.html, with a role and sources under every card (the user cut the per-card reason line; the reasons stay
here as notes for picking roles).

The list is EDHREC's average deck for the commander (the cards most played across every deck EDHREC has
for it). Each card's numbers (share of those decks that play it, and EDHREC's synergy: how much more often
it's played with this commander than in other decks of its colors) come from EDHREC's commander page.
The reason is hand-written from the card's own rules text (linked to Scryfall). Prices are the cheapest
paper printing on Scryfall.
Run from the repo root:  python3 tools/carousel/brew.py [slug ...]
"""
import html, json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'brews')
UA = {'User-Agent': 'commander-life/1.0', 'Accept': 'application/json'}
ROLES = ['Commander', 'Rat', 'Squirrel maker', 'Food maker', 'Food eater', 'Squirrel payoff', 'Token maker', 'Token doubler', 'Payoff', 'Drain', 'Sac outlet', 'Draw', 'Ramp', 'Tutor',
         'Recursion', 'Removal', 'Counter', 'Protection', 'Land']

# card -> (role, why). Chatterfang: "If one or more tokens would be created under your control, those tokens
# plus that many 1/1 green Squirrel creature tokens are created instead. {B}, Sacrifice X Squirrels: target
# creature gets +X/-X." So every token maker is also a Squirrel maker, and Squirrels are removal and fodder.
CHATTERFANG = {
    'Chatterfang, Squirrel General': ('Commander', 'Whenever you make tokens you get that many Squirrels too, and {B}, sacrifice X Squirrels gives a creature +X/−X, so spare Squirrels become removal. Forestwalk makes it unblockable against Forests.'),
    # token makers
    'Chitterspitter': ('Token maker', 'Makes a Squirrel for {G} (two with Chatterfang) and eats a token each upkeep to pump every Squirrel.'),
    'Camellia, the Seedmiser': ('Token maker', 'Sacrificing Food makes Squirrels, and gives your other Squirrels menace.'),
    'Deep Forest Hermit': ('Token maker', 'Four Squirrels on entering (eight with Chatterfang), and all Squirrels get +1/+1.'),
    'Hazel of the Rootbloom': ('Token maker', 'Copies a token each end step, two copies if it is a Squirrel, and taps your tokens for mana.'),
    "Hazel's Brewmaster": ('Token maker', 'A Food (and a Squirrel) every time it enters or attacks, plus graveyard exile.'),
    'Peregrin Took': ('Token maker', 'Adds a Food to every token creation, and Chatterfang adds a Squirrel for that Food too.'),
    'Scurry Oak': ('Token maker', 'Grows by evolve as bigger creatures arrive, and each time it gets counters it makes a Squirrel (two with Chatterfang).'),
    'Scurry of Squirrels': ('Token maker', 'Myriad makes attacking token copies of it each combat, and Chatterfang adds a Squirrel per copy.'),
    'Scute Swarm': ('Token maker', 'An Insect for each land you play (plus a Squirrel); at six lands it copies itself instead.'),
    'The Unbeatable Squirrel Girl': ('Token maker', 'A Squirrel when it enters or attacks, and for four mana doubles the Squirrels you have.'),
    'Garruk, Cursed Huntsman': ('Token maker', 'Two Wolves every turn (plus two Squirrels), or kill a creature and draw.'),
    'Squirrel Nest': ('Token maker', 'Turns a land into a Squirrel every turn; with Chatterfang, two.'),
    'Squirrel Sanctuary': ('Token maker', 'A Squirrel on entering, and it returns to hand when a nontoken creature dies so you can cast it again.'),
    'Chatter of the Squirrel': ('Token maker', 'A Squirrel now and another from the graveyard (flashback); each is two with Chatterfang.'),
    'Chatterstorm': ('Token maker', 'Storm: a Squirrel for every spell cast before it this turn, each doubled by Chatterfang.'),
    'Swarmyard Massacre': ('Token maker', 'Two Squirrels (four), then every creature that is not a Squirrel, Rat, Insect or Spider gets −1/−1 per Squirrel you have: often a one-sided wipe.'),
    'Verdant Command': ('Token maker', 'Two Squirrels (four) at instant speed, or exile a graveyard card or gain 3 life.'),
    'Rootcast Apprenticeship': ('Token maker', 'Pick three: copy a token, make a Squirrel, add +1/+1 counters, or make an opponent sacrifice an artifact.'),
    # token doublers
    'Academy Manufactor': ('Token doubler', 'Each Food, Treasure or Clue becomes one of each, three tokens, so Chatterfang adds three Squirrels.'),
    'Doubling Season': ('Token doubler', 'Doubles every token you make, Chatterfang\'s Squirrels included, and every counter.'),
    'Parallel Lives': ('Token doubler', 'Doubles every token you make, Chatterfang\'s Squirrels included.'),
    'Second Harvest': ('Token doubler', 'Copies every token you control at instant speed, and Chatterfang adds that many Squirrels again.'),
    'For the Common Good': ('Token doubler', 'Copies one token X times, then makes all your tokens indestructible and gains life for each.'),
    # payoffs
    'Honored Dreyleader': ('Payoff', 'Gets a +1/+1 counter for every Squirrel and Food that enters.'),
    'Squirrel Mob': ('Payoff', 'Gets +1/+1 for every other Squirrel on the battlefield.'),
    'Squirrel Sovereign': ('Payoff', 'Other Squirrels get +1/+1, so the 1/1 tokens become real attackers.'),
    'The Odd Acorn Gang': ('Payoff', 'Squirrels pump each other, and you draw when Squirrels deal combat damage.'),
    'Toski, Bearer of Secrets': ('Draw', 'Draws a card for each creature that hits a player, and is indestructible.'),
    'Sword of the Squeak': ('Payoff', 'Attaches itself free to each Squirrel that enters, and grows with every 1/1 you control.'),
    'Beastmaster Ascension': ('Payoff', 'Attack with seven Squirrels and every creature you have gets +5/+5.'),
    'Valley Rotcaller': ('Drain', 'When it attacks, each opponent loses 1 life per other Squirrel, Bat, Lizard and Rat you control.'),
    # drain
    'Blood Artist': ('Drain', 'Any creature dying drains a player for 1, so sacrificing Squirrels ends games.'),
    'Zulaport Cutthroat': ('Drain', 'Each of your creatures dying drains every opponent for 1.'),
    'Bastion of Remembrance': ('Drain', 'Each of your creatures dying drains every opponent for 1, and it brings a creature token (plus a Squirrel).'),
    'Mirkwood Bats': ('Drain', 'Each opponent loses 1 whenever you make or sacrifice a token, so every Chatterfang trigger pings twice.'),
    "Nadier's Nightblade": ('Drain', 'Each token that leaves the battlefield drains every opponent for 1.'),
    # sacrifice outlets
    "Ashnod's Altar": ('Sac outlet', 'Free sacrifice that turns each Squirrel into two mana, setting off every death trigger.'),
    'Warren Soultrader': ('Sac outlet', 'Pay 1 life and sacrifice a creature for a Treasure; the Treasure is a token, so Chatterfang adds a Squirrel to sacrifice next.'),
    'Ravenous Squirrel': ('Sac outlet', 'Sacrifice anything to draw and gain 1 life, and it grows with every sacrifice.'),
    'Pitiless Plunderer': ('Ramp', 'A Treasure for each of your creatures that dies, and each Treasure brings a Squirrel.'),
    # draw
    'Skullclamp': ('Draw', 'Equip a 1/1 Squirrel for 1 and it dies at once: two cards per Squirrel.'),
    'Idol of Oblivion': ('Draw', 'Draws a card on any turn you made a token, which is nearly every turn here.'),
    'Moldervine Reclamation': ('Draw', 'Draws a card and gains 1 life whenever one of your creatures dies.'),
    'Deadly Dispute': ('Draw', 'Sacrifice a Squirrel to draw two and make a Treasure (and another Squirrel).'),
    'Plumb the Forbidden': ('Draw', 'Sacrifice any number of Squirrels at instant speed for a card each, for example in answer to a wipe.'),
    'Shamanic Revelation': ('Draw', 'Draws a card for each creature you control: with a board of Squirrels, a full grip.'),
    'Black Market Connections': ('Draw', 'Each turn pick cards, a Treasure or a 3/2 Shapeshifter for life; the tokens bring Squirrels.'),
    # ramp
    'Sol Ring': ('Ramp', 'Two extra mana from turn one; in nearly every Commander deck.'),
    'Arcane Signet': ('Ramp', 'Taps for black or green, so Chatterfang lands a turn early.'),
    'Golgari Signet': ('Ramp', 'Two-mana rock that makes black and green.'),
    'Talisman of Resilience': ('Ramp', 'Two-mana rock for black or green.'),
    'Gilded Goose': ('Ramp', 'Makes Food (and a Squirrel each time) and turns Food into any color of mana.'),
    'Jaheira, Friend of the Forest': ('Ramp', 'Every token taps for {G}, so a board of Squirrels is a pile of mana.'),
    'Prosperous Innkeeper': ('Ramp', 'A Treasure (and a Squirrel) on entering, and 1 life for every creature that enters after.'),
    'Thornvault Forager': ('Ramp', 'Taps for mana, and for {3}{G} finds any Squirrel card in your library.'),
    'Tireless Provisioner': ('Ramp', 'A Food or Treasure for every land you play, each bringing a Squirrel.'),
    'Cultivate': ('Ramp', 'Two basic lands: one onto the battlefield, one to hand.'),
    "Nature's Lore": ('Ramp', 'Puts a Forest (Overgrown Tomb counts) onto the battlefield untapped.'),
    'Rampant Growth': ('Ramp', 'Puts a basic land onto the battlefield for two mana.'),
    'Demonic Tutor': ('Tutor', 'Finds whatever the game needs: Second Harvest, a doubler, or a sacrifice outlet.'),
    # removal and protection
    "Assassin's Trophy": ('Removal', 'Destroys any permanent an opponent controls, at instant speed, for two mana.'),
    'Beast Within': ('Removal', 'Destroys any permanent; its owner gets a 3/3 Beast.'),
    'Putrefy': ('Removal', 'Destroys an artifact or creature at instant speed.'),
    'Saw in Half': ('Removal', 'Kills an opponent\'s creature, or splits one of yours into two tokens, which brings two Squirrels.'),
    'Heroic Intervention': ('Protection', 'Your whole board gains hexproof and indestructible against a wipe.'),
    # lands
    'Swarmyard': ('Land', 'Regenerates a Squirrel, so Squirrels can attack and block without dying.'),
    'Yavimaya, Cradle of Growth': ('Land', 'Every land is a Forest, so every land taps for green and Chatterfang\'s forestwalk works against everyone.'),
    'Oran-Rief, the Vastwood': ('Land', 'A +1/+1 counter on each green creature that entered this turn, every Squirrel token included.'),
    'Bojuka Bog': ('Land', 'Exiles a player\'s graveyard when it enters.'),
    'Command Tower': ('Land', 'Taps for either color with no drawback.'),
    'Exotic Orchard': ('Land', 'In a four-player game it almost always taps for both colors.'),
    'Path of Ancestry': ('Land', 'Either color, and scry 1 when you cast a Squirrel with it.'),
    'Golgari Rot Farm': ('Land', 'Taps for two mana, and replaying the land it returns is another landfall trigger.'),
    'Overgrown Tomb': ('Land', 'Untapped dual that is a Swamp and a Forest, so Nature\'s Lore and Verdant Catacombs find it.'),
    'Verdant Catacombs': ('Land', 'Fetches Overgrown Tomb or a basic, and makes two landfall triggers.'),
    'Woodland Cemetery': ('Land', 'Dual that comes in untapped once you have a Swamp or Forest.'),
    'Llanowar Wastes': ('Land', 'Untapped dual for 1 damage.'),
    'Necroblossom Snarl': ('Land', 'Untapped dual if you show a Swamp or Forest.'),
    'Tainted Wood': ('Land', 'Untapped dual while you have a Swamp.'),
    'Temple of Malady': ('Land', 'Tapped dual with scry 1.'),
    'Twilight Mire': ('Land', 'Turns one mana into two of black and green in any mix.'),
    'Undergrowth Stadium': ('Land', 'Untapped dual in any game with two or more opponents.'),
    'Viridescent Bog': ('Land', 'Turns one mana into black and green.'),
    'Forest': ('Land', 'Basics: Nature\'s Lore, Cultivate and Rampant Growth fetch them, and Woodland Cemetery and Necroblossom Snarl need them.'),
    'Swamp': ('Land', 'Basics for black: Tainted Wood, Woodland Cemetery and Necroblossom Snarl need a Swamp.'),
}

# Marrow-Gnawer: "All Rats have fear. {T}, Sacrifice a Rat: Create X 1/1 black Rat creature tokens, where X is the
# number of Rats you control." Each activation roughly doubles the Rats, and fear makes them hard to block, so the
# deck is mostly Rats (17 Rat Colony) plus lords, ways to untap Marrow-Gnawer, and death payoffs.
MARROW = {
    'Marrow-Gnawer': ('Commander', 'All Rats have fear (only black or artifact creatures can block them), and tapping it with a Rat to sacrifice makes a Rat for every Rat you have: the board doubles each turn.'),
    'Rat Colony': ('Rat', 'Any number allowed in a deck; each gets +1/+0 for every other Rat, so a few of them and a Marrow-Gnawer activation swing for lethal.'),
    'Swarm of Rats': ('Rat', 'Power equal to the number of Rats you control, for two mana.'),
    'Persistent Marshstalker': ('Rat', '+1/+0 per other Rat, and with seven cards in the graveyard it comes back attacking whenever Rats attack.'),
    'Typhoid Rats': ('Rat', 'One-mana deathtouch blocker, and a Rat to sacrifice later.'),
    'Ink-Eyes, Servant of Oni': ('Rat', 'Ninjutsu in off an unblocked (feared) Rat, then reanimates a creature from that player\'s graveyard.'),
    # token makers
    'Pack Rat': ('Token maker', 'Its size is your Rat count, and any discarded card makes another copy of it.'),
    'Piper of the Swarm': ('Token maker', 'Rats get menace, it makes a Rat for {1}{B}, and three Rats steal any creature.'),
    'Lord Skitter, Sewer King': ('Token maker', 'A Rat every combat, and every Rat that enters exiles a card from an opponent\'s graveyard.'),
    'Ogre Slumlord': ('Token maker', 'A Rat whenever any other nontoken creature dies, and all your Rats have deathtouch.'),
    'Rat King, Verminister': ('Token maker', 'A Rat and a counter each end step a permanent left (every sacrifice counts), and three Rats bring back every Rat Colony from the graveyard.'),
    'Tangled Colony': ('Token maker', 'When it dies, a Rat for each damage dealt to it that turn, so a blocked Rat Colony pile turns into tokens.'),
    # payoffs
    'Ashcoat of the Shadow Swarm': ('Payoff', 'Attacking, every other Rat gets +X/+X for your Rat count, and each end step it mills four to return two Rats.'),
    'Coat of Arms': ('Payoff', 'Every Rat gets +1/+1 per other Rat: with ten Rats, each is an 11/11.'),
    'Patchwork Banner': ('Payoff', 'Rats get +1/+1, and it taps for mana.'),
    "Vanquisher's Banner": ('Payoff', 'Rats get +1/+1, and every Rat you cast draws a card.'),
    'Haunted One': ('Payoff', 'A Background: when Marrow-Gnawer taps, every Rat gets +2/+0 and undying, so the Rats you sacrifice come back.'),
    'Thornbite Staff': ('Payoff', 'On Marrow-Gnawer, every creature that dies untaps it, so each sacrificed Rat lets it activate again: Rats without limit.'),
    'Karumonix, the Rat King': ('Draw', 'Rats get toxic 1, and it puts every Rat from the top five cards into your hand.'),
    # drain
    "Bontu's Monument": ('Drain', 'Black creatures cost {1} less, and every creature you cast drains each opponent for 1.'),
    'Ayara, First of Locthwain': ('Drain', 'Each black creature entering drains each opponent for 1, Rat tokens included, and it sacrifices one to draw.'),
    'Mirkwood Bats': ('Drain', 'Each opponent loses 1 whenever you make or sacrifice a token, so a Marrow-Gnawer activation drains a lot.'),
    'Valley Rotcaller': ('Drain', 'Attacking, each opponent loses 1 life for every other Rat you control.'),
    'Foul-Tongue Shriek': ('Drain', 'One mana: an opponent loses 1 for each attacker, after a big Rat swing.'),
    'Gruesome Fate': ('Drain', 'Each opponent loses 1 life per creature you control: a finisher with a board of Rats.'),
    # draw
    'Skullclamp': ('Draw', 'Equip a 1/1 Rat for 1 and it dies at once: two cards per Rat.'),
    "Herald's Horn": ('Draw', 'Rats cost {1} less, and each upkeep a Rat on top goes to your hand.'),
    'Thrumming Stone': ('Draw', 'Ripple 4: each Rat Colony you cast reveals four and casts every other Rat Colony among them free.'),
    'Species Specialist': ('Draw', 'Draws a card whenever a Rat dies, so every sacrifice is a card.'),
    'Phyrexian Arena': ('Draw', 'An extra card every turn for 1 life.'),
    'Deadly Dispute': ('Draw', 'Sacrifice a Rat to draw two and make a Treasure.'),
    'Village Rites': ('Draw', 'One mana: sacrifice a Rat to draw two.'),
    'Sign in Blood': ('Draw', 'Two cards for two mana and 2 life.'),
    # ramp
    'Sol Ring': ('Ramp', 'Two extra mana from turn one; in nearly every Commander deck.'),
    'Arcane Signet': ('Ramp', 'Two-mana rock that taps for black.'),
    'Jet Medallion': ('Ramp', 'Every black spell costs {1} less, which is nearly every spell here.'),
    'Black Market': ('Ramp', 'A charge counter for every creature that dies (every sacrificed Rat), then that much black mana each turn.'),
    'Dark Ritual': ('Ramp', 'One mana for three: Marrow-Gnawer on turn two or three.'),
    # tutors
    'Ratcatcher': ('Tutor', 'Has fear, and finds a Rat card every upkeep.'),
    'Demonic Tutor': ('Tutor', 'Finds whatever the game needs: Thornbite Staff, Coat of Arms or an answer.'),
    'Vampiric Tutor': ('Tutor', 'One mana, at instant speed: the card you need on top of your library.'),
    # recursion
    'Echoing Return': ('Recursion', 'One mana returns every Rat Colony in your graveyard to your hand.'),
    "Patriarch's Bidding": ('Recursion', 'Everyone names a type: you name Rat and every Rat in your graveyard returns, after a wipe.'),
    # removal and protection
    'Crypt Rats': ('Removal', 'Black mana into X damage to every creature and player: a wipe or a finisher (Cabal Coffers pays for it).'),
    'Grave Pact': ('Removal', 'Every Rat you sacrifice makes each other player sacrifice a creature.'),
    'Kindred Dominance': ('Removal', 'Name Rat and every creature that is not a Rat is destroyed: a one-sided wipe.'),
    'Defile': ('Removal', 'One mana: -1/-1 per Swamp, which is most of your lands.'),
    'Feed the Swarm': ('Removal', 'Kills a creature or an enchantment, the one thing black struggles with.'),
    'Go for the Throat': ('Removal', 'Two-mana instant kill for any nonartifact creature.'),
    'Lightning Greaves': ('Protection', 'Haste and shroud for free: Marrow-Gnawer activates the turn it lands and dodges removal.'),
    # lands
    'Swarmyard': ('Land', 'Regenerates a Rat, so Rats attack and block without dying.'),
    'Cabal Coffers': ('Land', 'Two mana for a black mana per Swamp: huge Crypt Rats and Pack Rat turns.'),
    'Cabal Stronghold': ('Land', 'Another Coffers, counting basic Swamps.'),
    'Urborg, Tomb of Yawgmoth': ('Land', 'Every land is a Swamp, so Coffers and Defile count them all.'),
    'Three Tree City': ('Land', 'Name Rat and it taps for a mana per Rat you control.'),
    'Mudflat Village': ('Land', 'Black mana for creatures, and it sacrifices to return a Rat card to hand.'),
    'Bojuka Bog': ('Land', 'Exiles a player\'s graveyard when it enters.'),
    'Swamp': ('Land', 'Mono-black, so basics are most of the mana base, and Cabal Coffers, Cabal Stronghold and Defile count them.'),
}

# Vren, the Relentless: "Ward {2}. If a creature an opponent controls would die, exile it instead. At the beginning of
# each end step, create X 1/1 black Rat creature tokens with 'This token gets +1/+1 for each other Rat you control,'
# where X is the number of creatures that were exiled under your opponents' control this turn." So every removal
# spell and edict is also a Rat maker, on every player's turn, and the Rats grow each other.
VREN = {
    'Vren, the Relentless': ('Commander', 'Opponents\' creatures that would die are exiled instead, and each end step makes a Rat for each one, every turn. Its Rats get +1/+1 per other Rat, and ward {2} protects it.'),
    'Typhoid Rats': ('Rat', 'One-mana deathtouch: whatever it trades with is exiled, so it is a Rat for a Rat.'),
    'Azure Beastbinder': ('Rat', 'Hard to block, and each attack strips an opponent\'s best permanent of its abilities.'),
    'Mindwhisker': ('Rat', 'Surveils every upkeep, and at threshold opponents\' creatures get -1/-0.'),
    'Persistent Marshstalker': ('Rat', '+1/+0 per other Rat, and at threshold it comes back attacking whenever Rats attack.'),
    # token makers
    'Pack Rat': ('Token maker', 'Its size is your Rat count, and any discarded card makes another copy of it.'),
    'Piper of the Swarm': ('Token maker', 'Rats get menace, it makes a Rat for {1}{B}, and three Rats steal any creature.'),
    'Lord Skitter, Sewer King': ('Token maker', 'A Rat every combat, and every Rat that enters exiles a card from an opponent\'s graveyard.'),
    "Lord Skitter's Butcher": ('Token maker', 'A Rat, a sacrifice to draw, or menace for the team when it enters.'),
    'Marrow-Gnawer': ('Token maker', 'Rats get fear, and sacrificing one makes a Rat for every Rat you control.'),
    'Ogre Slumlord': ('Token maker', 'A Rat when any other nontoken creature dies, and all your Rats have deathtouch, so every block exiles.'),
    'Tangled Colony': ('Token maker', 'When it dies, a Rat for each damage dealt to it that turn.'),
    'Voracious Vermin': ('Token maker', 'A Rat on entering, and it grows each time one of your creatures dies.'),
    # payoffs
    'Ashcoat of the Shadow Swarm': ('Payoff', 'Attacking, every other Rat gets +X/+X for your Rat count, and each end step it mills four to return two Rats.'),
    'Patchwork Banner': ('Payoff', 'Rats get +1/+1, and it taps for mana.'),
    'Cover of Darkness': ('Payoff', 'Name Rat and all of them have fear, so a board of growing Rats goes unblocked.'),
    'Karumonix, the Rat King': ('Draw', 'Rats get toxic 1, and it puts every Rat from the top five cards into your hand.'),
    # drain
    'Ayara, First of Locthwain': ('Drain', 'Each black creature entering drains each opponent for 1, Vren\'s Rats included, and it sacrifices one to draw.'),
    'Braids, Arisen Nightmare': ('Drain', 'Each end step sacrifice a Rat: each opponent sacrifices a creature (exiled, so a Rat) or loses 2 and you draw.'),
    'Valley Rotcaller': ('Drain', 'Attacking, each opponent loses 1 life for every other Rat you control.'),
    # draw
    'Kindred Discovery': ('Draw', 'Name Rat: a card whenever a Rat enters or attacks, and Vren makes them in batches.'),
    'Distant Melody': ('Draw', 'Name Rat: a card for every Rat you control.'),
    'Shoreline Looter': ('Draw', 'Unblockable Rat that loots, then draws, each hit.'),
    'Phyrexian Arena': ('Draw', 'An extra card every turn for 1 life.'),
    'Rhystic Study': ('Draw', 'A card whenever an opponent casts a spell and won\'t pay {1}.'),
    # ramp
    'Sol Ring': ('Ramp', 'Two extra mana from turn one; in nearly every Commander deck.'),
    'Arcane Signet': ('Ramp', 'Two-mana rock for blue or black.'),
    'Dimir Signet': ('Ramp', 'Two-mana rock that makes blue and black.'),
    'Talisman of Dominance': ('Ramp', 'Two-mana rock for blue or black.'),
    'Fellwar Stone': ('Ramp', 'Two-mana rock, almost always the right color in a four-player game.'),
    'Mind Stone': ('Ramp', 'Two-mana rock that cashes in for a card later.'),
    'Jet Medallion': ('Ramp', 'Every black spell costs {1} less, most of the deck.'),
    'Dark Ritual': ('Ramp', 'One mana for three: Vren on turn two.'),
    # edicts: each opponent sacrifices, the creature is exiled instead, and Vren makes a Rat for each
    'Accursed Marauder': ('Removal', 'Each player sacrifices a nontoken creature: you give up a Rat, each opponent loses a real creature, and Vren makes a Rat for each.'),
    "Demon's Disciple": ('Removal', 'Edict on a body: each opponent loses a creature (a Rat for you) and you sacrifice a spare Rat.'),
    'Fleshbag Marauder': ('Removal', 'Edict on a body: each opponent loses a creature (a Rat for you) and you sacrifice a spare Rat.'),
    'Merciless Executioner': ('Removal', 'Edict on a body: each opponent loses a creature (a Rat for you) and you sacrifice a spare Rat.'),
    'Plaguecrafter': ('Removal', 'Edict on a body; players with no creature discard instead.'),
    'Innocent Blood': ('Removal', 'One-mana edict: up to three Rats at the end step.'),
    "Liliana's Triumph": ('Removal', 'Instant edict on every opponent: a Rat each.'),
    "Sheoldred's Edict": ('Removal', 'Each opponent sacrifices a nontoken creature, a token or a planeswalker, your choice.'),
    'Soul Shatter': ('Removal', 'Each opponent sacrifices their biggest creature or planeswalker.'),
    'Flare of Malice': ('Removal', 'Free if you sacrifice a black creature: each opponent sacrifices their biggest creature.'),
    "Vona's Hunger": ('Removal', 'Each opponent sacrifices a creature; with ten permanents, half their creatures.'),
    'Grave Pact': ('Removal', 'Every creature of yours that dies makes each opponent sacrifice one, so trading Rats makes more Rats.'),
    'Dictate of Erebos': ('Removal', 'Grave Pact with flash.'),
    'Season of Loss': ('Removal', 'Up to five edicts in one spell, or draw for what died, or drain.'),
    # wipes: every opponent creature is exiled at once, so the end step brings a pile of Rats
    'Kindred Dominance': ('Removal', 'Name Rat and every other creature is destroyed (exiled): a one-sided wipe that pays you a Rat per creature.'),
    'Crippling Fear': ('Removal', 'Name Rat: everything else gets -3/-3, and Vren turns what dies into Rats.'),
    'Swarmyard Massacre': ('Removal', 'Two Squirrels, then non-Rats get -1/-1 per Rat and Squirrel you control: usually one-sided.'),
    'Toxic Deluge': ('Removal', 'Pay X life for -X/-X to everything; Vren\'s Rats come after the wipe, at end step.'),
    'Crypt Rats': ('Removal', 'Black mana into X damage to every creature and player.'),
    'Force of Despair': ('Removal', 'Free on an opponent\'s turn: destroys every creature that entered this turn.'),
    # spot removal
    'Go for the Throat': ('Removal', 'Kills a nonartifact creature at instant speed (exiled, so a Rat).'),
    'Infernal Grasp': ('Removal', 'Kills any creature at instant speed for 2 life.'),
    'Fell': ('Removal', 'Two-mana sorcery kill.'),
    'Feed the Swarm': ('Removal', 'Kills a creature or an enchantment.'),
    'Pongify': ('Removal', 'One-mana kill in blue; the creature dies (a Rat for you) though its owner gets a 3/3.'),
    'Rapid Hybridization': ('Removal', 'Pongify again: a kill and a Rat for one blue.'),
    # counters
    'Counterspell': ('Counter', 'Counters anything for two blue.'),
    'Arcane Denial': ('Counter', 'Two-mana counter for anything; both players draw.'),
    'Negate': ('Counter', 'Stops a wipe or removal aimed at Vren.'),
    'An Offer You Can\'t Refuse': ('Counter', 'One-mana counter for any noncreature spell.'),
    'Lightning Greaves': ('Protection', 'Haste and shroud for free.'),
    'Swiftfoot Boots': ('Protection', 'Haste and hexproof for Vren or a key Rat.'),
    # lands
    'Swarmyard': ('Land', 'Regenerates a Rat, so Rats attack and block without dying.'),
    'Three Tree City': ('Land', 'Name Rat and it taps for a mana per Rat you control.'),
    'Mudflat Village': ('Land', 'Black mana for creatures, and it sacrifices to return a Rat card to hand.'),
    'Bojuka Bog': ('Land', 'Exiles a player\'s graveyard when it enters.'),
    'Command Tower': ('Land', 'Taps for either color with no drawback.'),
    'Exotic Orchard': ('Land', 'In a four-player game it almost always taps for both colors.'),
    'Path of Ancestry': ('Land', 'Either color, and scry 1 when you cast a Rat with it.'),
    'Watery Grave': ('Land', 'Untapped dual for 2 life, an Island and a Swamp.'),
    'Sunken Hollow': ('Land', 'Island Swamp dual, untapped with two basics out.'),
    'Drowned Catacomb': ('Land', 'Dual that comes in untapped once you have an Island or Swamp.'),
    'Choked Estuary': ('Land', 'Untapped dual if you show an Island or Swamp.'),
    'Shipwreck Marsh': ('Land', 'Untapped dual once you have two other lands.'),
    'Tainted Isle': ('Land', 'Untapped dual while you have a Swamp.'),
    'Underground River': ('Land', 'Untapped dual for 1 damage.'),
    'Darkwater Catacombs': ('Land', 'Turns one mana into blue and black.'),
    'Island': ('Land', 'Basics for blue: Drowned Catacomb, Choked Estuary and Sunken Hollow need them.'),
    'Swamp': ('Land', 'Basics for black, most of the deck\'s mana: Tainted Isle needs a Swamp.'),
}

# Lenn's Chatterfang: a gift deck, hand-picked (not EDHREC's average) for Lenn, who likes token builds. Bracket 3:
# three Game Changers (Gaea's Cradle, Demonic Tutor, Seedborn Muse), no two-card infinite combos (Earthcraft + Squirrel
# Nest and Ivy Lane Denizen + Scurry Oak are left out for that, and Pitiless Plunderer too: with Chatterfang it loops by
# itself, Commander Spellbook's two-card combo), no land destruction, no extra turns. It will be
# proxied, so price didn't limit the picks. Compared with the average deck it plays more token makers, a third
# doubler-style replacement (Tippy-Toe), more anthems and overrun finishers, and fewer drain-only cards.
LENN = {
    'Chatterfang, Squirrel General': ('Commander', 'Every token you make comes with that many Squirrels, and spare Squirrels become removal.'),
    # token makers
    'Chitterspitter': ('Token maker', 'A Squirrel for {G} (two with Chatterfang), and it grows every Squirrel each upkeep.'),
    'Deep Forest Hermit': ('Token maker', 'Four Squirrels on entering (eight with Chatterfang), and Squirrels get +1/+1.'),
    'Deranged Hermit': ('Token maker', 'Four Squirrels (eight), and Squirrels get +1/+1; skip the echo and sacrifice it to Ashnod\'s Altar or Skullclamp it.'),
    'Hazel of the Rootbloom': ('Token maker', 'Copies a token each end step (two if it is a Squirrel), and taps tokens for mana.'),
    "Hazel's Brewmaster": ('Token maker', 'A Food and a Squirrel every time it enters or attacks.'),
    'Peregrin Took': ('Token maker', 'Every token creation adds a Food, and Chatterfang adds a Squirrel for that Food.'),
    'Tippy-Toe, Terrific Partner': ('Token maker', 'Like Peregrin: every token creation adds a Food (and its Squirrel), and gaining life draws a card each end step.'),
    'The Unbeatable Squirrel Girl': ('Token maker', 'A Squirrel when it enters or attacks, and for four mana doubles your Squirrels.'),
    'Scurry of Squirrels': ('Token maker', 'Myriad makes attacking copies of it each combat, each with a Squirrel.'),
    'Scurry Oak': ('Token maker', 'Evolves as bigger creatures arrive, and each counter makes a Squirrel (two with Chatterfang).'),
    'Camellia, the Seedmiser': ('Token maker', 'Sacrificing Food makes Squirrels, and other Squirrels get menace.'),
    'Tendershoot Dryad': ('Token maker', 'A Saproling at the start of every player\'s upkeep (plus a Squirrel each), and they get +2/+2 once you control ten permanents.'),
    'Bitterblossom': ('Token maker', 'A flying Faerie (and a Squirrel) every upkeep for two mana.'),
    'Garruk, Cursed Huntsman': ('Token maker', 'Two Wolves a turn (plus two Squirrels), or kill a creature and draw.'),
    'Squirrel Nest': ('Token maker', 'Turns a land into a Squirrel every turn; two with Chatterfang, and every turn with Seedborn Muse.'),
    'Scute Swarm': ('Token maker', 'An Insect (and a Squirrel) per land played; at six lands it copies itself.'),
    'Chatterstorm': ('Token maker', 'Storm: a Squirrel for every spell cast before it this turn, each doubled.'),
    'Swarmyard Massacre': ('Token maker', 'Four Squirrels, then every creature that isn\'t a Squirrel, Rat, Insect or Spider gets −1/−1 per Squirrel you have.'),
    'Verdant Command': ('Token maker', 'Four Squirrels at instant speed, or exile a graveyard card or gain 3 life.'),
    'Pest Infestation': ('Token maker', 'Destroys X artifacts or enchantments and makes twice X Pests (plus as many Squirrels).'),
    'Rootcast Apprenticeship': ('Token maker', 'Copy a token, make a Squirrel, add counters or make someone sacrifice an artifact.'),
    # token doublers
    'Doubling Season': ('Token doubler', 'Doubles every token, Chatterfang\'s Squirrels included, and every counter.'),
    'Parallel Lives': ('Token doubler', 'Doubles every token, Chatterfang\'s Squirrels included.'),
    'Second Harvest': ('Token doubler', 'Copies every token at instant speed, and Chatterfang adds that many Squirrels again.'),
    'Academy Manufactor': ('Token doubler', 'Each Food, Treasure or Clue becomes one of each, so three Squirrels.'),
    # payoffs
    'Seedborn Muse': ('Payoff', 'Untaps everything on every player\'s turn: Squirrel Nest, Chitterspitter and Gaea\'s Cradle make Squirrels or mana four times a round.'),
    'Squirrel Sovereign': ('Payoff', 'Other Squirrels get +1/+1.'),
    'The Odd Acorn Gang': ('Payoff', 'Squirrels pump each other, and Squirrel hits draw cards.'),
    'Honored Dreyleader': ('Payoff', 'A +1/+1 counter for every Squirrel and Food that enters.'),
    'Champion of Lambholt': ('Payoff', 'Grows with every creature that enters, and nothing smaller can block your creatures.'),
    'Sword of the Squeak': ('Payoff', 'Attaches free to each Squirrel that enters and grows with every 1/1.'),
    'Beastmaster Ascension': ('Payoff', 'Seven attackers and everything gets +5/+5.'),
    'Craterhoof Behemoth': ('Payoff', 'Every creature gets trample and +X/+X for your creature count: with a board of tokens, the game ends.'),
    # drain
    'Zulaport Cutthroat': ('Drain', 'Each of your creatures dying drains every opponent for 1.'),
    'Mirkwood Bats': ('Drain', 'Each token made or sacrificed pings every opponent.'),
    "Nadier's Nightblade": ('Drain', 'Each token leaving drains every opponent for 1.'),
    'The Meathook Massacre': ('Drain', 'Each of your creatures dying drains every opponent, and a small X sweeps away little blockers (keep it below your anthems).'),
    'Valley Rotcaller': ('Drain', 'Attacks drain 1 per other Squirrel.'),
    # sac outlets
    "Ashnod's Altar": ('Sac outlet', 'Free sacrifice that turns each Squirrel into two mana and sets off every death trigger.'),
    'Ravenous Squirrel': ('Sac outlet', 'Sacrifice anything to draw, and it grows.'),
    # draw
    'Skullclamp': ('Draw', 'Equip a 1/1 Squirrel for 1: two cards.'),
    'Toski, Bearer of Secrets': ('Draw', 'A card for each creature that hits a player.'),
    'Deadly Dispute': ('Draw', 'Sacrifice a Squirrel: draw two, plus a Treasure and a Squirrel.'),
    'Idol of Oblivion': ('Draw', 'A card on any turn you made a token.'),
    'Black Market Connections': ('Draw', 'Cards, a Treasure or a Shapeshifter each turn, each token bringing a Squirrel.'),
    'Shamanic Revelation': ('Draw', 'A card per creature: a full grip off a board of tokens.'),
    # ramp
    'Sol Ring': ('Ramp', 'Two extra mana from turn one.'),
    'Arcane Signet': ('Ramp', 'Black or green, so Chatterfang lands a turn early.'),
    'Birds of Paradise': ('Ramp', 'Turn-one mana of any color.'),
    'Gilded Goose': ('Ramp', 'Food (and a Squirrel) on entering, and Food into mana.'),
    'Jaheira, Friend of the Forest': ('Ramp', 'Every token taps for {G}.'),
    'Cryptolith Rite': ('Ramp', 'Every creature taps for any color, Squirrels included.'),
    'Tireless Provisioner': ('Ramp', 'A Food or Treasure (and a Squirrel) per land played.'),
    'Prosperous Innkeeper': ('Ramp', 'A Treasure (and a Squirrel) on entering, and 1 life per creature that enters, which turns on Tippy-Toe\'s draw.'),
    "Nature's Lore": ('Ramp', 'An untapped Forest (Bayou or Overgrown Tomb) for two.'),
    # tutors
    'Demonic Tutor': ('Tutor', 'Finds the doubler, Craterhoof, or whatever the table needs answered.'),
    "Green Sun's Zenith": ('Tutor', 'Finds any green creature: Deranged Hermit, Hazel, Craterhoof.'),
    # removal and protection
    "Assassin's Trophy": ('Removal', 'Destroys any permanent at instant speed.'),
    'Beast Within': ('Removal', 'Destroys any permanent; its owner gets a 3/3.'),
    'Deadly Rollick': ('Removal', 'Free with Chatterfang out: exile a creature.'),
    'Saw in Half': ('Removal', 'Kills a creature, or splits one of yours into two tokens (and two Squirrels).'),
    'Maelstrom Pulse': ('Removal', 'Destroys a permanent and every copy of it, for example an opponent\'s token army.'),
    'Heroic Intervention': ('Protection', 'Hexproof and indestructible for the whole board against a wipe.'),
    'Arachnogenesis': ('Protection', 'Stops a big attack and makes a Spider (and a Squirrel) per attacker.'),
    # lands
    "Gaea's Cradle": ('Land', 'A green mana per creature: tokens become mana.'),
    'Swarmyard': ('Land', 'Regenerates a Squirrel.'),
    'Yavimaya, Cradle of Growth': ('Land', 'Every land is a Forest: green from every land and forestwalk for Chatterfang.'),
    'Oran-Rief, the Vastwood': ('Land', 'A +1/+1 counter on each green creature that entered this turn.'),
    'Three Tree City': ('Land', 'Name Squirrel: a mana per Squirrel.'),
    'Phyrexian Tower': ('Land', 'Sacrifice a Squirrel for {B}{B}.'),
    'Fountainport': ('Land', 'Sacrifice a token to draw; makes Fish and Treasure (each with a Squirrel).'),
    'Bojuka Bog': ('Land', 'Exiles a graveyard on entering.'),
    'Boseiju, Who Endures': ('Land', 'A Forest that is also an instant answer to an artifact, enchantment or nonbasic land.'),
    'Urborg, Tomb of Yawgmoth': ('Land', 'Every land is a Swamp too, so black from every land.'),
    'Command Tower': ('Land', 'Either color.'),
    'Bayou': ('Land', 'Untapped Swamp Forest; fetchable.'),
    'Overgrown Tomb': ('Land', 'Untapped Swamp Forest; fetchable.'),
    'Verdant Catacombs': ('Land', 'Fetches Bayou or Overgrown Tomb.'),
    'Polluted Delta': ('Land', 'Fetches a Swamp: Bayou or Overgrown Tomb.'),
    'Misty Rainforest': ('Land', 'Fetches a Forest: Bayou or Overgrown Tomb.'),
    'Woodland Cemetery': ('Land', 'Untapped dual with a Swamp or Forest out.'),
    'Llanowar Wastes': ('Land', 'Untapped dual for 1 damage.'),
    'Twilight Mire': ('Land', 'One mana into two of black and green.'),
    'Undergrowth Stadium': ('Land', 'Untapped dual with two or more opponents.'),
    'Necroblossom Snarl': ('Land', 'Untapped dual if you show a Swamp or Forest.'),
    'Blooming Marsh': ('Land', 'Untapped dual early.'),
    'Darkbore Pathway': ('Land', 'Black or green side, untapped.'),
    'Forest': ('Land', 'Seven: Nature\'s Lore and the duals want them.'),
    'Swamp': ('Land', 'Five, for the black duals.'),
}

# Lenn's deck at Bracket 2: the four cards that make it Bracket 3 swapped out (three Game Changers, and Peregrin Took,
# whose Food loops with Camellia in three- and four-card infinite combos). Same order, so the swap is card for card.
LENN_B2_SWAPS = [
    ("Gaea's Cradle", 'Golgari Rot Farm', ('Land', 'Taps for two mana; stands in for Gaea\'s Cradle, a Game Changer.')),
    ('Demonic Tutor', 'Sylvan Library', ('Draw', 'Sees three cards a turn and keeps the best (or pays 4 life each for more); stands in for Demonic Tutor, a Game Changer.')),
    ('Seedborn Muse', 'Drey Keeper', ('Token maker', 'Two Squirrels (four with Chatterfang), and {3}{B} gives every Squirrel +1/+0 and menace; stands in for Seedborn Muse, a Game Changer.')),
    ('Peregrin Took', 'Bastion of Remembrance', ('Drain', 'A creature token (and a Squirrel) on entering, and each of your creatures dying drains every opponent; stands in for Peregrin Took, whose Food loops with Camellia.')),
]
_sw = {a: (b, w) for a, b, w in LENN_B2_SWAPS}
LENN_B2 = {_sw[n][0] if n in _sw else n: _sw[n][1] if n in _sw else v for n, v in LENN.items()}

# Lenn's Camellia: the replacement for Lenn's Chatterfang, after Reddit's review said Chatterfang plays far above a table
# of new players on precons. Bracket 2 by power, not just on paper. The user's rule: almost every card makes Squirrels,
# and anything else needs a good reason. Camellia turns every Food sacrificed into a Squirrel, so a card counts if it
# makes Squirrel tokens (Squirrel maker), makes Food (Food maker) or sacrifices Food (Food eater); the few others say why.
# Left out on purpose: Chatterfang (what we moved away from), Peregrin Took and Tippy-Toe (Tippy-Toe + Ninja Pizza +
# Camellia is an infinite loop on Commander Spellbook; Peregrin's Food loops the same way), Academy Manufactor, Ashnod's
# Altar, Doubling Season, Parallel Lives, Skullclamp, Craterhoof, Beastmaster Ascension, and fetch lands and original
# duals. Spellbook (find-my-combos, estimate-bracket) finds no combos and no Game Changers. Roles 'A/B': A is the filter
# and sort role, B a second job.
CAMELLIA = {
    'Camellia, the Seedmiser': ('Commander', 'Every Food you sacrifice becomes a 1/1 Squirrel, other Squirrels get menace, and {2}, Forage pumps every other Squirrel.'),
    # makes Squirrel tokens itself
    'Chatter of the Squirrel': ('Squirrel maker', 'A Squirrel for {G}, and another from the graveyard for {1}{G}.'),
    'Squirrel Sanctuary': ('Squirrel maker', 'A Squirrel for {G}, and it comes back to hand when a nontoken creature dies, to cast again.'),
    'Nested Shambler': ('Squirrel maker', 'A one-drop that leaves Squirrels behind when it dies (as many as its power).'),
    'Chatterstorm': ('Squirrel maker', 'A Squirrel for each spell cast before it this turn: a late-game burst.'),
    'Verdant Command': ('Squirrel maker/Removal', 'Two Squirrels at instant speed, plus graveyard exile, 3 life or a stopped planeswalker.'),
    'Bushy Bodyguard': ('Squirrel maker', 'Pay offspring {2} for a token copy (a Squirrel), and foraging a Food grows it and makes another via Camellia.'),
    'Chitterspitter': ('Squirrel maker', 'A Squirrel for {G} every turn, and every Squirrel grows each upkeep.'),
    'Squirrel Nest': ('Squirrel maker', 'Turns a land into a Squirrel every turn.'),
    'Scurry Oak': ('Squirrel maker', 'A Squirrel each time it gets +1/+1 counters: Camellia\'s forage and Honored Dreyleader-sized creatures feed it.'),
    'Scurry of Squirrels': ('Squirrel maker', 'Myriad: attacking token copies of it (each a Squirrel) at every other opponent.'),
    'Cloakwood Hermit': ('Squirrel maker', 'Gives Camellia two Squirrels each end step a creature died, chump blockers included.'),
    'The Unbeatable Squirrel Girl': ('Squirrel maker', 'A Squirrel when she enters or attacks, and late game {1}{G}{G}{G} doubles your Squirrels.'),
    'Hazel of the Rootbloom': ('Squirrel maker/Ramp', 'Two copies of a Squirrel token every end step, and taps your tokens for mana.'),
    'Rootcast Apprenticeship': ('Squirrel maker', 'Three modes: Squirrels, copies of your best token, counters, or an artifact edict.'),
    'Acorn Harvest': ('Squirrel maker', 'Two Squirrels, then two more from the graveyard (flashback).'),
    'Second Harvest': ('Squirrel maker', 'Copies every token you have at instant speed, Squirrels and Food alike.'),
    'For the Common Good': ('Squirrel maker/Protection', 'X copies of a token, then all your tokens are indestructible until your next turn: answers a board wipe.'),
    'Deep Forest Hermit': ('Squirrel maker', 'Four Squirrels on entering, and Squirrels get +1/+1 while it stays.'),
    'Drey Keeper': ('Squirrel maker', 'Two Squirrels, and {3}{B} gives them +1/+0 and menace for the swing.'),
    'Swarmyard Massacre': ('Squirrel maker/Removal', 'Two Squirrels, then every non-Squirrel creature shrinks by your Squirrel count: a mostly one-sided wipe.'),
    # makes Food: Camellia turns each one into a Squirrel when it is eaten
    'Gilded Goose': ('Food maker/Ramp', 'Food on entering and for {1}{G}, and eats Food for mana (a Squirrel each time).'),
    'Many Partings': ('Food maker/Ramp', 'A basic land to hand and a Food, for {G}.'),
    "Scavenger's Talent": ('Food maker', 'A Food each turn one of your creatures dies, so Squirrels lost in combat come back.'),
    "Witch's Oven": ('Food maker', 'Sacrifice a creature for Food (two if it is big), and the Food becomes a Squirrel.'),
    'Vinereap Mentor': ('Food maker', 'A Squirrel that leaves a Food when it enters and when it dies.'),
    'Bakersbane Duo': ('Food maker', 'A two-drop Squirrel with a Food.'),
    'Pippin, Warden of Isengard': ('Food maker', 'Food for {1} every turn, and four Foods give the team +3/+3 and haste (plus four Squirrels).'),
    'Trail of Crumbs': ('Food maker/Draw', 'A Food, and each Food eaten digs two cards deep for a permanent.'),
    'Savor': ('Food maker/Removal', '−2/−2 at instant speed, plus a Food.'),
    'Pawpatch Formation': ('Food maker/Removal', 'Kills a flier or an enchantment, or draws a card and makes a Food.'),
    'Revive the Shire': ('Food maker', 'Gets back any permanent card, plus a Food.'),
    'Campsite Cuisine': ('Food maker', 'Food from each legend (Camellia, Hazel, Squirrel Girl, Pippin, Greta, Meatsqueak, Elanor, Toski, Acorn Gang), and Foods pump attackers.'),
    'Tireless Provisioner': ('Food maker/Ramp', 'A Food or a Treasure for every land played.'),
    'Heaped Harvest': ('Food maker/Ramp', 'A Food that fetches a basic land when it enters and again when eaten.'),
    'Meatsqueak, Hoard Lord': ('Food maker', 'A Squirrel that makes a Food each turn something dies, and gives Squirrels +3/+3 per seven Foods.'),
    'Savvy Hunter': ('Food maker/Draw', 'A Food each time it attacks or blocks, and two Foods draw a card.'),
    'Greta, Sweettooth Scourge': ('Food maker/Draw', 'A Food, then eats Food for +1/+1 counters or cards.'),
    'Tainted Treats': ('Food maker/Removal', 'Kills an artifact or creature at instant speed, and a Food if it was small.'),
    'Hot Dog Cart': ('Food maker/Ramp', 'A mana rock of any color that comes with a Food.'),
    'Nuka-Cola Vending Machine': ('Food maker/Ramp', 'Food for {1} every turn, and each Food eaten leaves a Treasure too.'),
    'Ninja Pizza': ('Food maker/Ramp', 'A Food every turn, and any Food can be eaten for mana (a Squirrel each time).'),
    "Hazel's Brewmaster": ('Food maker', 'A Squirrel that makes Food on entering and attacking, and shares graveyards\' abilities with your Foods.'),
    "Night of the Sweets' Revenge": ('Food maker/Ramp', 'Every Food taps for {G}, and late it gives the team +X/+X per Food: a finisher.'),
    'Bake into a Pie': ('Food maker/Removal', 'Kills any creature at instant speed, plus a Food.'),
    'Elanor Gardner': ('Food maker/Ramp', 'A Food, and a basic land each turn you ate one.'),
    'Stew the Coneys': ('Food maker/Removal', 'One of your creatures fights one of theirs one-sidedly, plus a Food.'),
    'Midnight Snack': ('Food maker/Drain', 'A Food each turn you attack, and late it drains an opponent for the life you gained.'),
    'Spider Food': ('Food maker/Removal', 'Kills an artifact, enchantment or flier, plus a Food.'),
    "Bumbleflower's Sharepot": ('Food maker/Removal', 'A Food now, and later {5} destroys any nonland permanent.'),
    'Lembas': ('Food maker/Draw', 'A Food that draws a card, and it shuffles back in after it is eaten.'),
    # eats Food: each forage or Food sacrifice is a Squirrel from Camellia
    'Thornvault Forager': ('Food eater/Ramp', 'A Squirrel mana dork that eats Food for two mana, and finds a Squirrel late.'),
    'Ravenous Squirrel': ('Food eater/Draw', 'Sacrifices Food or creatures to draw, growing each time.'),
    'Corpseberry Cultivator': ('Food eater', 'Eats a Food every combat to grow (and makes a Squirrel).'),
    'Treetop Sentries': ('Food eater/Draw', 'A Squirrel with reach that eats a Food to draw.'),
    'Curious Forager': ('Food eater', 'A Squirrel that eats a Food to get back any permanent card.'),
    'Feed the Cycle': ('Food eater/Removal', 'Kills a creature or planeswalker; pay with a Food and get a Squirrel back.'),
    # Squirrels that reward having Squirrels
    'Squirrel Sovereign': ('Squirrel payoff', 'A Squirrel lord: every other Squirrel gets +1/+1.'),
    'Honored Dreyleader': ('Squirrel payoff', 'A Squirrel that grows with every Squirrel and Food that arrives.'),
    'The Odd Acorn Gang': ('Squirrel payoff/Draw', 'Squirrels pump each other, and Squirrel hits draw cards.'),
    'Valley Rotcaller': ('Squirrel payoff/Drain', 'A Squirrel whose attacks drain 1 per other Squirrel: how the deck closes games.'),
    'Toski, Bearer of Secrets': ('Squirrel payoff/Draw', 'An indestructible Squirrel that draws a card per creature that hits.'),
    # not Squirrels, with a reason
    'Sol Ring': ('Ramp', 'Not a Squirrel: two mana on turn one, in every precon, so it keeps the deck at precon level, not above it.'),
    'Heroic Intervention': ('Protection', 'Not a Squirrel: a board wipe is the one thing that beats a token deck, and this stops it.'),
    # lands: 35 and a land-or-trick
    'Revitalizing Repast': ('Land/Protection', 'A land when you need one, or a counter and indestructible to save a creature from removal.'),
    'Command Tower': ('Land', 'Either color, untapped.'),
    'Gingerbread Cabin': ('Land', 'A Forest that makes a Food when it enters untapped (three other Forests).'),
    'The Shire': ('Land', 'Untapped with a legend out, and makes Food late.'),
    'Restless Cottage': ('Land', 'Either color; late it attacks as a 4/4 that makes a Food.'),
    'Swarmyard': ('Land', 'Regenerates a Squirrel.'),
    'Oakhollow Village': ('Land', 'Green for creatures, and +1/+1 counters on Squirrels that just arrived.'),
    'Mudflat Village': ('Land', 'Black for creatures, and sacrifices to get a Squirrel card back.'),
    'Woodland Cemetery': ('Land', 'Untapped dual with a Swamp or Forest out.'),
    'Llanowar Wastes': ('Land', 'Untapped dual for 1 damage.'),
    'Golgari Rot Farm': ('Land', 'Taps for two.'),
    'Jungle Hollow': ('Land', 'Dual with 1 life.'),
    'Golgari Guildgate': ('Land', 'Dual.'),
    'Temple of Malady': ('Land', 'Dual with scry 1.'),
    'Evolving Wilds': ('Land', 'Fetches a basic.'),
    'Path of Ancestry': ('Land', 'Either color, and scry when it casts a Squirrel.'),
    'Necroblossom Snarl': ('Land', 'Untapped dual if you show a Swamp or Forest.'),
    'Twilight Mire': ('Land', 'One mana into two of black and green.'),
    'Undergrowth Stadium': ('Land', 'Untapped dual with two or more opponents.'),
    'Three Tree City': ('Land', 'Name Squirrel: a mana per Squirrel.'),
    'Forest': ('Land', 'Ten: the deck is mostly green, and Gingerbread Cabin wants Forests.'),
    'Swamp': ('Land', 'Six, for the black cards.'),
}

BREWS = {
    'chatterfang': {'name': 'Chatterfang Squirrels', 'edhrec': 'chatterfang-squirrel-general', 'why': CHATTERFANG, 'colors': 'black-green'},
    'marrow-gnawer': {'name': 'Marrow-Gnawer Rats', 'edhrec': 'marrow-gnawer', 'why': MARROW, 'colors': 'mono-black'},
    'vren': {'name': 'Vren Rats', 'edhrec': 'vren-the-relentless', 'why': VREN, 'colors': 'blue-black'},
    # hand-picked: the list is LENN itself (not EDHREC's average deck); EDHREC's numbers still show where it has them
    'chatterfang-lenn': {'name': "Lenn's Chatterfang Tokens (Bracket 3)", 'edhrec': 'chatterfang-squirrel-general', 'why': LENN, 'colors': 'black-green',
                         'pick': {'Forest': 7, 'Swamp': 5}, 'bracket': 3,
                         'about': 'A gift deck for Lenn, who likes token builds. Bracket 3: three Game Changers (Gaea\'s Cradle, Demonic Tutor, '
                                  'Seedborn Muse), no two-card infinite combos, no land destruction or extra turns. Built to be proxied, so price '
                                  'didn\'t limit the picks. Every card is Commander-legal.'},
    'chatterfang-lenn-b2': {'name': "Lenn's Chatterfang Tokens (Bracket 2)", 'edhrec': 'chatterfang-squirrel-general', 'why': LENN_B2, 'colors': 'black-green',
                            'pick': {'Forest': 7, 'Swamp': 5}, 'bracket': 2,
                            'about': 'The Bracket 2 version of Lenn\'s gift deck: the Bracket 3 list with four swaps. No Game Changers, no '
                                     'infinite combos of any size (Commander Spellbook finds none), one tutor (Green Sun\'s Zenith), no land '
                                     'destruction or extra turns. Every card is Commander-legal.'},
    'camellia-lenn': {'name': "Lenn's Camellia Squirrels (Bracket 2)", 'edhrec': 'camellia-the-seedmiser', 'why': CAMELLIA, 'colors': 'black-green',
                      'pick': {'Forest': 10, 'Swamp': 6}, 'show_why': True, 'gift': 'a gift for Lenn',
                      'about': 'Lenn\'s gift deck, rebuilt around Camellia after Reddit\'s review found Chatterfang far too strong for a table of '
                               'new players on precons. Almost every card makes Squirrels: Squirrel tokens itself, or Food, which Camellia turns '
                               'into a Squirrel when it is eaten, or it eats Food. The few that don\'t say why they are here. Bracket 2: no Game '
                               'Changers, no infinite combos (Commander Spellbook finds none), one Squirrel tutor, no land destruction or extra '
                               'turns, and no doublers, Craterhoof or fetch lands. Average mana value 2.7, with 36 lands. Every card is Commander-legal.'},
}

def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers=dict(UA, **({'Content-Type': 'application/json'} if data else {})))
    for i in range(4):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=60).read())
        except Exception:
            if i == 3: raise
            time.sleep(2 ** i)

def cheapest(name):
    q = urllib.parse.quote(f'!"{name}" game:paper')
    try:
        r = get(f'https://api.scryfall.com/cards/search?q={q}&unique=prints')
        ps = [float(x['prices'].get('usd') or x['prices'].get('usd_foil')) for x in r['data'] if x['prices'].get('usd') or x['prices'].get('usd_foil')]
        return min(ps) if ps else None
    finally:
        time.sleep(0.11)

def build(slug, b):
    edh = 'https://json.edhrec.com/pages'
    page = get(f"{edh}/commanders/{b['edhrec']}.json")
    decks = page['container']['json_dict']['card']['num_decks']
    stats = {}
    for l in page['container']['json_dict']['cardlists']:
        for v in l['cardviews']: stats.setdefault(v['name'], [round(v['num_decks'] / v['potential_decks'], 3), round(v['synergy'], 3)])
    if 'pick' in b:  # hand-picked list: the reasons dict in order, commander first, basics counted in 'pick'
        lst = [(n, b['pick'].get(n, 1)) for n in b['why']]
        cmd = lst[0][0]
    else:
        avg = get(f"{edh}/average-decks/{b['edhrec']}.json")
        cmd = avg['deck']['commander'][0]
        lst = [(cmd, 1)] + [(n, q) for t, cs in avg['deck']['cards'].items() for n, q in cs]
    assert sum(q for _, q in lst) == 100, f'{sum(q for _, q in lst)} cards, not 100'
    miss = [n for n, _ in lst if n not in b['why']]
    assert not miss, f'no reason written for: {miss}'
    found = {}
    for i in range(0, len(lst), 75):
        r = get('https://api.scryfall.com/cards/collection', json.dumps({'identifiers': [{'name': n} for n, _ in lst[i:i + 75]]}).encode())
        for c in r['data']: found[c['name']] = found[c['name'].split(' // ')[0]] = c
        time.sleep(0.15)
    ALL = []
    for n, q in lst:
        c = found[n]
        faces = c.get('card_faces') or []
        iu = c.get('image_uris') or faces[0]['image_uris']
        colors = c.get('colors', faces[0].get('colors', []) if faces else [])
        role, why = b['why'][n]
        r = {'n': n, 'p': cheapest(n), 'q': q, 's': c['set'].upper(), 't': c['type_line'],
             'i': iu['normal'], 'm': int(c.get('cmc', 0)), 'c': ''.join(x for x in 'WUBRG' if x in colors), 'k': role.split('/'),
             'u': c['scryfall_uri'].split('?')[0]}
        if n in stats: r['e'] = stats[n]
        if b.get('show_why'): r['w'] = why  # this deck shows each card's reason (the user: anything not a Squirrel maker needs one)
        if c['legalities'].get('commander') != 'legal': r['note'] = 'Not Commander-legal'  # always flagged (house rule)
        if n == cmd: r['e'] = [1, 0]
        if len(faces) > 1 and not c.get('image_uris'): r['b'] = faces[1]['image_uris']['normal']
        ALL.append(r)
    ALL.sort(key=lambda r: (ROLES.index(r['k'][0]), -(r['e'][0] if 'e' in r else 0)))
    total = sum((r['p'] or 0) * r['q'] for r in ALL)
    edh_page = f"https://edhrec.com/commanders/{b['edhrec']}"
    avg_page = f"https://edhrec.com/average-decks/{b['edhrec']}"
    lead = (f'<p><b>The list</b> is hand-picked. {html.escape(b["about"])}</p>' if 'pick' in b else
            f'<p><b>The list</b> is <a href="{avg_page}" target="_blank" rel="noopener">EDHREC\'s average {html.escape(cmd.split(",")[0])} deck</a>: '
            f'the cards played most across the {decks:,} {html.escape(cmd.split(",")[0])} decks EDHREC has (pulled {time.strftime("%b %-d %Y")}).</p>')
    if slug.startswith('chatterfang-lenn'):  # Lenn's two versions: the swap list and the proxy order, on both pages
        li = ''.join(f'<li>{html.escape(a)} → {html.escape(c)}</li>' for a, c, _ in LENN_B2_SWAPS)
        lead += ('<p><b>Two versions.</b> <a href="chatterfang-lenn.html">Bracket 3</a> and <a href="chatterfang-lenn-b2.html">Bracket 2</a> '
                 f'share 96 cards. To go from Bracket 3 to Bracket 2, swap:</p><ul>{li}</ul>'
                 '<p><a href="chatterfang-lenn-proxies.txt">Proxy order</a>: every card both versions need, one of each, basics left out.</p>')
    srcs = (lead + f'<p><b>Under each card</b>: its role (from its rules text: the <i>card text</i> link, on Scryfall), '
            f'then EDHREC\'s numbers from the <a href="{edh_page}" target="_blank" rel="noopener">commander page</a>: the share of those decks that play it, '
            f'and synergy, how much more often it is played here than in other {b["colors"]} decks (near 0% means a generic staple)'
            f'{"; cards EDHREC has no numbers for show only their role" if "pick" in b else ""}.</p>'
            '<p><b>Prices</b> are the cheapest paper printing on Scryfall.</p>')
    cfg = {'slug': 'brew-' + slug, 'deck': b['name'], 'set': '', 'cmd': cmd, 'alt': None, 'decks': decks, 'edh': edh_page, 'srcs': srcs,
           'sub': (f'{sum(r["q"] for r in ALL)} cards · Bracket {b.get("bracket", 2)} · {"Squirrels" if b.get("show_why") else "tokens"} · {b.get("gift", "a gift for Lenn")} (to proxy; ${total:,.0f} in singles)' if 'pick' in b else
                   f'{sum(r["q"] for r in ALL)} cards · ${total:,.0f} in singles · from {decks:,} decks on EDHREC')}
    t = open(os.path.join(HERE, 'brew-template.html')).read()
    t = (t.replace('__TITLE__', html.escape(b['name'])).replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, slug + '.html'), 'w').write(t)
    if slug.startswith('chatterfang-lenn'):  # the proxy order covers both versions, so either can be built from one print run
        names = sorted({n for n in list(LENN) + list(LENN_B2) if n not in ('Forest', 'Swamp')})
        open(os.path.join(OUT, 'chatterfang-lenn-proxies.txt'), 'w').write(
            "Lenn's Chatterfang Tokens: proxy order for both versions (Bracket 3 and Bracket 2), basics left out.\n"
            f"{len(names)} cards. Bracket 3 only: {', '.join(a for a, _, _ in LENN_B2_SWAPS)}. "
            f"Bracket 2 only: {', '.join(c for _, c, _ in LENN_B2_SWAPS)}.\n\n" + ''.join(f'1 {n}\n' for n in names))
    if slug in ('chatterfang-lenn-b2', 'camellia-lenn'):  # paste-ready for Moxfield's import box (for Reddit reviews): plain "qty name" lines only
        open(os.path.join(OUT, slug + '-moxfield.txt'), 'w').write(
            ''.join(f'{b["pick"].get(n, 1)} {n}\n' for n in b['why']))
    print(f'{slug}: {sum(r["q"] for r in ALL)} cards, ${total:.2f}, from {decks} decks; no price: {[r["n"] for r in ALL if r["p"] is None]}')

if __name__ == '__main__':
    for s in sys.argv[1:] or BREWS:
        build(s, BREWS[s])
