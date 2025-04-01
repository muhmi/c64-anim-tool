#include "config/config.h"
#include <fmt/core.h>
#include <yaml-cpp/yaml.h>

using namespace AnimTool;

void AnimTool::load_yaml_config(const std::string &config_path, AppConfig &config) {
    YAML::Node yaml = YAML::LoadFile(config_path);

    if (yaml["input_file"]) {
        config.input_file = yaml["input_file"].as<std::string>();
    }

    if (yaml["output_file"]) {
        config.output_file = yaml["output_file"].as<std::string>();
    }

    if (yaml["verbose"]) {
        config.verbose = yaml["verbose"].as<bool>();
    }

    if (yaml["quality"]) {
        config.quality = yaml["quality"].as<int>();
    }

    if (yaml["include_paths"]) {
        config.include_paths.clear();
        for (const auto &path: yaml["include_paths"]) {
            config.include_paths.push_back(path.as<std::string>());
        }
    }

}

void AnimTool::print_config(const AppConfig &config) {
    fmt::print("Configuration:\n");
    fmt::print("  Input file: {}\n", config.input_file);
    fmt::print("  Output file: {}\n", config.output_file);
    fmt::print("  Verbose: {}\n", config.verbose ? "yes" : "no");
    fmt::print("  Quality: {}\n", config.quality);

    fmt::print("  Include paths: ");
    if (config.include_paths.empty()) {
        fmt::print("none");
    } else {
        for (const auto &path: config.include_paths) {
            fmt::print("{} ", path);
        }
    }
    fmt::print("\n");
}