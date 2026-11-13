"""Halaman Custom SPK — input manual & kriteria fleksibel (port dari custom.php + main.js)."""
import itertools
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from lib.saw import SAW, default_criteria
from . import theme as T

COST_LABEL = "Cost ↓ (kecil = paling butuh)"
BENEFIT_LABEL = "Benefit ↑ (besar = paling butuh)"
TYPE_TO_LABEL = {"cost": COST_LABEL, "benefit": BENEFIT_LABEL}
LABEL_TO_TYPE = {v: k for k, v in TYPE_TO_LABEL.items()}

_uid = itertools.count(1)


def short_text(s, limit=22):
    return s if len(s) <= limit else s[: limit - 2] + "…"


class CritRow:
    """Satu kriteria beserta skala 1–5."""

    def __init__(self, code="", name="", ctype="cost", weight=0.10, scale=None):
        self.uid = next(_uid)
        self.code = tk.StringVar(value=code)
        self.name = tk.StringVar(value=name)
        self.type = tk.StringVar(value=TYPE_TO_LABEL[ctype])
        self.weight = tk.StringVar(value=f"{weight:.2f}")
        scale = scale or {}
        self.scale = {s: tk.StringVar(value=scale.get(str(s), "")) for s in range(1, 6)}
        self.open = False
        self.panel = None
        self.badges = {}
        self.hint = None

    @property
    def ctype(self):
        return LABEL_TO_TYPE.get(self.type.get(), "cost")

    def option_texts(self):
        out = []
        for s in range(1, 6):
            lbl = self.scale[s].get().strip() or f"Nilai {s}"
            out.append(f"{s}. {short_text(lbl)}")
        return out

    def tooltip(self):
        lines = [self.name.get() or "(tanpa nama)",
                 ("Cost: 1=paling butuh → 5=tidak butuh" if self.ctype == "cost"
                  else "Benefit: 1=paling sedikit → 5=paling banyak")]
        for s in range(1, 6):
            v = self.scale[s].get().strip()
            if v:
                lines.append(f"{s} = {v}")
        return "\n".join(lines)


class StudRow:
    def __init__(self, name="", cls="", values=None):
        self.name = tk.StringVar(value=name)
        self.cls = tk.StringVar(value=cls)
        self.vals = {}          # uid kriteria -> int (1–5)
        self.boxes = {}         # uid kriteria -> Combobox
        self.seed = values or {}


class HScroll(tk.Frame):
    """Wadah dengan scroll horizontal (untuk tabel siswa yang lebar)."""

    def __init__(self, parent, bg=T.CARD):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, height=10)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hsb.set)
        self.canvas.pack(fill="x", expand=True)
        self.hsb.pack(fill="x")
        self.body = tk.Frame(self.canvas, bg=bg)
        self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._resize)

    def _resize(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), height=self.body.winfo_reqheight())


class CustomPage(T.ScrollFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        st = app.state
        self.school = tk.StringVar(value=st.get("school") or "SMK Kesehatan Sekawan")
        op = st.get("operator") or ""
        self.operator = tk.StringVar(value="" if op == "-" else op)
        self.quota = tk.StringVar(value=str(st.get("quota") or 0))
        self.crit_rows, self.stud_rows = [], []
        self.head_labels = {}

        pad = tk.Frame(self.body, bg=T.BG)
        pad.pack(fill="both", expand=True, padx=28, pady=20)
        T.page_header(pad, "Custom SPK",
                      "Input manual dengan kriteria dan sub-kriteria (skala 1–5) yang dapat "
                      "dikustomisasi sepenuhnya.").pack(fill="x", pady=(0, 14))

        self.msg = tk.Frame(pad, bg=T.BG)
        self.msg.pack(fill="x")
        self.result_frame = tk.Frame(pad, bg=T.BG)
        self.result_frame.pack(fill="x")
        self.form = tk.Frame(pad, bg=T.BG)
        self.form.pack(fill="x")

        # Info sekolah
        o, b, _ = T.card(self.form, "Info Sekolah & Operator")
        o.pack(fill="x", pady=(0, 12))
        r = tk.Frame(b, bg=T.CARD)
        r.pack(fill="x")
        r.grid_columnconfigure(0, weight=1)
        r.grid_columnconfigure(1, weight=1)
        T.labeled_entry(r, "Nama Sekolah", self.school).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        T.labeled_entry(r, "Nama Operator", self.operator).grid(row=0, column=1, sticky="ew", padx=(10, 0))
        T.labeled_entry(b, "Kuota PIP (0 = tampilkan semua)", self.quota, width=12).pack(anchor="w", pady=(8, 0))

        # Kriteria
        o, b, h = T.card(self.form, "Kriteria & Sub-Kriteria (Skala 1–5)")
        o.pack(fill="x", pady=(0, 12))
        right = tk.Frame(h, bg=T.CARD)
        right.pack(side="right")
        self.weight_lbl = tk.Label(right, bg=T.CARD, font=T.FONT_B)
        self.weight_lbl.pack(side="left", padx=12)
        T.button(right, "+ Tambah Kriteria", self.add_crit, "secondary").pack(side="left")
        T.alert(b, "info",
                "Cost → nilai 1 = kondisi terburuk/paling butuh, nilai 5 = terbaik  |  Benefit → nilai 1 = "
                "paling sedikit, nilai 5 = paling banyak/butuh. Klik \"Atur Skala\" untuk mengisi keterangan "
                "tiap nilai 1–5.").pack(fill="x", pady=(0, 10))
        self.crit_box = tk.Frame(b, bg=T.CARD)
        self.crit_box.pack(fill="x")

        # Data siswa
        o, b, h = T.card(self.form, "Data Siswa")
        o.pack(fill="x", pady=(0, 12))
        T.button(h, "+ Tambah Siswa", self.add_stud, "secondary").pack(side="right")
        T.alert(b, "info", "Pilih nilai 1–5 untuk setiap kriteria. Arahkan kursor ke kode kriteria pada "
                           "header kolom untuk melihat keterangan skala.").pack(fill="x", pady=(0, 10))
        self.hscroll = HScroll(b)
        self.hscroll.pack(fill="x")
        self.stud_grid = self.hscroll.body

        act = tk.Frame(self.form, bg=T.BG)
        act.pack(fill="x", pady=(0, 12))
        T.button(act, "⚡ Hitung SAW Sekarang", self.calculate).pack(side="left")
        T.button(act, "↺ Reset", self.reset, "secondary").pack(side="left", padx=10)
        tk.Label(act, text="Data tidak disimpan ke server", fg=T.MUTED, bg=T.BG, font=T.FONT_SM).pack(side="left")

        self.reset()

    # ── Inisialisasi ────────────────────────────────────────────────────────
    def _clear_msg(self):
        for w in self.msg.winfo_children():
            w.destroy()
        self.msg.configure(height=1)

    def reset(self, criteria=None):
        self._clear_msg()
        for w in self.result_frame.winfo_children():
            w.destroy()
        self.form.pack(fill="x")
        criteria = criteria or default_criteria()
        self.crit_rows = [CritRow(c["code"], c["name"], c["type"], c["weight"], c["scale"]) for c in criteria]
        for cr in self.crit_rows:
            self._watch(cr)
        self.stud_rows = [StudRow() for _ in range(3)]
        self._draw_criteria()
        self._draw_students()
        self._update_weight_hint()
        self.to_top()

    def on_show(self, from_ahp=False, **_):
        if from_ahp and self.app.state.get("ahp_criteria"):
            self.reset(self.app.state["ahp_criteria"])
            T.alert(self.msg, "success",
                    "Bobot AHP berhasil dimuat! Bobot kriteria dari hasil Kalkulator AHP telah ter-isi otomatis "
                    "di bawah. Anda bisa langsung input data siswa dan klik Hitung SAW."
                    ).pack(fill="x", pady=(0, 12))

    def _watch(self, cr):
        cr.weight.trace_add("write", lambda *_: self._update_weight_hint())
        cr.code.trace_add("write", lambda *_a, c=cr: self._sync_head(c))
        for s in range(1, 6):
            cr.scale[s].trace_add("write", lambda *_a, c=cr: self._refresh_options(c))

    # ── Kriteria ────────────────────────────────────────────────────────────
    def _draw_criteria(self):
        for w in self.crit_box.winfo_children():
            w.destroy()
        for cr in self.crit_rows:
            self._draw_crit_block(cr)

    def _draw_crit_block(self, cr):
        blk = tk.Frame(self.crit_box, bg=T.CARD, highlightbackground=T.BORDER, highlightthickness=1)
        blk.pack(fill="x", pady=5)
        main = tk.Frame(blk, bg=T.CARD)
        main.pack(fill="x", padx=12, pady=10)

        def field(label, widget_fn, **pk):
            f = tk.Frame(main, bg=T.CARD)
            f.pack(side="left", padx=(0, 10), **pk)
            tk.Label(f, text=label.upper(), font=("Segoe UI", 8, "bold"), fg=T.MUTED, bg=T.CARD, anchor="w"
                     ).pack(fill="x")
            w = widget_fn(f)
            w.pack(fill="x")
            return w

        field("Kode", lambda f: ttk.Entry(f, textvariable=cr.code, width=6, justify="center"))
        name_w = field("Nama Kriteria", lambda f: ttk.Entry(f, textvariable=cr.name, width=34))
        field("Jenis", lambda f: ttk.Combobox(f, textvariable=cr.type, values=[COST_LABEL, BENEFIT_LABEL],
                                              state="readonly", width=30))
        field("Bobot", lambda f: ttk.Entry(f, textvariable=cr.weight, width=7, justify="center"))

        btns = tk.Frame(main, bg=T.CARD)
        btns.pack(side="left", anchor="s")
        scale_btn = T.button(btns, "⊞ Atur Skala ▼", lambda: self._toggle_scale(cr, scale_btn), "secondary")
        scale_btn.pack(side="left", padx=(0, 8))
        T.button(btns, "✕", lambda: self.remove_crit(cr), "danger", width=3).pack(side="left")

        # Panel skala
        panel = tk.Frame(blk, bg="#f8faff")
        cr.panel = panel
        head = tk.Frame(panel, bg="#f8faff")
        head.pack(fill="x", padx=14, pady=(10, 6))
        tk.Label(head, text="Sub-Kriteria / Indikator Skala", font=T.FONT_B, fg=T.NAVY, bg="#f8faff").pack(side="left")
        cr.hint = tk.Label(head, font=("Segoe UI", 8, "italic"), fg=T.MUTED, bg="#f8faff")
        cr.hint.pack(side="right")
        cr.badges = {}
        for s in range(1, 6):
            row = tk.Frame(panel, bg="#f8faff")
            row.pack(fill="x", padx=14, pady=2)
            b = tk.Label(row, text=str(s), font=T.FONT_B, width=3)
            b.pack(side="left", padx=(0, 8))
            cr.badges[s] = b
            ttk.Entry(row, textvariable=cr.scale[s], width=60).pack(side="left")
        tk.Frame(panel, bg="#f8faff", height=8).pack()
        cr.type.trace_add("write", lambda *_a, c=cr: self._on_type_change(c))
        self._on_type_change(cr)
        if cr.open:
            panel.pack(fill="x")
            scale_btn.config(text="⊞ Atur Skala ▲")

    def _on_type_change(self, cr):
        if cr.hint is None or not cr.hint.winfo_exists():
            return
        is_cost = cr.ctype == "cost"
        cr.hint.config(text="⬇ Cost: nilai 1 = kondisi terburuk → skor tertinggi dalam SAW" if is_cost
                       else "⬆ Benefit: nilai 5 = kondisi terbaik → skor tertinggi dalam SAW")
        worst, best, mid = ("#fed7d7", "#c53030"), ("#c6f6d5", "#276749"), ("#e2e8f0", "#4a5568")
        for s, b in cr.badges.items():
            if not b.winfo_exists():
                continue
            if is_cost:
                bg, fg = worst if s == 1 else best if s == 5 else mid
            else:
                bg, fg = worst if s == 5 else best if s == 1 else mid
            b.config(bg=bg, fg=fg)
        self._refresh_options(cr)

    def _toggle_scale(self, cr, btn):
        cr.open = not cr.open
        if cr.open:
            cr.panel.pack(fill="x")
            btn.config(text="⊞ Atur Skala ▲")
        else:
            cr.panel.pack_forget()
            btn.config(text="⊞ Atur Skala ▼")

    def add_crit(self):
        cr = CritRow(f"C{len(self.crit_rows) + 1}", "", "cost", 0.10)
        cr.open = True
        self._watch(cr)
        self.crit_rows.append(cr)
        for s in self.stud_rows:
            s.vals[cr.uid] = 1
        self._draw_criteria()
        self._draw_students()
        self._update_weight_hint()

    def remove_crit(self, cr):
        if len(self.crit_rows) <= 1:
            self.app.warn("Minimal 1 kriteria diperlukan.")
            return
        self._snapshot_students()
        self.crit_rows.remove(cr)
        for s in self.stud_rows:
            s.vals.pop(cr.uid, None)
        self._draw_criteria()
        self._draw_students()
        self._update_weight_hint()

    def _update_weight_hint(self):
        total = 0.0
        for cr in self.crit_rows:
            try:
                total += float(cr.weight.get())
            except ValueError:
                pass
        ok = abs(total - 1) < 0.005
        self.weight_lbl.config(text=f"Total bobot: {total:.2f} {'✓' if ok else '⚠ idealnya = 1.00'}",
                               fg=T.SUCCESS if ok else T.RED)

    # ── Siswa ───────────────────────────────────────────────────────────────
    def _snapshot_students(self):
        for s in self.stud_rows:
            for uid, cb in s.boxes.items():
                try:
                    if cb.winfo_exists():
                        s.vals[uid] = max(1, cb.current() + 1)
                except tk.TclError:
                    pass

    def _draw_students(self):
        self._snapshot_students()
        for w in self.stud_grid.winfo_children():
            w.destroy()
        self.head_labels = {}
        g = self.stud_grid

        def hdr(text, col, anchor="center", width=None):
            lb = tk.Label(g, text=text, font=T.FONT_B, fg="white", bg=T.NAVY, anchor=anchor, pady=7, padx=6,
                          **({"width": width} if width else {}))
            lb.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            return lb

        hdr("#", 0, width=4)
        hdr("Nama Siswa", 1, "w", 24)
        hdr("Kelas", 2, width=10)
        for j, cr in enumerate(self.crit_rows):
            lb = hdr(cr.code.get(), 3 + j, width=20)
            lb.config(cursor="question_arrow")
            Tooltip_ = T.Tooltip(lb, cr.tooltip)  # noqa: F841
            self.head_labels[cr.uid] = lb
        hdr("Hapus", 3 + len(self.crit_rows), width=6)

        for i, s in enumerate(self.stud_rows):
            s.boxes = {}
            tk.Label(g, text=str(i + 1), bg=T.CARD, fg=T.MUTED).grid(row=i + 1, column=0, padx=1, pady=2)
            ttk.Entry(g, textvariable=s.name, width=26).grid(row=i + 1, column=1, padx=1, pady=2, sticky="ew")
            ttk.Entry(g, textvariable=s.cls, width=10).grid(row=i + 1, column=2, padx=1, pady=2)
            for j, cr in enumerate(self.crit_rows):
                v = s.vals.get(cr.uid, 1)
                s.vals[cr.uid] = v
                cb = ttk.Combobox(g, values=cr.option_texts(), state="readonly", width=22)
                cb.current(v - 1)
                cb.grid(row=i + 1, column=3 + j, padx=1, pady=2)
                cb.bind("<<ComboboxSelected>>", lambda e, st=s, uid=cr.uid: st.vals.__setitem__(
                    uid, e.widget.current() + 1))
                s.boxes[cr.uid] = cb
            T.button(g, "✕", lambda st=s: self.remove_stud(st), "danger", width=3
                     ).grid(row=i + 1, column=3 + len(self.crit_rows), padx=4, pady=2)

    def _sync_head(self, cr):
        lb = self.head_labels.get(cr.uid)
        if lb is not None and lb.winfo_exists():
            lb.config(text=cr.code.get())

    def _refresh_options(self, cr):
        texts = cr.option_texts()
        for s in self.stud_rows:
            cb = s.boxes.get(cr.uid)
            if cb is not None and cb.winfo_exists():
                cur = cb.current()
                cb.config(values=texts)
                cb.current(max(cur, 0))

    def add_stud(self):
        self._snapshot_students()
        self.stud_rows.append(StudRow())
        self._draw_students()

    def remove_stud(self, st):
        if len(self.stud_rows) <= 1:
            self.app.warn("Minimal 1 data siswa diperlukan.")
            return
        self._snapshot_students()
        self.stud_rows.remove(st)
        self._draw_students()

    # ── Hitung ──────────────────────────────────────────────────────────────
    def calculate(self):
        self._clear_msg()
        self._snapshot_students()
        errors = []

        criteria, used = [], []
        for i, cr in enumerate(self.crit_rows):
            if not cr.name.get().strip():
                continue
            try:
                w = float(cr.weight.get())
            except ValueError:
                w = 0.0
            criteria.append({
                "code": (cr.code.get().strip() or f"C{i + 1}").upper(),
                "name": cr.name.get().strip(),
                "type": cr.ctype,
                "weight": max(0.01, w),
                "scale": {str(s): cr.scale[s].get().strip() for s in range(1, 6)},
            })
            used.append(cr)
        if not criteria:
            errors.append("Minimal 1 kriteria harus diisi.")

        students = []
        for s in self.stud_rows:
            if not s.name.get().strip():
                continue
            values = [max(1, min(5, int(s.vals.get(cr.uid, 1)))) for cr in used]
            students.append({"name": s.name.get().strip(), "class": s.cls.get().strip(), "values": values})
        if not students:
            errors.append("Minimal 1 data siswa harus diisi.")

        if errors:
            T.alert(self.msg, "danger", "Kesalahan:\n" + "\n".join("• " + e for e in errors)
                    ).pack(fill="x", pady=(0, 12))
            return

        try:
            quota = int(self.quota.get().strip() or 0)
        except ValueError:
            quota = 0
        school, operator = self.school.get().strip(), self.operator.get().strip()

        saw = SAW()
        saw.set_criteria(criteria)
        saw.set_students(students)
        results = saw.calculate()
        self.app.state.update(results=results, criteria=criteria, school=school,
                              operator=operator or "-", quota=quota)
        self.show_result(results, criteria, operator, quota)

    # ── Hasil ───────────────────────────────────────────────────────────────
    def show_result(self, results, criteria, operator, quota):
        for w in self.result_frame.winfo_children():
            w.destroy()
        self.form.pack_forget()

        T.alert(self.result_frame, "success",
                f"Perhitungan selesai! {len(results)} siswa diproses dengan {len(criteria)} kriteria."
                ).pack(fill="x", pady=(0, 12))
        if quota > 0:
            tk.Label(self.result_frame, bg=T.BG, fg=T.SUCCESS, font=T.FONT_B, anchor="w",
                     text=f"Kuota PIP: {quota}   —   Peringkat 1–{quota} = Direkomendasikan"
                     ).pack(fill="x", pady=(0, 10))

        outer, body, head = T.card(self.result_frame, "Hasil Perankingan")
        outer.pack(fill="x")
        right = tk.Frame(head, bg=T.CARD)
        right.pack(side="right")
        T.button(right, "Input Baru", self.reset, "secondary").pack(side="right", padx=(8, 0))
        T.button(right, "Download PDF", self.app.save_pdf).pack(side="right")

        wrap, tv = T.result_table(body, criteria, results, quota, short_status=True, height=14)
        wrap.pack(fill="both", expand=True)

        detail = tk.Label(body, bg=T.CARD, fg=T.MUTED, font=T.FONT_SM, anchor="w", justify="left", wraplength=900,
                          text="Pilih satu baris untuk melihat keterangan skala tiap kriteria.")
        detail.pack(fill="x", pady=(8, 0))

        def on_select(_):
            sel = tv.selection()
            if not sel:
                return
            r = results[int(sel[0])]
            parts = []
            for c, v in zip(criteria, r["values"]):
                lbl = c["scale"].get(str(int(v))) or f"Nilai {int(v)}"
                parts.append(f"{c['code']} = {int(v)} ({lbl})")
            detail.config(text=f"{r['name']}:  " + "   ·   ".join(parts), fg=T.TEXT)

        tv.bind("<<TreeviewSelect>>", on_select)
        tk.Label(body, bg=T.CARD, fg=T.MUTED, font=T.FONT_SM, anchor="w",
                 text=f"{datetime.now().strftime('%d %B %Y, %H:%M:%S')} WIB  ·  Operator: {operator}"
                 ).pack(fill="x", pady=(8, 0))
        self.to_top()
