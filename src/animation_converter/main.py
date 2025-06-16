import multiprocessing
import os
import sys

import color_data_utils
import colorama
import petscii
import utils
from anim_reorder import reorder_screens_by_similarity
from build_utils import build, clean_build, get_build_path
from cli_parser import parse_arguments
from colorama import Fore
from packer import Packer
from packer_config import set_packer_options
from utils import Size2D


def main():
    # colorama
    colorama.init(autoreset=True)

    args = parse_arguments()

    default_charset = None

    build_folder = get_build_path()

    if args.charset:
        if not os.path.exists(args.charset):
            print(Fore.RED + f"File {args.charset} does not exist")
            return 1

        skip_first_bytes = args.charset.endswith(".64c")

        print(f"Reading charset from file {args.charset}")
        default_charset = petscii.read_charset(args.charset, skip_first_bytes)
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

        if not os.path.exists(input_file):
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

    if args.allow_reorder_frames:
        screens = reorder_screens_by_similarity(screens)

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

    no_color_support = Size2D(2, 2)

    for block_size in block_sizes:

        if args.use_color and block_size == no_color_support:
            continue

        packer = Packer(block_size=block_size)
        set_packer_options(anim_change_index, output_file_name, packer, args)
        anim_stream = packer.pack(
            screens, charsets, args.use_color, args.anim_slowdown_frames
        )

        if smallest_size is None or len(anim_stream) < smallest_size:
            smallest_size = len(anim_stream)
            selected_block_size = block_size

    packer = Packer(block_size=selected_block_size)
    set_packer_options(anim_change_index, output_file_name, packer, args)
    anim_stream = packer.pack(
        screens,
        charsets,
        args.use_color,
        args.anim_slowdown_frames,
        allow_debug_output=False,
    )

    print(
        f"Selected block size {selected_block_size}, blocks: {len(packer.ALL_BLOCKS)}, used blocks: {len(packer.USED_BLOCKS)}, anim: {build_folder}, generated {len(anim_stream)} bytes of animation data"
    )

    utils.write_bin(f"{build_folder}/anim.bin", anim_stream)

    packer.write_player(screens, charsets, build_folder)

    print("Writing charsets")
    for idx, charset in enumerate(charsets):
        print(f"{build_folder}/charset_{idx}.bin")
        petscii.write_charset(
            charset,
            f"{
                build_folder}/charset_{idx}.bin",
        )

    if args.output_sources:
        print(Fore.GREEN + f"Output sources to {args.output_sources}")
        utils.create_folder_if_not_exists(args.output_sources)
        for filename in os.listdir(build_folder):
            file_path = os.path.join(build_folder, filename)
            if os.path.isfile(file_path):
                utils.copy_file(file_path, args.output_sources)

    if args.skip_build == False:
        build(output_file_name, args.non_linear_prg)

    if args.write_petmate == True:
        petscii.write_petmate(screens, f"{output_file_name}.petmate", True)

    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
