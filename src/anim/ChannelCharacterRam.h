#pragma once

#include "AnimSourceData.h"

namespace AnimTool::Anim {

    class ChannelCharacterRam : public SourceChannel {
    public:
        struct Frame {
            uint8_t character_ram[1000]{};
            uint8_t charset_index{};
            uint16_t duration{};
        };
        std::vector<Charset> charsets;

        [[nodiscard]] Type getType() const override { return Type::CHARACTER_RAM; }
    };
}