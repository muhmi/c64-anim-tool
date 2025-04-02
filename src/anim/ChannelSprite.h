#pragma once
#include "AnimSourceData.h"

namespace AnimTool::Anim {
    class ChannelSprite : public AnimTool::Anim::SourceChannel {
    public:
        struct Frame {
            std::bitset<8> sprite_enabled;
            std::bitset<8> sprite_expanded_x;
            std::bitset<8> sprite_expanded_y;
            std::__1::array<uint16_t, 8> sprite_data_index{};
            std::__1::array<uint16_t, 8> sprite_x{};
            std::__1::array<uint16_t, 8> sprite_y{};
            uint16_t duration{};
        };
        std::__1::vector<AnimTool::Anim::SpriteData> sprites;

        [[nodiscard]] Type type() const override { return Type::SPRITE; }
    };

}