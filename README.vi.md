# ebook-convert-1bitmono 📚⚡

> Pipeline tự động hóa chuyển đổi và tối ưu hóa sách điện tử & tài liệu scan sang định dạng EPUB chuẩn chất lượng cao. Tích hợp chuẩn nén 1-bit Monochrome Bilevel siêu nhẹ, khử trang trắng rác và tự động phục hồi ảnh bìa minh họa gốc.

[English](README.md) | **Tiếng Việt**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Tính Năng Nổi Bật

- ⚡ **Chuẩn Nén 1-Bit Monochrome Bilevel:** Biến các cuốn sách scan chữ dung lượng nặng (>100MB) thành file EPUB Fixed-Layout siêu nhẹ (chỉ còn ~20–35MB) mà vẫn giữ độ sắc nét từng nét chữ ở độ phân giải cao (2000px - 3400px).
- 🎨 **Tự Động Phục Hồi Bìa Sách Minh Họa Gốc:** Tự động trích xuất ảnh bìa chất lượng cao từ trang đầu tiên của file gốc và thay thế bìa tạm 2 màu mặc định của Calibre.
- 🧹 **Khử Sạch Layer Rác & Trang Trắng Đệm:** Sử dụng thuật toán phân tích histogram độ lệch chuẩn (`mean >= 250`, `stddev <= 3.5`) để loại bỏ 100% trang trắng rác, đồng thời bóc tách sạch các layer phân mảnh `_2.jpg`, `_3.png` và icon `<3KB` do Calibre `pdftohtml` sinh ra.
- 📱 **Khung Hiển Thị Responsive SVG Viewport:** Sử dụng thẻ `<svg viewBox="0 0 w h">` giúp trang sách tự động phóng to vừa vặn 100% cửa sổ đọc trên mọi loại thiết bị (Kindle, Kobo, iPad, điện thoại, máy tính) mà không bị viền đen hay lệch khung hình.
- 🛡️ **Bảo Toàn Dữ Liệu An Toàn:** Tự động kiểm tra tính toàn vẹn của file EPUB (`META-INF/container.xml`) trước khi quyết định xóa file nguồn cũ.

---

## 📦 Yêu Cầu Phần Mềm & Cài Đặt

### 1. Calibre (Bắt buộc cho sách chữ / chuyển đổi reflowable)
- Tải về từ [Trang chủ Calibre](https://calibre-ebook.com/download) (hoặc dùng bản Calibre Portable).
- Đảm bảo lệnh `ebook-convert` đã có trong biến môi trường `PATH`, hoặc đặt biến môi trường `CALIBRE_PATH` trỏ tới file thực thi:
  - *Windows:* `C:\Program Files\Calibre2\ebook-convert.exe` hoặc `D:\Calibre Portable\Calibre\ebook-convert.exe`
  - *macOS:* `/Applications/calibre.app/Contents/MacOS/ebook-convert`
  - *Linux:* `/usr/bin/ebook-convert`

### 2. Cài Đặt Thư Viện Python
Yêu cầu **Python 3.9+**:
```bash
git clone https://github.com/trungtypo-png/ebook-convert-1bitmono.git
cd ebook-convert-1bitmono
pip install -r requirements.txt
```

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Chuyển Đổi Sách & Tài Liệu Scan
```bash
# Chuyển đổi toàn bộ tài liệu trong thư mục (Chế độ 1-bit monochrome cho PDF scan)
python scripts/convert_books.py "/duong/dan/thu/muc/sach" --mode 1bit

# Chuyển đổi và tự động xóa file gốc sau khi tạo EPUB thành công
python scripts/convert_books.py "/duong/dan/thu/muc/sach" --delete-source

# Chuyển đổi PDF scan giữ nguyên màu gốc (color) hoặc xám (grayscale)
python scripts/convert_books.py "/duong/dan/sach.pdf" --mode color
```

### 2. Quét & Khử Trang Trắng / Layer Rác Toàn Thư Viện
```bash
python scripts/clean_large_epubs.py "/duong/dan/thu/muc/sach"
```

### 3. Tự Động Sửa Bìa Cho Toàn Bộ EPUB
```bash
python scripts/fix_epub_covers.py "/duong/dan/thu/muc/sach"
```

### 4. Sử Dụng Trực Tiếp Trong Code Python
```python
from scripts.convert_books import convert_document_to_epub, convert_scanned_pdf_to_epub

# Chuyển đổi sách chữ PRC / MOBI / AZW3 / DOCX sang EPUB
success, output_path = convert_document_to_epub("sach.mobi", delete_source=False)

# Chuyển đổi PDF scan sang EPUB 1-bit monochrome siêu nét & nhẹ
success, output_path = convert_scanned_pdf_to_epub("sach_scan.pdf", mode="1bit", dpi_scale=1.5)
```

---

## 🤖 Antigravity / AI Agent Skill

Repository này đi kèm file cấu hình [`SKILL.md`](./SKILL.md) đã được chuẩn hóa sẵn, có thể nạp trực tiếp vào **Google Antigravity** hoặc các framework AI Agent để tự động hóa toàn bộ quy trình xử lý kho sách của bạn.

---

## 📄 Giấy Phép (License)

Phát hành dưới giấy phép mã nguồn mở [MIT License](LICENSE).
