#pragma once

#include "AnimSourceData.h"

namespace AnimTool::Anim {
    struct SpriteData {
        std::array<uint8_t, 64> data;
    };

    class ChannelSprite : public AnimTool::SourceChannel {
    public:
        struct Frame {
            std::bitset<8> sprite_enabled;
            std::bitset<8> sprite_expanded_x;
            std::bitset<8> sprite_expanded_y;
            std::array<uint16_t, 8> sprite_data_index{};
            std::array<uint16_t, 8> sprite_x{};
            std::array<uint16_t, 8> sprite_y{};
            uint16_t duration{};
        };
        std::vector<AnimTool::Anim::SpriteData> sprites;

        [[nodiscard]] Type getType() const override { return Type::SPRITE; }
    };

}