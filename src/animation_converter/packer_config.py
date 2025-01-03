from animation_converter import petscii
from animation_converter.utils import locations_with_same_color


def set_packer_options(
    anim_change_index, fill_color_palette, output_file_name, packer_to_setup, args
):
    if args.per_row_mode:
        packer_to_setup.ONLY_PER_ROW_MODE = True
    if args.disable_rle:
        packer_to_setup.set_rle_encoder_enabled(False)
    if args.init_color_between_anims:
        packer_to_setup.INIT_COLOR_MEM_BETWEEN_ANIMS = True
        packer_to_setup.ANIM_CHANGE_SCREEN_INDEXES = anim_change_index
    if args.color_animation:
        packer_to_setup.FILL_COLOR_WITH_EFFECT = True
        screens = petscii.read_screens(args.color_animation)
        packer_to_setup.FILL_COLOR_BLOCKS = locations_with_same_color(screens[0])
        packer_to_setup.FILL_COLOR_PALETTE = fill_color_palette
    if args.music:
        packer_to_setup.MUSIC_FILE_NAME = args.music
    if args.template_dir:
        packer_to_setup.OVERRIDE_TEMPLATE_DIR = args.template_dir
    if args.output_sources:
        packer_to_setup.OUTPUT_SOURCES_DIR = args.output_sources
    if output_file_name:
        packer_to_setup.PRG_FILE_NAME = output_file_name
