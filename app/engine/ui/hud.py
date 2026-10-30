""" What the interface of the game shows, refreshed on each frame: the
cargo, the fuel, what the missions need, the landing shortcut and the
messages """

from typing import TYPE_CHECKING

from ...logic.hud import fuel_message
from .cargo_panel import show_cargo
from .fuel_gauge import show_fuel
from .land_button import show_shortcut
from .tracker import show_needs

if TYPE_CHECKING:
    from ..game import Game


def show_hud(game: 'Game') -> None:
    ids, player = game.ids, game.player
    miner = player.miner
    load = show_cargo(ids.cargo, miner, miner.mining or ids.base.depot.mineral)
    ids.cargo_button.text = f'Soute  {load}'
    show_needs(ids.tracker, ids.base, player)
    game.land_glow = show_shortcut(ids.land_button, player.shortcut, game.time)
    show_fuel(ids.fuel, player.tank)
    ids.message_label.text = miner.message or fuel_message(
        player.tank.gauge, player.parking is not None,
    )
    ids.news_label.text = game.system.events.headline
