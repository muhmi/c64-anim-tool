"""
Main application window for C64 Animation Tool
"""

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, YES, X, BOTTOM, HORIZONTAL

from animation_converter.petscii import write_petmate
from .models import AnimationProject, AppSettings
from .panels import ProjectPanel, PreviewPanel, LogPanel, StatsPanel
from .dialogs import SettingsDialog
from .logging_setup import setup_logging, add_gui_logging_handler


logger = logging.getLogger("animation_tool")


class C64AnimationToolGUI(ttk.Window):
    """Main application window"""

    def __init__(self):
        super().__init__(themename="darkly")

        self.title("C64 Animation Tool")
        self.geometry("1400x900")

        self.project = None
        self.settings = AppSettings()

        self.setup_ui()
        self.setup_menu()

        logger.info("C64 Animation Tool started")

    def setup_ui(self):
        """Setup main UI layout"""

        # Main container
        main_container = ttk.Frame(self, padding=10)
        main_container.pack(fill=BOTH, expand=YES)

        # Create paned window for resizable panels
        paned = ttk.PanedWindow(main_container, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=YES)

        # Left panel (project settings)
        self.project_panel = ProjectPanel(paned, self)
        paned.add(self.project_panel, weight=1)

        # Right side container
        right_container = ttk.Frame(paned)
        paned.add(right_container, weight=2)

        # Right panel (preview) - takes most space
        self.preview_panel = PreviewPanel(right_container, self)
        self.preview_panel.pack(fill=BOTH, expand=YES)

        # Stats panel - small area at bottom right
        self.stats_panel = StatsPanel(right_container, self)
        self.stats_panel.pack(fill=X, pady=(10, 0))

        # Log panel at very bottom
        self.log_panel = LogPanel(self)
        self.log_panel.pack(fill=X, side=BOTTOM, pady=(10, 0))

        # Connect logging to GUI
        add_gui_logging_handler(logger, self.log_panel.log_text)

        # Status bar
        self.setup_status_bar()

    def setup_menu(self):
        """Setup menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_status_bar(self):
        """Setup status bar at bottom"""
        status_frame = ttk.Frame(self, padding=(10, 5))
        status_frame.pack(fill=X, side=BOTTOM)

        self.status_label = ttk.Label(
            status_frame, text="Ready", bootstyle="inverse-secondary"
        )
        self.status_label.pack(side="left")

    def update_status(self, message: str, error: bool = False):
        """Update status bar"""
        self.status_label.config(
            text=message, bootstyle="inverse-danger" if error else "inverse-secondary"
        )

    def new_project(self):
        """Create new project"""
        folder = filedialog.askdirectory(title="Select Project Folder")
        if folder:
            config_path = Path(folder) / "config.yaml"
            self.project = AnimationProject(config_path)
            self.project.config = {"input_files": []}
            self.project.save()

            self.project_panel.project_path_var.set(str(config_path))
            self.project_panel.load_config_to_gui()

            self.update_status(f"Created project: {config_path}")
            logger.info(f"Created new project: {config_path}")

    def open_project(self):
        """Open existing project"""
        config_file = filedialog.askopenfilename(
            title="Select Project Config",
            filetypes=[("YAML Config", "*.yaml *.yml"), ("All files", "*.*")],
        )
        if config_file:
            self.project = AnimationProject(Path(config_file))
            self.project_panel.project_path_var.set(config_file)
            self.project_panel.load_config_to_gui()

            self.update_status(f"Opened project: {config_file}")
            logger.info(f"Opened project: {config_file}")

    def process_frames(self):
        """Process input files to generate frames"""
        if not self.project:
            messagebox.showwarning(
                "No Project", "Please open or create a project first"
            )
            return

        try:
            self.update_status("Processing frames...")
            logger.info("Starting frame processing...")

            self.project.process_frames()

            # Refresh frames list
            self.project_panel.refresh_frames_list()

            # Update stats
            self.stats_panel.update_stats()

            # Show first frame
            if self.project.screens:
                self.show_frame(0)

            self.update_status(f"Processed {len(self.project.screens)} frames")
            logger.info(
                f"Frame processing complete: {len(self.project.screens)} frames"
            )
        except Exception as e:
            error_msg = f"Failed to process frames: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.update_status("Error processing frames", error=True)
            logger.error(error_msg)

    def show_frame(self, idx: int):
        """Display frame in preview panel"""
        self.preview_panel.show_frame(idx)

    def export_prg(self):
        """Export to .prg file"""
        if not self.project or not self.project.screens:
            messagebox.showwarning("No Frames", "Process frames first")
            return

        # TODO: Implement PRG export by calling existing CLI pipeline
        logger.info("PRG export: TODO - will be implemented using existing CLI code")
        messagebox.showinfo("TODO", "PRG export will be implemented in next stage")

    def export_petmate(self):
        """Export to Petmate format"""
        if not self.project or not self.project.screens:
            messagebox.showwarning("No Frames", "Process frames first")
            return

        output_file = filedialog.asksaveasfilename(
            title="Save Petmate File",
            defaultextension=".petmate",
            filetypes=[("Petmate", "*.petmate"), ("All files", "*.*")],
        )

        if output_file:
            try:
                write_petmate(
                    self.project.screens, output_file, use_custom_charset=True
                )
                messagebox.showinfo("Success", f"Exported to {output_file}")
                self.update_status(f"Exported Petmate: {output_file}")
                logger.info(f"Exported Petmate: {output_file}")
            except Exception as e:
                error_msg = f"Export failed: {str(e)}"
                messagebox.showerror("Error", error_msg)
                logger.error(error_msg)

    def show_settings(self):
        """Show settings dialog"""
        settings_dialog = SettingsDialog(self, self.settings)
        self.wait_window(settings_dialog)
        if settings_dialog.result:
            for key, value in settings_dialog.result.items():
                self.settings.set(key, value)
            logger.info("Settings updated")

    def show_docs(self):
        """Show documentation"""
        messagebox.showinfo(
            "Documentation",
            "Documentation available at:\nhttps://github.com/muhmi/c64-anim-tool",
        )

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "C64 Animation Tool\nVersion 0.2\n\n"
            "PNG/GIF to C64 PETSCII converter\n\n"
            "Created by phonics",
        )


def main():
    """Entry point for GUI - called from animation_converter.main when no CLI args"""
    # Setup logging before creating GUI
    setup_logging()

    app = C64AnimationToolGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
