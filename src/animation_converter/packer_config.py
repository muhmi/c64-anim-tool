import petscii
import utils
from utils import locations_with_same_color


def parse_address(address: str):
    if address[0] == "$":
        return to_asm_hex(int(f"0x{address[1:]}", 16))
    if len(address) > 2 and address[0] == "0" and address[1] == "x":
        return to_asm_hex(int(address, 16))
    return to_asm_hex(int(address))


def to_asm_hex(num: int):
    return f"${hex(num)[2:]}"


def set_packer_options(anim_change_index, output_file_name, packer_to_setup, args):
    if args.per_row_mode:
        packer_to_setup.ONLY_PER_ROW_MODE = True
    if args.disable_rle:
        packer_to_setup.set_rle_encoder_enabled(False)
    if args.init_color_between_anims:
        packer_to_setup.INIT_COLOR_MEM_BETWEEN_ANIMATIONS = True
        packer_to_setup.ANIM_CHANGE_SCREEN_INDEXES = anim_change_index
    if args.color_animation:
        packer_to_setup.FILL_COLOR_WITH_EFFECT = True
        screens = petscii.read_screens(args.color_animation)
        packer_to_setup.FILL_COLOR_BLOCKS = locations_with_same_color(screens[0])
        if args.color_animation_palette:
            packer_to_setup.FILL_COLOR_PALETTE = utils.read_color_palette(
                args.color_animation_palette
            )
    if args.music:
        packer_to_setup.MUSIC_FILE_NAME = args.music
    if args.template_dir:
        packer_to_setup.OVERRIDE_TEMPLATE_DIR = args.template_dir
    if output_file_name:
        packer_to_setup.PRG_FILE_NAME = output_file_name
    if args.scroll:
        packer_to_setup.SCROLL_WHEN_COPY_SCREEN = True
        packer_to_setup.SCROLL_DIRECTION = args.scroll
    if args.scroll_disable_repeat:
        packer_to_setup.SCROLL_DISABLE_REPEAT = True
    if args.effect_start_address:
        packer_to_setup.EFFECT_START_ADDRESS = parse_address(args.effect_start_address)
    if args.anim_start_address:
        if args.anim_start_address != "*":
            packer_to_setup.ANIM_START_ADDRESS = parse_address(args.anim_start_address)
    if args.color_animation_slowdown:
        packer_to_setup.COLOR_ANIM_SLOWDOWN = args.color_animation_slowdown
