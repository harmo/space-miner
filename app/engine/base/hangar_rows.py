""" Rows of the hangar: the slots of the ship, the parts fitting the one
picked, and the stats of the ship. Styled in hangar.kv. """

from typing import Any, Literal

from kivy.input.motionevent import MotionEvent
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from ...logic.base.shop import (
    Buyable,
    can_buy,
    missing_materials,
    resale_price,
)
from ...logic.mining.minerals import MINERALS
from ...logic.ship.hulls import HULLS
from ...logic.ship.lasers import laser
from ...logic.ship.parts import PARTS, effects
from ...logic.ship.shipyard import (
    Design,
    ShipStats,
    fitted,
    ship_stats,
    transfer,
)
from .missions_panel import credits_text

Action = Literal['fitted', 'fit', 'buy', 'remove']
MONEY = '#ffd166'
LACKING = '#ff8c80'
# Stats, better the lower they are
LOWER_BETTER = {'Conso. en vol', 'Conso. au tir'}


class SlotButton(BoxLayout):
    panel = ObjectProperty(None)        # the hangar
    slot = StringProperty('')           # id of the slot
    name = StringProperty('')
    part = StringProperty('')           # name of the part fitted
    selected = BooleanProperty(False)


class PartRow(BoxLayout):
    """ Pressed, the ship shows how it would be with it """
    panel = ObjectProperty(None)
    part = ObjectProperty(None, allownone=True)  # id, None takes it off
    name = StringProperty('')
    detail = StringProperty('')         # what it changes
    cost = StringProperty('')           # markup
    action = StringProperty('')
    action_text = StringProperty('')
    can_act = BooleanProperty(False)
    resale = StringProperty('')         # with a part in the hangar
    selected = BooleanProperty(False)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if super().on_touch_down(touch):
            return True                 # one of its buttons
        if self.collide_point(*touch.pos):
            self.panel.choose(self.part)
            return True
        return False

    def act(self) -> None:
        if self.action == 'buy':
            self.panel.buy(self.part)
        else:
            self.panel.fit(self.part)


class StatRow(BoxLayout):
    name = StringProperty('')
    value = StringProperty('')
    change = StringProperty('')         # "better", "worse" or none


def cost_text(item: Buyable, panel: Any) -> str:
    """ Credits and ore, in red where lacking """
    money = MONEY if panel.wallet.can_pay(item.price) else LACKING
    texts = [f'[color={money}]{credits_text(item.price)}[/color]']
    lacking = missing_materials(item, panel.stock)
    for name, units in item.materials:
        color = LACKING if name in lacking else '#ffffffaa'
        texts.append(
            f'[color={color}]{units} {MINERALS[name].name}[/color]'
        )
    return '  ·  '.join(texts)


def part_row(panel: Any, part_id: str | None, design: Design, slot: str,
             chosen: str | None, load: float) -> PartRow:
    current = design.parts.get(slot)
    part = PARTS[part_id] if part_id else None
    fits = ship_stats(fitted(design, slot, part_id)).capacity >= load
    spares = panel.inventory.count(part_id) if part_id else 0
    action: Action
    if part_id == current:
        action, text, cost = 'fitted', 'Montée', ''
    elif part is None:
        action, text, cost = 'remove', 'Retirer', ''
    elif spares:
        action, text = 'fit', 'Monter'
        cost = f'{spares} en réserve' if spares > 1 else 'En réserve'
    else:
        action, text = 'buy', 'Acheter'
        cost = cost_text(part, panel)
    if not fits and action != 'fitted':
        cost = f'[color={LACKING}]Soute trop chargée[/color]'
    can_act = action != 'fitted' and fits and (
        action != 'buy' or part is not None
        and can_buy(part, panel.wallet, panel.stock)
    )
    return PartRow(
        panel=panel, part=part_id, name=part.name if part else 'Rien',
        detail=effects(part) if part else 'Emplacement libre',
        cost=cost, action=action, action_text=text, can_act=can_act,
        resale=(
            f'Vendre {credits_text(resale_price(part))}'
            if part and spares else ''
        ),
        selected=part_id == chosen,
    )


def hull_row(panel: Any, hull_id: str, design: Design, chosen: str | None,
             load: float) -> PartRow:
    """ A hull to move the ship onto """
    hull = HULLS[hull_id]
    fits = ship_stats(transfer(design, hull_id)[0]).capacity >= load
    action: Action
    if hull_id == design.hull:
        action, text, cost = 'fitted', 'Actuelle', ''
    elif hull_id in panel.inventory.hulls:
        action, text, cost = 'fit', 'Choisir', 'Au hangar'
    else:
        action, text, cost = 'buy', 'Acheter', cost_text(hull, panel)
    if not fits and action != 'fitted':
        cost = f'[color={LACKING}]Soute trop chargée[/color]'
    detail = (
        f'{len(hull.slots)} emplacements · soute {hull.capacity:.0f} · '
        f'vitesse {hull.max_speed:.0f}'
    )
    if hull.laser > 1:
        detail += f' · laser {hull.laser}'
    return PartRow(
        panel=panel, part=hull_id, name=hull.name, detail=detail, cost=cost,
        action=action, action_text=text,
        can_act=action != 'fitted' and fits and (
            action != 'buy' or can_buy(hull, panel.wallet, panel.stock)
        ),
        selected=hull_id == chosen,
    )


def stat_values(stats: ShipStats) -> list[tuple[str, float, str]]:
    level = stats.laser
    return [
        ('Vitesse', stats.max_speed, f'{stats.max_speed:.0f}'),
        ('Poussée', stats.thrust, f'{stats.thrust:.1f}'),
        ('Maniabilité', stats.turn_speed, f'{stats.turn_speed:g}'),
        ('Soute', stats.capacity, f'{stats.capacity:.0f}'),
        ('Laser', level, f'{level} · ×{laser(level).power:g}'),
        ('Scanner', stats.scan,
         f'{stats.scan:,.0f}'.replace(',', ' ') if stats.scan else 'aucun'),
        ('Réservoir', stats.tank, f'{stats.tank:.0f}'),
        ('Conso. en vol', stats.burn, f'{stats.burn:.1f} /s'),
        ('Conso. au tir', laser(level).burn, f'{laser(level).burn:.1f} /s'),
    ]


def stat_rows(current: ShipStats, compared: ShipStats) -> list[StatRow]:
    """ Those of the ship, and how they would change """
    rows = []
    for (name, now, text), (_, then, then_text) in zip(
        stat_values(current), stat_values(compared), strict=True,
    ):
        if abs(then - now) < 1e-9:
            rows.append(StatRow(name=name, value=text))
        else:
            rows.append(StatRow(
                name=name, value=f'{text}  »  {then_text}',
                change='better' if (then < now) == (name in LOWER_BETTER)
                else 'worse',
            ))
    return rows
