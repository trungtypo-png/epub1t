import os
import sys
import zipfile
import re
import io
from PIL import Image, ImageStat

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def is_blank_image(img_data, mean_thresh=250.0, std_thresh=3.5):
    """Detects whether an image is a blank white or black spacer/divider page."""
    try:
        im = Image.open(io.BytesIO(img_data))
        gray = im.convert('L')
        stat = ImageStat.Stat(gray)
        mean, stddev = stat.mean[0], stat.stddev[0]
        if mean >= mean_thresh and stddev <= std_thresh:
            return True
        if mean <= 5.0 and stddev <= 2.0:
            return True
    except Exception:
        pass
    return False


def clean_epub_artifacts(epub_p):
    """
    Cleans up Calibre pdftohtml multi-layer artifacts (_2.jpg, _3.png) and tiny icon artifacts (<3KB).
    Removes phantom blank pages and updates (x)html contents & OPF manifests.
    """
    if not os.path.exists(epub_p):
        return False, 'File not found'
    
    orig_sz = os.path.getsize(epub_p) / (1024 * 1024)
    with zipfile.ZipFile(epub_p, 'r') as zin:
        file_map = {name: zin.read(name) for name in zin.namelist()}

    removed_files = set()
    for name, data in list(file_map.items()):
        # 1. Multi-layer pdftohtml artifacts
        if re.search(r'index-\d+_[23]\.(jpg|png|webp)', name):
            removed_files.add(name)
            del file_map[name]
        # 2. Tiny icon / dropcap / spacer noise
        elif name.lower().endswith(('.jpg', '.png', '.webp')) and name != 'cover_image.jpg' and len(data) < 3000:
            removed_files.add(name)
            del file_map[name]

    if not removed_files:
        return False, 'No artifacts found'

    # Clean references in HTML / XHTML files
    for name, data in list(file_map.items()):
        if name.endswith(('.html', '.xhtml')):
            text = data.decode('utf-8', errors='ignore')
            for r_name in removed_files:
                text = re.sub(r'<p[^>]*><img[^>]*src=[\"\']' + re.escape(r_name) + r'[\"\'][^>]*/>\s*</p>', '', text)
                text = re.sub(r'<img[^>]*src=[\"\']' + re.escape(r_name) + r'[\"\'][^>]*/>', '', text)
            file_map[name] = text.encode('utf-8')

    # Clean OPF Manifest items
    if 'content.opf' in file_map:
        opf_text = file_map['content.opf'].decode('utf-8', errors='ignore')
        for r_name in removed_files:
            opf_text = re.sub(r'<item[^>]*href=[\"\']' + re.escape(r_name) + r'[\"\'][^>]*/>\s*', '', opf_text)
        file_map['content.opf'] = opf_text.encode('utf-8')

    temp_p = epub_p + '.tmp'
    with zipfile.ZipFile(temp_p, 'w', zipfile.ZIP_DEFLATED) as zout:
        if 'mimetype' in file_map:
            zout.writestr('mimetype', file_map['mimetype'], compress_type=zipfile.ZIP_STORED)
        for name, data in file_map.items():
            if name != 'mimetype':
                zout.writestr(name, data)

    os.replace(temp_p, epub_p)
    new_sz = os.path.getsize(epub_p) / (1024 * 1024)
    return True, f'Removed {len(removed_files)} artifacts ({orig_sz:.1f}MB -> {new_sz:.1f}MB)'


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    if os.path.isfile(target) and target.lower().endswith('.epub'):
        ok, msg = clean_epub_artifacts(target)
        print(f"Result for {os.path.basename(target)}: {msg}")
    elif os.path.isdir(target):
        count = 0
        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.lower().endswith('.epub'):
                    p = os.path.join(root, f)
                    ok, msg = clean_epub_artifacts(p)
                    if ok:
                        count += 1
                        print(f"[{count}] Cleaned {f}: {msg}")
        print(f"Total EPUB files optimized: {count}")
