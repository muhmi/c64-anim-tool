#pragma once

#include "AnimSourceData.h"

namespace AnimTool {
    class ChannelColorRAM : public SourceChannel {
    public:
        struct Frame {
            uint8_t m_colorRam[1000]{};
            uint16_t m_delayMs{};
        };

        [[nodiscard]] Type getType() const override { return Type::COLOR_RAM; }
    };
}