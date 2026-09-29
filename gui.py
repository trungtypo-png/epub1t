import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Ensure scripts folder is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts.convert_books import convert_document_to_epub, convert_scanned_pdf_to_epub
from scripts.clean_large_epubs import clean_epub_artifacts
from scripts.fix_epub_covers import fix_epub_cover


class EbookConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ebook Convert & 1-Bit Optimizer 📚")
        self.geometry("640x560")
        self.minsize(580, 480)

        # Variables
        self.path_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="1bit")
        self.del_src_var = tk.BooleanVar(value=False)
        self.fix_cover_var = tk.BooleanVar(value=True)
        self.clean_art_var = tk.BooleanVar(value=True)
        self.is_processing = False

        self._build_ui()

    def _build_ui(self):
        # Header Frame
        header = ttk.Frame(self, padding="15 15 15 10")
        header.pack(fill=tk.X)

        title_lbl = ttk.Label(header, text="Ebook 1-Bit Mono & EPUB Optimizer", font=("Segoe UI", 14, "bold"))
        title_lbl.pack(anchor=tk.W)
        subtitle_lbl = ttk.Label(header, text="Chuyển đổi sách chữ & tối ưu hoá PDF scan sang EPUB siêu nhẹ", font=("Segoe UI", 9))
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Main Content Frame
        content = ttk.Frame(self, padding="15 0 15 10")
        content.pack(fill=tk.BOTH, expand=True)

        # File/Folder Selection
        path_group = ttk.LabelFrame(content, text=" 📂 Chọn File hoặc Thư Mục Sách ", padding="10")
        path_group.pack(fill=tk.X, pady=(0, 10))

        path_entry = ttk.Entry(path_group, textvariable=self.path_var, font=("Segoe UI", 9))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_file = ttk.Button(path_group, text="Chọn File...", command=self._browse_file)
        btn_file.pack(side=tk.LEFT, padx=(0, 4))
        btn_dir = ttk.Button(path_group, text="Chọn Thư Mục...", command=self._browse_dir)
        btn_dir.pack(side=tk.LEFT)

        # Options Group
        opts_group = ttk.LabelFrame(content, text=" ⚙️ Tùy Chọn Chuyển Đổi ", padding="10")
        opts_group.pack(fill=tk.X, pady=(0, 10))

        # Mode Selection
        mode_frame = ttk.Frame(opts_group)
        mode_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(mode_frame, text="Chế độ PDF Scan:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        r1 = ttk.Radiobutton(mode_frame, text="1-Bit Monochrome (Siêu nét & nhẹ)", variable=self.mode_var, value="1bit")
        r1.pack(side=tk.LEFT, padx=(0, 10))
        r2 = ttk.Radiobutton(mode_frame, text="Màu gốc (Color)", variable=self.mode_var, value="color")
        r2.pack(side=tk.LEFT, padx=(0, 10))
        r3 = ttk.Radiobutton(mode_frame, text="Xám (Grayscale)", variable=self.mode_var, value="grayscale")
        r3.pack(side=tk.LEFT)

        # Checkboxes
        chk_frame = ttk.Frame(opts_group)
        chk_frame.pack(fill=tk.X)
        c1 = ttk.Checkbutton(chk_frame, text="Tự động sửa ảnh bìa gốc (Cover Fix)", variable=self.fix_cover_var)
        c1.pack(side=tk.LEFT, padx=(0, 15))
        c2 = ttk.Checkbutton(chk_frame, text="Khử trang trắng & layer rác", variable=self.clean_art_var)
        c2.pack(side=tk.LEFT, padx=(0, 15))
        c3 = ttk.Checkbutton(chk_frame, text="Xóa file nguồn cũ sau khi xong", variable=self.del_src_var)
        c3.pack(side=tk.LEFT)

        # Log Text Box
        log_group = ttk.LabelFrame(content, text=" 📝 Tiến Trình Xử Lý ", padding="5")
        log_group.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = tk.Text(log_group, wrap=tk.WORD, font=("Consolas", 8), bg="#1E1E1E", fg="#D4D4D4")
        scrollbar = ttk.Scrollbar(log_group, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Action Buttons & Progress Bar
        bottom_frame = ttk.Frame(self, padding="15 0 15 15")
        bottom_frame.pack(fill=tk.X)

        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 8))

        self.btn_run = ttk.Button(bottom_frame, text="🚀 BẮT ĐẦU CHUYỂN ĐỔI", command=self._start_processing)
        self.btn_run.pack(fill=tk.X, ipady=4)

    def _browse_file(self):
        f = filedialog.askopenfilename(
            title="Chọn File Sách",
            filetypes=[("Ebooks & Documents", "*.pdf *.mobi *.prc *.azw *.azw3 *.docx *.doc *.fb2"), ("All files", "*.*")]
        )
        if f:
            self.path_var.set(f)

    def _browse_dir(self):
        d = filedialog.askdirectory(title="Chọn Thư Mục Chứa Sách")
        if d:
            self.path_var.set(d)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def _start_processing(self):
        target = self.path_var.get().strip()
        if not target or not os.path.exists(target):
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một file hoặc thư mục hợp lệ!")
            return

        if self.is_processing:
            return

        self.is_processing = True
        self.btn_run.config(state=tk.DISABLED)
        self.progress.start(10)
        self.log_text.delete(1.0, tk.END)
        self.log(f"=== BẮT ĐẦU QUY TRÌNH: {target} ===")

        threading.Thread(target=self._run_worker, args=(target,), daemon=True).start()

    def _run_worker(self, target):
        try:
            mode = self.mode_var.get()
            del_src = self.del_src_var.get()
            fix_cov = self.fix_cover_var.get()
            clean_art = self.clean_art_var.get()

            files = []
            if os.path.isfile(target):
                files.append(target)
            else:
                for root, _, filenames in os.walk(target):
                    for fn in filenames:
                        ext = os.path.splitext(fn)[1].lower()
                        if ext in ['.pdf', '.prc', '.mobi', '.azw', '.azw3', '.docx', '.doc', '.fb2', '.epub']:
                            files.append(os.path.join(root, fn))

            self.log(f"Tìm thấy {len(files)} file cần xử lý...\n")

            for i, f in enumerate(files, 1):
                fn = os.path.basename(f)
                ext = os.path.splitext(fn)[1].lower()
                self.log(f"[{i}/{len(files)}] Đang xử lý: {fn}")

                if ext == '.epub':
                    if clean_art:
                        ok, msg = clean_epub_artifacts(f)
                        if ok:
                            self.log(f"   -> Dọn layer rác: {msg}")
                    if fix_cov:
                        ok, desc = fix_epub_cover(f)
                        if ok:
                            self.log(f"   -> Đã sửa bìa ({desc})")
                elif ext == '.pdf':
                    ok, res = convert_scanned_pdf_to_epub(f, mode=mode)
                    self.log(f"   -> Kết quả: {'Thành công' if ok else 'Thất bại'} ({res})")
                    if ok and del_src:
                        os.remove(f)
                        self.log("   -> Đã xóa file PDF nguồn an toàn.")
                else:
                    ok, res = convert_document_to_epub(f, delete_source=del_src, auto_fix_cover=fix_cov)
                    self.log(f"   -> Kết quả: {'Thành công' if ok else 'Thất bại'}")
                    if ok and clean_art:
                        clean_epub_artifacts(res)

            self.log("\n=== HOÀN TẤT TOÀN BỘ QUY TRÌNH ===")
            messagebox.showinfo("Thành công", f"Đã xử lý xong {len(files)} file!")
        except Exception as e:
            self.log(f"\n[LỖI]: {str(e)}")
            messagebox.showerror("Lỗi", str(e))
        finally:
            self.is_processing = False
            self.progress.stop()
            self.btn_run.config(state=tk.NORMAL)


if __name__ == "__main__":
    app = EbookConverterApp()
    app.mainloop()
