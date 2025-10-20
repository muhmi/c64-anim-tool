# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

C64 Animation Tool - A Python-based tool for converting PNG/GIF animations to Commodore 64 PETSCII format with charset generation and compression. The tool generates .prg files that can run on C64 emulators or real hardware.

## Core Architecture

### Processing Pipeline

The animation conversion follows this flow:
1. **Input Processing** (`petscii.py`): Reads PNG/GIF files or .c PETSCII files, extracts frames
2. **Charset Generation** (`petscii.py`): Either uses provided charset or generates charsets from image data using Hamming distance algorithms for character similarity
3. **Frame Optimization** (`anim_reorder.py`): Optionally reorders frames to group similar charsets together for better compression
4. **Packing** (`packer.py`): Compresses animation data using block-based delta compression with RLE encoding
5. **Code Generation** (`packer.py` + Jinja2 templates): Generates 6502 assembly code for playback
6. **Assembly** (`build_utils.py`): Uses 64tass assembler to create final .prg file

### Key Modules

- **`main.py`**: Entry point, orchestrates the pipeline
- **`cli_parser.py`**: Handles all command-line arguments and YAML config parsing
- **`petscii.py`**: Core PETSCII and charset manipulation, including character distance calculations using lookup tables for performance
- **`packer.py`**: Animation compression engine using configurable block sizes (2x2 to 4x5) and macro blocks. Tests multiple block sizes to find optimal compression
- **`packer_config.py`**: Configures packer options based on CLI args
- **`compress.py`**: RLE and other compression utilities
- **`color_data_utils.py`**: Color memory manipulation (offset, randomize)
- **`anim_reorder.py`**: Frame reordering for compression optimization
- **`scroller.py`**: Scroll animation detection and handling
- **`build_utils.py`**: Wrapper for 64tass assembler execution

### Code Generation

The tool uses Jinja2 templates in `src/resources/test-program/` to generate 6502 assembly:
- **`player_test_setup.asm`**: Standard double-buffered player (default)
- **`player_50fps_test.asm`**: Fast 50fps single-buffered player
- **`player.asm`**: Core playback routines
- **`fill_color_template.asm`**: Color memory effects

Templates are populated with:
- Block operation opcodes
- Charset data
- Animation stream data
- Configuration (screen dimensions, timing, colors)

### Platform-Specific Binaries

The tool includes 64tass assembler binaries for all platforms in `bins/`:
- `bins/linux/64tass`
- `bins/macos/64tass`
- `bins/windows/64tass.exe`

These are bundled into standalone executables via Nuitka/PyInstaller.

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install development tools (Black, Ruff)
make install-dev-tools
```

### Code Quality
```bash
# Format code
make format-python  # or: make format

# Lint code
make lint-python    # or: make lint

# Check formatting (CI-friendly, no auto-fix)
make check-format

# Run all CI checks
make ci-check
```

### Building Executables
```bash
# Build with Nuitka (optimized, recommended)
make distribute

# Build with Nuitka (fast build, no optimization)
make distribute-fast

# Build with Nuitka (debug symbols)
make distribute-debug

# Fallback: Build with PyInstaller
make distribute-pyinstaller

# Clean build artifacts
make clean
```

### Running the Tool

#### During Development (from source)
```bash
# Direct Python execution
PYTHONPATH=src python src/animation_converter/main.py --help

# With config file
PYTHONPATH=src python src/animation_converter/main.py --config test-data/cubeloop/cubeloop5.yaml
```

#### After Building
```bash
# Use the compiled binary
./dist/animation-tool --help
./dist/animation-tool --config test-data/cubeloop/cubeloop5.yaml
```

### Testing During Development
```bash
# Test a simple GIF conversion with charset limiting
PYTHONPATH=src python src/animation_converter/main.py test-data/sklbunny-nodding-reissue.gif --limit-charsets=5

# Test with PETSCII file and custom charset
PYTHONPATH=src python src/animation_converter/main.py test-data/cubez/cubez-24.c \
    --use-color \
    --anim-slowdown-frames=5 \
    --offset-color-frames=2 \
    --charset=test-data/cubez/cubez-chars-charset.64c
```

## Configuration

### YAML Config Files

Config files use snake_case (not dashes). Example:
```yaml
input_files:
  - animation.gif
anim_slowdown_frames: 10
color_animation: ./warning.c
use_color: true
fast_mode: true
per_row_mode: true
```

Path resolution order:
1. Relative to config file
2. Relative to tool directory
3. Relative to current working directory

### Common Options

- `--limit-charsets N`: Compress characters to N charsets (must be >1)
- `--use-color`: Enable color memory animation
- `--fast-mode`: Generate 50fps single-buffered player (no double buffering)
- `--per-row-mode`: Use per-row delta packing mode
- `--scroll [up|down|left|right]`: Enable scroll animation
- `--skip-build`: Skip .prg assembly (useful for debugging generated .asm)
- `--output-sources DIR`: Copy generated sources to directory
- `--write-petmate`: Export to Petmate format

## Code Style

This project uses:
- **Black** for code formatting (line-length: 88)
- **Ruff** for linting with these enabled rules:
  - pycodestyle (E, W)
  - Pyflakes (F)
  - isort (I)
  - flake8-bugbear (B)
  - flake8-comprehensions (C4)
  - pyupgrade (UP)
  - flake8-unused-arguments (ARG)
  - flake8-simplify (SIM)
  - flake8-pie (PIE)
  - Pylint (PL) - with some complexity rules disabled
  - Ruff-specific rules (RUF)

Ignored rules (see `pyproject.toml`):
- E501 (line length - handled by Black)
- PLR0913, PLR0912, PLR0915 (complexity metrics)
- PLW0603 (global statement - used intentionally for lookup tables)

## CI/CD

GitHub Actions workflow (`.github/workflows/build_executables.yaml`):
1. **Code Quality Check**: Runs Black and Ruff on all platforms
2. **Multi-platform Build**: Builds executables for Linux, macOS, Windows using Nuitka
3. **Release Creation**: Creates GitHub release with platform-specific zip files

Builds are triggered on:
- Push to main branch
- Manual workflow dispatch

## Performance Optimizations

### Hamming Distance Lookup Table
`petscii.py` uses a pre-calculated lookup table for byte Hamming distances (256x256 table) to speed up character similarity calculations. The table is initialized once globally and reused across all comparisons.

### Block Size Testing
The packer tests multiple block sizes (2x2, 2x3, 3x2, 3x3, 3x4, 4x3, 4x4, 4x5) in parallel to find the optimal compression ratio, then uses the winner for final output.

### Multiprocessing
The tool is multiprocessing-safe (`multiprocessing.freeze_support()` in main) for potential future parallelization.

## Output Structure

Generated files in `build/` directory:
- `anim.bin`: Compressed animation data
- `charset_N.bin`: Character set data (one per charset)
- `*.asm`: Generated 6502 assembly code
- `test.prg`: Final executable (if build succeeds)

## Important Notes

- The tool requires 64tass assembler binaries in `bins/` directory
- PETSCII files (.c format) require a charset (default: `src/resources/test-program/c64_charset.bin`)
- Music files (.prg) can be included in test builds via `--music` option
- The packer skips 2x2 block size when `--use-color` is enabled
- Frame reordering (`--allow-reorder-frames`) can improve compression but changes playback order
