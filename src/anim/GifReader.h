#pragma once

#include <functional>
#include <vector>

struct GifFileType;

namespace AnimTool {

    struct GifFrame {
        std::vector<uint8_t> pixels;  // Indexed frames based on
        int width{};
        int height{};
        int delay_ms{};  // Delay in milliseconds before showing the next frame
    };


    struct GifAnimation {
        std::vector<GifFrame> frames;
        std::string source_filename;
    };

    class GifReader {
    public:
        using PixelConverter = std::function<uint8_t(std::tuple<uint8_t, uint8_t, uint8_t>)>;

        static PixelConverter MakeDefaultPixelConverter();

        /**
         * Read a GIF animation file and convert it to a series of RGB frames
         *
         * @param filename Path to the GIF file to be loaded
         * @param paletteConverter a function to convert (R,G,B) pixels to C64 palette indexes
         * @param transparentColorIndex palette index to use for transparent color
         * @return A unique pointer to GifAnimation
         * @throws std::runtime_error If the file cannot be opened
         * @throws std::runtime_error If the file format is invalid
         * @throws std::runtime_error If memory allocation fails
         * @throws std::runtime_error If reading from the file fails
         */
        [[nodiscard]] static std::unique_ptr<GifAnimation>
        readAnimation(const std::string &filename, const PixelConverter &paletteConverter,
                      const uint8_t transparentColorIndex = 0);

    private:
        static GifFrame extractFrame(GifFileType *gif, int frameIndex, const uint8_t transparentColorIndex,
                                     const PixelConverter &paletteConverter);

        // Get the delay time for a frame in milliseconds
        static int getFrameDelay(GifFileType *gif, int frameIndex);
    };
}
