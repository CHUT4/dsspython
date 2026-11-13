"""Tema & komponen UI dasar (warna mengikuti style.css versi web)."""
import tkinter as tk
from tkinter import ttk

NAVY = "#1e3a5f"
NAVY_DARK = "#0f2240"
NAVY_MID = "#2d5282"
RED = "#c53030"
RED_LIGHT = "#fed7d7"
BG = "#f7f9fc"
CARD = "#ffffff"
BORDER = "#e2e8f0"
TEXT = "#1a202c"
MUTED = "#718096"
SUCCESS = "#276749"
SUCCESS_BG = "#f0fff4"
INFO_BG = "#ebf4ff"
SOFT = "#f0f4f8"

FONT = ("Segoe UI", 10)
FONT_B = ("Segoe UI", 10, "bold")
FONT_SM = ("Segoe UI", 9)
FONT_H1 = ("Segoe UI", 18, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_MONO = ("Consolas", 10)


def setup_style(root):
    s = ttk.Style(root)
    try:
        s.theme_use("clam")
    except tk.TclError:
        pass
    root.configure(bg=BG)
    s.configure(".", font=FONT, background=BG, foreground=TEXT)
    s.configure("TFrame", background=BG)
    s.configure("Card.TFrame", background=CARD)

    for name, bg, fg, hover in [
        ("Primary", NAVY, "white", NAVY_MID),
        ("Secondary", SOFT, NAVY, BORDER),
        ("Danger", RED_LIGHT, RED, "#feb2b2"),
    ]:
        s.configure(f"{name}.TButton", background=bg, foreground=fg, font=FONT_B,
                    padding=(14, 7), borderwidth=0, focusthickness=0, relief="flat")
        s.map(f"{name}.TButton", background=[("active", hover), ("disabled", BORDER)])

    s.configure("TEntry", fieldbackground="white", bordercolor=BORDER, padding=5)
    s.configure("TCombobox", fieldbackground="white", bordercolor=BORDER, padding=4)
    s.configure("Treeview", background="white", fieldbackground="white", rowheight=26,
                bordercolor=BORDER, font=FONT)
    s.configure("Treeview.Heading", background=NAVY, foreground="white", font=FONT_B,
                padding=6, relief="flat")
    s.map("Treeview.Heading", background=[("active", NAVY_MID)])
    s.map("Treeview", background=[("selected", "#bee3f8")], foreground=[("selected", TEXT)])
    s.configure("Bar.Horizontal.TProgressbar", troughcolor=BORDER, background=NAVY, thickness=8)


def button(parent, text, command, kind="primary", **kw):
    style = {"primary": "Primary.TButton", "secondary": "Secondary.TButton",
             "danger": "Danger.TButton"}[kind]
    return ttk.Button(parent, text=text, command=command, style=style, cursor="hand2", **kw)


class ScrollFrame(tk.Frame):
    """Frame yang bisa di-scroll vertikal. Isi ditaruh di `.body`."""

    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.bind("<Enter>", self._bind_wheel)
        self.bind("<Leave>", self._unbind_wheel)

    def _bind_wheel(self, _):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Button-4>", self._on_wheel)
        self.canvas.bind_all("<Button-5>", self._on_wheel)

    def _unbind_wheel(self, _):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_wheel(self, e):
        if self.body.winfo_height() <= self.canvas.winfo_height():
            return
        if e.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif e.num == 5:
            self.canvas.yview_scroll(3, "units")
        else:
            self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def to_top(self):
        self.canvas.yview_moveto(0)

    def on_show(self, **_):
        """Dipanggil saat halaman ditampilkan (bisa di-override)."""


def page_header(parent, title, subtitle):
    f = tk.Frame(parent, bg=BG)
    tk.Label(f, text=title, font=FONT_H1, fg=NAVY, bg=BG, anchor="w").pack(fill="x")
    tk.Label(f, text=subtitle, font=FONT, fg=MUTED, bg=BG, anchor="w", justify="left",
             wraplength=900).pack(fill="x", pady=(2, 0))
    return f


def card(parent, title=None):
    """Kartu putih berborder. Mengembalikan (outer, body, header_right)."""
    outer = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    head = None
    if title:
        head = tk.Frame(outer, bg=CARD)
        head.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(head, text=title, font=FONT_H2, fg=NAVY, bg=CARD).pack(side="left")
    body = tk.Frame(outer, bg=CARD)
    body.pack(fill="both", expand=True, padx=16, pady=(4, 14))
    return outer, body, head


def alert(parent, kind, text, wrap=900):
    colors = {
        "info": (INFO_BG, "#2b6cb0", "#bee3f8", "i"),
        "success": (SUCCESS_BG, SUCCESS, "#9ae6b4", "✓"),
        "danger": ("#fff5f5", RED, "#feb2b2", "!"),
    }
    bg, fg, border, icon = colors[kind]
    f = tk.Frame(parent, bg=bg, highlightbackground=border, highlightthickness=1)
    tk.Label(f, text=icon, font=FONT_B, fg=fg, bg=bg, width=3).pack(side="left", anchor="n", pady=8)
    tk.Label(f, text=text, font=FONT, fg=fg, bg=bg, justify="left", anchor="w",
             wraplength=wrap).pack(side="left", fill="x", expand=True, padx=(0, 10), pady=8)
    return f


def labeled_entry(parent, label, var, width=30, hint=None, bg=CARD):
    f = tk.Frame(parent, bg=bg)
    tk.Label(f, text=label, font=FONT_B, fg=TEXT, bg=bg, anchor="w").pack(fill="x")
    e = ttk.Entry(f, textvariable=var, width=width)
    e.pack(fill="x", pady=(2, 0))
    if hint:
        tk.Label(f, text=hint, font=FONT_SM, fg=MUTED, bg=bg, anchor="w", justify="left",
                 wraplength=420).pack(fill="x")
    return f


class Tooltip:
    def __init__(self, widget, text_fn):
        self.widget, self.text_fn, self.tip = widget, text_fn, None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")

    def show(self, _=None):
        text = self.text_fn()
        if not text or self.tip:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=text, justify="left", bg=NAVY_DARK, fg="white", font=FONT_SM,
                 padx=10, pady=8).pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def result_table(parent, criteria, results, quota, short_status=False, height=12):
    """Treeview hasil perankingan (dipakai Hitung SAW & Custom SPK)."""
    from lib.saw import fmt_vi

    wrap = tk.Frame(parent, bg=CARD)
    cols = ["no", "nama", "kelas"] + [c["code"] for c in criteria] + ["vi", "status"]
    tv = ttk.Treeview(wrap, columns=cols, show="headings", height=min(height, max(len(results), 3)))
    tv.heading("no", text="No.")
    tv.column("no", width=50, anchor="center", stretch=False)
    tv.heading("nama", text="Nama Siswa")
    tv.column("nama", width=220, anchor="w")
    tv.heading("kelas", text="Kelas")
    tv.column("kelas", width=80, anchor="center", stretch=False)
    for c in criteria:
        tv.heading(c["code"], text=c["code"])
        tv.column(c["code"], width=60, anchor="center", stretch=False)
    tv.heading("vi", text="Skor Vi")
    tv.column("vi", width=80, anchor="center", stretch=False)
    tv.heading("status", text="Status")
    tv.column("status", width=150, anchor="center", stretch=False)
    tv.tag_configure("rec", background="#e8f5e9")
    tv.tag_configure("odd", background="#f7f9fc")

    for i, r in enumerate(results):
        is_rec = quota > 0 and r["rank"] <= quota
        if quota > 0:
            status = ("✓ Rekomen" if short_status else "✓ Direkomendasikan") if is_rec else "— Di luar kuota"
        else:
            status = "—"
        vals = [r["rank"], r["name"], r["class"]] + [int(v) for v in r["values"]] + [fmt_vi(r["vi"]), status]
        tv.insert("", "end", iid=str(i), values=vals, tags=("rec",) if is_rec else (("odd",) if i % 2 else ()))

    vsb = ttk.Scrollbar(wrap, orient="vertical", command=tv.yview)
    hsb = ttk.Scrollbar(wrap, orient="horizontal", command=tv.xview)
    tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tv.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    wrap.grid_rowconfigure(0, weight=1)
    wrap.grid_columnconfigure(0, weight=1)
    return wrap, tv
