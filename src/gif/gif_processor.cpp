#include "gif/gif_processor.h"
#include <stdexcept>
#include <iostream>

// Include stb headers - actual implementations are in stb_impl.cpp
#include "third_party/stb/stb_image.h"
#include "third_party/stb/stb_image_write.h"

GifProcessor::GifProcessor(const AppConfig& config)
    : config_(config) 
{
    if (config_.input_file.empty()) {
        throw std::runtime_error("No input file specified");
    }
    
    if (config_.output_file.empty()) {
        // Default to input filename with '_processed' suffix
        size_t dot_pos = config_.input_file.find_last_of('.');
        if (dot_pos != std::string::npos) {
            config_.output_file = config_.input_file.substr(0, dot_pos) + 
                                "_processed" + 
                                config_.input_file.substr(dot_pos);
        } else {
            config_.output_file = config_.input_file + "_processed";
        }
    }
}

void GifProcessor::process() {
    // Load the input image
    loadImage(config_.input_file);
    
    if (config_.verbose) {
        std::cout << "Loaded image: " << width_ << "x" << height_ 
                  << " with " << channels_ << " channels" << std::endl;
    }
    
    // Process the image
    performProcessing();
    
    // Save the result
    saveImage(config_.output_file);
    
    if (config_.verbose) {
        std::cout << "Saved processed image to: " << config_.output_file << std::endl;
    }
}

void GifProcessor::loadImage(const std::string& filename) {
    // Free previous image data if any
    if (!image_data_.empty()) {
        image_data_.clear();
    }
    
    // Load the image using stb_image
    unsigned char* data = stbi_load(
        filename.c_str(),
        &width_,
        &height_,
        &channels_,
        0  // Load as-is, without forcing a specific number of channels
    );
    
    if (!data) {
        throw std::runtime_error("Failed to load image: " + 
                                std::string(stbi_failure_reason()));
    }
    
    // Copy data to our vector and free the original
    size_t data_size = width_ * height_ * channels_;
    image_data_.assign(data, data + data_size);
    
    // Free the original data
    stbi_image_free(data);
}

void GifProcessor::saveImage(const std::string& filename) {
    if (image_data_.empty()) {
        throw std::runtime_error("No image data to save");
    }
    
    int result = 0;
    
    // Determine file type from extension
    std::string ext = filename.substr(filename.find_last_of('.') + 1);
    
    // Convert to lowercase
    for (auto& c : ext) {
        c = std::tolower(c);
    }
    
    // Save based on file extension
    if (ext == "jpg" || ext == "jpeg") {
        result = stbi_write_jpg(
            filename.c_str(),
            width_,
            height_,
            channels_,
            image_data_.data(),
            config_.quality  // Use quality setting from config
        );
    } else if (ext == "png") {
        result = stbi_write_png(
            filename.c_str(),
            width_,
            height_,
            channels_,
            image_data_.data(),
            width_ * channels_  // Stride in bytes
        );
    } else if (ext == "bmp") {
        result = stbi_write_bmp(
            filename.c_str(),
            width_,
            height_,
            channels_,
            image_data_.data()
        );
    } else {
        throw std::runtime_error("Unsupported output format: " + ext);
    }
    
    if (!result) {
        throw std::runtime_error("Failed to save image to: " + filename);
    }
}

void GifProcessor::performProcessing() {
    // TODO: Implement your image processing operations here
    // This is just a placeholder that inverts the image
    
    if (config_.verbose) {
        std::cout << "Performing image processing..." << std::endl;
    }
    
    // Simple example: invert the image
    for (auto& pixel : image_data_) {
        pixel = 255 - pixel;
    }
}