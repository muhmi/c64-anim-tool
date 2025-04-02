#pragma once

#include <array>
#include <cstdint>
#include <bitset>
#include <vector>

namespace AnimTool::Anim {
    struct Charset {
        uint8_t bitmap[2048]{};
        std::array<uint16_t, 256> usage_count{};
    };

    class Char {
    public:
        Char(Charset *charset, uint8_t idx) : parentCharset(charset), index(idx) {}

        uint8_t *data();

        [[nodiscard]] const uint8_t *data() const;

        void clear();

        void invert();

        [[nodiscard]] uint16_t useCount() const;

        void incUseCount();

    private:
        Charset *parentCharset;
        uint8_t index;
    };

    struct ScreenLocation {
        uint8_t row;
        uint8_t col;
    };

    struct SpriteData {
        std::array<uint8_t, 64> data;
    };

    struct ChannelScreenColor {
        struct Frame {
            uint8_t background_color{};
            uint8_t foreground_color{};
            uint16_t duration{};
        };
    };

    struct ChannelColorRAM {
        struct Frame {
            uint8_t color_ram[1000]{};
            uint16_t duration{};
        };
    };

    struct ChannelCharacterRam {
        struct Frame {
            uint8_t character_ram[1000]{};
            uint8_t charset_index{};
            uint16_t duration{};
        };
        std::vector<Charset> charsets;
    };

    struct ChannelSprite {
        struct Frame {
            std::bitset<8> sprite_enabled;
            std::bitset<8> sprite_expanded_x;
            std::bitset<8> sprite_expanded_y;
            std::array<uint16_t, 8> sprite_data_index{};
            std::array<uint16_t, 8> sprite_xpos;
            std::array<uint16_t, 8> sprite_ypos;
            uint16_t duration{};
        };
        std::vector<SpriteData> sprites;
    };

    struct ChannelColorAnimation {
        struct Frame {
            uint8_t area_index{};
            uint16_t duration{};
        };

        struct AnimatedArea {
            std::vector<ScreenLocation> locations;
        };

    };

    struct ChannelScrollFullScreen {
        enum class Direction : uint8_t {
            UP,
            DOWN,
            LEFT,
            RIGHT
        };
        struct Frame {
            bool wrap{};
            uint16_t duration{};
        };
        Direction direction{};
    };

    using Channel = std::variant<ChannelScreenColor, ChannelCharacterRam, ChannelColorRAM, ChannelSprite, ChannelColorAnimation, ChannelScrollFullScreen>;

    // Animation source data is split to channels which represent changes different things like VIC register or charset RAM
    struct SourceData {
        std::vector<Channel> channels;
    };
}
