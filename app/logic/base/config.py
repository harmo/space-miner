""" Settings of the base on the Earth """

UNLOAD_RATE = 15.             # units per second, into the depot

# Missions
# By tier of reputation: more of them for players who proved themselves
MISSION_OFFERS = (3, 4, 5, 6, 8)    # to choose from
MISSIONS_ACTIVE = (2, 3, 4, 6, 8)   # accepted at most
MISSION_AMOUNT = 15.          # units wanted of a mineral as common as iron
MISSION_BONUS = 1.5           # reward, times what the ore is worth

# Trade
RESALE = .5                   # parts sell back for this part of their price
ORE_SALE = .5                 # ore sells for this part of what it is worth

# Fuel, filled on landing: the ice of the depot first, then credits
ICE_FUEL = 2.                 # units of fuel a unit of ice makes
FUEL_PRICE = 2                # credits a unit
# Players out of ice and credits are given this part of their tank, not to
# be stuck on the Earth
FREE_RESERVE = .2
# Towing a ship out of fuel back to the Earth
TOW_BASE = 100                # credits
TOW_RATE = .02                # credits a pixel away from the Earth

# Reputation: missions validated to reach each tier of parts
TIER_MISSIONS = (0, 3, 8, 15, 25)
MISSION_GROWTH = .3           # bigger orders on each level, paying as much
# Rarer minerals are wanted more on higher levels: their frequencies are
# flattened by this much on each level
MISSION_RARER = .2

# Outposts, see outposts.py
PAD_WIDTH = 90.               # pixels, where ships land on their site
PAD_DIRECTION = 90.           # degrees, from the center of their body

# Refinery: rock of the depot crushed into what little it holds
CRUSH_RATE = 4.               # units of rock a second
# Found in a unit of rock, the rest is regolith
CRUSH_YIELDS = (('iron', .3), ('copper', .15), ('gold', .04), ('crystal', .02))
