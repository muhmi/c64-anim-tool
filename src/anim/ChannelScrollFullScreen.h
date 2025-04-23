#pragma once

#include "AnimSourceData.h"

namespace AnimTool {
    class ChannelScrollFullScreen : public SourceChannel {
       public:
        enum class Direction : uint8_t { UP, DOWN, LEFT, RIGHT };
        struct Frame {
            bool m_wrap{};
            uint16_t m_delayMs{};
        };
        Direction m_direction{};

        [[nodiscard]] Type getType() const override { return Type::SCROLL_FULL_SCREEN; }
    };
}  // namespace AnimTool
