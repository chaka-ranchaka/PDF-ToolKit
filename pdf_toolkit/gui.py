from pathlib import Path
from shutil import copy2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk
from pypdf import PdfReader

try:
    import pymupdf as fitz
except ImportError:  # pragma: no cover
    fitz = None

from .file_utils import require_distinct_output, require_existing_file
from .pdf_operations import (
    add_watermark,
    compress_pdf,
    convert_pdf,
    convert_pdf_color,
    extract_images,
    images_to_pdf,
    merge_pdfs,
    parse_page_ranges,
    remove_pages,
    reorder_pages,
    rotate_pages,
    split_pdf,
)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # pragma: no cover
    DND_FILES, TkinterDnD = None, None


class PdfToolkitApp:
    """
    Main GUI application for PDF Toolkit.

    The GUI intentionally keeps the interface minimal while exposing
    the existing PDF operations through a single operation selector.
    """

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    COLORS = {
        "bg": "#0b0f14",
        "surface": "#111720",
        "surface_2": "#151c26",
        "surface_3": "#1b2430",
        "border": "#273342",
        "text": "#f1f5f9",
        "muted": "#8b98a8",
        "accent": "#64e6c4",
        "accent_dark": "#2fa98b",
        "danger": "#ff6b81",
        "warning": "#f4c95d",
        "white": "#ffffff",
        "black": "#000000",
    }

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, root: tk.Tk):
        self.root = root

        self.root.title("PDF Toolkit")
        self.root.geometry("940x720")
        self.root.minsize(820, 620)
        self.root.configure(bg=self.COLORS["bg"])

        self.files: list[Path] = []

        # Main state
        self.operation = tk.StringVar(value="Gabungkan PDF")
        self.page_input = tk.StringVar()
        self.output_input = tk.StringVar()
        self.extra_input = tk.StringVar()

        # Watermark
        self.watermark_position = tk.StringVar(value="Tengah")
        self.watermark_opacity = tk.StringVar(value="25")
        self.watermark_size = tk.StringVar(value="32")
        self.watermark_angle = tk.StringVar(value="35")

        # PDF conversion
        self.convert_format = tk.StringVar(value="TXT")

        # PDF color conversion
        self.color_mode = tk.StringVar(value="Original")
        self.color_dpi = tk.StringVar(value="150")

        # Settings
        self.confirm_before_run = tk.BooleanVar(value=False)
        self.show_file_info = tk.BooleanVar(value=True)

        # Status
        self.status = tk.StringVar(value="Ready")
        self.file_count = tk.StringVar(value="0 files")

        self._setup_styles()
        self._build()

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _setup_styles(self):
        style = ttk.Style(self.root)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "App.TFrame",
            background=self.COLORS["bg"],
        )

        style.configure(
            "Surface.TFrame",
            background=self.COLORS["surface"],
        )

        style.configure(
            "Surface2.TFrame",
            background=self.COLORS["surface_2"],
        )

        style.configure(
            "Surface3.TFrame",
            background=self.COLORS["surface_3"],
        )

        style.configure(
            "Title.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 21, "bold"),
        )

        style.configure(
            "Subtitle.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 9),
        )

        style.configure(
            "Surface.TLabel",
            background=self.COLORS["surface"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 9),
        )

        style.configure(
            "Muted.Surface.TLabel",
            background=self.COLORS["surface"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 9),
        )

        style.configure(
            "Section.TLabel",
            background=self.COLORS["surface"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "Accent.TButton",
            background=self.COLORS["accent"],
            foreground="#06120f",
            font=("Segoe UI", 9, "bold"),
            padding=(15, 9),
            borderwidth=0,
        )

        style.map(
            "Accent.TButton",
            background=[
                ("active", self.COLORS["accent_dark"]),
                ("pressed", self.COLORS["accent_dark"]),
            ],
            foreground=[
                ("active", self.COLORS["white"]),
                ("pressed", self.COLORS["white"]),
            ],
        )

        style.configure(
            "Secondary.TButton",
            background=self.COLORS["surface_3"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 9),
            padding=(10, 8),
            borderwidth=0,
        )

        style.map(
            "Secondary.TButton",
            background=[
                ("active", "#243140"),
                ("pressed", "#243140"),
            ],
        )

        style.configure(
            "Danger.TButton",
            background=self.COLORS["surface_3"],
            foreground=self.COLORS["danger"],
            font=("Segoe UI", 9),
            padding=(10, 8),
            borderwidth=0,
        )

        style.map(
            "Danger.TButton",
            background=[
                ("active", "#2b2027"),
                ("pressed", "#2b2027"),
            ],
        )

        style.configure(
            "TCombobox",
            fieldbackground=self.COLORS["surface_3"],
            background=self.COLORS["surface_3"],
            foreground=self.COLORS["text"],
            arrowcolor=self.COLORS["accent"],
            borderwidth=0,
            padding=7,
        )

        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", self.COLORS["surface_3"]),
            ],
            foreground=[
                ("readonly", self.COLORS["text"]),
            ],
        )

        style.configure(
            "TEntry",
            fieldbackground=self.COLORS["surface_3"],
            foreground=self.COLORS["text"],
            insertcolor=self.COLORS["accent"],
            borderwidth=0,
            padding=7,
        )

        style.configure(
            "TCheckbutton",
            background=self.COLORS["surface"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 9),
        )

        style.map(
            "TCheckbutton",
            background=[
                ("active", self.COLORS["surface"]),
            ],
            foreground=[
                ("active", self.COLORS["accent"]),
            ],
        )

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build(self):
        self.main_frame = ttk.Frame(
            self.root,
            padding=24,
            style="App.TFrame",
        )
        self.main_frame.pack(fill="both", expand=True)

        self._build_header()
        self._build_drop_zone()
        self._build_file_section()
        self._build_operation_section()
        self._build_output_section()
        self._build_action_bar()
        self._build_status_bar()

        self._update_options()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ttk.Frame(
            self.main_frame,
            style="App.TFrame",
        )
        header.pack(fill="x", pady=(0, 18))

        left = ttk.Frame(
            header,
            style="App.TFrame",
        )
        left.pack(side="left")

        title_frame = ttk.Frame(
            left,
            style="App.TFrame",
        )
        title_frame.pack(anchor="w")

        ttk.Label(
            title_frame,
            text="◈",
            foreground=self.COLORS["accent"],
            background=self.COLORS["bg"],
            font=("Segoe UI Symbol", 20, "bold"),
        ).pack(side="left", padx=(0, 8))

        ttk.Label(
            title_frame,
            text="PDF TOOLKIT",
            style="Title.TLabel",
        ).pack(side="left")

        ttk.Label(
            left,
            text="Local document processing • Fast • Private",
            style="Subtitle.TLabel",
        ).pack(anchor="w", padx=(34, 0))

        ttk.Button(
            header,
            text="☰",
            command=self._open_settings,
            style="Secondary.TButton",
            width=4,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Drop zone
    # ------------------------------------------------------------------

    def _build_drop_zone(self):
        self.drop_zone = tk.Frame(
            self.main_frame,
            bg=self.COLORS["surface_2"],
            highlightbackground=self.COLORS["border"],
            highlightcolor=self.COLORS["accent"],
            highlightthickness=1,
            height=105,
            cursor="hand2",
        )
        self.drop_zone.pack(fill="x", pady=(0, 14))
        self.drop_zone.pack_propagate(False)

        self.drop_icon = tk.Label(
            self.drop_zone,
            text="＋",
            bg=self.COLORS["surface_2"],
            fg=self.COLORS["accent"],
            font=("Segoe UI", 22),
        )
        self.drop_icon.pack(pady=(15, 0))

        self.drop_title = tk.Label(
            self.drop_zone,
            text="Drop files here",
            bg=self.COLORS["surface_2"],
            fg=self.COLORS["text"],
            font=("Segoe UI", 10, "bold"),
        )
        self.drop_title.pack()

        self.drop_subtitle = tk.Label(
            self.drop_zone,
            text="or click to browse files",
            bg=self.COLORS["surface_2"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 8),
        )
        self.drop_subtitle.pack(pady=(2, 0))

        self._bind_drop_zone()

    def _bind_drop_zone(self):
        widgets = [
            self.drop_zone,
            self.drop_icon,
            self.drop_title,
            self.drop_subtitle,
        ]

        for widget in widgets:
            widget.bind("<Button-1>", lambda _event: self._add_files())
            widget.bind(
                "<Enter>",
                lambda _event: self._drop_zone_hover(True),
            )
            widget.bind(
                "<Leave>",
                lambda _event: self._drop_zone_hover(False),
            )

        if DND_FILES is not None:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind(
                "<<Drop>>",
                self._drop_files,
            )

    def _drop_zone_hover(self, active: bool):
        bg = (
            self.COLORS["surface_3"]
            if active
            else self.COLORS["surface_2"]
        )

        self.drop_zone.configure(
            bg=bg,
            highlightbackground=(
                self.COLORS["accent"]
                if active
                else self.COLORS["border"]
            ),
        )

        for widget in [
            self.drop_icon,
            self.drop_title,
            self.drop_subtitle,
        ]:
            widget.configure(bg=bg)

    # ------------------------------------------------------------------
    # File section
    # ------------------------------------------------------------------

    def _build_file_section(self):
        section = ttk.Frame(
            self.main_frame,
            style="Surface.TFrame",
            padding=14,
        )
        section.pack(fill="both", expand=True, pady=(0, 14))

        header = ttk.Frame(
            section,
            style="Surface.TFrame",
        )
        header.pack(fill="x", pady=(0, 8))

        ttk.Label(
            header,
            text="INPUT FILES",
            style="Section.TLabel",
        ).pack(side="left")

        ttk.Label(
            header,
            textvariable=self.file_count,
            style="Muted.Surface.TLabel",
        ).pack(side="right")

        body = ttk.Frame(
            section,
            style="Surface.TFrame",
        )
        body.pack(fill="both", expand=True)

        list_frame = tk.Frame(
            body,
            bg=self.COLORS["surface_2"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
        )
        list_frame.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.file_list = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            relief="flat",
            borderwidth=0,
            bg=self.COLORS["surface_2"],
            fg=self.COLORS["text"],
            selectbackground=self.COLORS["accent_dark"],
            selectforeground=self.COLORS["white"],
            activestyle="none",
            font=("Segoe UI", 9),
            highlightthickness=0,
        )
        self.file_list.pack(
            side="left",
            fill="both",
            expand=True,
            padx=8,
            pady=8,
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.file_list.yview,
        )
        scrollbar.pack(side="right", fill="y")

        self.file_list.configure(
            yscrollcommand=scrollbar.set
        )

        buttons = ttk.Frame(
            body,
            style="Surface.TFrame",
        )
        buttons.pack(
            side="right",
            fill="y",
            padx=(10, 0),
        )

        ttk.Button(
            buttons,
            text="＋",
            command=self._add_files,
            style="Secondary.TButton",
            width=4,
        ).pack(fill="x")

        ttk.Button(
            buttons,
            text="×",
            command=self._remove_files,
            style="Danger.TButton",
            width=4,
        ).pack(fill="x", pady=4)

        ttk.Button(
            buttons,
            text="↑",
            command=lambda: self._move(-1),
            style="Secondary.TButton",
            width=4,
        ).pack(fill="x")

        ttk.Button(
            buttons,
            text="↓",
            command=lambda: self._move(1),
            style="Secondary.TButton",
            width=4,
        ).pack(fill="x", pady=4)

    # ------------------------------------------------------------------
    # Operation section
    # ------------------------------------------------------------------

    def _build_operation_section(self):
        section = ttk.Frame(
            self.main_frame,
            style="Surface.TFrame",
            padding=14,
        )
        section.pack(fill="x", pady=(0, 14))

        top = ttk.Frame(
            section,
            style="Surface.TFrame",
        )
        top.pack(fill="x")

        ttk.Label(
            top,
            text="OPERATION",
            style="Section.TLabel",
        ).pack(side="left")

        self.operation_selector = ttk.Combobox(
            top,
            textvariable=self.operation,
            state="readonly",
            values=[
                "Gabungkan PDF",
                "Gabungkan halaman terpilih",
                "Pisahkan PDF",
                "Hapus halaman",
                "Putar halaman",
                "Atur ulang halaman",
                "Ekstrak gambar",
                "Kompres PDF",
                "Watermark",
                "Gambar ke PDF",
                "Konversi PDF",
                "Ubah warna PDF",
            ],
            width=32,
        )
        self.operation_selector.pack(
            side="right",
        )

        self.operation_selector.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._update_options(),
        )

        self._build_options_panel(section)

    # ------------------------------------------------------------------
    # Options panel
    # ------------------------------------------------------------------

    def _build_options_panel(self, parent):
        self.options_panel = ttk.Frame(
            parent,
            style="Surface.TFrame",
        )
        self.options_panel.pack(
            fill="x",
            pady=(12, 0),
        )

        # --------------------------------------------------------------
        # General page input
        # --------------------------------------------------------------

        self.general_options = ttk.Frame(
            self.options_panel,
            style="Surface.TFrame",
        )

        self.page_label = ttk.Label(
            self.general_options,
            text="Halaman",
            style="Muted.Surface.TLabel",
        )
        self.page_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.page_entry = ttk.Entry(
            self.general_options,
            textvariable=self.page_input,
        )
        self.page_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 10),
        )

        self.extra_label = ttk.Label(
            self.general_options,
            text="Parameter",
            style="Muted.Surface.TLabel",
        )
        self.extra_label.grid(
            row=0,
            column=1,
            sticky="w",
        )

        self.extra_entry = ttk.Entry(
            self.general_options,
            textvariable=self.extra_input,
        )
        self.extra_entry.grid(
            row=1,
            column=1,
            sticky="ew",
        )

        self.general_options.columnconfigure(0, weight=1)
        self.general_options.columnconfigure(1, weight=1)

        # --------------------------------------------------------------
        # Watermark
        # --------------------------------------------------------------

        self.watermark_frame = ttk.Frame(
            self.options_panel,
            style="Surface.TFrame",
        )

        ttk.Label(
            self.watermark_frame,
            text="Teks",
            style="Muted.Surface.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.watermark_text_entry = ttk.Entry(
            self.watermark_frame,
            textvariable=self.extra_input,
        )
        self.watermark_text_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )

        ttk.Label(
            self.watermark_frame,
            text="Posisi",
            style="Muted.Surface.TLabel",
        ).grid(
            row=0,
            column=1,
            sticky="w",
        )

        ttk.Combobox(
            self.watermark_frame,
            textvariable=self.watermark_position,
            state="readonly",
            values=[
                "Tengah",
                "Kiri atas",
                "Kanan atas",
                "Kiri bawah",
                "Kanan bawah",
            ],
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(0, 8),
        )

        ttk.Label(
            self.watermark_frame,
            text="Opacity %",
            style="Muted.Surface.TLabel",
        ).grid(
            row=0,
            column=2,
            sticky="w",
        )

        ttk.Entry(
            self.watermark_frame,
            textvariable=self.watermark_opacity,
            width=8,
        ).grid(
            row=1,
            column=2,
            sticky="ew",
            padx=(0, 8),
        )

        ttk.Label(
            self.watermark_frame,
            text="Size",
            style="Muted.Surface.TLabel",
        ).grid(
            row=0,
            column=3,
            sticky="w",
        )

        ttk.Entry(
            self.watermark_frame,
            textvariable=self.watermark_size,
            width=8,
        ).grid(
            row=1,
            column=3,
            sticky="ew",
            padx=(0, 8),
        )

        ttk.Label(
            self.watermark_frame,
            text="Rotasi",
            style="Muted.Surface.TLabel",
        ).grid(
            row=0,
            column=4,
            sticky="w",
        )

        ttk.Entry(
            self.watermark_frame,
            textvariable=self.watermark_angle,
            width=8,
        ).grid(
            row=1,
            column=4,
            sticky="ew",
        )

        for column in range(5):
            self.watermark_frame.columnconfigure(
                column,
                weight=1,
            )

        # --------------------------------------------------------------
        # Format conversion
        # --------------------------------------------------------------

        self.convert_frame = ttk.Frame(
            self.options_panel,
            style="Surface.TFrame",
        )

        ttk.Label(
            self.convert_frame,
            text="Output format",
            style="Muted.Surface.TLabel",
        ).pack(side="left")

        ttk.Combobox(
            self.convert_frame,
            textvariable=self.convert_format,
            state="readonly",
            values=["TXT", "HTML", "DOCX"],
            width=10,
        ).pack(
            side="left",
            padx=(10, 0),
        )

        # --------------------------------------------------------------
        # Color conversion
        # --------------------------------------------------------------

        self.color_frame = ttk.Frame(
            self.options_panel,
            style="Surface.TFrame",
        )

        ttk.Label(
            self.color_frame,
            text="Color mode",
            style="Muted.Surface.TLabel",
        ).pack(
            side="left",
            padx=(0, 10),
        )

        self._build_color_selector(self.color_frame)

        ttk.Label(
            self.color_frame,
            text="DPI",
            style="Muted.Surface.TLabel",
        ).pack(
            side="left",
            padx=(18, 8),
        )

        ttk.Entry(
            self.color_frame,
            textvariable=self.color_dpi,
            width=7,
        ).pack(side="left")

    # ------------------------------------------------------------------
    # Color selector
    # ------------------------------------------------------------------

    def _build_color_selector(self, parent):
        self.color_buttons = {}

        for mode, label in [
            ("Original", "Original"),
            ("grayscale", "Grayscale"),
            ("blackwhite", "Black & White"),
        ]:
            button = tk.Button(
                parent,
                text=label,
                command=lambda value=mode: self._select_color_mode(value),
                relief="flat",
                bd=0,
                padx=12,
                pady=6,
                cursor="hand2",
                font=("Segoe UI", 8, "bold"),
            )
            button.pack(
                side="left",
                padx=(0, 4),
            )

            self.color_buttons[mode] = button

        self._refresh_color_buttons()

    def _select_color_mode(self, mode: str):
        self.color_mode.set(mode)
        self._refresh_color_buttons()

    def _refresh_color_buttons(self):
        for mode, button in self.color_buttons.items():
            selected = self.color_mode.get() == mode

            button.configure(
                bg=(
                    self.COLORS["accent"]
                    if selected
                    else self.COLORS["surface_3"]
                ),
                fg=(
                    "#06120f"
                    if selected
                    else self.COLORS["text"]
                ),
                activebackground=(
                    self.COLORS["accent_dark"]
                    if selected
                    else "#243140"
                ),
                activeforeground=self.COLORS["white"],
            )

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def _build_output_section(self):
        section = ttk.Frame(
            self.main_frame,
            style="Surface.TFrame",
            padding=14,
        )
        section.pack(fill="x", pady=(0, 14))

        ttk.Label(
            section,
            text="OUTPUT",
            style="Section.TLabel",
        ).pack(anchor="w")

        row = ttk.Frame(
            section,
            style="Surface.TFrame",
        )
        row.pack(
            fill="x",
            pady=(7, 0),
        )

        ttk.Entry(
            row,
            textvariable=self.output_input,
        ).pack(
            side="left",
            fill="x",
            expand=True,
        )

        ttk.Button(
            row,
            text="Browse",
            command=self._choose_output,
            style="Secondary.TButton",
        ).pack(
            side="right",
            padx=(8, 0),
        )

    # ------------------------------------------------------------------
    # Action bar
    # ------------------------------------------------------------------

    def _build_action_bar(self):
        frame = ttk.Frame(
            self.main_frame,
            style="App.TFrame",
        )
        frame.pack(
            fill="x",
            pady=(0, 8),
        )

        ttk.Button(
            frame,
            text="⌕  Preview",
            command=self._preview,
            style="Secondary.TButton",
        ).pack(side="left")

        ttk.Button(
            frame,
            text="▶  Run Operation",
            command=self._run,
            style="Accent.TButton",
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _build_status_bar(self):
        frame = tk.Frame(
            self.main_frame,
            bg=self.COLORS["bg"],
        )
        frame.pack(fill="x")

        tk.Label(
            frame,
            text="●",
            bg=self.COLORS["bg"],
            fg=self.COLORS["accent"],
            font=("Segoe UI", 8),
        ).pack(side="left")

        tk.Label(
            frame,
            textvariable=self.status,
            bg=self.COLORS["bg"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(
            side="left",
            padx=(5, 0),
        )

        tk.Label(
            frame,
            text="LOCAL PROCESSING",
            bg=self.COLORS["bg"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Dynamic options
    # ------------------------------------------------------------------

    def _update_options(self):
        operation = self.operation.get()

        self.general_options.pack_forget()
        self.watermark_frame.pack_forget()
        self.convert_frame.pack_forget()
        self.color_frame.pack_forget()

        if operation == "Watermark":
            self.watermark_frame.pack(
                fill="x",
            )
            return

        if operation == "Konversi PDF":
            self.convert_frame.pack(
                fill="x",
            )
            return

        if operation == "Ubah warna PDF":
            self.color_frame.pack(
                fill="x",
            )
            return

        # Operations that require page/extra input
        operations_with_general_options = {
            "Gabungkan halaman terpilih",
            "Pisahkan PDF",
            "Hapus halaman",
            "Putar halaman",
            "Atur ulang halaman",
        }

        if operation in operations_with_general_options:
            self.general_options.pack(
                fill="x",
            )

            if operation == "Atur ulang halaman":
                self.page_label.configure(
                    text="Urutan halaman"
                )
                self.extra_entry.configure(
                    state="disabled"
                )
                self.extra_label.configure(
                    text="Contoh: 3, 1, 2"
                )

            elif operation == "Putar halaman":
                self.page_label.configure(
                    text="Halaman"
                )
                self.extra_entry.configure(
                    state="normal"
                )
                self.extra_label.configure(
                    text="Sudut (90 / 180 / 270)"
                )

            elif operation == "Hapus halaman":
                self.page_label.configure(
                    text="Halaman yang dihapus"
                )
                self.extra_entry.configure(
                    state="disabled"
                )
                self.extra_label.configure(
                    text="Tidak diperlukan"
                )

            elif operation == "Pisahkan PDF":
                self.page_label.configure(
                    text="Halaman pemisah"
                )
                self.extra_entry.configure(
                    state="disabled"
                )
                self.extra_label.configure(
                    text="Tidak diperlukan"
                )

            elif operation == "Gabungkan halaman terpilih":
                self.page_label.configure(
                    text="Halaman"
                )
                self.extra_entry.configure(
                    state="disabled"
                )
                self.extra_label.configure(
                    text="Tidak diperlukan"
                )

    # ------------------------------------------------------------------
    # File handling
    # ------------------------------------------------------------------

    def _add_files(self):
        operation = self.operation.get()

        if operation == "Gambar ke PDF":
            types = [
                (
                    "Images",
                    "*.png *.jpg *.jpeg *.webp *.bmp",
                )
            ]
        else:
            types = [
                (
                    "PDF",
                    "*.pdf",
                )
            ]

        selected = filedialog.askopenfilenames(
            title="Select input files",
            filetypes=types,
        )

        if not selected:
            return

        self.files.extend(
            Path(path)
            for path in selected
        )

        self._refresh()

    def _drop_files(self, event):
        paths = self.root.tk.splitlist(event.data)

        operation = self.operation.get()

        if operation == "Gambar ke PDF":
            allowed = {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".bmp",
            }

            valid_paths = [
                Path(path)
                for path in paths
                if Path(path).suffix.lower() in allowed
            ]

        else:
            valid_paths = [
                Path(path)
                for path in paths
                if Path(path).suffix.lower() == ".pdf"
            ]

        self.files.extend(valid_paths)
        self._refresh()

    def _remove_files(self):
        selected = self.file_list.curselection()

        for index in reversed(selected):
            self.files.pop(index)

        self._refresh()

    def _move(self, direction: int):
        selected = self.file_list.curselection()

        if len(selected) != 1:
            return

        old_index = selected[0]
        new_index = old_index + direction

        if not 0 <= new_index < len(self.files):
            return

        self.files[old_index], self.files[new_index] = (
            self.files[new_index],
            self.files[old_index],
        )

        self._refresh()

        self.file_list.selection_set(new_index)
        self.file_list.see(new_index)

    def _refresh(self):
        self.file_list.delete(
            0,
            tk.END,
        )

        for path in self.files:
            self.file_list.insert(
                tk.END,
                f"  ◉  {path.name}",
            )

        count = len(self.files)

        self.file_count.set(
            f"{count} file"
            if count == 1
            else f"{count} files"
        )

    # ------------------------------------------------------------------
    # Output picker
    # ------------------------------------------------------------------

    def _choose_output(self):
        operation = self.operation.get()

        extension = ".pdf"
        filetypes = [
            (
                "PDF",
                "*.pdf",
            )
        ]

        if operation == "Konversi PDF":
            extension = (
                "."
                + self.convert_format.get().lower()
            )

            filetypes = [
                (
                    self.convert_format.get(),
                    f"*{extension}",
                )
            ]

        path = filedialog.asksaveasfilename(
            title="Choose output location",
            defaultextension=extension,
            filetypes=filetypes,
        )

        if path:
            self.output_input.set(path)

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _preview(self):
        if not self.files:
            messagebox.showwarning(
                "Preview",
                "Pilih file input terlebih dahulu.",
            )
            return

        try:
            operation = self.operation.get()

            details = [
                f"{operation}",
                f"{len(self.files)} input file(s)",
                "",
            ]

            for path in self.files:
                if not path.is_file():
                    raise FileNotFoundError(
                        f"File tidak ditemukan: {path}"
                    )

                if path.suffix.lower() == ".pdf":
                    reader = PdfReader(
                        str(path)
                    )

                    details.append(
                        f"◉ {path.name}  •  "
                        f"{len(reader.pages)} halaman"
                    )
                else:
                    details.append(
                        f"◉ {path.name}"
                    )

            if self.page_input.get().strip():
                details.extend(
                    [
                        "",
                        f"Halaman: "
                        f"{self.page_input.get().strip()}",
                    ]
                )

            if operation == "Watermark":
                details.extend(
                    [
                        f"Watermark: "
                        f"{self.extra_input.get() or '(kosong)'}",
                        f"Position: "
                        f"{self.watermark_position.get()}",
                        f"Opacity: "
                        f"{self.watermark_opacity.get()}%",
                        f"Size: "
                        f"{self.watermark_size.get()}",
                        f"Rotation: "
                        f"{self.watermark_angle.get()}°",
                    ]
                )

            elif operation == "Konversi PDF":
                details.append(
                    f"Format tujuan: "
                    f"{self.convert_format.get()}"
                )

            elif operation == "Ubah warna PDF":
                mode = self.color_mode.get()

                mode_label = {
                    "Original": "Original",
                    "grayscale": "Grayscale",
                    "blackwhite": "Black & White",
                }.get(mode, mode)

                details.append(
                    f"Color mode: {mode_label}"
                )

                if mode != "Original":
                    details.append(
                        f"DPI: {self.color_dpi.get()}"
                    )

            image = self._load_preview_image(
                self.files[0]
            )

            self._show_preview(
                "PDF Toolkit • Preview",
                "\n".join(details),
                image,
            )

        except (
            FileNotFoundError,
            RuntimeError,
            ValueError,
            OSError,
        ) as error:
            messagebox.showerror(
                "Preview gagal",
                str(error),
            )

    def _load_preview_image(
        self,
        path: Path,
    ) -> Image.Image:

        if path.suffix.lower() == ".pdf":
            if fitz is None:
                raise RuntimeError(
                    "PyMuPDF belum terpasang. "
                    "Jalankan: pip install -r requirements.txt"
                )

            document = fitz.open(
                str(path)
            )

            try:
                if document.page_count == 0:
                    raise ValueError(
                        "PDF tidak memiliki halaman."
                    )

                pixmap = document[0].get_pixmap(
                    matrix=fitz.Matrix(
                        1.5,
                        1.5,
                    ),
                    alpha=False,
                )

                return Image.frombytes(
                    "RGB",
                    (
                        pixmap.width,
                        pixmap.height,
                    ),
                    pixmap.samples,
                )

            finally:
                document.close()

        return Image.open(path).convert(
            "RGB"
        )

    def _show_preview(
        self,
        title: str,
        details: str,
        image: Image.Image,
    ):
        window = tk.Toplevel(
            self.root
        )

        window.title(title)
        window.geometry("780x720")
        window.minsize(650, 600)
        window.configure(
            bg=self.COLORS["bg"]
        )

        window.transient(
            self.root
        )

        container = tk.Frame(
            window,
            bg=self.COLORS["bg"],
            padx=20,
            pady=20,
        )
        container.pack(
            fill="both",
            expand=True,
        )

        tk.Label(
            container,
            text="PREVIEW",
            bg=self.COLORS["bg"],
            fg=self.COLORS["accent"],
            font=("Segoe UI", 9, "bold"),
        ).pack(
            anchor="w"
        )

        tk.Label(
            container,
            text=details,
            justify="left",
            anchor="w",
            bg=self.COLORS["bg"],
            fg=self.COLORS["text"],
            font=("Consolas", 9),
        ).pack(
            anchor="w",
            fill="x",
            pady=(8, 14),
        )

        preview_frame = tk.Frame(
            container,
            bg=self.COLORS["surface_2"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
        )
        preview_frame.pack(
            fill="both",
            expand=True,
        )

        image.thumbnail(
            (
                700,
                520,
            ),
            Image.Resampling.LANCZOS,
        )

        photo = ImageTk.PhotoImage(
            image
        )

        preview = tk.Label(
            preview_frame,
            image=photo,
            bg=self.COLORS["surface_2"],
        )

        preview.image = photo

        preview.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        ttk.Button(
            container,
            text="Close",
            command=window.destroy,
            style="Secondary.TButton",
        ).pack(
            anchor="e",
            pady=(12, 0),
        )

    # ------------------------------------------------------------------
    # Run operation
    # ------------------------------------------------------------------

    def _run(self):
        try:
            operation = self.operation.get()

            if not self.output_input.get().strip():
                raise ValueError(
                    "Pilih file output terlebih dahulu."
                )

            output = Path(
                self.output_input.get()
            )

            if self.confirm_before_run:
                if self.confirm_before_run.get():
                    confirmed = messagebox.askyesno(
                        "Confirm operation",
                        f"Jalankan operasi:\n\n"
                        f"{operation}\n\n"
                        f"Output:\n{output}",
                    )

                    if not confirmed:
                        return

            # ----------------------------------------------------------
            # PDF format conversion
            # ----------------------------------------------------------

            if operation == "Konversi PDF":
                if len(self.files) != 1:
                    raise ValueError(
                        "Pilih tepat satu file PDF "
                        "untuk dikonversi."
                    )

                result = convert_pdf(
                    self.files[0],
                    output,
                    self.convert_format.get(),
                )

            # ----------------------------------------------------------
            # PDF color conversion
            # ----------------------------------------------------------

            elif operation == "Ubah warna PDF":
                if len(self.files) != 1:
                    raise ValueError(
                        "Pilih tepat satu file PDF "
                        "untuk mengubah warna."
                    )

                source = self.files[0]

                if self.color_mode.get() == "Original":
                    require_existing_file(
                        source
                    )

                    require_distinct_output(
                        output,
                        [source],
                    )

                    copy2(
                        source,
                        output,
                    )

                    result = len(
                        PdfReader(
                            str(source)
                        ).pages
                    )

                else:
                    try:
                        dpi = int(
                            self.color_dpi.get()
                        )
                    except ValueError:
                        raise ValueError(
                            "DPI harus berupa angka."
                        )

                    result = convert_pdf_color(
                        source,
                        output,
                        mode=self.color_mode.get(),
                        dpi=dpi,
                    )

            # ----------------------------------------------------------
            # Images -> PDF
            # ----------------------------------------------------------

            elif operation == "Gambar ke PDF":
                if not self.files:
                    raise ValueError(
                        "Pilih minimal satu gambar."
                    )

                result = images_to_pdf(
                    self.files,
                    output,
                )

            # ----------------------------------------------------------
            # Merge
            # ----------------------------------------------------------

            elif operation == "Gabungkan PDF":
                if not self.files:
                    raise ValueError(
                        "Pilih file PDF terlebih dahulu."
                    )

                result = merge_pdfs(
                    self.files,
                    output,
                )

            # ----------------------------------------------------------
            # Merge selected pages
            # ----------------------------------------------------------

            elif operation == "Gabungkan halaman terpilih":
                if not self.files:
                    raise ValueError(
                        "Pilih file PDF terlebih dahulu."
                    )

                result = merge_pdfs(
                    self.files,
                    output,
                    parse_page_ranges(
                        self.page_input.get()
                    ),
                )

            # ----------------------------------------------------------
            # Single PDF operations
            # ----------------------------------------------------------

            else:
                if not self.files:
                    raise ValueError(
                        "Pilih file input terlebih dahulu."
                    )

                source = self.files[0]

                pages = parse_page_ranges(
                    self.page_input.get()
                )

                if operation == "Pisahkan PDF":
                    result = split_pdf(
                        source,
                        output,
                        pages,
                    )

                elif operation == "Hapus halaman":
                    result = remove_pages(
                        source,
                        output,
                        pages or [],
                    )

                elif operation == "Putar halaman":
                    try:
                        angle = int(
                            self.extra_input.get()
                        )
                    except ValueError:
                        raise ValueError(
                            "Sudut rotasi harus berupa angka."
                        )

                    result = rotate_pages(
                        source,
                        output,
                        pages,
                        angle,
                    )

                elif operation == "Atur ulang halaman":
                    order_text = (
                        self.extra_input.get()
                        .strip()
                    )

                    if not order_text:
                        raise ValueError(
                            "Masukkan urutan halaman."
                        )

                    try:
                        order = [
                            int(x.strip()) - 1
                            for x in order_text.split(",")
                        ]
                    except ValueError:
                        raise ValueError(
                            "Urutan halaman harus berupa "
                            "angka yang dipisahkan koma."
                        )

                    result = reorder_pages(
                        source,
                        output,
                        order,
                    )

                elif operation == "Ekstrak gambar":
                    result = extract_images(
                        source,
                        output.parent
                        / f"{source.stem}_images",
                    )

                elif operation == "Kompres PDF":
                    result = compress_pdf(
                        source,
                        output,
                    )

                elif operation == "Watermark":
                    watermark_text = (
                        self.extra_input.get()
                    )

                    if not watermark_text.strip():
                        raise ValueError(
                            "Masukkan teks watermark."
                        )

                    try:
                        opacity = (
                            float(
                                self.watermark_opacity.get()
                            )
                            / 100
                        )

                        size = int(
                            self.watermark_size.get()
                        )

                        angle = int(
                            self.watermark_angle.get()
                        )

                    except ValueError:
                        raise ValueError(
                            "Opacity, ukuran, dan rotasi "
                            "harus berupa angka."
                        )

                    result = add_watermark(
                        source,
                        output,
                        watermark_text,
                        self.watermark_position.get(),
                        opacity,
                        size,
                        angle,
                    )

                else:
                    raise ValueError(
                        f"Operasi tidak dikenali: "
                        f"{operation}"
                    )

            self.status.set(
                f"Completed • {result} item(s) processed"
            )

            messagebox.showinfo(
                "Operation complete",
                f"Operasi berhasil.\n\n"
                f"{result} item diproses.\n\n"
                f"Output:\n{output}",
            )

        except (
            ValueError,
            FileNotFoundError,
            RuntimeError,
            OSError,
        ) as error:

            self.status.set(
                "Operation failed"
            )

            messagebox.showerror(
                "Operation failed",
                str(error),
            )

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _open_settings(self):
        window = tk.Toplevel(
            self.root
        )

        window.title("Settings")
        window.geometry("340x390")
        window.resizable(
            False,
            False,
        )

        window.configure(
            bg=self.COLORS["bg"]
        )

        window.transient(
            self.root
        )

        container = tk.Frame(
            window,
            bg=self.COLORS["bg"],
            padx=22,
            pady=22,
        )
        container.pack(
            fill="both",
            expand=True,
        )

        header = tk.Frame(
            container,
            bg=self.COLORS["bg"],
        )
        header.pack(
            fill="x",
            pady=(0, 20),
        )

        tk.Label(
            header,
            text="☰",
            bg=self.COLORS["bg"],
            fg=self.COLORS["accent"],
            font=("Segoe UI Symbol", 18),
        ).pack(side="left")

        tk.Label(
            header,
            text="Settings",
            bg=self.COLORS["bg"],
            fg=self.COLORS["text"],
            font=("Segoe UI", 15, "bold"),
        ).pack(
            side="left",
            padx=(8, 0),
        )

        # --------------------------------------------------------------
        # General
        # --------------------------------------------------------------

        tk.Label(
            container,
            text="GENERAL",
            bg=self.COLORS["bg"],
            fg=self.COLORS["accent"],
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 8),
        )

        settings_card = tk.Frame(
            container,
            bg=self.COLORS["surface"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        settings_card.pack(
            fill="x",
        )

        tk.Checkbutton(
            settings_card,
            text="Confirm before processing",
            variable=self.confirm_before_run,
            bg=self.COLORS["surface"],
            fg=self.COLORS["text"],
            selectcolor=self.COLORS["surface_3"],
            activebackground=self.COLORS["surface"],
            activeforeground=self.COLORS["text"],
            font=("Segoe UI", 9),
        ).pack(
            anchor="w",
        )

        tk.Checkbutton(
            settings_card,
            text="Show file information in preview",
            variable=self.show_file_info,
            bg=self.COLORS["surface"],
            fg=self.COLORS["text"],
            selectcolor=self.COLORS["surface_3"],
            activebackground=self.COLORS["surface"],
            activeforeground=self.COLORS["text"],
            font=("Segoe UI", 9),
        ).pack(
            anchor="w",
            pady=(8, 0),
        )

        # --------------------------------------------------------------
        # About
        # --------------------------------------------------------------

        tk.Label(
            container,
            text="ABOUT",
            bg=self.COLORS["bg"],
            fg=self.COLORS["accent"],
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
            pady=(22, 8),
        )

        about = tk.Frame(
            container,
            bg=self.COLORS["surface"],
            highlightbackground=self.COLORS["border"],
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        about.pack(
            fill="x",
        )

        tk.Label(
            about,
            text="PDF Toolkit",
            bg=self.COLORS["surface"],
            fg=self.COLORS["text"],
            font=("Segoe UI", 10, "bold"),
        ).pack(
            anchor="w"
        )

        tk.Label(
            about,
            text=(
                "Local PDF utilities for everyday "
                "document processing.\n"
                "No cloud upload required."
            ),
            justify="left",
            bg=self.COLORS["surface"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        ttk.Button(
            container,
            text="Close",
            command=window.destroy,
            style="Secondary.TButton",
        ).pack(
            anchor="e",
            pady=(18, 0),
        )

    # ------------------------------------------------------------------
    # Run GUI
    # ------------------------------------------------------------------


def run_gui() -> None:
    if TkinterDnD is not None:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    PdfToolkitApp(root)

    root.mainloop()