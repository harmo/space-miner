""" Painting tools for the Earth and the planets: smooth noise, gradients,
color maps, and the shading that makes a disc look round. Images are
SIZE pixels across, with the disc of the planet in their middle. """


from PIL import Image

Color = tuple[int, int, int]


def hex_color(value: str) -> Color:
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


def layer(color: Color, alpha: Image.Image) -> Image.Image:
    image = Image.new('RGBA', alpha.size, (*color, 0))
    image.putalpha(alpha)
    return image
