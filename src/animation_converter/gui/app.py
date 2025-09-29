"""
C64 Animation Tool GUI - src/animation_converter/gui/app.py
Stage 1: Basic Setup with Frame Preview

Usage:
    - No args: animation-tool → Opens this GUI
    - With args: animation-tool --config x.yaml → Runs CLI
"""

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional

from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.constants import (
    BOTH,
    BOTTOM,
    CENTER,
    HORIZONTAL,
    LEFT,
    RIGHT,
    YES,
    W,
    X,
    Y,
)
import yaml

from animation_converter.cli_parser import load_config_file, resolve_file_paths

# Import from parent package (animation_converter)
from animation_converter.petscii import PetsciiScreen, read_screens, write_petmate


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
        """Process input files to generate screens - reuses existing code"""
        input_files = self.config.get("input_files", [])
        if isinstance(input_files, str):
            input_files = [input_files]

        background_color = self.config.get("background_color")
        border_color = self.config.get("border_color")
        inverse = self.config.get("inverse", False)
        cleanup = self.config.get("cleanup", 1)

        self.screens = []
        for input_file in input_files:
            if os.path.exists(input_file):
                screens = read_screens(
                    input_file,
                    charset=None,
                    background_color=background_color,
                    border_color=border_color,
                    inverse=inverse,
                    cleanup=cleanup,
                )
                self.screens.extend(screens)

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


class ProjectPanel(ttk.Frame):
    """Left panel - Project settings and frame list"""

    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app

        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=YES)

        # Tab 1: Project Settings
        self.settings_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.settings_tab, text="Project")

        # Tab 2: Frame List
        self.frames_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frames_tab, text="Frames")

        self.setup_settings_tab()
        self.setup_frames_tab()

    def setup_settings_tab(self):
        """Setup project settings tab"""

        # Project section
        project_frame = ttk.LabelFrame(
            self.settings_tab, text="Project", padding=15, bootstyle="primary"
        )
        project_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(project_frame, text="Project Folder:").pack(anchor=W, pady=(0, 5))

        project_container = ttk.Frame(project_frame)
        project_container.pack(fill=X, pady=(0, 10))

        self.project_path_var = ttk.StringVar()
        ttk.Entry(
            project_container, textvariable=self.project_path_var, state="readonly"
        ).pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))

        ttk.Button(
            project_container,
            text="Open",
            command=self.app.open_project,
            bootstyle="secondary-outline",
            width=8,
        ).pack(side=RIGHT, padx=(2, 0))

        ttk.Button(
            project_container,
            text="New",
            command=self.app.new_project,
            bootstyle="secondary-outline",
            width=8,
        ).pack(side=RIGHT)

        # Input files section
        input_frame = ttk.LabelFrame(
            self.settings_tab, text="Input Files", padding=15, bootstyle="info"
        )
        input_frame.pack(fill=X, pady=(0, 10))

        # Scrollable listbox for input files
        list_container = ttk.Frame(input_frame)
        list_container.pack(fill=BOTH, expand=YES, pady=(0, 5))

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.input_files_list = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            height=4,
            bg="#2b3e50",
            fg="#ffffff",
            selectbackground="#3e8ed0",
        )
        self.input_files_list.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.config(command=self.input_files_list.yview)

        # Buttons for managing input files
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=X)

        ttk.Button(
            btn_frame,
            text="Add",
            command=self.add_input_file,
            bootstyle="success-outline",
            width=8,
        ).pack(side=LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Remove",
            command=self.remove_input_file,
            bootstyle="danger-outline",
            width=8,
        ).pack(side=LEFT)

        # Actions
        action_frame = ttk.LabelFrame(
            self.settings_tab, text="Actions", padding=15, bootstyle="success"
        )
        action_frame.pack(fill=X, pady=(0, 10))

        ttk.Button(
            action_frame,
            text="Process Frames",
            command=self.app.process_frames,
            bootstyle="success",
            width=20,
        ).pack(fill=X, pady=(0, 5))

        ttk.Button(
            action_frame,
            text="Export .prg",
            command=self.app.export_prg,
            bootstyle="info",
            width=20,
        ).pack(fill=X, pady=(0, 5))

        ttk.Button(
            action_frame,
            text="Export Petmate",
            command=self.app.export_petmate,
            bootstyle="info-outline",
            width=20,
        ).pack(fill=X)

    def setup_frames_tab(self):
        """Setup frames list tab"""

        # Frame list
        list_frame = ttk.Frame(self.frames_tab)
        list_frame.pack(fill=BOTH, expand=YES)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.frames_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg="#2b3e50",
            fg="#ffffff",
            selectbackground="#3e8ed0",
            font=("Courier", 10),
        )
        self.frames_listbox.pack(side=LEFT, fill=BOTH, expand=YES)
        self.frames_listbox.bind("<<ListboxSelect>>", self.on_frame_select)
        scrollbar.config(command=self.frames_listbox.yview)

    def add_input_file(self):
        """Add input file to project"""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[
                ("Supported files", "*.gif *.png *.c *.petmate"),
                ("Images", "*.gif *.png"),
                ("Petscii", "*.c *.petmate"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.input_files_list.insert(tk.END, filename)
            self.update_project_config()

    def remove_input_file(self):
        """Remove selected input file"""
        selection = self.input_files_list.curselection()
        if selection:
            self.input_files_list.delete(selection[0])
            self.update_project_config()

    def update_project_config(self):
        """Update project config with current GUI state"""
        if self.app.project:
            files = list(self.input_files_list.get(0, tk.END))
            self.app.project.config["input_files"] = files

    def on_frame_select(self, _event):
        """Handle frame selection in list"""
        selection = self.frames_listbox.curselection()
        if selection:
            idx = selection[0]
            self.app.show_frame(idx)

    def refresh_frames_list(self):
        """Refresh the frames listbox"""
        self.frames_listbox.delete(0, tk.END)
        if self.app.project:
            for i, screen in enumerate(self.app.project.screens):
                charset_size = screen.charset_size()
                self.frames_listbox.insert(
                    tk.END, f"Frame {i:03d} ({charset_size} chars)"
                )


class PreviewPanel(ttk.Frame):
    """Right panel - Frame preview and settings"""

    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        self.current_image = None
        self.photo_image = None

        # Preview area
        preview_frame = ttk.LabelFrame(
            self, text="Frame Preview", padding=15, bootstyle="secondary"
        )
        preview_frame.pack(fill=BOTH, expand=YES)

        # Canvas for rendering
        canvas_frame = ttk.Frame(preview_frame)
        canvas_frame.pack(fill=BOTH, expand=YES)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#000000",
            highlightthickness=1,
            highlightbackground="#4e5d6c",
        )
        self.canvas.pack(fill=BOTH, expand=YES)

        # Frame info
        info_frame = ttk.Frame(preview_frame)
        info_frame.pack(fill=X, pady=(10, 0))

        self.info_label = ttk.Label(
            info_frame, text="No frame loaded", font=("Helvetica", 10)
        )
        self.info_label.pack()

        # Frame settings (expandable section)
        self.settings_frame = ttk.LabelFrame(
            self, text="Frame Settings", padding=15, bootstyle="info"
        )
        self.settings_frame.pack(fill=X, pady=(10, 0))

        ttk.Label(
            self.settings_frame, text="Frame-specific settings will appear here"
        ).pack()

    def show_frame(self, frame_idx: int):
        """Display a frame in the preview"""
        if not self.app.project:
            return

        img = self.app.project.render_frame(frame_idx, scale=2)
        if img:
            self.current_image = img

            # Convert to PhotoImage for display
            self.photo_image = ImageTk.PhotoImage(img)

            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                image=self.photo_image,
                anchor=CENTER,
            )

            # Update info
            screen = self.app.project.get_frame(frame_idx)
            if screen:
                info = f"Frame {frame_idx} | Charset: {screen.charset_size()} chars"
                if screen.background_color is not None:
                    info += f" | BG: {screen.background_color}"
                if screen.border_color is not None:
                    info += f" | Border: {screen.border_color}"
                self.info_label.config(text=info)


class C64AnimationToolGUI(ttk.Window):
    """Main application window"""

    def __init__(self):
        super().__init__(themename="darkly")

        self.title("C64 Animation Tool")
        self.geometry("1400x900")

        self.project: Optional[AnimationProject] = None

        self.setup_ui()
        self.setup_menu()

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

        # Right panel (preview)
        self.preview_panel = PreviewPanel(paned, self)
        paned.add(self.preview_panel, weight=2)

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
        file_menu.add_command(label="Exit", command=self.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_status_bar(self):
        """Setup status bar at bottom"""
        status_frame = ttk.Frame(self, padding=(10, 5))
        status_frame.pack(fill=X, side=BOTTOM)

        self.status_label = ttk.Label(
            status_frame, text="Ready", bootstyle="inverse-secondary"
        )
        self.status_label.pack(side=LEFT)

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
            self.update_status(f"Created project: {config_path}")

    def open_project(self):
        """Open existing project"""
        config_file = filedialog.askopenfilename(
            title="Select Project Config",
            filetypes=[("YAML Config", "*.yaml *.yml"), ("All files", "*.*")],
        )
        if config_file:
            self.project = AnimationProject(Path(config_file))
            self.project_panel.project_path_var.set(config_file)

            # Load input files into GUI
            self.project_panel.input_files_list.delete(0, tk.END)
            input_files = self.project.config.get("input_files", [])
            if isinstance(input_files, str):
                input_files = [input_files]
            for f in input_files:
                self.project_panel.input_files_list.insert(tk.END, f)

            self.update_status(f"Opened project: {config_file}")

    def process_frames(self):
        """Process input files to generate frames"""
        if not self.project:
            messagebox.showwarning(
                "No Project", "Please open or create a project first"
            )
            return

        try:
            self.update_status("Processing frames...")
            self.project_panel.update_project_config()
            self.project.process_frames()

            # Refresh frames list
            self.project_panel.refresh_frames_list()

            # Show first frame
            if self.project.screens:
                self.show_frame(0)

            self.update_status(f"Processed {len(self.project.screens)} frames")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process frames: {e!s}")
            self.update_status("Error processing frames", error=True)

    def show_frame(self, idx: int):
        """Display frame in preview panel"""
        self.preview_panel.show_frame(idx)

    def export_prg(self):
        """Export to .prg file"""
        if not self.project or not self.project.screens:
            messagebox.showwarning("No Frames", "Process frames first")
            return

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
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e!s}")

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "C64 Animation Tool\nVersion 0.1\n\nPNG/GIF to C64 PETSCII converter",
        )


def main():
    """Entry point for GUI - called from animation_converter.main when no CLI args"""
    app = C64AnimationToolGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
