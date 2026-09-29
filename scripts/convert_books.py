import os
import sys
import shutil
import subprocess
import zipfile
import uuid
import io
from PIL import Image, ImageStat
import pymupdf

# Support UTF-8 output across platforms
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def get_calibre_path():
    """
    Dynamically locate the Calibre ebook-convert binary from:
    1. CALIBRE_PATH environment variable
    2. System PATH
    3. Common platform default installation directories
    """
    env_path = os.environ.get('CALIBRE_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    
    which_path = shutil.which('ebook-convert')
    if which_path:
        return which_path

    candidates = [
        r'C:\Program Files\Calibre2\ebook-convert.exe',
        r'C:\Program Files (x86)\Calibre2\ebook-convert.exe',
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


def is_blank_image(img_data, mean_thresh=250.0, std_thresh=3.5):
    """Detects whether an image is a blank white or black spacer/divider page."""
    try:
        im = Image.open(io.BytesIO(img_data))
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


def convert_document_to_epub(src_path, delete_source=False, auto_fix_cover=True):
    """
    Converts text and rich-document formats (PRC, MOBI, AZW, AZW3, DOCX, DOC, RTF, HTML, FB2, CHM) to EPUB.
    Validates the result and optionally cleans/fixes the cover and removes the source file.
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
        if delete_source:
            os.remove(src_path)
        return True, epub_path
    return False, res.stderr


def convert_scanned_pdf_to_epub(
    pdf_path,
    epub_path=None,
    dpi_scale=1.5,
    mode='1bit',
    jpeg_quality=82,
    skip_blank_pages=True
):
    """
    Converts scanned PDF books into high-performance Fixed-Layout EPUBs.
    
    Modes:
    - '1bit' (Default): Preserves RGB cover on page 0, converts interior pages to 1-bit Bilevel Monochrome PNG.
      Produces ultra-sharp text and diagrams at minimal file sizes (30-60 KB per page).
    - 'grayscale': Converts interior pages to 8-bit Grayscale JPEG.
    - 'color': Keeps full RGB color JPEG (Q80-85).
    """
    if epub_path is None:
        epub_path = os.path.splitext(pdf_path)[0] + '.epub'
    
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
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_data = pix.tobytes(output='png')

            # Skip blank divider pages (preserve page 0 / cover)
            if i > 0 and skip_blank_pages and is_blank_image(img_data):
                skipped_blanks += 1
                continue

            valid_idx += 1
            w, h = pix.width, pix.height

            # Page 0 is always preserved as high-res RGB color
            if i == 0 or mode == 'color':
                out_bytes = pix.tobytes(output='jpg', jpg_quality=max(85, jpeg_quality))
                img_ext = 'jpg'
                media_type = 'image/jpeg'
            elif mode == '1bit':
                pil_img = Image.open(io.BytesIO(img_data)).convert('1', dither=Image.Dither.FLOYDSTEINBERG)
                buf = io.BytesIO()
                pil_img.save(buf, format='PNG', optimize=True)
                out_bytes = buf.getvalue()
                img_ext = 'png'
                media_type = 'image/png'
            elif mode == 'grayscale':
                pil_img = Image.open(io.BytesIO(img_data)).convert('L')
                buf = io.BytesIO()
                pil_img.save(buf, format='JPEG', quality=jpeg_quality)
                out_bytes = buf.getvalue()
                img_ext = 'jpg'
                media_type = 'image/jpeg'
            else:
                out_bytes = pix.tobytes(output='jpg', jpg_quality=jpeg_quality)
                img_ext = 'jpg'
                media_type = 'image/jpeg'

            img_filename = f'page_{valid_idx:04d}.{img_ext}'
            zf.writestr(f'OEBPS/Images/{img_filename}', out_bytes)

            page_id = f'page_{valid_idx:04d}'
            xhtml_filename = f'page_{valid_idx:04d}.xhtml'
            
            # Responsive SVG Viewport markup
            xhtml_content = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title} - Page {valid_idx}</title>
    <meta name="viewport" content="width={w}, height={h}"/>
    <style type="text/css">
        @page {{ margin: 0; padding: 0; }}
        body {{ margin: 0; padding: 0; background-color: #FFFFFF; text-align: center; }}
        div.img-wrapper {{ width: 100vw; height: 100vh; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; }}
        svg {{ width: 100%; height: 100%; }}
    </style>
</head>
<body>
    <div class="img-wrapper">
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink"
             width="100%" height="100%" viewBox="0 0 {w} {h}">
            <image width="{w}" height="{h}" xlink:href="../Images/{img_filename}"/>
        </svg>
    </div>
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
        print("Usage: python convert_books.py <file-or-directory> [--mode 1bit|grayscale|color] [--delete-source]")
        sys.exit(1)

    target = sys.argv[1]
    mode = '1bit'
    del_src = '--delete-source' in sys.argv
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
                # Attempt 1-bit scan optimization by default for PDF scans
                ok, res = convert_scanned_pdf_to_epub(f, mode=mode)
            else:
                ok, res = convert_document_to_epub(f, delete_source=del_src)
            print(f"  -> Result: {'OK' if ok else 'FAILED'} ({res})")
        except Exception as e:
            print(f"  -> Error: {e}")
