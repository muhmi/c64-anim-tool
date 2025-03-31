cmake_minimum_required(VERSION 3.28)
project(c64-anim-tool VERSION 0.1.0 LANGUAGES CXX)

# Set C++20 as the standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build type configuration
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Build type" FORCE)
endif()
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
if(APPLE)
  # Get the currently active SDK path
  execute_process(
          COMMAND xcrun --show-sdk-path
          OUTPUT_VARIABLE MACOS_SDK_PATH
          OUTPUT_STRIP_TRAILING_WHITESPACE
  )

  if(MACOS_SDK_PATH)
    message(STATUS "Using macOS SDK: ${MACOS_SDK_PATH}")
    set(CMAKE_OSX_SYSROOT ${MACOS_SDK_PATH})

    # Extract SDK version for information
    execute_process(
            COMMAND xcrun --show-sdk-version
            OUTPUT_VARIABLE MACOS_SDK_VERSION
            OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    message(STATUS "macOS SDK version: ${MACOS_SDK_VERSION}")
  else()
    message(WARNING "Could not determine macOS SDK path")
  endif()
endif()

# Configure compile options based on compiler
if(MSVC)
  # MSVC-specific options
  add_compile_options(/W4 /MP)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
else()
  # GCC/Clang options
  add_compile_options(-Wall -Wextra -Wpedantic)
  
  # Add sanitizers if enabled (Clang preferred)
  if(ENABLE_SANITIZERS)
    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
      message(STATUS "Enabling sanitizers with Clang")
      add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
      add_link_options(-fsanitize=address,undefined)
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
      message(STATUS "Enabling sanitizers with GCC (Clang preferred)")
      add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
      add_link_options(-fsanitize=address,undefined)
    else()
      message(WARNING "Sanitizers requested but not supported by the compiler")
    endif()
  endif()
  
  # Ensure static linking on Linux
  if(UNIX AND NOT APPLE AND USE_STATIC_LINKAGE)
    message(STATUS "Setting up static linking for Linux")
    add_link_options(-static-libgcc -static-libstdc++)
  endif()
endif()

# Add external dependencies
include(FetchContent)

# Fetch CLI11
FetchContent_Declare(
  cli11
  GIT_REPOSITORY https://github.com/CLIUtils/CLI11
  GIT_TAG v2.3.2
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

# Add a target for stb headers
add_library(stb INTERFACE)
target_include_directories(stb INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/src/third_party/stb)

# Create the core GIF library
add_library(gif_lib
  src/gif/gif_processor.cpp
  src/gif/stb_impl.cpp # This file needs to be created with proper impl
)

target_include_directories(gif_lib PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/src  # Makes "gif/gif_processor.h" work
)

target_link_libraries(gif_lib PUBLIC
  stb
  yaml-cpp
)

# Create the config library
add_library(config_lib
  src/config/config.cpp
)

target_include_directories(config_lib PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/src  # Makes "config/config.h" work
)

target_link_libraries(config_lib PUBLIC
  yaml-cpp
)

# Create the CLI executable if requested
if(BUILD_CLI)
  add_executable(c64-anim-tool
    src/cli/main.cpp
  )
  
  target_link_libraries(c64-anim-tool PRIVATE
    gif_lib
    config_lib
    CLI11::CLI11
  )
endif()

# Testing setup
if(BUILD_TESTING)
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
    config_lib
    Catch2::Catch2WithMain
  )
  
  catch_discover_tests(config_tests)
  
  # GIF module tests
  add_executable(gif_tests
    src/gif/test/test_gif_processor.cpp
  )
  
  target_link_libraries(gif_tests PRIVATE
    gif_lib
    Catch2::Catch2WithMain
  )
  
  catch_discover_tests(gif_tests)
  
  # Combined test suite for CI/CD
  add_executable(all_tests
    src/config/test/test_config.cpp
    src/gif/test/test_gif_processor.cpp
  )
  
  target_link_libraries(all_tests PRIVATE
    gif_lib
    config_lib
    Catch2::Catch2WithMain
  )
  
  catch_discover_tests(all_tests)
endif()