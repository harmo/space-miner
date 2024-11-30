""" Colors as floats from 0 to 1, as Kivy wants them """

Rgb = tuple[float, float, float]


def rgb(value: str) -> Rgb:
    """ '#rrggbb' to floats from 0 to 1 """
    return (
        int(value[1:3], 16) / 255,
        int(value[3:5], 16) / 255,
        int(value[5:7], 16) / 255,
    )
