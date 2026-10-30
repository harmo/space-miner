""" Settings of the solar system: sizes are in pixels, speeds in px/s """

# Sun
SUN_RADIUS = 600.
SUN_GRAVITY = 400.            # pull at its surface (px/s²)
SUN_GRAVITY_FALLOFF = 1.      # pull in 1/distance: it reaches everywhere

# Planets
FIRST_ORBIT = 2200.           # distance of the closest planet to the sun
# Between an orbit and the next, wider and wider outwards like in the real
# solar system, the belt around the sun taking an orbit of its own
ORBIT_GAPS = (1600., 1700., 1900., 2800., 2800., 3300., 3800., 4400.)
GAP_SPREAD = (.9, 1.15)       # each gap times as much, game after game
EARTH_ORBIT = 2               # the Earth is the third planet
BELT_AFTER = 3                # the belt around the sun, after the fourth
PLANET_SPEED = 40.            # on the first orbit, slower farther out
PLANET_RADIUS = (150., 350.)
PLANET_MASS = 1e6             # heavy enough not to be pushed by the ship
EARTH_RADIUS = 200.

GRAVITY = 1.25                # planet surface gravity is GRAVITY * radius
GRAVITY_FALLOFF = 2.          # planets pull in 1/distance²
GRAVITY_RANGE = 6.            # planets pull the ship up to this many radii

# Cérès, a big asteroid in the middle of the belt around the sun: the site
# of an outpost, never mined
CERES_RADIUS = 70.
CERES_GRAVITY = 40.           # at its surface, weak (px/s²)

# Moon and asteroids
MOON_RADIUS = 45.
MOON_ORBIT = 550.             # distance from the Earth's center
MOON_SPEED = 60.
MOON_MASS = 500.

BELT_COUNT = 3                # planets with an asteroid belt
BELT_ASTEROIDS = 30
BELT_WIDTH = (120., 350.)     # orbits start this far from the planet surface
BELT_SPEED = (30., 70.)
# The belt around the sun, between the fourth and the fifth planet
SUN_BELT_ASTEROIDS = 120
SUN_BELT_WIDTH = 1000.
SUN_BELT_SPEED = (.9, 1.1)    # times the speed of a planet on that orbit
ASTEROID_RADIUS = (4., 10.)
ASTEROID_MASS = 5.
ASTEROID_SPIN = 60.           # degrees/s

ORBIT_PULL = 2.               # how fast a bumped orbiter returns to its orbit

# Belts mined below this part of their asteroids grow back, until full
REGROW_THRESHOLD = .4
REGROW_TIME = 300.            # seconds for a whole belt
REGROW_AWAY = 3000.           # from the ship, out of its sight

# Swarms of rich asteroids, passing between the orbits of the planets
SWARM_EVERY = (300., 540.)    # seconds between them
SWARM_STAYS = 240.            # seconds
SWARM_ASTEROIDS = 12
SWARM_WIDTH = 300.            # across their orbit
SWARM_SPREAD = 8.             # degrees, along it
SWARM_RADIUS = (6., 12.)      # of its asteroids, bigger than in belts

# Solar flares: the sun warns, blazes, then leaves ejecta of the rarest ore
# on low orbits, which fall back into it
FLARE_EVERY = (360., 600.)    # seconds between them
FLARE_WARNING = 30.           # seconds told before
FLARE_BLAZE = 20.             # seconds
FLARE_SURGE = 4.              # times the heat of the sun, at its height
EJECTA_STAYS = 180.           # seconds
EJECTA_ASTEROIDS = 16
EJECTA_ORBIT = (300., 900.)   # from the sun surface
EJECTA_SPREAD = 120.          # degrees, along their orbits
EJECTA_RADIUS = (9., 15.)     # of its asteroids, bigger than in swarms
