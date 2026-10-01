import os
import sys
import shutil
import subprocess
import zipfile
import uuid
import io
from PIL import Image, ImageStat, ImageOps
import pymupdf

# Support UTF-8 output across platforms
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def get_calibre_path(custom_path=None):
    """
    Dynamically locate the Calibre ebook-convert binary from:
    1. Explicit custom_path argument
    2. CALIBRE_PATH environment variable
    3. System PATH
    4. Common platform default and portable installation directories
    """
    if custom_path and os.path.exists(custom_path):
        if os.path.isdir(custom_path):
            exe = os.path.join(custom_path, 'ebook-convert.exe')
            if os.path.exists(exe):
                return exe
            exe_sub = os.path.join(custom_path, 'Calibre', 'ebook-convert.exe')
            if os.path.exists(exe_sub):
                return exe_sub
        return custom_path

    env_path = os.environ.get('CALIBRE_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    
    which_path = shutil.which('ebook-convert')
    if which_path:
        return which_path

    candidates = [
        r'C:\Program Files\Calibre2\ebook-convert.exe',
        r'C:\Program Files (x86)\Calibre2\ebook-convert.exe',
        r'C:\Calibre Portable\Calibre\ebook-convert.exe',
        r'D:\Calibre Portable\Calibre\ebook-convert.exe',
        r'E:\Calibre Portable\Calibre\ebook-convert.exe',
        r'F:\Calibre Portable\Calibre\ebook-convert.exe',
        '/Applications/calibre.app/Contents/MacOS/ebook-convert',
        '/usr/bin/ebook-convert',
        '/usr/local/bin/ebook-convert',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return 'ebook-convert'


CALIBRE_CONVERT = get_calibre_path()



def is_valid_epub(epub_path):
    """Verifies that an EPUB file exists, has content, and has a valid container.xml."""
    if not os.path.exists(epub_path) or os.path.getsize(epub_path) < 1000:
        return False
    try:
        with zipfile.ZipFile(epub_path, 'r') as zf:
            return 'META-INF/container.xml' in zf.namelist()
    except Exception:
        return False


def is_blank_image(img_or_data, mean_thresh=250.0, std_thresh=3.5):
    """Detects whether an image is a blank white or black spacer/divider page."""
    try:
        if isinstance(img_or_data, Image.Image):
            gray = img_or_data.convert('L') if img_or_data.mode != 'L' else img_or_data
        else:
            im = Image.open(io.BytesIO(img_or_data))
            gray = im.convert('L')
        stat = ImageStat.Stat(gray)
        mean = stat.mean[0]
        stddev = stat.stddev[0]
        if mean >= mean_thresh and stddev <= std_thresh:
            return True
        if mean <= 5.0 and stddev <= 2.0:
            return True
    except Exception:
        pass
    return False


def is_digital_text_pdf(pdf_path, sample_pages=10, min_chars_per_page=120, min_text_page_ratio=0.5):
    """
    Detects whether a PDF has an authentic digital text layer (meaning it should be reflowable text),
    or is a scanned book/manga (which should be 1-bit monochrome bilevel).
    """
    try:
        doc = pymupdf.open(pdf_path)
        total = len(doc)
        if total == 0:
            return False
        
        start_p = 1 if total > 1 else 0
        end_p = min(total, start_p + sample_pages)
        sampled_count = end_p - start_p
        if sampled_count <= 0:
            sampled_count = 1
            start_p = 0
            end_p = 1

        text_pages = 0
        total_chars = 0
        for p_idx in range(start_p, end_p):
            t = doc[p_idx].get_text().strip()
            total_chars += len(t)
            if len(t) >= min_chars_per_page:
                text_pages += 1
                
        doc.close()
        return (text_pages / sampled_count >= min_text_page_ratio) or (total_chars / sampled_count >= 150)
    except Exception:
        return False


def binarize_image(pil_img, bg_whiten_cutoff=208, dark_ink_cutoff=55):
    """
    Intelligent Adaptive Binarization Filter:
    1. Analyzes grayscale luminance distribution.
    2. Whitens paper background tint (anything >= bg_whiten_cutoff is clamped to 255 pure white),
       completely eliminating speckle noise / dust particles around scanned letters.
    3. Strengthens dark ink strokes (anything <= dark_ink_cutoff is pushed to solid black).
    4. Smoothly remaps mid-tone shades for illustration details.
    5. Converts to 1-Bit Bilevel PNG with crisp text and zero background noise.
    """
    gray = pil_img.convert('L')
    
    # Auto-detect negative / inverted polarity (e.g. PDF ImageMask or dark scan)
    if ImageStat.Stat(gray).mean[0] < 128:
        gray = ImageOps.invert(gray)

    # Calculate paper brightness dynamically from high percentiles
    hist = gray.histogram()
    total = gray.width * gray.height
    cum = 0
    estimated_bg = 245
    for val in range(255, -1, -1):
        cum += hist[val]
        if cum >= total * 0.12:  # Top 12% brightest pixels reflect the paper tone
            estimated_bg = val
            break
    
    # Adapt cutoff to actual paper background tone
    effective_white = min(bg_whiten_cutoff, max(185, int(estimated_bg * 0.94)))
    effective_dark = min(dark_ink_cutoff, int(effective_white * 0.28))

    lut = []
    span = max(1, effective_white - effective_dark)
    for i in range(256):
        if i >= effective_white:
            lut.append(255)  # 100% pure white paper background
        elif i <= effective_dark:
            lut.append(0)    # 100% solid black text ink
        else:
            val = int(255 * ((i - effective_dark) / span))
            lut.append(val)
            
    stretched = gray.point(lut)
    res = stretched.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
    if ImageStat.Stat(res.convert('L')).mean[0] < 128:
        res = ImageOps.invert(res.convert('L')).convert('1')
    return res


def convert_document_to_epub(src_path, auto_fix_cover=True):
    """
    Converts text and rich-document formats (PRC, MOBI, AZW, AZW3, DOCX, DOC, RTF, HTML, FB2, CHM) to EPUB.
    Validates the result and optionally fixes the cover.
    """
    epub_path = os.path.splitext(src_path)[0] + '.epub'
    cmd = [CALIBRE_CONVERT, src_path, epub_path]
    res = subprocess.run(cmd, capture_output=True, text=True, errors='replace', timeout=300)
    
    if is_valid_epub(epub_path):
        if auto_fix_cover:
            try:
                from .fix_epub_covers import fix_epub_cover
            except ImportError:
                from fix_epub_covers import fix_epub_cover
            try:
                fix_epub_cover(epub_path)
            except Exception:
                pass
        return True, epub_path
    return False, res.stderr


def convert_scanned_pdf_to_epub(
    pdf_path,
    epub_path=None,
    dpi_scale=1.5,
    mode='auto',
    jpeg_quality=82,
    skip_blank_pages=True,
    progress_callback=None
):
    """
    Converts PDF books into high-performance Fixed-Layout EPUBs or Reflowable EPUBs.
    
    Modes:
    - 'auto' (Default): Automatically inspects PDF content; routes digital text PDFs to
      'text' (Reflowable EPUB) and scanned books/manga to '1bit' (Fixed-Layout EPUB).
    - '1bit': Preserves RGB cover on page 0, converts interior pages to 1-bit Bilevel Monochrome PNG.
      Produces ultra-sharp text and diagrams at minimal file sizes (30-60 KB per page).
    - 'grayscale': Converts interior pages to 8-bit Grayscale JPEG.
    - 'color': Keeps full RGB color JPEG (Q80-85).
    - 'text': Extracts text & decodes AVn/VNI fonts -> Reflowable pure text EPUB + clean TXT.
    """
    if epub_path is None:
        epub_path = os.path.splitext(pdf_path)[0] + '.epub'

    if mode == 'auto':
        if is_digital_text_pdf(pdf_path):
            mode = 'text'
            print(f"  -> [Auto-Detect] Detected Digital Text PDF -> Converting to Reflowable EPUB")
        else:
            mode = '1bit'
            print(f"  -> [Auto-Detect] Detected Scanned Image PDF -> Converting to 1-Bit Bilevel EPUB")

    if mode == 'text':
        try:
            from .extract_text import export_pdf_to_reflowable_epub
        except ImportError:
            from extract_text import export_pdf_to_reflowable_epub
        return export_pdf_to_reflowable_epub(pdf_path, epub_path=epub_path, progress_callback=progress_callback)
    
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    title = filename
    author = 'Unknown Author'
    if ' - ' in filename:
        parts = filename.split(' - ', 1)
        title = parts[0].strip()
        author = parts[1].strip()

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    book_uuid = str(uuid.uuid4())

    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        zf.writestr('META-INF/container.xml', container_xml)

        manifest_items = []
        spine_items = []
        toc_nav_points = []
        
        mat = pymupdf.Matrix(dpi_scale, dpi_scale)
        valid_idx = 0
        skipped_blanks = 0

        for i, page in enumerate(doc):
            if progress_callback:
                try:
                    progress_callback(i + 1, total_pages)
                except Exception:
                    pass

            rect = page.rect
            page_h = max(1.0, rect.height)
            
            # Target ~2800 - 3200px height for ultra-sharp vector-like text matching LEGO benchmark
            scale = max(2.5, min(4.8, 3000.0 / page_h))
            mat = pymupdf.Matrix(scale, scale)
            
            # Check if page has single native high-res image
            imgs = page.get_images()
            raw_img = None
            if len(imgs) == 1:
                try:
                    xref = imgs[0][0]
                    obj_dict = doc.xref_object(xref)
                    # Skip raw extraction for ImageMask or inverted decode to let MuPDF render correct polarity
                    if '/ImageMask true' not in obj_dict and '/Decode' not in obj_dict and '/ImageMask' not in obj_dict:
                        base_info = doc.extract_image(xref)
                        # If embedded image is already high resolution (>= 1600px height)
                        if base_info['height'] >= 1600:
                            extracted = Image.open(io.BytesIO(base_info['image']))
                            # Polarity safety check on extracted native image
                            if ImageStat.Stat(extracted.convert('L')).mean[0] < 128:
                                raw_img = None  # Fallback to MuPDF renderer
                            else:
                                raw_img = extracted
                except Exception:
                    raw_img = None

            if raw_img is None:
                pix = page.get_pixmap(matrix=mat, alpha=False)
                raw_img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)

            # Check blank divider pages (preserve page 0 / cover)
            if i > 0 and skip_blank_pages:
                if is_blank_image(raw_img):
                    skipped_blanks += 1
                    continue

            valid_idx += 1
            w, h = raw_img.size

            # Page 0 is always preserved as high-res RGB color
            if i == 0 or mode == 'color':
                rgb_img = raw_img.convert('RGB')
                if i > 0 and ImageStat.Stat(rgb_img.convert('L')).mean[0] < 128:
                    rgb_img = ImageOps.invert(rgb_img)
                buf = io.BytesIO()
                rgb_img.save(buf, format='JPEG', quality=max(85, jpeg_quality))
                out_bytes = buf.getvalue()
                img_ext = 'jpg'
                media_type = 'image/jpeg'
            elif mode == '1bit':
                pil_img = binarize_image(raw_img)
                buf = io.BytesIO()
                pil_img.save(buf, format='PNG', optimize=False)
                out_bytes = buf.getvalue()
                img_ext = 'png'
                media_type = 'image/png'
            elif mode == 'grayscale':
                pil_img = raw_img.convert('L')
                if ImageStat.Stat(pil_img).mean[0] < 128:
                    pil_img = ImageOps.invert(pil_img)
                buf = io.BytesIO()
                pil_img.save(buf, format='JPEG', quality=jpeg_quality)
                out_bytes = buf.getvalue()
                img_ext = 'jpg'
                media_type = 'image/jpeg'
            else:
                rgb_img = raw_img.convert('RGB')
                buf = io.BytesIO()
                rgb_img.save(buf, format='JPEG', quality=jpeg_quality)
                out_bytes = buf.getvalue()
                img_ext = 'jpg'
                media_type = 'image/jpeg'

            img_filename = f'page_{valid_idx:04d}.{img_ext}'
            zf.writestr(f'OEBPS/Images/{img_filename}', out_bytes)

            page_id = f'page_{valid_idx:04d}'
            xhtml_filename = f'page_{valid_idx:04d}.xhtml'
            
            # Clean Full-Viewport SVG (Exact Match to LEGO Benchmark)
            xhtml_content = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title} - Page {valid_idx}</title>
    <meta name="viewport" content="width={w}, height={h}"/>
    <style type="text/css">
        @page {{ margin: 0; padding: 0; }}
        html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background-color: #FFFFFF; }}
        svg {{ width: 100%; height: 100%; margin: 0; padding: 0; display: block; }}
    </style>
</head>
<body>
    <svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink"
         width="100%" height="100%" viewBox="0 0 {w} {h}">
        <image width="{w}" height="{h}" xlink:href="../Images/{img_filename}"/>
    </svg>
</body>
</html>'''
            zf.writestr(f'OEBPS/Text/{xhtml_filename}', xhtml_content)

            manifest_items.append(f'        <item id="img_{page_id}" href="Images/{img_filename}" media-type="{media_type}"/>')
            manifest_items.append(f'        <item id="xhtml_{page_id}" href="Text/{xhtml_filename}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'        <itemref idref="xhtml_{page_id}"/>')

            if valid_idx == 1 or valid_idx % 25 == 0 or i == total_pages - 1:
                toc_nav_points.append(f'''        <navPoint id="navPoint-{valid_idx}" playOrder="{valid_idx}">
            <navLabel><text>Page {valid_idx}</text></navLabel>
            <content src="Text/{xhtml_filename}"/>
        </navPoint>''')

        content_opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package version="3.0" unique-identifier="BookId" xmlns="http://www.idpf.org/2007/opf" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:identifier id="BookId">urn:uuid:{book_uuid}</dc:identifier>
        <dc:title>{title}</dc:title>
        <dc:creator>{author}</dc:creator>
        <dc:language>en</dc:language>
        <meta name="cover" content="img_page_0001"/>
        <meta property="rendition:layout">pre-paginated</meta>
        <meta property="rendition:orientation">auto</meta>
        <meta property="rendition:spread">auto</meta>
    </metadata>
    <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
{chr(10).join(manifest_items)}
    </manifest>
    <spine toc="ncx">
{chr(10).join(spine_items)}
    </spine>
</package>'''
        zf.writestr('OEBPS/content.opf', content_opf)

        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="urn:uuid:{book_uuid}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="{valid_idx}"/>
        <meta name="dtb:maxPageNumber" content="{valid_idx}"/>
    </head>
    <docTitle><text>{title}</text></docTitle>
    <navMap>
{chr(10).join(toc_nav_points)}
    </navMap>
</ncx>'''
        zf.writestr('OEBPS/toc.ncx', toc_ncx)

    return True, epub_path


def convert_digital_pdf_to_epub(pdf_path, auto_fix_cover=True):
    """Converts a reflowable text PDF to standard reflowable EPUB with auto cover extraction."""
    epub_path = os.path.splitext(pdf_path)[0] + '.epub'
    cmd = [CALIBRE_CONVERT, pdf_path, epub_path]
    res = subprocess.run(cmd, capture_output=True, text=True, errors='replace', timeout=600)
    
    if is_valid_epub(epub_path):
        if auto_fix_cover:
            try:
                from .fix_epub_covers import fix_epub_cover
            except ImportError:
                from fix_epub_covers import fix_epub_cover
            try:
                fix_epub_cover(epub_path, pdf_path)
            except Exception:
                pass
        return True, epub_path
    return False, res.stderr


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python convert_books.py <file-or-directory> [--mode auto|1bit|grayscale|color|text]")
        sys.exit(1)

    target = sys.argv[1]
    mode = 'auto'
    if '--mode' in sys.argv:
        m_idx = sys.argv.index('--mode') + 1
        if m_idx < len(sys.argv):
            mode = sys.argv[m_idx]

    files_to_process = []
    if os.path.isfile(target):
        files_to_process.append(target)
    elif os.path.isdir(target):
        for root, _, filenames in os.walk(target):
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in ['.prc', '.mobi', '.azw', '.azw3', '.docx', '.doc', '.fb2', '.pdf']:
                    files_to_process.append(os.path.join(root, fn))

    print(f"Found {len(files_to_process)} file(s) to process.")
    for f in files_to_process:
        ext = os.path.splitext(f)[1].lower()
        print(f"Processing: {f}...")
        try:
            if ext == '.pdf':
                ok, res = convert_scanned_pdf_to_epub(f, mode=mode)
            else:
                ok, res = convert_document_to_epub(f)
            print(f"  -> Result: {'OK' if ok else 'FAILED'} ({res})")
        except Exception as e:
            print(f"  -> Error: {e}")
