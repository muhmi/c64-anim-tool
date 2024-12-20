import json
import os
import re
import sys
from functools import lru_cache
from heapq import heappop, heappush
from io import StringIO
from itertools import combinations
from multiprocessing import Pool, cpu_count
from typing import List, Set, Tuple

import numpy as np
from bitarray import bitarray
from numba import jit
from PIL import Image, ImageDraw, ImageSequence
from utils import (create_folder_if_not_exists, rgb_to_idx, save_images_as_gif,
                   vicPalette, write_bin)


class char_use_location:
    def __init__(self, screen_index, row, col):
        self.screen_index = screen_index
        self.row = row
        self.col = col

    def __eq__(self, other):
        if isinstance(other, char_use_location):
            return (
                self.screen_index == other.screen_index
                and self.row == other.row
                and self.col == other.col
            )
        return False

    def __hash__(self):
        return hash((self.screen_index, self.row, self.col))

    def __repr__(self):
        return f"char_use_location(screen_index={self.screen_index}, row={self.row}, col={self.col})"


@jit(nopython=True)
def byte_hamming_distance(byte1, byte2):
    xor = byte1 ^ byte2
    count = 0
    while xor:
        count += xor & 1
        xor >>= 1
    return count


@jit(nopython=True)
def _jitted_char_distance(char1_data, char2_data):
    distance = 0
    for row1, row2 in zip(char1_data, char2_data):
        distance += byte_hamming_distance(row1, row2)
    return distance


# Keep the same interface but use the jitted function internally
@lru_cache(maxsize=20000)  # Replace the global dict with lru_cache
def char_hamming_distance(char1, char2):
    # Convert character data to numpy arrays for Numba
    data1 = np.array(char1.data, dtype=np.uint8)
    data2 = np.array(char2.data, dtype=np.uint8)
    return _jitted_char_distance(data1, data2)


class petscii_char:
    BLANK_DATA = bitarray("0" * 64)  # 8x8 = 64 bits, blank character
    FULL_DATA = bitarray("1" * 64)  # Full 8x8 character (all bits set)
    # Super ugly hack to support charset compression :D Look away :D
    GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK = None

    def __init__(self, data=None):
        self.data = data if data is not None else bitarray("0" * 64)
        self.used_in_screen = set()
        self._hash = None
        self._blank = None
        self.usage = set()

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self.data.tobytes())  # Use bytes for hashing
        return self._hash

    def __eq__(self, other):
        if isinstance(other, petscii_char):
            equal = self.data == other.data
            if petscii_char.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK is None:
                return equal
            else:
                if not equal:
                    equal = (
                        self.distance(other)
                        <= petscii_char.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK
                    )
                return equal
        return False

    def __repr__(self):
        return f"petscii_char(data={self.data})"

    def is_blank(self):
        if self._blank is None:
            self._blank = self.data == petscii_char.BLANK_DATA
        return self._blank

    def add_usage(self, screen_index, row, col):
        self.used_in_screen.add(screen_index)
        self.usage.add(char_use_location(screen_index, row, col))

    def use_count(self):
        return len(self.usage)

    def display(self):
        # Simplified display, directly index the bitarray
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
    target_char: petscii_char, charset: list[petscii_char]
) -> tuple[petscii_char, int]:
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


def write_charset(charset: List[petscii_char], file_name: str):
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
            char = petscii_char(byte_data)
            petscii_chars.append(char)

    return petscii_chars


@jit(nopython=True)
def _jitted_calculate_distances(
    char_data: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    n_chars = len(char_data)
    n_pairs = (n_chars * (n_chars - 1)) // 2

    # Pre-allocate arrays for distances and indices
    distances = np.zeros(n_pairs, dtype=np.float32)
    indices_i = np.zeros(n_pairs, dtype=np.int32)
    indices_j = np.zeros(n_pairs, dtype=np.int32)

    idx = 0
    for i in range(n_chars):
        for j in range(i + 1, n_chars):
            # Calculate distance between chars[i] and chars[j]
            dist = 0
            for row1, row2 in zip(char_data[i], char_data[j]):
                xor = row1 ^ row2
                while xor:
                    dist += xor & 1
                    xor >>= 1

            distances[idx] = dist
            indices_i[idx] = i
            indices_j[idx] = j
            idx += 1

    return distances, indices_i, indices_j


@jit(nopython=True)
def _jitted_find_min_valid(
    distances: np.ndarray,
    indices_i: np.ndarray,
    indices_j: np.ndarray,
    removed: np.ndarray,
) -> Tuple[int, int, int]:
    min_dist = np.inf
    min_idx = -1

    for idx in range(len(distances)):
        i, j = indices_i[idx], indices_j[idx]
        if not removed[i] and not removed[j] and distances[idx] < min_dist:
            min_dist = distances[idx]
            min_idx = idx

    if min_idx != -1:
        return min_idx, indices_i[min_idx], indices_j[min_idx]
    return -1, -1, -1


def reduce_charset(charset: List[petscii_char], target_size: int) -> List[petscii_char]:
    if len(charset) <= target_size:
        return charset.copy()

    # Convert characters to numpy array for JIT processing
    char_data = np.array([char.data for char in charset], dtype=np.uint8)
    current_chars = list(charset)

    # Calculate initial distances using JIT
    distances, indices_i, indices_j = _jitted_calculate_distances(char_data)

    # Keep track of removed indices - make this large enough for all potential new chars
    max_possible_chars = len(charset) * 2  # Conservative estimate
    removed = np.zeros(max_possible_chars, dtype=np.bool_)

    while len(current_chars) - np.sum(removed) > target_size:
        # Find next valid pair using JIT
        min_idx, i, j = _jitted_find_min_valid(distances, indices_i, indices_j, removed)

        if min_idx == -1:
            break

        # Merge the characters (this part stays in Python for class operations)
        char1 = current_chars[i]
        char2 = current_chars[j]

        merged_char = petscii_char(char1.data)
        merged_char.used_in_screen = char1.used_in_screen.union(char2.used_in_screen)
        merged_char.usage = char1.usage.union(char2.usage)

        # Mark indices as removed
        removed[i] = True
        removed[j] = True

        # Add new character
        new_idx = len(current_chars)
        current_chars.append(merged_char)

        # Extend arrays for new distances
        char_data = np.vstack((char_data, merged_char.data))

        # Pre-allocate arrays for new distances
        new_distances = []
        new_indices_i = []
        new_indices_j = []

        # Calculate new distances to merged character
        for k in range(new_idx):
            if not removed[k]:
                dist = 0
                for row1, row2 in zip(char_data[k], char_data[new_idx]):
                    xor = row1 ^ row2
                    while xor:
                        dist += xor & 1
                        xor >>= 1
                new_distances.append(dist)
                new_indices_i.append(k)
                new_indices_j.append(new_idx)

        # Convert to numpy arrays and append
        if new_distances:  # Only append if we have new distances
            distances = np.concatenate(
                [distances, np.array(new_distances, dtype=np.float32)]
            )
            indices_i = np.concatenate(
                [indices_i, np.array(new_indices_i, dtype=np.int32)]
            )
            indices_j = np.concatenate(
                [indices_j, np.array(new_indices_j, dtype=np.int32)]
            )

    # Create final result excluding removed characters
    result = [char for i, char in enumerate(current_chars) if not removed[i]]
    return result[:target_size]


def get_rgb_from_palette(image, x, y):
    index = image.getpixel((x, y))
    return image.palette.palette[index * 3 : index * 3 + 3]


def get_pixel_rgb(image, x, y):
    if image.mode == "P":
        return get_rgb_from_palette(image, x, y)
    else:
        return image.getpixel((x, y))


class petscii_screen:

    def __init__(self, screen_index, background_color=None, border_color=None):
        self.screen_index = screen_index
        self.screen_codes = [0] * 1000
        self.color_data = [0] * 1000
        self.background_color = background_color
        self.border_color = border_color
        self.charset = []

    def read(self, image, default_charset=None, inverse=False, cleanup=1):

        bw_image = image.convert("L").point(lambda x: 0 if x <= 1 else 255, "1")
        width, height = bw_image.size

        if default_charset is None:
            self.charset = []
            self.charset.append(petscii_char(petscii_char.BLANK_DATA))
            self.charset.append(petscii_char(petscii_char.FULL_DATA))
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
                        char_bits = petscii_char.FULL_DATA
                    else:
                        char_bits = petscii_char.BLANK_DATA

                char = petscii_char(char_bits)
                char_index = 0
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

                # Store as integer, no need for bitarray
                if offset < 1000:
                    self.screen_codes[offset] = char_index

                    if self.background_color is None:
                        # Assume it's BW if no background color is given
                        self.color_data[offset] = 1 if char_index > 0 else 0
                    else:
                        # Background color specified, find any other color than
                        # it
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
        color_bg = 0
        color_border = 0

        if self.background_color:
            color_bg = self.background_color

        if self.border_color:
            color_border = self.border_color

        def write_ints_to_buffer(ints, buffer, group_size=40):
            for i in range(0, len(ints), group_size):
                group = ints[i : i + group_size]
                line = ",".join(str(num) for num in group)
                buffer.write(line + ",\n")

        buffer = StringIO()
        buffer.write(
            f"unsigned char frame{
                self.screen_index:04d}[]={{// border,bg,chars,colors\n"
        )
        buffer.write(f"{color_bg}, {color_border},\n")
        write_ints_to_buffer(self.screen_codes, buffer)
        write_ints_to_buffer(self.color_data, buffer)
        buffer.write("};\n")

        return buffer.getvalue()

    def remap_characters(self, new_charset: List[petscii_char], allow_error=False):
        def find_closest_char(target_char, char_list):
            if not char_list:
                return None

            closest_char = min(char_list, key=lambda x: target_char.distance(x))
            return closest_char

        new_screen = []
        for code in self.screen_codes:
            char = self.charset[code]
            if allow_error == False:
                new_index = new_charset.index(char)
                new_screen.append(new_index)
            else:
                if char in new_charset:
                    new_index = new_charset.index(char)
                else:
                    closest_char = find_closest_char(char, new_charset)
                    new_index = new_charset.index(closest_char)
                new_screen.append(new_index)

        self.screen_codes = new_screen
        self.charset = new_charset

    def remap_chars(self, char_mapping: dict):
        # Create new charset from the unique values in char_mapping
        new_charset = list(set(char_mapping.values()))

        # Create a mapping from old charset indices to new charset indices
        old_to_new_index = {
            self.charset.index(old): new_charset.index(new)
            for old, new in char_mapping.items()
            if old in self.charset
        }

        # Remap character indices in screen_codes
        self.screen_codes = [
            old_to_new_index.get(code, code) for code in self.screen_codes
        ]

        # Update the charset
        self.charset = new_charset

    def render(self, char_size=8, border=0):
        screen_width = 40 * char_size
        screen_height = 25 * char_size
        img = Image.new(
            "RGB",
            (screen_width + 2 * border, screen_height + 2 * border),
            color=vicPalette[0],
        )
        draw = ImageDraw.Draw(img)

        for row in range(25):
            for col in range(40):
                offset = row * 40 + col
                char_index = self.screen_codes[offset]
                char = self.charset[char_index]
                bg_color = vicPalette[0]  # Assuming black background
                fg_color = vicPalette[self.color_data[offset]]

                char_img = char.render(char_size)
                # Ensure the image is in '1' (binary) mode
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
        new_screen = petscii_screen(
            self.screen_index, self.background_color, self.border_color
        )

        # Copy screen_codes and color_data
        new_screen.screen_codes = self.screen_codes.copy()
        new_screen.color_data = self.color_data.copy()

        # Deep copy of charset
        new_screen.charset = [petscii_char(char.data.copy()) for char in self.charset]

        # Copy usage information for each character
        for old_char, new_char in zip(self.charset, new_screen.charset):
            new_char.used_in_screen = old_char.used_in_screen.copy()
            new_char.usage = {
                char_use_location(loc.screen_index, loc.row, loc.col)
                for loc in old_char.usage
            }

        return new_screen


def save_debug_screens(screens, ouput_filename, duration=200, loop=0):
    images = []
    for screen in screens:
        images.append(screen.render())
    save_images_as_gif(images, ouput_filename, duration, loop)


def read_petscii(file_path: str, charset: List[petscii_char]) -> List[petscii_screen]:

    with open(file_path, "r") as file:
        content = file.read()

    # Regular expression to match frame data
    frame_pattern = re.compile(r"unsigned char frame(\w+)\[\]=\{(.*?)\};", re.DOTALL)
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

        screen = petscii_screen(int(frame_id, 16))
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
        data = json.loads(file.read())
    return data


def ints_to_bitarray(list: List[int]):
    if len(list) != 8:
        raise ValueError("The input list must contain exactly 8 integers")

    ba = bitarray(endian="big")
    for num in list:
        # Ensure each number is within the 0-255 range (8 bits)
        if not 0 <= num <= 255:
            raise ValueError(f"Each integer must be between 0 and 255, got {num}")

        # Convert the integer to its 8-bit representation and extend the
        # bitarray
        ba.extend(f"{num:08b}")

    return ba


# :{"name":"shutdown-charset","font":{"bits":[


def read_charset_from_petmate(customFont):
    name = customFont["name"]
    bits = customFont["font"]["bits"]
    print(f"Reading custom font {name}, bits = {len(bits)}")

    charset = []
    for i in range(0, len(bits), 8):
        char_data = bits[i : i + 8]
        byte_data = ints_to_bitarray(char_data)
        char = petscii_char(byte_data)
        charset.append(char)

    if len(charset) > 256:
        raise ValueError(f"Charset is too big {len(charset)}")

    print(f"Custom font {name}, has {len(charset)} characters")

    return charset


def read_petmate(file_path: str) -> List[petscii_screen]:

    script_dir = os.path.dirname(__file__)

    petmate = read_json(file_path)

    charsets = {}
    charsets["upper"] = read_charset(f"{script_dir}/data/c64_charset.bin")
    for name, customFont in petmate["customFonts"].items():
        charsets[name] = read_charset_from_petmate(customFont)

    charset = charsets["upper"]

    screens = []
    for idx, frame in enumerate(petmate["framebufs"]):

        charset_name = frame["charset"]
        border = int(frame["borderColor"])
        bg = int(frame["backgroundColor"])

        print(
            f"Frame {idx}, charset {charset_name}, backgroundColor {bg}, borderColor {border}, data {
                len(
                    frame['framebuf'])}"
        )

        if charset_name in charsets:
            charset = charsets[charset_name]
        else:
            print(f"Cannot find custom charset with name {charset_name}")
            sys.exit(1)

        screen = petscii_screen(idx)
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
) -> List["petscii_screen"]:
    if filename.endswith(".c"):
        return read_petscii(filename, charset)
    if filename.endswith(".petmate"):
        return read_petmate(filename)
    else:
        screens = []
        img = Image.open(filename)
        for idx, frame in enumerate(ImageSequence.Iterator(img)):
            screen = petscii_screen(idx, background_color, border_color)
            screen.read(frame, charset, inverse, cleanup)
            screens.append(screen)
        return screens


def compress_charsets(
    screens: List["petscii_screen"],
    charsets: List[List["petscii_char"]],
    max_charsets: int,
    debug_output_folder=None,
    start_threshold=1,
) -> Tuple[List["petscii_screen"], List["petscii_char"], float]:

    petscii_char.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK = start_threshold
    found_threshold = petscii_char.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK

    new_screens = [] + screens
    new_charsets = [] + charsets

    while len(new_charsets) > max_charsets:
        print(
            f"  Trying to compress_charsets, now at threshold={found_threshold}, charsets={
                len(new_charsets)}"
        )
        new_screens, new_charsets = merge_charsets(
            screens,
            debug_output_folder=debug_output_folder,
            debug_prefix="compressed_changes_",
        )
        petscii_char.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK += 1
        found_threshold = petscii_char.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK

    petscii_char.GLOBAL_CHAR_EQUALITY_THRESHOLD_HACK = None

    return new_screens, new_charsets, found_threshold


def merge_charsets(screens, debug_output_folder=None, debug_prefix="changes_"):
    all_characters = []

    total_chars = 0
    for idx, screen in enumerate(screens):
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

    chars_used_in_all = []
    for char in all_characters:
        if len(char.used_in_screen) == len(screens):
            chars_used_in_all.append(char)

    print(
        f"  {
            len(screens)} screens contain {
            len(all_characters)} unique characters of total {total_chars}"
    )
    print(
        f"  There are {len(chars_used_in_all)} characters that are shared in all screens"
    )

    seed_charset = [] + chars_used_in_all

    sorted_chars = sorted(
        all_characters, key=lambda char: len(char.usage), reverse=True
    )
    for char in sorted_chars:
        if char not in seed_charset:
            seed_charset.append(char)
        if len(seed_charset) > 31:
            break

    dbg_character_changes = []
    dbg_screen_code_changes = []
    dbg_screen_color_changes = []

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
                petscii_char(petscii_char.BLANK_DATA),
                petscii_char(petscii_char.FULL_DATA),
            ] + reduce_charset(charset, 253)
        if idx > 0:
            diff = set(screens[idx - 1].charset) - set(screen.charset)
            print(
                f"  {
                    len(diff)} charset changes required from screen {
                    idx -
                    1} to {idx}"
            )

            # Write out debug image with characters that are not found in prev frames
            # charset colorized
            debug_screen = screen.copy()
            debug_screen.color_data = [1] * 1000
            for char in screen.charset:
                if char not in screens[idx - 1].charset:
                    for usage in char.usage:
                        debug_screen.color_data[usage.row * 40 + usage.col] = 2
            dbg_character_changes.append(debug_screen)

            # Write out debug image with petscii code changes highlighted
            debug_screen = screen.copy()
            for offset, char in enumerate(screen.screen_codes):
                if screens[idx - 1].screen_codes[offset] != char:
                    debug_screen.color_data[offset] = 2
                else:
                    debug_screen.color_data[offset] = 1
            dbg_screen_code_changes.append(debug_screen)

            # Write out debug image with color changes highlighted
            debug_screen = screen.copy()
            for offset, col in enumerate(screen.color_data):
                if screens[idx - 1].color_data[offset] != col:
                    debug_screen.color_data[offset] = 2
                    debug_screen.screen_codes[offset] = 1
                else:
                    debug_screen.color_data[offset] = 1
            dbg_screen_color_changes.append(debug_screen)

        screen.remap_characters(charset, allow_error=True)

    charsets.append(charset)

    print(f"Merged the screens to {len(charsets)} charsets")

    if debug_output_folder is not None:

        create_folder_if_not_exists(f"{debug_output_folder}/debug")

        with open(f"{debug_output_folder}/petscii.c", "wb") as pets:
            for screen in screens:
                pets.write(screen.to_petscii_editor_data().encode("utf-8"))

        save_debug_screens(
            screens,
            f"{
                debug_output_folder}/debug/{debug_prefix}screens.gif",
            200,
        )

        save_debug_screens(
            dbg_character_changes,
            f"{
                debug_output_folder}/debug/{debug_prefix}charset.gif",
            200,
        )

        save_debug_screens(
            dbg_screen_code_changes,
            f"{
                debug_output_folder}/debug/{debug_prefix}screen.gif",
            200,
        )

        save_debug_screens(
            dbg_screen_color_changes,
            f"{
                debug_output_folder}/debug/{debug_prefix}color.gif",
            200,
        )

    return screens, charsets


def merge_charsets_compress(screens, max_charsets=4):
    if max_charsets == 1:
        all_chars = []
        for idx, screen in enumerate(screens):
            all_chars.extend(screen.charset)

        print(f"Crunching all {len(all_chars)} characters to one charset")
        charset = [
            petscii_char(petscii_char.BLANK_DATA),
            petscii_char(petscii_char.FULL_DATA),
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
