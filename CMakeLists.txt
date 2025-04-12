cmake_minimum_required(VERSION 3.28)
project(c64-anim-tool VERSION 0.1.0 LANGUAGES CXX C)

# Set C++20 as the standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build type configuration
if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Build type" FORCE)
endif ()
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

# Options for the build
option(ENABLE_SANITIZERS "Enable address and undefined behavior sanitizers" OFF)
option(BUILD_TESTING "Enable test targets" ON)
option(USE_STATIC_LINKAGE "Prefer static linkage" ON)
option(BUILD_CLI "Build CLI application" ON)

# Set output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Handle macOS SDK paths
if (APPLE)
    # Get the currently active SDK path
    execute_process(
            COMMAND xcrun --show-sdk-path
            OUTPUT_VARIABLE MACOS_SDK_PATH
            OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    if (MACOS_SDK_PATH)
        message(STATUS "Using macOS SDK: ${MACOS_SDK_PATH}")
        set(CMAKE_OSX_SYSROOT ${MACOS_SDK_PATH})

        # Extract SDK version for information
        execute_process(
                COMMAND xcrun --show-sdk-version
                OUTPUT_VARIABLE MACOS_SDK_VERSION
                OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        message(STATUS "macOS SDK version: ${MACOS_SDK_VERSION}")
    else ()
        message(WARNING "Could not determine macOS SDK path")
    endif ()
endif ()

# Handle external library warnings
if (MSVC)
    # MSVC warnings as errors and level
    set(ANIMTOOL_WARNING_FLAGS /W4)
    set(EXTERNAL_WARNING_FLAGS /W0)
else ()
    # GCC/Clang warnings
    set(ANIMTOOL_WARNING_FLAGS -Wall -Wextra -Wpedantic)
    set(EXTERNAL_WARNING_FLAGS -w)
endif ()

# Configure compile options based on compiler
if (MSVC)
    # MSVC-specific options
    add_compile_options(${ANIMTOOL_WARNING_FLAGS})
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
else ()
    # GCC/Clang options
    add_compile_options(${ANIMTOOL_WARNING_FLAGS})

    # Add sanitizers if enabled (Clang preferred)
    if (ENABLE_SANITIZERS)
        if (CMAKE_CXX_COMPILER_ID MATCHES "Clang")
            message(STATUS "Enabling sanitizers with Clang")
            add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
            add_link_options(-fsanitize=address,undefined)
        elseif (CMAKE_CXX_COMPILER_ID MATCHES "GNU")
            message(STATUS "Enabling sanitizers with GCC (Clang preferred)")
            add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
            add_link_options(-fsanitize=address,undefined)
        else ()
            message(WARNING "Sanitizers requested but not supported by the compiler")
        endif ()
    endif ()

    # Ensure static linking on Linux
    if (UNIX AND NOT APPLE AND USE_STATIC_LINKAGE)
        message(STATUS "Setting up static linking for Linux")
        add_link_options(-static-libgcc -static-libstdc++)
    endif ()
endif ()

if (TARGET yaml-cpp)
    target_compile_options(yaml-cpp PRIVATE ${EXTERNAL_WARNING_FLAGS})
endif ()

if (TARGET fmt)
    target_compile_options(fmt PRIVATE ${EXTERNAL_WARNING_FLAGS})
endif ()

# Add external dependencies
include(FetchContent)

# Fetch CLI11
FetchContent_Declare(
        cli11
        GIT_REPOSITORY https://github.com/CLIUtils/CLI11
        GIT_TAG v2.5.0
)
FetchContent_MakeAvailable(cli11)

# Fetch yaml-cpp
FetchContent_Declare(
        yaml-cpp
        GIT_REPOSITORY https://github.com/jbeder/yaml-cpp.git
        GIT_TAG yaml-cpp-0.7.0
)
# Ensure yaml-cpp is built statically
set(YAML_CPP_BUILD_TESTS OFF CACHE BOOL "Disable yaml-cpp tests")
set(YAML_CPP_BUILD_TOOLS OFF CACHE BOOL "Disable yaml-cpp tools")
set(YAML_BUILD_SHARED_LIBS OFF CACHE BOOL "Build yaml-cpp statically")
FetchContent_MakeAvailable(yaml-cpp)

# Fetch {fmt} library
FetchContent_Declare(
        fmt
        GIT_REPOSITORY https://github.com/fmtlib/fmt.git
        GIT_TAG 11.1.4
)
FetchContent_MakeAvailable(fmt)

# Fetch giflib
FetchContent_Declare(
        giflib
        URL https://sourceforge.net/projects/giflib/files/giflib-5.2.1.tar.gz
        URL_HASH SHA256=31da5562f44c5f15d63340a09a4fd62b48c45620cd302f77a6d9acf0077879bd
)

set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build giflib statically")
FetchContent_GetProperties(giflib)
if (NOT giflib_POPULATED)
    FetchContent_Populate(giflib)

    file(GLOB GIFLIB_SOURCES ${giflib_SOURCE_DIR}/*.c)

    add_library(giflib STATIC ${GIFLIB_SOURCES})

    target_include_directories(giflib PUBLIC
            ${giflib_SOURCE_DIR}
    )

    target_compile_options(giflib PRIVATE ${EXTERNAL_WARNING_FLAGS})
endif ()


# Anim stuffs
add_library(anim_lib
        src/anim/CharsetReader.cpp
        src/anim/PetsciiReader.cpp
        src/config/config.cpp
        src/anim/AnimSourceData.cpp
        src/anim/CharsetReader.cpp
        src/anim/CharsetReader.h
        src/anim/GifReader.cpp
        src/anim/GifReader.h
        src/anim/Defer.h
        # src/anim/ChannelCharacterRam.cpp
        # src/anim/ChannelScreenColor.cpp
        # src/anim/ChannelColorRAM.cpp
        # src/anim/ChannelColorAnimation.cpp
        # src/anim/ChannelScrollFullScreen.cpp
        # src/anim/ChannelSprite.cpp
)

target_include_directories(anim_lib PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(anim_lib PUBLIC
        fmt::fmt
        yaml-cpp
        giflib
)

if (BUILD_CLI)
    add_executable(c64-anim-tool
            src/cli/main.cpp
    )

    target_link_libraries(c64-anim-tool PRIVATE
            anim_lib
            CLI11::CLI11
            fmt::fmt
    )
endif ()

if (BUILD_TESTING)
    # Fetch Catch2
    FetchContent_Declare(
            catch2
            GIT_REPOSITORY https://github.com/catchorg/Catch2.git
            GIT_TAG v3.4.0
    )
    FetchContent_MakeAvailable(catch2)

    # Enable testing with CTest
    enable_testing()
    include(CTest)
    include(${catch2_SOURCE_DIR}/extras/Catch.cmake)

    # Config module tests
    add_executable(config_tests
            src/config/test/test_config.cpp
    )
    target_link_libraries(config_tests PRIVATE
            Catch2::Catch2WithMain
    )
    catch_discover_tests(config_tests)

    # CLI module tests
    add_executable(cli_tests
            src/cli/test/test_cli.cpp
    )
    target_link_libraries(cli_tests PRIVATE
            anim_lib
            CLI11::CLI11
            Catch2::Catch2WithMain
    )
    catch_discover_tests(cli_tests)

    # Combined test suite for CI/CD
    add_executable(all_tests
            src/config/test/test_config.cpp
            src/cli/test/test_cli.cpp
    )
    target_link_libraries(all_tests PRIVATE
            anim_lib
            CLI11::CLI11
            Catch2::Catch2WithMain
    )
    catch_discover_tests(all_tests)
endif ()