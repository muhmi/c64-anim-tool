#pragma once

#include <cstdint>
#include <vector>

namespace AnimTool {
    struct Frame {
        uint8_t m_backgroundColor{};
        uint8_t m_foregroundColor{};
        uint8_t m_colorRam[1000]{};
        uint8_t m_characterRam[1000]{};
        int m_delayMs{};
    };

    struct PetsciiAnim {
        std::vector<Frame> m_frames;
        std::string m_sourceFilename;
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