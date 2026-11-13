"""Halaman Hitung SPK via Excel (port dari hitung.php + download-template.php)."""
import os
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from lib import xlsx_reader
from lib.saw import SAW, default_criteria
from . import theme as T

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "template", "Template_SPK_PIP.xlsx")


class HitungPage(T.ScrollFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.school = tk.StringVar()
        self.operator = tk.StringVar()
        self.quota = tk.StringVar(value="0")
        self.file_path = None
        self.file_label = tk.StringVar(value="Belum ada file dipilih")
        self.pad = tk.Frame(self.body, bg=T.BG)
        self.pad.pack(fill="both", expand=True, padx=28, pady=20)
        self.show_form()

    def on_show(self, **_):
        pass

    def _clear(self):
        for w in self.pad.winfo_children():
            w.destroy()
        self.to_top()

    def _header_and_steps(self, processed):
        T.page_header(self.pad, "Hitung SPK via Excel",
                      "Unduh templat, isi data siswa, unggah kembali, lalu generate laporan PDF "
                      "secara otomatis.").pack(fill="x")
        steps = tk.Frame(self.pad, bg=T.BG)
        steps.pack(fill="x", pady=(14, 18))
        labels = [("✓" if processed else "1", "Unduh Templat", not processed),
                  ("2", "Isi & Unggah", False),
                  ("3", "Generate PDF", processed)]
        for num, text, active in labels:
            done = processed and num == "✓"
            bg = T.SUCCESS if done else (T.NAVY if active else T.BORDER)
            fg = "white" if (done or active) else T.MUTED
            tk.Label(steps, text=num, bg=bg, fg=fg, font=T.FONT_B, width=3).pack(side="left")
            tk.Label(steps, text=text, bg=T.BG, fg=T.NAVY if active else T.MUTED, font=T.FONT_B
                     ).pack(side="left", padx=(6, 24))

    # ── Form ────────────────────────────────────────────────────────────────
    def show_form(self, errors=None):
        self._clear()
        self._header_and_steps(False)

        if errors:
            T.alert(self.pad, "danger", "Terjadi kesalahan:\n" + "\n".join("• " + e for e in errors)
                    ).pack(fill="x", pady=(0, 14))

        cols = tk.Frame(self.pad, bg=T.BG)
        cols.pack(fill="x")
        cols.grid_columnconfigure(0, weight=1, uniform="c")
        cols.grid_columnconfigure(1, weight=1, uniform="c")

        # Langkah 1
        o1, b1, _ = T.card(cols, "Langkah 1 — Unduh Templat")
        o1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(b1, bg=T.CARD, fg=T.MUTED, justify="left", anchor="w", wraplength=380,
                 text="Unduh file Excel di bawah ini. Templat sudah berisi header kolom dan dropdown "
                      "untuk tiap kriteria. Isi dengan data siswa sebenarnya.").pack(fill="x", pady=(0, 10))
        T.alert(b1, "info", "Isi nilai 1–5 untuk setiap kriteria mengacu pada tabel skala di halaman Beranda.",
                wrap=360).pack(fill="x", pady=(0, 10))
        T.button(b1, "Unduh Template_SPK_PIP.xlsx", self.download_template).pack(fill="x")
        box = tk.Frame(b1, bg="#f8fafc")
        box.pack(fill="x", pady=(12, 0))
        tk.Label(box, bg="#f8fafc", justify="left", anchor="w", font=T.FONT_SM, wraplength=380,
                 text="Format kolom:\nA: Nama Siswa | B: Kelas | C: C1 | D: C2 | E: C3 | F: C4 | G: C5"
                 ).pack(fill="x", padx=10, pady=8)

        # Langkah 2
        o2, b2, _ = T.card(cols, "Langkah 2 — Unggah & Hitung")
        o2.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        T.labeled_entry(b2, "Nama Sekolah *", self.school).pack(fill="x", pady=4)
        T.labeled_entry(b2, "Nama Operator *", self.operator).pack(fill="x", pady=4)
        T.labeled_entry(b2, "Kuota PIP Tahun Ini", self.quota,
                        hint="Isi untuk menandai siswa yang masuk rekomendasi sesuai kuota (0 = tampilkan semua)."
                        ).pack(fill="x", pady=4)
        tk.Label(b2, text="Unggah File Excel *", font=T.FONT_B, bg=T.CARD, anchor="w").pack(fill="x", pady=(6, 2))
        zone = tk.Frame(b2, bg="#f8fafc", highlightbackground=T.BORDER, highlightthickness=2, cursor="hand2")
        zone.pack(fill="x")
        tk.Label(zone, text="Klik untuk memilih file .xlsx", font=T.FONT_B, fg=T.NAVY, bg="#f8fafc"
                 ).pack(pady=(12, 0))
        tk.Label(zone, text="Format: .xlsx — Maks 5 MB", font=T.FONT_SM, fg=T.MUTED, bg="#f8fafc").pack()
        tk.Label(zone, textvariable=self.file_label, font=T.FONT_SM, fg=T.SUCCESS if self.file_path else T.MUTED,
                 bg="#f8fafc").pack(pady=(0, 12))
        for w in [zone] + zone.winfo_children():
            w.bind("<Button-1>", lambda e: self.pick_file())
        T.button(b2, "⚡ Hitung SPK Sekarang", self.calculate).pack(fill="x", pady=(12, 0))

    def pick_file(self):
        path = filedialog.askopenfilename(title="Pilih file Excel", filetypes=[("Excel", "*.xlsx")])
        if path:
            self.file_path = path
            self.file_label.set("✓ File dipilih: " + os.path.basename(path))

    def download_template(self):
        if not os.path.exists(TEMPLATE_PATH):
            messagebox.showerror("Template tidak ditemukan",
                                 "File template/Template_SPK_PIP.xlsx tidak ada di folder aplikasi.")
            return
        dest = filedialog.asksaveasfilename(title="Simpan template", defaultextension=".xlsx",
                                            initialfile="Template_SPK_PIP.xlsx",
                                            filetypes=[("Excel", "*.xlsx")])
        if dest:
            shutil.copyfile(TEMPLATE_PATH, dest)
            messagebox.showinfo("Berhasil", "Template disimpan di:\n" + dest)

    # ── Hitung ──────────────────────────────────────────────────────────────
    def calculate(self):
        school, operator = self.school.get().strip(), self.operator.get().strip()
        try:
            quota = int(self.quota.get().strip() or 0)
        except ValueError:
            quota = 0
        errors = []
        if not school:
            errors.append("Nama sekolah tidak boleh kosong.")
        if not operator:
            errors.append("Nama operator tidak boleh kosong.")
        if not self.file_path:
            errors.append("File Excel belum diunggah.")
        elif not self.file_path.lower().endswith(".xlsx"):
            errors.append("Format file harus .xlsx (Excel).")

        criteria = default_criteria()
        results = []
        if not errors:
            try:
                rows = xlsx_reader.read(self.file_path)
                students = xlsx_reader.parse_students(rows, len(criteria))
                if not students:
                    errors.append("Tidak ada data siswa di dalam file. Pastikan menggunakan templat yang benar.")
                else:
                    saw = SAW()
                    saw.set_criteria(criteria)
                    saw.set_students(students)
                    results = saw.calculate()
                    self.app.state.update(results=results, criteria=criteria, school=school,
                                          operator=operator, quota=quota)
            except Exception as e:  # noqa: BLE001
                errors.append("Gagal membaca file: " + str(e))

        if errors:
            self.show_form(errors)
        else:
            self.show_result(results, criteria, school, operator, quota)

    # ── Hasil ───────────────────────────────────────────────────────────────
    def show_result(self, results, criteria, school, operator, quota):
        self._clear()
        self._header_and_steps(True)
        T.alert(self.pad, "success",
                f"Perhitungan selesai! Data {len(results)} siswa berhasil diproses. "
                "Klik tombol di bawah untuk menyimpan laporan PDF.").pack(fill="x", pady=(0, 12))

        if quota > 0:
            q = tk.Frame(self.pad, bg=T.BG)
            q.pack(fill="x", pady=(0, 10))
            tk.Label(q, text=f"Kuota PIP: {quota}   —   Siswa peringkat 1–{quota} ditandai Direkomendasikan",
                     bg=T.BG, fg=T.SUCCESS, font=T.FONT_B).pack(side="left")

        outer, body, head = T.card(self.pad, "Hasil Perankingan SAW")
        outer.pack(fill="x")
        right = tk.Frame(head, bg=T.CARD)
        right.pack(side="right")
        T.button(right, "Hitung Ulang", self.show_form, "secondary").pack(side="right", padx=(8, 0))
        T.button(right, "Download Laporan PDF", self.app.save_pdf).pack(side="right")

        wrap, _ = T.result_table(body, criteria, results, quota, height=14)
        wrap.pack(fill="both", expand=True)
        tk.Label(body, bg=T.CARD, fg=T.MUTED, font=T.FONT_SM, anchor="w", justify="left", wraplength=900,
                 text=f"Dihitung pada: {datetime.now().strftime('%d %B %Y, %H:%M:%S')} WIB  ·  "
                      f"Operator: {operator}  ·  Sekolah: {school}").pack(fill="x", pady=(10, 0))
