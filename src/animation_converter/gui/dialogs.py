"""
Dialog windows for GUI
"""

import sys
import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, YES, X, LEFT, RIGHT, W


class SettingsDialog(tk.Toplevel):
    """Settings dialog window"""

    def __init__(self, parent, settings):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("500x300")
        self.resizable(False, False)

        self.result = None
        self.settings = settings

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup settings UI"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # VICE emulator path
        vice_frame = ttk.LabelFrame(main_frame, text="VICE Emulator", padding=15)
        vice_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(vice_frame, text="Path to x64sc executable:").pack(
            anchor=W, pady=(0, 5)
        )

        path_frame = ttk.Frame(vice_frame)
        path_frame.pack(fill=X)

        self.vice_path_var = ttk.StringVar(value=self.settings.get("vice_path", ""))
        ttk.Entry(path_frame, textvariable=self.vice_path_var).pack(
            side=LEFT, fill=X, expand=YES, padx=(0, 5)
        )

        ttk.Button(path_frame, text="Browse", command=self.browse_vice, width=10).pack(
            side=RIGHT
        )

        # TODO: Add more settings here when needed
        # - Default project location
        # - Default export settings
        # - Theme selection

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=(20, 0))

        ttk.Button(
            btn_frame, text="Save", command=self.save, bootstyle="success", width=10
        ).pack(side=RIGHT, padx=(5, 0))

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.cancel,
            bootstyle="secondary",
            width=10,
        ).pack(side=RIGHT)

    def browse_vice(self):
        """Browse for VICE executable"""
        if sys.platform == "win32":
            filetypes = [("Executable", "*.exe"), ("All files", "*.*")]
        else:
            filetypes = [("All files", "*")]

        filename = filedialog.askopenfilename(
            title="Select VICE x64sc Executable", filetypes=filetypes
        )
        if filename:
            self.vice_path_var.set(filename)

    def save(self):
        """Save settings and close"""
        self.result = {"vice_path": self.vice_path_var.get()}
        self.destroy()

    def cancel(self):
        """Cancel and close"""
        self.destroy()
