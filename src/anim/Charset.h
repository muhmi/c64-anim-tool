#pragma once

#include <array>
#include <bitset>
#include <cstdint>
#include <utility>
#include <vector>

#include "Utils.h"

namespace AnimTool {
    class Charset;

    class Char final {
       public:
        static Char BLANK;
        static Char FULL;

        explicit Char(const uint8_t *bitmap);

        uint8_t *data();

        [[nodiscard]] const uint8_t *data() const;

        void clear();

        void invert();

        bool isBlank() const;

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

        bool operator==(const Char &other) const { return distance(other) == 0; }

        bool operator!=(const Char &other) const { return distance(other) != 0; }

       private:
        uint8_t m_bitmap[8]{0, 0, 0, 0, 0, 0, 0, 0};
    };

    class Charset final {
       public:
        explicit Charset(std::string sourceFilename) : m_sourceFilename(std::move(sourceFilename)) {}

        uint8_t insert(const Char &character);

        std::optional<uint8_t> indexOf(const Char &character) const;
        uint8_t closestChar(const Char& character) const;

        [[nodiscard]] size_t size() const { return m_characters.size(); }

        [[nodiscard]] size_t hash() const;

        Char operator[](uint8_t index) const { return m_characters[index]; }

        bool operator==(const Charset &other) const;

        bool operator!=(const Charset &other) const;

       private:
        std::vector<Char> m_characters{};
        std::string m_sourceFilename;
    };

}  // namespace AnimTool

namespace std {
    template <>
    struct hash<AnimTool::Char> {
        size_t operator()(const AnimTool::Char &c) const { return c.hash(); }
    };

    template <>
    struct hash<AnimTool::Charset> {
        size_t operator()(const AnimTool::Charset &c) const { return c.hash(); }
    };
}  // namespace std