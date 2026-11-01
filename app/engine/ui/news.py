""" What happens in the solar system, at the top of the screen: a line for
each event, the most urgent first. Styled in news.kv. """

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from ...logic.world.bulletin import Headline
from .widgets import load_style


class NewsLine(Label):
    pass


class NewsBoard(BoxLayout):

    def show(self, headlines: list[Headline]) -> None:
        if len(self.children) != len(headlines):
            self.clear_widgets()
            for _ in headlines:
                self.add_widget(NewsLine())
        lines = reversed(self.children)
        for line, headline in zip(lines, headlines, strict=True):
            line.text = headline.text
            line.color = (*headline.color, 1)

    @property
    def text(self) -> str:
        """ All of it, from the top """
        return '\n'.join(line.text for line in reversed(self.children))


load_style(__file__)
