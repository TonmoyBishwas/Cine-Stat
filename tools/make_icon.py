"""Draw the CineStat application icon and write it out as a Windows .ico.

Run it from the project folder:

    python tools/make_icon.py

It writes `assets/cinestat.png` (used on macOS and Linux) and
`assets/cinestat.ico` (used on Windows, where the title bar, the taskbar,
Alt-Tab and every File Explorer listing all want an .ico).

There is no image library in requirements.txt and no reason to add one, so
the drawing is done with matplotlib - which the project already uses for the
Charts tab - and the .ico container is written by hand. That is less work than
it sounds: since Windows Vista an .ico is allowed to hold PNG files directly,
so the format is a six-byte header, one sixteen-byte directory entry per size,
and then the PNGs one after another.

The mark itself is a film strip whose frames are a bar chart: the two halves
of what this program does, in one shape.
"""

import struct
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                 # no window - we are only writing files
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ASSETS = Path(__file__).resolve().parent.parent / "assets"

#: Windows asks for the icon at all of these sizes: 16 in a File Explorer
#: list, 32 on the taskbar, 48 in a large-icon view, 256 in the preview pane.
SIZES = (16, 24, 32, 48, 64, 128, 256)

BACKGROUND = "#0B5FA5"                # a deep Windows blue
BACKGROUND_TOP = "#1683D8"            # ...lightening towards the top
SPROCKET = "#0A4B82"                  # the film strip's perforated edges
BARS = ["#FFFFFF", "#EAF4FF", "#BFE0FF"]


def draw(size):
    """Draw the icon at one size and return the path of the PNG written."""
    figure = plt.figure(figsize=(size / 100, size / 100), dpi=100)
    axes = figure.add_axes([0, 0, 1, 1])
    axes.set_xlim(0, 100)
    axes.set_ylim(0, 100)
    axes.axis("off")
    figure.patch.set_alpha(0)

    # The rounded square every Windows 11 icon sits on. Drawn as a stack of
    # thin bars so it fades from light at the top to dark at the bottom -
    # cheaper than a real gradient and indistinguishable at icon sizes.
    corner = 18
    tile = FancyBboxPatch((6, 6), 88, 88,
                          boxstyle=f"round,pad=0,rounding_size={corner}",
                          linewidth=0, facecolor=BACKGROUND)
    axes.add_patch(tile)
    for step in range(88):
        blend = step / 87                  # 0 at the bottom, 1 at the top
        colour = _mix(BACKGROUND, BACKGROUND_TOP, blend)
        strip = Rectangle((6, 6 + step), 88, 1.2, linewidth=0,
                          facecolor=colour)
        strip.set_clip_path(tile)
        axes.add_patch(strip)

    # The film strip: a perforated edge down each side.
    for x_position in (10, 82):
        for y_position in range(14, 90, 13):
            hole = Rectangle((x_position, y_position), 8, 7,
                             linewidth=0, facecolor=SPROCKET)
            hole.set_clip_path(tile)
            axes.add_patch(hole)

    # ...and the frames in the middle are a bar chart.
    for index, (left, height) in enumerate([(26, 28), (44, 46), (62, 64)]):
        axes.add_patch(Rectangle((left, 20), 14, height, linewidth=0,
                                 facecolor=BARS[index],
                                 joinstyle="round"))

    ASSETS.mkdir(parents=True, exist_ok=True)
    path = ASSETS / f"_icon_{size}.png"
    figure.savefig(path, dpi=100, transparent=True)
    plt.close(figure)
    return path


def _mix(first, second, amount):
    """Blend two '#rrggbb' colours: 0.0 is all `first`, 1.0 is all `second`."""
    one = [int(first.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    two = [int(second.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    blended = [round(a + (b - a) * amount) for a, b in zip(one, two)]
    return "#{:02X}{:02X}{:02X}".format(*blended)


def write_ico(png_paths, target):
    """Pack a list of PNG files into one Windows .ico.

    The layout, straight out of Microsoft's specification:

        ICONDIR     6 bytes   : reserved, type (1 = icon), how many images
        ICONDIRENTRY 16 bytes : width, height, colours, reserved, planes,
                                bit depth, size of the image, where it starts
        ...then the image data, one after another.

    A width or height of 256 does not fit in one byte, so the format writes it
    as 0 and the reader knows what that means.
    """
    images = [path.read_bytes() for path in png_paths]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)

    directory, body = b"", b""
    for size, data in zip(SIZES, images):
        side = 0 if size >= 256 else size
        directory += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32,
                                 len(data), offset)
        body += data
        offset += len(data)

    target.write_bytes(header + directory + body)
    return target


def main():
    pngs = [draw(size) for size in SIZES]

    ico = write_ico(pngs, ASSETS / "cinestat.ico")
    # The 256-pixel one is kept as the plain PNG for everywhere that is not
    # Windows; the rest were only ever scaffolding for the .ico.
    biggest = pngs[-1]
    biggest.replace(ASSETS / "cinestat.png")
    for leftover in pngs[:-1]:
        leftover.unlink()

    print(f"wrote {ico} ({ico.stat().st_size:,} bytes)")
    print(f"wrote {ASSETS / 'cinestat.png'}")


if __name__ == "__main__":
    main()
