#pragma once

#include <string>
#include <vector>

namespace AnimTool {
    /**
     * Application configuration structure.
     * Holds all settings that can be set via command line or config file.
     */
    struct AppConfig {
        std::string input_file;
        std::string output_file;
        bool verbose = false;
        int quality = 100;
        std::vector<std::string> include_paths;
    };

    /**
     * Load configuration from a YAML file.
     *
     * @param config_path Path to the YAML configuration file
     * @param config Configuration structure to populate
     * @throws std::runtime_error if the file cannot be parsed
     */
    void load_yaml_config(const std::string &config_path, AppConfig &config);

    /**
     * Print the current configuration.
     *
     * @param config Configuration to print
     */
    void print_config(const AppConfig &config);
}  // namespace AnimTool