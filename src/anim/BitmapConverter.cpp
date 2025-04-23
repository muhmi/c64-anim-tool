#include "BitmapConverter.h"

namespace AnimTool {

    std::array<std::tuple<uint8_t, uint8_t, uint8_t>, 16> PeptoOldConverter::VIC_PALETTE = {{
        {0, 0, 0},        // 00 black
        {255, 255, 255},  // 01 white
        {104, 55, 43},    // 02 red
        {112, 164, 178},  // 03 cyan
        {111, 61, 134},   // 04 purple
        {88, 141, 67},    // 05 green
        {53, 40, 121},    // 06 blue
        {184, 199, 111},  // 07 yellow
        {111, 79, 37},    // 08 orange
        {67, 57, 0},      // 09 brown
        {154, 103, 89},   // 10 light_red
        {68, 68, 68},     // 11 dark_gray
        {108, 108, 108},  // 12 gray
        {154, 210, 132},  // 13 light_green
        {108, 94, 181},   // 14 light_blue
        {149, 149, 149}   // 15 light_gray
    }};

    PeptoOldConverter::PeptoOldConverter(uint8_t backgroundColor) : m_backgroundColor(backgroundColor) {}

    uint8_t PeptoOldConverter::convertRGBToPaletteIndex(uint8_t r, uint8_t g, uint8_t b) const {
        double smallestError = 1000000.0;
        uint8_t idx = 0;

        for (size_t i = 0; i < VIC_PALETTE.size(); i++) {
            auto [pr, pg, pb] = VIC_PALETTE[i];

            double cr = static_cast<double>(pr) - r;
            double cg = static_cast<double>(pg) - g;
            double cb = static_cast<double>(pb) - b;

            double err = std::sqrt((cr * cr) + (cg * cg) + (cb * cb));

            if (err < smallestError) {
                smallestError = err;
                idx = static_cast<uint8_t>(i);
            }
        }

        return idx;
    }

    uint8_t PeptoOldConverter::getBackgroundColorIndex() const { return m_backgroundColor; }

}  // namespace AnimTool