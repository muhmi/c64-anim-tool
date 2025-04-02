#pragma once

#include "AnimSourceData.h"

namespace AnimTool::Anim {
    class ChannelColorAnimation : public SourceChannel {
    public:
        struct Frame {
            uint8_t area_index{};
            uint16_t duration{};
        };

        struct AnimatedArea {
            std::vector<AnimTool::Anim::ScreenLocation> locations;
        };
        std::vector<AnimatedArea> areas;

        [[nodiscard]] Type getType() const override { return Type::COLOR_ANIMATION; }

        [[nodiscard]] std::vector<Type> replacesChannels() const override {
            return {Type::COLOR_ANIMATION};
        }
    };
}