# Ghi Chú & Kế Hoạch Cải Thiện Bộ Giải Mã AVn & OCR (TODO)

Tài liệu này ghi nhận các trường hợp vỡ dấu, lỗi font sót lại từ ảnh chụp thực tế của sách *Bill Gates đã nói* để xử lý và cải thiện trong các phiên bản tiếp theo.

---

## 1. Danh Sách Lỗi Phát Hiện Từ Ảnh Thực Tế

### Nhóm 1: Từ viết hoa toàn bộ (All-Caps / Tiêu đề chương)
* Hiện tại bộ quy tắc chủ yếu xử lý chữ thường (`oaå` -> `oạ`, `aâ` -> `à`), các tiêu đề in hoa chưa được map hết dẫn đến:
  - `GIAI ĐOAẢN` ➔ Cần sửa thành: `GIAI ĐOẠN`
  - `TRƯƠÃNG THAÂNH` ➔ Cần sửa thành: `TRƯỞNG THÀNH`
  - `NHÂN VÂÅT` ➔ Cần sửa thành: `NHÂN VẬT`

### Nhóm 2: Dấu ngã (~) bị nhận nhầm hoặc thiếu dấu
* Một số từ mang dấu ngã (`~`) bị biến thành dấu mũ hoặc không dấu:
  - `vân tiếp tục` ➔ Cần sửa thành: `vẫn tiếp tục`
  - `diên ra` ➔ Cần sửa thành: `diễn ra`
  - `đo xem môi lần` ➔ Cần sửa thành: `đo xem mỗi lần`

### Nhóm 3: Dấu thanh lơ lửng / Ký tự dấu kép (Dangling Accents / Diacritic Ghosting)
* Hiện tượng một số từ tiếng Việt đã có dấu nhưng bị dính thêm ký tự dấu sắc lơ lửng (`´` - `\u00B4`), dấu huyền lơ lửng (``` ` - `\u0060`), hoặc ký tự phân cách:
  - `thiế´u` ➔ Cần chuẩn hóa thành: `thiếu`
  - `đố´i` ➔ Cần chuẩn hóa thành: `đối`
  - `phầ`n` ➔ Cần chuẩn hóa thành: `phần`
  - `mề`m` ➔ Cần chuẩn hóa thành: `mềm`
  - `tiế´p` ➔ Cần chuẩn hóa thành: `tiếp`
  - `phố´i` ➔ Cần chuẩn hóa thành: `phối`
  - `kiế´n` ➔ Cần chuẩn hóa thành: `kiến`
  - `lầ`m` ➔ Cần chuẩn hóa thành: `lầm`
  - `cố´` ➔ Cần chuẩn hóa thành: `cố`
  - `rằ`ng` ➔ Cần chuẩn hóa thành: `rằng`
  - `đế´n` ➔ Cần chuẩn hóa thành: `đến`
  - `triế´t` ➔ Cần chuẩn hóa thành: `triết`
  - `điề`u` ➔ Cần chuẩn hóa thành: `điều`
  - `đấ´ng` ➔ Cần chuẩn hóa thành: `đấng`
  - `tố´i` ➔ Cần chuẩn hóa thành: `tối`

### Nhóm 4: Bảng mã riêng biệt cho âm `ĩ`
* `vônh cửu` ➔ Cần sửa thành: `vĩnh cửu` (trong font này `ônh` tương đương với `ĩnh`).

---

## 2. Giải Pháp Triển Khai Trong Tương Lai

1. **Bộ lọc khử dấu lơ lửng (Strip Dangling Accents Regex):**
   ```python
   # Khử dấu sắc/huyền/ngã lơ lửng chèn giữa các ký tự
   text = re.sub(r'([áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ])[\u00B4\u0060\^~]', r'\1', text)
   ```

2. **Bổ sung ánh xạ từ in hoa toàn bộ (Uppercase Title Mappings):**
   * `ĐOAẢN` ➔ `ĐOẠN`
   * `TRƯƠÃNG` ➔ `TRƯỞNG`
   * `THAÂNH` ➔ `THÀNH`
   * `VÂÅT` ➔ `VẬT`

3. **Từ điển ngữ cảnh cho các trường hợp đặc biệt:**
   * `vônh` ➔ `vĩnh`
   * `vân` (khi đi kèm `tiếp tục`) ➔ `vẫn`
   * `diên` (khi đi kèm `ra`) ➔ `diễn`
   * `môi` (khi đi kèm `lần`) ➔ `mỗi`
