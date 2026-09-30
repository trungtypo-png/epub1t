# ebook-convert-1bitmono 📚⚡

> Pipeline tự động hóa chuyển đổi và tối ưu hóa sách điện tử & tài liệu scan sang định dạng EPUB chuẩn chất lượng cao. Tích hợp chuẩn nén 1-bit Monochrome Bilevel siêu nhẹ, khử trang trắng rác và tự động phục hồi ảnh bìa minh họa gốc.

[English](README.md) | **Tiếng Việt**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.1.0-green.svg)](https://github.com/trungtypo-png/ebook-convert-1bitmono/releases)

---

## 🌟 Tính Năng Nổi Bật

- ⚡ **Chuẩn Nén 1-Bit Monochrome Bilevel:** Biến các cuốn sách scan chữ dung lượng nặng (>100MB) thành file EPUB Fixed-Layout siêu nhẹ (chỉ còn ~20–35MB) mà vẫn giữ độ sắc nét từng nét chữ ở độ phân giải cao (2000px - 3400px).
- 🎨 **Tự Động Phục Hồi Bìa Sách Minh Họa Gốc:** Tự động trích xuất ảnh bìa chất lượng cao từ trang đầu tiên của file gốc và thay thế bìa tạm 2 màu mặc định của Calibre.
- 🧹 **Khử Sạch Layer Rác & Trang Trắng Đệm:** Sử dụng thuật toán phân tích histogram độ lệch chuẩn (`mean >= 250`, `stddev <= 3.5`) để loại bỏ 100% trang trắng rác, đồng thời bóc tách sạch các layer phân mảnh `_2.jpg`, `_3.png` và icon `<3KB` do Calibre `pdftohtml` sinh ra.
- 📱 **Khung Hiển Thị Responsive SVG Viewport:** Sử dụng thẻ `<svg viewBox="0 0 w h">` giúp trang sách tự động phóng to vừa vặn 100% cửa sổ đọc trên mọi loại thiết bị (Kindle, Kobo, iPad, điện thoại, máy tính) mà không bị viền đen hay lệch khung hình.
- 🛡️ **Bảo Toàn Dữ Liệu An Toàn:** Tự động kiểm tra tính toàn vẹn của file EPUB (`META-INF/container.xml`) trước khi quyết định xóa file nguồn cũ.

---

## 📦 Cài Đặt & Sử Dụng

### 1. Tải Ứng Dụng Đóng Gói Sẵn (Không Cần Cài Python)
Tải trực tiếp từ mục **[Releases](https://github.com/trungtypo-png/ebook-convert-1bitmono/releases)**:
* **Windows:** Tải file `Ebook1BitOptimizer-Windows.zip` (giải nén và chạy `Ebook1BitOptimizer.exe`).
* **macOS:** Tải file `Ebook1BitOptimizer-macOS.tar.gz`.

### 2. Hoặc Chạy Trực Tiếp Bằng Python 3.9+
```bash
git clone https://github.com/trungtypo-png/ebook-convert-1bitmono.git
cd ebook-convert-1bitmono
pip install -r requirements.txt
python gui.py
```

### 3. Công cụ Calibre (Tùy chọn cho sách chữ)
* Chỉ cần khi chuyển đổi sách chữ định dạng cổ (`.prc`, `.mobi`, `.azw3`, `.docx`).
* Tải về tại [Trang chủ Calibre](https://calibre-ebook.com/download) (hoặc bản Calibre Portable).

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Giao Diện Đồ Họa (GUI)
Chạy `python gui.py` hoặc click đúp file `.exe` / app đã đóng gói.

### 2. Dòng Lệnh (CLI)
```bash
# Chuyển đổi toàn bộ thư mục sách/PDF (Chế độ 1-bit scan)
python scripts/convert_books.py "/duong/dan/thu/muc/sach" --mode 1bit

# Chuyển đổi và xóa an toàn file gốc
python scripts/convert_books.py "/duong/dan/thu/muc/sach" --delete-source

# Dọn sạch trang trắng & layer rác
python scripts/clean_large_epubs.py "/duong/dan/thu/muc/sach"

# Sửa bìa minh họa gốc
python scripts/fix_epub_covers.py "/duong/dan/thu/muc/sach"
```

---

## 🤝 Lời Cảm Ơn & Ghi Nhận Đóng Góp (Credits & Contributors)

Dự án xin gửi lời cảm ơn trân trọng đến các tác giả và cộng đồng các dự án mã nguồn mở tuyệt vời:

* **[Calibre](https://github.com/kovidgoyal/calibre)** phát triển bởi *Kovid Goyal* và các cộng tác viên — Công cụ tiêu chuẩn hàng đầu thế giới về quản lý và chuyển đổi ebook.
* **[Kindle Comic Converter (KCC)](https://github.com/ciromattia/kcc)** phát triển bởi *Ciro Mattia*, *Darío Marcelino* và cộng đồng — Nền tảng tiên phong tối ưu truyện tranh cho thiết bị đọc sách e-reader.
* **[PyMuPDF (FitZ)](https://github.com/pymupdf/PyMuPDF)** phát triển bởi *Artifex Software* & đội ngũ *PyMuPDF* — Engine trích xuất và render PDF tốc độ cao.
* **[Pillow (PIL)](https://github.com/python-pillow/Pillow)** bởi *Jeffrey A. Clark* và cộng tác viên — Thư viện xử lý hình ảnh cốt lõi trong Python.

---

## 🤖 Antigravity / AI Agent Skill

Repository này đi kèm file cấu hình [`SKILL.md`](./SKILL.md) đã được chuẩn hóa sẵn, có thể nạp trực tiếp vào **Google Antigravity** hoặc các framework AI Agent để tự động hóa toàn bộ quy trình xử lý kho sách của bạn.

---

## 📄 Giấy Phép (License)

Phát hành dưới giấy phép mã nguồn mở [MIT License](LICENSE).
