import struct


class LZMALikeCodec:
    def __init__(self, window_size=4096):
        self.window_size = window_size

    def find_match(self, data, pos):
        start = max(0, pos - self.window_size)
        end = min(pos + 255, len(data))
        longest_match = 0
        longest_match_distance = 0

        for i in range(start, pos):
            match_length = 0
            while (
                pos + match_length < end
                and data[i + match_length] == data[pos + match_length]
            ):
                match_length += 1

            if match_length > longest_match:
                longest_match = match_length
                longest_match_distance = pos - i
                if longest_match == 255:  # We've reached the maximum match length
                    break

        if longest_match >= 3 and longest_match_distance < self.window_size:
            return longest_match_distance, longest_match
        return None, 0

    def compress(self, data):
        compressed = bytearray()
        pos = 0
        while pos < len(data):
            distance, length = self.find_match(data, pos)
            if length >= 3 and distance < self.window_size:
                compressed.append(length)
                compressed.extend(struct.pack("<H", distance))
                pos += length
            else:
                compressed.append(0)
                compressed.append(data[pos])
                pos += 1
        return compressed

    def decompress(self, data, original_length):
        decompressed = bytearray()
        pos = 0
        while len(decompressed) < original_length:
            control = data[pos]
            pos += 1
            if control == 0:
                decompressed.append(data[pos])
                pos += 1
            else:
                length = control
                distance = struct.unpack("<H", data[pos : pos + 2])[0]
                pos += 2
                start = len(decompressed) - distance
                for i in range(length):
                    decompressed.append(decompressed[start + i])
        return decompressed

    def compress_to_file(self, input_file, output_file):
        with open(input_file, "rb") as infile, open(output_file, "wb") as outfile:
            data = infile.read()
            compressed = self.compress(data)
            # Write original length
            outfile.write(struct.pack("<H", len(data)))
            outfile.write(compressed)

    def decompress_from_file(self, input_file, output_file):
        with open(input_file, "rb") as infile, open(output_file, "wb") as outfile:
            original_length = struct.unpack("<H", infile.read(2))[
                0
            ]  # Read original length
            print(f"original_length = {original_length}")
            compressed_data = infile.read()
            decompressed = self.decompress(compressed_data, original_length)
            outfile.write(decompressed)
