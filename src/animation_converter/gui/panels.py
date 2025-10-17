"""
GUI panels for C64 Animation Tool
"""

import logging
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext

import ttkbootstrap as ttk
from ttkbootstrap.constants import (
    BOTH,
    YES,
    X,
    Y,
    LEFT,
    RIGHT,
    W,
    BOTTOM,
    CENTER,
    END,
    DISABLED,
)
from PIL import ImageTk

from animation_converter.petscii import write_petmate


logger = logging.getLogger("animation_tool")


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

        # TODO: Add optional resources section here
        # - Charset toggle + file picker
        # - Music toggle + file picker
        # - Color animation toggle + file picker
        # - Output folder toggle + folder picker

        # TODO: Add animation settings section here
        # - Limit charsets spinbox
        # - Cleanup spinbox
        # - Border/background color spinboxes
        # - Use color checkbox
        # - Inverse checkbox

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

        # TODO: Add Test PRG button

        ttk.Button(
            action_frame,
            text="Export Petmate",
            command=self.app.export_petmate,
            bootstyle="info-outline",
            width=20,
        ).pack(fill=X)

        # TODO: Add Export Petscii+Charsets button

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
            self.input_files_list.insert(END, filename)
            self.update_project_config()
            logger.info(f"Added: {os.path.basename(filename)}")

    def remove_input_file(self):
        """Remove selected input file"""
        selection = self.input_files_list.curselection()
        if selection:
            self.input_files_list.delete(selection[0])
            self.update_project_config()

    def update_project_config(self):
        """Update project config with current GUI state"""
        if self.app.project:
            files = list(self.input_files_list.get(0, END))
            self.app.project.config["input_files"] = files
            self.app.project.save()

    def load_config_to_gui(self):
        """Load config into GUI"""
        if not self.app.project:
            return

        # Load input files
        self.input_files_list.delete(0, END)
        input_files = self.app.project.config.get("input_files", [])
        if isinstance(input_files, str):
            input_files = [input_files]
        for f in input_files:
            self.input_files_list.insert(END, f)

        # TODO: Load other settings when we add those widgets

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

    def on_frame_select(self, _event):
        """Handle frame selection in list"""
        selection = self.frames_listbox.curselection()
        if selection:
            idx = selection[0]
            self.app.show_frame(idx)

    def refresh_frames_list(self):
        """Refresh the frames listbox"""
        self.frames_listbox.delete(0, END)
        if self.app.project:
            for i, screen in enumerate(self.app.project.screens):
                charset_size = screen.charset_size()
                self.frames_listbox.insert(END, f"Frame {i:03d} ({charset_size} chars)")


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

        # TODO: Add frame-specific settings here
        # - Border/background color overrides
        # - Frame duration slider

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


class LogPanel(ttk.Frame):
    """Bottom panel - Log output"""

    def __init__(self, parent):
        super().__init__(parent, padding=5)

        # Log area
        log_frame = ttk.LabelFrame(self, text="Log", padding=10, bootstyle="dark")
        log_frame.pack(fill=BOTH, expand=YES)

        # Scrolled text widget
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            bg="#1a1a1a",
            fg="#00ff00",
            font=("Courier", 9),
            state=DISABLED,
        )
        self.log_text.pack(fill=BOTH, expand=YES)


class StatsPanel(ttk.Frame):
    """Panel showing animation statistics"""

    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app

        stats_frame = ttk.LabelFrame(
            self, text="Animation Info", padding=10, bootstyle="info"
        )
        stats_frame.pack(fill=BOTH, expand=YES)

        # Create labels for stats
        self.frame_count_label = ttk.Label(stats_frame, text="Frames: 0")
        self.frame_count_label.pack(anchor=W, pady=2)

        self.charset_count_label = ttk.Label(stats_frame, text="Charsets: 0")
        self.charset_count_label.pack(anchor=W, pady=2)

        # TODO: Add more stats when packing is implemented
        # - Animation size
        # - Player size
        # - Total size
        # - Expected FPS

    def update_stats(self):
        """Update statistics display"""
        if not self.app.project or not self.app.project.screens:
            self.frame_count_label.config(text="Frames: 0")
            self.charset_count_label.config(text="Charsets: 0")
            return

        frame_count = len(self.app.project.screens)
        charset_count = (
            len(self.app.project.charsets) if self.app.project.charsets else 0
        )

        self.frame_count_label.config(text=f"Frames: {frame_count}")
        self.charset_count_label.config(text=f"Charsets: {charset_count}")
