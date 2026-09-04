from pathlib import Path

from .file_utils import ensure_pdf_name, list_pdf_files
from .pdf_operations import (
    add_watermark, compress_pdf, extract_images, images_to_pdf, merge_pdfs,
    convert_pdf, parse_page_ranges, remove_pages, reorder_pages, rotate_pages,
    split_pdf,
)


def _choose_pdf(folder: Path) -> Path | None:
    files = list_pdf_files(folder)
    if not files:
        print("Tidak ada file PDF di folder ini.")
        return None
    for index, path in enumerate(files, 1):
        print(f"{index}. {path.name}")
    while True:
        try:
            choice = int(input("Pilih nomor PDF: "))
            if 1 <= choice <= len(files):
                return files[choice - 1]
        except ValueError:
            pass
        print(f"Masukkan angka 1-{len(files)}.")


def _pages(prompt: str):
    return parse_page_ranges(input(prompt).strip())


def run_cli() -> None:
    folder = Path.cwd()
    while True:
        print("\nPDF Toolkit (CLI)")
        print("1. Gabungkan PDF   2. Gabungkan halaman terpilih")
        print("3. Pisahkan PDF    4. Hapus halaman")
        print("5. Putar halaman   6. Atur ulang halaman")
        print("7. Ekstrak gambar  8. Kompres PDF")
        print("9. Watermark       10. Gambar ke PDF")
        print("11. Konversi PDF   12. Keluar")
        choice = input("Pilih menu: ").strip()
        try:
            if choice in {"1", "2"}:
                files = list_pdf_files(folder)
                output = folder / ensure_pdf_name(input("Nama output: "), "merged.pdf")
                selected = _pages("Halaman (kosong/all untuk semua): ") if choice == "2" else None
                print(f"Berhasil menggabungkan {merge_pdfs(files, output, selected)} file.")
            elif choice == "3":
                source = _choose_pdf(folder)
                if source:
                    output = folder / ensure_pdf_name(input("Nama output: "), f"{source.stem}_split.pdf")
                    print(f"Berhasil menyimpan {split_pdf(source, output, _pages('Halaman: '))} halaman.")
            elif choice == "4":
                source = _choose_pdf(folder)
                if source:
                    output = folder / ensure_pdf_name(input("Nama output: "), f"{source.stem}_edited.pdf")
                    print(f"Tersisa {remove_pages(source, output, _pages('Halaman yang dihapus: ') or [])} halaman.")
            elif choice == "5":
                source = _choose_pdf(folder)
                if source:
                    output = folder / ensure_pdf_name(input("Nama output: "), f"{source.stem}_rotated.pdf")
                    angle = int(input("Sudut (90/180/270): "))
                    print(f"Mengubah {rotate_pages(source, output, _pages('Halaman (all untuk semua): '), angle)} halaman.")
            elif choice == "6":
                source = _choose_pdf(folder)
                if source:
                    order = [int(item.strip()) - 1 for item in input("Urutan halaman: ").split(",")]
                    output = folder / ensure_pdf_name(input("Nama output: "), f"{source.stem}_reordered.pdf")
                    print(f"Berhasil mengatur {reorder_pages(source, output, order)} halaman.")
            elif choice == "7":
                source = _choose_pdf(folder)
                if source:
                    print(f"Mengekstrak {extract_images(source, folder / f'{source.stem}_images')} gambar.")
            elif choice == "8":
                source = _choose_pdf(folder)
                if source:
                    output = folder / ensure_pdf_name(input("Nama output: "), f"{source.stem}_compressed.pdf")
                    print(f"Mengompres {compress_pdf(source, output)} halaman.")
            elif choice == "9":
                source = _choose_pdf(folder)
                if source:
                    output = folder / ensure_pdf_name(input("Nama output: "), f"{source.stem}_watermarked.pdf")
                    print(f"Menambahkan watermark ke {add_watermark(source, output, input('Teks watermark: '))} halaman.")
            elif choice == "10":
                images = [Path(item.strip()) for item in input("Path gambar, pisahkan koma: ").split(",")]
                output = folder / ensure_pdf_name(input("Nama output: "), "images.pdf")
                print(f"Berhasil mengubah {images_to_pdf(images, output)} gambar.")
            elif choice == "11":
                source = _choose_pdf(folder)
                if source:
                    format_name = input("Format tujuan (TXT/HTML/DOCX): ").strip().upper()
                    extension = format_name.lower()
                    output = folder / input("Nama output: ").strip()
                    if output.suffix.lower() != f".{extension}":
                        output = output.with_suffix(f".{extension}")
                    print(f"Berhasil mengonversi {convert_pdf(source, output, format_name)} halaman.")
            elif choice == "12":
                return
            else:
                print("Menu tidak tersedia.")
        except (ValueError, FileNotFoundError, RuntimeError) as error:
            print(f"Gagal: {error}")