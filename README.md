# epub1t 📚⚡

> Automated PDF to EPUB converter and high-performance ebook optimization pipeline. Converts digital documents (PRC, MOBI, AZW, AZW3, DOCX) and scanned PDFs to lightweight, razor-sharp EPUBs with 1-bit monochrome bilevel compression, PyMuPDF OCR, Vietnamese AVn font decoding, ghost page pruning, and smart cover extraction.

**English** | [Tiếng Việt](README.vi.md)

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.3.1-green.svg)](https://github.com/trungtypo-png/epub1t/releases)

---

## 🌟 Key Features

- ⚡ **1-Bit Monochrome Bilevel Compression:** Transforms heavy 24-bit RGB scanned text PDFs (>100MB) into lightweight Fixed-Layout EPUBs (20-35MB) with razor-sharp vector-like clarity at high resolutions (2000px - 3400px).
- 🚀 **High-Speed Direct Buffer Pipeline:** Zero-copy pixel buffer streaming and instant PNG encoding — converts a 300-page book in **under 25 seconds** (4.5x faster).
- 🛡️ **Auto-Polarity Guard:** Automatically detects negative/inverted scans or PDF `ImageMask` with inverse decode arrays (`/Decode [1 0]`, mean luminance < 128), ensuring interior pages render with pure white paper backgrounds (`255`) and solid black text/drawings (`0`).
- 🧹 **Intelligent Adaptive Binarization & Anti-Noise:** Auto-whitening scan paper background tone while preserving illustration sketches, completely eliminating grainy dust and speckle noise.
- 🎨 **Official Illustrated Cover Restoration:** Automatically extracts the real first-page cover from PDF/source files and replaces Calibre's generic 2-tone placeholder cover.
- 🧹 **Artifact & Ghost Page Cleaner:** Detects blank spacer pages using histogram standard deviation analysis (`mean >= 250`, `stddev <= 3.5`) and strips away fragmented Calibre `pdftohtml` multi-layer images (`_2.jpg`, `_3.png`, sub-3KB noise).
- 🔡 **AVn / VNI-Times Legacy Font Decoding:** Fixes severely broken Vietnamese diacritics (`vaâo → vào`, `khoaû → khỏa`) in pre-2005 PDF books using composite PostScript diacritic token analysis — outputs clean Unicode UTF-8 EPUBs under 1MB.
- 📱 **Responsive SVG Viewport:** Implements `<svg viewBox="0 0 w h">` wrappers so fixed-layout pages perfectly adapt to any e-reader/tablet resolution without letterboxing.
- 🛡️ **Safe Source Deletion:** Validates EPUB structural integrity (`META-INF/container.xml` verification) before removing source files.

---

## 📊 Real-World Benchmark Results

### 1. 1-Bit Monochrome Bilevel Compression (PDF Scan)
> Files > 10MB converted from scanned PDF to 1-Bit Monochrome EPUB:

![Real-World Optimization Benchmark](./benchmark_results_en.png)

Average size reduction: **~80%** across 12 real scanned book collections — without any visible loss in text sharpness.

### 2. AVn / VNI-Times Legacy Font Decoding (Pre-2005 Vietnamese PDFs)
> Resolving severely corrupted diacritics (`vaâo → vào`, `khoaû → khỏa`, `thûuâng → thường`):

![AVn Legacy Font Decoding Comparison](./avn_font_benchmark.png)

* **Before (Right):** Severely broken PostScript composite characters from legacy 1-byte/2-byte AVn fonts.
* **After (Left):** Perfectly decoded standard Unicode UTF-8 EPUB with vector-sharp clarity and reflowable text under 1MB.

---

## 📝 Changelog

### v1.1.3
* 🎯 **Native High-Res Auto-Detection:** Automatically extracts embedded original scan images (`2332 x 3444` matching LEGO benchmark) without lossy downscaling.
* 📱 **Full-Viewport Edge-to-Edge SVG:** Cleaned up SVG wrapper markup removing intermediate container margins for true 100% full-screen fit across e-readers.
* 🧹 **Paper Whitening & Anti-Noise Filter:** Adaptive background tone elimination to remove speckle dust around letters.

### v1.2.0
* 🚀 **4.5x Speed Boost:** Zero-copy direct memory buffer streaming from MuPDF into Pillow via `Image.frombytes()` and instant PNG encoding (converts a 300-page book in ~23 seconds).
* 📊 **Real-Time Per-Page Progress UI:** Interactive progress bar and percentage label (`Page X/Total (Y%)`) on GUI.

### v1.3.0 (Beta)
* 📖 **Text Extraction & Reflowable EPUB Export:** Automatically extract full book content into clean UTF-8 `.txt` and pack into standard reflowable EPUB ebooks with original cover art.
* ⚡ **Blazing Fast AVn/VNI Decoding (Regex Single-Pass):** Auto-detects and decodes legacy Vietnamese composite font diacritics in **<0.5s** for 288 pages.
* 👁️ **Built-in PyMuPDF OCR Fallback:** Automatically falls back to optical character recognition for scan pages without a selectable digital text layer.
* 🎛️ **4th GUI Mode:** Added `Reflowable EPUB (Beta)` mode directly in the interface.

### v1.3.1
* 🛡️ **Auto-Polarity Guard:** Automatically detects negative/inverted polarity scans and PDF `ImageMask` with inverted decode arrays (`/Decode [1 0]`, mean luminance < 128), ensuring pure white paper backgrounds (`255`) and solid black text/drawings (`0`).
* 📄 **Zero Dust & Speckle Noise:** Eliminates inverted black-background bugs entirely across massive multi-hundred page books while eliminating grayish background noise.
* 📱 **Full-Bleed SVG Viewport:** Edge-to-edge adaptive viewport scaling without distortion or letterboxing across all e-reader apps.
* 📊 **Record Compression Ratio:** Compresses full 765 high-resolution pages (`2122 x 3000px`) down to just **25.51 MB** (~33 KB/page).

---

## 📦 Prerequisites & Installation

### 1. Download Standalone App (No Python required)
Get the pre-built binaries from the **[Releases](https://github.com/trungtypo-png/epub1t/releases)** page:
* **Windows:** Download `Epub1t-v1.3.1-Windows.zip` (extract and run `Epub1t.exe`).
* **macOS:** Download `Epub1t-v1.3.1-macOS.zip` (extract and open the app bundle).

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

# Convert PDF to reflowable EPUB and extract clean .txt
python scripts/convert_books.py "/path/to/book.pdf" --mode text

# Convert and safely remove source files upon success
python scripts/convert_books.py "/path/to/books" --delete-source

# Clean multi-layer artifacts & ghost blank pages
python scripts/clean_large_epubs.py "/path/to/books"

# Fix & restore real book covers
python scripts/fix_epub_covers.py "/path/to/books"
```

---

## 💡 Common Use Cases & Problem Solving

Whether you are organizing a digital library or preparing books for e-readers, **epub1t** is engineered to solve these core challenges:

* 📚 **Convert Scanned PDF to EPUB for E-Readers (Kindle, Kobo, Boox, iPad):**
  Raw scanned PDFs (>100MB) cause severe lagging, slow page turns, and memory crashes on e-readers. Epub1t converts scanned PDFs into lightweight Fixed-Layout EPUBs using 1-bit Monochrome Bilevel compression, slashing file sizes by ~80% down to 20–35MB while delivering razor-sharp text clarity at 3000px height.

* 📖 **PDF OCR & Text Extraction to Reflowable EPUB:**
  Easily transform image-only PDF scans and digital documents into reflowable text EPUBs and clean `.txt` files. Integrated with PyMuPDF OCR to enable resizable fonts, dark mode themes, text searching, and instant dictionary lookups.

* 🔡 **Fix Broken Vietnamese Diacritics (AVn, VNI, TCVN3 Font Decoder):**
  Directly converts and recovers garbled text from pre-2005 Vietnamese PDF books (`vaâo → vào`, `thûuâng → thường`) into clean Unicode UTF-8 text in less than 0.5 seconds.

* 🔄 **Batch Ebook Format Conversion (PRC, MOBI, AZW, AZW3, DOCX to EPUB):**
  Streamlines your entire digital book catalog into modern EPUB 3 files with structural validation (`META-INF/container.xml`) and optional safe deletion of obsolete source files.

* 🎨 **Restore Real Illustrated Book Covers & Purge Blank Pages:**
  Eliminates Calibre's generic two-tone placeholder covers by extracting authentic high-resolution covers from page 0, while stripping out ghost blank pages and fragmented image layers.

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
