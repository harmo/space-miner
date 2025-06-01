""" Settings shared by the whole game: the textures, space, explosions,
the interface and the physics. Sizes are in pixels, speeds in px/s. Each
part of the game has its own in its package. """

PLANETS = [f'planet{i}' for i in range(1, 8)]
MOON = 'moon'
SUN_DISC = .7                 # part of the sun texture that is not glow

# Space repeats itself every WORLD_SIZE, the solar system fits in it
WORLD_SIZE = 72000.
STAR_TILE = 12000.            # the star field repeats on a smaller tile


EXPLOSION_DURATION = 1.2      # seconds

MARKER_LENGTH = (12., 120.)   # from far away to close
MARKER_NEAR = 1500.           # distances of the shortest and longest markers
MARKER_FAR = 30000.
CHEVRON_SIZE = (9., 16.)      # from the edge of its reach to close
CHEVRON_OPACITY = (.35, .7)   # likewise, discreet
