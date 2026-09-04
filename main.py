import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF Toolkit")
    parser.add_argument("--cli", action="store_true", help="jalankan antarmuka terminal")
    args = parser.parse_args()

    if args.cli:
        from pdf_toolkit.cli import run_cli

        run_cli()
        return

    from pdf_toolkit.gui import run_gui

    run_gui()


if __name__ == "__main__":
    main()
