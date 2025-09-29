from io import StringIO
from itertools import islice
import os
import sys
from typing import List

from . import color_data_utils
from colorama import Fore
from jinja2 import Environment, FileSystemLoader
from .petscii import PetsciiChar, PetsciiScreen
from .rle_codec import RLECodec
from .scroller import find_areas_with_content
from . import utils
from .utils import Block, Size2D

PACKER_MAX_OP_CODES = 255
RLE_END_MARKER = 255
SCREEN_WIDTH = 40
SCREEN_HEIGHT = 25
MAX_SCREEN_OFFSET = 1000
MIN_COMPRESSION_RUN_LENGTH = 3
PER_ROW_END_LINE_MARKER = 200
PER_ROW_CODE_OFFSET = 100


class Packer:
    def __init__(
        self, block_size: Size2D = Size2D(3, 3), macro_block_size: Size2D = Size2D(2, 4)
    ):
        self.USED_MACRO_BLOCKS = None
        self.USED_BLOCKS = None
        self.BLOCK_SIZE = block_size
        self.MACRO_BLOCK_SIZE = macro_block_size
        self.X_STEP = self.MACRO_BLOCK_SIZE.x * self.BLOCK_SIZE.x
        self.Y_STEP = self.MACRO_BLOCK_SIZE.y * self.BLOCK_SIZE.y

        self.RLE_ENCODER_ENABLED = True

        self.PACKER_BIT_TABLE = [
            0b10000000,
            0b01000000,
            0b00100000,
            0b00010000,
            0b00001000,
            0b00000100,
            0b00000010,
            0b00000001,
        ]

        self.OP_CODES = {}
        self.NAME_TO_OP_CODE = {}
        for op in range(256):
            self.OP_CODES[op] = "player_op_error"
        self.player_next_free_op = 0

        self.ALL_BLOCKS = []
        self.FILL_OP_CODES = []
        self.FILL_SAME_VALUE_OP_CODES = []
        self.FILL_RLE_OP_CODES = []
        self.FILL_RLE_SIZE = {}
        self.FILL_RLE_TEMPLATE_HELPER = {}
        self.BLOCK_OFFSETS_SIZES = set()
        self.USED_RLE_COUNTS = {}
        self.OPS_USED = set()
        self.RLE_DECODE_NEEDED = False
        self.ONLY_PER_ROW_MODE = False
        self.SCROLL_WHEN_COPY_SCREEN = False
        self.SCROLL_DIRECTION = "left"
        self.INIT_COLOR_MEM_BETWEEN_ANIMATIONS = False
        self.SCROLL_DISABLE_REPEAT = False
        self.ANIM_CHANGE_SCREEN_INDEXES = []
        self.USE_ONLY_COLOR = False
        self.FILL_COLOR_WITH_EFFECT = False
        self.FILL_COLOR_BLOCKS = {}
        self.FILL_COLOR_PALETTE = [
            0,
            0,
            11,
            11,
            12,
            12,
            15,
            15,
            7,
            7,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            7,
            7,
            15,
            15,
            12,
            12,
            11,
            11,
            0,
            0,
        ]
        self.MUSIC_FILE_NAME = "music.dat"
        self.OVERRIDE_TEMPLATE_DIR = None
        self.PRG_FILE_NAME = "test.prg"
        self.EFFECT_START_ADDRESS = 0x3000
        self.ANIM_START_ADDRESS = "*"
        self.COLOR_ANIM_SLOWDOWN = 0
        self.FILL_COLOR_MIN_SEQ_LEN = 10
        self.FILL_COLOR_MAX_SEQ_LEN = 127
        self.ANIM_SLOWDOWN_TABLE = []

        self._initialize_player_ops()

    def _initialize_player_ops(self):
        self.OP_ERROR = self.add_op("player_op_error")
        self.OP_SET_BORDER = self.add_op("player_op_set_border")
        self.OP_SET_BACKGROUND = self.add_op("player_op_set_background")
        self.OP_FRAME_END = self.add_op("player_op_frame_done")
        self.OP_SET_CHARSET = self.add_op("player_op_set_charset")
        self.OP_RESTART = self.add_op("player_op_restart")
        self.OP_SET_DEST_PTR = self.add_op("player_op_set_dest_ptr")
        self.OP_SET_COLOR_MODE = self.add_op("player_op_set_color_mode")
        self.OP_SET_SCREEN_MODE = self.add_op("player_op_set_screen_mode")
        self.OP_FULL_SCREEN_RLE = self.add_op("player_op_fill_rle_fullscreen")
        self.OP_CLEAR = self.add_op("player_op_clear")
        self.OP_CLEAR_COLOR = self.add_op("player_op_clear_color")
        self.OP_FULL_SCREEN_2x2_BLOCKS = self.add_op("player_op_fullscreen_2x2_blocks")
        self.OP_PER_ROW_CHANGES = self.add_op("player_op_per_row_changes")
        self.OP_SET_ANIM_SLOWDOWN = self.add_op("player_set_anim_slowndown")

        for macro_block in self.get_macro_blocks():
            for block in self.get_blocks(macro_block):
                self.ALL_BLOCKS.append(block)

        for block in self.ALL_BLOCKS:
            sz = len(self.offsets(block))
            if sz > 0 and sz not in self.BLOCK_OFFSETS_SIZES:
                self.BLOCK_OFFSETS_SIZES.add(sz)
                self.FILL_OP_CODES.append(self.add_op(f"player_op_fill{sz}"))
                self.FILL_SAME_VALUE_OP_CODES.append(
                    self.add_op(f"player_op_fill_same{sz}")
                )

        self.USED_BLOCKS = set()

        if self.player_next_free_op >= PACKER_MAX_OP_CODES:
            print(
                f"Player op code count is too high! {
                self.player_next_free_op}"
            )
            sys.exit(1)

    def set_rle_encoder_enabled(self, state: bool):
        self.RLE_ENCODER_ENABLED = state

    def add_op(self, asm_label: str):
        op = self.player_next_free_op
        self.player_next_free_op += 1

        self.OP_CODES[op] = asm_label
        self.NAME_TO_OP_CODE[asm_label] = op

        return op

    def get_macro_blocks(self):
        blocks = []
        for macro_y in range(0, SCREEN_HEIGHT, self.Y_STEP):
            for macro_x in range(0, SCREEN_WIDTH, self.X_STEP):
                macro_block = Block(macro_x, macro_y, self.X_STEP, self.Y_STEP)
                blocks.append(macro_block)
        return blocks

    def get_blocks(self, macro_block):
        macro_x = macro_block.x
        macro_y = macro_block.y
        blocks = []
        for y in range(macro_y, macro_y + self.Y_STEP, self.BLOCK_SIZE.y):
            for x in range(macro_x, macro_x + self.X_STEP, self.BLOCK_SIZE.x):
                if x > SCREEN_WIDTH or y > SCREEN_HEIGHT:
                    continue
                block = Block(x, y, self.BLOCK_SIZE.x, self.BLOCK_SIZE.y)
                blocks.append(block)
        return blocks

    @staticmethod
    def offsets(block):
        offsets = []
        for y in range(block.y, block.y + block.height):
            for x in range(block.x, block.x + block.width):
                offset = y * SCREEN_WIDTH + x
                if offset < MAX_SCREEN_OFFSET:
                    offsets.append(offset)
        return offsets

    def is_block_same(self, screen1: List[int], screen2: List[int], block: Block):
        return all(screen1[offset] == screen2[offset] for offset in self.offsets(block))

    def has_data(self, screen1: List[int], block: Block):
        return all(screen1[offset] == 0 for offset in self.offsets(block))

    def read_block(self, screen: List[int], block: Block):
        data = []
        for offset in self.offsets(block):
            data.append(screen[offset])
        return data

    def rle_full_screen(self, screen: List[int]):
        encoded = []
        count = 1
        current = screen[0]
        chunks = 1

        for value in screen[1:]:
            if value == current and count < RLE_END_MARKER:
                count += 1
            else:
                if count in self.USED_RLE_COUNTS:
                    self.USED_RLE_COUNTS[count] += 1
                else:
                    self.USED_RLE_COUNTS[count] = 1
                encoded.extend([count, current])
                chunks += 1
                count = 1
                current = value

        encoded.extend([count, current])

        op_name = "player_op_fill_rle_fullscreen"

        anim_stream = [self.NAME_TO_OP_CODE[op_name]]
        anim_stream.extend(encoded)
        anim_stream.append(RLE_END_MARKER)

        return anim_stream

    def diff_frames_per_row(self, screen1: List[int], screen2: List[int]):
        def build_change_list(frame_a, frame_b):
            diff = []
            for y in range(SCREEN_HEIGHT):
                for x in range(SCREEN_WIDTH):
                    offset = y * SCREEN_WIDTH + x
                    a = frame_a[offset]
                    b = frame_b[offset]
                    if a != b:
                        diff.append((x, y, b))
            return diff

        changes = build_change_list(screen1, screen2)

        anim_stream = [self.OP_PER_ROW_CHANGES]

        for y in range(SCREEN_HEIGHT):
            row_changes = sorted((c for c in changes if c[1] == y), key=lambda c: c[0])

            if len(row_changes) > 0:

                i = 0
                while i < len(row_changes):
                    run_start = i
                    run_length = 1

                    while (
                        i + 1 < len(row_changes)
                        and row_changes[i + 1][0] == row_changes[i][0] + 1
                        and row_changes[i + 1][2] == row_changes[i][2]
                        and run_length < SCREEN_WIDTH * 2
                    ):
                        i += 1
                        run_length += 1

                    if run_length > MIN_COMPRESSION_RUN_LENGTH:
                        # Write compressed form: count, x, character
                        anim_stream.append(PER_ROW_CODE_OFFSET + run_length)
                        anim_stream.append(row_changes[run_start][0])
                        anim_stream.append(row_changes[run_start][2])
                        i += 1  # move to the next change not part of the current run
                    else:
                        # Write each pixel individually
                        for j in range(run_start, i + 1):
                            anim_stream.append(row_changes[j][0])
                            anim_stream.append(row_changes[j][2])
                        i += 1

            # End of line marker
            anim_stream.append(PER_ROW_END_LINE_MARKER)

        return anim_stream

    def diff_frames_macro(self, screen1: List[int], screen2: List[int]):
        anim_stream = [self.OP_FULL_SCREEN_2x2_BLOCKS]

        for macro_block in self.get_macro_blocks():
            changes = 0
            block_changes = []
            for block_idx, block in enumerate(self.get_blocks(macro_block)):
                if not self.is_block_same(screen1, screen2, block):
                    changes |= 1 << block_idx
                    block_changes.extend(self.read_block(screen2, block))
            anim_stream.append(changes)
            anim_stream.extend(block_changes)
        return anim_stream

    def encode_block(self, screen: List[int], block: Block, anim_stream: List[int]):
        data = self.read_block(screen, block)
        if len(set(data)) <= 1:
            anim_stream.append(self.NAME_TO_OP_CODE[f"player_op_fill_same{len(data)}"])
            anim_stream.append(data[0])
        else:
            encoded = RLECodec.encode(data)
            if len(encoded) < len(data) - 2:
                op_name = f"player_op_fill_rle{
                len(encoded)}_{
                len(data)}"
                if op_name not in self.NAME_TO_OP_CODE:
                    op = self.add_op(op_name)
                    self.FILL_RLE_SIZE[op] = len(encoded)
                    self.FILL_RLE_TEMPLATE_HELPER[op_name] = {
                        "decoded": len(data),
                        "encoded": len(encoded),
                    }
                    self.FILL_RLE_OP_CODES.append(op)

                anim_stream.append(self.NAME_TO_OP_CODE[op_name])
                anim_stream.extend(encoded)
            else:
                anim_stream.append(self.NAME_TO_OP_CODE[f"player_op_fill{len(data)}"])
                anim_stream.extend(data)

    def diff_frames(self, screen1: List[int], screen2: List[int], use_color: bool):
        anim_stream = []

        if self.ONLY_PER_ROW_MODE:
            return self.diff_frames_per_row(screen1, screen2)

        if len(self.ALL_BLOCKS) > PACKER_MAX_OP_CODES:
            anim_stream = self.diff_frames_macro(screen1, screen2)
        else:
            for block_index, block in enumerate(self.ALL_BLOCKS):
                if not self.is_block_same(screen1, screen2, block):
                    # Set dest pointer
                    anim_stream.append(self.OP_SET_DEST_PTR)
                    anim_stream.append(block_index)
                    # Write the data
                    self.encode_block(screen2, block, anim_stream)

            if not use_color:
                macro = self.diff_frames_macro(screen1, screen2)
                if len(macro) < len(anim_stream):
                    anim_stream = macro

        all_values = set(screen2)
        if len(all_values) == 1:
            anim_stream = [self.OP_CLEAR, screen2[0]]
            return anim_stream

        # TODO: Bring this in for other animations?
        # per_row_changes = self.diff_frames_per_row(screen1, screen2)
        # if len(per_row_changes) < len(anim_stream):
        #    anim_stream = per_row_changes

        if self.RLE_ENCODER_ENABLED:
            full_screen_rle = self.rle_full_screen(screen2)
            if len(full_screen_rle) < len(anim_stream):
                anim_stream = full_screen_rle

        return anim_stream

    def pack(
        self,
        screens: List[PetsciiScreen],
        charsets: List[List[int]],
        use_color=False,
        allow_debug_output=False,
    ):
        anim_stream = []
        prev_charset = -1

        prev_border = 0
        prev_background = 0

        self.OPS_USED = set()
        self.USED_BLOCKS = set()
        self.USED_MACRO_BLOCKS = set()

        for idx, screen in enumerate(screens):
            for macro_block in self.get_macro_blocks():
                for block in self.get_blocks(macro_block):
                    screen1 = [0] * MAX_SCREEN_OFFSET
                    if idx > 0:
                        screen1 = screens[idx - 1].screen_codes

                    screen2 = screen.screen_codes
                    if not self.is_block_same(screen1, screen2, block):
                        self.USED_BLOCKS.add(block)
                        self.USED_MACRO_BLOCKS.add(macro_block)

                    if use_color:
                        screen1 = [0] * MAX_SCREEN_OFFSET
                        if idx > 0:
                            screen1 = screens[idx - 1].color_data

                        screen2 = screen.color_data
                        if not self.is_block_same(screen1, screen2, block):
                            self.USED_BLOCKS.add(block)
                            self.USED_MACRO_BLOCKS.add(macro_block)

        current_anim_frame_slowdown_idx = 0

        for idx, screen in enumerate(screens):
            if screen.border_color is not None and prev_border != screen.border_color:
                anim_stream.append(self.OP_SET_BORDER)
                anim_stream.append(screen.border_color)
                prev_border = screen.border_color

            if (
                screen.background_color is not None
                and prev_background != screen.background_color
            ):
                anim_stream.append(self.OP_SET_BACKGROUND)
                anim_stream.append(screen.background_color)
                prev_background = screen.background_color

            if screen.charset is not None:
                current_charset = charsets.index(screen.charset)
                if prev_charset != current_charset:
                    if allow_debug_output:
                        print(
                            f"Screen {idx}, charset change from {prev_charset} -> {current_charset}"
                        )
                    anim_stream.append(self.OP_SET_CHARSET)
                    anim_stream.append(current_charset)
                    prev_charset = current_charset

            if not self.USE_ONLY_COLOR:
                prev_petscii = [0] * MAX_SCREEN_OFFSET
                if idx > 0:
                    prev_petscii = screens[idx - 1].screen_codes
                changes = self.diff_frames(prev_petscii, screen.screen_codes, use_color)
                anim_stream.extend(changes)

            if use_color:
                anim_stream.append(self.OP_SET_COLOR_MODE)
                prev_color = [0] * MAX_SCREEN_OFFSET
                if idx > 0:
                    prev_color = screens[idx - 1].color_data

                changes = self.diff_frames(prev_color, screen.color_data, use_color)
                anim_stream.extend(changes)

                anim_stream.append(self.OP_SET_SCREEN_MODE)
            elif self.INIT_COLOR_MEM_BETWEEN_ANIMATIONS:
                if idx in self.ANIM_CHANGE_SCREEN_INDEXES:
                    print(f"frame {idx}, clear color memory to {screen.color_data[0]}")
                    anim_stream.append(self.OP_CLEAR_COLOR)
                    anim_stream.append(screen.color_data[0])

            if len(self.ANIM_SLOWDOWN_TABLE) > 0:
                slowdown = self.ANIM_SLOWDOWN_TABLE[current_anim_frame_slowdown_idx]
                anim_stream.append(self.OP_SET_ANIM_SLOWDOWN)
                anim_stream.append(slowdown)

                current_anim_frame_slowdown_idx += 1
                if current_anim_frame_slowdown_idx == len(self.ANIM_SLOWDOWN_TABLE):
                    current_anim_frame_slowdown_idx = 0

            anim_stream.append(self.OP_FRAME_END)

        anim_stream.append(self.OP_RESTART)
        self.OPS_USED.add(self.OP_CODES[self.OP_RESTART])

        offset = 0
        screen = [0] * MAX_SCREEN_OFFSET
        color = [0] * MAX_SCREEN_OFFSET
        for idx in range(len(screens)):
            screen, color, offset = self.unpack(anim_stream, offset, screen, color)

            if not self.USE_ONLY_COLOR and screen != screens[idx].screen_codes:
                print(Fore.RED + "ERROR: Packer & unpacker dont work together!!!")
                print(f"SCREEN DATA IS BROKEN AT FRAME {idx}")
                print("unpacked:")
                self.print_list(screen)
                print("expected:")
                self.print_list(screens[idx].screen_codes)
                sys.exit(1)

            if use_color and color != screens[idx].color_data:
                print(Fore.RED + "ERROR: Packer & unpacker dont work together!!!")
                print(f"COLOR DATA IS BROKEN AT FRAME {idx}")
                print("unpacked:")
                self.print_list(color)
                print("expected:")
                self.print_list(screens[idx].color_data)
                sys.exit(1)

        return anim_stream

    @staticmethod
    def print_list(ints, group_size=SCREEN_WIDTH):
        for i in range(0, len(ints), group_size):
            group = ints[i : i + group_size]
            line = ",".join(f"{num:4d}" for num in group)
            print(line)

    def unpack(
        self,
        anim_stream: List[int],
        offset: int,
        screen: List[int],
        color: List[int],
        allow_debug_output=False,
    ):
        """
        Unpacks an animation generated by pack function, used to validate that the animation stream makes sense.
        This is not intended to replay animations, only to validate.
        """

        def read_next_byte():
            nonlocal offset
            b = anim_stream[offset]
            offset += 1
            return b

        def process_state_machine():
            nonlocal offset, screen, color, block_ptr, writing_screen

            op_code = read_next_byte()
            # if self.OP_CODES[op_code] not in self.OPS_USED:
            if allow_debug_output:
                print(f"{offset:4d}: op_code {op_code}, {self.OP_CODES[op_code]}")
            self.OPS_USED.add(self.OP_CODES[op_code])

            if op_code == self.OP_FRAME_END:
                return True  # Signal to break the main loop

            elif op_code == self.OP_FULL_SCREEN_2x2_BLOCKS:
                for macro_block in self.get_macro_blocks():
                    changes = read_next_byte()
                    for block_idx, block in enumerate(self.get_blocks(macro_block)):
                        mask = 1 << block_idx
                        if changes & mask == mask:
                            for screen_offset in self.offsets(block):
                                if writing_screen:
                                    screen[screen_offset] = read_next_byte()
                                else:
                                    color[screen_offset] = read_next_byte()
                return False

            elif op_code == self.OP_SET_DEST_PTR:
                block_idx = read_next_byte()
                block_ptr = self.ALL_BLOCKS[block_idx]

            elif op_code == self.OP_SET_ANIM_SLOWDOWN:
                read_next_byte()  # next byte is slowdown frame count, not used in this validation function

            elif op_code in self.FILL_RLE_OP_CODES:
                self.RLE_DECODE_NEEDED = True
                encoded_size = self.FILL_RLE_SIZE[op_code]
                encoded = [read_next_byte() for _ in range(encoded_size)]
                decoded = RLECodec.decode(encoded)
                for idx, screen_offset in enumerate(self.offsets(block_ptr)):
                    if writing_screen:
                        screen[screen_offset] = decoded[idx]
                    else:
                        color[screen_offset] = decoded[idx]

            elif op_code in self.FILL_OP_CODES:
                for screen_offset in self.offsets(block_ptr):
                    if writing_screen:
                        screen[screen_offset] = read_next_byte()
                    else:
                        color[screen_offset] = read_next_byte()

            elif op_code in self.FILL_SAME_VALUE_OP_CODES:
                value = read_next_byte()
                for screen_offset in self.offsets(block_ptr):
                    if writing_screen:
                        screen[screen_offset] = value
                    else:
                        color[screen_offset] = value

            elif op_code == self.OP_FULL_SCREEN_RLE:
                screen_offset = 0
                while True:
                    count = read_next_byte()
                    if count == RLE_END_MARKER:
                        break
                    value = read_next_byte()
                    decoded = [value] * count
                    for code in decoded:
                        if writing_screen:
                            screen[screen_offset] = code
                        else:
                            color[screen_offset] = code
                        screen_offset += 1

            elif op_code == self.OP_PER_ROW_CHANGES:
                for y in range(SCREEN_HEIGHT):
                    code = read_next_byte()
                    if code == PER_ROW_END_LINE_MARKER:
                        continue

                    while code != PER_ROW_END_LINE_MARKER:
                        if code > PER_ROW_CODE_OFFSET:
                            count = code - PER_ROW_CODE_OFFSET
                            xpos = read_next_byte()
                            value = read_next_byte()
                            for idx in range(count):
                                screen_offset = y * SCREEN_WIDTH + xpos + idx
                                if screen_offset < MAX_SCREEN_OFFSET:
                                    if writing_screen:
                                        screen[screen_offset] = value
                                    else:
                                        color[screen_offset] = value
                        else:
                            xpos = code
                            value = read_next_byte()
                            screen_offset = y * SCREEN_WIDTH + xpos
                            if screen_offset < MAX_SCREEN_OFFSET:
                                if writing_screen:
                                    screen[screen_offset] = value
                                else:
                                    color[screen_offset] = value

                        code = read_next_byte()

            elif op_code == self.OP_CLEAR:
                value = read_next_byte()
                if writing_screen:
                    screen = [value] * MAX_SCREEN_OFFSET
                else:
                    color = [value] * MAX_SCREEN_OFFSET
            elif op_code == self.OP_CLEAR_COLOR:
                value = read_next_byte()
                color = [value] * MAX_SCREEN_OFFSET
            elif op_code in (
                self.OP_SET_BACKGROUND,
                self.OP_SET_BORDER,
                self.OP_SET_CHARSET,
            ):
                offset += 1
            elif op_code == self.OP_SET_COLOR_MODE:
                writing_screen = False
            elif op_code == self.OP_SET_SCREEN_MODE:
                writing_screen = True
            else:
                op_name = "unknown"
                if op_code in self.OP_CODES:
                    op_name = self.OP_CODES[op_code]
                raise ValueError(f"Unhandled op code {op_code}, {op_name}")

            return False  # Continue the main loop

        block_ptr = None
        writing_screen = True

        while True:
            if process_state_machine():
                break

        return screen, color, offset

    def get_screen_offsets(self, screens, anim_stream):
        offset = 0
        screen = [0] * MAX_SCREEN_OFFSET
        color = [0] * MAX_SCREEN_OFFSET
        offsets = []
        for _idx in range(len(screens)):
            offsets.append(offset)
            screen, color, offset = self.unpack(anim_stream, offset, screen, color)

        return offsets

    @staticmethod
    def write(buffer: StringIO, text: str, indent=1):
        buffer.write("\t" * indent)
        buffer.write(text)
        buffer.write("\n")

    def first_offset(self, block: Block):
        offs = self.offsets(block)
        if len(offs) > 0:
            return self.offsets(block)[0]
        else:
            return 0

    def write_player(
        self,
        screens: List[PetsciiScreen],
        charsets: List[List[PetsciiChar]],
        output_folder: str,
        anim_slowdown_frames: int,
        use_color: bool = False,
        optimize_player: bool = True,
    ):
        template_dir = utils.get_resource_path(
            os.path.join("src", "resources", "test-program")
        )
        if self.OVERRIDE_TEMPLATE_DIR:
            template_dir = os.path.abspath(self.OVERRIDE_TEMPLATE_DIR)
            print(Fore.GREEN + f"Reading templates and data from {template_dir}")

        macro_blocks = self.get_macro_blocks()

        # write a tester for the player
        charset_files = []
        for idx, _ in enumerate(charsets):
            offset = 0x5000 + (idx * 0x800)
            charset_files.append((f"charset_{idx}.bin", hex(offset)[2:]))

        charset = charsets[0]
        blank_char_index = 0
        for idx, char in enumerate(charset):
            if char.is_blank():
                blank_char_index = idx
                break

        print(
            f"Animation has {len(self.USED_BLOCKS)} used blocks out of {len(self.ALL_BLOCKS)}"
        )

        test_music = None
        test_music_filename = None
        if os.path.exists(os.path.join(template_dir, self.MUSIC_FILE_NAME)):
            test_music = os.path.join(template_dir, self.MUSIC_FILE_NAME)
        elif os.path.exists(self.MUSIC_FILE_NAME):
            test_music = self.MUSIC_FILE_NAME
        else:
            print(
                Fore.YELLOW
                + f"WARNING: Unable to find music data file {self.MUSIC_FILE_NAME}"
            )

        if test_music:
            test_music_filename = os.path.basename(test_music)

        test_music_address = "$1000"
        if test_music_filename.endswith(".prg"):
            test_music_address = "$1000-2"

        last_used_op_code = 0
        for k, v in self.OP_CODES.items():
            if v not in self.OPS_USED:
                self.OP_CODES[k] = "player_op_error"
            if self.OP_CODES[k] != "player_op_error":
                last_used_op_code = k

        bit_mask = []
        for i in range(8):
            bit_mask.append(1 << i)

        offset_from_macro_all = {}

        for macro_block in self.get_macro_blocks():
            offsets_from_macro = []
            first_offset = None
            blocks = self.get_blocks(macro_block)
            for block in blocks:
                offsets = self.offsets(block)
                for offset in offsets:
                    if first_offset is None:
                        first_offset = offset
                    offsets_from_macro.append(offset - first_offset)
            offset_from_macro_all[len(blocks)] = offsets_from_macro

        if (
            "player_op_fill_rle_fullscreen" in self.OPS_USED
            and len(self.USED_RLE_COUNTS) > 0
        ):
            sorted_rle_counts = dict(
                sorted(
                    self.USED_RLE_COUNTS.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            )
            top_10 = list(islice(sorted_rle_counts.items(), 10))
            if top_10[0][0] == 1:
                print(
                    Fore.YELLOW
                    + "WARING: Using RLE to pack full screen but its going to perform poorly with this data"
                )

        namespace = {
            "charset_files": charset_files,
            "blank_char_index": blank_char_index,
            "hex": hex,
            "len": len,
            "max": max,
            "anim_start_address": self.ANIM_START_ADDRESS,
            "effect_start_address": self.EFFECT_START_ADDRESS,
            "fill_color_with_effect": self.FILL_COLOR_WITH_EFFECT,
            "color_anim_slowdown": self.COLOR_ANIM_SLOWDOWN,
            "enumerate": enumerate,
            "x_step": self.X_STEP,
            "y_step": self.Y_STEP,
            "block_size_x": self.BLOCK_SIZE.x,
            "block_size_y": self.BLOCK_SIZE.y,
            "count_macro_blocks": len(macro_blocks),
            "all_blocks": self.ALL_BLOCKS,
            "macro_blocks": self.get_macro_blocks(),
            "all_ops": self.OP_CODES,
            "get_blocks": self.get_blocks,
            "get_offsets": self.offsets,
            "first_offset": self.first_offset,
            "use_color": use_color,
            "block_offsets": self.offsets(self.ALL_BLOCKS[0]),
            "block_offsets_sizes": self.BLOCK_OFFSETS_SIZES,
            "used_blocks": self.USED_BLOCKS,
            "remove_unused_blocks": optimize_player,
            "FILL_RLE_TEMPLATE_HELPER": self.FILL_RLE_TEMPLATE_HELPER,
            "PLAYER_RLE_END_MARKER": RLE_END_MARKER,
            "TEST_SLOWDOWN": anim_slowdown_frames,
            "test_music": test_music_filename,
            "test_music_address": test_music_address,
            "ops_in_use": self.OPS_USED,
            "bit_mask": bit_mask,
            "offset_from_macro": offset_from_macro_all,
            "rle_decode_needed": self.RLE_DECODE_NEEDED,
            "only_per_row_mode": self.ONLY_PER_ROW_MODE,
            "last_used_op_code": last_used_op_code,
            "scroll_copy": self.SCROLL_WHEN_COPY_SCREEN,
            "scroll_direction": self.SCROLL_DIRECTION,
            "scroll_disable_repeat": self.SCROLL_DISABLE_REPEAT,
            "used_area": find_areas_with_content(screens),
            "fill_color_palette": self.FILL_COLOR_PALETTE,
        }

        env = Environment(
            loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True
        )
        test_code_template = env.get_template("player_test_setup.asm")
        player_template = env.get_template("player.asm")

        player_file = f"{output_folder}/player.asm"
        player = player_template.render(namespace)
        with open(player_file, "w") as fp:
            fp.write(player)

        output = test_code_template.render(namespace)
        with open(f"{output_folder}/{self.PRG_FILE_NAME}.asm", "w") as f:
            f.write(output)

        if self.FILL_COLOR_WITH_EFFECT:
            fill_color_blocks = [
                self.FILL_COLOR_BLOCKS[key]
                for key in sorted(self.FILL_COLOR_BLOCKS.keys())
            ]

            template = env.get_template("fill_color_template.asm")
            namespace = {
                "enumerate": enumerate,
                "len": len,
                "hex": hex,
                "fill_color_blocks": fill_color_blocks,
                "fill_color_generated_code": color_data_utils.generate_color_fill_code(
                    fill_color_blocks,
                    self.FILL_COLOR_MIN_SEQ_LEN,
                    self.FILL_COLOR_MAX_SEQ_LEN,
                ),
                "fill_color_palette": self.FILL_COLOR_PALETTE,
            }

            fill_color_file = f"{output_folder}/fill_color.asm"
            with open(fill_color_file, "w") as fp:
                fp.write(template.render(namespace))

        if test_music:
            utils.copy_file(test_music, f"{output_folder}")
