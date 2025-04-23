#pragma once

#include "AnimSourceData.h"

namespace AnimTool {
class ChannelColorAnimation : public SourceChannel {
   public:
    struct Frame {
        uint8_t m_areaIndex{};
        uint16_t m_delayMs{};
    };

    struct AnimatedArea {
        std::vector<AnimTool::ScreenLocation> m_locations;
    };
    std::vector<AnimatedArea> m_areas;

    [[nodiscard]] Type getType() const override { return Type::COLOR_ANIMATION; }
};
}  // namespace AnimTool