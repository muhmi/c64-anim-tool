import argparse
import os
from timeit import default_number
from typing import Any, Dict

import yaml
from colorama import Fore


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
    parser.add_argument(
        "--use-color", action="store_true", default=False, help="Animate color data"
    )
    parser.add_argument(
        "--scroll",
        type=str,
        default=None,
        help="Scroll animation, needs direction: up,down,left,right",
    )
    parser.add_argument(
        "--scroll-disable-repeat",
        action="store_true",
        default=False,
        help="Disable repeat for scroll animation, for left/right",
    )
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
        default=None,
        help="Slowdown test animation by given frames",
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
        "--color-animation-slowdown",
        type=int,
        default=None,
        help="Slowdown color animation",
    )
    parser.add_argument(
        "--color-anim-min-seq-len",
        type=int,
        default=10,
        help="Minimum amount of consequent offsets to merge to a loop for color animation generated code",
    )
    parser.add_argument(
        "--color-anim-max-seq-len",
        type=int,
        default=10,
        help="Max amount of consequent offsets to merge to a loop for color animation generated code",
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
    parser.add_argument(
        "--allow-reorder-frames",
        type=bool,
        default=False,
        help="Allow reordering of frames so that frames with similar charsets are next to each other",
    )
    parser.add_argument(
        "--non-linear-prg", type=bool, default=False, help="Generate non-linear (mprg)"
    )
    parser.add_argument(
        "--skip-build", type=bool, default=False, help="Dont try to build .prg"
    )
    parser.add_argument(
        "--effect-start-address",
        type=str,
        default="$3000",
        help="Effect start address in hex",
    )
    parser.add_argument(
        "--anim-start-address",
        type=str,
        default="*",
        help="Set anim start address, defaults to after charsets",
    )
    parser.add_argument(
        "--write-petmate",
        type=bool,
        default=False,
        help="Write out a petmate file with petscii animation and charsets",
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
