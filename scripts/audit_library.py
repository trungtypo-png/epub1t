import os
import sys
import re
import io
import json
import time
import argparse
import zipfile
from collections import defaultdict
from PIL import Image, ImageStat

# Ensure UTF-8 output across Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        pymupdf = None


def normalize_title(name):
    """Normalize book filename for fuzzy matching between formats."""
    stem = os.path.splitext(os.path.basename(name))[0].lower()
    # Remove common tags, brackets, and extra punctuation
    stem = re.sub(r'[\(\[\{].*?[\)\]\}]', '', stem)
    stem = re.sub(r'[_\-\.\,\:\;]', ' ', stem)
    stem = re.sub(r'\s+', ' ', stem).strip()
    return stem


def is_blank_image(img_or_data, mean_thresh=250.0, std_thresh=3.5):
    """Detect whether an image is a blank white or black spacer page."""
    try:
        if isinstance(img_or_data, Image.Image):
            gray = img_or_data.convert('L') if img_or_data.mode != 'L' else img_or_data
        else:
            im = Image.open(io.BytesIO(img_or_data))
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


def inspect_pdf_nature(pdf_path):
    """
    Examines a PDF to determine if it is:
    - 'digital_text' (real vector text, best for Calibre reflowable EPUB)
    - 'scanned_image' (scanned page images, best for epub1t 1-bit monochrome)
    - 'corrupt' / 'empty'
    """
    if not pymupdf or not os.path.exists(pdf_path):
        return 'unknown', 0, 0
    
    try:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        if total_pages == 0:
            return 'empty', 0, 0

        # Sample up to first 5 pages (excluding cover)
        sample_pages = min(5, total_pages)
        text_char_count = 0
        image_count = 0

        for i in range(sample_pages):
            page = doc[i]
            text = page.get_text('text')
            text_char_count += len(text.strip())
            image_count += len(page.get_images())

        avg_chars_per_page = text_char_count / sample_pages
        if avg_chars_per_page > 150:
            return 'digital_text', total_pages, int(avg_chars_per_page)
        elif image_count >= sample_pages:
            return 'scanned_image', total_pages, int(avg_chars_per_page)
        else:
            return 'mixed_or_scanned', total_pages, int(avg_chars_per_page)
    except Exception:
        return 'corrupt', 0, 0


def inspect_epub(epub_path):
    """
    Inspects an EPUB for:
    - Integrity (valid container, opf)
    - File size
    - Layout (reflowable vs fixed-layout)
    - Inverted/negative polarity in interior images (black background bug)
    - Calibre multi-layer artifacts (_2.jpg, _3.png)
    - Tiny junk images (<3KB)
    - Total page/image count
    """
    info = {
        'path': epub_path,
        'filename': os.path.basename(epub_path),
        'size_mb': os.path.getsize(epub_path) / (1024 * 1024),
        'is_valid': False,
        'has_container': False,
        'has_opf': False,
        'layout': 'unknown',
        'image_count': 0,
        'inverted_polarity': False,
        'inverted_pages': [],
        'multilayer_artifacts': 0,
        'tiny_junk_images': 0,
        'has_cover': False,
        'issues': []
    }

    try:
        with zipfile.ZipFile(epub_path, 'r') as zf:
            info['is_valid'] = True
            names = zf.namelist()
            info['has_container'] = 'META-INF/container.xml' in names
            
            opf_files = [n for n in names if n.lower().endswith('.opf')]
            info['has_opf'] = len(opf_files) > 0
            
            if not info['has_container'] or not info['has_opf']:
                info['issues'].append('INVALID_STRUCTURE')
                return info

            opf_content = zf.read(opf_files[0]).decode('utf-8', errors='ignore')
            if 'rendition:layout' in opf_content and 'pre-paginated' in opf_content:
                info['layout'] = 'fixed_layout'
            else:
                info['layout'] = 'reflowable'

            # Cover check
            if 'cover' in opf_content.lower() or any('cover' in n.lower() for n in names):
                info['has_cover'] = True
            else:
                info['issues'].append('MISSING_COVER')

            # Image inspection
            image_names = [n for n in names if n.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            info['image_count'] = len(image_names)

            # Check artifacts
            for img_n in image_names:
                if re.search(r'index-\d+_[23]\.(jpg|png|webp)', img_n):
                    info['multilayer_artifacts'] += 1
                try:
                    data = zf.read(img_n)
                    if len(data) < 2500 and 'cover' not in img_n.lower():
                        info['tiny_junk_images'] += 1
                except Exception:
                    pass

            if info['multilayer_artifacts'] > 0:
                info['issues'].append(f'MULTILAYER_ARTIFACTS({info["multilayer_artifacts"]})')

            # Polarity Check on Interior Scanned Pages (Fixed-layout or Image-as-page EPUBs)
            is_scanned_book = (info['layout'] == 'fixed_layout') or (len(image_names) >= 20)
            if is_scanned_book and len(image_names) > 3:
                # Sample interior pages (skip cover page 0 and check true page images)
                sample_indices = [2, 5, min(15, len(image_names) - 1), min(30, len(image_names) - 1)]
                sample_indices = sorted(list(set([idx for idx in sample_indices if idx < len(image_names)])))
                
                dark_count = 0
                for idx in sample_indices:
                    img_name = image_names[idx]
                    try:
                        im_data = zf.read(img_name)
                        im = Image.open(io.BytesIO(im_data))
                        # Only full-page scans can suffer from negative/inverted page polarity
                        if im.height >= 800 and im.width >= 500:
                            stat = ImageStat.Stat(im.convert('L'))
                            mean_b = stat.mean[0]
                            # Inverted text pages have solid black background (mean < 50)
                            if mean_b < 50 and not is_blank_image(im):
                                dark_count += 1
                                info['inverted_pages'].append(f'{img_name} (mean={mean_b:.1f})')
                    except Exception:
                        pass
                
                if dark_count >= 2:
                    info['inverted_polarity'] = True
                    info['issues'].append('INVERTED_POLARITY')

            # Size warnings
            if info['size_mb'] > 50:
                info['issues'].append('CRITICAL_BLOAT_OVER_50MB')
            elif info['size_mb'] > 15:
                info['issues'].append('BLOAT_OVER_15MB')

    except zipfile.BadZipFile:
        info['issues'].append('CORRUPT_ZIP')
    except Exception as e:
        info['issues'].append(f'ERROR_{type(e).__name__}')

    return info


def run_library_audit(
    root_dir,
    ignore_folders=None,
    check_pdf_nature=True,
    progress_callback=None
):
    """Audits the entire ebook repository and returns a structured audit report."""
    if ignore_folders is None:
        ignore_folders = {'.agents', '.git', '$RECYCLE.BIN', 'System Volume Information', '01. Truyện Tranh'}

    start_time = time.time()
    all_files = []
    category_counts = defaultdict(lambda: defaultdict(int))
    
    # 1. Collect all files
    for root, dirs, files in os.walk(root_dir):
        # Prune ignored folders
        dirs[:] = [d for d in dirs if d not in ignore_folders and not d.startswith('.')]
        # Skip if path contains any ignored folder
        if any(ign in root for ign in ignore_folders):
            continue

        rel_dir = os.path.relpath(root, root_dir)
        top_cat = rel_dir.split(os.sep)[0] if rel_dir != '.' else 'Root'

        for f in files:
            ext = f.lower().split('.')[-1]
            full_path = os.path.join(root, f)
            all_files.append((top_cat, full_path, f, ext))

    # 2. Filter formats
    epubs = [item for item in all_files if item[3] == 'epub']
    pdfs = [item for item in all_files if item[3] == 'pdf' and not item[2].startswith('._')]
    mobis = [item for item in all_files if item[3] in ('mobi', 'prc', 'azw', 'azw3')]
    docxs = [item for item in all_files if item[3] in ('docx', 'doc')]
    junk_mac = [item for item in all_files if item[2].startswith('._') or item[2] in ('.DS_Store', 'Thumbs.db')]

    total_scanned = len(all_files)
    
    # 3. Build index of EPUB titles for matching
    epub_index = set()
    for cat, full_p, f, ext in epubs:
        epub_index.add(normalize_title(f))
        category_counts[cat]['epub'] += 1

    # 4. Check Unconverted Sources
    unconverted_pdfs = []
    unconverted_mobis = []
    unconverted_docxs = []

    for cat, full_p, f, ext in pdfs:
        category_counts[cat]['pdf'] += 1
        norm = normalize_title(f)
        if norm not in epub_index:
            unconverted_pdfs.append((cat, full_p, f))

    for cat, full_p, f, ext in mobis:
        category_counts[cat]['mobi'] += 1
        norm = normalize_title(f)
        if norm not in epub_index:
            unconverted_mobis.append((cat, full_p, f))

    for cat, full_p, f, ext in docxs:
        category_counts[cat]['docx'] += 1
        norm = normalize_title(f)
        if norm not in epub_index:
            unconverted_docxs.append((cat, full_p, f))

    # 5. Classify Unconverted PDFs (Digital text vs Scanned images)
    pdf_details = []
    if check_pdf_nature:
        for idx, (cat, full_p, f) in enumerate(unconverted_pdfs):
            if progress_callback:
                progress_callback('pdf', idx + 1, len(unconverted_pdfs), f)
            nature, pages, chars = inspect_pdf_nature(full_p)
            sz = os.path.getsize(full_p) / (1024 * 1024)
            pdf_details.append({
                'category': cat,
                'path': full_p,
                'filename': f,
                'size_mb': sz,
                'pages': pages,
                'nature': nature,
                'chars_per_page': chars,
                'recommended_tool': 'calibre_convert' if nature == 'digital_text' else 'epub1t_1bit'
            })

    # 6. Deep Inspect EPUBs
    epub_inspections = []
    for idx, (cat, full_p, f, ext) in enumerate(epubs):
        if progress_callback:
            progress_callback('epub', idx + 1, len(epubs), f)
        res = inspect_epub(full_p)
        res['category'] = cat
        epub_inspections.append(res)

    # 7. Compute Statistics & Health Score
    broken_epubs = [e for e in epub_inspections if not e['is_valid'] or 'INVALID_STRUCTURE' in e['issues']]
    inverted_epubs = [e for e in epub_inspections if e['inverted_polarity']]
    bloated_epubs = [e for e in epub_inspections if e['size_mb'] > 15]
    artifact_epubs = [e for e in epub_inspections if e['multilayer_artifacts'] > 0]
    missing_covers = [e for e in epub_inspections if 'MISSING_COVER' in e['issues']]

    # Health Score Formula (0 to 100)
    score = 100.0
    score -= len(broken_epubs) * 12.0
    score -= len(inverted_epubs) * 8.0
    score -= len(bloated_epubs) * 1.5
    score -= min(20.0, len(unconverted_pdfs) * 0.4)
    score -= min(10.0, len(missing_covers) * 0.2)
    score -= min(10.0, len(junk_mac) * 0.2)
    health_score = max(0.0, min(100.0, score))

    if health_score >= 90:
        grade = 'A (Xuất sắc)'
    elif health_score >= 80:
        grade = 'B (Tốt)'
    elif health_score >= 70:
        grade = 'C (Khá - Cần xử lý một số đầu sách)'
    elif health_score >= 50:
        grade = 'D (Cần bảo trì)'
    else:
        grade = 'F (Báo động)'

    duration = time.time() - start_time

    return {
        'root_dir': root_dir,
        'duration_seconds': duration,
        'health_score': round(health_score, 1),
        'grade': grade,
        'summary': {
            'total_epubs': len(epubs),
            'total_pdfs': len(pdfs),
            'total_mobis': len(mobis),
            'total_docxs': len(docxs),
            'unconverted_pdfs': len(unconverted_pdfs),
            'unconverted_mobis': len(unconverted_mobis),
            'unconverted_docxs': len(unconverted_docxs),
            'mac_junk_files': len(junk_mac),
            'broken_epubs': len(broken_epubs),
            'inverted_epubs': len(inverted_epubs),
            'bloated_epubs_over_15mb': len(bloated_epubs),
            'epubs_with_artifacts': len(artifact_epubs),
            'epubs_missing_cover': len(missing_covers)
        },
        'category_breakdown': dict(category_counts),
        'broken_epubs': broken_epubs,
        'inverted_epubs': inverted_epubs,
        'bloated_epubs': bloated_epubs,
        'unconverted_pdf_details': pdf_details,
        'unconverted_mobis': unconverted_mobis,
        'unconverted_docxs': unconverted_docxs,
        'mac_junk_files': [j[1] for j in junk_mac]
    }


def format_markdown_report(report):
    """Formats the audit result into a clean, GitHub Markdown report."""
    s = report['summary']
    md = []
    md.append(f"# Báo Cáo Sức Khỏe Kho Sách Ebook: {os.path.basename(report['root_dir'])}")
    md.append(f"\n> **Thời gian quét:** {report['duration_seconds']:.1f} giây | **Thư mục:** `{report['root_dir']}`\n")
    
    # Overall Score Box
    md.append("## 1. Tổng Quan Chỉ Số Sức Khỏe (Library Health Score)")
    md.append(f"\n| Chỉ Số | Giá Trị | Đánh Giá |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| **Điểm Sức Khỏe** | **{report['health_score']} / 100** | **Hạng {report['grade']}** |")
    md.append(f"| **Tổng Sách EPUB** | **{s['total_epubs']}** | Kho sách chính |")
    md.append(f"| **PDF Chưa Convert** | **{s['unconverted_pdfs']}** / {s['total_pdfs']} | Cần chuyển đổi sang EPUB |")
    md.append(f"| **MOBI/PRC Chưa Convert** | **{s['unconverted_mobis']}** | Cần convert & xóa nguồn |")
    md.append(f"| **EPUB Hỏng (Corrupt)** | **{s['broken_epubs']}** | Cần tái tạo khẩn cấp |")
    md.append(f"| **EPUB Âm Bản (Inverted)** | **{s['inverted_epubs']}** | Lỗi nền đen chữ trắng |")
    md.append(f"| **EPUB Quá Tải (>15MB)** | **{s['bloated_epubs_over_15mb']}** | Cần nén 1-bit monochrome |")
    md.append(f"| **File Rác macOS (._*)** | **{s['mac_junk_files']}** | Cần dọn dẹp sạch |")

    # Critical Issues
    if report['broken_epubs'] or report['inverted_epubs']:
        md.append("\n## 2. Các Sự Cố Nghiêm Trọng Cần Khắc Phục Ngay")
        if report['broken_epubs']:
            md.append("\n### 2.1. EPUB Bị Hỏng Cấu Trúc (Corrupt/Unreadable)")
            for item in report['broken_epubs']:
                md.append(f"- ❌ `[{item['category']}]` {item['filename']} -> Lỗi: `{', '.join(item['issues'])}`")
        
        if report['inverted_epubs']:
            md.append("\n### 2.2. EPUB Bị Âm Bản (Nền Đen Chữ Trắng / ImageMask Bug)")
            for item in report['inverted_epubs']:
                md.append(f"- ⚠️ `[{item['category']}]` {item['filename']} -> Trang lỗi: {', '.join(item['inverted_pages'][:3])}")

    # Unconverted PDFs
    pdf_details = report['unconverted_pdf_details']
    if pdf_details:
        md.append(f"\n## 3. Danh Sách PDF Chưa Convert Sang EPUB ({len(pdf_details)} file)")
        md.append("\n| Phân Loại | File Sách | Dung Lượng | Trang | Công Cụ Đề Xuất |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")
        
        # Sort by size descending
        sorted_pdfs = sorted(pdf_details, key=lambda x: x['size_mb'], reverse=True)
        for item in sorted_pdfs[:40]:  # Top 40 largest
            nature_badge = "📖 Chữ số (Text)" if item['nature'] == 'digital_text' else "🖼️ Ảnh scan"
            tool_rec = "`ebook-convert` (Chữ chảy)" if item['recommended_tool'] == 'calibre_convert' else "`epub1t` (1-bit High-Res)"
            md.append(f"| {nature_badge} | `{item['filename']}` | {item['size_mb']:.1f} MB | {item['pages']} trang | {tool_rec} |")
        
        if len(sorted_pdfs) > 40:
            md.append(f"\n*... và {len(sorted_pdfs) - 40} file PDF khác xem chi tiết trong file JSON.*")

    # Bloated EPUBs
    if report['bloated_epubs']:
        md.append(f"\n## 4. Danh Sách EPUB Dung Lượng Lớn (>15MB) Cần Nén 1-Bit ({len(report['bloated_epubs'])} file)")
        sorted_bloat = sorted(report['bloated_epubs'], key=lambda x: x['size_mb'], reverse=True)
        md.append("\n| Thư Mục | File Sách | Dung Lượng | Ảnh | Đề Xuất Xử Lý |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")
        for item in sorted_bloat[:25]:
            md.append(f"| `{item['category']}` | `{item['filename']}` | **{item['size_mb']:.1f} MB** | {item['image_count']} ảnh | Chạy `epub1t` 1-bit High-Res |")

    # Action Plan & Remediation Commands
    rdir = report['root_dir']
    md.append("\n## 5. Kế Hoạch & Lệnh Tự Động Xử Lý (Remediation)")
    md.append("\nĐể khắc phục hàng loạt các mục trên mà không tốn token, chạy các lệnh sau:")
    md.append("\n```bash")
    md.append("# 1. Dọn dẹp sạch file rác macOS AppleDouble (._*):")
    md.append('python -c "import os, glob; [os.remove(f) for f in glob.glob(\'F:/Book/**/._*\', recursive=True)]"')
    md.append("\n# 2. Tự động convert tất cả PDF scan sang EPUB 1-bit bằng epub1t:")
    md.append(r'python -m epub1t.batch_convert --input-dir "F:\Book" --mode 1bit')
    md.append("\n# 3. Đồng bộ hai chiều và scan lại Nextcloud:")
    md.append('ssh zed110@100.93.221.116 "docker exec -u www-data nextcloud php occ files:scan --all"')
    md.append("```\n")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Audit and Health Check Ebook Library (EPUB/PDF)")
    parser.add_argument("--path", default=r"F:\Book", help="Root directory of ebook library")
    parser.add_argument("--report", default=None, help="Output markdown report file path")
    parser.add_argument("--json", default=None, help="Output json report file path")
    parser.add_argument("--no-pdf-inspect", action="store_true", help="Skip deep inspection of PDF nature")
    parser.add_argument("--clean-junk", action="store_true", help="Automatically delete macOS junk files (._*)")
    parser.add_argument("--batch-convert-scans", action="store_true", help="Auto-convert all unconverted scanned PDFs to 1-bit EPUB via epub1t")
    args = parser.parse_args()

    print(f"Scanning ebook library at: {args.path} ...")
    
    def on_progress(stage, curr, total, name):
        if curr % 25 == 0 or curr == total:
            print(f"[{stage.upper()}] {curr}/{total} - {name[:40]}...")

    report = run_library_audit(
        args.path,
        check_pdf_nature=not args.no_pdf_inspect,
        progress_callback=on_progress
    )

    md_output = format_markdown_report(report)

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(md_output)
        print(f"\nMarkdown report saved to: {args.report}")
    else:
        print("\n" + md_output)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"JSON report saved to: {args.json}")

    if args.clean_junk and report['mac_junk_files']:
        deleted = 0
        for f in report['mac_junk_files']:
            try:
                os.remove(f)
                deleted += 1
            except Exception:
                pass
        print(f"Cleaned {deleted} macOS junk files.")

    if args.batch_convert_scans:
        sys.path.insert(0, r"D:\github\epub1t")
        try:
            from scripts.convert_books import convert_scanned_pdf_to_epub
        except ImportError:
            try:
                from convert_books import convert_scanned_pdf_to_epub
            except ImportError:
                print("Could not import convert_books from epub1t!")
                return

        scans = [item for item in report.get('unconverted_pdf_details', []) if item.get('recommended_tool') == 'epub1t_1bit']
        print(f"\n[+] Tìm thấy {len(scans)} file PDF scan cần convert sang EPUB 1-bit:")
        for idx, item in enumerate(scans):
            pdf_p = item['path']
            print(f"[{idx+1}/{len(scans)}] Đang xử lý: {item['filename']} ...")
            try:
                ok, res = convert_scanned_pdf_to_epub(pdf_p, mode='1bit')
                print(f"    -> Kết quả: {ok}")
            except Exception as e:
                print(f"    -> Lỗi: {e}")
        print("\n[+] Hoàn tất chuyển đổi hàng loạt!")


if __name__ == "__main__":
    main()
