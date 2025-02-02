import random
from typing import List

from petscii import PetsciiScreen


def offset_color_frames(screens: List[PetsciiScreen], offset: int):
    color_datas = []
    for screen in screens:
        color_datas.append([] + screen.color_data)
    index = offset % len(screens)
    offset_screens = []
    for screen in screens:
        offset_screen = screen.copy()
        offset_screen.color_data = color_datas[index]
        index = (index + 1) % len(screens)
        offset_screens.append(offset_screen)
    return offset_screens


def randomize_color_frames(screens: List[PetsciiScreen], seed: int):
    color_datas = []
    for screen in screens:
        color_datas.append([] + screen.color_data)

    random.Random(seed).shuffle(color_datas)

    for idx, screen in enumerate(screens):
        screen.color_data = color_datas[idx]

    return screens


def generate_color_fill_code(
    fill_blocks, min_sequence_length=10, max_sequence_length=120
):
    def find_sequences(numbers):
        sequences = []
        current_seq = []

        for i, num in enumerate(numbers):
            if not current_seq:
                current_seq = [num]
            elif num == current_seq[-1] + 1:
                # Check if adding this number would exceed max length
                if len(current_seq) < max_sequence_length:
                    current_seq.append(num)
                else:
                    # Current sequence has reached max length, store it and start new
                    if len(current_seq) >= min_sequence_length:
                        sequences.append(current_seq)
                    current_seq = [num]
            else:
                if len(current_seq) >= min_sequence_length:
                    sequences.append(current_seq)
                current_seq = [num]

        if current_seq and len(current_seq) >= min_sequence_length:
            sequences.append(current_seq)

        return sequences

    def remove_sequences_from_list(numbers, sequences):
        flat_seq = [num for seq in sequences for num in seq]
        return [num for num in numbers if num not in flat_seq]

    result = []

    for idx, offsets in enumerate(fill_blocks):
        result.append(f"fill_color_step{idx}")
        result.append("\tlda fill_color")

        # Find continuous sequences
        sequences = find_sequences(offsets)

        # Generate fill_max_127 calls for sequences
        for sequence in sequences:
            start_offset = sequence[0]
            count = len(sequence)
            result.append(f"\t#fill_max_127 ${hex(0xd800 + start_offset)[2:]}, {count}")

        # Generate individual sta instructions for remaining offsets
        remaining = remove_sequences_from_list(offsets, sequences)
        for offset in remaining:
            result.append(f"\tsta ${hex(0xd800 + offset)[2:]}")

        result.append("\trts")
        result.append("")

    return "\n".join(result)
