@echo off
REM Simple script to download STB header files for Windows

REM Create the directory structure
mkdir src\third_party\stb 2>nul

REM Download the necessary STB headers
echo Downloading stb_image.h...
curl -s -o src\third_party\stb\stb_image.h https://raw.githubusercontent.com/nothings/stb/master/stb_image.h

echo Downloading stb_image_write.h...
curl -s -o src\third_party\stb\stb_image_write.h https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h

echo STB headers downloaded successfully to src\third_party\stb\