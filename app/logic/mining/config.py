""" Settings of the ore, and of the canisters it is lost in: sizes are in
pixels, speeds in px/s """

ORE_DENSITY = .25             # an asteroid holds ORE_DENSITY * radius² ore

# Ore lost in a crash floats away in canisters
CANISTER_UNITS = 10.          # ore per canister at most
CANISTER_SIZE = (22., 11.)
CANISTER_SPEED = (40., 120.)  # thrown away from what the ship hit
CANISTER_SPREAD = 70.         # degrees around that direction
CANISTER_SPIN = 120.          # degrees/s
CANISTER_MAX = 60             # beyond, the oldest ones vanish
# Once thrown, canisters slow down relative to the asteroids around them,
# then turn with them, or stop along with the sun
CANISTER_DRAG = .8
# Near a planet, they gather on an orbit close to it, each at its height
CANISTER_ORBIT_DRAG = .6
CANISTER_ORBIT_ALTITUDE = (120., 260.)  # above its surface
CANISTER_GATHER = .5          # a second, of how far they are from their orbit
CANISTER_GATHER_SPEED = 150.  # at most
CANISTER_FOLLOW_RANGE = 2000.
CANISTER_NEIGHBOR_PERIOD = .5  # seconds between looks for the neighbors
