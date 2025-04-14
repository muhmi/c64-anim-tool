#include "CharsetReader.h"
#include "Charset.h"
#include "fmt/core.h"
#include <fstream>

using namespace AnimTool;

Charset AnimTool::CharsetReader::readCharset(const std::string &ilename) {

    if (!ilename.ends_with(".bin") && !ilename.ends_with(".64c")) {
        throw std::invalid_argument(
                fmt::format("Only .bin and .64c are supported, unable to load {}", ilename));
    }

    Charset charset;
    charset.m_sourceFilename = ilename;

    std::ifstream file(ilename, std::ios::binary);

    if (!file) {
        throw std::runtime_error(fmt::format("Failed to open file: {}", ilename));
    }

    if (ilename.ends_with(".64c")) {
        // skip first two bytes
        file.seekg(2, std::ios::beg);
    }

    if (!file) {
        throw std::runtime_error(fmt::format("Failed to seek file: {}", ilename));
    }

    // load full file contents as binary
    file.read(reinterpret_cast<char *>(charset.m_bitmap), sizeof(charset.m_bitmap));

    std::streamsize bytesRead = file.gcount();
    if (bytesRead == 0) {
        throw std::runtime_error(fmt::format("No data read from file: {}", ilename));
    }

    return charset;
}
