#include "CharsetReader.h"

#include <fstream>

#include "Charset.h"
#include "fmt/core.h"

using namespace AnimTool;

Charset AnimTool::CharsetReader::readCharset(const std::string &filename) {
    if (!filename.ends_with(".bin") && !filename.ends_with(".64c")) {
        throw std::invalid_argument(fmt::format("Only .bin and .64c are supported, unable to load {}", filename));
    }

    Charset charset(filename);
    std::ifstream file(filename, std::ios::binary);

    if (!file) {
        throw std::runtime_error(fmt::format("Failed to open file: {}", filename));
    }

    if (filename.ends_with(".64c")) {
        // skip first two bytes as these files have load address first? or something?
        file.seekg(2, std::ios::beg);
    }

    if (!file) {
        throw std::runtime_error(fmt::format("Failed to seek file: {}", filename));
    }

    // load full file contents as binary
    uint8_t bitmap[2048];
    file.read(reinterpret_cast<char *>(bitmap), sizeof(bitmap));

    std::streamsize bytesRead = file.gcount();
    if (bytesRead == 0) {
        throw std::runtime_error(fmt::format("No data read from file: {}", filename));
    }

    auto charactersRead = static_cast<uint8_t>(static_cast<int>(bytesRead) / 8);

    for (uint8_t idx = 0; idx < charactersRead; ++idx) {
        Char character(&bitmap[idx * 8]);
        charset.insert(character);
    }

    return charset;
}
