#pragma once

#include "config/config.h"
#include <string>
#include <vector>

/**
 * GIF image processor class.
 * Handles loading, processing, and saving GIF images.
 */
class GifProcessor {
public:
    /**
     * Constructor.
     * 
     * @param config Application configuration
     */
    explicit GifProcessor(const AppConfig& config);
    
    /**
     * Process the GIF file according to configuration.
     * 
     * @throws std::runtime_error if processing fails
     */
    void process();
    
private:
    /**
     * Load image data from file.
     * 
     * @param filename File to load
     * @throws std::runtime_error if loading fails
     */
    void loadImage(const std::string& filename);
    
    /**
     * Save image data to file.
     * 
     * @param filename File to save to
     * @throws std::runtime_error if saving fails
     */
    void saveImage(const std::string& filename);
    
    /**
     * Perform image processing operations based on configuration.
     */
    void performProcessing();
    
    // Image data
    int width_ = 0;
    int height_ = 0;
    int channels_ = 0;
    std::vector<unsigned char> image_data_;
    
    AppConfig config_;
};