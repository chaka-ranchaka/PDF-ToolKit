import fitz

import re
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from pdf_toolkit.pdf_operations import (
    add_watermark,
    compress_pdf,
    convert_pdf,
    extract_images,
    images_to_pdf,
    merge_pdfs,
    parse_page_ranges,
    remove_pages,
    reorder_pages,
    rotate_pages,
    split_pdf,
    convert_pdf_color,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a small three-page PDF used by most tests."""
    path = tmp_path / "sample.pdf"
    writer = PdfWriter()

    for _ in range(3):
        writer.add_blank_page(width=612, height=792)

    with path.open("wb") as file:
        writer.write(file)

    return path


@pytest.fixture
def second_pdf(tmp_path: Path) -> Path:
    """Create a second PDF with two pages for merge tests."""
    path = tmp_path / "second.pdf"
    writer = PdfWriter()

    for _ in range(2):
        writer.add_blank_page(width=612, height=792)

    with path.open("wb") as file:
        writer.write(file)

    return path


@pytest.fixture
def sample_text_pdf(tmp_path: Path) -> Path:
    """Create a PDF containing extractable text for conversion tests."""
    path = tmp_path / "text.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)

    # pypdf alone does not provide a convenient text writer. ReportLab is
    # already a project dependency, so use it only for this test fixture.
    from reportlab.pdfgen import canvas

    canvas_writer = canvas.Canvas(str(path), pagesize=(612, 792))
    canvas_writer.drawString(72, 720, "PDF ToolKit Test")
    canvas_writer.drawString(72, 700, "First page")
    canvas_writer.showPage()
    canvas_writer.drawString(72, 720, "Second page")
    canvas_writer.showPage()
    canvas_writer.save()

    return path


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a small RGB PNG for images-to-PDF tests."""
    from PIL import Image

    path = tmp_path / "sample.png"
    image = Image.new("RGB", (120, 80), "white")
    image.save(path)
    image.close()

    return path


@pytest.fixture
def sample_image_pdf(tmp_path: Path) -> Path:
    """Create a PDF containing an embedded raster image."""
    from PIL import Image

    image_path = tmp_path / "embedded.png"
    image = Image.new("RGB", (120, 80), "white")
    image.save(image_path)
    image.close()

    path = tmp_path / "image.pdf"

    from reportlab.pdfgen import canvas

    canvas_writer = canvas.Canvas(str(path), pagesize=(612, 792))
    canvas_writer.drawImage(str(image_path), 72, 600, width=120, height=80)
    canvas_writer.showPage()
    canvas_writer.save()

    return path


def page_count(path: Path) -> int:
    return len(PdfReader(str(path)).pages)


# ---------------------------------------------------------------------------
# parse_page_ranges
# ---------------------------------------------------------------------------

def test_parse_page_ranges():
    assert parse_page_ranges("2,5,8-10") == [1, 4, 7, 8, 9]
    assert parse_page_ranges("10-8") == [7, 8, 9]
    assert parse_page_ranges("all") is None


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
        "a",
        "2-",
        "-2",
        "2--5",
        "1,a",
        ",,,",
    ],
)
def test_parse_page_ranges_rejects_invalid_input(value):
    with pytest.raises(ValueError):
        parse_page_ranges(value)


@pytest.mark.parametrize("value", ["ALL", " all "])
def test_parse_page_ranges_accepts_all_case_insensitive(value):
    assert parse_page_ranges(value) is None


def test_parse_page_ranges_empty_input():
    assert parse_page_ranges("") is None


def test_parse_page_ranges_whitespace_input_rejected():
    with pytest.raises(ValueError, match="setidaknya satu"):
        parse_page_ranges("   ")


def test_parse_page_ranges_removes_duplicates_and_sorts():
    assert parse_page_ranges("5,2,2,4-3") == [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# merge_pdfs
# ---------------------------------------------------------------------------

def test_merge_pdfs_merges_all_pages(sample_pdf, second_pdf, tmp_path):
    output = tmp_path / "merged.pdf"

    result = merge_pdfs([sample_pdf, second_pdf], output)

    assert result == 2
    assert output.exists()
    assert page_count(output) == 5


def test_merge_pdfs_with_selected_pages(sample_pdf, second_pdf, tmp_path):
    output = tmp_path / "merged-selected.pdf"

    result = merge_pdfs(
        [sample_pdf, second_pdf],
        output,
        selected_pages=[0, 2],
    )

    assert result == 2
    assert page_count(output) == 3


def test_merge_pdfs_rejects_empty_inputs(tmp_path):
    output = tmp_path / "merged.pdf"

    with pytest.raises(ValueError, match="setidaknya satu"):
        merge_pdfs([], output)


def test_merge_pdfs_rejects_missing_input(tmp_path):
    missing = tmp_path / "missing.pdf"
    output = tmp_path / "merged.pdf"

    with pytest.raises(FileNotFoundError):
        merge_pdfs([missing], output)


def test_merge_pdfs_rejects_output_equal_to_input(sample_pdf, tmp_path):
    with pytest.raises(ValueError):
        merge_pdfs([sample_pdf], sample_pdf)


def test_merge_pdfs_rejects_when_selected_pages_match_no_pages(
    sample_pdf, tmp_path
):
    output = tmp_path / "merged.pdf"

    with pytest.raises(ValueError, match="Tidak ada halaman"):
        merge_pdfs([sample_pdf], output, selected_pages=[99])


# ---------------------------------------------------------------------------
# split_pdf
# ---------------------------------------------------------------------------

def test_split_pdf_all_pages(sample_pdf, tmp_path):
    output = tmp_path / "split.pdf"

    result = split_pdf(sample_pdf, output, None)

    assert result == 3
    assert page_count(output) == 3


def test_split_pdf_selected_pages(sample_pdf, tmp_path):
    output = tmp_path / "split-selected.pdf"

    result = split_pdf(sample_pdf, output, [0, 2])

    assert result == 2
    assert page_count(output) == 2


def test_split_pdf_rejects_no_matching_pages(sample_pdf, tmp_path):
    output = tmp_path / "split.pdf"

    with pytest.raises(ValueError, match="Tidak ada halaman"):
        split_pdf(sample_pdf, output, [99])


def test_split_pdf_rejects_output_equal_to_input(sample_pdf):
    with pytest.raises(ValueError):
        split_pdf(sample_pdf, sample_pdf, None)


def test_split_pdf_rejects_missing_input(tmp_path):
    missing = tmp_path / "missing.pdf"
    output = tmp_path / "split.pdf"

    with pytest.raises(FileNotFoundError):
        split_pdf(missing, output, None)


# ---------------------------------------------------------------------------
# remove_pages
# ---------------------------------------------------------------------------

def test_remove_pages(sample_pdf, tmp_path):
    output = tmp_path / "removed.pdf"

    result = remove_pages(sample_pdf, output, [1])

    assert result == 2
    assert page_count(output) == 2


def test_remove_pages_can_remove_multiple_pages(sample_pdf, tmp_path):
    output = tmp_path / "removed.pdf"

    result = remove_pages(sample_pdf, output, [0, 2])

    assert result == 1
    assert page_count(output) == 1


def test_remove_pages_rejects_removing_all_pages(sample_pdf, tmp_path):
    output = tmp_path / "removed.pdf"

    with pytest.raises(ValueError, match="Semua halaman"):
        remove_pages(sample_pdf, output, [0, 1, 2])


def test_remove_pages_ignores_out_of_range_indexes(sample_pdf, tmp_path):
    output = tmp_path / "removed.pdf"

    result = remove_pages(sample_pdf, output, [99])

    assert result == 3
    assert page_count(output) == 3


def test_remove_pages_rejects_output_equal_to_input(sample_pdf):
    with pytest.raises(ValueError):
        remove_pages(sample_pdf, sample_pdf, [0])


# ---------------------------------------------------------------------------
# rotate_pages
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("angle", [90, 180, 270])
def test_rotate_pages_selected_page(sample_pdf, tmp_path, angle):
    output = tmp_path / f"rotated-{angle}.pdf"

    result = rotate_pages(sample_pdf, output, [1], angle)

    assert result == 1

    reader = PdfReader(str(output))
    assert reader.pages[0].rotation == 0
    assert reader.pages[1].rotation == angle
    assert reader.pages[2].rotation == 0


@pytest.mark.parametrize("angle", [90, 180, 270])
def test_rotate_pages_all_pages(sample_pdf, tmp_path, angle):
    output = tmp_path / f"rotated-all-{angle}.pdf"

    result = rotate_pages(sample_pdf, output, None, angle)

    assert result == 3

    reader = PdfReader(str(output))
    assert all(page.rotation == angle for page in reader.pages)


@pytest.mark.parametrize("angle", [0, 45, 360, -90])
def test_rotate_pages_rejects_invalid_angle(sample_pdf, tmp_path, angle):
    output = tmp_path / "rotated.pdf"

    with pytest.raises(ValueError, match="Sudut rotasi"):
        rotate_pages(sample_pdf, output, None, angle)


def test_rotate_pages_with_non_matching_index(sample_pdf, tmp_path):
    output = tmp_path / "rotated.pdf"

    result = rotate_pages(sample_pdf, output, [99], 90)

    assert result == 0
    assert all(page.rotation == 0 for page in PdfReader(str(output)).pages)


# ---------------------------------------------------------------------------
# reorder_pages
# ---------------------------------------------------------------------------

def test_reorder_pages(sample_pdf, tmp_path):
    output = tmp_path / "reordered.pdf"

    result = reorder_pages(sample_pdf, output, [2, 0, 1])

    assert result == 3
    assert page_count(output) == 3


@pytest.mark.parametrize(
    "order",
    [
        [],
        [-1, 0, 1],
        [0, 1, 99],
    ],
)
def test_reorder_pages_rejects_invalid_order(sample_pdf, tmp_path, order):
    output = tmp_path / "reordered.pdf"

    with pytest.raises(ValueError, match="tidak valid"):
        reorder_pages(sample_pdf, output, order)


def test_reorder_pages_allows_duplicate_indexes(sample_pdf, tmp_path):
    """Document current behavior: duplicate page indexes are accepted."""
    output = tmp_path / "reordered.pdf"

    result = reorder_pages(sample_pdf, output, [0, 0, 2])

    assert result == 3
    assert page_count(output) == 3


# ---------------------------------------------------------------------------
# extract_images
# ---------------------------------------------------------------------------

def test_extract_images(sample_image_pdf, tmp_path):
    output_dir = tmp_path / "extracted"

    result = extract_images(sample_image_pdf, output_dir)

    assert result >= 1
    extracted_files = list(output_dir.iterdir())
    assert len(extracted_files) == result
    assert all(path.is_file() for path in extracted_files)


def test_extract_images_creates_output_directory(sample_image_pdf, tmp_path):
    output_dir = tmp_path / "nested" / "images"

    assert not output_dir.exists()

    result = extract_images(sample_image_pdf, output_dir)

    assert result >= 1
    assert output_dir.exists()


def test_extract_images_from_pdf_without_images(sample_pdf, tmp_path):
    output_dir = tmp_path / "extracted"

    result = extract_images(sample_pdf, output_dir)

    assert result == 0
    assert output_dir.exists()
    assert list(output_dir.iterdir()) == []


def test_extract_images_rejects_missing_input(tmp_path):
    missing = tmp_path / "missing.pdf"
    output_dir = tmp_path / "extracted"

    with pytest.raises(FileNotFoundError):
        extract_images(missing, output_dir)


# ---------------------------------------------------------------------------
# compress_pdf
# ---------------------------------------------------------------------------

def test_compress_pdf(sample_pdf, tmp_path):
    output = tmp_path / "compressed.pdf"

    result = compress_pdf(sample_pdf, output)

    assert result == 3
    assert output.exists()
    assert page_count(output) == 3


def test_compress_pdf_rejects_output_equal_to_input(sample_pdf):
    with pytest.raises(ValueError):
        compress_pdf(sample_pdf, sample_pdf)


def test_compress_pdf_rejects_missing_input(tmp_path):
    missing = tmp_path / "missing.pdf"
    output = tmp_path / "compressed.pdf"

    with pytest.raises(FileNotFoundError):
        compress_pdf(missing, output)


# ---------------------------------------------------------------------------
# add_watermark
# ---------------------------------------------------------------------------

def test_add_watermark(sample_pdf, tmp_path):
    output = tmp_path / "watermarked.pdf"

    result = add_watermark(
        sample_pdf,
        output,
        text="CONFIDENTIAL",
        position="Tengah",
        opacity=0.25,
        size=32,
        angle=35,
    )

    assert result == 3
    assert output.exists()
    assert page_count(output) == 3


@pytest.mark.parametrize(
    "position",
    ["Tengah", "Kiri atas", "Kanan atas", "Kiri bawah", "Kanan bawah"],
)
def test_add_watermark_supported_positions(sample_pdf, tmp_path, position):
    output = tmp_path / "watermarked.pdf"

    result = add_watermark(
        sample_pdf,
        output,
        text="TEST",
        position=position,
    )

    assert result == 3
    assert page_count(output) == 3


def test_add_watermark_rejects_empty_text(sample_pdf, tmp_path):
    output = tmp_path / "watermarked.pdf"

    with pytest.raises(ValueError, match="Teks watermark"):
        add_watermark(sample_pdf, output, "   ")


def test_add_watermark_rejects_invalid_position(sample_pdf, tmp_path):
    output = tmp_path / "watermarked.pdf"

    with pytest.raises(ValueError, match="Posisi watermark"):
        add_watermark(sample_pdf, output, "TEST", position="Bottom")


@pytest.mark.parametrize("opacity", [0, 0.04, 1.01, 2])
def test_add_watermark_rejects_invalid_opacity(sample_pdf, tmp_path, opacity):
    output = tmp_path / "watermarked.pdf"

    with pytest.raises(ValueError, match="Opacity"):
        add_watermark(sample_pdf, output, "TEST", opacity=opacity)


@pytest.mark.parametrize("size", [0, 7, 121, 200])
def test_add_watermark_rejects_invalid_size(sample_pdf, tmp_path, size):
    output = tmp_path / "watermarked.pdf"

    with pytest.raises(ValueError, match="Ukuran watermark"):
        add_watermark(sample_pdf, output, "TEST", size=size)


@pytest.mark.parametrize("angle", [-181, 181, 360])
def test_add_watermark_rejects_invalid_angle(sample_pdf, tmp_path, angle):
    output = tmp_path / "watermarked.pdf"

    with pytest.raises(ValueError, match="Rotasi watermark"):
        add_watermark(sample_pdf, output, "TEST", angle=angle)


def test_add_watermark_rejects_output_equal_to_input(sample_pdf):
    with pytest.raises(ValueError):
        add_watermark(sample_pdf, sample_pdf, "TEST")


# ---------------------------------------------------------------------------
# convert_pdf
# ---------------------------------------------------------------------------

def test_convert_pdf_to_txt(sample_text_pdf, tmp_path):
    output = tmp_path / "converted.txt"

    result = convert_pdf(sample_text_pdf, output, "TXT")

    assert result == 2
    assert output.exists()

    text = output.read_text(encoding="utf-8")
    assert "PDF ToolKit Test" in text
    assert "First page" in text
    assert "Second page" in text


def test_convert_pdf_to_html(sample_text_pdf, tmp_path):
    output = tmp_path / "converted.html"

    result = convert_pdf(sample_text_pdf, output, "HTML")

    assert result == 2
    assert output.exists()

    html = output.read_text(encoding="utf-8")
    assert "<!doctype html>" in html
    assert "<html lang=\"id\">" in html
    assert "PDF ToolKit Test" in html
    assert "First page" in html


def test_convert_pdf_to_html_escapes_text(tmp_path):
    """Ensure HTML conversion does not emit raw HTML from extracted text."""
    path = tmp_path / "special.pdf"

    from reportlab.pdfgen import canvas

    canvas_writer = canvas.Canvas(str(path), pagesize=(612, 792))
    canvas_writer.drawString(72, 720, "<script>alert('x')</script>")
    canvas_writer.showPage()
    canvas_writer.save()

    output = tmp_path / "converted.html"
    convert_pdf(path, output, "HTML")

    html = output.read_text(encoding="utf-8")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_convert_pdf_to_docx(sample_text_pdf, tmp_path):
    output = tmp_path / "converted.docx"

    result = convert_pdf(sample_text_pdf, output, "DOCX")

    assert result == 2
    assert output.exists()
    assert output.stat().st_size > 0

    from docx import Document

    document = Document(str(output))
    paragraphs = "\n".join(paragraph.text for paragraph in document.paragraphs)

    assert "PDF ToolKit Test" in paragraphs
    assert "First page" in paragraphs
    assert "Second page" in paragraphs


@pytest.mark.parametrize("format_name", ["pdf", "PNG", "DOC", "", None])
def test_convert_pdf_rejects_unsupported_format(
    sample_text_pdf, tmp_path, format_name
):
    output = tmp_path / "converted"

    with pytest.raises(ValueError, match="tidak didukung"):
        convert_pdf(sample_text_pdf, output, format_name)


def test_convert_pdf_rejects_output_equal_to_input(sample_text_pdf):
    with pytest.raises(ValueError):
        convert_pdf(sample_text_pdf, sample_text_pdf, "TXT")


def test_convert_pdf_rejects_missing_input(tmp_path):
    missing = tmp_path / "missing.pdf"
    output = tmp_path / "converted.txt"

    with pytest.raises(FileNotFoundError):
        convert_pdf(missing, output, "TXT")


# ---------------------------------------------------------------------------
# images_to_pdf
# ---------------------------------------------------------------------------

def test_images_to_pdf(sample_image, tmp_path):
    output = tmp_path / "images.pdf"

    result = images_to_pdf([sample_image], output)

    assert result == 1
    assert output.exists()
    assert page_count(output) == 1


def test_images_to_pdf_multiple_images(tmp_path):
    from PIL import Image

    image_paths = []

    for index in range(3):
        path = tmp_path / f"image-{index}.png"
        image = Image.new("RGB", (120, 80), "white")
        image.save(path)
        image.close()
        image_paths.append(path)

    output = tmp_path / "images.pdf"

    result = images_to_pdf(image_paths, output)

    assert result == 3
    assert page_count(output) == 3


def test_images_to_pdf_rejects_empty_input(tmp_path):
    output = tmp_path / "images.pdf"

    with pytest.raises(ValueError, match="setidaknya satu"):
        images_to_pdf([], output)


def test_images_to_pdf_rejects_missing_image(tmp_path):
    missing = tmp_path / "missing.png"
    output = tmp_path / "images.pdf"

    with pytest.raises(FileNotFoundError):
        images_to_pdf([missing], output)


def test_images_to_pdf_rejects_output_equal_to_input(sample_image):
    with pytest.raises(ValueError):
        images_to_pdf([sample_image], sample_image)


# ---------------------------------------------------------------------------
# Cross-cutting / regression tests
# ---------------------------------------------------------------------------

def test_all_generated_pdf_outputs_are_readable(
    sample_pdf,
    second_pdf,
    sample_text_pdf,
    sample_image,
    tmp_path,
):
    """Smoke-test the major PDF-producing operations end-to-end."""
    merged = tmp_path / "merged.pdf"
    split = tmp_path / "split.pdf"
    rotated = tmp_path / "rotated.pdf"
    reordered = tmp_path / "reordered.pdf"
    compressed = tmp_path / "compressed.pdf"
    watermarked = tmp_path / "watermarked.pdf"
    image_pdf = tmp_path / "from-image.pdf"

    merge_pdfs([sample_pdf, second_pdf], merged)
    split_pdf(sample_pdf, split, [0, 2])
    rotate_pages(sample_pdf, rotated, [0], 90)
    reorder_pages(sample_pdf, reordered, [2, 1, 0])
    compress_pdf(sample_pdf, compressed)
    add_watermark(sample_pdf, watermarked, "TEST")
    images_to_pdf([sample_image], image_pdf)

    for output in [
        merged,
        split,
        rotated,
        reordered,
        compressed,
        watermarked,
        image_pdf,
    ]:
        reader = PdfReader(str(output))
        assert len(reader.pages) > 0


def test_operations_do_not_create_files_outside_tmp_path(sample_pdf, tmp_path):
    """All test artifacts should live inside pytest's temporary directory."""
    output = tmp_path / "output.pdf"

    merge_pdfs([sample_pdf], output)

    assert output.parent == tmp_path


# Keep the module free of accidental unused test imports while making the
# intended PDF output behavior explicit.
def test_pdf_reader_can_open_sample_pdf(sample_pdf):
    reader = PdfReader(str(sample_pdf))
    assert len(reader.pages) == 3
    assert reader.pages[0].mediabox.width > 0
    assert reader.pages[0].mediabox.height > 0

def test_convert_pdf_color_grayscale(sample_pdf, tmp_path):
    output = tmp_path / "grayscale.pdf"

    result = convert_pdf_color(
        sample_pdf,
        output,
        mode="grayscale",
    )

    assert result == 3
    assert output.exists()
    assert output.stat().st_size > 0

    document = fitz.open(output)

    try:
        assert document.page_count == 3

        for page in document:
            pixmap = page.get_pixmap(alpha=False)

            assert pixmap.n > 0

            samples = pixmap.samples

            for index in range(0, len(samples), pixmap.n):
                red = samples[index]
                green = samples[index + 1]
                blue = samples[index + 2]

                assert red == green == blue
    finally:
        document.close()


def test_convert_pdf_color_blackwhite(sample_pdf, tmp_path):
    output = tmp_path / "blackwhite.pdf"

    result = convert_pdf_color(
        sample_pdf,
        output,
        mode="blackwhite",
    )

    assert result == 3
    assert output.exists()
    assert output.stat().st_size > 0

    document = fitz.open(output)

    try:
        assert document.page_count == 3

        for page in document:
            pixmap = page.get_pixmap(alpha=False)

            samples = pixmap.samples

            for index in range(0, len(samples), pixmap.n):
                red = samples[index]
                green = samples[index + 1]
                blue = samples[index + 2]

                assert red in {0, 255}
                assert green in {0, 255}
                assert blue in {0, 255}

                assert red == green == blue
    finally:
        document.close()


@pytest.mark.parametrize("mode", ["invalid", "", "color"])
def test_convert_pdf_color_rejects_invalid_mode(sample_pdf, tmp_path, mode):
    output = tmp_path / "output.pdf"

    with pytest.raises(ValueError, match="Mode warna tidak didukung"):
        convert_pdf_color(
            sample_pdf,
            output,
            mode=mode,
        )


@pytest.mark.parametrize("dpi", [71, 301, 0, 500])
def test_convert_pdf_color_rejects_invalid_dpi(sample_pdf, tmp_path, dpi):
    output = tmp_path / "output.pdf"

    with pytest.raises(ValueError, match="DPI harus antara 72 dan 300"):
        convert_pdf_color(
            sample_pdf,
            output,
            mode="grayscale",
            dpi=dpi,
        )

# ---------------------------------------------------------------------------
# Color grayscale/blackwhite conversion tests
# ---------------------------------------------------------------------------

def test_convert_pdf_color_rejects_output_equal_to_input(sample_pdf):
    with pytest.raises(ValueError):
        convert_pdf_color(
            sample_pdf,
            sample_pdf,
            mode="grayscale",
        )