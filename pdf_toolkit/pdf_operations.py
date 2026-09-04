from io import BytesIO
from html import escape
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .file_utils import require_distinct_output, require_existing_file

try:
    from PIL import Image
except ImportError:  # pragma: no cover - dependency is declared in requirements.txt
    Image = None


def parse_page_ranges(value: str) -> list[int] | None:
    """Convert 1-based input such as ``2,5,8-10`` to sorted 0-based indexes."""
    if not value or value.strip().lower() == "all":
        return None
    pages: set[int] = set()
    try:
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                start, end = (int(item) for item in part.split("-", 1))
                if start < 1 or end < 1:
                    raise ValueError
                start, end = sorted((start, end))
                pages.update(range(start - 1, end))
            else:
                page = int(part)
                if page < 1:
                    raise ValueError
                pages.add(page - 1)
    except (TypeError, ValueError) as error:
        raise ValueError("Format halaman tidak valid. Contoh: 2,5,8-10") from error
    if not pages:
        raise ValueError("Masukkan setidaknya satu halaman.")
    return sorted(pages)


def _pages(reader: PdfReader, selected_pages: list[int] | None):
    if selected_pages is None:
        return reader.pages
    return [reader.pages[index] for index in selected_pages if 0 <= index < len(reader.pages)]


def merge_pdfs(inputs: list[Path], output: Path, selected_pages: list[int] | None = None) -> int:
    if not inputs:
        raise ValueError("Pilih setidaknya satu file PDF.")
    for path in inputs:
        require_existing_file(path)
    require_distinct_output(output, inputs)
    writer = PdfWriter()
    page_count = 0
    for path in inputs:
        for page in _pages(PdfReader(str(path)), selected_pages):
            writer.add_page(page)
            page_count += 1
    if page_count == 0:
        raise ValueError("Tidak ada halaman yang cocok dengan pilihan.")
    with output.open("wb") as file:
        writer.write(file)
    return len(inputs)


def split_pdf(input_path: Path, output: Path, selected_pages: list[int] | None) -> int:
    require_existing_file(input_path)
    require_distinct_output(output, [input_path])
    pages = list(_pages(PdfReader(str(input_path)), selected_pages))
    if not pages:
        raise ValueError("Tidak ada halaman yang cocok dengan pilihan.")
    writer = PdfWriter()
    for page in pages:
        writer.add_page(page)
    with output.open("wb") as file:
        writer.write(file)
    return len(pages)


def remove_pages(input_path: Path, output: Path, pages_to_remove: list[int]) -> int:
    require_existing_file(input_path)
    require_distinct_output(output, [input_path])
    reader = PdfReader(str(input_path))
    writer = PdfWriter()
    removed = set(pages_to_remove)
    for index, page in enumerate(reader.pages):
        if index not in removed:
            writer.add_page(page)
    if not writer.pages:
        raise ValueError("Semua halaman tidak boleh dihapus.")
    with output.open("wb") as file:
        writer.write(file)
    return len(writer.pages)


def rotate_pages(input_path: Path, output: Path, selected_pages: list[int] | None, angle: int) -> int:
    if angle not in {90, 180, 270}:
        raise ValueError("Sudut rotasi harus 90, 180, atau 270.")
    require_existing_file(input_path)
    require_distinct_output(output, [input_path])
    reader = PdfReader(str(input_path))
    chosen = set(range(len(reader.pages))) if selected_pages is None else set(selected_pages)
    writer = PdfWriter()
    changed = 0
    for index, page in enumerate(reader.pages):
        if index in chosen:
            page.rotate(angle)
            changed += 1
        writer.add_page(page)
    with output.open("wb") as file:
        writer.write(file)
    return changed


def reorder_pages(input_path: Path, output: Path, order: list[int]) -> int:
    require_existing_file(input_path)
    require_distinct_output(output, [input_path])
    reader = PdfReader(str(input_path))
    if not order or any(index < 0 or index >= len(reader.pages) for index in order):
        raise ValueError("Urutan halaman mengandung nomor yang tidak valid.")
    writer = PdfWriter()
    for index in order:
        writer.add_page(reader.pages[index])
    with output.open("wb") as file:
        writer.write(file)
    return len(order)


def extract_images(input_path: Path, output_dir: Path) -> int:
    if Image is None:
        raise RuntimeError("Pillow belum terpasang. Jalankan: pip install -r requirements.txt")
    require_existing_file(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for page_number, page in enumerate(PdfReader(str(input_path)).pages, start=1):
        for image_number, image in enumerate(page.images, start=1):
            suffix = Path(image.name).suffix.lower() or ".png"
            target = output_dir / f"{input_path.stem}_page{page_number}_img{image_number}{suffix}"
            target.write_bytes(image.data)
            count += 1
    return count


def compress_pdf(input_path: Path, output: Path) -> int:
    require_existing_file(input_path)
    require_distinct_output(output, [input_path])
    reader = PdfReader(str(input_path))
    writer = PdfWriter()
    for page in reader.pages:
        page.compress_content_streams()
        writer.add_page(page)
    with output.open("wb") as file:
        writer.write(file)
    return len(reader.pages)


def add_watermark(
    input_path: Path,
    output: Path,
    text: str,
    position: str = "Tengah",
    opacity: float = 0.25,
    size: int = 32,
    angle: int = 35,
) -> int:
    if not text.strip():
        raise ValueError("Teks watermark tidak boleh kosong.")
    require_existing_file(input_path)
    require_distinct_output(output, [input_path])
    try:
        from reportlab.pdfgen import canvas
    except ImportError as error:
        raise RuntimeError("ReportLab belum terpasang. Jalankan: pip install -r requirements.txt") from error
    if position not in {"Tengah", "Kiri atas", "Kanan atas", "Kiri bawah", "Kanan bawah"}:
        raise ValueError("Posisi watermark tidak valid.")
    if not 0.05 <= opacity <= 1:
        raise ValueError("Opacity watermark harus antara 0.05 dan 1.")
    if not 8 <= size <= 120:
        raise ValueError("Ukuran watermark harus antara 8 dan 120.")
    if not -180 <= angle <= 180:
        raise ValueError("Rotasi watermark harus antara -180 dan 180.")
    reader = PdfReader(str(input_path))
    writer = PdfWriter()
    for page in reader.pages:
        stream = BytesIO()
        canvas_writer = canvas.Canvas(stream, pagesize=(float(page.mediabox.width), float(page.mediabox.height)))
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        canvas_writer.setFillAlpha(opacity)
        canvas_writer.setFont("Helvetica-Bold", size)
        anchors = {
            "Tengah": (width / 2, height / 2, "center"),
            "Kiri atas": (size, height - size * 1.5, "left"),
            "Kanan atas": (width - size, height - size * 1.5, "right"),
            "Kiri bawah": (size, size * 1.5, "left"),
            "Kanan bawah": (width - size, size * 1.5, "right"),
        }
        x, y, alignment = anchors[position]
        canvas_writer.saveState()
        canvas_writer.translate(x, y)
        canvas_writer.rotate(angle)
        canvas_writer.drawCentredString(0, 0, text) if alignment == "center" else canvas_writer.drawString(0 if alignment == "left" else -canvas_writer.stringWidth(text, "Helvetica-Bold", size), 0, text)
        canvas_writer.restoreState()
        canvas_writer.save()
        stream.seek(0)
        page.merge_page(PdfReader(stream).pages[0])
        writer.add_page(page)
    with output.open("wb") as file:
        writer.write(file)
    return len(reader.pages)


def convert_pdf(input_path: Path, output: Path, format_name: str) -> int:
    """Convert PDF text into a plain-text, HTML, or DOCX document."""
    require_existing_file(input_path)
    require_distinct_output(output, [input_path])
    if format_name not in {"TXT", "HTML", "DOCX"}:
        raise ValueError("Format konversi tidak didukung.")
    pages = PdfReader(str(input_path)).pages
    text_pages = [page.extract_text() or "" for page in pages]
    text = "\n\n".join(text_pages)
    if format_name == "TXT":
        output.write_text(text, encoding="utf-8")
    elif format_name == "HTML":
        body = "\n".join(f"<p>{escape(page).replace(chr(10), '<br>')}</p>" for page in text_pages)
        output.write_text(
            f"<!doctype html>\n<html lang=\"id\"><head><meta charset=\"utf-8\"><title>{escape(input_path.stem)}</title></head><body>{body}</body></html>",
            encoding="utf-8",
        )
    else:
        try:
            from docx import Document
        except ImportError as error:
            raise RuntimeError("python-docx belum terpasang. Jalankan: pip install -r requirements.txt") from error
        document = Document()
        for index, page_text in enumerate(text_pages):
            if index:
                document.add_page_break()
            for paragraph in page_text.splitlines() or [""]:
                document.add_paragraph(paragraph)
        document.save(output)
    return len(pages)


def images_to_pdf(image_paths: list[Path], output: Path) -> int:
    if Image is None:
        raise RuntimeError("Pillow belum terpasang. Jalankan: pip install -r requirements.txt")
    if not image_paths:
        raise ValueError("Pilih setidaknya satu gambar.")
    for path in image_paths:
        require_existing_file(path)
    require_distinct_output(output, image_paths)
    images = []
    try:
        for path in image_paths:
            images.append(Image.open(path).convert("RGB"))
        images[0].save(output, save_all=True, append_images=images[1:])
    finally:
        for image in images:
            image.close()
    return len(image_paths)