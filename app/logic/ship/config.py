""" Settings of the ship, of its landing and of its work: sizes are in
pixels, speeds in px/s. The rest depends on its parts: see parts.py """

SHIP_DRAG = .3                # how fast the ship slows down when coasting
# However heavy its parts make it, a ship still flies
MIN_SPEED = 120.
MIN_THRUST = .4
MIN_TURN_SPEED = 1.5


# Crashes: touching anything is fatal, except landing softly on the Earth
LANDING_MAX_SPEED = 120.      # relative to the Earth


HOLD_GAIN = 1.5               # how fast the ship reaches its holding spot
# How fast the thrusters match the velocity needed to hold: 4 * HOLD_GAIN
# reaches the spot as fast as possible without overshooting it
HOLD_RESPONSE = 4 * HOLD_GAIN
LASER_RATE = 3.               # rock extracted per second
