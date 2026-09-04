from pathlib import Path


def ensure_pdf_name(name: str, default: str) -> str:
    value = (name or default).strip() or default
    return value if value.lower().endswith(".pdf") else f"{value}.pdf"


def list_pdf_files(folder: Path) -> list[Path]:
    return sorted(
        (path for path in folder.glob("*.pdf") if path.is_file()),
        key=lambda path: path.name.lower(),
    )


def require_distinct_output(output: Path, inputs: list[Path]) -> None:
    if any(path.resolve() == output.resolve() for path in inputs):
        raise ValueError("File output tidak boleh sama dengan file input.")


def require_existing_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"File tidak ditemukan: {path}")