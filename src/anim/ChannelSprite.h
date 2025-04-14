#pragma once

#include "AnimSourceData.h"

namespace AnimTool {
    struct SpriteData {
        std::array<uint8_t, 64> m_data;
    };

    class ChannelSprite : public AnimTool::SourceChannel {
    public:
        struct Frame {
            std::bitset<8> m_spriteEnabled;
            std::bitset<8> m_spriteExpanded_x;
            std::bitset<8> m_spriteExpanded_y;
            std::array<uint16_t, 8> m_spriteDataIndex{};
            std::array<uint16_t, 8> m_spriteX{};
            std::array<uint16_t, 8> m_spriteY{};
            uint16_t m_delayMs{};
        };
        std::vector<AnimTool::SpriteData> m_sprites;

        [[nodiscard]] Type getType() const override { return Type::SPRITE; }
    };

}