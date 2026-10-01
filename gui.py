import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Ensure scripts folder is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts.convert_books import convert_document_to_epub, convert_scanned_pdf_to_epub, get_calibre_path, is_digital_text_pdf
from scripts.clean_large_epubs import clean_epub_artifacts
from scripts.fix_epub_covers import fix_epub_cover
from scripts.extract_text import export_pdf_to_txt

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".epub1t_config.json")

TEXTS = {
    'vi': {
        'app_title': "Epub1t — Ebook to EPUB 1-Bit Optimizer 📚",
        'title': "Epub1t",
        'subtitle': "Chuyển đổi sách chữ & tối ưu hoá PDF scan sang EPUB siêu nhẹ",
        'lang_label': "Ngôn ngữ:",
        'path_group': " 📂 Chọn File hoặc Thư Mục Sách ",
        'btn_file': "Chọn File...",
        'btn_dir': "Chọn Thư Mục...",
        'opts_group': " ⚙️ Tùy Chọn Chuyển Đổi ",
        'mode_label': "Chế độ PDF:",
        'mode_auto': "Tự động (Auto)",
        'mode_1bit': "1-Bit Đơn sắc",
        'mode_color': "Màu gốc",
        'mode_gray': "Xám",
        'mode_text': "EPUB Chữ",
        'chk_cover': "Tự động sửa ảnh bìa gốc (Cover Fix)",
        'chk_clean': "Khử trang trắng & layer rác",
        'calibre_group': " 🔌 Calibre CLI (Tùy chọn cho sách chữ PRC/MOBI/DOCX) ",
        'calibre_detected': "🟢 Đã nhận diện Calibre: {path}",
        'calibre_not_found': "🟡 Chưa tìm thấy Calibre (Chỉ cần nếu convert PRC/MOBI)",
        'btn_calibre_browse': "Đổi đường dẫn...",
        'calibre_dialog_title': "Chọn file ebook-convert hoặc thư mục Calibre Portable",
        'log_group': " 📝 Tiến Trình Xử Lý ",
        'btn_run': "🚀 BẮT ĐẦU CHUYỂN ĐỔI",
        'btn_running': "⏳ ĐANG XỬ LÝ...",
        'file_dialog_title': "Chọn File Sách",
        'dir_dialog_title': "Chọn Thư Mục Chứa Sách",
        'warn_path': "Vui lòng chọn một file hoặc thư mục hợp lệ!",
        'warn_title': "Cảnh báo",
        'success_title': "Thành công",
        'success_msg': "Đã xử lý xong {count} file!",
        'log_start': "=== BẮT ĐẦU QUY TRÌNH: {path} ===",
        'log_found': "Tìm thấy {count} file cần xử lý...\n",
        'log_proc': "[{i}/{total}] Đang xử lý: {fn}",
        'log_clean': "   -> Dọn layer rác: {msg}",
        'log_cover': "   -> Đã sửa bìa ({desc})",
        'log_result': "   -> Kết quả: {status} ({res})",
        'log_auto_text': "   -> [Tự động] Nhận diện: Sách có lớp chữ số -> Chuyển sang EPUB Chữ",
        'log_auto_scan': "   -> [Tự động] Nhận diện: Sách scan thuần ảnh -> Chuyển sang EPUB 1-Bit Đơn sắc",
        'log_txt': "   -> Đã trích xuất Text: {txt_fn}",
        'log_done': "\n=== HOÀN TẤT TOÀN BỘ QUY TRÌNH ===",
        'status_ok': "Thành công",
        'status_fail': "Thất bại",
    },
    'en': {
        'app_title': "Epub1t — Ebook to EPUB 1-Bit Optimizer 📚",
        'title': "Epub1t",
        'subtitle': "Convert books & optimize scanned PDFs into lightweight EPUBs",
        'lang_label': "Language:",
        'path_group': " 📂 Select Book File or Directory ",
        'btn_file': "Browse File...",
        'btn_dir': "Browse Folder...",
        'opts_group': " ⚙️ Conversion Options ",
        'mode_label': "PDF Mode:",
        'mode_auto': "Auto-Detect",
        'mode_1bit': "1-Bit Monochrome",
        'mode_color': "Original Color",
        'mode_gray': "Grayscale",
        'mode_text': "Reflowable EPUB",
        'chk_cover': "Auto Restore Real Cover",
        'chk_clean': "Clean Ghost Blank Pages & Artifacts",
        'calibre_group': " 🔌 Calibre CLI (Optional for PRC/MOBI/DOCX text books) ",
        'calibre_detected': "🟢 Calibre Detected: {path}",
        'calibre_not_found': "🟡 Calibre not found (Only needed for PRC/MOBI)",
        'btn_calibre_browse': "Browse Path...",
        'calibre_dialog_title': "Select ebook-convert binary or Calibre Portable directory",
        'log_group': " 📝 Processing Logs ",
        'btn_run': "🚀 START CONVERSION",
        'btn_running': "⏳ PROCESSING...",
        'file_dialog_title': "Select Ebook File",
        'dir_dialog_title': "Select Ebook Directory",
        'warn_path': "Please select a valid file or directory!",
        'warn_title': "Warning",
        'success_title': "Success",
        'success_msg': "Processed {count} file(s) successfully!",
        'log_start': "=== STARTING PIPELINE: {path} ===",
        'log_found': "Found {count} file(s) to process...\n",
        'log_proc': "[{i}/{total}] Processing: {fn}",
        'log_clean': "   -> Cleaned artifacts: {msg}",
        'log_cover': "   -> Restored cover ({desc})",
        'log_result': "   -> Result: {status} ({res})",
        'log_auto_text': "   -> [Auto-Detect] Detected digital text -> Exporting Reflowable EPUB",
        'log_auto_scan': "   -> [Auto-Detect] Detected scanned pages -> Exporting 1-Bit Monochrome EPUB",
        'log_done': "\n=== PIPELINE FINISHED ===",
        'status_ok': "Success",
        'status_fail': "Failed",
    }
}


class EbookConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("730x700")
        self.minsize(660, 580)

        # Variables
        self.lang = "vi"
        self.custom_calibre_path = self._load_config().get("calibre_path", "")
        self.path_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="auto")
        self.fix_cover_var = tk.BooleanVar(value=True)
        self.clean_art_var = tk.BooleanVar(value=True)
        self.is_processing = False

        self._build_ui()
        self.apply_language("vi")

    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({"calibre_path": self.custom_calibre_path}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _build_ui(self):
        # Header Frame
        header = ttk.Frame(self, padding="15 15 15 10")
        header.pack(fill=tk.X)

        title_frame = ttk.Frame(header)
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.title_lbl = ttk.Label(title_frame, text="", font=("Segoe UI", 14, "bold"))
        self.title_lbl.pack(anchor=tk.W)
        self.subtitle_lbl = ttk.Label(title_frame, text="", font=("Segoe UI", 9))
        self.subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Language Switcher
        lang_frame = ttk.Frame(header)
        lang_frame.pack(side=tk.RIGHT, anchor=tk.E)

        self.lang_lbl = ttk.Label(lang_frame, text="", font=("Segoe UI", 9))
        self.lang_lbl.pack(side=tk.LEFT, padx=(0, 6))

        self.lang_combo = ttk.Combobox(lang_frame, values=["Tiếng Việt", "English"], state="readonly", width=11)
        self.lang_combo.current(0)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_lang_changed)
        self.lang_combo.pack(side=tk.LEFT)

        # Main Content Frame
        content = ttk.Frame(self, padding="15 0 15 10")
        content.pack(fill=tk.BOTH, expand=True)

        # File/Folder Selection
        self.path_group = ttk.LabelFrame(content, text="", padding="10")
        self.path_group.pack(fill=tk.X, pady=(0, 8))

        path_entry = ttk.Entry(self.path_group, textvariable=self.path_var, font=("Segoe UI", 9))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.btn_file = ttk.Button(self.path_group, text="", command=self._browse_file)
        self.btn_file.pack(side=tk.LEFT, padx=(0, 4))
        self.btn_dir = ttk.Button(self.path_group, text="", command=self._browse_dir)
        self.btn_dir.pack(side=tk.LEFT)

        # Options Group
        self.opts_group = ttk.LabelFrame(content, text="", padding="10")
        self.opts_group.pack(fill=tk.X, pady=(0, 8))

        # Mode Selection
        mode_frame = ttk.Frame(self.opts_group)
        mode_frame.pack(fill=tk.X, pady=(0, 8))
        self.mode_lbl = ttk.Label(mode_frame, text="", font=("Segoe UI", 9, "bold"))
        self.mode_lbl.pack(side=tk.LEFT, padx=(0, 10))

        self.r0 = ttk.Radiobutton(mode_frame, text="", variable=self.mode_var, value="auto")
        self.r0.pack(side=tk.LEFT, padx=(0, 8))
        self.r1 = ttk.Radiobutton(mode_frame, text="", variable=self.mode_var, value="1bit")
        self.r1.pack(side=tk.LEFT, padx=(0, 8))
        self.r2 = ttk.Radiobutton(mode_frame, text="", variable=self.mode_var, value="color")
        self.r2.pack(side=tk.LEFT, padx=(0, 8))
        self.r3 = ttk.Radiobutton(mode_frame, text="", variable=self.mode_var, value="grayscale")
        self.r3.pack(side=tk.LEFT, padx=(0, 8))
        self.r4 = ttk.Radiobutton(mode_frame, text="", variable=self.mode_var, value="text")
        self.r4.pack(side=tk.LEFT)

        # Checkboxes
        chk_frame = ttk.Frame(self.opts_group)
        chk_frame.pack(fill=tk.X)
        self.c1 = ttk.Checkbutton(chk_frame, text="", variable=self.fix_cover_var)
        self.c1.pack(side=tk.LEFT, padx=(0, 15))
        self.c2 = ttk.Checkbutton(chk_frame, text="", variable=self.clean_art_var)
        self.c2.pack(side=tk.LEFT)

        # Calibre Engine Status & Settings Frame
        self.calibre_group = ttk.LabelFrame(content, text="", padding="8")
        self.calibre_group.pack(fill=tk.X, pady=(0, 8))

        self.calibre_status_lbl = ttk.Label(self.calibre_group, text="", font=("Segoe UI", 8))
        self.calibre_status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.btn_calibre = ttk.Button(self.calibre_group, text="", command=self._browse_calibre)
        self.btn_calibre.pack(side=tk.RIGHT)

        # Action Button & Progress Bar — placed ABOVE log so always visible
        run_frame = ttk.Frame(content)
        run_frame.pack(fill=tk.X, pady=(0, 6))

        self.btn_run = ttk.Button(run_frame, text="", command=self._start_processing)
        self.btn_run.pack(fill=tk.X, ipady=5)

        self.progress = ttk.Progressbar(run_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(4, 0))

        self.progress_lbl = ttk.Label(run_frame, text="", font=("Segoe UI", 8), foreground="#555555")
        self.progress_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Log Text Box
        self.log_group = ttk.LabelFrame(content, text="", padding="5")
        self.log_group.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.log_text = tk.Text(self.log_group, wrap=tk.WORD, font=("Consolas", 8), bg="#1E1E1E", fg="#D4D4D4")
        scrollbar = ttk.Scrollbar(self.log_group, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


    def _on_lang_changed(self, event=None):
        selected = self.lang_combo.get()
        new_lang = "vi" if selected == "Tiếng Việt" else "en"
        self.apply_language(new_lang)

    def _update_calibre_status(self):
        t = TEXTS[self.lang]
        calibre_bin = get_calibre_path(self.custom_calibre_path)
        if calibre_bin and os.path.exists(calibre_bin):
            self.calibre_status_lbl.config(text=t['calibre_detected'].format(path=calibre_bin), foreground="#2E7D32")
        else:
            self.calibre_status_lbl.config(text=t['calibre_not_found'], foreground="#E65100")

    def _browse_calibre(self):
        t = TEXTS[self.lang]
        f = filedialog.askopenfilename(
            title=t['calibre_dialog_title'],
            filetypes=[("Calibre Executable", "ebook-convert.exe ebook-convert"), ("All files", "*.*")]
        )
        if f:
            self.custom_calibre_path = f
            self._save_config()
            self._update_calibre_status()

    def apply_language(self, lang):
        self.lang = lang
        t = TEXTS[lang]

        self.title(t['app_title'])
        self.title_lbl.config(text=t['title'])
        self.subtitle_lbl.config(text=t['subtitle'])
        self.lang_lbl.config(text=t['lang_label'])

        self.path_group.config(text=t['path_group'])
        self.btn_file.config(text=t['btn_file'])
        self.btn_dir.config(text=t['btn_dir'])

        self.opts_group.config(text=t['opts_group'])
        self.mode_lbl.config(text=t['mode_label'])
        self.r0.config(text=t['mode_auto'])
        self.r1.config(text=t['mode_1bit'])
        self.r2.config(text=t['mode_color'])
        self.r3.config(text=t['mode_gray'])
        self.r4.config(text=t['mode_text'])

        self.c1.config(text=t['chk_cover'])
        self.c2.config(text=t['chk_clean'])

        self.calibre_group.config(text=t['calibre_group'])
        self.btn_calibre.config(text=t['btn_calibre_browse'])
        self._update_calibre_status()

        self.log_group.config(text=t['log_group'])
        if not self.is_processing:
            self.btn_run.config(text=t['btn_run'])
        else:
            self.btn_run.config(text=t['btn_running'])

    def _browse_file(self):
        t = TEXTS[self.lang]
        f = filedialog.askopenfilename(
            title=t['file_dialog_title'],
            filetypes=[("Ebooks & Documents", "*.pdf *.mobi *.prc *.azw *.azw3 *.docx *.doc *.fb2"), ("All files", "*.*")]
        )
        if f:
            self.path_var.set(f)

    def _browse_dir(self):
        t = TEXTS[self.lang]
        d = filedialog.askdirectory(title=t['dir_dialog_title'])
        if d:
            self.path_var.set(d)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def _start_processing(self):
        t = TEXTS[self.lang]
        target = self.path_var.get().strip()
        if not target or not os.path.exists(target):
            messagebox.showwarning(t['warn_title'], t['warn_path'])
            return

        if self.is_processing:
            return

        self.is_processing = True
        self.btn_run.config(state=tk.DISABLED, text=t['btn_running'])
        self.progress['value'] = 0
        self.progress_lbl.config(text="")
        self.log_text.delete(1.0, tk.END)
        self.log(t['log_start'].format(path=target))

        threading.Thread(target=self._run_worker, args=(target,), daemon=True).start()

    def _run_worker(self, target):
        t = TEXTS[self.lang]
        try:
            mode = self.mode_var.get()
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

            self.log(t['log_found'].format(count=len(files)))

            for i, f in enumerate(files, 1):
                fn = os.path.basename(f)
                ext = os.path.splitext(fn)[1].lower()
                self.log(t['log_proc'].format(i=i, total=len(files), fn=fn))

                if ext == '.epub':
                    if clean_art:
                        ok, msg = clean_epub_artifacts(f)
                        if ok:
                            self.log(t['log_clean'].format(msg=msg))
                    if fix_cov:
                        ok, desc = fix_epub_cover(f)
                        if ok:
                            self.log(t['log_cover'].format(desc=desc))
                elif ext == '.pdf':
                    effective_mode = mode
                    if mode == 'auto':
                        if is_digital_text_pdf(f):
                            effective_mode = 'text'
                            self.log(t['log_auto_text'])
                        else:
                            effective_mode = '1bit'
                            self.log(t['log_auto_scan'])

                    def page_cb(cur, total):
                        pct = int(cur / total * 100) if total else 0
                        self.progress['value'] = pct
                        self.progress_lbl.config(text=f"Trang {cur}/{total} ({pct}%)" if self.lang == 'vi' else f"Page {cur}/{total} ({pct}%)")
                        self.update_idletasks()

                    ok, res = convert_scanned_pdf_to_epub(f, mode=effective_mode, progress_callback=page_cb)
                    status_str = t['status_ok'] if ok else t['status_fail']
                    self.log(t['log_result'].format(status=status_str, res=res))
                    if effective_mode == 'text' and ok:
                        try:
                            ok_txt, txt_res = export_pdf_to_txt(f)
                            if ok_txt:
                                self.log(t['log_txt'].format(txt_fn=os.path.basename(txt_res)))
                        except Exception:
                            pass
                else:
                    ok, res = convert_document_to_epub(f, auto_fix_cover=fix_cov)
                    status_str = t['status_ok'] if ok else t['status_fail']
                    self.log(t['log_result'].format(status=status_str, res=os.path.basename(res) if ok else res))
                    if ok and clean_art:
                        clean_epub_artifacts(res)

            self.log(t['log_done'])
            messagebox.showinfo(t['success_title'], t['success_msg'].format(count=len(files)))
        except Exception as e:
            self.log(f"\n[ERROR]: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.is_processing = False
            self.progress.stop()
            self.btn_run.config(state=tk.NORMAL, text=t['btn_run'])


if __name__ == "__main__":
    app = EbookConverterApp()
    app.mainloop()
