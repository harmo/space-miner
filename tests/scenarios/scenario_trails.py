""" Exhaust trails, one look per engine, while thrusting only """

from typing import Any

from app.logic.ship.shipyard import Design
from app.logic.ship.trails import TRAILS

from .harness import Scenario

scenario = Scenario('trails')
check = scenario.check
DESIGNS = {
    'hull': Design(),
    'engine': Design(parts={'rear': 'engine'}),
    'twin_engine': Design(parts={'rear': 'twin_engine'}),
    'afterburner': Design(parts={'rear': 'afterburner'}),
    'ion_engine': Design(parts={'rear': 'ion_engine'}),
    'fusion_engine': Design(parts={'rear': 'fusion_engine'}),
    'solar_sail': Design(parts={'rear': 'solar_sail'}),
    'cruiser': Design('cruiser', {
        'rear_left': 'fusion_engine', 'rear_right': 'vector_nozzle',
    }),
}
remembered: dict[str, Any] = {}


def styles() -> set[Any]:
    return {spark.style for spark in scenario.game.looks.exhaust.trail.sparks}


def flight(name: str, design: Design) -> None:
    def refits() -> None:
        player = scenario.player
        player.restart(design)
        scenario.game.camera.camera_scale = .4

    def takes_off() -> None:
        check(not styles(), f'{name}: no trail once landed')
        remembered['touch'] = scenario.hold_towards(
            scenario.away_from_earth()
        )

    def thrusts() -> None:
        scenario.game.camera.look_at(scenario.player.ship.position)
        scenario.screenshot(name)
        remembered['touch'].touch_up()
        expected = {TRAILS[style] for _, style in
                    scenario.game.looks.exhaust.nozzles}
        check(styles() == expected, f'{name}: its own trail')

    def fades() -> None:
        check(not styles(), f'{name}: no trail once it stops thrusting')

    scenario.step(.3)(refits)
    scenario.step(.3)(takes_off)
    scenario.step(.7)(thrusts)
    scenario.step(1.5)(fades)


for name, design in DESIGNS.items():
    flight(name, design)

scenario.run()
