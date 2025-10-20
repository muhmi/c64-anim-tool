# C64 Animation Tool

Convert PNG/GIF animations to Commodore 64 PETSCII format with automatic charset generation and optimized compression. Creates runnable .prg files for C64 emulators and real hardware.

## Installation

1. Download the latest build from the [GitHub Actions artifacts](https://github.com/muhmi/c64-anim-tool/actions/workflows/build_executables.yaml)
2. Extract the archive for your platform (Linux, macOS, or Windows)
3. **macOS only**: Remove quarantine attribute: `xattr -d com.apple.quarantine ~/Downloads/animation-tool`
4. Move the binary to a location in your PATH or run it directly

## Quick Start

All commands require a config file. Here's a minimal example:

**config.yaml:**
```yaml
input_files:
  - animation.gif
limit_charsets: 5
```

**Run:**
```bash
animation-tool --config config.yaml
```

This generates `test.prg` which you can run in VICE or other C64 emulators.

## Configuration

The tool is **config-first** - you must provide a YAML config file with `--config`. Options can be specified in the config file (using `snake_case`) or overridden via command-line arguments (using `--dashed-names`).

### Config File Example

```yaml
# Input files (required - can be PNG, GIF, or .c PETSCII files)
input_files:
  - animation.gif
  - credits.c

# Charset generation
limit_charsets: 5              # Compress to max N charsets
charset: custom.64c            # Or use a predefined charset
cleanup: 4                     # Remove chars with <N pixels

# Performance mode
fast_mode: true                # 50fps single-buffered playback
per_row_mode: true             # Per-row delta compression

# Colors
use_color: true                # Animate color RAM
background_color: 0            # Black background
border_color: 0                # Black border

# Timing
anim_slowdown_frames: 2        # Wait N frames between animation frames

# Output
output_sources: build          # Copy generated .asm files here
skip_build: false              # Set true to only generate sources
```

**Path Resolution:** Paths in the config are resolved in order:
1. Relative to config file location
2. Relative to tool directory
3. Relative to current working directory

## Option Groups

### Input Options

| Option | Type | Description |
|--------|------|-------------|
| `input_files` | list | **Required in config or CLI.** PNG, GIF, or .c PETSCII files to process |
| `--charset` | path | Use predefined charset (.64c or .bin) instead of generating from images |
| `--background-color` | 0-15 | Assume this C64 color as image background |
| `--border-color` | 0-15 | Border color for test .prg (default: 0) |

### Charset Generation & Compression

| Option | Type | Description |
|--------|------|-------------|
| `--limit-charsets` | int | Compress characters to max N charsets (default: 4, must be >1) |
| `--cleanup` | int | Remove characters with fewer than N pixels (default: 1) |
| `--start-threshold` | 1-7 | Hamming distance threshold for charset merging (default: 2) |
| `--full-charsets` | bool | Force full 256-char charsets (may reduce quality) |
| `--allow-reorder-frames` | bool | Reorder frames to group similar charsets (improves compression) |

**How it works:** When processing GIFs/PNGs without `--charset`, the tool extracts unique characters and groups them into charsets. `--limit-charsets` uses Hamming distance to merge similar characters. Lower `--start-threshold` = more aggressive merging.

### Color Animation

| Option | Type | Description |
|--------|------|-------------|
| `--use-color` | bool | Enable color RAM animation (disables 2x2 block size) |
| `--color-data` | path | Use this file as source for color data frames |
| `--offset-color-frames` | int | Shift color frames by N (can be negative) |
| `--randomize-color-frames` | int | Randomize color timing (value = random seed) |
| `--init-color-between-anims` | bool | Clear color RAM between different input files |

**Color animation** requires `--use-color`. Use `--color-data` to apply colors from one animation to another. `--offset-color-frames` helps sync color changes with screen changes.

### Advanced Color Effects

| Option | Type | Description |
|--------|------|-------------|
| `--color-animation` | path | Generate animated color code from .c file's first frame |
| `--color-animation-palette` | colors | Color palette (comma-separated or image file) |
| `--color-animation-slowdown` | int | Slow down color animation |
| `--color-anim-min-seq-len` | int | Min consecutive offsets for loop optimization (default: 10) |
| `--color-anim-max-seq-len` | int | Max consecutive offsets for loop optimization (default: 10) |

**Color animation** generates 6502 code to animate specific screen positions through a color palette. Use `--color-animation-palette` to define colors (e.g., `1,2,3,4` or `palette.png`).

### Scroll Animation

| Option | Type | Description |
|--------|------|-------------|
| `--scroll` | direction | Enable scrolling: `up`, `down`, `left`, `right` |
| `--scroll-disable-repeat` | bool | Disable wrap-around for left/right scrolling |

**Scroll mode** creates a scrolling effect by modifying screen copies. Use `--scroll-disable-repeat` for left/right scrolling that doesn't loop.

### Chromatic Aberration Effect

| Option | Type | Description |
|--------|------|-------------|
| `--color-aberration-mode` | bool | Enable chromatic aberration effect (default: true) |
| `--color-aberration-colors` | colors | Background colors to cycle (default: 2,5,6) |
| `--color-aberration-scroll` | values | Horizontal scroll register values (default: 0,0,0) |

**When enabled, automatically sets:**
- `--inverse true` (inverted charset)
- `--disable-rle true` (RLE disabled)
- `--per-row-mode true` (per-row packing)
- Uses `player_50fps_test.asm` template

This creates a visual "glitch" effect by rapidly changing background colors and scroll registers.

### Performance & Playback

| Option | Type | Description |
|--------|------|-------------|
| `--fast-mode` | bool | 50fps single-buffered playback (no double buffering) - **single charset only** |
| `--per-row-mode` | bool | Use per-row delta packing (better for certain animations) |
| `--disable-rle` | bool | Disable RLE compression (larger but sometimes faster) |
| `--anim-slowdown-frames` | int | Wait N frames between animation frames (default: 0) |
| `--anim-slowdown-table` | values | Per-frame slowdown table (comma-separated) |

**Fast mode** uses `player_50fps_test.asm` template which:
- Writes directly to screen memory ($0400) without double buffering
- Only supports **single charset** animations (no charset switching)
- Does NOT support: scrolling, color animation effects, or double buffering
- Best for simple, high-speed animations with one charset

**Per-row mode** changes the packing algorithm to work row-by-row instead of block-based.

### Output & Build

| Option | Type | Description |
|--------|------|-------------|
| `--output-sources` | path | Copy generated .asm/.bin files to this directory |
| `--skip-build` | bool | Don't assemble .prg (useful for inspecting generated code) |
| `--write-petmate` | bool | Export animation to Petmate .petmate format |
| `--music` | path | Include music file in test.prg |

### Advanced Options

| Option | Type | Description |
|--------|------|-------------|
| `--effect-start-address` | hex | Effect load address (default: $3000) |
| `--anim-start-address` | hex | Animation data address (default: after charsets) |
| `--template-dir` | path | Custom directory for .asm templates |
| `--asm-test-runner-name` | name | Template file name (default: player_test_setup.asm) |
| `--inverse` | bool | Use inverted characters |
| `--non-linear-prg` | bool | Generate non-linear .prg format |

## Usage Examples

### Basic: Convert GIF to .prg

**config.yaml:**
```yaml
input_files:
  - bunny.gif
limit_charsets: 5
```

```bash
animation-tool --config config.yaml
```

Generates `test.prg` with up to 5 charsets.

### PETSCII Animation with Custom Charset

**config.yaml:**
```yaml
input_files:
  - animation.c
charset: custom-chars.64c
use_color: true
anim_slowdown_frames: 5
offset_color_frames: 2
```

Uses the provided charset and animates color RAM with timing adjustments.

### Simple Fast Animation

**config.yaml:**
```yaml
input_files:
  - simple-anim.gif
fast_mode: true
per_row_mode: true
cleanup: 4
charset: single-charset.64c  # Fast mode requires single charset
background_color: 0
```

50fps single-buffered animation. Note: fast mode only works with a single charset and doesn't support color animation or scrolling.

### Chromatic Aberration Effect

**config.yaml:**
```yaml
input_files:
  - demo.gif
color_aberration_mode: true
color_aberration_colors: 2,5,6,7
color_aberration_scroll: 4,0,2
music: soundtrack.prg
```

Creates a glitchy visual effect with custom colors and scroll wobble, plus music.

### Scrolling Animation

**config.yaml:**
```yaml
input_files:
  - scroller.c
scroll: left
scroll_disable_repeat: true
charset: font.64c
```

Left-scrolling text that doesn't wrap around.

### Color RAM Animation with Palette

**config.yaml:**
```yaml
input_files:
  - static-image.c
color_animation: color-positions.c
color_animation_palette: 1,15,12,11,0,11,12,15,1
color_animation_slowdown: 3
```

Animates specific screen positions through a custom color palette.

### Export for External Use

**config.yaml:**
```yaml
input_files:
  - animation.gif
limit_charsets: 3
output_sources: my-demo/assets
skip_build: true
```

Generates .asm and .bin files in `my-demo/assets/` without building .prg, useful for integrating into larger demo projects.

## Option Dependencies & Limitations

### Automatic Option Enabling

Some options automatically enable others:

- **`--color-aberration-mode`** → Sets `--inverse`, `--disable-rle`, `--per-row-mode`, uses `player_50fps_test.asm`
- **`--fast-mode`** → Uses `player_50fps_test.asm` (single-buffered)
- **`--use-color`** → Skips 2x2 block size during packing optimization
- **`--scroll`** → Requires direction: `up`, `down`, `left`, or `right`

### Fast Mode Limitations

The `--fast-mode` option uses `player_50fps_test.asm` which has significant limitations:

**Does NOT support:**
- Multiple charsets (only single charset animations)
- Double buffering (writes directly to $0400)
- Color animation effects (`--color-animation`)
- Standard color RAM animation (`--use-color`)
- Scroll effects (`--scroll`)
- Screen buffer copying

**Memory layout differences:**
- Standard mode: Uses double buffering with SCREEN1_LOCATION ($4400) and SCREEN2_LOCATION ($4800)
- Fast mode: Writes directly to UNPACK_BUFFER_LOCATION ($4400), displays at $0400

Use fast mode only for simple, single-charset animations where maximum frame rate is essential.

## Output Files

Generated in `build/` directory (unless `--output-sources` specified):

- **`test.prg`** - Runnable C64 program
- **`anim.bin`** - Compressed animation data
- **`charset_N.bin`** - Character set data (one per charset)
- **`*.asm`** - Generated 6502 assembly source

## Command-Line Reference

All config options can be overridden via command line:

```bash
animation-tool --config base.yaml \
  --use-color \
  --limit-charsets 3 \
  --anim-slowdown-frames 5 \
  --music soundtrack.prg \
  input_override.gif
```

Input files from command line take precedence over config. Other options: CLI args override config values.

## Troubleshooting

**"No input files specified"**
- Add `input_files: [file.gif]` to your config OR provide files as CLI arguments

**Too many charsets / animation too large**
- Increase `--limit-charsets` (but not too high - C64 has limited memory)
- Try `--cleanup` with higher value (4-6) to remove small details
- Use `--allow-reorder-frames` to improve compression
- Enable `--per-row-mode` for different compression characteristics

**Animation runs too fast/slow**
- Adjust `--anim-slowdown-frames` (higher = slower)
- Use `--fast-mode` for maximum frame rate
- Try `--anim-slowdown-table` for variable timing

**Colors don't match**
- Set `--background-color` to match your image's background
- Use `--color-data` to apply colors from another animation
- Try `--offset-color-frames` to sync color changes

## Development

See [CLAUDE.md](CLAUDE.md) for development setup, build instructions, and architecture details

