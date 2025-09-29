import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, Canvas
from pathlib import Path


class C64AnimationToolGUI(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")

        self.title("C64 Animation Tool")
        self.geometry("1200x800")

        # Variables
        self.input_file = ttk.StringVar()
        self.output_file = ttk.StringVar()
        self.frame_rate = ttk.IntVar(value=25)
        self.scale_factor = ttk.DoubleVar(value=1.0)

        self.setup_ui()

    def setup_ui(self):
        """Setup the main UI layout"""

        # Main container with padding
        main_container = ttk.Frame(self, padding=15)
        main_container.pack(fill=BOTH, expand=YES)

        # Left panel for controls
        left_panel = ttk.Frame(main_container, padding=10)
        left_panel.pack(side=LEFT, fill=BOTH, expand=NO, padx=(0, 10))

        # Right panel for preview
        right_panel = ttk.Frame(main_container, padding=10)
        right_panel.pack(side=RIGHT, fill=BOTH, expand=YES)

        # Setup sections
        self.setup_file_section(left_panel)
        self.setup_conversion_settings(left_panel)
        self.setup_actions(left_panel)
        self.setup_preview_section(right_panel)
        self.setup_status_bar()

    def setup_file_section(self, parent):
        """File input/output section"""
        file_frame = ttk.LabelFrame(
            parent, text="Files", padding=15, bootstyle="primary"
        )
        file_frame.pack(fill=X, pady=(0, 15))

        # Input file
        ttk.Label(file_frame, text="Input File:").pack(anchor=W, pady=(0, 5))

        input_container = ttk.Frame(file_frame)
        input_container.pack(fill=X, pady=(0, 15))

        ttk.Entry(input_container, textvariable=self.input_file, state="readonly").pack(
            side=LEFT, fill=X, expand=YES, padx=(0, 5)
        )

        ttk.Button(
            input_container,
            text="Browse...",
            command=self.browse_input,
            bootstyle="secondary-outline",
            width=10,
        ).pack(side=RIGHT)

        # Output file
        ttk.Label(file_frame, text="Output File:").pack(anchor=W, pady=(0, 5))

        output_container = ttk.Frame(file_frame)
        output_container.pack(fill=X)

        ttk.Entry(
            output_container, textvariable=self.output_file, state="readonly"
        ).pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))

        ttk.Button(
            output_container,
            text="Browse...",
            command=self.browse_output,
            bootstyle="secondary-outline",
            width=10,
        ).pack(side=RIGHT)

    def setup_conversion_settings(self, parent):
        """Conversion settings section"""
        settings_frame = ttk.LabelFrame(
            parent, text="Conversion Settings", padding=15, bootstyle="info"
        )
        settings_frame.pack(fill=X, pady=(0, 15))

        # Frame rate
        ttk.Label(settings_frame, text="Frame Rate (fps):").pack(anchor=W, pady=(0, 5))

        frame_rate_container = ttk.Frame(settings_frame)
        frame_rate_container.pack(fill=X, pady=(0, 15))

        ttk.Scale(
            frame_rate_container,
            from_=1,
            to=60,
            variable=self.frame_rate,
            command=self.on_frame_rate_change,
            bootstyle="info",
        ).pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))

        self.frame_rate_label = ttk.Label(frame_rate_container, text="25", width=4)
        self.frame_rate_label.pack(side=RIGHT)

        # Scale factor
        ttk.Label(settings_frame, text="Scale Factor:").pack(anchor=W, pady=(0, 5))

        scale_container = ttk.Frame(settings_frame)
        scale_container.pack(fill=X, pady=(0, 15))

        ttk.Scale(
            scale_container,
            from_=0.1,
            to=4.0,
            variable=self.scale_factor,
            command=self.on_scale_change,
            bootstyle="info",
        ).pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))

        self.scale_label = ttk.Label(scale_container, text="1.0x", width=5)
        self.scale_label.pack(side=RIGHT)

        # Color mode
        ttk.Label(settings_frame, text="Color Mode:").pack(anchor=W, pady=(0, 5))

        color_modes = ["Multicolor", "Hires", "FLI", "AFLI"]
        self.color_mode = ttk.Combobox(
            settings_frame, values=color_modes, state="readonly"
        )
        self.color_mode.current(0)
        self.color_mode.pack(fill=X)

    def setup_actions(self, parent):
        """Action buttons section"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=X, pady=(0, 15))

        ttk.Button(
            action_frame,
            text="Convert",
            command=self.convert,
            bootstyle="success",
            width=15,
        ).pack(fill=X, pady=(0, 10))

        ttk.Button(
            action_frame,
            text="Preview",
            command=self.preview,
            bootstyle="info-outline",
            width=15,
        ).pack(fill=X, pady=(0, 10))

        ttk.Button(
            action_frame,
            text="Clear",
            command=self.clear_all,
            bootstyle="warning-outline",
            width=15,
        ).pack(fill=X)

    def setup_preview_section(self, parent):
        """Preview canvas section"""
        preview_frame = ttk.LabelFrame(
            parent, text="Preview", padding=15, bootstyle="secondary"
        )
        preview_frame.pack(fill=BOTH, expand=YES)

        # Canvas for preview
        canvas_container = ttk.Frame(preview_frame)
        canvas_container.pack(fill=BOTH, expand=YES)

        self.canvas = Canvas(
            canvas_container,
            bg="#2b3e50",
            highlightthickness=1,
            highlightbackground="#4e5d6c",
        )
        self.canvas.pack(fill=BOTH, expand=YES)

        # Preview info
        info_frame = ttk.Frame(preview_frame)
        info_frame.pack(fill=X, pady=(10, 0))

        self.preview_info = ttk.Label(
            info_frame, text="No preview available", font=("Helvetica", 10)
        )
        self.preview_info.pack()

    def setup_status_bar(self):
        """Status bar at bottom"""
        status_frame = ttk.Frame(self, padding=(15, 5))
        status_frame.pack(fill=X, side=BOTTOM)

        self.status_label = ttk.Label(
            status_frame, text="Ready", bootstyle="inverse-secondary"
        )
        self.status_label.pack(side=LEFT)

        # Progress bar
        self.progress = ttk.Progressbar(
            status_frame, mode="determinate", bootstyle="success-striped", length=200
        )
        self.progress.pack(side=RIGHT)

    # Event handlers
    def browse_input(self):
        """Browse for input file"""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("Image files", "*.png *.jpg *.gif"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.input_file.set(filename)
            self.update_status(f"Loaded: {Path(filename).name}")

            # Auto-suggest output filename
            input_path = Path(filename)
            output_path = input_path.with_suffix(".prg")
            self.output_file.set(str(output_path))

    def browse_output(self):
        """Browse for output file"""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".prg",
            filetypes=[
                ("C64 Program", "*.prg"),
                ("Binary file", "*.bin"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.output_file.set(filename)

    def on_frame_rate_change(self, value):
        """Update frame rate label"""
        self.frame_rate_label.config(text=str(int(float(value))))

    def on_scale_change(self, value):
        """Update scale label"""
        self.scale_label.config(text=f"{float(value):.1f}x")

    def convert(self):
        """Handle convert action"""
        if not self.input_file.get():
            self.update_status("Error: No input file selected", error=True)
            return

        if not self.output_file.get():
            self.update_status("Error: No output file specified", error=True)
            return

        self.update_status("Converting...")
        self.progress["value"] = 0

        # TODO: Add your conversion logic here
        # For now, simulate progress
        for i in range(0, 101, 10):
            self.progress["value"] = i
            self.update()
            self.after(100)

        self.update_status("Conversion complete!")

    def preview(self):
        """Handle preview action"""
        if not self.input_file.get():
            self.update_status("Error: No input file selected", error=True)
            return

        self.update_status("Generating preview...")

        # TODO: Add your preview logic here
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            text="Preview will appear here",
            fill="#ffffff",
            font=("Helvetica", 14),
        )
        self.preview_info.config(text="Preview: Frame 1/100")

        self.update_status("Preview ready")

    def clear_all(self):
        """Clear all fields and reset"""
        self.input_file.set("")
        self.output_file.set("")
        self.frame_rate.set(25)
        self.scale_factor.set(1.0)
        self.color_mode.current(0)
        self.canvas.delete("all")
        self.preview_info.config(text="No preview available")
        self.progress["value"] = 0
        self.update_status("Ready")

    def update_status(self, message, error=False):
        """Update status bar message"""
        self.status_label.config(
            text=message, bootstyle="inverse-danger" if error else "inverse-secondary"
        )


if __name__ == "__main__":
    app = C64AnimationToolGUI()
    app.mainloop()
