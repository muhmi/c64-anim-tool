#pragma once

#include "Utils.h"

#include <array>
#include <cstdint>
#include <bitset>
#include <utility>
#include <vector>

namespace AnimTool {
    class Charset;

    class Char final {
    public:
        explicit Char(const uint8_t *bitmap, uint8_t idx);

        uint8_t *data();

        [[nodiscard]] const uint8_t *data() const;

        void clear();

        void invert();

        [[nodiscard]] ANIM_TOOL_INLINE uint16_t distance(const Char &other) const {
            return hamming_distance_8bytes(data(), other.data());
        }

        [[nodiscard]] size_t hash() const {
            size_t hash_value = 0;
            const uint8_t *bytes = data();
            for (int i = 0; i < 8; i++) {
                hash_value = hash_value * 31 + bytes[i];
            }
            return hash_value;
        }

        bool operator==(const Char &other) const {
            return distance(other) == 0;
        }

        bool operator!=(const Char &other) const {
            return distance(other) != 0;
        }

    private:


        uint8_t m_bitmap[8]{0, 0, 0, 0, 0, 0, 0, 0};
        uint8_t m_index{0};
    };

    class Charset final {
    public:
        explicit Charset(std::string sourceFilename) : m_sourceFilename(std::move(sourceFilename)) {}

        uint8_t insert(const Char& character);

        [[nodiscard]] size_t hash() const;

        Char operator[](uint8_t index) const {
            return m_characters[index];
        }

        bool operator==(const Charset &other) const;

        bool operator!=(const Charset &other) const;

    private:
        std::vector<Char> m_characters;
        std::string m_sourceFilename;

    };

}

namespace std {
    template<>
    struct hash<AnimTool::Char> {
        size_t operator()(const AnimTool::Char &c) const {
            return c.hash();
        }
    };

    template<>
    struct hash<AnimTool::Charset> {
        size_t operator()(const AnimTool::Charset &c) const {
            return c.hash();
        }
    };
}