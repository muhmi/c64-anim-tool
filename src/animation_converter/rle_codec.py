class RLECodec:
    @staticmethod
    def encode(data):
        if not data:
            return []

        encoded = []
        count = 1
        current = data[0]

        for value in data[1:]:
            if value == current and count < 64:
                count += 1
            else:
                encoded.extend([count, current])
                count = 1
                current = value

        encoded.extend([count, current])
        return encoded

    @staticmethod
    def decode(encoded_data):
        if len(encoded_data) % 2 != 0:
            raise ValueError("Encoded data must have an even number of elements")

        decoded = []
        for i in range(0, len(encoded_data), 2):
            count = encoded_data[i]
            value = encoded_data[i + 1]
            decoded.extend([value] * count)

        return decoded


if __name__ == "__main__":
    # Test data
    original = [1, 1, 1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5] + [6] * 300

    # Encode
    encoded = RLECodec.encode(original)
    print("Encoded:", encoded)

    # Decode
    decoded = RLECodec.decode(encoded)
    print("Decoded:", decoded)

    # Verify
    print("Original length:", len(original))
    print("Encoded length:", len(encoded))
    print("Decoded length:", len(decoded))
    print("Decoded matches original:", decoded == original)
