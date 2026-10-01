# Ghi Chú & Kế Hoạch Cải Thiện Bộ Giải Mã AVn & OCR (TODO)

Tài liệu này ghi nhận các trường hợp vỡ dấu, lỗi font sót lại từ ảnh chụp thực tế của sách *Bill Gates đã nói* và trạng thái hoàn thành.

---

## 1. Danh Sách Lỗi Phát Hiện Từ Ảnh Thực Tế

### Nhóm 1: Từ viết hoa toàn bộ (All-Caps / Tiêu đề chương) — [x] ĐÃ GIẢI QUYẾT TRONG v1.3.2
* Bộ quy tắc mở rộng hỗ trợ toàn bộ 100% nguyên âm tiếng Việt in hoa (`ÀOAÅN` -> `ĐOẠN`, `ÛÚÃ` -> `ƯỞ`, `AÂ` -> `À`, `ÊÅ` -> `Ậ`, `ĐÓ` -> `ĐỈ`):
  - `GIAI ĐOAẢN` ➔ `GIAI ĐOẠN`
  - `TRƯƠÃNG THAÂNH` ➔ `TRƯỞNG THÀNH`
  - `NHÂN VÂÅT` ➔ `NHÂN VẬT`
  - `TỘT ĐÓNH` ➔ `TỘT ĐỈNH`
  - `HIỆN TÌNH NGÀNH CÔNG NGHỆ THÔNG TIN QUA TƯ DUY CỦA BILL GATES`
  - `CÁC MỐC THỜI GIAN QUAN TRỌNG TRONG CUỘC ĐỜI BILL GATES`

### Nhóm 2: Dấu ngã (~) bị nhận nhầm hoặc thiếu dấu — [x] ĐÃ GIẢI QUYẾT TRONG v1.3.2
* Bổ sung quy tắc dấu ngã 2-byte AVn (`0xee` / `î`) và từ điển ngữ cảnh:
  - `vân tiếp tục` ➔ `vẫn tiếp tục`
  - `vâîn` ➔ `vẫn`
  - `diên ra` ➔ `diễn ra`
  - `đo xem môi lần` ➔ `đo xem mỗi lần`
  - `chăèng qua` ➔ `chẳng qua`
  - `ngôî ngược` ➔ `ngỗ ngược`
  - `hấp dâîn` ➔ `hấp dẫn`

### Nhóm 3: Dấu thanh lơ lửng / Ký tự dấu kép (Dangling Accents / Diacritic Ghosting) — [x] ĐÃ GIẢI QUYẾT TRONG v1.3.2
* Bộ lọc regex tự động dọn sạch các ký tự dấu sắc lơ lửng (`´` - `\u00B4`), dấu huyền lơ lửng (``` ` - `\u0060`), circumflex (`^`), tilde (`~`):
  - `thiế´u` ➔ `thiếu`
  - `đố´i` ➔ `đối`
  - `phầ`n` ➔ `phần`
  - `mề`m` ➔ `mềm`
  - `tiế´p` ➔ `tiếp`
  - `phố´i` ➔ `phối`
  - `kiế´n` ➔ `kiến`
  - `lầ`m` ➔ `lầm`
  - `cố´` ➔ `cố`
  - `rằ`ng` ➔ `rằng`
  - `đế´n` ➔ `đến`
  - `triế´t` ➔ `triết`
  - `điề`u` ➔ `điều`
  - `đấ´ng` ➔ `đấng`
  - `tố´i` ➔ `tối`

### Nhóm 4: Bảng mã riêng biệt cho âm `ĩ` — [x] ĐÃ GIẢI QUYẾT TRONG v1.3.2
* Đã ánh xạ toàn diện:
  - `vônh cửu` ➔ `vĩnh cửu`
  - `nghôa` ➔ `nghĩa`
  - `nghô` ➔ `nghĩ`
  - `họa sô` ➔ `họa sĩ`, `tiến sô` ➔ `tiến sĩ`, `nghệ sô` ➔ `nghệ sĩ`

---

## 2. Các Tính Năng Đột Phá Bổ Sung Theo Chuẩn Convert2EPUB (v1.3.2)

1. **Nhận diện Chương Thực Tế & Mục Lục Sống Động (Real Chapters & Working TOC):**
   - Tự động phát hiện các tiêu đề chương (`Chương X`, `Phần X`, tiêu đề in hoa như `MỘT CON NGƯỜI MỘT CON ĐƯỜNG`, `GIAI ĐOẠN TRƯỞNG THÀNH`, v.v.).
   - Tách thành từng file `chapter_XXX.xhtml` độc lập chuẩn EPUB 3 thay vì cắt chia 10 trang ngẫu nhiên.
   - Xây dựng đồng thời `OEBPS/toc.ncx` (EPUB 2 / Kindle) và `OEBPS/Text/nav.xhtml` (EPUB 3 / Apple Books / Thorium) với tên chương đầy đủ.

2. **Khử Tiêu Đề Đầu/Cuối Trang & Watermark (Running Headers, Footers & Watermark Stripping):**
   - Tự động nhận diện và loại bỏ các dòng tiêu đề lặp lại (`Bill Gates đã nói • 11`, `10 • Bill Gates đã nói`).
   - Xóa bỏ số trang lẻ loi kẹp giữa nội dung làm ngắt đứt mạch đọc câu chữ.
   - Tự động dọn sạch các watermark quảng cáo (`Chiasemoi.com`, `thuviensach`, `tve-4u`, v.v.).

3. **Nối Đoạn Văn Mượt Mà & Nối Từ Gạch Nối (Reflowable Paragraphs & De-hyphenation):**
   - Tự động nối các dòng bị ngắt cứng của định dạng PDF thành các đoạn văn `<p>` hoàn chỉnh, thụt lề chuẩn xuất bản.
   - Nối tự động các từ bị gạch nối cuối dòng (`kinh-` + `doanh` ➔ `kinh doanh`, `Micro-` + `Soft` ➔ `Microsoft`).
