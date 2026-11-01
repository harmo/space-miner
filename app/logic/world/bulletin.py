""" News shown for a few seconds at the top of the screen """

from dataclasses import dataclass

from ..colors import Rgb

NEWS_TIME = 6.                # seconds


@dataclass(frozen=True)
class Headline:
    """ A line at the top of the screen """
    text: str
    color: Rgb


class Bulletin:

    def __init__(self) -> None:
        self.news = ''
        self.left = 0.            # seconds it is shown still

    def tell(self, news: str) -> None:
        self.news, self.left = news, NEWS_TIME

    def update(self, dt: float) -> None:
        self.left = max(0., self.left - dt)

    @property
    def shown(self) -> str:
        return self.news if self.left > 0 else ''
