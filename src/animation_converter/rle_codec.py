from logger import get_logger

logger = get_logger()

RLE_MAX_RUN_LENGTH = 64


class RLECodec:
    @staticmethod
    def encode(data):
        if not data:
            return []

        result = []
        count = 1
        current = data[0]

        for value in data[1:]:
            if value == current and count < RLE_MAX_RUN_LENGTH:
                count += 1
            else:
                result.extend([count, current])
                count = 1
                current = value

        result.extend([count, current])
        return result

    @staticmethod
    def decode(encoded_data):
        if len(encoded_data) % 2 != 0:
            raise ValueError("Encoded data must have an even number of elements")

        result = []
        for i in range(0, len(encoded_data), 2):
            count = encoded_data[i]
            value = encoded_data[i + 1]
            result.extend([value] * count)

        return result


if __name__ == "__main__":
    # Test data
    original = [1, 1, 1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5] + [6] * 300

    # Encode
    encoded = RLECodec.encode(original)
    logger.info(f"Encoded: {encoded}")

    # Decode
    decoded = RLECodec.decode(encoded)
    logger.info(f"Decoded: {decoded}")

    # Verify
    logger.info(f"Original length: {len(original)}")
    logger.info(f"Encoded length: {len(encoded)}")
    logger.info(f"Decoded length: {len(decoded)}")
    logger.success(f"Decoded matches original: {decoded == original}")
