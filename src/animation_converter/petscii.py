import json
import os
import re
import sys
from functools import lru_cache
from io import StringIO
from typing import Dict, List, Tuple

from bitarray import bitarray
from colorama import Fore
from PIL import Image, ImageDraw, ImageSequence
from utils import (create_folder_if_not_exists, rgb_to_idx, save_images_as_gif,
                   vicPalette, write_bin)


class CharUseLocation:
    def __init__(self, screen_index: int, row: int, col: int):
        self.screen_index = screen_index
        self.row = row
        self.col = col

    def __eq__(self, other):
        if isinstance(other, CharUseLocation):
            return (
                self.screen_index == other.screen_index
                and self.row == other.row
                and self.col == other.col
            )
        return False

    def __hash__(self):
        return self.screen_index * 10000 + self.row * 100 + self.col


def byte_hamming_distance(byte1: int, byte2: int) -> int:
    xor = byte1 ^ byte2
    count = 0
    while xor:
        count += xor & 1
        xor >>= 1
    return count


def char_distance_simple(char1_data: bytes, char2_data: bytes) -> int:
    distance = 0
    for row1, row2 in zip(char1_data, char2_data):
        distance += byte_hamming_distance(row1, row2)
    return distance


@lru_cache(maxsize=20000)
def char_hamming_distance(char1, char2):
    data1 = char1.data.tobytes()
    data2 = char2.data.tobytes()
    return char_distance_simple(data1, data2)


class PetsciiChar:
    BLANK_DATA = bitarray("0" * 64)  # 8x8 = 64 bits, blank character
    FULL_DATA = bitarray("1" * 64)  # Full 8x8 character (all bits set)
    # Hack to support charset compression
    GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK = None

    def __init__(self, data=None):
        self.data = data if data is not None else bitarray("0" * 64)
        self.used_in_screen = set()
        self._hash = None
        self._blank = None
        self.usage = set()

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self.data.tobytes())
        return self._hash

    def __eq__(self, other):
        if isinstance(other, PetsciiChar):
            equal = self.data == other.data
            if PetsciiChar.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK is None:
                return equal
            else:
                if not equal:
                    equal = (
                        self.distance(other)
                        <= PetsciiChar.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK
                    )
                return equal
        return False

    def is_blank(self):
        if self._blank is None:
            self._blank = self.data == PetsciiChar.BLANK_DATA
        return self._blank

    def add_usage(self, screen_index, row, col):
        self.used_in_screen.add(screen_index)
        self.usage.add(CharUseLocation(screen_index, row, col))

    def use_count(self):
        return len(self.usage)

    def display(self):
        for i in range(8):
            line = "".join("#" if self.data[i * 8 + j] else "." for j in range(8))
            print(line)

    def render(self, size=8):
        img = Image.new("1", (size, size), 0)
        draw = ImageDraw.Draw(img)
        for i in range(size):
            for j in range(size):
                if self.data[i * 8 + j]:
                    draw.point((j, i), 1)
        return img

    def distance(self, other_char):
        return char_hamming_distance(self, other_char)


def find_closest_char(
    target_char: PetsciiChar, charset: List[PetsciiChar]
) -> Tuple[PetsciiChar, int]:
    if not charset:
        raise ValueError("charset cannot be empty")

    closest_char = None
    min_distance = float("inf")

    for char in charset:
        dist = target_char.distance(char)
        if dist < min_distance:
            min_distance = dist
            closest_char = char

    return closest_char, min_distance


def write_charset(charset: List[PetsciiChar], file_name: str):
    binary = []
    for char in charset:
        for b in char.data.tobytes():
            binary.append(b)
    write_bin(file_name, binary)


def read_charset(file_path, skipFirstBytes=False):
    petscii_chars = []

    with open(file_path, "rb") as file:
        if skipFirstBytes:
            file.read(2)

        while True:
            char_data = file.read(8)
            if len(char_data) < 8:
                break

            byte_data = bitarray()
            byte_data.frombytes(char_data)
            char = PetsciiChar(byte_data)
            petscii_chars.append(char)

    return petscii_chars


def reduce_charset_greedy(
    charset: List[PetsciiChar], target_size: int
) -> List[PetsciiChar]:
    if len(charset) <= target_size:
        return charset.copy()

    # Sort by usage count (keep most used characters)
    sorted_chars = sorted(charset, key=lambda char: char.use_count(), reverse=True)
    return sorted_chars[:target_size]


def reduce_charset_by_similarity(
    charset: List[PetsciiChar], target_size: int
) -> List[PetsciiChar]:
    if len(charset) <= target_size:
        return charset.copy()

    current_chars = list(charset)
    char_data_bytes = [char.data.tobytes() for char in charset]

    while len(current_chars) > target_size:
        min_distance = float("inf")
        merge_i, merge_j = 0, 1

        # Find closest pair
        for i in range(len(current_chars)):
            for j in range(i + 1, len(current_chars)):
                dist = char_distance_simple(char_data_bytes[i], char_data_bytes[j])
                if dist < min_distance:
                    min_distance = dist
                    merge_i, merge_j = i, j

        # Merge characters
        char1 = current_chars[merge_i]
        char2 = current_chars[merge_j]

        merged_char = PetsciiChar(char1.data.copy())
        merged_char.used_in_screen = char1.used_in_screen.union(char2.used_in_screen)
        merged_char.usage = char1.usage.union(char2.usage)

        # Remove the merged characters and add the new one
        if merge_j > merge_i:
            current_chars.pop(merge_j)
            char_data_bytes.pop(merge_j)
            current_chars.pop(merge_i)
            char_data_bytes.pop(merge_i)
        else:
            current_chars.pop(merge_i)
            char_data_bytes.pop(merge_i)
            current_chars.pop(merge_j)
            char_data_bytes.pop(merge_j)

        current_chars.append(merged_char)
        char_data_bytes.append(merged_char.data.tobytes())

    return current_chars


def reduce_charset(charset: List[PetsciiChar], target_size: int) -> List[PetsciiChar]:
    # For small reductions, use greedy (much faster)
    if len(charset) - target_size < 50:
        return reduce_charset_greedy(charset, target_size)
    else:
        # For large reductions, use similarity-based approach
        return reduce_charset_by_similarity(charset, target_size)


def get_rgb_from_palette(image, x, y):
    index = image.getpixel((x, y))
    return image.palette.palette[index * 3 : index * 3 + 3]


def get_pixel_rgb(image, x, y):
    if image.mode == "P":
        return get_rgb_from_palette(image, x, y)
    else:
        return image.getpixel((x, y))


class PetsciiScreen:
    def __init__(self, screen_index, background_color=None, border_color=None):
        self.screen_index = screen_index
        self.screen_codes = [0] * 1000
        self.color_data = [0] * 1000
        self.background_color = background_color
        self.border_color = border_color
        self.charset = []

    def read(self, image, default_charset=None, inverse=False, cleanup=1):
        bw_image = image.convert("L").point(lambda p: 0 if p <= 1 else 255, "1")
        width, height = bw_image.size

        if default_charset is None:
            self.charset = []
            self.charset.append(PetsciiChar(PetsciiChar.BLANK_DATA))
            self.charset.append(PetsciiChar(PetsciiChar.FULL_DATA))
        else:
            self.charset = default_charset

        for y in range(0, height, 8):
            for x in range(0, width, 8):
                row = y // 8
                col = x // 8
                offset = row * 40 + col

                # Create bitarray directly while iterating over the 8x8 block
                char_bits = bitarray()
                num_pixels = 0
                for i in range(8):
                    for j in range(8):
                        px = x + j
                        py = y + i
                        if (
                            px < width
                            and py < height
                            and bw_image.getpixel((px, py)) != 0
                        ):
                            num_pixels = num_pixels + 1
                            if inverse:
                                char_bits.append(0)
                            else:
                                char_bits.append(1)
                        else:
                            if inverse:
                                char_bits.append(1)
                            else:
                                char_bits.append(0)

                if num_pixels <= cleanup:
                    if inverse:
                        char_bits = PetsciiChar.FULL_DATA
                    else:
                        char_bits = PetsciiChar.BLANK_DATA

                char = PetsciiChar(char_bits)
                if char in self.charset:
                    # Char in charset, add usage
                    char_index = self.charset.index(char)
                    char = self.charset[char_index]
                    char.add_usage(self.screen_index, row, col)
                else:
                    if default_charset is not None:
                        # Find closest char in default charset
                        char, _ = find_closest_char(char, self.charset)
                        char_index = self.charset.index(char)
                        char.add_usage(self.screen_index, row, col)
                    else:
                        # Add new char
                        char.add_usage(self.screen_index, row, col)
                        char_index = len(self.charset)
                        self.charset.append(char)

                # Store as integer
                if offset < 1000:
                    self.screen_codes[offset] = char_index

                    if self.background_color is None:
                        # Assume it's BW if no background color is given
                        self.color_data[offset] = 1 if char_index > 0 else 0
                    else:
                        # Background color specified, find any other color
                        if char.is_blank():
                            self.color_data[offset] = 0
                        else:
                            foreground_color = None
                            for cy in range(8):
                                if foreground_color is not None:
                                    break
                                for cx in range(8):
                                    color = rgb_to_idx(
                                        get_pixel_rgb(image, x + cx, y + cy)
                                    )
                                    if color != self.background_color:
                                        foreground_color = color
                                        break
                            if foreground_color is None:
                                foreground_color = self.background_color
                            self.color_data[offset] = foreground_color

    def to_petscii_editor_data(self) -> str:
        color_bg = self.background_color or 0
        color_border = self.border_color or 0

        def write_ints_to_buffer(ints, target_buffer, group_size=40):
            for i in range(0, len(ints), group_size):
                group = ints[i : i + group_size]
                line = ",".join(str(num) for num in group)
                target_buffer.write(line + ",\n")

        buffer = StringIO()
        buffer.write(
            f"unsigned char frame{self.screen_index:04d}[]={{// border,bg,chars,colors\n"
        )
        buffer.write(f"{color_bg}, {color_border},\n")
        write_ints_to_buffer(self.screen_codes, buffer)
        write_ints_to_buffer(self.color_data, buffer)
        buffer.write("};\n")

        return buffer.getvalue()

    def remap_characters(self, new_charset: List[PetsciiChar], allow_error=False):
        new_screen = []
        for code in self.screen_codes:
            char = self.charset[code]
            if not allow_error:
                new_index = new_charset.index(char)
                new_screen.append(new_index)
            else:
                if char in new_charset:
                    new_index = new_charset.index(char)
                else:
                    closest_char, _ = find_closest_char(char, new_charset)
                    new_index = new_charset.index(closest_char)
                new_screen.append(new_index)

        self.screen_codes = new_screen
        self.charset = new_charset

    def render(self, char_size=8, border=0):
        screen_width = 40 * char_size
        screen_height = 25 * char_size
        img = Image.new(
            "RGB",
            (screen_width + 2 * border, screen_height + 2 * border),
            color=vicPalette[0],
        )
        for row in range(25):
            for col in range(40):
                offset = row * 40 + col
                char_index = self.screen_codes[offset]
                char = self.charset[char_index]
                bg_color = vicPalette[0]  # Black background
                fg_color = vicPalette[self.color_data[offset]]

                char_img = char.render(char_size)
                char_img = char_img.convert("1")

                # Create colored version of the character
                colored_char = Image.new("RGB", char_img.size, bg_color)
                draw_char = ImageDraw.Draw(colored_char)
                draw_char.bitmap((0, 0), char_img, fill=fg_color)

                x = col * char_size + border
                y = row * char_size + border
                img.paste(colored_char, (x, y))

        return img

    def charset_size(self):
        return len(self.charset)

    def copy(self):
        new_screen = PetsciiScreen(
            self.screen_index, self.background_color, self.border_color
        )

        # Copy screen_codes and color_data
        new_screen.screen_codes = self.screen_codes.copy()
        new_screen.color_data = self.color_data.copy()

        # Deep copy of charset
        new_screen.charset = [PetsciiChar(char.data.copy()) for char in self.charset]

        # Copy usage information for each character
        for old_char, new_char in zip(self.charset, new_screen.charset):
            new_char.used_in_screen = old_char.used_in_screen.copy()
            new_char.usage = {
                CharUseLocation(loc.screen_index, loc.row, loc.col)
                for loc in old_char.usage
            }

        return new_screen


def save_debug_screens(screens, output_filename, duration=200, loop=0):
    images = []
    for screen in screens:
        images.append(screen.render())
    save_images_as_gif(images, output_filename, duration, loop)


def read_petscii(file_path: str, charset: List[PetsciiChar]) -> List[PetsciiScreen]:
    with open(file_path, "r") as file:
        content = file.read()

    # Regular expression to match frame data
    frame_pattern = re.compile(r"unsigned char frame(\w+)\[]=\{(.*?)};", re.DOTALL)
    frames = frame_pattern.findall(content)

    screens = []
    for frame_id, frame_data in frames:
        # Extract border and background colors
        lines = frame_data.strip().split("\n")
        border, bg = map(int, lines[1].strip().rstrip(",").split(","))

        # Extract character and color data
        data = [
            int(x)
            for line in lines[2:]
            for x in line.strip().rstrip(",").split(",")
            if x.strip()
        ]

        screen = PetsciiScreen(int(frame_id, 16))
        screen.charset = charset
        screen.border_color = border
        screen.background_color = bg

        # Fill screen_codes and color_data
        screen.screen_codes = data[:1000]
        screen.color_data = data[1000:2000]

        if charset is not None:
            # Update petscii_char usage
            for row in range(25):
                for col in range(40):
                    index = row * 40 + col
                    char_index = screen.screen_codes[index]
                    if char_index < len(charset):
                        charset[char_index].add_usage(screen.screen_index, row, col)

        screens.append(screen)

    return screens


def read_json(file_path: str):
    with open(file_path, "r") as file:
        return json.load(file)


def ints_to_bitarray(ints: List[int]):
    if len(ints) != 8:
        raise ValueError("The input list must contain exactly 8 integers")

    ba = bitarray(endian="big")
    for num in ints:
        if not 0 <= num <= 255:
            raise ValueError(f"Each integer must be between 0 and 255, got {num}")
        ba.extend(f"{num:08b}")

    return ba


def read_charset_from_petmate(custom_font):
    name = custom_font["name"]
    bits = custom_font["font"]["bits"]
    print(f"Reading custom font {name}, bits = {len(bits)}")

    charset = []
    for i in range(0, len(bits), 8):
        char_data = bits[i : i + 8]
        byte_data = ints_to_bitarray(char_data)
        char = PetsciiChar(byte_data)
        charset.append(char)

    if len(charset) > 256:
        raise ValueError(f"Charset is too big {len(charset)}")

    print(f"Custom font {name}, has {len(charset)} characters")
    return charset


def read_petmate(file_path: str) -> List[PetsciiScreen]:
    script_dir = os.path.dirname(__file__)
    petmate = read_json(file_path)

    charsets = {"upper": read_charset(f"{script_dir}/data/c64_charset.bin")}
    for name, customFont in petmate["customFonts"].items():
        charsets[name] = read_charset_from_petmate(customFont)

    charset = charsets["upper"]

    screens = []
    for idx, frame in enumerate(petmate["framebufs"]):
        charset_name = frame["charset"]
        border = int(frame["borderColor"])
        bg = int(frame["backgroundColor"])

        print(
            f"Frame {idx}, charset {charset_name}, backgroundColor {bg}, borderColor {border}"
        )

        if charset_name in charsets:
            charset = charsets[charset_name]
        else:
            print(f"Cannot find custom charset with name {charset_name}")
            sys.exit(1)

        screen = PetsciiScreen(idx)
        screen.charset = [] + charset
        screen.border_color = border
        screen.background_color = bg

        for row, row_data in enumerate(frame["framebuf"]):
            for col, entry in enumerate(row_data):
                color = entry["color"]
                code = entry["code"]
                offset = row * 40 + col
                screen.screen_codes[offset] = code
                screen.color_data[offset] = color
        screens.append(screen)

    return screens


def read_screens(
    filename,
    charset=None,
    background_color=None,
    border_color=None,
    inverse=False,
    cleanup=1,
) -> List[PetsciiScreen]:
    if filename.endswith(".c"):
        return read_petscii(filename, charset)
    if filename.endswith(".petmate"):
        return read_petmate(filename)
    else:
        screens = []
        img = Image.open(filename)
        for idx, frame in enumerate(ImageSequence.Iterator(img)):
            screen = PetsciiScreen(idx, background_color, border_color)
            screen.read(frame, charset, inverse, cleanup)
            screens.append(screen)
        if len(screens) == 1:
            screens = [screens[0], screens[0]]
        return screens


def merge_charsets(screens, debug_output_folder=None):
    all_characters = []

    total_chars = 0
    for screen in screens:
        total_chars += len(screen.charset)
        for char in screen.charset:
            if char not in all_characters:
                all_characters.append(char)
            else:
                char_idx = all_characters.index(char)
                existing = all_characters[char_idx]
                for use in char.usage:
                    existing.used_in_screen.add(use.screen_index)
                    existing.usage.add(use)

    chars_used_in_all = [
        char for char in all_characters if len(char.used_in_screen) == len(screens)
    ]

    print(
        f"  {len(screens)} screens contain {len(all_characters)} unique characters of total {total_chars}"
    )
    print(
        f"  There are {len(chars_used_in_all)} characters that are shared in all screens"
    )

    seed_charset = [] + chars_used_in_all
    sorted_chars = sorted(all_characters, key=lambda ch: len(ch.usage), reverse=True)
    for char in sorted_chars:
        if char not in seed_charset:
            seed_charset.append(char)
        if len(seed_charset) > 31:
            break

    charset = [] + seed_charset
    charsets = []

    for idx, screen in enumerate(screens):
        new_charset = [] + charset

        for char in screen.charset:
            if char not in charset:
                new_charset.append(char)

        if len(new_charset) > 255:
            charsets.append(charset)
            charset = [] + seed_charset
            for char in screen.charset:
                if char not in charset:
                    charset.append(char)
        else:
            charset.clear()
            charset.extend(new_charset)

        if len(charset) > 255:
            charset = [
                PetsciiChar(PetsciiChar.BLANK_DATA),
                PetsciiChar(PetsciiChar.FULL_DATA),
            ] + reduce_charset(charset, 253)

        screen.remap_characters(charset, allow_error=True)

    charsets.append(charset)
    print(Fore.GREEN + f"Merged the screens to {len(charsets)} charsets")

    if debug_output_folder is not None:
        create_folder_if_not_exists(f"{debug_output_folder}/debug")
        with open(f"{debug_output_folder}/petscii.c", "wb") as pets:
            for screen in screens:
                pets.write(screen.to_petscii_editor_data().encode("utf-8"))

    return screens, charsets


def compress_charsets(
    screens: List[PetsciiScreen],
    charsets: List[List[PetsciiChar]],
    max_charsets: int,
    debug_output_folder=None,
    start_threshold=1,
) -> Tuple[List[PetsciiScreen], List[List[PetsciiChar]], float]:
    PetsciiChar.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK = start_threshold
    found_threshold = start_threshold

    new_screens = screens[:]
    new_charsets = charsets[:]

    while len(new_charsets) > max_charsets:
        print(
            f"  Trying to compress_charsets, now at threshold={found_threshold}, charsets={len(new_charsets)}"
        )
        new_screens, new_charsets = merge_charsets(new_screens, debug_output_folder)
        PetsciiChar.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK += 1
        found_threshold += 1

    PetsciiChar.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK = None
    return new_screens, new_charsets, found_threshold


def merge_charsets_compress(screens, max_charsets=4, full_charsets=False):
    if max_charsets == 1:
        all_chars = []
        for screen in screens:
            all_chars.extend(screen.charset)

        print(Fore.GREEN + f"Crunching all {len(all_chars)} characters to one charset")
        charset = [
            PetsciiChar(PetsciiChar.BLANK_DATA),
            PetsciiChar(PetsciiChar.FULL_DATA),
        ] + reduce_charset(all_chars, 253)

        for screen in screens:
            screen.remap_characters(charset, True)

        return screens, [charset]
    else:
        screens, charsets = merge_charsets(screens)
        screens, charsets, _ = compress_charsets(
            screens, charsets, max_charsets=max_charsets
        )
        return screens, charsets
