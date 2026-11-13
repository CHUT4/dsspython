"""SPK PIP — Sistem Penunjang Keputusan Penerima Program Indonesia Pintar
SMK Kesehatan Sekawan | Metode: Hybrid AHP-SAW

Aplikasi desktop (Python + Tkinter). Tanpa database, tanpa library tambahan.
Jalankan:  python main.py
"""
import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from lib.pdf_report import SpkPdf  # noqa: E402
from ui import theme as T  # noqa: E402
from ui.ahp import AhpPage  # noqa: E402
from ui.beranda import BerandaPage  # noqa: E402
from ui.custom import CustomPage  # noqa: E402
from ui.hitung import HitungPage  # noqa: E402

PAGES = [
    ("beranda", "Beranda"),
    ("ahp", "Kalkulator AHP"),
    ("hitung", "Hitung SAW"),
    ("custom", "Custom SPK"),
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SPK PIP — SMK Kesehatan Sekawan")
        self.geometry("1240x780")
        self.minsize(980, 620)
        T.setup_style(self)

        # State sesi (hanya di memori — stateless, tidak ada database)
        self.state = {}

        self._build_navbar()
        self.container = tk.Frame(self, bg=T.BG)
        self.container.pack(fill="both", expand=True)
        self._build_footer()

        self.pages = {
            "beranda": BerandaPage(self.container, self),
            "ahp": AhpPage(self.container, self),
            "hitung": HitungPage(self.container, self),
            "custom": CustomPage(self.container, self),
        }
        self.current = None
        self.show("beranda")

    # ── Layout ──────────────────────────────────────────────────────────────
    def _build_navbar(self):
        bar = tk.Frame(self, bg=T.NAVY, height=64)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        brand = tk.Frame(bar, bg=T.NAVY, cursor="hand2")
        brand.pack(side="left", padx=20)
        self._logo = None
        try:  # logo opsional (butuh Pillow); kalau tidak ada, dilewati saja
            from PIL import Image, ImageTk
            img = Image.open(os.path.join(BASE_DIR, "assets", "images", "logo-smk.jpg")).resize((40, 40))
            self._logo = ImageTk.PhotoImage(img)
            tk.Label(brand, image=self._logo, bg=T.NAVY).pack(side="left", padx=(0, 10))
        except Exception:  # noqa: BLE001
            pass
        txt = tk.Frame(brand, bg=T.NAVY)
        txt.pack(side="left")
        tk.Label(txt, text="SMK Kesehatan Sekawan", font=("Segoe UI", 11, "bold"), fg="white", bg=T.NAVY).pack(anchor="w")
        tk.Label(txt, text="Sistem Penunjang Keputusan PIP", font=("Segoe UI", 8), fg="#a9bcd6", bg=T.NAVY).pack(anchor="w")
        for w in [brand] + brand.winfo_children() + txt.winfo_children():
            w.bind("<Button-1>", lambda e: self.show("beranda"))

        links = tk.Frame(bar, bg=T.NAVY)
        links.pack(side="left", padx=30)
        self.nav_btns = {}
        for key, label in PAGES:
            b = tk.Label(links, text=label, font=("Segoe UI", 10, "bold"), fg="#c9d6e8", bg=T.NAVY,
                         padx=14, pady=8, cursor="hand2")
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda e, k=key: self.show(k))
            self.nav_btns[key] = b

    def _build_footer(self):
        f = tk.Frame(self, bg=T.NAVY_DARK)
        f.pack(fill="x", side="bottom")
        tk.Label(f, text="SPK Penerima PIP — SMK Kesehatan Sekawan", fg="white", bg=T.NAVY_DARK,
                 font=("Segoe UI", 9, "bold")).pack(pady=(6, 0))
        tk.Label(f, text="Metode Simple Additive Weighting (SAW) · Sistem Penunjang Keputusan",
                 fg="#8aa0bf", bg=T.NAVY_DARK, font=("Segoe UI", 8)).pack(pady=(0, 6))

    # ── Navigasi ────────────────────────────────────────────────────────────
    def show(self, key, **kw):
        if self.current:
            self.pages[self.current].pack_forget()
        self.current = key
        page = self.pages[key]
        page.pack(fill="both", expand=True)
        for k, b in self.nav_btns.items():
            b.config(bg=T.NAVY_MID if k == key else T.NAVY, fg="white" if k == key else "#c9d6e8")
        page.on_show(**kw)

    def warn(self, msg):
        messagebox.showwarning("Perhatian", msg)

    # ── Output PDF ──────────────────────────────────────────────────────────
    def save_pdf(self):
        st = self.state
        if not st.get("results"):
            messagebox.showwarning("Belum ada hasil", "Hitung dulu di halaman Hitung SAW atau Custom SPK.")
            self.show("hitung")
            return
        default = "SPK_PIP_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"
        path = filedialog.asksaveasfilename(title="Simpan Laporan PDF", defaultextension=".pdf",
                                            initialfile=default, filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            SpkPdf(st.get("school") or "SMK Kesehatan Sekawan", st.get("operator") or "-",
                   st["criteria"], st["results"], int(st.get("quota") or 0)).save(path)
        except OSError as e:
            messagebox.showerror("Gagal menyimpan", str(e))
            return
        if messagebox.askyesno("Laporan PDF tersimpan", f"Tersimpan di:\n{path}\n\nBuka file sekarang?"):
            self._open_file(path)

    @staticmethod
    def _open_file(path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    App().mainloop()
