""" What is drawn over the game world on each frame: orbits, waves of solar
flares, outposts, markers, the work of the ship and explosions """

import math

from ...logic.config import (
    FLARE_COLOR,
    HEAT_RANGE,
    HOME_COLOR,
    ORBIT_DOT_SPACING,
    ORBIT_PLANET_GAP,
    OUTPOST_COLOR,
    PLANET_COLOR,
    SCAN_ARROWS,
    SUN_COLOR,
    SWARM_COLOR,
)
from ...logic.hud import chevron_look, orbit_dots
from ...logic.mining.minerals import MINERALS
from ...logic.preferences import Preferences
from ...logic.ship.lasers import laser
from ...logic.ship.scanner import found, mineral_name
from ...logic.world.space import Vec2
from ..base.outposts import Outpost
from ..ship.looks import ShipLooks
from ..ship.player import Player
from ..world.solar_system import SolarSystem
from ..world.spots import Spot
from .outpost_look import draw_outpost
from .overlay import Overlay

OUTPOST_SIZE = 60.            # around the pad, for its marker


def draw_scene(overlay: Overlay, size: Vec2, system: SolarSystem,
               outposts: list[Outpost], player: Player, ship: ShipLooks,
               playing: bool, preferences: Preferences) -> None:
    """ Markers and the work of the ship are for playing, not for the
    scenery behind the home page """
    overlay.begin(size)
    if preferences.orbits:
        draw_orbits(overlay, size, system)
    draw_wave(overlay, system)
    for outpost in outposts:
        draw_outpost(overlay, outpost)
    ship.exhaust.draw(overlay)
    ship.gear.draw(overlay, player)
    if playing:
        if preferences.markers:
            draw_markers(overlay, system, outposts)
        draw_scan(overlay, system, player)
        draw_work(overlay, player)
    for explosion in player.explosions:
        overlay.explosion(explosion)


def draw_wave(overlay: Overlay, system: SolarSystem) -> None:
    """ Leaving the sun while it flares, fading out as far as it heats """
    wave = system.events.flares.wave
    if wave is not None:
        sun = system.sun
        overlay.wave(sun.pos, sun.radius + wave * HEAT_RANGE, FLARE_COLOR,
                     1 - wave)


def draw_orbits(overlay: Overlay, size: Vec2, system: SolarSystem) -> None:
    """ Of the planets, in the view """
    camera = overlay.camera
    scale = camera.camera_scale
    view_center = camera.get_camera_center()
    half_size = (size[0] * scale / 2, size[1] * scale / 2)
    for planet in system.planets:
        if planet.orbit is None:
            continue
        overlay.dots(orbit_dots(
            system.sun.pos, planet.orbit.radius, view_center, half_size,
            ORBIT_DOT_SPACING,
            hidden=(planet.pos, planet.radius + ORBIT_PLANET_GAP),
        ))


def draw_markers(overlay: Overlay, system: SolarSystem,
                 outposts: list[Outpost]) -> None:
    """ Towards the planets, the sun, a swarm passing by, the ejecta of a
    flare and the outposts, out of the screen """
    overlay.marker(system.sun, SUN_COLOR)
    swarm = system.events.swarm_spot
    if swarm is not None:
        overlay.marker(swarm, SWARM_COLOR)
    ejecta = system.events.flares.ejecta_spot
    if ejecta is not None:
        overlay.marker(ejecta, FLARE_COLOR)
    for outpost in outposts:
        overlay.marker(Spot(outpost.pos, OUTPOST_SIZE), OUTPOST_COLOR)
    for planet in system.planets:
        overlay.marker(
            planet, HOME_COLOR if planet is system.earth else PLANET_COLOR
        )


def draw_scan(overlay: Overlay, system: SolarSystem, player: Player) -> None:
    """ Towards what the scanner finds, out of the screen. Nothing without
    a scanner. """
    reach = player.stats.scan
    if player.ship is None or reach <= 0:
        return
    pos = player.ship.position
    for asteroid in found(
        system.asteroids, pos, reach, player.looked_for, SCAN_ARROWS
    ):
        overlay.chevron(
            asteroid, MINERALS[mineral_name(asteroid)].color,
            *chevron_look(math.dist(pos, asteroid.pos), reach),
        )


def draw_work(overlay: Overlay, player: Player) -> None:
    """ The asteroid mined with the laser, or the canister picked up """
    miner = player.miner
    if player.ship is None:
        return
    if miner.lock is not None:
        asteroid = miner.lock.target
        beam = laser(miner.laser)
        overlay.lock(asteroid, miner.deposits.progress(asteroid), beam.color)
        if miner.firing:
            overlay.laser(
                player.ship.nose, asteroid.pos, beam, strong=miner.extracting
            )
    if miner.pickup is not None:
        overlay.lock(miner.pickup.target, 0., laser(miner.laser).color)
