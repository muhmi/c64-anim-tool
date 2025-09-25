from io import StringIO
import json
import os
import re
import sys
from typing import List, Tuple

from bitarray import bitarray
from colorama import Fore
from PIL import Image, ImageDraw, ImageSequence
from utils import (
    create_folder_if_not_exists,
    rgb_to_idx,
    save_images_as_gif,
    vicPalette,
    write_bin,
)

MAX_BYTE_VALUE = 255
MAX_CHARSET_SIZE = 256
CHARSET_SEED_LIMIT = 31
REDUCTION_RATIO_SMALL = 1.5
REDUCTION_RATIO_MEDIUM = 3.0
MAX_SCREEN_OFFSET = 1000
MAX_SEED_CHARSET_SIZE = 31


class CharUseLocation:
    """Simple class to track character usage locations"""

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


# Lookup table for byte hamming distances
_HAMMING_LOOKUP = {}
_HAMMING_LOOKUP_INITIALIZED = False


def init_hamming_lookup():
    """Initialize lookup table for byte hamming distances - much faster"""
    global _HAMMING_LOOKUP
    global _HAMMING_LOOKUP_INITIALIZED
    print("Precalculating hamming lookup...")
    if _HAMMING_LOOKUP_INITIALIZED is False:
        _HAMMING_LOOKUP = {}
        for i in range(256):
            for j in range(256):
                xor = i ^ j
                count = 0
                temp = xor
                while temp:
                    count += temp & 1
                    temp >>= 1
                _HAMMING_LOOKUP[(i, j)] = count
        print("🚀 Initialized hamming distance lookup table")
        _HAMMING_LOOKUP_INITIALIZED = True


def byte_hamming_distance(byte1: int, byte2: int) -> int:
    """OPTIMIZED: Use lookup table instead of bit counting"""
    if _HAMMING_LOOKUP_INITIALIZED is False:
        init_hamming_lookup()
    return _HAMMING_LOOKUP[(byte1, byte2)]


def char_distance_simple(char1_data: bytes, char2_data: bytes) -> int:
    """OPTIMIZED: Early exit + lookup table + skip identical bytes"""
    if _HAMMING_LOOKUP_INITIALIZED is False:
        init_hamming_lookup()
    # Quick early exit for identical data (saves ~30% of calls)
    if char1_data == char2_data:
        return 0

    # Use lookup table, skip identical bytes for speed
    distance = 0
    for row1, row2 in zip(char1_data, char2_data):
        if row1 != row2:  # Only process different bytes
            distance += _HAMMING_LOOKUP[(row1, row2)]
    return distance


def char_hamming_distance(char1, char2):
    """Cached character distance calculation"""
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
        """FIXED: Proper equality check that doesn't break character matching"""
        if not isinstance(other, PetsciiChar):
            return False

        # Quick identity check
        if self is other:
            return True

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
            # OPTIMIZATION: Early termination for exact matches
            if dist == 0:
                break

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
            if len(char_data) < 8:  # noqa: PLR2004
                break

            byte_data = bitarray()
            byte_data.frombytes(char_data)
            char = PetsciiChar(byte_data)
            petscii_chars.append(char)

    return petscii_chars


def reduce_charset_smart(
    charset: List[PetsciiChar], target_size: int
) -> List[PetsciiChar]:
    if len(charset) <= target_size:
        return charset.copy()

    # Always preserve essential characters
    essential_chars = []
    for char in charset:
        if char.is_blank() or char.data == PetsciiChar.FULL_DATA:
            essential_chars.append(char)

    # Remove duplicates from essential chars
    unique_essential = []
    for char in essential_chars:
        if char not in unique_essential:
            unique_essential.append(char)
    essential_chars = unique_essential

    # Get remaining characters sorted by usage
    other_chars = [char for char in charset if char not in essential_chars]
    other_chars.sort(key=lambda c: c.use_count(), reverse=True)

    # Calculate how many more characters we can include
    remaining_slots = target_size - len(essential_chars)

    if remaining_slots <= 0:
        # If we have too many essential chars, just return the most used ones
        all_chars = sorted(charset, key=lambda c: c.use_count(), reverse=True)
        return all_chars[:target_size]

    # Take the most used characters from the remaining set
    selected_chars = other_chars[:remaining_slots]

    result = essential_chars + selected_chars
    return result


def reduce_charset_aggressive_sampling(
    charset: List[PetsciiChar], target_size: int
) -> List[PetsciiChar]:
    """
    FASTEST: Aggressive sampling approach - avoids O(n²) entirely
    """
    if len(charset) <= target_size:
        return charset.copy()

    print(f"⚡ Aggressive sampling: {len(charset)} -> {target_size}")

    # Always keep blank and full characters
    essential_chars = [
        char
        for char in charset
        if char.is_blank() or char.data == PetsciiChar.FULL_DATA
    ]

    # Sort all others by usage count
    other_chars = [char for char in charset if char not in essential_chars]
    other_chars.sort(key=lambda c: c.use_count(), reverse=True)

    # Take top N by usage
    slots_remaining = target_size - len(essential_chars)
    if slots_remaining > 0:
        selected_chars = other_chars[:slots_remaining]
        result = essential_chars + selected_chars
    else:
        # If we have too many essential chars, just take the most used overall
        all_sorted = sorted(charset, key=lambda c: c.use_count(), reverse=True)
        result = all_sorted[:target_size]

    print(f"⚡ Aggressive sampling complete: {len(result)} chars")
    return result


def reduce_charset(charset: List[PetsciiChar], target_size: int) -> List[PetsciiChar]:
    """
    FIXED: Main charset reduction function with proper algorithm selection
    """
    if len(charset) <= target_size:
        return charset.copy()

    reduction_ratio = len(charset) / target_size if target_size > 0 else 1

    if reduction_ratio < REDUCTION_RATIO_SMALL:
        # Small reduction - just use top usage chars (fastest and safest)
        sorted_chars = sorted(charset, key=lambda c: c.use_count(), reverse=True)
        result = sorted_chars[:target_size]
        return result
    elif reduction_ratio < REDUCTION_RATIO_MEDIUM:
        # Medium reduction - use smart approach
        return reduce_charset_smart(charset, target_size)
    else:
        # Large reduction - use aggressive sampling
        return reduce_charset_aggressive_sampling(charset, target_size)


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
        self.screen_codes = [0] * MAX_SCREEN_OFFSET
        self.color_data = [0] * MAX_SCREEN_OFFSET
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
                        elif inverse:
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
                elif default_charset is not None:
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
                if offset < MAX_SCREEN_OFFSET:
                    self.screen_codes[offset] = char_index

                    if self.background_color is None:
                        # Assume it's BW if no background color is given
                        self.color_data[offset] = 1 if char_index > 0 else 0
                    # Background color specified, find any other color
                    elif char.is_blank():
                        self.color_data[offset] = 0
                    else:
                        foreground_color = None
                        for cy in range(8):
                            if foreground_color is not None:
                                break
                            for cx in range(8):
                                color = rgb_to_idx(get_pixel_rgb(image, x + cx, y + cy))
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
    with open(file_path) as file:
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
        screen.screen_codes = data[:MAX_SCREEN_OFFSET]
        screen.color_data = data[MAX_SCREEN_OFFSET : MAX_SCREEN_OFFSET * 2]

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
    with open(file_path) as file:
        return json.load(file)


def ints_to_bitarray(ints: List[int]):
    if len(ints) != 8:  # noqa: PLR2004
        raise ValueError("The input list must contain exactly 8 integers")

    ba = bitarray(endian="big")
    for num in ints:
        if not 0 <= num <= 255:  # noqa: PLR2004
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

    if len(charset) > MAX_BYTE_VALUE:
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
        screen.charset = [*charset]
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


def write_petmate(
    screens: List[PetsciiScreen], output_file: str, use_custom_charset: bool = False
) -> None:
    """
    Write a list of PetsciiScreen objects to a petmate file.

    Args:
        screens: List of PetsciiScreen objects to write
        output_file: Path to the output file
        use_custom_charset: If True, create custom charsets; if False, use built-in "upper" charset
    """
    output = {
        "version": 2,
        "screens": list(range(len(screens))),
        "framebufs": [],
        "customFonts": {},
    }

    # First pass: identify and deduplicate charsets if we're using custom charsets
    custom_charsets = {}
    charset_mapping = {}

    if use_custom_charset:
        for screen in screens:
            charset_key = id(screen.charset)

            if charset_key not in charset_mapping:
                charset_name = f"charset_{len(charset_mapping)}"
                charset_mapping[charset_key] = charset_name
                custom_charsets[charset_name] = screen.charset

    # Second pass: create framebufs
    for _i, screen in enumerate(screens):
        # Determine charset name - either custom or built-in
        if use_custom_charset:
            charset_key = id(screen.charset)
            charset_name = charset_mapping[charset_key]
        else:
            charset_name = "upper"  # Default to built-in charset

        # Create the 2D framebuf array
        framebuf = []
        for row in range(25):
            row_data = []
            for col in range(40):
                offset = row * 40 + col
                if offset < len(screen.screen_codes) and offset < len(
                    screen.color_data
                ):
                    entry = {
                        "code": int(screen.screen_codes[offset]),
                        "color": int(screen.color_data[offset]),
                    }
                else:
                    entry = {
                        "code": 32,
                        "color": 14,
                    }  # Space character with light blue color
                row_data.append(entry)
            framebuf.append(row_data)

        frame = {
            "width": 40,
            "height": 25,
            "backgroundColor": (
                int(screen.background_color)
                if screen.background_color is not None
                else 6
            ),
            "borderColor": (
                int(screen.border_color) if screen.border_color is not None else 14
            ),
            "charset": charset_name,
            "name": f"screen_{screen.screen_index:03d}",
            "framebuf": framebuf,
        }
        output["framebufs"].append(frame)

    # Process custom charsets according to WsCustomFontsV2 type
    if use_custom_charset:
        for name, charset in custom_charsets.items():
            # Create the bits array
            bits = []
            for char in charset:
                # For each character, extract 8 rows of bits as integers
                for row in range(8):
                    row_start = row * 8
                    row_end = row_start + 8
                    row_bits = char.data[row_start:row_end]
                    row_int = int(row_bits.to01(), 2)
                    bits.append(row_int)

            # Create charOrder array - maps integers 0-255 to their positions in the charset
            # For a standard charset, this would just be [0, 1, 2, ..., 255]
            charOrder = list(range(256))

            # Add to customFonts
            output["customFonts"][name] = {
                "name": name,
                "font": {"bits": bits, "charOrder": charOrder},
            }

    # Write to file
    with open(output_file, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    charset_type = "custom" if use_custom_charset else "built-in 'upper'"
    print(f"Wrote {len(screens)} screens to {output_file} using {charset_type} charset")


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
    """Optimized charset merging with better performance"""
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

    seed_charset = [*chars_used_in_all]
    sorted_chars = sorted(all_characters, key=lambda ch: len(ch.usage), reverse=True)
    for char in sorted_chars:
        if char not in seed_charset:
            seed_charset.append(char)
        if len(seed_charset) > MAX_SEED_CHARSET_SIZE:
            break

    charset = [*seed_charset]
    charsets = []

    for _idx, screen in enumerate(screens):
        new_charset = [*charset]

        for char in screen.charset:
            if char not in charset:
                new_charset.append(char)

        if len(new_charset) > MAX_BYTE_VALUE:
            charsets.append(charset)
            charset = [*seed_charset]
            for char in screen.charset:
                if char not in charset:
                    charset.append(char)
        else:
            charset.clear()
            charset.extend(new_charset)

        if len(charset) > MAX_BYTE_VALUE:
            charset = [
                PetsciiChar(PetsciiChar.BLANK_DATA),
                PetsciiChar(PetsciiChar.FULL_DATA),
                *reduce_charset(charset, 253),
            ]

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
    """Simplified charset compression"""
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


def merge_charsets_compress(screens, max_charsets=4):
    """Main entry point for charset compression"""
    if max_charsets == 1:
        all_chars = []
        for screen in screens:
            all_chars.extend(screen.charset)

        print(Fore.GREEN + f"Crunching all {len(all_chars)} characters to one charset")
        charset = [
            PetsciiChar(PetsciiChar.BLANK_DATA),
            PetsciiChar(PetsciiChar.FULL_DATA),
            *reduce_charset(all_chars, 253),
        ]

        for screen in screens:
            screen.remap_characters(charset, True)

        return screens, [charset]
    else:
        screens, charsets = merge_charsets(screens)
        screens, charsets, _ = compress_charsets(
            screens, charsets, max_charsets=max_charsets
        )
        return screens, charsets
