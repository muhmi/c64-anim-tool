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

    struct Frame {
        uint8_t background_color;
        uint8_t foreground_color;
        uint8_t color_ram[1000];
        uint8_t character_ram[1000];
        uint8_t charset_index;
        uint16_t duration;
    };

    struct SourceData {
        std::vector<Charset> charsets;
        std::vector<Frame> frames;
    };
}
