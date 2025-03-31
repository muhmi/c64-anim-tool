#include <catch2/catch_test_macros.hpp>
#include <filesystem>
#include <vector>
#include <cstdint>

#include "gif/gif_processor.h"

// Helper function to create a test image
void createTestImage(const std::string& filename, int width, int height) {
    // Create a simple BMP file for testing
    FILE* f = fopen(filename.c_str(), "wb");
    if (!f) {
        throw std::runtime_error("Failed to create test image file");
    }
    
    // BMP header (14 bytes)
    uint8_t bmp_header[14] = {
        'B', 'M',           // Signature
        0, 0, 0, 0,         // File size (filled in later)
        0, 0, 0, 0,         // Reserved
        54, 0, 0, 0         // Pixel data offset
    };
    
    // DIB header (40 bytes)
    uint8_t dib_header[40] = {
        40, 0, 0, 0,        // DIB header size
        0, 0, 0, 0,         // Width (filled in later)
        0, 0, 0, 0,         // Height (filled in later)
        1, 0,               // Color planes
        24, 0,              // Bits per pixel (24-bit RGB)
        0, 0, 0, 0,         // No compression
        0, 0, 0, 0,         // Image size (filled in later)
        0, 0, 0, 0,         // X pixels per meter
        0, 0, 0, 0,         // Y pixels per meter
        0, 0, 0, 0,         // Colors in palette
        0, 0, 0, 0          // Important colors
    };
    
    // Set width and height in DIB header
    dib_header[4] = width & 0xFF;
    dib_header[5] = (width >> 8) & 0xFF;
    dib_header[6] = (width >> 16) & 0xFF;
    dib_header[7] = (width >> 24) & 0xFF;
    
    dib_header[8] = height & 0xFF;
    dib_header[9] = (height >> 8) & 0xFF;
    dib_header[10] = (height >> 16) & 0xFF;
    dib_header[11] = (height >> 24) & 0xFF;
    
    // Row padding (BMP rows must be multiple of 4 bytes)
    int row_size = width * 3;
    int padding = (4 - (row_size % 4)) % 4;
    int data_size = (row_size + padding) * height;
    
    // Update file size in header
    uint32_t file_size = 54 + data_size;
    bmp_header[2] = file_size & 0xFF;
    bmp_header[3] = (file_size >> 8) & 0xFF;
    bmp_header[4] = (file_size >> 16) & 0xFF;
    bmp_header[5] = (file_size >> 24) & 0xFF;
    
    // Update image size in DIB header
    dib_header[20] = data_size & 0xFF;
    dib_header[21] = (data_size >> 8) & 0xFF;
    dib_header[22] = (data_size >> 16) & 0xFF;
    dib_header[23] = (data_size >> 24) & 0xFF;
    
    // Write headers
    fwrite(bmp_header, 1, 14, f);
    fwrite(dib_header, 1, 40, f);
    
    // Write pixel data (all white)
    std::vector<uint8_t> row(row_size + padding, 255);
    for (int i = 0; i < height; i++) {
        fwrite(row.data(), 1, row_size + padding, f);
    }
    
    fclose(f);
}

TEST_CASE("GifProcessor basic functionality", "[gif_processor]") {
    // Create temporary directory for test files
    std::filesystem::path temp_dir = std::filesystem::temp_directory_path();
    std::string test_input = (temp_dir / "test_input.bmp").string();
    std::string test_output = (temp_dir / "test_output.bmp").string();
    
    // Create a test image
    createTestImage(test_input, 10, 10);
    
    SECTION("Constructor sets output filename if not provided") {
        AppConfig config;
        config.input_file = test_input;
        // Intentionally leaving output_file empty
        
        GifProcessor processor(config);
        
        // Check that output file was automatically set
        REQUIRE(config.output_file == test_input + "_processed");
    }
    
    SECTION("Process function loads and saves image") {
        AppConfig config;
        config.input_file = test_input;
        config.output_file = test_output;
        
        GifProcessor processor(config);
        processor.process();
        
        // Check that output file exists
        REQUIRE(std::filesystem::exists(test_output));
    }
    
    SECTION("Constructor throws on empty input file") {
        AppConfig config;
        // Input file is intentionally empty
        
        REQUIRE_THROWS_AS(GifProcessor(config), std::runtime_error);
    }
    
    // Clean up test files
    std::filesystem::remove(test_input);
    std::filesystem::remove(test_output);
}