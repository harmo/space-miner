""" The work of the ship: mining asteroids and picking canisters up, into
its cargo """

import math
from collections.abc import Callable, Sequence
from random import Random

from ...logic.config import DEBRIS_FRAGMENTS, DEBRIS_SPEED
from ...logic.mining.minerals import MINERALS, mining_rate
from ...logic.mining.ore import EPSILON, Deposits, Hold, cargo_room, mineral_of
from ...logic.ship.config import (
    LASER_RANGE,
    LASER_RATE,
    MINING_DISTANCE,
    PICKUP_FRAGMENTS,
    PICKUP_HOLD,
    PICKUP_RANGE,
    PICKUP_SPEED,
)
from ...logic.ship.ship import Ship
from ...logic.ship.shipyard import ShipStats
from ...logic.world.explosion import Explosion
from ...logic.world.space import Celestial, Station, Vec2
from ..world.canister_field import Canister, CanisterField
from ..world.solar_system import SolarSystem


class Miner:

    def __init__(self, system: SolarSystem, canisters: CanisterField,
                 rng: Random, explosions: list[Explosion],
                 stats: ShipStats) -> None:
        self.system = system
        self.canisters = canisters
        self.rng = rng
        self.explosions = explosions        # shared with the player
        self.lock: Station[Celestial] | None = None     # asteroid mined
        self.pickup: Station[Canister] | None = None    # canister wanted
        self.firing = False
        self.too_weak = False               # laser firing in vain
        self.cargo_full = False             # mining or pickup stopped
        self.stats = stats                  # of the ship, refitted or not
        self.deposits = Deposits()
        self.ore: Hold = {}     # in the cargo, by mineral
        # Told the mineral of each asteroid mined out, and of each canister
        # picked up
        self.on_mined_out: list[Callable[[str], None]] = []
        self.on_pick_up: list[Callable[[], None]] = []
        system.on_remove.append(self.gone)

    def gone(self, asteroid: Celestial) -> None:
        """ Mined out, or left with its swarm """
        self.deposits.forget(asteroid)
        if self.lock is not None and self.lock.target is asteroid:
            self.release()

    @property
    def laser(self) -> int:
        return self.stats.laser

    @property
    def capacity(self) -> float:
        return self.stats.capacity

    @property
    def busy(self) -> bool:
        return self.lock is not None or self.pickup is not None

    def lock_on(self, asteroid: Celestial, ship: Vec2) -> None:
        """ Hold on the side where the ship is, at mining distance """
        self.release()
        self.lock = Station(asteroid, ship, MINING_DISTANCE)

    def work_at(self, pos: Vec2, tolerance: float, ship: Vec2) -> bool:
        """ Pick up the canister at `pos`, or else mine the asteroid there.
        Releases what the ship worked on when there is neither. """
        canister = self.canisters.at(pos, tolerance)
        asteroid = self.system.asteroid_at(pos, tolerance)
        if canister is not None:
            self.pick_up(canister, ship)
        elif asteroid is not None:
            self.lock_on(asteroid, ship)
        else:
            self.release()
            return False
        return True

    def pick_up(self, canister: Canister, ship: Vec2) -> None:
        self.release()
        self.pickup = Station(canister, ship, PICKUP_HOLD)

    def release(self) -> None:
        self.lock = None
        self.pickup = None
        self.firing = False
        self.too_weak = False
        self.cargo_full = False

    def lose_cargo(self) -> Hold:
        """ Empties the cargo, returns what it held """
        ore = dict(self.ore)
        self.ore.clear()                    # the panels hold on to it
        self.release()
        return ore

    @property
    def extracting(self) -> bool:
        """ Whether the laser is mining for real """
        return self.firing and not self.too_weak and not self.cargo_full

    @property
    def mining(self) -> str | None:
        """ Mineral being extracted right now """
        if self.lock is None or not self.extracting:
            return None
        return self.lock.target.mineral or 'rock'

    @property
    def message(self) -> str:
        if self.cargo_full:
            return 'Soute pleine'
        if self.too_weak and self.lock is not None:
            return f'Laser trop faible pour {mineral_of(self.lock.target).the}'
        return ''

    def work(self, ship: Ship, dt: float,
             attractors: Sequence[Celestial]) -> None:
        if self.pickup is not None:
            ship.hold(dt, self.pickup, attractors)
            self.collect(ship, self.pickup.target)
        elif self.lock is not None:
            ship.hold(dt, self.lock, attractors)
            self.mine(ship, self.lock.target, dt)

    def mine(self, ship: Ship, asteroid: Celestial, dt: float) -> None:
        self.firing = math.dist(ship.nose, asteroid.pos) <= LASER_RANGE
        rate = mining_rate(mineral_of(asteroid), self.laser, LASER_RATE)
        room = cargo_room(self.ore, self.capacity)
        self.too_weak = self.firing and rate == 0
        self.cargo_full = self.firing and rate > 0 and room == 0
        if self.extracting:
            name = asteroid.mineral or 'rock'
            extracted = self.deposits.mine(asteroid, dt, rate, room)
            self.ore[name] = self.ore.get(name, 0.) + extracted
            if self.deposits.left(asteroid) <= 0:
                self.mined_out(asteroid)

    def mined_out(self, asteroid: Celestial) -> None:
        self.explosions.append(Explosion(
            self.rng, asteroid.pos, asteroid.velocity,
            mineral_of(asteroid).color, DEBRIS_FRAGMENTS, DEBRIS_SPEED,
        ))
        self.system.remove(asteroid)
        for told in self.on_mined_out:
            told(asteroid.mineral or 'rock')

    def collect(self, ship: Ship, canister: Canister) -> None:
        """ Takes in what fits in the cargo, once close enough """
        if canister not in self.canisters.canisters:
            self.release()                  # vanished meanwhile
            return
        if math.dist(ship.position, canister.pos) > PICKUP_RANGE:
            return
        taken = min(canister.amount, cargo_room(self.ore, self.capacity))
        self.ore[canister.mineral] = (
            self.ore.get(canister.mineral, 0.) + taken
        )
        canister.amount -= taken
        if canister.amount > EPSILON:
            self.cargo_full = True          # the rest stays in it
            return
        self.explosions.append(Explosion(
            self.rng, canister.pos, canister.velocity,
            MINERALS[canister.mineral].color,
            PICKUP_FRAGMENTS, PICKUP_SPEED,
        ))
        self.canisters.remove(canister)
        self.release()
        for told in self.on_pick_up:
            told()
