#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

#if defined(_MSC_VER)
#define ANIM_TOOL_INLINE __forceinline
#elif defined(__GNUC__) || defined(__clang__)
#define ANIM_TOOL_INLINE __attribute__((always_inline)) inline
#else
#define ANIM_TOOL_INLINE inline
#endif

namespace AnimTool {

// FNV-1a hash function (64-bit version)
template <typename T>
size_t fnv1a_hash(const T *data, size_t size) {
    const uint64_t FNV_PRIME = 1099511628211ULL;
    const uint64_t FNV_OFFSET_BASIS = 14695981039346656037ULL;

    const auto *bytes = reinterpret_cast<const uint8_t *>(data);
    uint64_t hash = FNV_OFFSET_BASIS;

    for (size_t i = 0; i < size; ++i) {
        hash ^= static_cast<uint64_t>(bytes[i]);
        hash *= FNV_PRIME;
    }

    return static_cast<size_t>(hash);
}

ANIM_TOOL_INLINE size_t fnv1a_hash(const std::string &str) {
    return fnv1a_hash(str.data(), str.size());
}

ANIM_TOOL_INLINE uint16_t hamming_distance_8bytes(const unsigned char *bytes1,
                                                  const unsigned char *bytes2) {
    uint16_t distance = 0;
    for (int i = 0; i < 8; i++) {
        unsigned char xor_result = bytes1[i] ^ bytes2[i];
        while (xor_result) {
            distance += xor_result & 1;
            xor_result >>= 1;
        }
    }
    return distance;
}
}  // namespace AnimTool