import argparse
import os
import subprocess
import sys

import color_data_utils
import colorama
import petscii
import utils
from colorama import Fore
from packer import Packer, Size2D
from PIL import ImageDraw, ImageSequence


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert PNG/GIF to C64 PETSCII + charset."
    )
    parser.add_argument(
        "input_files", type=str, nargs="+", help="Input .c, PNG or GIF files."
    )
    parser.add_argument(
        "--charset",
        type=str,
        default=None,
        help="Use this charset instead (.64c or .bin)",
    )
    parser.add_argument(
        "--cleanup",
        type=int,
        default=1,
        help="Remove characters with under N pixels",
    )
    parser.add_argument(
        "--color-data",
        type=str,
        default=None,
        help="Use this file as source for color data",
    )
    parser.add_argument("--use-color", action="store_true", help="Animate color data")
    parser.add_argument(
        "--limit-charsets",
        type=int,
        default=4,
        help="Try to limit amount of charsets to this number, must be over 1",
    )
    parser.add_argument(
        "--start-threshold",
        type=int,
        default=2,
        help="When limiting charsets use this threshold value for closeness of characters at start (1 to 7)",
    )
    parser.add_argument(
        "--border-color", type=int, default=0, help="Use this border color"
    )
    parser.add_argument(
        "--background-color",
        type=int,
        default=None,
        help="Assume image background is this color",
    )
    parser.add_argument(
        "--anim-slowdown-frames",
        type=int,
        default=0,
        help="Slowdown test animation by given frames",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["petscii", "animation"],
        default="petscii",
        help="Conversion mode: 'petscii' or 'animation'. Default is 'petscii'.",
    )
    parser.add_argument(
        "--offset-color-frames",
        type=int,
        default=None,
        help="Offset color frames by given value, can be negative",
    )
    parser.add_argument(
        "--randomize-color-frames",
        type=int,
        default=None,
        help="Randomize color frames, use given value as random seed",
    )
    parser.add_argument(
        "--disable-rle", type=bool, default=False, help="Disable RLE encoder"
    )
    parser.add_argument(
        "--inverse", type=bool, default=False, help="Inverse characters"
    )
    parser.add_argument(
        "--per-row-mode", type=bool, default=False, help="Per for delta packer mode"
    )
    parser.add_argument(
        "--init-color-between-anims",
        type=bool,
        default=False,
        help="Write color memory to background color between different animation source files",
    )
    parser.add_argument(
        "--color-animation",
        type=str,
        default=None,
        help="Generate code to animate color data based on first frame of this .c file",
    )
    parser.add_argument(
        "--color-animation-palette",
        type=str,
        default=None,
        help="Read color palette from a file for the color animation (if a file is given its assumed to be an image with first row being the palette)",
    )
    return parser.parse_args()


def main():
    # colorama
    colorama.init(autoreset=True)

    args = parse_arguments()

    default_charset = None

    build_folder = get_build_path()

    if args.charset:
        if os.path.exists(args.charset) == False:
            print(Fore.RED + f"File {args.charset} does not exist")
            return 1

        skipFirstBytes = args.charset.endswith(".64c")

        print(f"Reading charset from file {args.charset}")
        default_charset = petscii.read_charset(args.charset, skipFirstBytes)
        print(f"{len(default_charset)} characters found.")

    utils.create_folder_if_not_exists(build_folder)
    clean_build()

    anim_change_index = []

    screens = []
    for input_file in args.input_files:
        print(
            Fore.BLUE
            + f"Processing {
                input_file}, writing output to folder {
                build_folder}"
        )

        if default_charset is None and (input_file.endswith(".c")):
            script_dir = os.path.dirname(__file__)
            print(f"No default charset provided, using c64_charset.bin")
            default_charset = petscii.read_charset(f"{script_dir}/data/c64_charset.bin")

        if os.path.exists(input_file) == False:
            print(Fore.RED + f"File {input_file} does not exist")
            return 1
        screens_in_file = petscii.read_screens(
            input_file,
            default_charset,
            args.background_color,
            args.border_color,
            args.inverse,
            args.cleanup,
        )
        anim_change_index.append(len(screens))
        print(f"Found {len(screens_in_file)} screens in file")
        screens.extend(screens_in_file)

    charsets = [default_charset]

    if args.color_data:
        print(f"Reading color data from {args.color_data}")
        color_data_frames = petscii.read_screens(
            args.color_data, default_charset, args.background_color, args.border_color
        )
        for idx, screen in enumerate(screens):
            color_frame = idx % len(color_data_frames)
            screen.color_data = [] + color_data_frames[color_frame].color_data

    if args.offset_color_frames:
        print(f"Offsetting color frames by {args.offset_color_frames}")
        screens = color_data_utils.offset_color_frames(
            screens, args.offset_color_frames
        )

    if args.randomize_color_frames:
        print(f"Randomizing color frames with seed {args.randomize_color_frames}")
        screens = color_data_utils.randomize_color_frames(
            screens, args.randomize_color_frames
        )

    if default_charset is None:
        print(f"Remove duplicate characters")
        screens, charsets = petscii.merge_charsets(screens, build_folder)

    for idx, screen in enumerate(screens):
        print(f"  screen {idx}: characters={screen.charset_size()}")

    if args.limit_charsets:
        if len(charsets) > args.limit_charsets:
            screens, charsets = petscii.merge_charsets_compress(
                screens, args.limit_charsets
            )
        else:
            print(f"No need to limit charsets, already at {len(charsets)}")

    fill_color_palette = [1, 7, 3, 5, 4, 2, 6, 0]
    if args.color_animation_palette:
        fill_color_palette = utils.read_color_palette(args.color_animation_palette)

    print(f"Packing, use_color = {args.use_color}")

    smallest_size = None
    selected_block_size = None

    block_sizes = [
        Size2D(2, 2),
        Size2D(2, 3),
        Size2D(3, 2),
        Size2D(3, 3),
        Size2D(3, 4),
        Size2D(4, 3),
        Size2D(4, 4),
        Size2D(4, 5),
    ]

    def locations_with_same_color(screen: petscii.petscii_screen):
        points = {}
        for y in range(25):
            for x in range(40):
                offset = y * 40 + x
                color = screen.color_data[offset]
                if color in points:
                    points[color].append(y * 40 + x)
                else:
                    points[color] = [y * 40 + x]
        return points

    def set_packer_options(packer, args):
        if args.per_row_mode:
            packer.ONLY_PER_ROW_MODE = True
        if args.disable_rle:
            packer.set_rle_encoder_enabled(False)
        if args.init_color_between_anims:
            packer.INIT_COLOR_MEM_BETWEEN_ANIMS = True
            packer.ANIM_CHANGE_SCREEN_INDEXES = anim_change_index
        if args.color_animation:
            packer.FILL_COLOR_WITH_EFFECT = True
            screens = petscii.read_screens(args.color_animation)
            packer.FILL_COLOR_BLOCKS = locations_with_same_color(screens[0])
            packer.FILL_COLOR_PALETTE = fill_color_palette

    no_color_support = Size2D(2, 2)

    for block_size in block_sizes:

        if args.use_color and block_size == no_color_support:
            continue

        packer = Packer(block_size=block_size)
        set_packer_options(packer, args)
        anim_stream = packer.pack(screens, charsets, args.use_color)

        if smallest_size is None or len(anim_stream) < smallest_size:
            smallest_size = len(anim_stream)
            selected_block_size = block_size

    packer = Packer(block_size=selected_block_size)
    set_packer_options(packer, args)
    anim_stream = packer.pack(
        screens, charsets, args.use_color, allow_debug_output=True
    )

    print(
        f"Selected block size {selected_block_size}, blocks: {len(packer.ALL_BLOCKS)}, used blocks: {len(packer.USED_BLOCKS)}, anim: {build_folder}, generated {len(anim_stream)} bytes of animation data"
    )

    utils.write_bin(f"{build_folder}/anim.bin", anim_stream)

    packer.write_player(
        screens,
        charsets,
        build_folder,
        args.anim_slowdown_frames,
        args.use_color,
    )

    print("Writing charsets")
    for idx, charset in enumerate(charsets):
        petscii.write_charset(
            charset,
            f"{
                build_folder}/charset_{idx}.bin",
        )

    build()

    return 0


def get_build_path():
    return utils.get_resource_path("build")


def get_c64tass_path():
    return utils.get_resource_path(os.path.join("bins", "macos", "64tass"))


def clean_build():
    folder_path = get_build_path()
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def build():
    # -o test.prg test.asm
    result = subprocess.run(
        [get_c64tass_path(), "-B", "-o", "test.prg", f"{get_build_path()}/test.asm"],
        capture_output=True,
        text=True,
    )
    print(f"Return code: {result.returncode}")
    print(f"Output: {result.stdout}")
    print(f"Errors: {result.stderr}")


if __name__ == "__main__":
    sys.exit(main())
