from functools import lru_cache
import math
import os
from pathlib import Path
import shutil
import sys
from typing import List, NamedTuple
from PIL import Image

MAX_SCREEN_OFFSET = 100

vicPalette = (  # pepto old
    (0, 0, 0),  # 00 black
    (255, 255, 255),  # 01 white
    (104, 55, 43),  # 02 red
    (112, 164, 178),  # 03 cyan
    (111, 61, 134),  # 04 purple
    (88, 141, 67),  # 05 green
    (53, 40, 121),  # 06 blue
    (184, 199, 111),  # 07 yellow
    (111, 79, 37),  # 08 orange
    (67, 57, 0),  # 09 brown
    (154, 103, 89),  # 10 light_red
    (68, 68, 68),  # 11 dark_gray
    (108, 108, 108),  # 12 gray
    (154, 210, 132),  # 13 light_green
    (108, 94, 181),  # 14 light_blue
    (149, 149, 149),  # 15 light_gray
)


@lru_cache(maxsize=20000)
def rgb_to_idx(rgb):
    smallest_error = 1000000
    idx = 0
    for i in range(16):
        cr = vicPalette[i][0] - rgb[0]
        cg = vicPalette[i][1] - rgb[1]
        cb = vicPalette[i][2] - rgb[2]
        err = math.sqrt((cr * cr) + (cg * cg) + (cb * cb))
        if err < smallest_error:
            smallest_error = err
            idx = i
    return idx


def write_bin(file_name, byte_list):
    with open(file_name, "wb") as sd:
        for v in byte_list:
            sd.write(v.to_bytes(1, "big"))


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created.")
    else:
        print(f"Folder '{folder_path}' already exists.")


def save_images_as_gif(images, output_filename, duration=500, loop=0):
    # Ensure all images are in 'P' mode (palettized)
    images = [img.convert("P") for img in images]

    # Save the images as an animated GIF
    images[0].save(
        output_filename,
        save_all=True,
        append_images=images[1:],
        optimize=False,
        duration=duration,
        loop=loop,
    )


def copy_file(source_path, destination_folder):
    file_name = os.path.basename(source_path)
    destination_path = os.path.join(destination_folder, file_name)
    shutil.copy2(source_path, destination_path)
    print(f"File copied successfully from {source_path} to {destination_path}")


def get_resource_path(relative_path):
    if "__compiled__" in globals():
        # Running inside nuitka
        base_path = Path(os.path.dirname(__file__))
    elif getattr(sys, "frozen", False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in normal Python environment
        base_path = Path(__file__).parent.parent.parent

    test_path = base_path / relative_path
    print(f"Path: {test_path}")
    print(f"Path exists: {test_path.exists()}")
    print(f"Contents: {list(test_path.glob('*'))}")

    return base_path / relative_path


def read_palette_from_file(source: str) -> List[int]:
    cols = Image.open(source)
    palette = []
    (width, _) = cols.size
    for x in range(width):
        palette.append(rgb_to_idx(cols.getpixel((x, 0))))
    return palette[:255]


def read_color_palette(source: str) -> List[int]:
    if os.path.exists(source):
        return read_palette_from_file(source)
    else:
        return [int(x.strip()) for x in source.split(",")]


def locations_with_same_color(screen_for_color_data):
    points = {}
    for y in range(25):
        for x in range(40):
            offset = y * 40 + x
            color = screen_for_color_data.color_data[offset]
            if color in points:
                points[color].append(y * 40 + x)
            else:
                points[color] = [y * 40 + x]
    return points


def parse_int_table(value):
    """
    Parse a list of values given from CLI or YAML.
    Supports:
        - single integer
        - a string with comma separated list of integers
        - a list of integers or strings
    """
    if isinstance(value, list):
        return [int(x) for x in value]

    if isinstance(value, (str, int)):
        str_value = str(value)
        if "," in str_value:
            return [int(x.strip()) for x in str_value.split(",")]
        else:
            return [int(str_value)]

    raise ValueError(f"Unsupported type for anim_slowdown_frames: {type(value)}")


class Size2D(NamedTuple):
    x: int
    y: int


class Block(NamedTuple):
    x: int
    y: int
    width: int
    height: int

    def has_pixels_in_range(self):
        if self.y * 40 + self.x >= MAX_SCREEN_OFFSET:
            return False
        max_y = min(self.y + self.height - 1, 24)
        max_x = min(self.x + self.width - 1, 39)
        return max_y * 40 + max_x < MAX_SCREEN_OFFSET
