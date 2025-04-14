#include "PetsciiReader.h"
#include "fmt/core.h"
#include <fstream>
#include <regex>
#include <string>
#include <vector>
#include <sstream>
#include <stdexcept>

using namespace AnimTool;

PetsciiAnim AnimTool::PetsciiReader::readFrames(const std::string &filename) {
    PetsciiAnim anim;
    anim.m_sourceFilename = filename;

    std::ifstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error(fmt::format("Failed to open file: {}", filename));
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string content = buffer.str();
    file.close();

    std::regex frame_pattern(R"(unsigned char frame(\w+)\[\]=\{(?s)(.*?)\};)");

    auto frames_begin = std::sregex_iterator(content.begin(), content.end(), frame_pattern);
    auto frames_end = std::sregex_iterator();

    for (auto i = frames_begin; i != frames_end; ++i) {
        const std::smatch &match = *i;
        std::string frame_id = match[1];
        std::string frame_data = match[2];

        Frame frame{};

        // Split the frame data into lines
        std::istringstream frame_stream(frame_data);
        std::string line;
        std::vector<std::string> lines;

        while (std::getline(frame_stream, line)) {
            lines.push_back(line);
        }

        // Extract border and background colors
        if (lines.size() > 1) {
            std::string color_line = lines[1];

            // Remove trailing comma if present
            if (!color_line.empty() && color_line.back() == ',') {
                color_line.pop_back();
            }

            // Split the color values
            std::istringstream color_stream(color_line);
            std::string color_value;
            std::vector<int> colors;

            while (std::getline(color_stream, color_value, ',')) {
                // Trim whitespace
                color_value.erase(0, color_value.find_first_not_of(" \t"));
                color_value.erase(color_value.find_last_not_of(" \t") + 1);

                if (!color_value.empty()) {
                    colors.push_back(std::stoi(color_value));
                }
            }

            if (colors.size() >= 2) {
                frame.m_foregroundColor = colors[0]; // border color in Python
                frame.m_backgroundColor = colors[1];
            }
        }

        // Extract character and color data
        std::vector<uint8_t> data;

        for (size_t idx = 2; idx < lines.size(); ++idx) {
            std::string data_line = lines[idx];

            // Remove trailing comma if present
            if (!data_line.empty() && data_line.back() == ',') {
                data_line.pop_back();
            }

            // Split the data values
            std::istringstream data_stream(data_line);
            std::string data_value;

            while (std::getline(data_stream, data_value, ',')) {
                // Trim whitespace
                data_value.erase(0, data_value.find_first_not_of(" \t"));
                data_value.erase(data_value.find_last_not_of(" \t") + 1);

                if (!data_value.empty()) {
                    data.push_back(std::stoi(data_value));
                }
            }
        }

        if (data.size() >= 2000) {
            for (int j = 0; j < 1000; ++j) {
                frame.m_characterRam[j] = data[j];
                frame.m_colorRam[j] = data[j + 1000];
            }
        }

        anim.m_frames.push_back(frame);
    }

    return anim;
}
