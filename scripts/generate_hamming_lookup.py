#!/usr/bin/env python3
"""
Generate pre-computed Hamming distance lookup table.

This script creates a binary file containing a 256x256 lookup table
for byte-to-byte Hamming distances. The table is used by petscii.py
for fast character distance calculations.

Output: src/animation_converter/data/hamming_lookup.bin (64KB)
Format: 256x256 array of uint8 values (Hamming distances 0-8)
"""

import os
import sys

# Constants
MAX_HAMMING_DISTANCE = 8  # Maximum Hamming distance for a byte (8 bits)
LOOKUP_TABLE_SIZE = 65536  # 256 * 256 bytes


def calculate_hamming_distance(byte1: int, byte2: int) -> int:
    """Calculate Hamming distance between two bytes"""
    xor = byte1 ^ byte2
    count = 0
    temp = xor
    while temp:
        count += temp & 1
        temp >>= 1
    return count


def generate_lookup_table() -> bytes:
    """
    Generate complete 256x256 Hamming distance lookup table.

    Returns:
        Bytes object containing 65,536 uint8 values
    """
    print("Generating Hamming distance lookup table...")
    print("  Size: 256x256 = 65,536 bytes")

    # Build lookup table
    lookup_data = bytearray()

    for i in range(256):
        if i % 32 == 0:
            print(f"  Progress: {i}/256 ({i*100//256}%)")

        for j in range(256):
            distance = calculate_hamming_distance(i, j)
            lookup_data.append(distance)

    print("  Progress: 256/256 (100%)")
    print(f"  Generated {len(lookup_data)} bytes")

    return bytes(lookup_data)


def verify_lookup_table(data: bytes) -> bool:
    """
    Verify lookup table integrity.

    Args:
        data: Lookup table data

    Returns:
        True if valid, False otherwise
    """
    print("\nVerifying lookup table...")

    if len(data) != 256 * 256:
        print(f"  ERROR: Invalid size {len(data)} (expected 65536)")
        return False

    # Spot check some known values
    test_cases = [
        (0, 0, 0),  # Same byte = 0 distance
        (0xFF, 0x00, 8),  # All bits different = 8 distance
        (0b10101010, 0b01010101, 8),  # Alternating bits = 8 distance
        (0b11110000, 0b00001111, 8),  # Half-half = 8 distance
        (0b11111111, 0b11111110, 1),  # One bit different = 1 distance
        (0x0F, 0x00, 4),  # 4 bits different
    ]

    for byte1, byte2, expected in test_cases:
        index = byte1 * 256 + byte2
        actual = data[index]
        if actual != expected:
            print(
                f"  ERROR: Hamming({byte1:02X}, {byte2:02X}) = {actual}, expected {expected}"
            )
            return False

    print("  All spot checks passed ✓")

    # Verify symmetry: distance(a, b) == distance(b, a)
    print("  Checking symmetry...")
    for i in range(0, 256, 17):  # Sample every 17th value
        for j in range(0, 256, 17):
            dist_ij = data[i * 256 + j]
            dist_ji = data[j * 256 + i]
            if dist_ij != dist_ji:
                print(f"  ERROR: Asymmetry at ({i}, {j}): {dist_ij} != {dist_ji}")
                return False

    print("  Symmetry verified ✓")

    # Verify range: all distances should be 0-8
    print("  Checking value range...")
    for value in data:
        if value > MAX_HAMMING_DISTANCE:
            print(
                f"  ERROR: Invalid distance value {value} (max is {MAX_HAMMING_DISTANCE})"
            )
            return False

    print(f"  All values in valid range [0-{MAX_HAMMING_DISTANCE}] ✓")

    print("\nVerification complete: Lookup table is valid ✓")
    return True


def main():
    # Determine output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_dir = os.path.join(project_root, "src", "resources", "data")
    output_file = os.path.join(output_dir, "hamming_lookup.bin")

    print(f"Output file: {output_file}")

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Generate lookup table
    lookup_data = generate_lookup_table()

    # Verify before writing
    if not verify_lookup_table(lookup_data):
        print("\nERROR: Verification failed!")
        return 1

    # Write to file
    print(f"\nWriting to {output_file}...")
    with open(output_file, "wb") as f:
        f.write(lookup_data)

    # Verify file size
    file_size = os.path.getsize(output_file)
    print(f"  Wrote {file_size} bytes")

    if file_size != LOOKUP_TABLE_SIZE:
        print(
            f"  ERROR: Unexpected file size {file_size}, expected {LOOKUP_TABLE_SIZE}"
        )
        return 1

    print("\n✅ Successfully generated hamming_lookup.bin")
    print(f"   Location: {output_file}")
    print(f"   Size: {file_size:,} bytes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
