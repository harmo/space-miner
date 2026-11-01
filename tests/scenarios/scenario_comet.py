""" A comet passes through the solar system: told, on the map with its path,
slow far away and racing by the sun, its tail growing. It sheds ice, which
the ship mines, then richer asteroids, all gone with it. """

import math
from typing import Any

from app.engine.entities import get_body
from app.logic.world.comets import tail_length
from app.logic.world.config import COMET_ICE
from app.logic.world.swarms import RICH

from .harness import Scenario

scenario = Scenario('comet')
check = scenario.check
remembered: dict[str, Any] = {}
played = scenario.record_sounds()


def events() -> Any:
    return scenario.game.system.events


def jump(anomaly: float) -> None:
    """ Along its way, its body along with it """
    orbit = events().comet_orbit
    orbit.anomaly = anomaly
    orbit.along = orbit.solved()
    get_body(scenario.game.gameworld, events().comet.entity_id).position = (
        orbit.position
    )


@scenario.step(1.)
def waits_for_a_comet() -> None:
    check(events().comet is None, 'none at first')
    events().comet_clock.waiting = 0.


@scenario.step(.3)
def a_comet_comes() -> None:
    check(events().comet is not None, 'a comet comes')
    system = scenario.game.system
    distance = math.dist(events().comet.pos, system.sun.pos)
    check(abs(distance - system.orbits[-1]) < 50,
          f'from as far as the last planet: {distance:.0f}')
    check('swarm' in played, f'heard: {played}')
    news = scenario.game.ids.news_label.text
    check('Comète' in news and 'près du soleil' in news, f'told: {news}')
    scenario.press(scenario.game.ids.map_button)


@scenario.step(.3)
def is_on_the_map() -> None:
    scenario.screenshot('map')
    scenario.game.map_open = False


@scenario.step(.3)
def sheds_ice_far_from_the_sun() -> None:
    debris = events().debris
    check(len(debris) == COMET_ICE, f'around it: {len(debris)}')
    check(all(a.mineral == 'ice' for a in debris), 'of ice')
    check(all(a.orbit.parent is events().comet for a in debris),
          'turning around it')
    comet, asteroid = events().comet, debris[0]
    away = math.atan2(
        asteroid.pos[1] - comet.pos[1], asteroid.pos[0] - comet.pos[0],
    )
    scenario.put_ship(
        (asteroid.pos[0] + math.cos(away) * 200,
         asteroid.pos[1] + math.sin(away) * 200),
        asteroid.velocity, angle=away + math.pi,
    )
    player = scenario.player
    player.miner.work_at(asteroid.pos, 40., player.ship.position)


@scenario.step(2.)
def mines_it() -> None:
    ore = scenario.player.miner.ore
    check(ore.get('ice', 0.) > 0, f'ice in the cargo: {ore}')
    scenario.player.miner.release()


@scenario.step(.1)
def races_by_the_sun() -> None:
    jump(-.08)
    orbit = events().comet_orbit
    remembered['far'] = 50.
    scenario.put_ship((orbit.position[0] + 8000, orbit.position[1]), (0, 0))


@scenario.step(.2)
def goes_by_with_its_tail() -> None:
    orbit, sun = events().comet_orbit, scenario.game.system.sun
    distance = math.dist(orbit.position, sun.pos) - sun.radius
    check(tail_length(distance) > 0, f'with its tail: {distance:.0f}')
    speed = math.hypot(*orbit.velocity)
    check(speed > remembered['far'] * 4, f'fast: {speed:.0f}')
    rich = [a for a in events().debris if a.mineral in RICH]
    check(len(rich) > 3, f'rich asteroids around it: {len(rich)}')
    remembered['debris'] = list(events().debris)
    x, y = orbit.position
    scenario.put_ship((x + 350, y + 250), orbit.velocity)


@scenario.step(.1)
def shows_its_tail() -> None:
    scenario.screenshot('tail')
    jump(2.9)


@scenario.step(.2)
def leaves() -> None:
    news = scenario.game.ids.news_label.text
    check('repart' in news, f'told: {news}')
    jump(math.pi - .001)


@scenario.step(.5)
def is_gone() -> None:
    check(events().comet is None, 'gone at the far end')
    check(not events().debris, 'with what it shed')
    asteroids = scenario.game.system.asteroids
    check(not set(remembered['debris']) & set(asteroids), 'all of it')
    check(scenario.game.ids.news_label.text == '', 'told no more')


scenario.run()
