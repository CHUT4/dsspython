"""Halaman Kalkulator Bobot AHP (port dari ahp.php)."""
import tkinter as tk
from tkinter import ttk

from lib.saw import default_criteria
from . import theme as T

TYPE_LABEL = {"cost": "Cost ↓", "benefit": "Benefit ↑"}
TYPE_VALUE = {v: k for k, v in TYPE_LABEL.items()}
RI_TABLE = [0, 0, 0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]

SAATY = [
    (1, "Sama pentingnya", "Kedua elemen memberikan kontribusi yang sama"),
    (2, "Nilai antara 1 dan 3", "—"),
    (3, "Sedikit lebih penting", "Pengalaman dan penilaian sedikit mendukung satu elemen"),
    (4, "Nilai antara 3 dan 5", "—"),
    (5, "Lebih penting", "Pengalaman dan penilaian sangat mendukung satu elemen"),
    (6, "Nilai antara 5 dan 7", "—"),
    (7, "Sangat lebih penting", "Satu elemen sangat dominan dalam praktik"),
    (8, "Nilai antara 7 dan 9", "—"),
    (9, "Mutlak lebih penting", "Satu elemen terbukti mutlak lebih penting"),
]


def parse_ratio(raw):
    """Parse '3', '0.5', atau pecahan '1/3'. None bila tidak valid."""
    raw = raw.strip().replace(",", ".")
    try:
        if "/" in raw:
            a, b = raw.split("/", 1)
            val = float(a) / float(b)
        else:
            val = float(raw)
    except (ValueError, ZeroDivisionError):
        return None
    return val if val > 0 else None


def recip_text(val):
    return f"{1 / val:.3f}" if val >= 1 else f"1/{1 / val:.2f}"


def compute_ahp(criteria, raw_matrix):
    """Hitung bobot + konsistensi (sama dengan ahp.php)."""
    n = len(criteria)
    geo = []
    for i in range(n):
        prod = 1.0
        for j in range(n):
            prod *= raw_matrix[i][j]
        geo.append(prod ** (1 / n))
    sum_geo = sum(geo)

    weights = [round(g / sum_geo, 4) for g in geo]
    weights[0] = round(weights[0] + (1 - sum(weights)), 4)

    lambda_max = 0.0
    for i in range(n):
        s = sum(raw_matrix[i][j] * weights[j] for j in range(n))
        lambda_max += s / weights[i] if weights[i] > 0 else 0
    lambda_max /= n

    ci = (lambda_max - n) / (n - 1) if n > 1 else 0
    ri = RI_TABLE[n] if n < len(RI_TABLE) else 1.49
    cr = ci / ri if ri > 0 else 0

    out_criteria = []
    for i, c in enumerate(criteria):
        d = dict(c)
        d["weight"] = weights[i]
        d["code"] = f"C{i + 1}"
        out_criteria.append(d)

    return {
        "criteria": out_criteria, "matrix": raw_matrix, "weights": weights, "geo": geo,
        "lambdaMax": round(lambda_max, 4), "CI": round(ci, 4), "CR": round(cr, 4),
        "RI": round(ri, 2), "consistent": cr < 0.1, "n": n,
    }


class AhpPage(T.ScrollFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.rows = []      # tiap kriteria: {"name": StringVar, "type": StringVar, "scale": dict}
        self.cells = {}     # (i, j) -> StringVar (segitiga atas)
        self.recip = {}     # (i, j) -> Label (segitiga bawah)

        pad = tk.Frame(self.body, bg=T.BG)
        pad.pack(fill="both", expand=True, padx=28, pady=20)
        T.page_header(pad, "Kalkulator Bobot AHP",
                      "Hitung bobot kriteria menggunakan metode Analytic Hierarchy Process (AHP) dengan "
                      "perbandingan berpasangan (pairwise comparison). Hasil bobot dapat langsung digunakan "
                      "di Custom SPK.").pack(fill="x", pady=(0, 14))

        self.msg = tk.Frame(pad, bg=T.BG)
        self.msg.pack(fill="x")
        self.result_frame = tk.Frame(pad, bg=T.BG)
        self.result_frame.pack(fill="x")
        self.form_frame = tk.Frame(pad, bg=T.BG)
        self.form_frame.pack(fill="x")

        # Langkah 1 — kriteria
        o1, b1, h1 = T.card(self.form_frame, "Langkah 1 — Daftar Kriteria")
        o1.pack(fill="x", pady=(0, 12))
        T.button(h1, "+ Tambah Kriteria", self.add_crit, "secondary").pack(side="right")
        T.alert(b1, "info", "Pastikan kriteria sama dengan yang akan digunakan di Custom SPK. Nama dan jenis "
                            "(Cost/Benefit) akan ikut terbawa saat bobot dipakai di Custom SPK."
                ).pack(fill="x", pady=(0, 8))
        self.crit_list = tk.Frame(b1, bg=T.CARD)
        self.crit_list.pack(fill="x")

        # Langkah 2 — matriks
        o2, b2, _ = T.card(self.form_frame, "Langkah 2 — Matriks Perbandingan Berpasangan")
        o2.pack(fill="x", pady=(0, 12))
        T.alert(b2, "info",
                "Isi nilai perbandingan menggunakan Skala Saaty 1–9: 1 = sama penting · 3 = sedikit lebih "
                "penting · 5 = lebih penting · 7 = sangat lebih penting · 9 = mutlak lebih penting. "
                "Nilai 2, 4, 6, 8 = nilai antara. Untuk kebalikan, gunakan pecahan (misal: 1/3, 1/5)."
                ).pack(fill="x", pady=(0, 8))
        self.matrix_holder = tk.Frame(b2, bg=T.CARD)
        self.matrix_holder.pack(fill="x")

        act = tk.Frame(self.form_frame, bg=T.BG)
        act.pack(fill="x", pady=(0, 12))
        T.button(act, "Hitung Bobot AHP", self.calculate).pack(side="left")
        T.button(act, "↺ Reset", self.reset, "secondary").pack(side="left", padx=10)
        tk.Label(act, text="Data tidak disimpan ke server", fg=T.MUTED, bg=T.BG, font=T.FONT_SM).pack(side="left")

        # Referensi Saaty
        o3, b3, _ = T.card(pad, "Referensi Skala Saaty")
        o3.pack(fill="x")
        tv = ttk.Treeview(b3, columns=("v", "d", "k"), show="headings", height=len(SAATY))
        tv.heading("v", text="Nilai")
        tv.column("v", width=70, anchor="center", stretch=False)
        tv.heading("d", text="Definisi")
        tv.column("d", width=220, anchor="w", stretch=False)
        tv.heading("k", text="Keterangan")
        tv.column("k", width=520, anchor="w")
        for v, d, k in SAATY:
            tv.insert("", "end", values=(v, d, k))
        tv.pack(fill="x")

        self.reset()

    # ── Kriteria ────────────────────────────────────────────────────────────
    def _clear_msg(self):
        for w in self.msg.winfo_children():
            w.destroy()
        self.msg.configure(height=1)

    def reset(self):
        self._clear_msg()
        for w in self.result_frame.winfo_children():
            w.destroy()
        self.form_frame.pack(fill="x")
        self.rows = []
        for c in default_criteria():
            self.rows.append({"name": tk.StringVar(value=c["name"]), "type": tk.StringVar(value=TYPE_LABEL[c["type"]]),
                              "scale": dict(c["scale"])})
        self.cells = {}
        self._draw_criteria()
        self._draw_matrix()

    def _draw_criteria(self):
        for w in self.crit_list.winfo_children():
            w.destroy()
        for i, r in enumerate(self.rows):
            f = tk.Frame(self.crit_list, bg=T.CARD, highlightbackground=T.BORDER, highlightthickness=0)
            f.pack(fill="x", pady=3)
            tk.Label(f, text=f"C{i + 1}", font=T.FONT_B, bg=T.SOFT, width=5).pack(side="left", padx=(0, 8))
            e = ttk.Entry(f, textvariable=r["name"])
            e.pack(side="left", fill="x", expand=True)
            e.bind("<KeyRelease>", lambda _e: self._draw_matrix())
            cb = ttk.Combobox(f, textvariable=r["type"], values=list(TYPE_VALUE), state="readonly", width=12)
            cb.pack(side="left", padx=8)
            btn = T.button(f, "✕", lambda idx=i: self.remove_crit(idx), "danger", width=3)
            btn.pack(side="left")
            if i < 2:
                btn.state(["disabled"])

    def add_crit(self):
        n = len(self.rows) + 1
        self.rows.append({"name": tk.StringVar(), "type": tk.StringVar(value=TYPE_LABEL["cost"]),
                          "scale": {str(s): f"Nilai {s}" for s in range(1, 6)}})
        self._draw_criteria()
        self._draw_matrix()

    def remove_crit(self, idx):
        if len(self.rows) <= 2:
            return
        del self.rows[idx]
        # buang nilai matriks yang terkait kriteria ini, geser sisanya
        n_old = len(self.rows) + 1
        old = {k: v.get() for k, v in self.cells.items()}
        self.cells = {}
        keep = [k for k in range(n_old) if k != idx]
        self._saved = {(a, b): old.get((keep[a], keep[b]), "1")
                       for a in range(len(keep)) for b in range(a + 1, len(keep))}
        self._draw_criteria()
        self._draw_matrix(restore=self._saved)

    # ── Matriks ─────────────────────────────────────────────────────────────
    def _draw_matrix(self, restore=None):
        old = restore if restore is not None else {k: v.get() for k, v in self.cells.items()}
        for w in self.matrix_holder.winfo_children():
            w.destroy()
        self.cells, self.recip = {}, {}
        n = len(self.rows)
        g = tk.Frame(self.matrix_holder, bg=T.CARD)
        g.pack(anchor="w")
        tk.Label(g, text="Kriteria", font=T.FONT_B, fg="white", bg=T.NAVY, padx=8, pady=6, anchor="w",
                 width=22).grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        for j, r in enumerate(self.rows):
            tk.Label(g, text=f"C{j + 1}", font=T.FONT_B, fg="white", bg=T.NAVY, width=10, pady=6
                     ).grid(row=0, column=j + 1, sticky="nsew", padx=1, pady=1)
        for i, r in enumerate(self.rows):
            nm = r["name"].get() or f"C{i + 1}"
            tk.Label(g, text=f"C{i + 1} — {nm}"[:30], font=T.FONT_B, bg="#f8fafc", anchor="w", padx=8,
                     width=22).grid(row=i + 1, column=0, sticky="nsew", padx=1, pady=1)
            for j in range(n):
                if i == j:
                    tk.Label(g, text="1", font=T.FONT_B, fg=T.NAVY, bg=T.SOFT
                             ).grid(row=i + 1, column=j + 1, sticky="nsew", padx=1, pady=1)
                elif j > i:
                    var = tk.StringVar(value=old.get((i, j), "1"))
                    self.cells[(i, j)] = var
                    e = ttk.Entry(g, textvariable=var, width=8, justify="center")
                    e.grid(row=i + 1, column=j + 1, padx=1, pady=1)
                    var.trace_add("write", lambda *_a, a=i, b=j: self._sync(a, b))
                else:
                    lb = tk.Label(g, text="1/1", font=T.FONT_MONO, fg=T.MUTED, bg=T.CARD)
                    lb.grid(row=i + 1, column=j + 1, padx=1, pady=1)
                    self.recip[(i, j)] = lb
        for (i, j) in self.cells:
            self._sync(i, j)

    def _sync(self, i, j):
        lb = self.recip.get((j, i))
        if lb is None:
            return
        val = parse_ratio(self.cells[(i, j)].get())
        if val is None:
            lb.config(text="—", fg=T.RED)
            return
        val = max(1 / 9, min(9, val))
        lb.config(text=recip_text(val), fg=T.MUTED)

    # ── Hitung ──────────────────────────────────────────────────────────────
    def calculate(self):
        self._clear_msg()
        criteria = []
        for r in self.rows:
            nm = r["name"].get().strip()
            if not nm:
                continue
            criteria.append({"code": f"C{len(criteria) + 1}", "name": nm,
                             "type": TYPE_VALUE.get(r["type"].get(), "cost"), "scale": dict(r["scale"])})
        if len(criteria) < 2:
            T.alert(self.msg, "danger", "Kesalahan:\n• Minimal 2 kriteria diperlukan untuk perhitungan AHP."
                    ).pack(fill="x", pady=(0, 12))
            return

        # matriks mengacu ke baris yang namanya terisi
        idx_map = [k for k, r in enumerate(self.rows) if r["name"].get().strip()]
        n = len(criteria)
        raw = [[1.0] * n for _ in range(n)]
        for a in range(n):
            for b in range(a + 1, n):
                val = parse_ratio(self.cells[(idx_map[a], idx_map[b])].get())
                if val is None:
                    T.alert(self.msg, "danger",
                            f"Kesalahan:\n• Nilai perbandingan C{idx_map[a] + 1} vs C{idx_map[b] + 1} tidak valid. "
                            "Gunakan angka 1–9 atau pecahan seperti 1/3."
                            ).pack(fill="x", pady=(0, 12))
                    return
                val = max(1 / 9, min(9, val))
                raw[a][b] = val
                raw[b][a] = 1 / val

        res = compute_ahp(criteria, raw)
        self.app.state["ahp_criteria"] = res["criteria"]
        self.app.state["ahp_weights"] = res["weights"]
        self.show_results(res)

    # ── Hasil ───────────────────────────────────────────────────────────────
    def show_results(self, res):
        for w in self.result_frame.winfo_children():
            w.destroy()
        self.form_frame.pack_forget()

        if res["consistent"]:
            T.alert(self.result_frame, "success",
                    f"Matriks konsisten! Penilaian perbandingan Anda valid (CR = {res['CR']} < 0.1). "
                    "Bobot kriteria siap digunakan.").pack(fill="x", pady=(0, 12))
        else:
            T.alert(self.result_frame, "danger",
                    f"Matriks tidak konsisten (CR = {res['CR']} ≥ 0.1). Silakan periksa kembali nilai "
                    "perbandingan Anda. Disarankan untuk merevisi penilaian hingga CR < 0.1."
                    ).pack(fill="x", pady=(0, 12))

        outer, body, head = T.card(self.result_frame, "Hasil Perhitungan Bobot AHP")
        outer.pack(fill="x")
        right = tk.Frame(head, bg=T.CARD)
        right.pack(side="right")
        T.button(right, "Hitung Ulang", self.back_to_form, "secondary").pack(side="right", padx=(8, 0))
        if res["consistent"]:
            T.button(right, "Pakai Bobot Ini di Custom SPK →",
                     lambda: self.app.show("custom", from_ahp=True)).pack(side="right")

        # Tabel bobot
        cols = ("kode", "nama", "jenis", "bobot", "persen", "viz")
        tv = ttk.Treeview(body, columns=cols, show="headings", height=len(res["criteria"]) + 1)
        for c, t, w, a in [("kode", "Kode", 60, "center"), ("nama", "Nama Kriteria", 300, "w"),
                           ("jenis", "Jenis", 90, "center"), ("bobot", "Bobot (w)", 90, "center"),
                           ("persen", "Persentase", 90, "center"), ("viz", "Visualisasi", 220, "w")]:
            tv.heading(c, text=t)
            tv.column(c, width=w, anchor=a, stretch=(c == "viz"))
        for i, c in enumerate(res["criteria"]):
            w = res["weights"][i]
            tv.insert("", "end", values=(c["code"], c["name"], TYPE_LABEL[c["type"]], f"{w:.4f}",
                                         f"{w * 100:.1f}%", "█" * max(1, round(min(100, w * 300) / 5))))
        tv.insert("", "end", values=("", "Total", "", f"{sum(res['weights']):.4f}", "100%", ""))
        tv.pack(fill="x", pady=(0, 14))

        # Metrik konsistensi
        mrow = tk.Frame(body, bg=T.CARD)
        mrow.pack(fill="x", pady=(0, 14))
        metrics = [("λmax", res["lambdaMax"], "Nilai eigen terbesar matriks"),
                   ("n", res["n"], "Jumlah kriteria"),
                   ("CI", res["CI"], "Consistency Index = (λmax−n)/(n−1)"),
                   ("CR", res["CR"], "Consistency Ratio = CI/RI (harus < 0.1)")]
        for k, (label, val, desc) in enumerate(metrics):
            mrow.grid_columnconfigure(k, weight=1, uniform="m")
            m = tk.Frame(mrow, bg="#f8fafc", highlightbackground=T.BORDER, highlightthickness=1)
            m.grid(row=0, column=k, sticky="nsew", padx=4)
            tk.Label(m, text=desc, font=("Segoe UI", 8), fg=T.MUTED, bg="#f8fafc", wraplength=190
                     ).pack(padx=8, pady=(8, 2))
            tk.Label(m, text=str(val), font=("Consolas", 16, "bold"), fg=T.NAVY, bg="#f8fafc").pack()
            tk.Label(m, text=label, font=T.FONT_B, fg=T.MUTED, bg="#f8fafc").pack(pady=(0, 8))

        # Matriks berpasangan
        tk.Label(body, text="Matriks Perbandingan Berpasangan", font=T.FONT_H2, fg=T.NAVY, bg=T.CARD,
                 anchor="w").pack(fill="x", pady=(4, 6))
        n = res["n"]
        mcols = ["kr"] + [c["code"] for c in res["criteria"]] + ["geo", "w"]
        mt = ttk.Treeview(body, columns=mcols, show="headings", height=n)
        mt.heading("kr", text="Kriteria")
        mt.column("kr", width=90, anchor="w", stretch=False)
        for c in res["criteria"]:
            mt.heading(c["code"], text=c["code"])
            mt.column(c["code"], width=70, anchor="center", stretch=False)
        mt.heading("geo", text="Geo Mean")
        mt.column("geo", width=90, anchor="center", stretch=False)
        mt.heading("w", text="Bobot")
        mt.column("w", width=90, anchor="center")
        for i in range(n):
            row = [res["criteria"][i]["code"]]
            for j in range(n):
                v = res["matrix"][i][j]
                row.append(f"{v:.2f}" if v >= 1 else f"1/{1 / v:.2f}")
            row += [f"{res['geo'][i]:.4f}", f"{res['weights'][i]:.4f}"]
            mt.insert("", "end", values=row)
        mt.pack(fill="x")

        if res["consistent"]:
            T.alert(body, "info", "Bobot AHP telah disimpan ke sesi. Klik \"Pakai Bobot Ini di Custom SPK\" "
                                  "untuk langsung menggunakan bobot ini di halaman Custom SPK — nilai bobot "
                                  "akan ter-isi otomatis.").pack(fill="x", pady=(14, 0))
        self.to_top()

    def back_to_form(self):
        for w in self.result_frame.winfo_children():
            w.destroy()
        self.form_frame.pack(fill="x")
        self.to_top()

    def on_show(self, **_):
        pass
