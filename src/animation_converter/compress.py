import argparse
import os

from logger import get_logger
from lzma_codec import LZMALikeCodec

logger = get_logger()


def compare_files(file1, file2, max_diff=10):
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        data1 = f1.read()
        data2 = f2.read()

    if len(data1) != len(data2):
        logger.warning(
            f"File sizes differ: {file1} is {len(data1)} bytes, {file2} is {len(data2)} bytes"
        )

    differences = 0
    for i in range(max(len(data1), len(data2))):
        if i < len(data1) and i < len(data2):
            if data1[i] != data2[i]:
                logger.debug(
                    f"Difference at byte {i}: {file1} has {data1[i]:02X}, {file2} has {data2[i]:02X}"
                )
                differences += 1
        elif i < len(data1):
            logger.debug(f"Extra byte in {file1} at position {i}: {data1[i]:02X}")
            differences += 1
        else:
            logger.debug(f"Extra byte in {file2} at position {i}: {data2[i]:02X}")
            differences += 1

        if differences >= max_diff:
            logger.debug(
                f"Reached maximum number of differences to display ({max_diff})"
            )
            break

    if differences == 0:
        logger.success("Files are identical")
        return True
    else:
        logger.warning(f"Total differences: {differences}")
        return False


def compress_file(input_file, output_file, window_size=4096):
    codec = LZMALikeCodec(window_size=window_size)
    codec.compress_to_file(input_file, output_file)
    logger.success(f"Compressed {input_file} to {output_file}")
    logger.info(f"Using window size: {codec.window_size} bytes")

    original_size = os.path.getsize(input_file)
    compressed_size = os.path.getsize(output_file)
    ratio = (1 - compressed_size / original_size) * 100

    logger.info(f"Original size: {original_size} bytes")
    logger.info(f"Compressed size: {compressed_size} bytes")
    logger.info(f"Compression ratio: {ratio:.2f}%")
    logger.info(f"Space saved: {ratio:.2f}%")


def decompress_file(input_file, output_file, window_size=4096):
    codec = LZMALikeCodec(window_size=window_size)
    codec.decompress_from_file(input_file, output_file)
    logger.success(f"Decompressed {input_file} to {output_file}")
    logger.info(f"Using window size: {codec.window_size} bytes")


def test_compression(input_file, window_size=4096):
    compressed_file = input_file + ".compressed"
    decompressed_file = input_file + ".decompressed"

    logger.info("-" * 40)
    logger.info(f"Testing file {input_file}")

    compress_file(input_file, compressed_file, window_size)
    decompress_file(compressed_file, decompressed_file, window_size)

    test_ok = compare_files(input_file, decompressed_file)

    if test_ok:
        os.unlink(compressed_file)
        os.unlink(decompressed_file)


def main():
    parser = argparse.ArgumentParser(description="File compression utility")
    parser.add_argument("input_file", help="Input file path")
    parser.add_argument(
        "output_file", nargs="?", help="Output file path (optional for --test)"
    )
    parser.add_argument("--test", action="store_true", help="Run compression test")
    parser.add_argument(
        "-c", "--compress", action="store_true", help="Compress the input file"
    )
    parser.add_argument(
        "-d", "--decompress", action="store_true", help="Decompress the input file"
    )
    parser.add_argument(
        "-w",
        "--window-size",
        type=int,
        default=4096,
        help="Window size for compression (default: 4096)",
    )

    args = parser.parse_args()

    if args.test:
        if args.output_file:
            logger.warning("output_file is ignored when using --test")
        test_compression(args.input_file, args.window_size)
    elif args.compress:
        if not args.output_file:
            parser.error("output_file is required when using -c/--compress")
        compress_file(args.input_file, args.output_file, args.window_size)
    elif args.decompress:
        if not args.output_file:
            parser.error("output_file is required when using -d/--decompress")
        decompress_file(args.input_file, args.output_file, args.window_size)
    else:
        parser.error("Please specify either --test, -c/--compress, or -d/--decompress")


if __name__ == "__main__":
    main()
