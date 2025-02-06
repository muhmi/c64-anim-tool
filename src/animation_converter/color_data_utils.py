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
    fill_blocks, min_sequence_length=10, max_sequence_length=120, base_address=0xD800
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

    def group_sequences_by_length(sequences):
        length_groups = {}
        for seq in sequences:
            length = len(seq)
            if length not in length_groups:
                length_groups[length] = []
            length_groups[length].append(seq)
        return length_groups

    result = []
    for idx, offsets in enumerate(fill_blocks):
        result.append(f"fill_color_step{idx}")
        result.append("\tlda fill_color")

        # Find continuous sequences
        sequences = find_sequences(offsets)

        # Group sequences by length and sort by length (descending)
        length_groups = group_sequences_by_length(sequences)
        sorted_lengths = sorted(length_groups.keys(), reverse=True)

        # Generate optimized fill code for each length group
        for length in sorted_lengths:
            sequences_of_length = length_groups[length]
            result.append(f"\tldx #{length} - 1")
            result.append("-")
            # Generate a loop for each sequence of this length
            loop_label = f"l{length}_{idx}"
            for sequence in sequences_of_length:
                start_offset = sequence[0]
                result.append(f"\tsta ${hex(base_address + start_offset)[2:]},x")

            result.append("\tdex")
            result.append("\tbpl -")
            result.append("")

        # Generate individual sta instructions for remaining offsets
        remaining = remove_sequences_from_list(offsets, sequences)
        for offset in remaining:
            result.append(f"\tsta ${hex(base_address + offset)[2:]}")

        result.append("\trts")
        result.append("")

    return "\n".join(result)
