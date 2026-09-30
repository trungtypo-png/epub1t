# epub1t 📚⚡

> Automated high-performance ebook conversion & optimization pipeline. Converts documents & scanned PDFs to lightweight, razor-sharp EPUBs with 1-bit monochrome bilevel compression, ghost page pruning, and smart cover extraction.

**English** | [Tiếng Việt](README.vi.md)

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.1.0-green.svg)](https://github.com/trungtypo-png/epub1t/releases)

---

## 🌟 Key Features

- ⚡ **1-Bit Monochrome Bilevel Compression:** Transforms heavy 24-bit RGB scanned text PDFs (>100MB) into lightweight Fixed-Layout EPUBs (20-35MB) with razor-sharp vector-like clarity at high resolutions (2000px - 3400px).
- 🎨 **Official Illustrated Cover Restoration:** Automatically extracts the real first-page cover from PDF/source files and replaces Calibre's generic 2-tone placeholder cover.
- 🧹 **Artifact & Ghost Page Cleaner:** Detects blank spacer pages using histogram standard deviation analysis (`mean >= 250`, `stddev <= 3.5`) and strips away fragmented Calibre `pdftohtml` multi-layer images (`_2.jpg`, `_3.png`, sub-3KB noise).
- 🔡 **AVn / VNI-Times Legacy Font Decoding:** Fixes severely broken Vietnamese diacritics (`vaâo → vào`, `khoaû → khỏa`) in pre-2005 PDF books using composite PostScript diacritic token analysis — outputs clean Unicode UTF-8 EPUBs under 1MB.
- 📱 **Responsive SVG Viewport:** Implements `<svg viewBox="0 0 w h">` wrappers so fixed-layout pages perfectly adapt to any e-reader/tablet resolution without letterboxing.
- 🛡️ **Safe Source Deletion:** Validates EPUB structural integrity (`META-INF/container.xml` verification) before removing source files.

---

## 📊 Real-World Benchmark Results

> Files > 10MB converted from scanned PDF to 1-Bit Monochrome EPUB:

![Real-World Optimization Benchmark](./benchmark_results_en.png)

Average size reduction: **~80%** across 12 real scanned book collections — without any visible loss in text sharpness.

---

## 📦 Prerequisites & Installation

### 1. Download Standalone App (No Python required)
Get the pre-built binaries from the **[Releases](https://github.com/trungtypo-png/epub1t/releases)** page:
* **Windows:** Download `Epub1t-v1.1.0-Windows.zip` (extract and run `Epub1t.exe`).
* **macOS:** Download `Epub1t-v1.1.0-macOS.zip` (extract and open the app bundle).

### 2. Or Run from Source (Python 3.9+)
```bash
git clone https://github.com/trungtypo-png/epub1t.git
cd epub1t
pip install -r requirements.txt
python gui.py
```

### 3. Optional Engine: Calibre CLI
* Only needed when converting legacy reflowable books (`.prc`, `.mobi`, `.azw3`, `.docx`).
* Download from [Calibre Official Site](https://calibre-ebook.com/download) or use Calibre Portable.

---

## 🚀 Usage

### 1. Graphical Interface (GUI)
Run `python gui.py` or double-click the pre-built executable.

### 2. Command Line Interface (CLI)
```bash
# Convert a folder of books/PDFs (Default 1-bit mode for scans)
python scripts/convert_books.py "/path/to/books" --mode 1bit

# Convert and safely remove source files upon success
python scripts/convert_books.py "/path/to/books" --delete-source

# Clean multi-layer artifacts & ghost blank pages
python scripts/clean_large_epubs.py "/path/to/books"

# Fix & restore real book covers
python scripts/fix_epub_covers.py "/path/to/books"
```

---

## 🤝 Acknowledgements & Credits

Special thanks to the creators and maintainers of the open-source projects that inspire and power this pipeline:

* **[Calibre](https://github.com/kovidgoyal/calibre)** by *Kovid Goyal* and contributors — The gold standard for digital ebook conversion and management.
* **[Kindle Comic Converter (KCC)](https://github.com/ciromattia/kcc)** by *Ciro Mattia*, *Darío Marcelino* and contributors — Pioneer in comic/manga e-reader optimization.
* **[PyMuPDF (FitZ)](https://github.com/pymupdf/PyMuPDF)** by *Artifex Software* & the *PyMuPDF Team* — High-performance PDF rendering and extraction.
* **[Pillow (PIL)](https://github.com/python-pillow/Pillow)** by *Jeffrey A. Clark* and contributors — Python imaging library.

---

## 🤖 Antigravity / Agent Skill

This repository includes a [`SKILL.md`](./SKILL.md) file ready to be loaded into **Google Antigravity** or other AI agent frameworks to automate library conversion workflows.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
