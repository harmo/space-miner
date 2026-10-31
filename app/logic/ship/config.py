""" Settings of the ship, of its landing and of its work: sizes are in
pixels, speeds in px/s. The rest depends on its parts: see parts.py """

SHIP_MASS = 50.
# How fast the ship slows down when coasting: barely, it glides on, bent by
# gravity, for a score of seconds
SHIP_DRAG = .05
# However heavy its parts make it, a ship still flies
MIN_SPEED = 120.
MIN_THRUST = .4
MIN_TURN_SPEED = 1.5

# Fuel, burnt by thrusting and firing the laser: see parts.py and lasers.py
MIN_BURN = .25                # of what the hull burns, whatever is fitted
LOW_FUEL = .25                # of the tank, the gauge warns below
CRITICAL_FUEL = .1

# Heat of the hull, from 0 to 1 where it blows up, close to the sun
HEAT_GAIN = .25               # a second at the sun surface, unshielded
HEAT_COOLING = .05            # a second, always
HOT = .5                      # the gauge warns above
OVERHEATING = .8
REGOLITH_TINT = (.8, .62, .42)  # ships fully shielded take this color
SHELTER_COOLING = .3          # a second, docked to a sheltering station

# Landing legs, the ship stands on them on the ground
LEG_LENGTH = 4.               # behind the rear of the ship
LEG_SPREAD = 1.5              # beyond its sides
LEG_DEPLOY_TIME = .6          # seconds to unfold or fold them
LEG_COLOR = (.49, .54, .6)
LEG_OUTLINE = (.18, .22, .27)

# Crashes: touching anything is fatal, except landing softly on a ground
LANDING_MAX_SPEED = 120.      # relative to the body
RESPAWN_DELAY = 2.5           # seconds

# Landing, distances from the surface of the body
SHORTCUT_RANGE = 600.         # the shortcut shows up, faded
LANDING_RANGE = 250.          # and can be used
SHORTCUT_PULSE = 1.6          # seconds, the shortcut glows when usable
LANDING_DURATION = 3.         # seconds
LANDED_SPEED = 20.            # slower relative to the body is landed
LANDED_GAP = 2.               # and its legs closer to the ground than this
START_DIRECTION = -90.        # the ship starts on the ground closest to it
GROUND_DEPTH = .04            # ground is looked for this deep in the image
GROUND_SAFETY = 3             # degrees of ground beyond the ship sides

# Work: mining and picking canisters up
PICK_RADIUS = 40.             # click tolerance around asteroids, canisters
MINING_DISTANCE = 120.        # the locked ship holds this far from it
HOLD_GAIN = 1.5               # how fast the ship reaches its holding spot
# How fast the thrusters match the velocity needed to hold: 4 * HOLD_GAIN
# reaches the spot as fast as possible without overshooting it
HOLD_RESPONSE = 4 * HOLD_GAIN
LASER_RANGE = 200.            # from the nose of the ship
LASER_RATE = 3.               # rock extracted per second
PICKUP_HOLD = 40.             # the ship holds this far from a canister
PICKUP_RANGE = 70.            # and picks it up from this close
PICKUP_FRAGMENTS = 8
PICKUP_SPEED = (10., 40.)

# Exhaust trails, how much of them shows
TRAIL_HOLDING = .3            # while holding in front of what it works on
TRAIL_LANDING = .8
TRAIL_MAX = 800               # sparks at most
