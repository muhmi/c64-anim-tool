#include "GifReader.h"

#include <fmt/core.h>
#include <gif_lib.h>

#include <algorithm>
#include <stdexcept>

#include "BitmapConverter.h"
#include "Defer.h"

using namespace AnimTool;

GifAnimation AnimTool::GifReader::readAnimation(const std::string &filename,
                                                const BitmapConverter &bitmapConverter) {
    GifFileType *gif = DGifOpenFileName(filename.c_str(), nullptr);

    // Ensure we close the file when exiting scope
    auto cleanup = makeDefer([gif]() { DGifCloseFile(gif, nullptr); });

    if (!gif) {
        throw std::runtime_error(fmt::format("Failed to open GIF file: {} (Error: {})", filename,
                                             GifErrorString(D_GIF_ERR_OPEN_FAILED)));
    }

    if (DGifSlurp(gif) != GIF_OK) {
        throw std::runtime_error(fmt::format("Failed to read GIF file: {} (Error: {})", filename,
                                             GifErrorString(gif->Error)));
    }

    int frameCount = gif->ImageCount;
    if (frameCount <= 0) {
        throw std::runtime_error(fmt::format("No frames found in GIF file: {}", filename));
    }

    GifAnimation animation;
    animation.m_source_filename = filename;
    for (int i = 0; i < frameCount; i++) {
        animation.m_frames.push_back(extractFrame(gif, i, bitmapConverter));
    }

    return animation;
}

GifFrame GifReader::extractFrame(GifFileType *gif, int frameIndex,
                                 const BitmapConverter &bitmapConverter) {
    if (frameIndex < 0 || frameIndex >= gif->ImageCount) {
        throw std::runtime_error(fmt::format("Invalid frame index: {}", frameIndex));
    }

    SavedImage *image = &gif->SavedImages[frameIndex];
    GifImageDesc *imageDesc = &image->ImageDesc;

    // Get frame dimensions
    int width = imageDesc->Width;
    int height = imageDesc->Height;

    // Find color map (local or global)
    ColorMapObject *colorMap = imageDesc->ColorMap ? imageDesc->ColorMap : gif->SColorMap;

    if (!colorMap) {
        throw std::runtime_error("No color map found for frame");
    }

    // Find transparent color index, if any
    int transparentIndex = -1;
    for (int i = 0; i < image->ExtensionBlockCount; i++) {
        ExtensionBlock *ext = &image->ExtensionBlocks[i];
        if (ext->Function == GRAPHICS_EXT_FUNC_CODE && ext->ByteCount >= 4 &&
            (ext->Bytes[0] & 0x01)) {  // Has transparency
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
            pixels.push_back(bitmapConverter.getBackgroundColorIndex());
            continue;
        }

        if (colorIndex >= colorMap->ColorCount) {
            colorIndex = 0;  // Use first color as fallback
        }

        uint8_t r = colorMap[i].Colors[colorIndex].Red;
        uint8_t g = colorMap[i].Colors[colorIndex].Green;
        uint8_t b = colorMap[i].Colors[colorIndex].Blue;
        pixels.push_back(bitmapConverter.convertRGBToPaletteIndex(r, g, b));
    }

    return GifFrame{.m_pixels = std::move(pixels),
                    .m_width = width,
                    .m_height = height,
                    .m_delayMs = getFrameDelay(gif, frameIndex)};
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
