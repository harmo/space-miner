""" Masks of the drawings: their round silhouette, the holes they enclose,
and their outline """


from PIL import Image, ImageDraw

SUPERSAMPLING = 4             # for smooth disc edges


def holes_mask(alpha: Image.Image) -> Image.Image:
    """ Transparent areas that can't be reached from the image border """
    solid = alpha.point(lambda a: 255 if a > 127 else 0)
    width, height = solid.size
    border = (
        [(x, y) for x in range(width) for y in (0, height - 1)]
        + [(x, y) for y in range(height) for x in (0, width - 1)]
    )
    # A ring can split the outside in several parts, flood each of them
    for point in border:
        if solid.getpixel(point) == 0:
            ImageDraw.floodfill(solid, point, 128)
    return solid.point(lambda v: 255 if v == 0 else 0)
