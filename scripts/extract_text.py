import os
import sys
import re
import uuid
import zipfile
import io
from PIL import Image
import pymupdf

# Support UTF-8 output across platforms
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# High-precision AVn / ABC / VNI single-pass replacement rules
_AVN_RULES = [
    # 3-char composite vowels
    ('ûúâ', 'ườ'), ('ûúá', 'ướ'), ('ûúä', 'ưỡ'), ('ûúå', 'ượ'), ('ûúã', 'ưở'), ('ûú', 'ươ'),
    ('Ûúâ', 'Ườ'), ('Ûúá', 'Ướ'), ('Ûúä', 'Ưỡ'), ('Ûúå', 'Ượ'), ('Ûúã', 'Ưưở'), ('Ûú', 'Ươ'),
    ('uöë', 'uố'), ('uöì', 'uồ'), ('uöí', 'uổ'), ('uöä', 'uỗ'), ('uöå', 'uộ'), ('uö', 'uô'),
    ('Uöë', 'Uố'), ('Uöì', 'Uồ'), ('Uöí', 'Uổ'), ('Uöä', 'Uỗ'), ('Uöå', 'Uộ'), ('Uö', 'Uô'),
    ('iïë', 'iế'), ('iïì', 'iề'), ('iïí', 'iể'), ('iïä', 'iễ'), ('iïå', 'iệ'), ('iï', 'iê'),
    ('Iïë', 'Iế'), ('Iïì', 'Iề'), ('Iïí', 'Iể'), ('Iïä', 'Iễ'), ('Iïå', 'Iệ'), ('Iï', 'Iê'),
    ('yïë', 'yế'), ('yïì', 'yề'), ('yïí', 'yể'), ('yïä', 'yễ'), ('yïå', 'yệ'), ('yï', 'yê'),
    ('Yïë', 'Yế'), ('Yïì', 'Yề'), ('Yïí', 'Yể'), ('Yïä', 'Yễ'), ('Yïå', 'Yệ'), ('Yï', 'Yê'),

    # 2-char ă (ù)
    ('ùæ', 'ắ'), ('ùç', 'ằ'), ('ùã', 'ẳ'), ('ùä', 'ẵ'), ('ùå', 'ặ'),
    ('Ùæ', 'Ắ'), ('Ùç', 'Ằ'), ('Ùã', 'Ẳ'), ('Ùä', 'Ẵ'), ('Ùå', 'Ặ'),

    # 2-char â (ê)
    ('êë', 'ấ'), ('êì', 'ầ'), ('êí', 'ẩ'), ('êä', 'ẫ'), ('êå', 'ậ'),
    ('Êë', 'Ấ'), ('Êì', 'Ầ'), ('Êí', 'Ẩ'), ('Êä', 'Ẫ'), ('Êå', 'Ậ'),

    # 2-char ê (ï)
    ('ïë', 'ế'), ('ïì', 'ề'), ('ïí', 'ể'), ('ïä', 'ễ'), ('ïå', 'ệ'),
    ('Ïë', 'Ế'), ('Ïì', 'Ề'), ('Ïí', 'Ể'), ('Ïä', 'Ễ'), ('Ïå', 'Ệ'),

    # 2-char ô (ö)
    ('öë', 'ố'), ('öì', 'ồ'), ('öí', 'ổ'), ('öä', 'ỗ'), ('öå', 'ộ'),
    ('Öë', 'Ố'), ('Öì', 'Ồ'), ('Öí', 'Ổ'), ('Öä', 'Ỗ'), ('Öå', 'Ộ'),

    # 2-char ơ (ú)
    ('úá', 'ớ'), ('úâ', 'ờ'), ('úã', 'ở'), ('úä', 'ỡ'), ('úå', 'ợ'),
    ('Úá', 'Ớ'), ('Úâ', 'Ờ'), ('Úã', 'Ở'), ('Úä', 'Ỡ'), ('Úå', 'Ợ'),

    # 2-char ư (û)
    ('ûá', 'ứ'), ('ûâ', 'ừ'), ('ûã', 'ử'), ('ûä', 'ữ'), ('ûå', 'ự'),
    ('Ûá', 'Ứ'), ('Ûâ', 'Ừ'), ('Ûã', 'Ử'), ('Ûä', 'Ữ'), ('Ûå', 'Ự'),

    # 2-char simple vowels + diacritics
    ('aá', 'á'), ('aâ', 'à'), ('aã', 'ả'), ('aä', 'ã'), ('aå', 'ạ'),
    ('Aá', 'Á'), ('Aâ', 'À'), ('Aã', 'Ả'), ('Aä', 'Ã'), ('Aå', 'Ạ'),
    ('eá', 'é'), ('eâ', 'è'), ('eã', 'ẻ'), ('eä', 'ẽ'), ('eå', 'ẹ'),
    ('Eá', 'É'), ('Eâ', 'È'), ('Eã', 'Ẻ'), ('Eä', 'Ẽ'), ('Eå', 'Ẹ'),
    ('oá', 'ó'), ('oâ', 'ò'), ('oã', 'ỏ'), ('oä', 'õ'), ('oå', 'ọ'),
    ('Oá', 'Ó'), ('Oâ', 'Ò'), ('Oã', 'Ỏ'), ('Oä', 'Õ'), ('Oå', 'Ọ'),
    ('uá', 'ú'), ('uâ', 'ù'), ('uã', 'ủ'), ('uä', 'ũ'), ('uå', 'ụ'),
    ('Uá', 'Ú'), ('Uâ', 'Ù'), ('Uã', 'Ủ'), ('Uä', 'Ũ'), ('Uå', 'Ụ'),
    ('yá', 'ý'), ('yâ', 'ỳ'), ('yã', 'ỷ'), ('yä', 'ỹ'), ('yå', 'ỵ'),
    ('Yá', 'Ý'), ('Yâ', 'Ỳ'), ('Yã', 'Ỷ'), ('Yä', 'Ỹ'), ('Yå', 'Ỵ'),

    # Contextual 'i hỏi'
    ('chó', 'chỉ'), ('Chó', 'Chỉ'), ('kó', 'kỉ'), ('Kó', 'Kỉ'),
    ('tó', 'tỉ'), ('Tó', 'Tỉ'), ('nhó', 'nhỉ'), ('Nhó', 'Nhỉ'),
    ('bó', 'bỉ'), ('Bó', 'Bỉ'), ('mó', 'mỉ'), ('Mó', 'Mỉ'),
    ('đó', 'đỉ'), ('Đó', 'Đỉ'), ('hó', 'hỉ'), ('Hó', 'Hỉ'),
    ('só', 'sỉ'), ('Só', 'Sỉ'), ('dó', 'dỉ'), ('Dó', 'Dỉ'),

    # Single-character replacements
    ('ù', 'ă'), ('Ù', 'Ă'),
    ('ê', 'â'), ('Ê', 'Â'),
    ('ï', 'ê'), ('Ï', 'Ê'),
    ('ö', 'ô'), ('Ö', 'Ô'),
    ('ú', 'ơ'), ('Ú', 'Ơ'),
    ('û', 'ư'), ('Û', 'Ư'),
    ('ñ', 'í'), ('Ñ', 'Í'),
    ('ò', 'ì'), ('Ò', 'Ì'),
    ('õ', 'ị'), ('Õ', 'Ị'),
    ('à', 'đ'), ('À', 'Đ'),
]

_AVN_DICT = dict(_AVN_RULES)
_AVN_REGEX = re.compile('|'.join(re.escape(k) for k in sorted(_AVN_DICT.keys(), key=len, reverse=True)))

_AVN_MARKERS = [
    'àaä', 'nhûäng', 'àûúåc', 'khöng', 'ngûúâi', 'thïë', 'rêët', 'bùæt',
    'viïåc', 'àiïìu', 'cöng', 'vúái', 'cuãa', 'phaãi', 'rùçng', 'àïën',
    'thaânh', 'thúâi', 'chuáng', 'phêìn', 'àêìu', 'maáy', 'caác'
]


def decode_avn(text):
    """Decodes AVn / legacy Vietnamese font tokens into clean Unicode UTF-8."""
    return _AVN_REGEX.sub(lambda m: _AVN_DICT[m.group(0)], text)


def is_avn_encoded(text):
    """Detects whether a given text chunk exhibits hallmark signatures of AVn encoding."""
    matches = sum(1 for m in _AVN_MARKERS if m in text)
    return matches >= 2


def get_tessdata_path(custom_path=None):
    """Locates the tessdata directory for PyMuPDF OCR."""
    if custom_path and os.path.isdir(custom_path):
        return custom_path
    
    env_p = os.environ.get('TESSDATA_PREFIX')
    if env_p and os.path.isdir(env_p):
        return env_p
        
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tessdata'),
        r'D:\github\tessdata',
        r'C:\Program Files\Tesseract-OCR\tessdata',
        r'C:\tessdata',
        r'/usr/share/tesseract-ocr/4.00/tessdata',
        r'/usr/share/tessdata',
    ]
    for c in candidates:
        if os.path.isdir(c) and os.path.exists(os.path.join(c, 'vie.traineddata')):
            return c
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


def extract_pdf_pages_text(pdf_path, ocr_lang='vie', tessdata_path=None, progress_callback=None):
    """
    Extracts high-accuracy text from each PDF page:
    1. Direct selectable text layer (if >= 30 chars).
    2. Intelligent AVn font decoding if legacy diacritics are detected.
    3. Automatic fallback to PyMuPDF built-in OCR if page is a scan / image only.
    """
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    tess_dir = get_tessdata_path(tessdata_path)
    pages_text = []

    for idx, page in enumerate(doc):
        if progress_callback:
            try:
                progress_callback(idx + 1, total_pages)
            except Exception:
                pass

        raw_text = page.get_text()
        clean_text = ""

        if len(raw_text.strip()) >= 30:
            if is_avn_encoded(raw_text):
                clean_text = decode_avn(raw_text)
            else:
                clean_text = raw_text
        else:
            # Fallback to OCR if page has minimal or zero text layer
            if tess_dir:
                try:
                    tp = page.get_textpage_ocr(language=ocr_lang, tessdata=tess_dir, dpi=150)
                    ocr_text = tp.extractText()
                    if is_avn_encoded(ocr_text):
                        clean_text = decode_avn(ocr_text)
                    else:
                        clean_text = ocr_text
                except Exception:
                    clean_text = raw_text
            else:
                clean_text = raw_text

        pages_text.append(clean_text)

    return pages_text


def export_pdf_to_txt(pdf_path, txt_path=None, ocr_lang='vie', tessdata_path=None, progress_callback=None):
    """Extracts text and saves to a clean, well-formatted UTF-8 text file."""
    if txt_path is None:
        txt_path = os.path.splitext(pdf_path)[0] + '.txt'

    pages = extract_pdf_pages_text(pdf_path, ocr_lang=ocr_lang, tessdata_path=tessdata_path, progress_callback=progress_callback)
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        for idx, page_content in enumerate(pages, 1):
            trimmed = page_content.strip()
            if trimmed:
                f.write(trimmed)
                f.write('\n\n')

    return True, txt_path


def export_pdf_to_reflowable_epub(pdf_path, epub_path=None, ocr_lang='vie', tessdata_path=None, progress_callback=None):
    """
    Converts PDF text into a standard reflowable EPUB book (pure selectable text).
    Preserves original cover image if available.
    """
    if epub_path is None:
        epub_path = os.path.splitext(pdf_path)[0] + '_text.epub'

    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    title = filename
    author = 'Unknown Author'
    if ' - ' in filename:
        parts = filename.split(' - ', 1)
        title = parts[0].strip()
        author = parts[1].strip()

    doc = pymupdf.open(pdf_path)
    book_uuid = str(uuid.uuid4())

    # Check cover on page 0
    cover_bytes = None
    if len(doc) > 0:
        p0 = doc[0]
        imgs = p0.get_images()
        if len(imgs) >= 1:
            try:
                base_info = doc.extract_image(imgs[0][0])
                cover_bytes = base_info['image']
            except Exception:
                pass
        if cover_bytes is None:
            pix = p0.get_pixmap(dpi=150)
            cover_bytes = pix.tobytes(output='jpg')

    pages = extract_pdf_pages_text(pdf_path, ocr_lang=ocr_lang, tessdata_path=tessdata_path, progress_callback=progress_callback)

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

        if cover_bytes:
            zf.writestr('OEBPS/Images/cover.jpg', cover_bytes)
            manifest_items.append('        <item id="cover_img" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>')
            
            cover_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Cover</title>
    <style>body {{ margin: 0; padding: 0; text-align: center; }} img {{ max-width: 100%; height: auto; }}</style>
</head>
<body>
    <img src="../Images/cover.jpg" alt="Cover"/>
</body>
</html>'''
            zf.writestr('OEBPS/Text/cover.xhtml', cover_xhtml)
            manifest_items.append('        <item id="cover_page" href="Text/cover.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append('        <itemref idref="cover_page"/>')

        # Combine text into clean chapters (e.g. chunks of pages or by detected chapter headers)
        chunk_size = 10
        total_p = len(pages)
        chap_idx = 0

        for i in range(0, total_p, chunk_size):
            chap_idx += 1
            chunk_pages = pages[i:i + chunk_size]
            body_html = []
            
            for p_num, p_txt in enumerate(chunk_pages, start=i + 1):
                lines = [l.strip() for l in p_txt.splitlines() if l.strip()]
                if not lines:
                    continue
                body_html.append(f'<div class="page-block" id="page_{p_num}">')
                for line in lines:
                    safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    body_html.append(f'<p>{safe_line}</p>')
                body_html.append('</div>')

            if not body_html:
                continue

            chap_filename = f'chapter_{chap_idx:03d}.xhtml'
            chap_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{title} - Section {chap_idx}</title>
    <style>
        body {{ font-family: "Georgia", "Times New Roman", serif; font-size: 1.05em; line-height: 1.6; margin: 5%; color: #111; }}
        p {{ margin: 0 0 0.8em 0; text-indent: 1.2em; text-align: justify; }}
        .page-block {{ margin-bottom: 2em; }}
    </style>
</head>
<body>
    {chr(10).join(body_html)}
</body>
</html>'''
            zf.writestr(f'OEBPS/Text/{chap_filename}', chap_xhtml)
            item_id = f'chap_{chap_idx:03d}'
            manifest_items.append(f'        <item id="{item_id}" href="Text/{chap_filename}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'        <itemref idref="{item_id}"/>')

            toc_nav_points.append(f'''        <navPoint id="navPoint-{chap_idx}" playOrder="{chap_idx}">
            <navLabel><text>Phần {chap_idx} (Trang {i+1}-{min(i+chunk_size, total_p)})</text></navLabel>
            <content src="Text/{chap_filename}"/>
        </navPoint>''')

        content_opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package version="3.0" unique-identifier="BookId" xmlns="http://www.idpf.org/2007/opf">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="BookId">urn:uuid:{book_uuid}</dc:identifier>
        <dc:title>{title}</dc:title>
        <dc:creator>{author}</dc:creator>
        <dc:language>vi</dc:language>
        <meta name="cover" content="cover_img"/>
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
        <meta name="dtb:totalPageCount" content="{chap_idx}"/>
        <meta name="dtb:maxPageNumber" content="{chap_idx}"/>
    </head>
    <docTitle><text>{title}</text></docTitle>
    <navMap>
{chr(10).join(toc_nav_points)}
    </navMap>
</ncx>'''
        zf.writestr('OEBPS/toc.ncx', toc_ncx)

    return True, epub_path
