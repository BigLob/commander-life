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
ROLES = ['Commander', 'Rat', 'Token maker', 'Token doubler', 'Payoff', 'Drain', 'Sac outlet', 'Draw', 'Ramp', 'Tutor',
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

BREWS = {
    'chatterfang': {'name': 'Chatterfang Squirrels', 'edhrec': 'chatterfang-squirrel-general', 'why': CHATTERFANG, 'colors': 'black-green'},
    'marrow-gnawer': {'name': 'Marrow-Gnawer Rats', 'edhrec': 'marrow-gnawer', 'why': MARROW, 'colors': 'mono-black'},
    'vren': {'name': 'Vren Rats', 'edhrec': 'vren-the-relentless', 'why': VREN, 'colors': 'blue-black'},
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
    page, avg = get(f"{edh}/commanders/{b['edhrec']}.json"), get(f"{edh}/average-decks/{b['edhrec']}.json")
    decks = page['container']['json_dict']['card']['num_decks']
    stats = {}
    for l in page['container']['json_dict']['cardlists']:
        for v in l['cardviews']: stats.setdefault(v['name'], [round(v['num_decks'] / v['potential_decks'], 3), round(v['synergy'], 3)])
    cmd = avg['deck']['commander'][0]
    lst = [(cmd, 1)] + [(n, q) for t, cs in avg['deck']['cards'].items() for n, q in cs]
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
             'i': iu['normal'], 'm': int(c.get('cmc', 0)), 'c': ''.join(x for x in 'WUBRG' if x in colors), 'k': [role],
             'u': c['scryfall_uri'].split('?')[0]}
        if n in stats: r['e'] = stats[n]
        if c['legalities'].get('commander') != 'legal': r['note'] = 'Not Commander-legal'  # always flagged (house rule)
        if n == cmd: r['e'] = [1, 0]
        if len(faces) > 1 and not c.get('image_uris'): r['b'] = faces[1]['image_uris']['normal']
        ALL.append(r)
    ALL.sort(key=lambda r: (ROLES.index(r['k'][0]), -(r['e'][0] if 'e' in r else 0)))
    total = sum((r['p'] or 0) * r['q'] for r in ALL)
    edh_page = f"https://edhrec.com/commanders/{b['edhrec']}"
    avg_page = f"https://edhrec.com/average-decks/{b['edhrec']}"
    srcs = (f'<p><b>The list</b> is <a href="{avg_page}" target="_blank" rel="noopener">EDHREC\'s average {html.escape(cmd.split(",")[0])} deck</a>: '
            f'the cards played most across the {decks:,} {html.escape(cmd.split(",")[0])} decks EDHREC has (pulled {time.strftime("%b %-d %Y")}).</p>'
            f'<p><b>Under each card</b>: its role (from its rules text: the <i>card text</i> link, on Scryfall), '
            f'then EDHREC\'s numbers from the <a href="{edh_page}" target="_blank" rel="noopener">commander page</a>: the share of those decks that play it, '
            f'and synergy, how much more often it is played here than in other {b["colors"]} decks (near 0% means a generic staple).</p>'
            '<p><b>Prices</b> are the cheapest paper printing on Scryfall.</p>')
    cfg = {'slug': 'brew-' + slug, 'deck': b['name'], 'set': '', 'cmd': cmd, 'alt': None, 'decks': decks, 'edh': edh_page, 'srcs': srcs,
           'sub': f'{sum(r["q"] for r in ALL)} cards · ${total:,.0f} in singles · from {decks:,} decks on EDHREC'}
    t = open(os.path.join(HERE, 'brew-template.html')).read()
    t = (t.replace('__TITLE__', html.escape(b['name'])).replace('/*CFG*/null', json.dumps(cfg, ensure_ascii=False))
          .replace('/*ALL*/[]', json.dumps(ALL, ensure_ascii=False, separators=(',', ':'))))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, slug + '.html'), 'w').write(t)
    print(f'{slug}: {sum(r["q"] for r in ALL)} cards, ${total:.2f}, from {decks} decks; no price: {[r["n"] for r in ALL if r["p"] is None]}')

if __name__ == '__main__':
    for s in sys.argv[1:] or BREWS:
        build(s, BREWS[s])
