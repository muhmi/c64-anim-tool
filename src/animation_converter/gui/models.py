# src/animation_converter/gui/models.py
"""
Data models for GUI
"""

import logging
import os
import yaml
from pathlib import Path
from typing import Optional, List

from PIL import Image

from animation_converter.petscii import PetsciiScreen, read_screens, read_charset


logger = logging.getLogger("animation_tool")


class AnimationProject:
    """Represents a project - thin wrapper around config file"""

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path
        self.config = {}
        self.screens: List[PetsciiScreen] = []
        self.charsets = []
        self.current_frame_idx = 0

        if project_path and project_path.exists():
            self.load()

    def load(self):
        """Load project from YAML config"""
        from animation_converter.cli_parser import load_config_file, resolve_file_paths

        self.config = load_config_file(str(self.project_path))

        # Resolve paths relative to config
        config_dir = os.path.dirname(os.path.abspath(self.project_path))
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cwd = os.getcwd()

        self.config = resolve_file_paths(self.config, config_dir, script_dir, cwd)

    def save(self):
        """Save project config to YAML"""
        with open(self.project_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def process_frames(self):
        """Process input files to generate screens"""
        input_files = self.config.get("input_files", [])
        if isinstance(input_files, str):
            input_files = [input_files]

        if not input_files:
            logger.warning("No input files to process")
            return

        background_color = self.config.get("background_color")
        border_color = self.config.get("border_color")
        inverse = self.config.get("inverse", False)
        cleanup = self.config.get("cleanup", 1)

        # Get charset if specified
        default_charset = None
        charset_path = self.config.get("charset")
        if charset_path and os.path.exists(charset_path):
            skip_first_bytes = charset_path.endswith(".64c")
            logger.info(f"Reading charset from {charset_path}")
            default_charset = read_charset(charset_path, skip_first_bytes)
            logger.info(f"Loaded {len(default_charset)} characters")

        self.screens = []
        for input_file in input_files:
            if os.path.exists(input_file):
                logger.info(f"Processing {input_file}")
                screens = read_screens(
                    input_file,
                    charset=default_charset,
                    background_color=background_color,
                    border_color=border_color,
                    inverse=inverse,
                    cleanup=cleanup,
                )
                self.screens.extend(screens)
                logger.info(
                    f"Loaded {len(screens)} frames from {os.path.basename(input_file)}"
                )
            else:
                logger.warning(f"File not found: {input_file}")

    def get_frame(self, idx: int) -> Optional[PetsciiScreen]:
        """Get frame at index"""
        if 0 <= idx < len(self.screens):
            return self.screens[idx]
        return None

    def render_frame(self, idx: int, scale: int = 2) -> Optional[Image.Image]:
        """Render a frame as PIL Image"""
        screen = self.get_frame(idx)
        if screen:
            return screen.render(char_size=8 * scale, border=0)
        return None


class AppSettings:
    """Application settings (persisted to ~/.c64-anim-tool/settings.yaml)"""

    def __init__(self):
        self.settings_dir = Path.home() / ".c64-anim-tool"
        self.settings_file = self.settings_dir / "settings.yaml"
        self.data = self.load()

    def load(self):
        """Load settings from disk"""
        if self.settings_file.exists():
            with open(self.settings_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def save(self):
        """Save settings to disk"""
        self.settings_dir.mkdir(exist_ok=True)
        with open(self.settings_file, "w") as f:
            yaml.dump(self.data, f)

    def get(self, key, default=None):
        """Get setting value"""
        return self.data.get(key, default)

    def set(self, key, value):
        """Set setting value"""
        self.data[key] = value
        self.save()
