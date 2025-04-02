#pragma once

#include "AnimSourceData.h"

namespace AnimTool::Anim {

    class ChannelScreenColor : public SourceChannel {
    public:
        struct Frame {
            uint8_t background_color{};
            uint8_t foreground_color{};
            uint16_t duration{};
        };

        [[nodiscard]] Type getType() const override { return Type::SCREEN_COLOR; }
    };

}