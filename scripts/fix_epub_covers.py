import os
import sys
import zipfile
import re
import pymupdf

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def find_first_image_in_epub(file_map):
    patterns = [
        r'^index-1_1\.(jpg|jpeg|png|webp)$',
        r'^index-0_1\.(jpg|jpeg|png|webp)$',
        r'^index-01_1\.(jpg|jpeg|png|webp)$',
        r'^index-001_1\.(jpg|jpeg|png|webp)$',
        r'^index-1_0\.(jpg|jpeg|png|webp)$',
        r'^cover\.(jpg|jpeg|png|webp)$',
        r'^OEBPS/Images/page_0001\.(jpg|jpeg|png|webp)$',
        r'^Images/page_0001\.(jpg|jpeg|png|webp)$',
    ]
    for p in patterns:
        for name in file_map.keys():
            if re.search(p, name, re.IGNORECASE) and name != 'cover_image.jpg':
                return name
    return None


def extract_pdf_cover(pdf_path, dpi_scale=2.0, jpeg_quality=90):
    try:
        doc = pymupdf.open(pdf_path)
        if len(doc) > 0:
            page = doc[0]
            mat = pymupdf.Matrix(dpi_scale, dpi_scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            return pix.tobytes(output='jpg', jpg_quality=jpeg_quality)
    except Exception as e:
        print(f'Error extracting PDF cover from {pdf_path}: {e}')
    return None


def fix_epub_cover(epub_path, pdf_path=None):
    """
    Replaces generic Calibre placeholder cover with the actual illustrated cover image.
    """
    if pdf_path is None:
        pdf_path = os.path.splitext(epub_path)[0] + '.pdf'

    with zipfile.ZipFile(epub_path, 'r') as zin:
        file_map = {name: zin.read(name) for name in zin.namelist()}
    
    if 'cover_image.jpg' in file_map:
        real_cover_bytes = None
        source_desc = ''

        first_img_name = find_first_image_in_epub(file_map)
        if first_img_name:
            real_cover_bytes = file_map[first_img_name]
            source_desc = f'internal image ({first_img_name})'
        
        if (real_cover_bytes is None or len(real_cover_bytes) < 10000) and os.path.exists(pdf_path):
            pdf_cover = extract_pdf_cover(pdf_path)
            if pdf_cover and len(pdf_cover) > 10000:
                real_cover_bytes = pdf_cover
                source_desc = f'PDF page 0 ({os.path.basename(pdf_path)})'
        
        if real_cover_bytes and len(real_cover_bytes) > 5000:
            file_map['cover_image.jpg'] = real_cover_bytes
            temp_epub = epub_path + '.tmp'
            with zipfile.ZipFile(temp_epub, 'w', zipfile.ZIP_DEFLATED) as zout:
                if 'mimetype' in file_map:
                    zout.writestr('mimetype', file_map['mimetype'], compress_type=zipfile.ZIP_STORED)
                for name, data in file_map.items():
                    if name != 'mimetype':
                        zout.writestr(name, data)
            os.replace(temp_epub, epub_path)
            return True, source_desc
    return False, 'no_change'


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    if os.path.isfile(target) and target.lower().endswith('.epub'):
        ok, desc = fix_epub_cover(target)
        print(f'Fixed {target}: {ok} ({desc})')
    elif os.path.isdir(target):
        count = 0
        for root, dirs, files in os.walk(target):
            for f in files:
                if f.lower().endswith('.epub'):
                    p = os.path.join(root, f)
                    try:
                        ok, desc = fix_epub_cover(p)
                        if ok:
                            count += 1
                            print(f'[{count}] Fixed cover: {f} using {desc}')
                    except Exception as e:
                        print(f'Error on {f}: {e}')
        print(f'Total covers fixed: {count}')
