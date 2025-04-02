#pragma once

#include "AnimSourceData.h"

namespace AnimTool::Anim {
    class ChannelColorRAM : public SourceChannel {
    public:
        struct Frame {
            uint8_t color_ram[1000]{};
            uint16_t duration{};
        };

        [[nodiscard]] Type type() const override { return Type::COLOR_RAM; }
    };
}