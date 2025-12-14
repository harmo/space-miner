""" What is drawn over the game world on each frame: orbits, markers, the
work of the ship and explosions """

import math

from ...logic.config import (
    HOME_COLOR,
    ORBIT_DOT_SPACING,
    ORBIT_PLANET_GAP,
    PLANET_COLOR,
    SCAN_ARROWS,
    SUN_COLOR,
    SWARM_COLOR,
)
from ...logic.hud import chevron_look, orbit_dots
from ...logic.mining.minerals import MINERALS
from ...logic.preferences import Preferences
from ...logic.ship.lasers import laser
from ...logic.ship.scanner import found, mineral_of
from ...logic.world.space import Vec2
from ..ship.looks import ShipLooks
from ..ship.player import Player
from ..world.solar_system import SolarSystem
from .overlay import Overlay


def draw_scene(overlay: Overlay, size: Vec2, system: SolarSystem,
               player: Player, ship: ShipLooks, playing: bool,
               preferences: Preferences) -> None:
    """ Markers and the work of the ship are for playing, not for the
    scenery behind the home page """
    overlay.begin(size)
    if preferences.orbits:
        draw_orbits(overlay, size, system)
    ship.exhaust.draw(overlay)
    ship.gear.draw(overlay, player)
    if playing:
        if preferences.markers:
            draw_markers(overlay, system)
        draw_scan(overlay, system, player)
        draw_work(overlay, player)
    for explosion in player.explosions:
        overlay.explosion(explosion)


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


def draw_markers(overlay: Overlay, system: SolarSystem) -> None:
    """ Towards the planets, the sun and a swarm passing by, out of the
    screen """
    overlay.marker(system.sun, SUN_COLOR)
    swarm = system.events.swarm_spot
    if swarm is not None:
        overlay.marker(swarm, SWARM_COLOR)
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
            asteroid, MINERALS[mineral_of(asteroid)].color,
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
