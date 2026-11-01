""" Keeps the game saved: takes it from the player and the base, and puts
it back in them """

from ..logic.base.board import Contracts
from ..logic.base.outposts import Outpost, Progress
from ..logic.base.shuttles import ShuttleState
from ..logic.mining.minerals import MINERALS
from ..logic.save import EARTH, Landed, Save, dump
from ..logic.ship.ground import Ground
from ..logic.ship.hulls import HULLS
from .base.earth_base import EarthBase
from .base.quays import quays_of
from .ship.player import Player
from .storage import write_save


class Keeper:

    def __init__(
        self,
        seed: int,
        slot: int,
        player: Player,
        base: EarthBase,
        outposts: list[Outpost]
    ) -> None:
        self.seed = seed
        self.slot = slot            # where it is saved
        self.player = player
        self.base = base
        self.outposts = outposts
        self.written = ''           # last saved, not to write it again

    def snapshot(self) -> Save:
        base, board = self.base, self.base.board
        landed = self.landed
        system = self.player.system
        return Save(
            seed=self.seed,
            credits=base.wallet.credits,
            design=self.player.design,
            hulls=[hull for hull in HULLS if hull in base.inventory.hulls],
            spares=dict(base.inventory.spares),
            stock=dict(base.depot.stock),
            # Lost when leaving in flight
            cargo=dict(self.player.miner.ore) if landed else {},
            seen_tier=base.seen_tier,
            contracts=board.contracts if board else Contracts(),
            looked_for=[
                name for name in MINERALS if name in self.player.looked_for
            ],
            fuel=round(self.player.tank.level, 2),
            concessions=sorted(base.permits.granted),
            followed=sorted(base.permits.followed),
            scan_missions=self.player.scan_missions,
            shuttles={
                quay.key: quay.post.shuttle.state
                for quay in quays_of(base, self.outposts)
                if quay.post.shuttle.state != ShuttleState()
            },
            canisters=self.player.canisters.lost(system.attractors),
            orbits=system.angles,
            events=system.events.state(),
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
        if parking.body is player.grounds.home.body:
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
        bodies and the outposts being restored first, for their pads """
        base, board = self.base, self.base.board
        system = self.player.system
        system.resume_orbits(save.orbits)
        base.wallet.credits = save.credits
        base.inventory.spares.clear()
        base.inventory.spares.update(save.spares)
        base.inventory.hulls.clear()
        base.inventory.hulls.update(save.hulls)
        base.depot.stock.clear()
        base.depot.stock.update(save.stock)
        base.seen_tier = save.seen_tier
        base.permits.granted.update(save.concessions)
        base.permits.followed.update(save.followed)
        if board is not None:
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
        self.player.scan_missions = save.scan_missions
        for quay in quays_of(base, self.outposts):
            if quay.key in save.shuttles:
                quay.post.shuttle.resume(save.shuttles[quay.key])
        self.player.canisters.recover(save.canisters, system.attractors)
        if save.events is not None:
            system.events.resume(save.events)
        self.written = dump(save)

    def save(self) -> None:
        """ When something changed """
        save = self.snapshot()
        text = dump(save)
        if text != self.written:
            write_save(self.slot, save)
            self.written = text
