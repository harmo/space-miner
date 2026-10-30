""" What the interface of the game shows, refreshed on each frame: the
cargo, the fuel, the heat, what the missions need, the landing shortcut
and the messages """

from typing import TYPE_CHECKING

from ...logic.hud import message
from ...logic.ship.landing import nearest
from .cargo_panel import show_cargo
from .gauges import show_fuel, show_heat
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
    game.land_glow = show_shortcut(
        ids.land_button, player.shortcut,
        nearest(player.grounds, player.anchor).docking, game.time,
    )
    show_fuel(ids.fuel, player.tank)
    show_heat(ids.heat, player.hull)
    ids.message_label.text = message(
        miner.message, player.tank.gauge, player.hull.warmth,
        player.parking is not None,
    )
    events = game.system.events
    ids.news_label.text = events.headline
    ids.news_label.color = (*events.headline_color, 1)
