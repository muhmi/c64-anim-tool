#pragma once

#include <cstdint>
#include <vector>

#include "Utils.h"

namespace AnimTool {

class SourceChannel {
   public:
    enum class Type : uint8_t {
        SCREEN_COLOR,
        COLOR_RAM,
        CHARACTER_RAM,
        SPRITE,
        COLOR_ANIMATION,
        SCROLL_FULL_SCREEN
    };

    ~SourceChannel() = default;

    [[nodiscard]] std::string getSourceName() const { return this->source_name; }

    [[nodiscard]] virtual std::string getName() const;

    [[nodiscard]] virtual Type getType() const = 0;

   private:
    std::string source_name{};
};

// Animation source data is split to channels which represent changes different things like VIC
// register or charset RAM
struct AnimSourceData {
    uint16_t default_frame_duration{};
    std::vector<SourceChannel> channels;
};
}  // namespace AnimTool
