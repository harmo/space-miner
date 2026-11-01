""" A game opened from its slot: all that goes when another one is opened,
its solar system, its outposts, its ship and what keeps them saved. The sun
stays, see SolarSystem.dispose. """

import os
from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING

from ..logic.base.outposts import Outpost, open_boards
from ..logic.config import WORLD_SIZE
from ..logic.ship.ground import Ground, Grounds
from ..logic.world.layout import plan_system
from .base.outposts import found_outposts
from .keeper import Keeper
from .ship.looks import ShipLooks
from .ship.player import Player
from .storage import read_save
from .textures import ground_edge
from .world.solar_system import SolarSystem

if TYPE_CHECKING:
    from .game import Game


@dataclass(frozen=True)
class Session:
    system: SolarSystem
    outposts: list[Outpost]
    player: Player
    looks: ShipLooks          # of the ship: its trail and legs
    keeper: Keeper


def open_session(game: 'Game') -> Session:
    """ The game of its slot, or a new one in a solar system of its own """
    save = read_save(game.slot)
    # The same solar system comes back with the saved game. Scenarios pick
    # theirs with SPACE_MINER_SEED.
    seed = save.seed if save else int(
        os.environ.get('SPACE_MINER_SEED') or game.rng.randrange(2 ** 31)
    )
    rng, base = game.rng, game.ids.base
    system = SolarSystem(
        game.gameworld, plan_system(Random(seed)),
        center=(WORLD_SIZE / 2, WORLD_SIZE / 2), rng=rng, sun=game.sun,
    )
    outposts = found_outposts(system, rng, base.permits)
    player = Player(
        game.gameworld, system, game.camera, rng,
        Grounds([
            Ground(system.earth, tuple(ground_edge('earth'))),
            *(outpost.ground for outpost in outposts),
        ]),
    )
    game.soundtrack.listen(player)
    base.setup(player, rng)
    game.ids.outpost.setup(player, outposts, base)
    base.outposts = outposts
    open_boards(outposts, base.wallet)
    game.ids.scanner.setup(player, system, lambda: game.desks)
    keeper = Keeper(seed, game.slot, player, base, outposts)
    if save is not None:
        keeper.restore(save)
    game.stars.wrap_all(player.anchor)
    return Session(system, outposts, player, ShipLooks(rng), keeper)
