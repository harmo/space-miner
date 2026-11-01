""" A comet passes through the solar system: told, on the map with its path,
slow far away and racing by the sun, its tail growing. It sheds ice, which
the ship mines, then richer asteroids, all gone with it. """

import math
from typing import Any

from app.engine.entities import get_body
from app.logic.config import COMET_COLOR, SWARM_COLOR
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
    comets = events().comets
    comets.orbit.set_anomaly(anomaly)
    body = get_body(scenario.game.gameworld, comets.comet.entity_id)
    body.position = comets.orbit.position


@scenario.step(1.)
def waits_for_a_comet() -> None:
    check(events().comets.comet is None, 'none at first')
    events().comets.clock.waiting = 0.


@scenario.step(.3)
def a_comet_comes() -> None:
    check(events().comets.comet is not None, 'a comet comes')
    system = scenario.game.system
    distance = math.dist(events().comets.comet.pos, system.sun.pos)
    check(abs(distance - system.orbits[-1]) < 50,
          f'from as far as the last planet: {distance:.0f}')
    check('comet' in played and 'swarm' not in played, f'heard: {played}')
    news = scenario.game.ids.news.text
    check('Comète' in news and 'près du soleil' in news, f'told: {news}')
    events().swarms.bulletin.tell("L'essaim a quitté le système")


@scenario.step(.2)
def is_told_along_with_the_rest() -> None:
    lines = scenario.game.ids.news.children
    check(len(lines) == 2, f'a line each: {scenario.game.ids.news.text}')
    comet, swarm = reversed(lines)
    check('Comète' in comet.text and 'essaim' in swarm.text,
          'the comet first')
    check(tuple(comet.color[:3]) == COMET_COLOR
          and tuple(swarm.color[:3]) == SWARM_COLOR, 'each with its color')
    scenario.screenshot('news')
    events().swarms.bulletin.left = 0.
    scenario.press(scenario.game.ids.map_button)


@scenario.step(.3)
def is_on_the_map() -> None:
    scenario.screenshot('map')
    scenario.game.map_open = False


@scenario.step(.3)
def sheds_ice_far_from_the_sun() -> None:
    debris = events().comets.debris
    check(len(debris) == COMET_ICE, f'around it: {len(debris)}')
    check(all(a.mineral == 'ice' for a in debris), 'of ice')
    check(all(a.orbit.parent is events().comets.comet for a in debris),
          'turning around it')
    comet, asteroid = events().comets.comet, debris[0]
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
    orbit = events().comets.orbit
    remembered['far'] = 50.
    scenario.put_ship((orbit.position[0] + 8000, orbit.position[1]), (0, 0))


@scenario.step(.2)
def goes_by_with_its_tail() -> None:
    orbit, sun = events().comets.orbit, scenario.game.system.sun
    distance = math.dist(orbit.position, sun.pos) - sun.radius
    check(tail_length(distance) > 0, f'with its tail: {distance:.0f}')
    speed = math.hypot(*orbit.velocity)
    check(speed > remembered['far'] * 4, f'fast: {speed:.0f}')
    rich = [a for a in events().comets.debris if a.mineral in RICH]
    check(len(rich) > 3, f'rich asteroids around it: {len(rich)}')
    remembered['debris'] = list(events().comets.debris)
    x, y = orbit.position
    scenario.put_ship((x + 350, y + 250), orbit.velocity)


@scenario.step(.1)
def shows_its_tail() -> None:
    scenario.screenshot('tail')
    jump(2.9)


@scenario.step(.2)
def leaves() -> None:
    news = scenario.game.ids.news.text
    check('repart' in news, f'told: {news}')
    jump(math.pi - .001)


@scenario.step(.5)
def is_gone() -> None:
    check(events().comets.comet is None, 'gone at the far end')
    check(not events().comets.debris, 'with what it shed')
    asteroids = scenario.game.system.asteroids
    check(not set(remembered['debris']) & set(asteroids), 'all of it')
    check(scenario.game.ids.news.text == '', 'told no more')


scenario.run()
