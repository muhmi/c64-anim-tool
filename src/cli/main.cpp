#include <string>
#include <CLI/CLI.hpp>
#include <fmt/core.h>
#include "config/config.h"

int main(int argc, char **argv) {
    // Create app configuration
    AnimTool::AppConfig config;
    std::string config_path;

    // Set up CLI parser
    CLI::App app{"GIF Processing Tool"};

    // Config file option
    app.add_option("--config", config_path, "Configuration file path")
            ->check(CLI::ExistingFile);

    // Tool options
    app.add_option("-i,--input", config.input_file, "Input file")
            ->check(CLI::ExistingFile);
    app.add_option("-o,--output", config.output_file, "Output file");
    app.add_flag("-v,--verbose", config.verbose, "Enable verbose output");
    app.add_option("-q,--quality", config.quality, "Output quality (1-100)")
            ->check(CLI::Range(1, 100));

    // Parse command line
    try {
        app.parse(argc, argv);
    } catch (const CLI::ParseError &e) {
        return app.exit(e);
    }

    // Load YAML config if specified
    if (!config_path.empty()) {
        try {
            load_yaml_config(config_path, config);
        } catch (const std::exception &e) {
            fmt::print(stderr, "Error loading config file: {}\n", e.what());
            return 1;
        }
    }

    // Print configuration if verbose
    if (config.verbose) {
        print_config(config);
    }

    return 0;
}