""" Settings shared by the whole game: the textures and sounds, space,
explosions, the interface and the physics. Sizes are in pixels, speeds in
px/s. Each part of the game has its own in its package. """

# Textures and sounds
IMAGES = 'assets/images'
SOUNDS = 'assets/sounds'
PLANETS = [f'planet{i}' for i in range(1, 8)]
MOON = 'moon'
CERES = 'ceres'               # painted as the planets, in the sun belt
COMET = 'comet'               # likewise
STATION = 'station'           # unseen, stations are drawn over the game
SUN_DISC = .7                 # part of the sun texture that is not glow
# Images of planets bigger than the planet itself, for their rings
PLANET_IMAGE_SCALE = {'planet6': 1.6}
# On the map, by texture
PLANET_COLORS = {
    'earth': (.23, .49, .76), 'planet1': (.85, .7, .5),
    'planet2': (.75, .4, .25), 'planet3': (.5, .8, .82),
    'planet4': (.58, .53, .49), 'planet5': (.88, .68, .64),
    'planet6': (.9, .82, .6), 'planet7': (.3, .42, .78),
}
RINGED = {'planet6'}

# Space repeats itself every WORLD_SIZE, the solar system fits in it
WORLD_SIZE = 72000.
STAR_TILE = 12000.            # the star field repeats on a smaller tile

STAR_COUNT = 6000             # per star tile
STAR_SIZE = (2., 5.)
STAR_WRAP_BATCH = 600         # stars checked for wrapping on each frame
# The far sky behind them: images in IMAGES/sky, how fast each one slides
# compared with the stars, and the size of its pixels in dp
SKY_LAYERS = (('nebula', .03, 2.), ('far_stars', .1, 1.))

# Explosions
EXPLOSION_FRAGMENTS = 32
EXPLOSION_SPEED = (60., 260.)
DEBRIS_FRAGMENTS = 10         # when an asteroid is mined out
DEBRIS_SPEED = (20., 80.)
EXPLOSION_DURATION = 1.2      # seconds

# Interface, drawn in screen pixels
CARGO_COLOR = (.36, .71, .9)  # bar of the load, from empty to full
CARGO_ALMOST_FULL = .9
CARGO_ALMOST_FULL_COLOR = (1., .62, .3)
CARGO_FULL_COLOR = (1., .35, .3)
FUEL_COLOR = (.45, .85, .55)  # gauge of the tank, warning as the cargo bar
HEAT_GAUGE_COLOR = (1., .8, .45)  # of the hull, likewise
MONEY_COLOR = (1., .82, .4)   # credits, wherever they show
COMET_COLOR = (.7, .92, 1.)   # comets, their tail, their path
MET_COLOR = (.45, .9, .5)     # ore wanted, once there is enough
MARKER_MARGIN = 6.            # from the screen edge
MARKER_THICKNESS = 3.
MARKER_LENGTH = (12., 120.)   # from far away to close
MARKER_NEAR = 1500.           # distances of the shortest and longest markers
MARKER_FAR = 30000.
MARKER_OPACITY = .7
ORBIT_DOT_SPACING = 14.       # orbits of the planets, dotted
ORBIT_DOT_SIZE = 1.
ORBIT_OPACITY = .18
ORBIT_PLANET_GAP = 30.        # no dots this close to the planet surface
HOME_COLOR = (.23, .49, .76)  # the Earth
PLANET_COLOR = (.85, .85, .9)  # the other planets
SHUTTLE_COLOR = (1., .76, .28)  # shuttles, on the map and in their hull
SWARM_COLOR = (1., .4, .85)   # rich asteroids passing by
FLARE_COLOR = (1., .55, .2)   # waves of solar flares, and their ejecta
OUTPOST_COLOR = (.5, .9, .78)  # sites of outposts, and outposts
SUN_COLOR = (1., .82, .25)
# Towards what the scanner finds, out of the screen
SCAN_ARROWS = 10              # at most, the closest
CHEVRON_SIZE = (9., 16.)      # from the edge of its reach to close
CHEVRON_OPACITY = (.35, .7)   # likewise, discreet
CHEVRON_WIDTH = 1.             # of their outline, hollow inside
CHEVRON_MARGIN = 22.          # from the screen edge, inside the bars
SHIP_COLOR = (.85, .64, .25)
# The sky reddens closer and closer to the sun
HEAT_RANGE = 5000.            # from the sun surface, where it starts
HEAT_COLOR = (.55, .08, .02)  # at the surface
# Compact interface on phones: on mobile platforms, or on any screen whose
# shorter side is below this many dp
MOBILE_PLATFORMS = ('android', 'ios')
COMPACT_SCREEN = 520.

# Physics
COLLISION_SHIP = 1
COLLISION_PLANET = 2          # the sun and the planets
COLLISION_ORBITER = 3         # the moon and the asteroids
COLLISION_CANISTER = 4        # only touches the ship

PHYSICS_COMPONENT_ORDER = [
    'position',
    'rotate',
    'rotate_renderer',
    'cymunk_physics',
]

# KivEnt systems declared in the kv file, in update order: physics moves the
# bodies, then the camera follows the ship, then everything is drawn
SYSTEMS = [
    'cymunk_physics',
    'position',
    'rotate',
    'camera1',
    'stars_renderer',
    'rotate_renderer',
]
MAX_FRAME_TIME = 1 / 20       # avoids physics jumps after a freeze

AUTOSAVE_PERIOD = 5.          # seconds between checks for changes to save
