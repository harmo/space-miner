""" The ship of the player through its lives: flying, crashing and coming
back on the Earth. Its work, mining, is up to its miner, its fuel and
heat to its condition. """

import math
from random import Random
from typing import Any

from ...logic.base.post import Docked
from ...logic.config import EXPLOSION_FRAGMENTS, EXPLOSION_SPEED, SHIP_COLOR
from ...logic.mining.canisters import eject_cargo
from ...logic.ship.config import (
    RESPAWN_DELAY,
    START_DIRECTION,
    TRAIL_HOLDING,
    TRAIL_LANDING,
)
from ...logic.ship.fuel import Tank
from ...logic.ship.heat import HullHeat
from ...logic.ship.landing import (
    Ground,
    Landing,
    Parking,
    Shortcut,
    closest_spot,
    is_landed,
    landed_on,
    nearest,
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
from ...logic.world.space import Celestial, Vec2
from ..entities import GameWorld, create_ship_entity, get_body, move_body
from ..world.canister_field import CanisterField
from ..world.solar_system import SolarSystem
from .condition import Condition
from .crash import Crash, crash_of
from .miner import Miner
from .ship_textures import ship_texture


class Player:

    def __init__(self, gameworld: GameWorld, system: SolarSystem,
                 camera: Any, rng: Random, grounds: list[Ground]) -> None:
        self.gameworld = gameworld
        self.system = system
        # Where the ship can land, the first one its home where it comes
        # back after a crash
        self.grounds = grounds
        self.camera = camera
        self.rng = rng
        self.ship: Ship | None = None       # None while exploded
        # Ships spawned: entities are reused, not this number
        self.spawned = 0
        self.anchor: Vec2 = (0., 0.)        # where the ship is, or was
        self.crash: Crash | None = None
        self.respawn_in = 0.
        self.landing: Landing | None = None
        self.parking: Parking | None = None  # landed
        self.explosions: list[Explosion] = []
        self.canisters = CanisterField(gameworld)  # cargo lost in crashes
        self.design = Design()
        self.stats = ship_stats(self.design)
        self.condition = Condition(self.stats)
        self.looked_for = set(LOOKED_FOR)   # by its scanner
        self.fits: dict[int, list[float]] = {}  # spots, by body
        self.fit()
        self.miner = Miner(
            system, self.canisters, rng, self.explosions, self.stats
        )
        self.spawn(math.radians(START_DIRECTION))

    @property
    def home(self) -> Ground:
        return self.grounds[0]

    def fit(self) -> None:
        """ Where the ship fits on each ground, for its width """
        width = self.stats.size[1]
        self.fits = {
            ground.body.entity_id: ground.spots(width)
            for ground in self.grounds
        }

    def spots(self, ground: Ground) -> list[float]:
        return self.fits[ground.body.entity_id]

    def spawn(self, direction: float, ground: Ground | None = None) -> None:
        """ Landed home, or on `ground`, as close to `direction` as it can """
        ground = ground or self.home
        body = ground.body
        direction = closest_spot(direction, self.spots(ground))
        length = self.stats.size[0]
        pos = landed_on(body, direction, length)
        entity_id = create_ship_entity(
            self.gameworld, pos, body.velocity, direction,
            ship_texture(self.design, self.stats.size), self.stats.size,
        )
        ship_body = get_body(self.gameworld, entity_id)
        self.ship = Ship(entity_id, ship_body, self.stats)
        self.spawned += 1
        self.condition.heat.reset()
        self.parking = parking_on(body, direction, length)
        self.anchor = pos
        self.camera.look_at(pos)
        self.camera.entity_to_focus = entity_id

    @property
    def shortcut(self) -> Shortcut:
        """ State of the landing shortcut """
        if self.ship is None or self.landing is not None:
            return 'hidden'
        ground = nearest(self.grounds, self.ship.position)
        body = ground.body
        x, y = position = self.ship.position
        direction = math.atan2(y - body.pos[1], x - body.pos[0])
        return shortcut(
            surface_distance(position, body),
            is_landed(
                position, self.ship.velocity, self.ship.body.angle, body,
                self.stats.size,
            ),
            over_ground(direction, self.spots(ground)),
        )

    @property
    def stranded(self) -> bool:
        """ Out of fuel away from home, waiting to be towed back: flying,
        or landed where it can't be refuelled. Outposts refuelling ships
        fill their tank as soon as they land. """
        if self.ship is None or not self.tank.empty or self.landing:
            return False
        return self.parking is None or self.parking.body is not self.home.body

    @property
    def docked(self) -> bool:
        """ Parked, where a base can serve the ship """
        return (
            self.ship is not None and self.parking is not None
            and self.landing is None and not self.miner.busy
        )

    @property
    def served(self) -> Docked:
        """ As the post it is landed at sees it """
        return Docked(self.miner.ore, self.tank, self.heat)

    def docked_on(self, body: Celestial) -> bool:
        return self.docked and self.parking is not None and (
            self.parking.body is body
        )

    @property
    def ground_body(self) -> Celestial:
        """ Of what the ship is parked, landing or about to land on """
        if self.parking is not None:
            return self.parking.body
        if self.landing is not None:
            return self.landing.body
        return nearest(self.grounds, self.anchor).body

    def refit(self, design: Design) -> None:
        """ Swap the ship for one built after `design`, where it is
        parked """
        parking = self.parking
        if parking is not None and self.docked:
            self.restart(design, parking.direction,
                         self.ground_of(parking.body))

    def ground_of(self, body: Celestial) -> Ground | None:
        return next(
            (ground for ground in self.grounds if ground.body is body), None,
        )

    def restart(self, design: Design,
                direction: float = math.radians(START_DIRECTION),
                ground: Ground | None = None) -> None:
        """ A ship built after `design`, landed home, or on `ground`,
        whatever the ship was doing """
        if self.ship is not None:
            self.gameworld.remove_entity(self.ship.entity_id)
        self.landing, self.crash = None, None
        self.miner.release()
        self.design, self.stats = design, ship_stats(design)
        self.miner.stats = self.stats
        self.condition.refit(self.stats)
        self.fit()
        self.spawn(direction, ground)

    def land(self) -> None:
        """ Land automatically on the closest ground, when close enough """
        if self.ship is None or self.shortcut != 'ready':
            return
        self.miner.release()
        self.parking = None
        ground = nearest(self.grounds, self.ship.position)
        body = ground.body
        x, y = self.ship.position
        approach = math.atan2(y - body.pos[1], x - body.pos[0])
        self.landing = Landing(
            body, (x, y), self.ship.body.angle,
            closest_spot(approach, self.spots(ground)), self.stats.size[0],
        )

    @property
    def tank(self) -> Tank:
        return self.condition.tank

    @property
    def heat(self) -> HullHeat:
        return self.condition.heat

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
            self.condition.burn(
                dt, self.stats, self.thrust(heading), self.miner.firing,
            )
            if self.tank.empty:
                heading = None
                self.miner.release()
            self.move_ship(self.ship, dt, heading)
            self.anchor = self.ship.position
            self.crash = self.condition.heat_up(
                dt, self.stats, self.ship, self.system.sunlight,
            ) or self.crash

        self.canisters.update(
            dt, self.system.asteroids, self.system.attractors
        )
        for explosion in self.explosions:
            explosion.update(dt)
        self.explosions[:] = [e for e in self.explosions if not e.done]

    def move_ship(self, ship: Ship, dt: float, heading: float | None) -> None:
        """ Landing, working, parked, or flying. Thrusting or working takes
        off. """
        if self.landing is not None:
            self.follow(ship, self.landing, dt)
        elif self.miner.busy:
            self.parking = None
            self.miner.work(ship, dt, self.system.attractors)
        elif self.parking is not None and heading is None:
            parking = self.parking
            ship.place(
                parking.position, parking.body.velocity, parking.angle,
            )
        else:
            self.parking = None
            ship.update(dt, heading, self.system.attractors)
            body = nearest(self.grounds, ship.position).body
            if heading is None and is_landed(
                ship.position, ship.velocity, ship.body.angle, body,
                self.stats.size,
            ):
                self.parking = parking_at(
                    body, ship.position, ship.body.angle
                )

    def follow(self, ship: Ship, landing: Landing, dt: float) -> None:
        landing.advance(dt)
        ship.place(landing.position, landing.velocity, landing.angle)
        if landing.done:
            self.landing = None
            self.parking = parking_on(
                landing.body, landing.end_direction, self.stats.size[0]
            )

    def on_contact(self, space: Any, arbiter: Any) -> bool:
        """ Called by the physics engine, which must not have bodies
        removed while it runs: the explosion happens on the next frame """
        if self.ship is not None:
            crash = crash_of(
                self.gameworld, self.ship, arbiter,
                {ground.body.entity_id for ground in self.grounds},
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
