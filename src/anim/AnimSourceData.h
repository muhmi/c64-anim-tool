#pragma once

#include "Utils.h"

#include <array>
#include <cstdint>
#include <bitset>
#include <vector>

namespace AnimTool {

    class Charset;
    class Char final {
    public:
        Char(Charset *charset, uint8_t idx) : m_parentCharset(charset), m_index(idx) {}

        uint8_t *data();

        [[nodiscard]] const uint8_t *data() const;

        void clear();

        void invert();

        [[nodiscard]] ANIM_TOOL_INLINE uint16_t distance(const Char &other) const {
            return hamming_distance_8bytes(data(), other.data());
        }

        [[nodiscard]] uint16_t useCount() const;

        void incUseCount();

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
        Charset *m_parentCharset;
        uint8_t m_index;
    };

    class Charset final {
    public:
        uint8_t m_bitmap[2048]{};
        std::array<uint16_t, 256> m_usageCount{};
        std::string m_sourceFilename;

        [[nodiscard]] size_t hash() const {
            size_t hash_value = fnv1a_hash(m_sourceFilename);
            size_t bitmap_hash = fnv1a_hash(m_bitmap, 2048);
            size_t usage_hash = fnv1a_hash(m_usageCount.data(), m_usageCount.size() * sizeof(uint16_t));

            hash_value ^= bitmap_hash + 0x9e3779b9 + (hash_value << 6) + (hash_value >> 2);
            hash_value ^= usage_hash + 0x9e3779b9 + (hash_value << 6) + (hash_value >> 2);

            return hash_value;
        }

        bool operator==(const Charset &other) const {
            if (m_sourceFilename != other.m_sourceFilename) return false;
            if (m_usageCount != other.m_usageCount) return false;
            for (size_t idx = 0; idx < 2048; ++idx) {
                if (m_bitmap[idx] != other.m_bitmap[idx])
                    return false;
            }
            return true;
        }

        bool operator!=(const Charset &other) const {
            return !(*this == other);
        }


    };

    struct ScreenLocation {
        uint8_t m_row{};
        uint8_t m_col{};
    };


    class SourceChannel {
    public:
        enum class Type : uint8_t {
            SCREEN_COLOR,
            COLOR_RAM,
            CHARACTER_RAM,
            SPRITE,
            COLOR_ANIMATION,
            SCROLL_FULL_SCREEN
        };

        ~SourceChannel() = default;

        [[nodiscard]] std::string getSourceName() const { return this->source_name; }

        [[nodiscard]] virtual std::string getName() const;

        [[nodiscard]] virtual Type getType() const = 0;

    private:
        std::string source_name{};
    };

    // Animation source data is split to channels which represent changes different things like VIC register or charset RAM
    struct AnimSourceData {
        uint16_t default_frame_duration{};
        std::vector<SourceChannel> channels;
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