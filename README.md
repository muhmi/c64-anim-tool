# c64-anim-tool

Tool for processing gifs/petcii animations to be used in C64 demos

## Building

### Prerequisites

- CMake 3.25 or higher
- C++20 compatible compiler (GCC 10+, Clang 10+, MSVC 2019+)
- Git (for fetching dependencies)

### Building with CMake Presets

The project includes CMake presets for different build configurations:

```bash
# List available presets
cmake --list-presets

# Configure using debug preset
cmake --preset=debug

# Build using debug preset
cmake --build --preset=debug

# Run tests
ctest --preset=all-tests
```

### Available Presets

- **debug**: Debug build of the CLI application
- **release**: Optimized release build of the CLI
- **clang-sanitizer**: Debug build with Clang sanitizers enabled
- **all-tests**: Build only the test executables
- **all-debug**: Complete build with both CLI and tests


## Project Structure

```
c64-anim-tool/
├── CMakeLists.txt         # Main build configuration
├── CMakePresets.json      # Build presets
├── src/
│   ├── cli/               # Command line interface
│   │   ├── main.cpp
│   │   └── test/
│   ├── config/            # Configuration handling
│   │   ├── config.cpp
│   │   ├── config.h
│   │   └── test/
│   ├── gif/               # GIF processing
│   │   ├── gif_processor.cpp
│   │   ├── gif_processor.h
│   │   ├── stb_impl.cpp
│   │   └── test/
│   └── third_party/       # External dependencies
│       └── stb/           # STB image libraries
└── build/                 # Build directory (created by build process)
```

## Dependencies

The project automatically fetches and configures the following dependencies:

- [CLI11](https://github.com/CLIUtils/CLI11): Command line parser
- [yaml-cpp](https://github.com/jbeder/yaml-cpp): YAML parser
- [Catch2](https://github.com/catchorg/Catch2): Testing framework
- [stb](https://github.com/nothings/stb): Single-file image libraries (manually downloaded)

## License

This is public domain.