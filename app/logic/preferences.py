""" Settings chosen by the player, kept apart from the saved game: a new
game keeps them """

import json
from dataclasses import asdict, dataclass, fields


@dataclass
class Preferences:
    orbits: bool = True       # dotted orbits of the planets
    markers: bool = True      # towards the Earth and asteroids, on the edges
    fullscreen: bool = True   # on computers
    # Volumes, from 0, silent, to 1
    sounds: float = 1.        # of everything but the ambience
    ambience: float = 1.      # space humming all around


def dump_preferences(preferences: Preferences) -> str:
    return json.dumps(asdict(preferences), indent=1, sort_keys=True)


def load_preferences(text: str) -> Preferences:
    """ The defaults for whatever is missing or unreadable """
    try:
        data = json.loads(text)
    except ValueError:
        return Preferences()
    if not isinstance(data, dict):
        return Preferences()
    known: dict[str, bool | float] = {}
    for item in fields(Preferences):
        value = data.get(item.name)
        if isinstance(value, bool):
            if item.type is bool:
                known[item.name] = value
        elif isinstance(value, int | float) and item.type is float:
            known[item.name] = max(0., min(float(value), 1.))
    return Preferences(**known)  # type: ignore[arg-type]
