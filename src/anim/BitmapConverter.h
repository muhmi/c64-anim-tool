#pragma once

#include <array>
#include <cstdint>

namespace AnimTool {

    class BitmapConverter {
    public:
        ~BitmapConverter() = default;

        [[nodiscard]] virtual uint8_t convertRGBToPaletteIndex(uint8_t r, uint8_t g, uint8_t b) const = 0;

        [[nodiscard]] virtual uint8_t getBackgroundColorIndex() const = 0;
    };

    class PeptoOldConverter final : public BitmapConverter {
    public:
        PeptoOldConverter(uint8_t backgroundColor);

        [[nodiscard]] uint8_t convertRGBToPaletteIndex(uint8_t r, uint8_t g, uint8_t b) const override;

        [[nodiscard]] uint8_t getBackgroundColorIndex() const override;

    private:
        static std::array<std::tuple<uint8_t, uint8_t, uint8_t>, 16> VIC_PALETTE;
        int m_backgroundColor;
    };

} // AnimTool
