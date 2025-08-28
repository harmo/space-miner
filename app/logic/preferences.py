""" Settings chosen by the player, kept apart from the saved game: a new
game keeps them """

import json
from dataclasses import asdict, dataclass, fields


@dataclass
class Preferences:
    orbits: bool = True       # dotted orbits of the planets
    markers: bool = True      # towards the Earth and asteroids, on the edges
    fullscreen: bool = True   # on computers


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
    known = {
        item.name: data[item.name] for item in fields(Preferences)
        if isinstance(data.get(item.name), bool)
    }
    return Preferences(**known)
