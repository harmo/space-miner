""" Settings of the solar system: sizes are in pixels, speeds in px/s """

# Sun
SUN_RADIUS = 600.
SUN_GRAVITY = 400.            # pull at its surface (px/s²)
# Pull in 1/distance², as planets: strong close to it, light far away
SUN_GRAVITY_FALLOFF = 2.

# Planets
FIRST_ORBIT = 2200.           # distance of the closest planet to the sun
# Between an orbit and the next, wider and wider outwards like in the real
# solar system, the belt around the sun taking an orbit of its own
ORBIT_GAPS = (1600., 1700., 1900., 2800., 2800., 3300., 3800., 4400.)
GAP_SPREAD = (.9, 1.15)       # each gap times as much, game after game
EARTH_ORBIT = 2               # the Earth is the third planet
BELT_AFTER = 3                # the belt around the sun, after the fourth
PLANET_SPEED = 40.            # on the first orbit, slower farther out
PLANET_MASS = 1e6             # heavy enough not to be pushed by the ship
SHADOW_LENGTH = 1400.         # of the shadow of the closest planet to the sun
EARTH_RADIUS = 200.
# From the sun outwards, as in the real solar system, their texture and
# their radius: Mercury, Venus, the Earth, Mars, Jupiter, Saturn, Uranus
# and Neptune
LINEUP = (
    ('planet4', 150.), ('planet5', 195.), ('earth', EARTH_RADIUS),
    ('planet2', 165.), ('planet1', 350.), ('planet6', 310.),
    ('planet3', 260.), ('planet7', 250.),
)

GRAVITY = 1.25                # planet surface gravity is GRAVITY * radius
GRAVITY_FALLOFF = 2.          # planets pull in 1/distance²
GRAVITY_RANGE = 6.            # planets pull the ship up to this many radii

# Cérès, a big asteroid in the middle of the belt around the sun: the site
# of an outpost, never mined
CERES_RADIUS = 70.
CERES_GRAVITY = 40.           # at its surface, weak (px/s²)
# Its own cloud of asteroids turning around it, the fullest there is, and
# growing back as soon as one is mined. Its middle stays clear, to land.
CERES_BELT_ASTEROIDS = 60
CERES_BELT_ORBITS = (400., 1600.)  # from its center
CERES_BELT_SPEED = (30., 70.)
CERES_REGROW_TIME = 60.       # seconds for a whole belt

# Stations orbiting planets, sites of outposts
STATION_RADIUS = 40.
STATION_ALTITUDE = 300.       # above the surface of their planet
STATION_SPEED = 50.

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

# Comets, on long ellipses reaching as far as the last planet
COMET_EVERY = (720., 1200.)   # seconds between them
COMET_TIME = 480.             # seconds through the solar system
COMET_PERIHELION = 500.       # from the sun surface, at the closest
COMET_RADIUS = 45.
COMET_TAIL = 1800.            # long, at most
COMET_TAIL_RANGE = 12000.     # from the sun surface, where it starts

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
