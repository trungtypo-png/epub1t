# ebook-convert-1bitmono 📚⚡

> Automated high-performance ebook conversion & optimization pipeline. Converts documents & scanned PDFs to lightweight, razor-sharp EPUBs with 1-bit monochrome bilevel compression, ghost page pruning, and smart cover extraction.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Key Features

- ⚡ **1-Bit Monochrome Bilevel Compression:** Transforms heavy 24-bit RGB scanned text PDFs (>100MB) into lightweight Fixed-Layout EPUBs (20-35MB) with razor-sharp vector-like clarity.
- 🎨 **Official Illustrated Cover Restoration:** Automatically extracts the real first-page cover from PDF/source files and replaces Calibre's generic 2-tone placeholder cover.
- 🧹 **Artifact & Ghost Page Cleaner:** Detects blank spacer pages using histogram standard deviation analysis (`mean >= 250`, `stddev <= 3.5`) and strips away fragmented Calibre `pdftohtml` multi-layer images (`_2.jpg`, `_3.png`, sub-3KB noise).
- 📱 **Responsive SVG Viewport:** Implements `<svg viewBox="0 0 w h">` wrappers so fixed-layout pages perfectly adapt to any e-reader/tablet resolution without letterboxing.
- 🛡️ **Safe Source Deletion:** Validates EPUB structural integrity (`META-INF/container.xml` verification) before removing source files.

---

## 📦 Prerequisites & Installation

### 1. Calibre CLI
- Download from the [Official Calibre Site](https://calibre-ebook.com/download) or use Calibre Portable.
- Ensure `ebook-convert` is in your `PATH`, or specify its path via the `CALIBRE_PATH` environment variable.

### 2. Python Dependencies
```bash
git clone https://github.com/your-username/ebook-convert-1bitmono.git
cd ebook-convert-1bitmono
pip install -r requirements.txt
```

---

## 🚀 Usage

### 1. Convert Ebooks & Scanned PDFs
```bash
# Convert a folder of books/PDFs (Default 1-bit mode for scans)
python scripts/convert_books.py "/path/to/books" --mode 1bit

# Convert and safely remove source files upon success
python scripts/convert_books.py "/path/to/books" --delete-source
```

### 2. Clean Multi-layer Artifacts & Blank Pages
```bash
python scripts/clean_large_epubs.py "/path/to/books"
```

### 3. Fix & Restore Real Book Covers
```bash
python scripts/fix_epub_covers.py "/path/to/books"
```

### 4. Python API
```python
from scripts.convert_books import convert_document_to_epub, convert_scanned_pdf_to_epub

# Convert PRC / MOBI / AZW3 / DOCX
success, output_path = convert_document_to_epub("book.mobi", delete_source=False)

# Convert scanned PDF to 1-bit monochrome EPUB
success, output_path = convert_scanned_pdf_to_epub("scan.pdf", mode="1bit", dpi_scale=1.5)
```

---

## 🤖 Antigravity / Agent Skill

This repository includes a [`SKILL.md`](./SKILL.md) file ready to be loaded into **Google Antigravity** or other AI agent frameworks to automate library conversion workflows.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
