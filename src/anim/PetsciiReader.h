#pragma once

#include <cstdint>
#include <vector>

namespace AnimTool {
    struct Frame {
        uint8_t background_color{};
        uint8_t foreground_color{};
        uint8_t color_ram[1000]{};
        uint8_t character_ram[1000]{};
    };

    struct PetsciiAnim {
        std::vector<Frame> frames;
        std::string source_filename;
    };

    class PetsciiReader {
    public:
        /**
         * Read .c files produced by Marq’s PETSCII editor
         *
         * @param petscii_c_filename path to .c file
         * @return PetsciiAnim
         * @throws std::runtime_error If the file cannot be opened
         */
        [[nodiscard]] static PetsciiAnim readFrames(const std::string &petscii_c_filename);
    };
}