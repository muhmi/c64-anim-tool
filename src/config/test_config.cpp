#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>
#include <fstream>
#include <string>
#include <filesystem>

#include "config/config.h"

// Create a temporary YAML file for testing
std::string createTempYamlFile(const std::string& content) {
    std::filesystem::path temp_dir = std::filesystem::temp_directory_path();
    std::string filename = (temp_dir / "test_config.yaml").string();
    
    std::ofstream file(filename);
    file << content;
    file.close();
    
    return filename;
}

TEST_CASE("Config parsing from YAML", "[config]") {
    SECTION("Basic configuration parsing") {
        std::string yaml_content = R"(
input_file: test_input.gif
output_file: test_output.gif
verbose: true
quality: 85
include_paths:
  - path1
  - path2
)";

        std::string yaml_file = createTempYamlFile(yaml_content);
        
        AppConfig config;
        load_yaml_config(yaml_file, config);
        
        REQUIRE(config.input_file == "test_input.gif");
        REQUIRE(config.output_file == "test_output.gif");
        REQUIRE(config.verbose == true);
        REQUIRE(config.quality == 85);
        REQUIRE(config.include_paths.size() == 2);
        REQUIRE(config.include_paths[0] == "path1");
        REQUIRE(config.include_paths[1] == "path2");
        
        // Clean up
        std::filesystem::remove(yaml_file);
    }
    
    SECTION("Partial configuration with defaults") {
        std::string yaml_content = R"(
input_file: partial_test.gif
# output_file is intentionally omitted
quality: 50
)";

        std::string yaml_file = createTempYamlFile(yaml_content);
        
        AppConfig config;
        // Set some defaults before loading
        config.verbose = false;
        config.quality = 100;
        
        load_yaml_config(yaml_file, config);
        
        REQUIRE(config.input_file == "partial_test.gif");
        REQUIRE(config.output_file == ""); // Not set in YAML
        REQUIRE(config.verbose == false);  // Should keep default
        REQUIRE(config.quality == 50);     // Should be overridden
        
        // Clean up
        std::filesystem::remove(yaml_file);
    }
    
    SECTION("Invalid YAML file") {
        std::string yaml_content = R"(
input_file: "unclosed string
quality: not-a-number
)";

        std::string yaml_file = createTempYamlFile(yaml_content);
        
        AppConfig config;
        
        REQUIRE_THROWS_AS(load_yaml_config(yaml_file, config), std::runtime_error);
        
        // Clean up
        std::filesystem::remove(yaml_file);
    }
}