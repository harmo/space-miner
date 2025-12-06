""" Settings shared by the whole game: the textures, space, explosions,
the interface and the physics. Sizes are in pixels, speeds in px/s. Each
part of the game has its own in its package. """

# Textures
IMAGES = 'assets/images'
PLANETS = [f'planet{i}' for i in range(1, 8)]
MOON = 'moon'
SUN_DISC = .7                 # part of the sun texture that is not glow
# Images of planets bigger than the planet itself, for their rings
PLANET_IMAGE_SCALE = {'planet6': 1.6}

# Space repeats itself every WORLD_SIZE, the solar system fits in it
WORLD_SIZE = 72000.
STAR_TILE = 12000.            # the star field repeats on a smaller tile

STAR_COUNT = 6000             # per star tile
STAR_SIZE = (2., 5.)
STAR_WRAP_BATCH = 600         # stars checked for wrapping on each frame

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
MARKER_MARGIN = 6.            # from the screen edge
MARKER_THICKNESS = 3.
MARKER_LENGTH = (12., 120.)   # from far away to close
MARKER_NEAR = 1500.           # distances of the shortest and longest markers
MARKER_FAR = 30000.
MARKER_OPACITY = .7
ORBIT_DOT_SIZE = 1.
ORBIT_OPACITY = .18
CHEVRON_SIZE = (9., 16.)      # from the edge of its reach to close
CHEVRON_OPACITY = (.35, .7)   # likewise, discreet
CHEVRON_WIDTH = 1.             # of their outline, hollow inside
CHEVRON_MARGIN = 22.          # from the screen edge, inside the bars
SHIP_COLOR = (.85, .64, .25)
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
