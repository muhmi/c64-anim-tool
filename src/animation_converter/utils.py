import math
import os
import shutil

from PIL import Image, ImageDraw, ImageSequence

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


def rgb_to_idx(rgb):
    smallestError = 1000000
    idx = 0
    for i in range(16):
        cr = vicPalette[i][0] - rgb[0]
        cg = vicPalette[i][1] - rgb[1]
        cb = vicPalette[i][2] - rgb[2]
        err = math.sqrt((cr * cr) + (cg * cg) + (cb * cb))
        if err < smallestError:
            smallestError = err
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