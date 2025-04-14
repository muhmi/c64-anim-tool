#pragma once

#include <functional>
#include <vector>

struct GifFileType;

namespace AnimTool {

    struct GifFrame {
        std::vector<uint8_t> m_pixels;
        int m_width{};
        int m_height{};
        int m_delayMs{};
    };

    struct GifAnimation {
        std::vector<GifFrame> m_frames;
        std::string m_source_filename;
    };

    class BitmapConverter;

    class GifReader {
    public:
        /**
         * Read a GIF animation file and convert it to a series of RGB frames
         *
         * @param filename Path to the GIF file to be loaded
         * @param bitmapConverter A BitmapConverter class to convert RGB to C64 palette index
         * @return A GifAnimation
         * @throws std::runtime_error If the file cannot be opened
         * @throws std::runtime_error If the file format is invalid
         * @throws std::runtime_error If memory allocation fails
         * @throws std::runtime_error If reading from the file fails
         */
        [[nodiscard]] static GifAnimation
        readAnimation(const std::string &filename, const BitmapConverter &bitmapConverter);

    private:
        static GifFrame extractFrame(GifFileType *gif, int frameIndex,
                                     const BitmapConverter &paletteConverter);

        // Get the delay time for a frame in milliseconds
        static int getFrameDelay(GifFileType *gif, int frameIndex);
    };
}
