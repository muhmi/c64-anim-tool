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
            std::__1::vector<AnimTool::Anim::ScreenLocation> locations;
        };
        std::__1::vector<AnimatedArea> areas;

        [[nodiscard]] Type type() const override { return Type::COLOR_ANIMATION; }

        [[nodiscard]] std::__1::vector<Type> replacesChannels() const override {
            return {Type::COLOR_ANIMATION};
        }
    };
}