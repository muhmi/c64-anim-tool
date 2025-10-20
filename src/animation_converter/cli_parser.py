import argparse
import os
from typing import Any, Dict

# Import logger - will use default INFO level until setup_logging is called
from logger import get_logger
import yaml

logger = get_logger()


def convert_arg_name(name: str, to_snake: bool = True) -> str:
    """Convert between snake_case and dash-arguments."""
    if to_snake:
        return name.replace("-", "_")
    else:
        return name.replace("_", "-")


def load_config_file(file_path: str) -> Dict[str, Any]:
    logger.success(f"Reading config from {file_path}")
    if file_path.endswith((".yml", ".yaml")):
        with open(file_path) as f:
            return yaml.safe_load(f)
    else:
        raise ValueError("Config file must be YAML (.yml/.yaml)")


def resolve_file_paths(
    config_data: Dict[str, Any], config_dir: str, script_dir: str, cwd: str
) -> Dict[str, Any]:
    """Resolve file paths in config data, trying multiple base directories."""

    def resolve_single_path(value: str) -> str:
        if os.path.isabs(value):
            return value

        # Try relative to config file first
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

    def resolve_path_value(value):
        if isinstance(value, str) and ("/" in value or "\\" in value):
            return resolve_single_path(value)
        elif isinstance(value, list):
            return [
                (
                    resolve_single_path(item)
                    if isinstance(item, str) and ("/" in item or "\\" in item)
                    else item
                )
                for item in value
            ]
        return value

    resolved_config = {}
    for key, value in config_data.items():
        resolved_config[key] = resolve_path_value(value)

    return resolved_config


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert PNG/GIF to C64 PETSCII + charset."
    )

    # Make config required and input_files optional
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to config file (YAML) - required",
    )

    # Make input_files optional - can be overridden by config or used as fallback
    parser.add_argument(
        "input_files",
        type=str,
        nargs="*",  # Changed from "+" to "*" to make it optional
        help="Input .c, PNG or GIF files (optional if defined in config)",
        default=[],
    )

    # All other arguments remain the same
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
        default=0,
        help="Slowdown test animation by given frames",
    )
    parser.add_argument(
        "--anim-slowdown-table",
        type=int,
        default=0,
        help="Slowdown test animation by given frames, using this table",
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
        "--color-aberration-mode",
        type=bool,
        default=True,
        help="Animate background color and wiggle horizontal scroll register",
    )
    parser.add_argument(
        "--color-aberration-colors",
        type=str,
        default="2,5,6",
        help="List of colors to loop through",
    )
    parser.add_argument(
        "--color-aberration-scroll",
        type=str,
        default="0,0,0",
        help="Horizontal scroll register values",
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
    parser.add_argument(
        "--asm-test-runner-name",
        type=str,
        default="player_test_setup.asm",
        help="Name of the asm file to use for building test .prg",
    )
    parser.add_argument(
        "--fast-mode",
        type=bool,
        default=False,
        help="Skip double buffering and try to run 50fps",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG level) output",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress all output except errors",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Write detailed logs to file",
    )

    args = parser.parse_args()

    # Color aberration mode needs inverse charset
    if args.color_aberration_mode:
        args.inverse = True
        args.disable_rle = True
        args.per_row_mode = True
        args.asm_test_runner_name = "player_50fps_test.asm"

    if args.fast_mode:
        args.asm_test_runner_name = "player_50fps_test.asm"

    # Load and merge config file
    config_data = load_config_file(args.config)
    validate_config_against_parser(config_data, parser)

    # Get base directories for path resolution
    config_dir = os.path.dirname(os.path.abspath(args.config))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()

    # Resolve file paths in config
    config_data = resolve_file_paths(config_data, config_dir, script_dir, cwd)

    # Handle input files - priority: CLI args > config > error
    if args.input_files:
        # CLI input files provided, use them (but still apply config for other settings)
        final_input_files = args.input_files
        logger.warning(f"Using input files from command line: {final_input_files}")
    elif "input_files" in config_data or "input-files" in config_data:
        # Input files defined in config
        config_input_files = config_data.get("input_files") or config_data.get(
            "input-files"
        )
        if isinstance(config_input_files, str):
            final_input_files = [config_input_files]
        elif isinstance(config_input_files, list):
            final_input_files = config_input_files
        else:
            raise ValueError(
                "input_files in config must be a string or list of strings"
            )
        logger.success(f"Using input files from config: {final_input_files}")
    else:
        raise ValueError(
            "No input files specified. Either provide them as command line arguments or define 'input_files' in your config file."
        )

    # Convert config to dict and update with command line arguments
    args_dict = vars(args)
    args_dict["input_files"] = final_input_files

    # Only update values that weren't explicitly set in command line
    for key, value in config_data.items():
        if key in ["input_files", "input-files"]:
            continue  # Already handled above

        # Convert snake_case config keys to dash-style argument names
        arg_key = convert_arg_name(key, to_snake=False)
        # Remove leading dashes if present in the key
        arg_key = arg_key.lstrip("-")
        # Convert back to snake_case for argparse
        arg_key = convert_arg_name(arg_key, to_snake=True)

        if (
            arg_key in args_dict
            and arg_key != "config"
            and args_dict[arg_key] == parser.get_default(arg_key)
        ):
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

    # Add special config-only keys that are valid
    valid_args.add("input_files")
    valid_args.add("input-files")  # Allow both snake_case and dash-case

    # Check each config key against valid arguments
    invalid_keys = []
    for key in config_data:
        arg_key = convert_arg_name(key, to_snake=True)
        if arg_key not in valid_args:
            invalid_keys.append(key)

    if invalid_keys:
        raise ValueError(
            f"Invalid configuration options found in config file: {', '.join(invalid_keys)}\n"
            f"Valid options are: {', '.join(sorted(valid_args))}"
        )
