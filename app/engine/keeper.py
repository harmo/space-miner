""" Keeps the game saved: takes it from the player and the base, and puts
it back in them """

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
            contracts=board.contracts,
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
        self.player.system.resume_orbits(save.orbits)
        self.restore_posts(save)
        self.restore_ship(save)
        self.restore_flights(save)
        self.written = dump(save)

    def restore_posts(self, save: Save) -> None:
        base = self.base
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
        base.board.resume(save.contracts)
        for outpost in self.outposts:
            outpost.restore(save.outposts.get(outpost.key, Progress()))

    def restore_ship(self, save: Save) -> None:
        player, landed = self.player, save.landed
        if landed is None:
            player.restart(save.design)
        else:
            player.restart(save.design, landed.direction, self.ground(landed))
        if save.fuel is not None:
            player.tank.level = min(save.fuel, player.tank.capacity)
        player.miner.ore.clear()
        player.miner.ore.update(save.cargo)
        player.looked_for = set(save.looked_for)
        player.scan_missions = save.scan_missions

    def restore_flights(self, save: Save) -> None:
        """ Shuttles, canisters adrift, and what goes on around them """
        for quay in quays_of(self.base, self.outposts):
            shuttle = quay.post.shuttle
            if quay.key in save.shuttles:
                shuttle.resume(save.shuttles[quay.key])
                if not quay.docks:
                    shuttle.retire(quay.post.depot.stock)
        system = self.player.system
        self.player.canisters.recover(save.canisters, system.attractors)
        if save.events is not None:
            system.events.resume(save.events)

    def save(self) -> None:
        """ When something changed """
        save = self.snapshot()
        text = dump(save)
        if text != self.written:
            write_save(self.slot, save)
            self.written = text
