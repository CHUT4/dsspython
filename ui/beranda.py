"""Halaman Beranda (port dari index.php)."""
import tkinter as tk
from tkinter import ttk

from lib.saw import default_criteria
from . import theme as T


class BerandaPage(T.ScrollFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        b = self.body
        pad = tk.Frame(b, bg=T.BG)
        pad.pack(fill="both", expand=True, padx=28, pady=20)

        # Hero
        hero = tk.Frame(pad, bg=T.NAVY)
        hero.pack(fill="x")
        tk.Label(hero, text="Sistem Penunjang Keputusan\nPenerima PIP", font=("Segoe UI", 22, "bold"),
                 fg="white", bg=T.NAVY, justify="left", anchor="w").pack(fill="x", padx=28, pady=(22, 6))
        tk.Label(hero, justify="left", anchor="w", wraplength=900, fg="#dbe7f5", bg=T.NAVY, font=T.FONT,
                 text="Sistem ini membantu proses seleksi calon penerima Program Indonesia Pintar (PIP) secara "
                      "objektif dan terukur menggunakan metode Simple Additive Weighting (SAW). Perankingan "
                      "didasarkan pada lima kriteria sosial-ekonomi siswa yang telah divalidasi oleh kepala sekolah."
                 ).pack(fill="x", padx=28)
        badges = tk.Frame(hero, bg=T.NAVY)
        badges.pack(fill="x", padx=28, pady=(12, 22))
        for t in ["Metode SAW", "5 Kriteria", "Stateless", "Laporan PDF"]:
            tk.Label(badges, text=t, fg="white", bg=T.NAVY_MID, font=T.FONT_SM, padx=10, pady=3
                     ).pack(side="left", padx=(0, 8))

        T.alert(pad, "info",
                "Cara Penggunaan Singkat: Pilih Kalkulator AHP untuk menghitung bobot kriteria secara otomatis "
                "menggunakan metode AHP, lalu hasil bobotnya bisa langsung dipakai di Custom SPK untuk input "
                "manual dengan kriteria fleksibel. Atau pilih Hitung SAW untuk mengunggah data siswa via Excel "
                "menggunakan bobot default yang telah ditetapkan."
                ).pack(fill="x", pady=(14, 14))

        T.page_header(pad, "Kriteria Penilaian SAW",
                      "Lima kriteria di bawah ini ditetapkan berdasarkan pedoman PIP Kemendikdasmen "
                      "dan disahkan oleh kepala sekolah.").pack(fill="x", pady=(0, 10))

        grid = tk.Frame(pad, bg=T.BG)
        grid.pack(fill="x")
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1, uniform="crit")
        for idx, c in enumerate(default_criteria()):
            self._criteria_card(grid, c).grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=6, pady=6)

        # Formula
        outer, body, _ = T.card(pad, "Formula Perhitungan SAW")
        outer.pack(fill="x", pady=(10, 0))
        row = tk.Frame(body, bg=T.CARD)
        row.pack(fill="x")
        row.grid_columnconfigure(0, weight=1, uniform="f")
        row.grid_columnconfigure(1, weight=1, uniform="f")
        self._formula(row, 0, "1. Normalisasi Matrix",
                      ["Benefit:  rij = xij / max(xj)", "Cost:       rij = min(xj) / xij"])
        self._formula(row, 1, "2. Nilai Preferensi (Vi)",
                      ["Vi = Σ (wj × rij)", "wj = bobot kriteria ke-j"])
        tk.Label(body, bg=T.CARD, fg=T.MUTED, font=T.FONT_SM, justify="left", anchor="w", wraplength=900,
                 text="Siswa dengan nilai Vi tertinggi ditempatkan di peringkat teratas dan direkomendasikan "
                      "sebagai penerima PIP sesuai kuota yang berlaku.").pack(fill="x", pady=(12, 0))

    @staticmethod
    def _formula(parent, col, title, lines):
        f = tk.Frame(parent, bg=T.CARD)
        f.grid(row=0, column=col, sticky="nsew", padx=6)
        tk.Label(f, text=title, font=T.FONT_B, fg=T.NAVY, bg=T.CARD, anchor="w").pack(fill="x", pady=(0, 6))
        box = tk.Frame(f, bg=T.SOFT)
        box.pack(fill="x")
        for ln in lines:
            tk.Label(box, text=ln, font=T.FONT_MONO, bg=T.SOFT, anchor="w", justify="left"
                     ).pack(fill="x", padx=14, pady=4)

    @staticmethod
    def _criteria_card(parent, c):
        f = tk.Frame(parent, bg=T.CARD, highlightbackground=T.BORDER, highlightthickness=1)
        head = tk.Frame(f, bg=T.NAVY)
        head.pack(fill="x")
        tk.Label(head, text=c["code"], font=T.FONT_B, fg="white", bg=T.NAVY_MID, padx=8, pady=3
                 ).pack(side="left", padx=10, pady=8)
        info = tk.Frame(head, bg=T.NAVY)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=c["name"], font=T.FONT_B, fg="white", bg=T.NAVY, anchor="w",
                 wraplength=200, justify="left").pack(fill="x")
        is_cost = c["type"] == "cost"
        tk.Label(info, text="Cost ↓" if is_cost else "Benefit ↑", font=T.FONT_SM,
                 fg="#c53030" if is_cost else "#276749", bg="#fed7d7" if is_cost else "#c6f6d5",
                 padx=6).pack(anchor="w", pady=(2, 6))

        body = tk.Frame(f, bg=T.CARD)
        body.pack(fill="both", expand=True, padx=10, pady=8)
        for num, desc in c["scale"].items():
            r = tk.Frame(body, bg=T.CARD)
            r.pack(fill="x", pady=1)
            tk.Label(r, text=num, font=T.FONT_B, fg=T.NAVY, bg=T.SOFT, width=2).pack(side="left", anchor="n")
            tk.Label(r, text=desc, font=T.FONT_SM, bg=T.CARD, anchor="w", justify="left", wraplength=200
                     ).pack(side="left", padx=6)

        wrap = tk.Frame(f, bg=T.CARD)
        wrap.pack(fill="x", padx=10, pady=(0, 10))
        pct = round(c["weight"] * 100)
        lab = tk.Frame(wrap, bg=T.CARD)
        lab.pack(fill="x")
        tk.Label(lab, text="Bobot Kriteria", font=T.FONT_SM, fg=T.MUTED, bg=T.CARD).pack(side="left")
        tk.Label(lab, text=f"{c['weight']:.2f} ({pct}%)", font=T.FONT_SM, fg=T.NAVY, bg=T.CARD
                 ).pack(side="right")
        ttk.Progressbar(wrap, style="Bar.Horizontal.TProgressbar", maximum=100,
                        value=min(100, pct * 2.86)).pack(fill="x", pady=(2, 0))
        return f
