#pragma once

#include "AnimSourceData.h"

namespace AnimTool {

    class ChannelScreenColor : public SourceChannel {
       public:
        struct Frame {
            uint8_t m_backgroundColor{};
            uint8_t m_foregroundColor{};
            uint16_t m_duration{};
        };

        [[nodiscard]] Type getType() const override { return Type::SCREEN_COLOR; }
    };

}  // namespace AnimTool