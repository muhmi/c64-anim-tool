"""
Logging configuration for GUI
"""

import logging
import tkinter as tk
from tkinter import scrolledtext
from ttkbootstrap.constants import DISABLED, NORMAL, END


class TextHandler(logging.Handler):
    """Logging handler that writes to a text widget"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state=NORMAL)
        self.text_widget.insert(END, msg + "\n")
        self.text_widget.configure(state=DISABLED)
        self.text_widget.see(END)


def setup_logging():
    """Setup logging for the application"""
    logger = logging.getLogger("animation_tool")
    logger.setLevel(logging.INFO)

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)

    return logger


def add_gui_logging_handler(logger, text_widget):
    """Add GUI text widget handler to logger"""
    handler = TextHandler(text_widget)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
