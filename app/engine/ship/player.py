""" The ship of the player through its lives: flying, crashing and coming
back on the Earth. Its work, mining, is up to its miner. Both burn the
fuel of its tank: out of it, the ship can neither thrust nor mine. """

import math
from random import Random
from typing import Any

from ...logic.config import EXPLOSION_FRAGMENTS, EXPLOSION_SPEED, SHIP_COLOR
from ...logic.mining.canisters import eject_cargo
from ...logic.ship.config import (
    RESPAWN_DELAY,
    START_DIRECTION,
    TRAIL_HOLDING,
    TRAIL_LANDING,
)
from ...logic.ship.fuel import Tank, burn_rate
from ...logic.ship.landing import (
    Landing,
    Parking,
    Shortcut,
    closest_spot,
    ground_margin,
    ground_spots,
    is_landed,
    landed_on,
    over_ground,
    parking_at,
    parking_on,
    shortcut,
    surface_distance,
)
from ...logic.ship.scanner import LOOKED_FOR
from ...logic.ship.ship import Ship
from ...logic.ship.shipyard import Design, ship_stats
from ...logic.world.explosion import Explosion
from ...logic.world.space import Vec2
from ..entities import GameWorld, create_ship_entity, get_body, move_body
from ..world.canister_field import CanisterField
from ..world.solar_system import SolarSystem
from .crash import Crash, crash_of
from .miner import Miner
from .ship_textures import ship_texture


class Player:

    def __init__(self, gameworld: GameWorld, system: SolarSystem,
                 camera: Any, rng: Random, edge: list[bool]) -> None:
        self.gameworld = gameworld
        self.system = system
        self.edge = edge                    # ground of the Earth, by degree
        self.camera = camera
        self.rng = rng
        self.ship: Ship | None = None       # None while exploded
        self.anchor: Vec2 = (0., 0.)        # where the ship is, or was
        self.crash: Crash | None = None
        self.respawn_in = 0.
        self.landing: Landing | None = None
        self.parking: Parking | None = None  # landed on the Earth
        self.explosions: list[Explosion] = []
        self.canisters = CanisterField(gameworld)  # cargo lost in crashes
        self.design = Design()
        self.stats = ship_stats(self.design)
        self.tank = Tank(self.stats.tank)
        self.looked_for = set(LOOKED_FOR)   # by its scanner
        self.ground = self.ground_spots()   # where the ship fits
        self.miner = Miner(
            system, self.canisters, rng, self.explosions, self.stats
        )
        self.spawn(math.radians(START_DIRECTION))

    def ground_spots(self) -> list[float]:
        width = self.stats.size[1]
        return ground_spots(
            self.edge, ground_margin(self.system.earth, width)
        )

    def spawn(self, direction: float) -> None:
        """ Landed on the Earth, on the ground closest to `direction` """
        earth = self.system.earth
        direction = closest_spot(direction, self.ground)
        length = self.stats.size[0]
        pos = landed_on(earth, direction, length)
        entity_id = create_ship_entity(
            self.gameworld, pos, earth.velocity, direction,
            ship_texture(self.design, self.stats.size), self.stats.size,
        )
        body = get_body(self.gameworld, entity_id)
        self.ship = Ship(entity_id, body, self.stats)
        self.parking = parking_on(earth, direction, length)
        self.anchor = pos
        self.camera.look_at(pos)
        self.camera.entity_to_focus = entity_id

    @property
    def shortcut(self) -> Shortcut:
        """ State of the landing shortcut """
        if self.ship is None or self.landing is not None:
            return 'hidden'
        earth = self.system.earth
        x, y = position = self.ship.position
        direction = math.atan2(y - earth.pos[1], x - earth.pos[0])
        return shortcut(
            surface_distance(position, earth),
            is_landed(
                position, self.ship.velocity, self.ship.body.angle, earth,
                self.stats.size,
            ),
            over_ground(direction, self.ground),
        )

    @property
    def stranded(self) -> bool:
        """ Out of fuel away from the Earth, waiting to be towed back """
        return (
            self.ship is not None and self.tank.empty
            and self.parking is None and self.landing is None
        )

    @property
    def docked(self) -> bool:
        """ Parked on the Earth, where the ship can be refitted """
        return (
            self.ship is not None and self.parking is not None
            and self.landing is None and not self.miner.busy
        )

    def refit(self, design: Design) -> None:
        """ Swap the ship for one built after `design`, where it is parked
        on the Earth """
        if self.parking is not None and self.docked:
            self.restart(design, self.parking.direction)

    def restart(self, design: Design,
                direction: float = math.radians(START_DIRECTION)) -> None:
        """ A ship built after `design`, landed on the Earth whatever the
        ship was doing """
        if self.ship is not None:
            self.gameworld.remove_entity(self.ship.entity_id)
        self.landing, self.crash = None, None
        self.miner.release()
        self.design, self.stats = design, ship_stats(design)
        self.miner.stats = self.stats
        self.tank.resize(self.stats.tank)
        self.ground = self.ground_spots()
        self.spawn(direction)

    def land(self) -> None:
        """ Land automatically on the Earth, when close enough """
        if self.ship is None or self.shortcut != 'ready':
            return
        self.miner.release()
        self.parking = None
        earth = self.system.earth
        x, y = self.ship.position
        approach = math.atan2(y - earth.pos[1], x - earth.pos[0])
        self.landing = Landing(
            earth, (x, y), self.ship.body.angle,
            closest_spot(approach, self.ground), self.stats.size[0],
        )

    def thrust(self, heading: float | None) -> float:
        """ From 0 to 1: full while flying towards `heading`, weaker while
        holding in front of what the ship works on, or landing. Nothing
        out of fuel, but landing goes on to the end. """
        if self.ship is None or self.parking is not None:
            return 0.
        if self.landing is not None:
            return TRAIL_LANDING
        if self.tank.empty:
            return 0.
        if self.miner.busy:
            return TRAIL_HOLDING
        return 1. if heading is not None else 0.

    def update(self, dt: float, heading: float | None) -> None:
        if self.crash is not None:
            self.explode(self.crash)
        if self.ship is None:
            self.respawn_in -= dt
            if self.respawn_in <= 0:
                self.spawn(math.radians(START_DIRECTION))
        if self.ship is not None:
            self.tank.burn(burn_rate(
                self.stats, self.thrust(heading), self.miner.firing,
            ) * dt)
            if self.tank.empty:
                heading = None
                self.miner.release()
            self.move_ship(self.ship, dt, heading)
            self.anchor = self.ship.position

        self.canisters.update(
            dt, self.system.asteroids, self.system.attractors
        )
        for explosion in self.explosions:
            explosion.update(dt)
        self.explosions[:] = [e for e in self.explosions if not e.done]

    def move_ship(self, ship: Ship, dt: float, heading: float | None) -> None:
        """ Landing, working, parked on the Earth, or flying. Thrusting or
        working takes off. """
        earth = self.system.earth
        if self.landing is not None:
            self.follow(ship, self.landing, dt)
        elif self.miner.busy:
            self.parking = None
            self.miner.work(ship, dt, self.system.attractors)
        elif self.parking is not None and heading is None:
            ship.place(
                self.parking.position(earth), earth.velocity,
                self.parking.angle,
            )
        else:
            self.parking = None
            ship.update(dt, heading, self.system.attractors)
            if heading is None and is_landed(
                ship.position, ship.velocity, ship.body.angle, earth,
                self.stats.size,
            ):
                self.parking = parking_at(
                    earth, ship.position, ship.body.angle
                )

    def follow(self, ship: Ship, landing: Landing, dt: float) -> None:
        landing.advance(dt)
        ship.place(landing.position, landing.velocity, landing.angle)
        if landing.done:
            self.landing = None
            self.parking = parking_on(
                self.system.earth, landing.end_direction, self.stats.size[0]
            )

    def on_contact(self, space: Any, arbiter: Any) -> bool:
        """ Called by the physics engine, which must not have bodies
        removed while it runs: the explosion happens on the next frame """
        if self.ship is not None:
            crash = crash_of(
                self.gameworld, self.ship, arbiter,
                self.system.earth.entity_id,
            )
            self.crash = crash or self.crash
        return True

    def explode(self, crash: Crash) -> None:
        """ The fragments fly along with what the ship crashed in, and the
        cargo is lost in canisters thrown away from it """
        self.crash = None
        if self.ship is None:
            return
        self.explosions.append(Explosion(
            self.rng, self.ship.position, crash.velocity, SHIP_COLOR,
            EXPLOSION_FRAGMENTS, EXPLOSION_SPEED,
        ))
        self.canisters.add(eject_cargo(
            self.rng, self.miner.lose_cargo(), self.ship.position,
            crash.velocity, crash.away,
        ))
        self.camera.entity_to_focus = None
        self.gameworld.remove_entity(self.ship.entity_id)
        self.ship = None
        self.landing = None
        self.parking = None
        self.respawn_in = RESPAWN_DELAY

    def shift(self, shift: Vec2) -> None:
        """ Move along with the rest of the world """
        self.canisters.shift(shift)
        if self.ship is not None:
            move_body(self.gameworld, self.ship.entity_id, shift)
        self.anchor = (self.anchor[0] + shift[0], self.anchor[1] + shift[1])
        for explosion in self.explosions:
            explosion.shift(shift)
