""" What the interface of the game shows, refreshed on each frame: the
cargo, the fuel, the heat, what the missions need, the landing shortcut
and the messages """

from typing import TYPE_CHECKING

from ...logic.hud import message
from .cargo_panel import show_cargo
from .gauges import show_fuel, show_heat
from .land_button import show_shortcut
from .tracker import show_needs

if TYPE_CHECKING:
    from ..game import Game


def show_hud(game: 'Game') -> None:
    ids, player = game.ids, game.player
    miner = player.miner
    stop = game.stop
    post = stop.post if stop else None
    unloaded = post.depot.mineral if post else None
    load = show_cargo(ids.cargo, miner, miner.mining or unloaded)
    ids.cargo_button.text = f'Soute  {load}'
    show_needs(ids.tracker, game.desks, player)
    game.land_glow = show_shortcut(
        ids.land_button, player.shortcut,
        player.grounds.nearest(player.anchor).kind, game.time,
    )
    show_fuel(ids.fuel, player.tank)
    show_heat(ids.heat, player.heat)
    ids.message_label.text = message(
        miner.message, player.tank.state, player.heat.warmth,
        player.parking is not None,
    )
    events = game.system.events
    ids.news_label.text = events.headline
    ids.news_label.color = (*events.headline_color, 1)
