#pragma once

#include <cstdint>

namespace AnimTool::Petscii {
    struct Frame {
        uint8_t background_color;
        uint8_t foreground_color;
        uint8_t color_ram[1000];
        uint8_t character_ram[1000];
    };
}