from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from pypdf import PdfReader

try:
    import pymupdf as fitz
except ImportError:  # pragma: no cover - dependency is declared in requirements.txt
    fitz = None

from .pdf_operations import (
    add_watermark, compress_pdf, extract_images, images_to_pdf, merge_pdfs,
    convert_pdf, parse_page_ranges, remove_pages, reorder_pages, rotate_pages,
    split_pdf,
)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # pragma: no cover - fallback for systems without the optional GUI package
    DND_FILES, TkinterDnD = None, None


class PdfToolkitApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF Toolkit")
        self.root.geometry("820x650")
        self.root.minsize(700, 560)
        self.files: list[Path] = []
        self.operation = tk.StringVar(value="Gabungkan PDF")
        self.page_input = tk.StringVar()
        self.output_input = tk.StringVar()
        self.extra_input = tk.StringVar()
        self.watermark_position = tk.StringVar(value="Tengah")
        self.watermark_opacity = tk.StringVar(value="25")
        self.watermark_size = tk.StringVar(value="32")
        self.watermark_angle = tk.StringVar(value="35")
        self.convert_format = tk.StringVar(value="TXT")
        self.status = tk.StringVar(value="Siap digunakan")
        self._build()

    def _build(self):
        self.root.configure(bg="#f4f6f8")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("App.TFrame", background="#f4f6f8")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Title.TLabel", background="#f4f6f8", foreground="#17202a", font=("Segoe UI", 23, "bold"))
        style.configure("Muted.TLabel", background="#f4f6f8", foreground="#68737d", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#ffffff", foreground="#27323a")
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=(16, 9))
        frame = ttk.Frame(self.root, padding=26, style="App.TFrame")
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="PDF Toolkit", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text="Alat dokumen lokal yang ringkas, cepat, dan mudah dipakai", style="Muted.TLabel").pack(anchor="w", pady=(2, 20))
        card = ttk.Frame(frame, padding=18, style="Card.TFrame")
        card.pack(fill="both", expand=True)
        ttk.Label(card, text="Pilih operasi", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        selector = ttk.Combobox(card, textvariable=self.operation, state="readonly", values=[
            "Gabungkan PDF", "Gabungkan halaman terpilih", "Pisahkan PDF", "Hapus halaman",
            "Putar halaman", "Atur ulang halaman", "Ekstrak gambar", "Kompres PDF",
            "Watermark", "Gambar ke PDF", "Konversi PDF",
        ], font=("Segoe UI", 10))
        selector.pack(fill="x", pady=(4, 12))
        selector.bind("<<ComboboxSelected>>", lambda _event: self._update_labels())
        ttk.Label(card, text="File input (urutan merge dapat diubah)", style="Card.TLabel").pack(anchor="w")
        file_frame = ttk.Frame(card, style="Card.TFrame")
        file_frame.pack(fill="both", expand=True, pady=4)
        self.file_list = tk.Listbox(file_frame, selectmode=tk.EXTENDED, height=9, relief="flat", borderwidth=0,
                                    bg="#f4f6f8", fg="#27323a", selectbackground="#2e7d6f", font=("Segoe UI", 10))
        self.file_list.pack(side="left", fill="both", expand=True)
        if DND_FILES is not None:
            self.file_list.drop_target_register(DND_FILES)
            self.file_list.dnd_bind("<<Drop>>", self._drop_files)
        buttons = ttk.Frame(file_frame, style="Card.TFrame")
        buttons.pack(side="left", fill="y", padx=(8, 0))
        ttk.Button(buttons, text="+  Tambah file", command=self._add_files).pack(fill="x")
        ttk.Button(buttons, text="Hapus pilihan", command=self._remove_files).pack(fill="x", pady=4)
        ttk.Button(buttons, text="Naik", command=lambda: self._move(-1)).pack(fill="x")
        ttk.Button(buttons, text="Turun", command=lambda: self._move(1)).pack(fill="x", pady=4)
        form = ttk.Frame(card, style="Card.TFrame")
        form.pack(fill="x", pady=8)
        self.page_label = ttk.Label(form, text="Halaman (kosong = semua)")
        self.page_label.grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.page_input).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.extra_label = ttk.Label(form, text="Teks watermark / sudut / urutan")
        self.extra_label.grid(row=0, column=1, sticky="w")
        self.extra_entry = ttk.Entry(form, textvariable=self.extra_input)
        self.extra_entry.grid(row=1, column=1, sticky="ew")
        self.watermark_frame = ttk.Frame(form, style="Card.TFrame")
        ttk.Label(self.watermark_frame, text="Posisi").grid(row=0, column=0, sticky="w")
        ttk.Combobox(self.watermark_frame, textvariable=self.watermark_position, state="readonly", values=["Tengah", "Kiri atas", "Kanan atas", "Kiri bawah", "Kanan bawah"]).grid(row=1, column=0, sticky="ew", padx=(0, 6))
        ttk.Label(self.watermark_frame, text="Opacity (%)").grid(row=0, column=1, sticky="w")
        ttk.Entry(self.watermark_frame, textvariable=self.watermark_opacity, width=8).grid(row=1, column=1, sticky="ew", padx=(0, 6))
        ttk.Label(self.watermark_frame, text="Ukuran").grid(row=0, column=2, sticky="w")
        ttk.Entry(self.watermark_frame, textvariable=self.watermark_size, width=8).grid(row=1, column=2, sticky="ew", padx=(0, 6))
        ttk.Label(self.watermark_frame, text="Rotasi").grid(row=0, column=3, sticky="w")
        ttk.Entry(self.watermark_frame, textvariable=self.watermark_angle, width=8).grid(row=1, column=3, sticky="ew")
        for column in range(4):
            self.watermark_frame.columnconfigure(column, weight=1)
        self.convert_frame = ttk.Frame(form, style="Card.TFrame")
        ttk.Label(self.convert_frame, text="Format tujuan").pack(side="left")
        ttk.Combobox(self.convert_frame, textvariable=self.convert_format, state="readonly", values=["TXT", "HTML", "DOCX"], width=10).pack(side="left", padx=8)
        ttk.Label(form, text="File output").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(form, textvariable=self.output_input).grid(row=3, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(form, text="Pilih lokasi", command=self._choose_output).grid(row=3, column=1, sticky="ew")
        form.columnconfigure(0, weight=3)
        form.columnconfigure(1, weight=2)
        action_frame = ttk.Frame(card, style="Card.TFrame")
        action_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(action_frame, text="Lihat preview", command=self._preview).pack(side="left")
        ttk.Button(action_frame, text="Jalankan operasi", style="Action.TButton", command=self._run).pack(side="right")
        ttk.Label(frame, textvariable=self.status, style="Muted.TLabel").pack(anchor="w", pady=(10, 0))
        self._update_labels()

    def _update_labels(self):
        operation = self.operation.get()
        self.page_label.configure(text="Urutan halaman" if operation == "Atur ulang halaman" else "Halaman (kosong = semua)")
        is_watermark = operation == "Watermark"
        is_convert = operation == "Konversi PDF"
        self.watermark_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0)) if is_watermark else self.watermark_frame.grid_remove()
        self.convert_frame.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0)) if is_convert else self.convert_frame.grid_remove()
        self.extra_label.configure(text="Teks watermark" if is_watermark else "Sudut / urutan")
        self.extra_entry.configure(state="normal" if not is_convert else "disabled")

    def _add_files(self):
        types = [("PDF", "*.pdf")] if self.operation.get() != "Gambar ke PDF" else [("Gambar", "*.png *.jpg *.jpeg *.webp")]
        self.files.extend(Path(path) for path in filedialog.askopenfilenames(filetypes=types))
        self._refresh()

    def _drop_files(self, event):
        paths = self.root.tk.splitlist(event.data)
        allowed = ".pdf" if self.operation.get() != "Gambar ke PDF" else (".png", ".jpg", ".jpeg", ".webp")
        self.files.extend(Path(path) for path in paths if Path(path).suffix.lower() in allowed)
        self._refresh()

    def _remove_files(self):
        for index in reversed(self.file_list.curselection()):
            self.files.pop(index)
        self._refresh()

    def _move(self, direction: int):
        selected = self.file_list.curselection()
        if len(selected) != 1:
            return
        old_index, new_index = selected[0], selected[0] + direction
        if 0 <= new_index < len(self.files):
            self.files[old_index], self.files[new_index] = self.files[new_index], self.files[old_index]
            self._refresh()
            self.file_list.selection_set(new_index)

    def _refresh(self):
        self.file_list.delete(0, tk.END)
        for path in self.files:
            self.file_list.insert(tk.END, path.name)

    def _choose_output(self):
        extension = ".pdf"
        types = [("PDF", "*.pdf")]
        if self.operation.get() == "Konversi PDF":
            extension = "." + self.convert_format.get().lower()
            types = [(self.convert_format.get(), f"*{extension}")]
        path = filedialog.asksaveasfilename(defaultextension=extension, filetypes=types)
        if path:
            self.output_input.set(path)

    def _preview(self):
        if not self.files:
            messagebox.showwarning("Preview", "Pilih file input terlebih dahulu.")
            return
        try:
            operation = self.operation.get()
            details = [f"{operation}  |  {len(self.files)} file input"]
            for path in self.files:
                if not path.is_file():
                    raise FileNotFoundError(f"File tidak ditemukan: {path}")
                if path.suffix.lower() == ".pdf":
                    reader = PdfReader(str(path))
                    details.append(f"{path.name}  |  {len(reader.pages)} halaman")
                else:
                    details.append(path.name)
            if self.page_input.get().strip():
                details.append(f"Halaman: {self.page_input.get().strip()}")
            if operation == "Watermark":
                details.append(f"Watermark: {self.extra_input.get() or '(teks kosong)'}  |  {self.watermark_position.get()}")
            elif operation == "Konversi PDF":
                details.append(f"Format tujuan: {self.convert_format.get()}")
            image = self._load_preview_image(self.files[0])
            self._show_preview("Preview dokumen", "\n".join(details), image)
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as error:
            messagebox.showerror("Preview gagal", str(error))

    def _load_preview_image(self, path: Path) -> Image.Image:
        if path.suffix.lower() == ".pdf":
            if fitz is None:
                raise RuntimeError("PyMuPDF belum terpasang. Jalankan: pip install -r requirements.txt")
            document = fitz.open(str(path))
            try:
                if not document.page_count:
                    raise ValueError("PDF tidak memiliki halaman.")
                pixmap = document[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            finally:
                document.close()
        return Image.open(path).convert("RGB")

    def _show_preview(self, title: str, details: str, image: Image.Image):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("760x700")
        window.transient(self.root)
        window.grab_set()
        container = ttk.Frame(window, padding=16)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text=details, justify="left").pack(anchor="w", pady=(0, 12))
        image.thumbnail((700, 590), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        preview = ttk.Label(container, image=photo, anchor="center")
        preview.image = photo
        preview.pack(fill="both", expand=True)

    def _run(self):
        try:
            operation, output = self.operation.get(), Path(self.output_input.get())
            if not self.output_input.get().strip():
                raise ValueError("Pilih file output terlebih dahulu.")
            if operation == "Konversi PDF":
                if len(self.files) != 1:
                    raise ValueError("Pilih tepat satu file PDF untuk dikonversi.")
                result = convert_pdf(self.files[0], output, self.convert_format.get())
            elif operation == "Gambar ke PDF":
                result = images_to_pdf(self.files, output)
            elif operation == "Gabungkan PDF":
                result = merge_pdfs(self.files, output)
            elif operation == "Gabungkan halaman terpilih":
                result = merge_pdfs(self.files, output, parse_page_ranges(self.page_input.get()))
            else:
                if not self.files:
                    raise ValueError("Pilih file input terlebih dahulu.")
                source, pages = self.files[0], parse_page_ranges(self.page_input.get())
                if operation == "Pisahkan PDF": result = split_pdf(source, output, pages)
                elif operation == "Hapus halaman": result = remove_pages(source, output, pages or [])
                elif operation == "Putar halaman": result = rotate_pages(source, output, pages, int(self.extra_input.get()))
                elif operation == "Atur ulang halaman": result = reorder_pages(source, output, [int(x.strip()) - 1 for x in self.extra_input.get().split(",")])
                elif operation == "Ekstrak gambar": result = extract_images(source, output.parent / f"{source.stem}_images")
                elif operation == "Kompres PDF": result = compress_pdf(source, output)
                else:
                    result = add_watermark(source, output, self.extra_input.get(), self.watermark_position.get(),
                                           float(self.watermark_opacity.get()) / 100, int(self.watermark_size.get()),
                                           int(self.watermark_angle.get()))
            self.status.set(f"Selesai: {result} item diproses")
            messagebox.showinfo("Selesai", f"Operasi berhasil: {result} item diproses.")
        except (ValueError, FileNotFoundError, RuntimeError) as error:
            self.status.set("Operasi gagal")
            messagebox.showerror("Operasi gagal", str(error))


def run_gui() -> None:
    root = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    PdfToolkitApp(root)
    root.mainloop()