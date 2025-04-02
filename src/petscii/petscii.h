#pragma once

#include <cstdint>
#include <vector>

namespace AnimTool::Petscii {
    struct Frame {
        uint8_t background_color;
        uint8_t foreground_color;
        uint8_t color_ram[1000];
        uint8_t character_ram[1000];
    };

    class Reader {
    public:
        static std::vector<Frame> readFrames(const std::string &petscii_c_filename);
    };
}