""" Keeps the game saved: takes it from the player and the base, and puts
it back in them """

from ..logic.base.missions import Contracts
from ..logic.base.outposts import Outpost, Progress, open_boards
from ..logic.mining.minerals import MINERALS
from ..logic.save import EARTH, Landed, Save, dump
from ..logic.ship.hulls import HULLS
from ..logic.ship.landing import Ground
from ..logic.ship.shipyard import Design
from .base.earth_base import EarthBase
from .ship.player import Player
from .storage import delete_save, write_save


class Keeper:

    def __init__(self, seed: int, player: Player, base: EarthBase,
                 outposts: list[Outpost]) -> None:
        self.seed = seed
        self.player = player
        self.base = base
        self.outposts = outposts
        self.written = ''           # last saved, not to write it again

    def snapshot(self) -> Save:
        base, board = self.base, self.base.board
        landed = self.landed
        return Save(
            seed=self.seed,
            credits=base.wallet.credits,
            design=self.player.design,
            hulls=[hull for hull in HULLS if hull in base.inventory.hulls],
            spares=dict(base.inventory.spares),
            stock=dict(base.depot.stock),
            # Lost when leaving in flight
            cargo=dict(self.player.miner.ore) if landed else {},
            validated=board.validated if board else 0,
            seen_tier=base.seen_tier,
            contracts=board.contracts if board else Contracts(),
            looked_for=[
                name for name in MINERALS if name in self.player.looked_for
            ],
            fuel=round(self.player.tank.level, 2),
            outposts={
                outpost.key: outpost.progress for outpost in self.outposts
                if outpost.progress.started
            },
            landed=landed,
        )

    @property
    def landed(self) -> Landed | None:
        """ Where the ship is parked, None in flight """
        player = self.player
        parking = player.parking
        if player.ship is None or player.landing or parking is None:
            return None
        if parking.body is player.home.body:
            return Landed(EARTH, parking.direction)
        place = next((
            outpost.key for outpost in self.outposts
            if outpost.body is parking.body
        ), None)
        return Landed(place, parking.direction) if place else None

    def ground(self, landed: Landed | None) -> Ground | None:
        """ Of the place the ship comes back to, home if unknown """
        if landed is None or landed.place == EARTH:
            return None
        return next((
            outpost.ground for outpost in self.outposts
            if outpost.key == landed.place
        ), None)

    def restore(self, save: Save) -> None:
        """ The ship comes back where it was landed, or on the Earth, the
        outposts being restored first, for their pads """
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
            board.resume(save.contracts)
        for outpost in self.outposts:
            outpost.restore(save.outposts.get(outpost.key, Progress()))
        landed = save.landed
        if landed is None:
            self.player.restart(save.design)
        else:
            self.player.restart(
                save.design, landed.direction, self.ground(landed),
            )
        tank = self.player.tank
        if save.fuel is not None:
            tank.level = min(save.fuel, tank.capacity)
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
        if self.base.board is not None:
            open_boards(
                self.outposts, self.base.wallet, self.base.board.standing,
            )
        for outpost in self.outposts:
            outpost.restore(Progress())
        player.restart(Design())
        player.tank.fill(player.tank.capacity)
        self.written = ''
        self.save()
