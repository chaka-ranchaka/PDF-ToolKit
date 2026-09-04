# 📕 PDF ToolKit

> A lightweight desktop PDF utility built with Python for merging, splitting, editing, converting, and managing PDF documents through a simple GUI and command-line interface.

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-FF6F00?style=for-the-badge)
![PyMuPDF](https://img.shields.io/badge/PDF-PyMuPDF-00599C?style=for-the-badge)

</p>

---

## ✨ Overview

**PDF ToolKit** is a desktop-based PDF utility developed with Python to simplify common PDF management tasks.

The application provides multiple PDF operations in a single tool, including merging, splitting, removing pages, rotating pages, reordering pages, watermarking, compression, image extraction, and document conversion.

PDF ToolKit supports both a **Graphical User Interface (GUI)** and a **Command-Line Interface (CLI)**, making it suitable for users who prefer either a visual workflow or terminal-based operations.

---

## 🚀 Features

### 📄 PDF Operations

- 🔗 **Merge PDF**
  - Combine multiple PDF documents into one file.
  - Select and arrange PDF files before merging.

- ✂️ **Split PDF**
  - Extract selected pages from a PDF.
  - Supports custom page ranges.

- 🗑️ **Remove Pages**
  - Remove unwanted pages from an existing PDF.

- 🔄 **Rotate Pages**
  - Rotate selected pages by different angles.

- ↕️ **Reorder Pages**
  - Rearrange PDF pages using a custom page order.

### 🖼️ Image Operations

- 🖼️ **Extract Images**
  - Extract embedded images from PDF documents.

- 📷 **Images to PDF**
  - Convert multiple images into a single PDF document.

### 💧 Watermark

Add customizable text watermarks to PDF documents.

Available customization options include:

- Position
- Font size
- Opacity
- Rotation

### 🗜️ PDF Compression

Reduce PDF file size through PDF stream compression.

### 🔄 PDF Conversion

Convert PDF documents into different formats:

- TXT
- HTML
- DOCX

### 👀 PDF Preview

Preview PDF pages before performing an operation.

### 🖥️ GUI & CLI

PDF ToolKit provides two interfaces:

**Graphical User Interface**

A desktop interface designed for easy PDF management.

**Command-Line Interface**

Run PDF operations directly from the terminal.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| 🐍 Python 3.11+ | Core programming language |
| 📕 pypdf | PDF manipulation |
| 🔬 PyMuPDF | PDF rendering and processing |
| 🖼️ Pillow | Image processing |
| 📄 ReportLab | PDF generation and watermarking |
| 📝 python-docx | DOCX generation |
| 🖱️ tkinterdnd2 | Drag-and-drop support |
| 🧪 pytest | Automated testing |
| 🖥️ Tkinter | Desktop GUI |

---

## 📁 Project Structure

```text
PDF-ToolKit/
│
├── pdf_toolkit/
│   ├── __init__.py
│   ├── cli.py
│   ├── file_utils.py
│   ├── gui.py
│   └── pdf_operations.py
│
├── tests/
│   └── test_pdf_operations.py
│
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

## 🧩 Architecture

The project uses a modular structure to separate the user interface, command-line interface, file utilities, and PDF processing logic.

```text
                         ┌─────────────────┐
                         │     main.py     │
                         │   Application   │
                         │     Entry       │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
             ┌──────────────┐           ┌──────────────┐
             │     GUI      │           │     CLI      │
             │    gui.py    │           │    cli.py    │
             └──────┬───────┘           └──────┬───────┘
                    │                          │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  PDF Operations     │
                    │ pdf_operations.py   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   File Utilities    │
                    │   file_utils.py     │
                    └─────────────────────┘
```

---

## 💻 Requirements

Before running PDF ToolKit, make sure you have:

- Python **3.11 or newer**
- pip
- Tkinter support

You can verify your Python installation with:

```bash
python --version
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/chaka-ranchaka/PDF-ToolKit.git
```

Navigate to the project directory:

```bash
cd PDF-ToolKit
```

### 2. Create a Virtual Environment

It is recommended to use a virtual environment.

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

#### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```cmd
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

---

## ▶️ Usage

### Run the GUI

Start PDF ToolKit with:

```bash
python main.py
```

The graphical interface will open and allow you to select the desired PDF operation.

### Run the CLI

Launch the command-line interface with:

```bash
python main.py --cli
```

---

## 🧭 Page Range Format

PDF ToolKit uses **1-based page numbering**.

### Single Page

```text
2
```

Selects page 2.

### Multiple Pages

```text
2,5,8
```

Selects pages 2, 5, and 8.

### Page Range

```text
2-5
```

Selects pages 2, 3, 4, and 5.

### Mixed Selection

```text
2,5,8-10
```

Selects pages 2, 5, 8, 9, and 10.

### All Pages

```text
all
```

Selects all pages.

---

## 🧪 Testing

PDF ToolKit uses `pytest` for automated testing.

Run the test suite with:

```bash
pytest
```

You can also use:

```bash
python -m pytest
```

---

## 🔐 Privacy

PDF ToolKit is designed as a local desktop application.

PDF processing is performed locally on the user's computer. The application does not require users to upload their PDF documents to an external web service for normal PDF operations.

This makes the tool suitable for workflows where keeping documents locally is preferred.

---

## ⚠️ Limitations

PDF ToolKit focuses on common PDF management operations rather than advanced commercial PDF editing.

Current limitations may include:

- No advanced PDF text editing.
- No OCR functionality for scanned documents.
- No advanced PDF annotation system.
- No password management interface.
- PDF-to-text conversion depends on extractable text.
- Scanned PDFs may require OCR before text can be extracted.
- Advanced document layout preservation may vary depending on the source PDF.

---

## 🗺️ Roadmap

Future improvements may include:

- [ ] 🔒 PDF password protection
- [ ] 🔓 Password-protected PDF support
- [ ] 🔍 OCR for scanned PDFs
- [ ] ✏️ PDF text editing
- [ ] 📝 PDF annotation tools
- [ ] 🖼️ Image insertion
- [ ] 📑 Batch PDF processing
- [ ] 📊 Improved progress indicators
- [ ] 🧪 Expanded automated test coverage
- [ ] 📦 Standalone executable release
- [ ] 🎨 Improved GUI design
- [ ] 🌐 Multi-language interface

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

### 1. Fork the Repository

Create your own fork of this project.

### 2. Clone Your Fork

```bash
git clone https://github.com/your-username/PDF-ToolKit.git
cd PDF-ToolKit
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature
```

### 4. Make Your Changes

Implement your feature or fix.

### 5. Run the Tests

```bash
pytest
```

### 6. Commit Your Changes

```bash
git add .
git commit -m "Add: your feature"
```

### 7. Push Your Branch

```bash
git push origin feature/your-feature
```

### 8. Open a Pull Request

Create a Pull Request from your branch to the main repository.

---

## 👨‍💻 Author

### Chaka Ranchaka

Electrical Engineering student interested in:

- 💻 Software Development
- 🤖 Artificial Intelligence & Computer Vision
- 🔌 Embedded Systems & IoT
- 📱 Flutter Development
- 🌐 Web Development
- 🧠 Exploring new technologies

GitHub: [@chaka-ranchaka](https://github.com/chaka-ranchaka)

---

## ⭐ Support

If you find **PDF ToolKit** useful, consider giving the repository a ⭐ on GitHub.

Your support helps the project grow and motivates further development.

---

<p align="center">

Built with 🐍 Python and curiosity.

</p>
