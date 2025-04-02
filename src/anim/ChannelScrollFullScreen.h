#pragma once
#include "AnimSourceData.h"

namespace AnimTool::Anim {
    class ChannelScrollFullScreen : public SourceChannel {
    public:
        enum class Direction : uint8_t {
            UP,
            DOWN,
            LEFT,
            RIGHT
        };
        struct Frame {
            bool wrap{};
            uint16_t duration{};
        };
        Direction direction{};

        [[nodiscard]] Type type() const override { return Type::SCROLL_FULL_SCREEN; }
    };
}
