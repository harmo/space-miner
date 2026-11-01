""" Three games side by side, each with its solar system: one played, left
for an empty slot, crashed in, then back as it was, again and again,
nothing of the others left behind. Then a slot erased. """

import os
from pathlib import Path
from typing import Any

from .harness import Scenario

scenario = Scenario('slots')
check = scenario.check
remembered: dict[str, Any] = {}


def home() -> Any:
    return scenario.game.ids.home


def card(slot: int) -> Any:
    return next(c for c in home().ids.slots.children if c.slot == slot)


def planets() -> list[float]:
    """ Where its first asteroids turn, drawn from its seed """
    system = scenario.game.system
    return [
        round(system.planned[asteroid].orbit_radius, 2)
        for asteroid in system.belts[0][:10]
    ]


def entities() -> int:
    """ In the physics engine """
    physics = scenario.game.gameworld.system_manager['cymunk_physics']
    return len(physics.space.bodies)


def into_the_sun() -> None:
    sun = scenario.game.system.sun
    scenario.put_ship((sun.pos[0] + sun.radius, sun.pos[1]), (0., 0.))


@scenario.step(1.)
def plays_the_first() -> None:
    scenario.screenshot('home')
    check(not scenario.game.ids.settings.parent.shown, 'no settings yet')
    scenario.base.wallet.earn(1234)
    scenario.player.miner.ore['gold'] = 4.
    remembered['planets'] = planets()
    remembered['entities'] = entities()
    # An empty slot draws its own solar system
    seed = int(os.environ['SPACE_MINER_SEED'])
    os.environ['SPACE_MINER_SEED'] = str(seed + 1)
    scenario.game.pause()


@scenario.step(.3)
def sees_the_slots() -> None:
    check('1 234 cr' in card(1).text, f'its game: {card(1).text}')
    check(card(1).current, 'shown as the paused one')
    check('Nouvelle partie' in card(2).text, f'the next: {card(2).text}')
    check(card(1).filled and not card(2).filled, 'only one can be erased')
    scenario.screenshot('paused')
    scenario.press(scenario.button(card(2), card(2).text))


@scenario.step(.5)
def starts_a_new_one() -> None:
    game = scenario.game
    check(game.playing and game.slot == 2, 'playing the second')
    check(scenario.base.wallet.credits == 0, 'without the credits')
    check(not scenario.player.miner.ore, 'nor the cargo')
    check(planets() != remembered['planets'], 'in another solar system')
    data = Path(scenario.data)
    check((data / 'save.json').exists(), 'the first one was saved')
    scenario.base.wallet.earn(500)
    scenario.player.miner.ore['iron'] = 6.
    into_the_sun()


@scenario.step(.5)
def crashes_there() -> None:
    check(scenario.player.ship is None, 'the sun is as solid as ever')
    check(scenario.player.canisters.canisters, 'its cargo thrown away')
    scenario.game.pause()
    remembered['second'] = planets()


@scenario.step(.3)
def goes_back() -> None:
    scenario.press(scenario.button(card(1), card(1).text))


@scenario.step(.5)
def finds_it_as_it_was() -> None:
    game = scenario.game
    check(game.slot == 1 and game.preferences.slot == 1, 'the first again')
    check(scenario.base.wallet.credits == 1234, 'with its credits')
    check(scenario.player.miner.ore == {'gold': 4.}, 'and its cargo')
    check(planets() == remembered['planets'], 'and its solar system')
    check(not scenario.player.canisters.canisters, 'no canister of the other')
    check(entities() == remembered['entities'],
          f'nothing left behind: {entities()}')
    game.choose(2)


@scenario.step(.5)
def and_back_again() -> None:
    check(scenario.base.wallet.credits == 500, 'the second as it was')
    check(planets() == remembered['second'], 'in its solar system')
    check(scenario.player.canisters.canisters, 'its canisters too')
    scenario.game.choose(1)


@scenario.step(.5)
def goes_on_flying() -> None:
    check(entities() == remembered['entities'],
          f'still nothing left behind: {entities()}')
    check(scenario.player.ship is not None, 'with a ship')
    into_the_sun()


@scenario.step(.5)
def crashes_as_well() -> None:
    check(scenario.player.ship is None, 'collisions still work')


@scenario.step(1.5)
def pauses() -> None:
    scenario.game.pause()


@scenario.step(.3)
def erases_the_other() -> None:
    scenario.press(scenario.button(card(2), 'Effacer'))


@scenario.step(.3)
def is_asked_first() -> None:
    check(card(2).confirming, 'erasing takes a confirmation')
    scenario.screenshot('erasing')
    scenario.press(scenario.button(card(2), 'Confirmer'))


@scenario.step(.3)
def has_it_erased() -> None:
    check(not (Path(scenario.data) / 'save_2.json').exists(), 'gone')
    check('Nouvelle partie' in card(2).text, f'told: {card(2).text}')
    check(scenario.game.paused and scenario.game.slot == 1,
          'the game under way stays')


scenario.run()
