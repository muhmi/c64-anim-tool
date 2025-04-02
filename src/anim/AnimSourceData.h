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
        uint8_t row{};
        uint8_t col{};
    };

    struct SpriteData {
        std::array<uint8_t, 64> data;
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

        std::string source_name{};

        [[nodiscard]] virtual std::string name() const;

        [[nodiscard]] virtual Type type() const = 0;

        // returns a list of channel types this channel replaces
        [[nodiscard]] virtual std::vector<Type> replacesChannels() const { return {}; };
    };

    // Animation source data is split to channels which represent changes different things like VIC register or charset RAM
    struct AnimSourceData {
        uint16_t default_frame_duration{};
        std::vector<SourceChannel> channels;
    };
}
