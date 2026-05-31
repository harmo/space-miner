""" Keeps the game saved: takes it from the player and the base, and puts
it back in them """

from ..logic.mining.minerals import MINERALS
from ..logic.save import Save, dump
from ..logic.ship.hulls import HULLS
from ..logic.ship.shipyard import Design
from .base.earth_base import EarthBase
from .ship.player import Player
from .storage import delete_save, write_save


class Keeper:

    def __init__(self, seed: int, player: Player, base: EarthBase) -> None:
        self.seed = seed
        self.player = player
        self.base = base
        self.written = ''           # last saved, not to write it again

    def snapshot(self) -> Save:
        base, board = self.base, self.base.board
        return Save(
            seed=self.seed,
            credits=base.wallet.credits,
            design=self.player.design,
            hulls=[hull for hull in HULLS if hull in base.inventory.hulls],
            spares=dict(base.inventory.spares),
            stock=dict(base.depot.stock),
            cargo=dict(self.player.miner.ore),
            validated=board.validated if board else 0,
            seen_tier=base.seen_tier,
            mission_level=board.level if board else 1,
            offers=list(board.offers) if board else [],
            active=list(board.active) if board else [],
            looked_for=[
                name for name in MINERALS if name in self.player.looked_for
            ],
        )

    def restore(self, save: Save) -> None:
        """ The ship comes back landed on the Earth """
        base, board = self.base, self.base.board
        base.wallet.credits = save.credits
        base.inventory.spares.clear()
        base.inventory.spares.update(save.spares)
        base.inventory.hulls.clear()
        base.inventory.hulls.update(save.hulls)
        base.depot.stock.clear()
        base.depot.stock.update(save.stock)
        base.seen_tier = save.seen_tier
        if board is not None:
            board.validated = save.validated
            board.level = max(1, min(save.mission_level, board.tier))
            board.active[:] = save.active
            # Fresh offers rather than none, as many as the reputation
            # brings
            if save.offers:
                board.offers[:] = save.offers
            board.top_up()
        self.player.restart(save.design)
        self.player.miner.ore.clear()
        self.player.miner.ore.update(save.cargo)
        self.player.looked_for = set(save.looked_for)
        self.written = dump(save)

    def save(self) -> None:
        """ When something changed """
        save = self.snapshot()
        text = dump(save)
        if text != self.written:
            write_save(save)
            self.written = text

    def new_game(self) -> None:
        """ Everything starts over, in the same solar system """
        delete_save()
        player = self.player
        for canister in list(player.canisters.canisters):
            player.canisters.remove(canister)
        player.explosions.clear()
        player.miner.ore.clear()
        self.base.reset()
        player.restart(Design())
        self.written = ''
        self.save()
