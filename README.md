## Animation tool

Small & crappy animation tool extracted from stereo demo by phonics.

## Installation

1. Download the latest build:
   [MacOS](https://github.com/muhmi/c64-anim-tool/actions/artifacts/latest?query=workflow%3A%22Build+Executables%22+branch%3Amain+event%3Apush+animation-tool-ubuntu-latest)
   [Linux](https://github.com/muhmi/c64-anim-tool/actions/artifacts/latest?query=workflow%3A%22Build+Executables%22+branch%3Amain+event%3Apush+animation-tool-ubuntu-latest)
3. On macos you need to run `xattr -d com.apple.quarantine ~/Downloads/animation-tool` (in terminal)
4. Copy the binary somewhere

## Usage

Run `animation-tool --help` to get a list of options:
```bash
$ animation-tool --help
Convert PNG/GIF to C64 PETSCII + charset.

positional arguments:
  input_files           Input .c, PNG or GIF files.

options:
  -h, --help            show this help message and exit
  --charset CHARSET     Use this charset instead (.64c or .bin)
  --color-data COLOR_DATA
                        Use this file as source for color data
  --use-color           Animate color data
  --limit-charsets LIMIT_CHARSETS
                        Try to limit amount of charsets to this number, must be over 1
  --start-threshold START_THRESHOLD
                        When limiting charsets use this threshold value for closeness of characters at start (1 to 7)
  --border-color BORDER_COLOR
                        Use this border color
  --background-color BACKGROUND_COLOR
                        Assume image background is this color
  --anim-slowdown-frames ANIM_SLOWDOWN_FRAMES
                        Slowdown test animation by given frames
  --mode {petscii,animation}
                        Conversion mode: 'petscii' or 'animation'. Default is 'petscii'.
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

