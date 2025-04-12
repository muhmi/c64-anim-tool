#include "GifReader.h"
#include "Defer.h"
#include <gif_lib.h>
#include <fmt/core.h>
#include <algorithm>
#include <stdexcept>

using namespace AnimTool;

std::unique_ptr<GifAnimation>
AnimTool::GifReader::readAnimation(const std::string &filename, const PixelConverter &paletteConverter, const uint8_t transparentColorIndex) {

    GifFileType *gif = DGifOpenFileName(filename.c_str(), nullptr);

    // Ensure we close the file when exiting scope
    auto cleanup = makeDefer([gif]() {
        DGifCloseFile(gif, nullptr);
    });

    if (!gif) {
        throw std::runtime_error(
                fmt::format("Failed to open GIF file: {} (Error: {})",
                            filename, GifErrorString(D_GIF_ERR_OPEN_FAILED))
        );
    }

    if (DGifSlurp(gif) != GIF_OK) {
        throw std::runtime_error(
                fmt::format("Failed to read GIF file: {} (Error: {})",
                            filename, GifErrorString(gif->Error))
        );
    }

    int frameCount = gif->ImageCount;
    if (frameCount <= 0) {
        throw std::runtime_error(
                fmt::format("No frames found in GIF file: {}", filename)
        );
    }

    auto animation = std::unique_ptr<GifAnimation>();
    animation->source_filename = filename;
    for (int i = 0; i < frameCount; i++) {
        animation->frames.push_back(extractFrame(gif, i, transparentColorIndex, paletteConverter));
    }

    return animation;
}

GifFrame GifReader::extractFrame(GifFileType *gif, int frameIndex, const uint8_t transparentColorIndex,
                                 const PixelConverter &paletteConverter) {
    if (frameIndex < 0 || frameIndex >= gif->ImageCount) {
        throw std::runtime_error(
                fmt::format("Invalid frame index: {}", frameIndex)
        );
    }

    SavedImage *image = &gif->SavedImages[frameIndex];
    GifImageDesc *imageDesc = &image->ImageDesc;

    // Get frame dimensions
    int width = imageDesc->Width;
    int height = imageDesc->Height;

    // Find color map (local or global)
    ColorMapObject *colorMap = imageDesc->ColorMap ?
                               imageDesc->ColorMap : gif->SColorMap;

    if (!colorMap) {
        throw std::runtime_error("No color map found for frame");
    }

    // Find transparent color index, if any
    int transparentIndex = -1;
    for (int i = 0; i < image->ExtensionBlockCount; i++) {
        ExtensionBlock *ext = &image->ExtensionBlocks[i];
        if (ext->Function == GRAPHICS_EXT_FUNC_CODE &&
            ext->ByteCount >= 4 &&
            (ext->Bytes[0] & 0x01)) { // Has transparency
            transparentIndex = ext->Bytes[3];
            break;
        }
    }

    std::vector<uint8_t> pixels;
    pixels.reserve(width * height);

    const int pixelCount = width * height;

    for (int i = 0; i < pixelCount; i++) {
        uint8_t colorIndex = image->RasterBits[i];

        if (colorIndex == transparentIndex) {
            pixels.push_back(transparentColorIndex);
            continue;
        }

        if (colorIndex >= colorMap->ColorCount) {
            colorIndex = 0;  // Use first color as fallback
        }

        uint8_t r = colorMap[i].Colors[colorIndex].Red;
        uint8_t g = colorMap[i].Colors[colorIndex].Green;
        uint8_t b = colorMap[i].Colors[colorIndex].Blue;
        pixels.push_back(paletteConverter({r, g, b}));
    }

    return GifFrame{
            .pixels = std::move(pixels),
            .width = width,
            .height = height,
            .delay_ms = getFrameDelay(gif, frameIndex)
    };
}

int GifReader::getFrameDelay(GifFileType *gif, int frameIndex) {
    SavedImage *image = &gif->SavedImages[frameIndex];

    for (int i = 0; i < image->ExtensionBlockCount; i++) {
        ExtensionBlock *ext = &image->ExtensionBlocks[i];
        if (ext->Function == GRAPHICS_EXT_FUNC_CODE && ext->ByteCount >= 4) {
            int delayTime = (ext->Bytes[1] | (ext->Bytes[2] << 8));
            return delayTime * 10;
        }
    }

    return 100;
}

const std::array<std::tuple<uint8_t, uint8_t, uint8_t>, 16> VIC_PALETTE =
        {{
                 {0, 0, 0},          // 00 black
                 {255, 255, 255},    // 01 white
                 {104, 55, 43},      // 02 red
                 {112, 164, 178},    // 03 cyan
                 {111, 61, 134},     // 04 purple
                 {88, 141, 67},      // 05 green
                 {53, 40, 121},      // 06 blue
                 {184, 199, 111},    // 07 yellow
                 {111, 79, 37},      // 08 orange
                 {67, 57, 0},        // 09 brown
                 {154, 103, 89},     // 10 light_red
                 {68, 68, 68},       // 11 dark_gray
                 {108, 108, 108},    // 12 gray
                 {154, 210, 132},    // 13 light_green
                 {108, 94, 181},     // 14 light_blue
                 {149, 149, 149}     // 15 light_gray
         }};

GifReader::PixelConverter GifReader::MakeDefaultPixelConverter() {
    return [palette = VIC_PALETTE](std::tuple<uint8_t, uint8_t, uint8_t> rgb) -> uint8_t {
        double smallestError = 1000000.0;
        uint8_t idx = 0;

        auto [r, g, b] = rgb;

        for (size_t i = 0; i < palette.size(); i++) {
            auto [pr, pg, pb] = palette[i];

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
    };
}
