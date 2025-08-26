## Animation tool

Small & crappy animation tool extracted from stereo demo by phonics.

## Installation

1. Download the latest build from Artifacts section of the [latest build](https://github.com/muhmi/c64-anim-tool/actions/workflows/build_executables.yaml)
3. On macos you need to run `xattr -d com.apple.quarantine ~/Downloads/animation-tool` (in terminal)
4. Copy the binary somewhere

## Usage

Run `animation-tool --help` to get a list of options:
```bash
$ animation-tool --help
usage: animation-tool [-h] --config CONFIG [--charset CHARSET] [--cleanup CLEANUP] [--color-data COLOR_DATA] [--use-color] [--scroll SCROLL] [--scroll-disable-repeat]
                      [--limit-charsets LIMIT_CHARSETS] [--full-charsets] [--start-threshold START_THRESHOLD] [--border-color BORDER_COLOR] [--background-color BACKGROUND_COLOR]
                      [--anim-slowdown-frames ANIM_SLOWDOWN_FRAMES] [--anim-slowdown-table ANIM_SLOWDOWN_TABLE] [--offset-color-frames OFFSET_COLOR_FRAMES]
                      [--randomize-color-frames RANDOMIZE_COLOR_FRAMES] [--disable-rle DISABLE_RLE] [--inverse INVERSE] [--per-row-mode PER_ROW_MODE]
                      [--init-color-between-anims INIT_COLOR_BETWEEN_ANIMS] [--color-animation COLOR_ANIMATION] [--color-animation-slowdown COLOR_ANIMATION_SLOWDOWN]
                      [--color-anim-min-seq-len COLOR_ANIM_MIN_SEQ_LEN] [--color-anim-max-seq-len COLOR_ANIM_MAX_SEQ_LEN] [--color-animation-palette COLOR_ANIMATION_PALETTE] [--music MUSIC]
                      [--template-dir TEMPLATE_DIR] [--output-sources OUTPUT_SOURCES] [--allow-reorder-frames ALLOW_REORDER_FRAMES] [--non-linear-prg NON_LINEAR_PRG] [--skip-build SKIP_BUILD]
                      [--effect-start-address EFFECT_START_ADDRESS] [--anim-start-address ANIM_START_ADDRESS] [--write-petmate WRITE_PETMATE]
                      [input_files ...]

Convert PNG/GIF to C64 PETSCII + charset.

positional arguments:
  input_files           Input .c, PNG or GIF files (optional if defined in config)

options:
  -h, --help            show this help message and exit
  --config CONFIG       Path to config file (YAML) - required
  --charset CHARSET     Use this charset instead (.64c or .bin)
  --cleanup CLEANUP     Remove characters with under N pixels
  --color-data COLOR_DATA
                        Use this file as source for color data
  --use-color           Animate color data
  --scroll SCROLL       Scroll animation, needs direction: up,down,left,right
  --scroll-disable-repeat
                        Disable repeat for scroll animation, for left/right
  --limit-charsets LIMIT_CHARSETS
                        Try to limit amount of charsets to this number, must be over 1
  --full-charsets       Try to produce only full 256 char charsets, quality may suffer now
  --start-threshold START_THRESHOLD
                        When limiting charsets use this threshold value for closeness of characters at start (1 to 7)
  --border-color BORDER_COLOR
                        Use this border color
  --background-color BACKGROUND_COLOR
                        Assume image background is this color
  --anim-slowdown-frames ANIM_SLOWDOWN_FRAMES
                        Slowdown test animation by given frames
  --anim-slowdown-table ANIM_SLOWDOWN_TABLE
                        Slowdown test animation by given frames, using this table
  --offset-color-frames OFFSET_COLOR_FRAMES
                        Offset color frames by given value, can be negative
  --randomize-color-frames RANDOMIZE_COLOR_FRAMES
                        Randomize color frames, use given value as random seed
  --disable-rle DISABLE_RLE
                        Disable RLE encoder
  --inverse INVERSE     Inverse characters
  --per-row-mode PER_ROW_MODE
                        Per for delta packer mode
  --init-color-between-anims INIT_COLOR_BETWEEN_ANIMS
                        Write color memory to background color between different animation source files
  --color-animation COLOR_ANIMATION
                        Generate code to animate color data based on first frame of this .c file
  --color-animation-slowdown COLOR_ANIMATION_SLOWDOWN
                        Slowdown color animation
  --color-anim-min-seq-len COLOR_ANIM_MIN_SEQ_LEN
                        Minimum amount of consequent offsets to merge to a loop for color animation generated code
  --color-anim-max-seq-len COLOR_ANIM_MAX_SEQ_LEN
                        Max amount of consequent offsets to merge to a loop for color animation generated code
  --color-animation-palette COLOR_ANIMATION_PALETTE
                        Read color palette from a file for the color animation (if a file is given its assumed to be an image with first row being the palette)
  --music MUSIC         Include given file as music to test.prg, invalid file name leads to music being ignored.
  --template-dir TEMPLATE_DIR
                        Use this directory as source for templates
  --output-sources OUTPUT_SOURCES
                        Output sources to given folder
  --allow-reorder-frames ALLOW_REORDER_FRAMES
                        Allow reordering of frames so that frames with similar charsets are next to each other
  --non-linear-prg NON_LINEAR_PRG
                        Generate non-linear (mprg)
  --skip-build SKIP_BUILD
                        Dont try to build .prg
  --effect-start-address EFFECT_START_ADDRESS
                        Effect start address in hex
  --anim-start-address ANIM_START_ADDRESS
                        Set anim start address, defaults to after charsets
  --write-petmate WRITE_PETMATE
                        Write out a petmate file with petscii animation and charsets

```

### Generate .prg from GIF animation

```bash
animation-tool test-data/sklbunny-nodding-reissue.gif --limit-charsets=5
```
This will read the frames inside the GIF animation and generate charsets from it.
Using the limit charsets option the tool will try to pack the characters to 5 charsets.

The result will be named "test.prg".

### Use a petscii animation with defined charset

```bash
animation-tool test-data/cubez/cubez-24.c --use-color --anim-slowdown-frames=5 --offset-color-frames=2 --charset=test-data/cubez/cubez-chars-charset.64c
```

### Config file
Instead of giving all options directly on commandline you can provide a YAML file with options.
Example config:
```yaml
input_files:
  - credits.gif
anim_slowdown_frames: 10
color_animation: ./warning.c
color_animation_palette: 1,2,3,4,5,4,3,2,1
```
NOTE: The yaml file uses snake-case instead of "-".

The paths (detected by values containing /) are resolved by looking for the file:
- relative to config file
- relative to tool directory
- relative to current working directory

