import argparse
import os
import subprocess
import sys
from typing import Any, Dict

import color_data_utils
import colorama
import petscii
import utils
import yaml
from colorama import Fore
from packer import Packer, Size2D
from PIL import ImageDraw, ImageSequence


def convert_arg_name(name: str, to_snake: bool = True) -> str:
    """Convert between snake_case and dash-arguments."""
    if to_snake:
        return name.replace("-", "_")
    else:
        return name.replace("_", "-")


def load_config_file(file_path: str) -> Dict[str, Any]:
    print(Fore.GREEN + f"Reading config from {file_path}")
    if file_path.endswith((".yml", ".yaml")):
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    else:
        raise ValueError("Config file must be YAML (.yml/.yaml)")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert PNG/GIF to C64 PETSCII + charset."
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file (YAML)",
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
        "--full-charsets",
        action="store_true",
        help="Try to produce only full 256 char charsets, quality may suffer now",
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
    parser.add_argument(
        "--music",
        type=str,
        default=None,
        help="Include given file as music to test.prg, invalid file name leads to music being ignored.",
    )
    parser.add_argument(
        "--template-dir",
        type=str,
        default=None,
        help="Use this directory as source for templates",
    )
    parser.add_argument(
        "--output-sources",
        type=str,
        default=None,
        help="Output sources to given folder",
    )

    args = parser.parse_args()

    # If config file is specified, load and merge with command line arguments
    if args.config:
        config_data = load_config_file(args.config)

        validate_config_against_parser(config_data, parser)

        # Get base directories
        config_dir = os.path.dirname(os.path.abspath(args.config))
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cwd = os.getcwd()

        # Function to resolve a path considering multiple base directories
        def resolve_path(value):
            if os.path.isabs(value):
                return value

            # Try relative to config file
            config_relative = os.path.join(config_dir, value)
            if os.path.exists(config_relative):
                return config_relative

            # Try relative to script directory
            script_relative = os.path.join(script_dir, value)
            if os.path.exists(script_relative):
                return script_relative

            # Try relative to current working directory
            cwd_relative = os.path.join(cwd, value)
            if os.path.exists(cwd_relative):
                return cwd_relative

            # If not found, return the config-relative path as fallback
            return config_relative

        # Resolve paths in config
        for key, value in config_data.items():
            if isinstance(value, str) and ("/" in value or "\\" in value):
                config_data[key] = resolve_path(value)

        # Convert config to dict and update with command line arguments
        args_dict = vars(args)

        # Only update values that weren't explicitly set in command line
        for key, value in config_data.items():
            # Convert snake_case config keys to dash-style argument names
            arg_key = convert_arg_name(key, to_snake=False)
            # Remove leading dashes if present in the key
            arg_key = arg_key.lstrip("-")
            # Convert back to snake_case for argparse
            arg_key = convert_arg_name(arg_key, to_snake=True)

            if arg_key in args_dict and arg_key != "config":
                if args_dict[arg_key] == parser.get_default(arg_key):
                    args_dict[arg_key] = value

        # Convert back to Namespace
        args = argparse.Namespace(**args_dict)

    return args


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

    output_file_name = None

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

        if output_file_name is None:
            output_file_name = os.path.splitext(os.path.basename(input_file))[0]

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
                screens, args.limit_charsets, args.full_charsets
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
        if args.music:
            packer.MUSIC_FILE_NAME = args.music
        if args.template_dir:
            packer.OVERRIDE_TEMPLATE_DIR = args.template_dir
        if args.output_sources:
            packer.OUTPUT_SOURCES_DIR = args.output_sources
        if output_file_name:
            packer.PRG_FILE_NAME = output_file_name

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
        screens, charsets, args.use_color, allow_debug_output=False
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

    build(output_file_name)

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


def build(output_file_name):
    # -o test.prg test.asm
    result = subprocess.run(
        [
            get_c64tass_path(),
            "-B",
            "-o",
            f"{output_file_name}.prg",
            f"{get_build_path()}/{output_file_name}.asm",
        ],
        capture_output=True,
        text=True,
    )
    print(f"Return code: {result.returncode}")
    print(f"Output: {result.stdout}")
    print(f"Errors: {result.stderr}")


def validate_config_against_parser(
    config_data: Dict[str, Any], parser: argparse.ArgumentParser
) -> None:
    """
    Validate that all config keys correspond to valid parser arguments.
    Raises ValueError for invalid options.
    """
    # Get all valid argument names from parser
    valid_args = set()
    for action in parser._actions:
        # Skip the help action and positional arguments
        if isinstance(action, argparse._HelpAction) or not action.option_strings:
            continue
        # Convert from option string (e.g., '--my-option') to config key format (my_option)
        for opt in action.option_strings:
            if opt.startswith("--"):
                valid_args.add(convert_arg_name(opt.lstrip("-"), to_snake=True))

    # Check each config key against valid arguments
    invalid_keys = []
    for key in config_data.keys():
        arg_key = convert_arg_name(key, to_snake=True)
        if arg_key not in valid_args:
            invalid_keys.append(key)

    if invalid_keys:
        raise ValueError(
            f"Invalid configuration options found in config file: {', '.join(invalid_keys)}\n"
            f"Valid options are: {', '.join(sorted(valid_args))}"
        )


if __name__ == "__main__":
    sys.exit(main())
