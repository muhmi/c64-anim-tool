"""
Logging module for C64 Animation Tool.

Provides colored console output using colorama and standard Python logging.
Designed to be easily integrated with GUI applications later.
"""

import logging
import sys
from typing import ClassVar, Optional

from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colorama colors based on log level.

    Colors:
    - DEBUG: Cyan
    - INFO: No color (default)
    - SUCCESS: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bright Red
    """

    LEVEL_COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": Fore.CYAN,
        "INFO": "",  # No color for regular info messages
        "SUCCESS": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        """Format the log record with appropriate color"""
        # Save original values
        original_levelname = record.levelname
        original_msg = record.msg

        # Get color for this level
        color = self.LEVEL_COLORS.get(record.levelname, "")

        # Apply color if available
        if color:
            record.msg = f"{color}{record.msg}{Style.RESET_ALL}"

        # Format the message
        formatted = super().format(record)

        # Restore original values (in case record is reused)
        record.levelname = original_levelname
        record.msg = original_msg

        return formatted


class AnimationToolLogger:
    """
    Custom logger wrapper for the C64 Animation Tool.

    This class wraps Python's standard logging module and provides:
    - Colored console output via colorama
    - Custom SUCCESS log level (between INFO and WARNING)
    - Easy configuration for verbosity levels
    - Simple interface for GUI integration later
    """

    # Custom log level between INFO (20) and WARNING (30)
    SUCCESS_LEVEL = 25

    def __init__(self, name: str = "animation_converter"):
        """
        Initialize the logger.

        Args:
            name: Logger name (default: "animation_converter")
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Capture all levels, filter at handler

        # Add custom SUCCESS level if not already added
        if not hasattr(logging, "SUCCESS"):
            logging.addLevelName(self.SUCCESS_LEVEL, "SUCCESS")

        # Default console handler
        self._console_handler: Optional[logging.Handler] = None
        self._file_handler: Optional[logging.Handler] = None

        # Setup default console output
        self.setup_console_handler(logging.INFO)

    def setup_console_handler(self, level: int = logging.INFO, colorized: bool = True):
        """
        Setup or replace the console handler.

        Args:
            level: Minimum log level to display (default: INFO)
            colorized: Use colored output (default: True)
        """
        # Remove existing console handler if present
        if self._console_handler:
            self.logger.removeHandler(self._console_handler)

        # Create new handler
        self._console_handler = logging.StreamHandler(sys.stdout)
        self._console_handler.setLevel(level)

        # Use colored formatter if requested
        if colorized:
            formatter = ColoredFormatter("%(message)s")
        else:
            formatter = logging.Formatter("%(message)s")

        self._console_handler.setFormatter(formatter)
        self.logger.addHandler(self._console_handler)

    def setup_file_handler(self, filepath: str, level: int = logging.DEBUG):
        """
        Add file logging.

        Args:
            filepath: Path to log file
            level: Minimum log level to write to file (default: DEBUG)
        """
        # Remove existing file handler if present
        if self._file_handler:
            self.logger.removeHandler(self._file_handler)

        # Create new file handler
        self._file_handler = logging.FileHandler(filepath, mode="w", encoding="utf-8")
        self._file_handler.setLevel(level)

        # File logs don't need color codes
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        self._file_handler.setFormatter(formatter)
        self.logger.addHandler(self._file_handler)

    def add_handler(self, handler: logging.Handler):
        """
        Add a custom handler (useful for GUI integration).

        Args:
            handler: Custom logging.Handler instance
        """
        self.logger.addHandler(handler)

    def set_level(self, level: int):
        """
        Set the console output level.

        Args:
            level: Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if self._console_handler:
            self._console_handler.setLevel(level)

    # Convenience methods matching logging API

    def debug(self, msg, *args, **kwargs):
        """Log a debug message"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log an info message"""
        self.logger.info(msg, *args, **kwargs)

    def success(self, msg, *args, **kwargs):
        """Log a success message (green)"""
        self.logger.log(self.SUCCESS_LEVEL, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log a warning message"""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log an error message"""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log a critical error message"""
        self.logger.critical(msg, *args, **kwargs)


# Global logger instance for convenience
_global_logger: Optional[AnimationToolLogger] = None


def get_logger() -> AnimationToolLogger:
    """
    Get the global logger instance.

    Returns:
        AnimationToolLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = AnimationToolLogger()
    return _global_logger


def setup_logging(
    verbose: bool = False, quiet: bool = False, log_file: Optional[str] = None
):
    """
    Configure logging based on verbosity flags.

    This is the main function to call from CLI argument parsing.

    Args:
        verbose: Enable verbose (DEBUG) output
        quiet: Suppress all output except errors
        log_file: Optional path to log file
    """
    logger = get_logger()

    # Determine log level
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Setup console handler
    logger.setup_console_handler(level=level, colorized=True)

    # Setup file handler if requested
    if log_file:
        logger.setup_file_handler(log_file)


# Convenience module-level functions for simple usage
logger = get_logger()
debug = logger.debug
info = logger.info
success = logger.success
warning = logger.warning
error = logger.error
critical = logger.critical
