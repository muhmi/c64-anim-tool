# src/animation_converter/gui/__init__.py
"""
GUI package for C64 Animation Tool.
Optional - only loaded when running without CLI arguments.
"""

from .app import main as run_gui

__all__ = ["run_gui"]
