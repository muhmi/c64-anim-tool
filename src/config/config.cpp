#include "config/config.h"
#include <yaml-cpp/yaml.h>
#include <iostream>
#include <stdexcept>

void load_yaml_config(const std::string& config_path, AppConfig& config) {
    try {
        YAML::Node yaml = YAML::LoadFile(config_path);
        
        // Parse YAML values with appropriate fallbacks
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
        
        // Handle array types
        if (yaml["include_paths"]) {
            config.include_paths.clear();
            for (const auto& path : yaml["include_paths"]) {
                config.include_paths.push_back(path.as<std::string>());
            }
        }
        
        // Add other configuration values here
        
    } catch (const YAML::Exception& e) {
        throw std::runtime_error(std::string("YAML parsing error: ") + e.what());
    }
}

void print_config(const AppConfig& config) {
    std::cout << "Configuration:" << std::endl;
    std::cout << "  Input file: " << config.input_file << std::endl;
    std::cout << "  Output file: " << config.output_file << std::endl;
    std::cout << "  Verbose: " << (config.verbose ? "yes" : "no") << std::endl;
    std::cout << "  Quality: " << config.quality << std::endl;
    
    std::cout << "  Include paths: ";
    if (config.include_paths.empty()) {
        std::cout << "none";
    } else {
        for (const auto& path : config.include_paths) {
            std::cout << path << " ";
        }
    }
    std::cout << std::endl;
}