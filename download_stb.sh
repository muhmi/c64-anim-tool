#!/bin/bash
# Simple script to download STB header files

set -e

# Create the directory structure
mkdir -p src/third_party/stb

# Download the necessary STB headers
echo "Downloading stb_image.h..."
curl -s -o src/third_party/stb/stb_image.h https://raw.githubusercontent.com/nothings/stb/master/stb_image.h

echo "Downloading stb_image_write.h..."
curl -s -o src/third_party/stb/stb_image_write.h https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h

echo "STB headers downloaded successfully to src/third_party/stb/"