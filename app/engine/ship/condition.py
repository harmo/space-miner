""" The condition of the ship in flight: the fuel of its tank, burnt by
thrusting and firing the laser, and the heat of its hull, by the sun. Out
of fuel the ship can neither thrust nor mine, too hot it blows up. """

import math

from ...logic.ship.fuel import Tank, burn_rate
from ...logic.ship.heat import Hull, Sunlight, heating
from ...logic.ship.ship import Ship
from ...logic.ship.shipyard import ShipStats
from .crash import Crash


class Condition:

    def __init__(self, stats: ShipStats) -> None:
        self.tank = Tank(stats.tank)
        self.hull = Hull()

    def refit(self, stats: ShipStats) -> None:
        """ As much fuel as fits in the tank of the new ship """
        self.tank.resize(stats.tank)

    def burn(self, dt: float, stats: ShipStats, thrust: float,
             firing: bool) -> None:
        """ `thrust` from 0 to 1 """
        self.tank.burn(burn_rate(stats, thrust, firing) * dt)

    def heat_up(self, dt: float, stats: ShipStats, ship: Ship,
                sunlight: Sunlight) -> Crash | None:
        """ The crash of the ship once too hot """
        self.hull.update(dt, heating(
            sunlight.distance(ship.position), shield=stats.shield,
            surge=sunlight.surge,
        ))
        if not self.hull.burnt:
            return None
        (x, y), (sun_x, sun_y) = ship.position, sunlight.pos
        return Crash(ship.velocity, math.atan2(y - sun_y, x - sun_x))
