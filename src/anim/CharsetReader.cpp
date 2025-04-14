#include "CharsetReader.h"
#include "AnimSourceData.h"
#include "fmt/core.h"
#include <fstream>

using namespace AnimTool;

Charset AnimTool::CharsetReader::readCharset(const std::string &charset_filename) {

    if (!charset_filename.ends_with(".bin") && !charset_filename.ends_with(".64c")) {
        throw std::invalid_argument(
                fmt::format("Only .bin and .64c are supported, unable to load {}", charset_filename));
    }

    Charset charset;
    charset.m_sourceFilename = charset_filename;

    std::ifstream file(charset_filename, std::ios::binary);

    if (!file) {
        throw std::runtime_error(fmt::format("Failed to open file: {}", charset_filename));
    }

    if (charset_filename.ends_with(".64c")) {
        // skip first two bytes
        file.seekg(2, std::ios::beg);
    }

    if (!file) {
        throw std::runtime_error(fmt::format("Failed to seek file: {}", charset_filename));
    }

    // load full file contents as binary
    file.read(reinterpret_cast<char *>(charset.m_bitmap), sizeof(charset.m_bitmap));

    std::streamsize bytesRead = file.gcount();
    if (bytesRead == 0) {
        throw std::runtime_error(fmt::format("No data read from file: {}", charset_filename));
    }

    return charset;
}
