# -*- coding: utf-8 -*-
import os, json, tempfile, datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from PyPDF2 import PdfMerger
from mahjong_score_sheet import generate_pdf_from_json
from _mahjong_fmt import format_mahjong_json

COLORS = {
    "bg": "#F2F0EB", "card_bg": "#FFFFFF", "header_bg": "#2D5A3D",
    "header_fg": "#F5E6C8", "accent": "#C8A84E", "accent_hover": "#D4B85A",
    "danger": "#C0392B", "danger_hover": "#E74C3C", "success": "#27AE60",
    "text": "#2C2C2C", "text_secondary": "#6B6B6B", "border": "#D5CFC3",
    "entry_bg": "#FAFAF7", "canvas_bg": "#EDEBE5", "status_bg": "#E8E5DD",
    "tag_green": "#E8F5E9", "tag_red": "#FFEBEE", "tag_gray": "#ECECEC",
}

FONTS = {
    "title": ("Microsoft YaHei UI", 16, "bold"),
    "heading": ("Microsoft YaHei UI", 11, "bold"),
    "body": ("Microsoft YaHei UI", 10),
    "small": ("Microsoft YaHei UI", 9),
    "mono": ("Consolas", 10),
}

SETTINGS_PATH = Path(os.path.expanduser("~")) / ".mahjong_score_sheet_settings.json"

def load_settings():
    defaults = {"last_output_dir": "", "east": "", "south": "", "west": "", "north": "",
                "main_title": "", "main_date": ""}
    try:
        if SETTINGS_PATH.exists():
            defaults.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
    except Exception: pass
    return defaults

def save_settings(s):
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass
# ===================================================
class CollapsibleFrame(tk.Frame):
    def __init__(self, master, title="", **kw):
        tk.Frame.__init__(self, master, bg=COLORS["card_bg"], **kw)
        self._collapsed = False
        self.header = tk.Frame(self, bg=COLORS["header_bg"], cursor="hand2")
        self.header.pack(fill="x")

        self.toggle_btn = tk.Label(
            self.header, text="  ▼  ", font=("", 9, "bold"),
            bg=COLORS["header_fg"], fg=COLORS["header_bg"],
            cursor="hand2", width=4, anchor="center",
            relief="flat", bd=0)
        self.toggle_btn.pack(side="left", padx=(8, 6), pady=4, ipady=1)

        self.title_label = tk.Label(
            self.header, text=title, font=FONTS["heading"],
            bg=COLORS["header_bg"], fg=COLORS["header_fg"],
            cursor="hand2", anchor="w")
        self.title_label.pack(side="left", fill="x", expand=True, pady=4)

        self.valid_badge = tk.Label(
            self.header, text="", font=FONTS["small"],
            bg=COLORS["header_bg"], fg=COLORS["header_fg"],
            padx=8, pady=1)
        self.valid_badge.pack(side="right", padx=(0, 8), pady=4)

        self.content = tk.Frame(self, bg=COLORS["card_bg"])
        self.content.pack(fill="both", expand=True, padx=1, pady=1)

        for w in (self.header, self.toggle_btn, self.title_label):
            w.bind("<Button-1>", self._toggle)

    def _toggle(self, event=None):
        self._collapsed = not self._collapsed
        if self._collapsed:
            self.content.pack_forget()
            self.toggle_btn.config(text="  ▶  ")
        else:
            self.content.pack(fill="both", expand=True, padx=1, pady=1)
            self.toggle_btn.config(text="  ▼  ")

    def set_title(self, text):
        self.title_label.config(text=text)

    def is_collapsed(self):
        return self._collapsed

# ===================================================
class RoundCard:
    def __init__(self, master, index, callbacks):
        self.master = master
        self.index = index
        self.callbacks = callbacks
        self._valid = None
        self._debounce_id = None

        self.collapse = CollapsibleFrame(master, title=f"第 {index} 局")
        c = self.collapse.content

        # Row 1: per-round title, date
        row1 = tk.Frame(c, bg=COLORS["card_bg"])
        row1.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(row1, text="本局标题", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(side="left")
        self.per_title = tk.Entry(row1, font=FONTS["body"], width=28,
                                  bg=COLORS["entry_bg"], relief="solid", bd=1)
        self.per_title.pack(side="left", padx=4)

        tk.Label(row1, text="日期", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(side="left", padx=(8, 0))
        self.per_date = tk.Entry(row1, font=FONTS["body"], width=20,
                                  bg=COLORS["entry_bg"], relief="solid", bd=1)
        self.per_date.pack(side="left", padx=4)

        # JSON text area
        self.text = scrolledtext.ScrolledText(
            c, font=FONTS["mono"], wrap="none",
            bg="#FDFDFB", fg=COLORS["text"],
            relief="flat", bd=0,
            insertbackground=COLORS["accent"],
            selectbackground=COLORS["accent"],
            selectforeground="#FFFFFF", padx=8, pady=6,
            height=14)
        self.text.pack(fill="both", expand=True, padx=10, pady=(2, 4))
        self.text.bind("<<Modified>>", self._on_text_change)

        # Button row
        btn_row = tk.Frame(c, bg=COLORS["card_bg"])
        btn_row.pack(fill="x", padx=10, pady=(0, 6))
        tk.Button(btn_row, text="↑", command=lambda: self.callbacks["move_up"](self),
                  font=FONTS["small"], relief="flat", bd=0, cursor="hand2",
                  bg=COLORS["canvas_bg"], activebackground="#DCD8CE",
                  padx=6, pady=1).pack(side="left", padx=1)
        tk.Button(btn_row, text="↓", command=lambda: self.callbacks["move_down"](self),
                  font=FONTS["small"], relief="flat", bd=0, cursor="hand2",
                  bg=COLORS["canvas_bg"], activebackground="#DCD8CE",
                  padx=6, pady=1).pack(side="left", padx=1)
        tk.Button(btn_row, text="从文件加载...", command=self.load_from_file,
                  font=FONTS["small"], relief="flat", bd=0, cursor="hand2",
                  bg=COLORS["canvas_bg"], activebackground="#DDD8C8",
                  padx=8, pady=1).pack(side="left", padx=(8, 1))
        tk.Button(btn_row, text="删除本局", command=self.delete,
                  font=FONTS["small"], relief="flat", bd=0, cursor="hand2",
                  bg=COLORS["danger"], fg="#FFFFFF",
                  activebackground=COLORS["danger_hover"],
                  padx=8, pady=1).pack(side="right", padx=4)

    def destroy(self):
        self.collapse.destroy()

    def _validate_json(self):
        raw = self.text.get("1.0", tk.END).strip()
        if not raw:
            self.collapse.valid_badge.config(text="", bg=COLORS["header_bg"], fg=COLORS["header_fg"])
            self._valid = None
            return
        try:
            json.loads(raw)
            self.collapse.valid_badge.config(text="  OK  ", bg=COLORS["success"], fg="#FFFFFF")
            self._valid = True
        except json.JSONDecodeError:
            self.collapse.valid_badge.config(text="  ERR ", bg=COLORS["danger"], fg="#FFFFFF")
            self._valid = False

    def _on_text_change(self, event=None):
        if self._debounce_id:
            self.master.after_cancel(self._debounce_id)
        self._debounce_id = self.master.after(350, self._do_validate)
        self.text.edit_modified(False)

    def _do_validate(self):
        self._validate_json()
        if self.callbacks.get("changed"):
            self.callbacks["changed"]()

    def load_from_file(self):
        path = filedialog.askopenfilename(title="选择 antoinput.json", filetypes=[("JSON", "*.json")])
        if not path: return
        try:
            txt = Path(path).read_text(encoding="utf-8")
            # Pretty-print JSON for readability using custom formatter
            try:
                jd = json.loads(txt)
                formatted = format_mahjong_json(jd)
            except json.JSONDecodeError:
                formatted = txt
                jd = None
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", formatted)
            self._validate_json()
            # Auto-fill per-round title from JSON
            if jd is not None:
                try:
                    if isinstance(jd.get("title"), list):
                        if len(jd["title"]) > 0 and jd["title"][0]:
                            self.per_title.delete(0, tk.END)
                            self.per_title.insert(0, jd["title"][0])
                        if len(jd["title"]) > 1 and jd["title"][1]:
                            self.per_date.delete(0, tk.END)
                            self.per_date.insert(0, jd["title"][1])
                except Exception: pass
                # Notify App to auto-fill main_title / main_date
                if self.callbacks.get("title_sync"):
                    self.callbacks["title_sync"](jd.get("title", ["", ""]))
        except Exception as e:
            messagebox.showerror("读取错误", str(e))

    def clear(self):
        self.text.delete("1.0", tk.END)
        self.per_title.delete(0, tk.END)
        self.per_date.delete(0, tk.END)
        self._validate_json()

    def delete(self):
        if not messagebox.askyesno("确认", f"确定删除第 {self.index} 局？"):
            return
        self.destroy()
        self.callbacks["remove"](self)

    def get_json_dict(self):
        raw = self.text.get("1.0", tk.END).strip()
        if not raw: return None
        try: return json.loads(raw)
        except json.JSONDecodeError: return None

    def validate(self):
        self._validate_json()
        return self._valid

    def set_index(self, i):
        self.index = i
        self.collapse.set_title(f"第 {i} 局")

# ===================================================
class App:
    def __init__(self, master):
        self.master = master
        self.settings = load_settings()
        self._gen_running = False
        self.rounds = []
        self._setup_theme()
        self._build_menu()
        self._build_ui()
        self._restore_settings()
        self._bind_shortcuts()

    def _setup_theme(self):
        self.master.title("Mahjong Score Sheet v4")
        self.master.configure(bg=COLORS["bg"])
        self.master.minsize(880, 640)
        w, h = 1050, 780
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        self.master.geometry(f"{w}x{h}+{(ws-w)//2}+{(hs-h)//2}")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Card.TFrame", background=COLORS["card_bg"])
        style.configure("Toolbar.TFrame", background=COLORS["bg"])
        style.configure("Status.TFrame", background=COLORS["status_bg"])
        style.configure("Title.TLabel", font=FONTS["title"],
                        background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("Section.TLabel", font=FONTS["heading"],
                        background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("Hint.TLabel", font=FONTS["small"],
                        background=COLORS["bg"], foreground=COLORS["text_secondary"])
        style.configure("Status.TLabel", font=FONTS["small"],
                        background=COLORS["status_bg"], foreground=COLORS["text_secondary"])
        style.configure("Accent.TButton", font=FONTS["heading"],
                        background=COLORS["accent"], foreground="#FFFFFF",
                        borderwidth=0, relief="flat", padding=(30, 10))
        style.map("Accent.TButton",
                  background=[("active", COLORS["accent_hover"]), ("disabled", "#AAAAAA")])

    def _build_menu(self):
        self.menubar = tk.Menu(self.master, font=FONTS["body"],
                               bg=COLORS["bg"], fg=COLORS["text"],
                               activebackground=COLORS["accent"], activeforeground="#FFFFFF")

        file_menu = tk.Menu(self.menubar, tearoff=0, font=FONTS["body"],
                            bg="#FFFFFF", fg=COLORS["text"])
        file_menu.add_command(label="新增一局 (Ctrl+N)", command=self.add_round)
        file_menu.add_command(label="导入 JSON... (Ctrl+O)", command=self.import_files)
        file_menu.add_separator()
        file_menu.add_command(label="保存项目...", command=self.save_project)
        file_menu.add_command(label="加载项目...", command=self.load_project)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.master.quit)
        self.menubar.add_cascade(label="文件", menu=file_menu)

        edit_menu = tk.Menu(self.menubar, tearoff=0, font=FONTS["body"],
                            bg="#FFFFFF", fg=COLORS["text"])
        edit_menu.add_command(label="清空全部局", command=self.clear_all)
        edit_menu.add_command(label="展开全部", command=self._expand_all)
        edit_menu.add_command(label="折叠全部", command=self._collapse_all)
        self.menubar.add_cascade(label="编辑", menu=edit_menu)

        help_menu = tk.Menu(self.menubar, tearoff=0, font=FONTS["body"],
                            bg="#FFFFFF", fg=COLORS["text"])
        help_menu.add_command(label="关于", command=self._show_about)
        self.menubar.add_cascade(label="帮助", menu=help_menu)

        self.master.config(menu=self.menubar)

    def _bind_shortcuts(self):
        self.master.bind("<Control-n>", lambda e: self.add_round())
        self.master.bind("<Control-o>", lambda e: self.import_files())
        self.master.bind("<Control-g>", lambda e: self.generate_all())
        self.master.bind("<Control-s>", lambda e: self.save_project())

    def _build_ui(self):
        # ---- Title bar ----
        tb = tk.Frame(self.master, bg=COLORS["bg"])
        tb.pack(fill="x", padx=20, pady=(14, 0))
        tk.Label(tb, text="麻将牌谱生成器", font=FONTS["title"],
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
        tk.Label(tb, text="v4 · 批量生成整合牌谱 PDF",
                 font=FONTS["small"], bg=COLORS["bg"],
                 fg=COLORS["text_secondary"]).pack(side="left", padx=10, pady=(6, 0))

        # ---- Settings card ----
        sf = tk.Frame(self.master, bg=COLORS["card_bg"],
                       highlightbackground=COLORS["border"], highlightthickness=1)
        sf.pack(fill="x", padx=20, pady=(10, 4))

        # Section header
        hf = tk.Frame(sf, bg=COLORS["card_bg"])
        hf.grid(row=0, column=0, columnspan=8, sticky="ew", padx=16, pady=(10, 4))
        tk.Label(hf, text="半庄设置", font=FONTS["heading"],
                 bg=COLORS["card_bg"], fg=COLORS["text"]).pack(side="left")
        tk.Frame(hf, bg=COLORS["border"], height=1).pack(side="left", fill="x", expand=True, padx=4, pady=8)

        self._mode = "single"
        self._mode_single_btn = tk.Label(
            hf, text="  单局模式  ", font=FONTS["small"],
            bg=COLORS["accent"], fg="#FFFFFF", cursor="hand2", padx=6, pady=2)
        self._mode_single_btn.pack(side="right", padx=(0, 2))
        self._mode_hanchan_btn = tk.Label(
            hf, text="  半庄模式  ", font=FONTS["small"],
            bg=COLORS["bg"], fg=COLORS["text_secondary"], cursor="hand2", padx=6, pady=2)
        self._mode_hanchan_btn.pack(side="right")
        self._mode_single_btn.bind("<Button-1>", lambda e: self._switch_mode("single"))
        self._mode_hanchan_btn.bind("<Button-1>", lambda e: self._switch_mode("hanchan"))

        # Title & date
        tk.Label(sf, text="半庄标题", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).grid(
                     row=1, column=0, sticky="e", padx=(16, 4), pady=4)
        self.main_title = tk.Entry(sf, font=FONTS["body"], width=36,
                                   bg=COLORS["entry_bg"], relief="solid", bd=1)
        self.main_title.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        tk.Label(sf, text="日期", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).grid(
                     row=1, column=2, sticky="e", padx=(12, 4), pady=4)
        self.main_date = tk.Entry(sf, font=FONTS["body"], width=24,
                                  bg=COLORS["entry_bg"], relief="solid", bd=1)
        self.main_date.grid(row=1, column=3, sticky="ew", padx=4, pady=4)

        # Player names
        tk.Label(sf, text="玩家姓名", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).grid(
                     row=2, column=0, sticky="ne", padx=(16, 4), pady=6)

        pf = tk.Frame(sf, bg=COLORS["card_bg"])
        pf.grid(row=2, column=1, columnspan=3, sticky="ew", padx=4, pady=6)
        labels = [("东家 A", "east"), ("南家 B", "south"), ("西家 C", "west"), ("北家 D", "north")]
        for i, (lbl, attr) in enumerate(labels):
            tk.Label(pf, text=lbl, font=FONTS["small"],
                     bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).grid(
                         row=0, column=i*2, padx=(0, 2))
            e = tk.Entry(pf, font=FONTS["body"], width=12,
                         bg=COLORS["entry_bg"], relief="solid", bd=1)
            e.grid(row=0, column=i*2+1, padx=(0, 8))
            setattr(self, f"{attr}_entry", e)

        # Advanced: shorthand/mapping
        adv_hdr = tk.Frame(sf, bg=COLORS["card_bg"])
        adv_hdr.grid(row=3, column=0, columnspan=4, sticky="ew", padx=16, pady=(6, 0))
        self._adv_visible = False
        self._adv_toggle_btn = tk.Label(
            adv_hdr, text="[+]  高级: 座次简写/映射", font=FONTS["small"],
            bg=COLORS["card_bg"], fg=COLORS["accent"], cursor="hand2", anchor="w")
        self._adv_toggle_btn.pack(side="left")
        self._adv_toggle_btn.bind("<Button-1>", self._toggle_advanced)

        self._adv_frame = tk.Frame(sf, bg=COLORS["card_bg"])
        self._adv_frame.grid(row=4, column=0, columnspan=4, sticky="ew", padx=16, pady=(4, 8))

        tk.Label(self._adv_frame, text="座次简写 (如 ABCD)", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(side="left")
        self.order_entry = tk.Entry(self._adv_frame, font=FONTS["body"], width=14,
                                    bg=COLORS["entry_bg"], relief="solid", bd=1)
        self.order_entry.pack(side="left", padx=4)

        tk.Label(self._adv_frame, text="映射 (如 A=Alice,B=Bob)", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(side="left", padx=(12, 0))
        self.mapping_entry = tk.Entry(self._adv_frame, font=FONTS["body"], width=44,
                                      bg=COLORS["entry_bg"], relief="solid", bd=1)
        self.mapping_entry.pack(side="left", padx=4)

        self._adv_frame.grid_remove()

        sf.columnconfigure(1, weight=1)
        sf.columnconfigure(3, weight=1)

        # ---- Separator ----
        sep = tk.Frame(self.master, bg=COLORS["border"], height=2)
        sep.pack(fill="x", padx=20, pady=(6, 0))

        # ---- Rounds toolbar ----
        tb2 = tk.Frame(self.master, bg=COLORS["bg"])
        tb2.pack(fill="x", padx=20, pady=(4, 2))
        tk.Label(tb2, text="对局列表", font=FONTS["heading"],
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
        self.round_count_label = tk.Label(tb2, text="", font=FONTS["small"],
                                          bg=COLORS["bg"], fg=COLORS["text_secondary"])
        self.round_count_label.pack(side="left", padx=8)

        self._toolbar_btns = []
        for txt, cmd in [("[+] 新增一局", self.add_round),
                          ("导入 JSON...", self.import_files),
                          ("清空全部", self.clear_all)]:
            b = tk.Button(tb2, text=txt, command=cmd, font=FONTS["small"],
                      relief="flat", bd=0, cursor="hand2",
                      bg=COLORS["bg"], activebackground="#DCD8CE",
                      padx=10, pady=4)
            b.pack(side="left", padx=2)
            self._toolbar_btns.append(b)

        # ---- Scrollable rounds area ----
        sc = tk.Frame(self.master, bg=COLORS["canvas_bg"],
                       highlightbackground=COLORS["border"], highlightthickness=1)
        sc.pack(fill="both", expand=True, padx=20, pady=(2, 6))

        self.rounds_canvas = tk.Canvas(sc, bg=COLORS["canvas_bg"], highlightthickness=0)
        self.rounds_canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(sc, orient="vertical",
                                      command=self.rounds_canvas.yview, bg=COLORS["bg"])
        self.rounds_canvas.configure(yscrollcommand=self._on_scroll)

        self.inner_frame = tk.Frame(self.rounds_canvas, bg=COLORS["canvas_bg"])
        self.canvas_window = self.rounds_canvas.create_window(
            (0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self._on_inner_configure)
        self.rounds_canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_mousewheel()

        # Empty state
        self.empty_label = tk.Label(
            self.inner_frame,
            text="暂无对局\n点击 [+] 新增一局 或 导入 JSON 开始",
            font=("Microsoft YaHei UI", 11),
            bg=COLORS["canvas_bg"], fg=COLORS["text_secondary"],
            justify="center", pady=40)
        self.empty_label.pack(fill="x")

        # ---- Hanchan input area (hidden in single mode) ----
        self._hanchan_frame = tk.Frame(self.inner_frame, bg=COLORS["canvas_bg"])

        hc_import_btn = tk.Button(
            self._hanchan_frame, text="导入半庄 JSON...", font=FONTS["small"],
            relief="flat", bd=0, cursor="hand2",
            bg="#E8E4D8", activebackground="#DDD8C8",
            padx=10, pady=3, command=self._load_hanchan_json)
        hc_import_btn.pack(padx=8, pady=(4, 0), anchor="w")

        # Tenhou URL input row
        hc_url_row = tk.Frame(self._hanchan_frame, bg=COLORS["canvas_bg"])
        hc_url_row.pack(fill="x", padx=8, pady=(4, 0))
        tk.Label(hc_url_row, text="天凤 URL:", font=FONTS["small"],
                 bg=COLORS["canvas_bg"], fg=COLORS["text_secondary"]).pack(side="left", padx=(0, 4))
        self._hanchan_url = tk.Entry(hc_url_row, font=FONTS["body"],
                                     bg=COLORS["entry_bg"], relief="solid", bd=1)
        self._hanchan_url.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._hanchan_fetch_btn = tk.Button(hc_url_row, text="获取", font=FONTS["small"],
                  relief="flat", bd=0, cursor="hand2",
                  bg=COLORS["accent"], fg="#FFFFFF",
                  activebackground=COLORS["accent_hover"],
                  padx=12, pady=3, command=self._fetch_tenhou_url)
        self._hanchan_fetch_btn.pack(side="left")

        # Hanchan text with horizontal + vertical scrollbars
        self._hanchan_text_frame = tk.Frame(self._hanchan_frame, bg=COLORS["canvas_bg"])
        self._hanchan_text_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self._hanchan_text = tk.Text(
            self._hanchan_text_frame, font=FONTS["mono"], wrap="none",
            bg="#FDFDFB", fg=COLORS["text"],
            relief="flat", bd=0,
            insertbackground=COLORS["accent"],
            selectbackground=COLORS["accent"],
            selectforeground="#FFFFFF", padx=8, pady=6,
            height=18)
        self._hanchan_text_vsb = tk.Scrollbar(
            self._hanchan_text_frame, orient="vertical",
            command=self._hanchan_text.yview, bg=COLORS["bg"])
        self._hanchan_text_hsb = tk.Scrollbar(
            self._hanchan_text_frame, orient="horizontal",
            command=self._hanchan_text.xview, bg=COLORS["bg"])
        self._hanchan_text.configure(
            yscrollcommand=self._hanchan_text_vsb.set,
            xscrollcommand=self._hanchan_text_hsb.set)
        self._hanchan_text.grid(row=0, column=0, sticky="nsew")
        self._hanchan_text_vsb.grid(row=0, column=1, sticky="ns")
        self._hanchan_text_hsb.grid(row=1, column=0, sticky="ew")
        self._hanchan_text_frame.grid_rowconfigure(0, weight=1)
        self._hanchan_text_frame.grid_columnconfigure(0, weight=1)

        hc_btn_row2 = tk.Frame(self._hanchan_frame, bg=COLORS["canvas_bg"])
        hc_btn_row2.pack(fill="x", padx=8, pady=(0, 2))
        tk.Button(hc_btn_row2, text="解析预览", font=FONTS["small"],
                  relief="flat", bd=0, cursor="hand2",
                  bg=COLORS["accent"], fg="#FFFFFF",
                  activebackground=COLORS["accent_hover"],
                  padx=10, pady=3, command=self._preview_hanchan).pack(side="left")

        self._hanchan_preview_frame = tk.Frame(self._hanchan_frame, bg=COLORS["canvas_bg"])
        self._hanchan_preview_frame.pack(fill="x", padx=8, pady=(4, 6))
        self._hanchan_preview = tk.Listbox(
            self._hanchan_preview_frame, font=FONTS["mono"],
            bg="#F8F8F4", fg=COLORS["text"],
            relief="flat", bd=0, height=6,
            selectbackground=COLORS["accent"])
        self._hanchan_preview_vsb = tk.Scrollbar(
            self._hanchan_preview_frame, orient="vertical",
            command=self._hanchan_preview.yview, bg=COLORS["bg"])
        self._hanchan_preview.configure(yscrollcommand=self._hanchan_preview_vsb.set)
        self._hanchan_preview.pack(side="left", fill="both", expand=True)
        self._hanchan_preview_vsb.pack(side="right", fill="y")

        # ---- Fixed bottom bar ----
        self.bottom_sep = tk.Frame(self.master, bg=COLORS["border"], height=2)
        self.bottom_sep.pack(fill="x", side="bottom", padx=0, pady=0)

        bot = tk.Frame(self.master, bg=COLORS["bg"])
        bot.pack(fill="x", side="bottom", padx=20, pady=(4, 6))

        cb_frame = tk.Frame(bot, bg=COLORS["bg"])
        cb_frame.pack(fill="x", pady=(0, 4))
        self.gen_individual = tk.BooleanVar(value=True)
        self.gen_merged = tk.BooleanVar(value=True)
        self._cb_indiv = tk.Checkbutton(
            cb_frame, text="生成单局 PDF", variable=self.gen_individual,
            font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"],
            activebackground=COLORS["bg"], selectcolor=COLORS["bg"],
            command=self._on_checkbox_change)
        self._cb_indiv.pack(side="left", padx=(0, 12))
        self._cb_merge = tk.Checkbutton(
            cb_frame, text="生成整合 PDF", variable=self.gen_merged,
            font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text"],
            activebackground=COLORS["bg"], selectcolor=COLORS["bg"],
            command=self._on_checkbox_change)
        self._cb_merge.pack(side="left")

        pf2 = tk.Frame(bot, bg=COLORS["bg"])
        pf2.pack(fill="x")
        self.progress = ttk.Progressbar(pf2, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.gen_btn = tk.Button(pf2,
            text="    生成整合牌谱 PDF    ",
            command=self.generate_all,
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=COLORS["accent"], fg="#FFFFFF",
            activebackground=COLORS["accent_hover"], activeforeground="#FFFFFF",
            relief="flat", bd=0, cursor="hand2", padx=28, pady=10)
        self.gen_btn.pack(side="right")

        # ---- Status bar ----
        st = tk.Frame(self.master, bg=COLORS["status_bg"], height=24)
        st.pack(fill="x", side="bottom")
        self.status_label = tk.Label(st, text="就绪", font=FONTS["small"],
                                     bg=COLORS["status_bg"],
                                     fg=COLORS["text_secondary"], anchor="w")
        self.status_label.pack(side="left", padx=12, pady=2)

        # Add first empty round
        self.add_round()

    def _toggle_advanced(self, event=None):
        self._adv_visible = not self._adv_visible
        if self._adv_visible:
            self._adv_frame.grid()
            self._adv_toggle_btn.config(text="[-]  高级选项 (收起)",
                                        fg=COLORS["text_secondary"])
        else:
            self._adv_frame.grid_remove()
            self._adv_toggle_btn.config(text="[+]  高级: 座次简写/映射",
                                        fg=COLORS["accent"])

    # ========== Mode switching ==========
    def _switch_mode(self, mode):
        self._mode = mode
        if mode == "single":
            self._mode_single_btn.config(bg=COLORS["accent"], fg="#FFFFFF")
            self._mode_hanchan_btn.config(bg=COLORS["bg"], fg=COLORS["text_secondary"])
            self._hanchan_frame.pack_forget()
            for b in self._toolbar_btns:
                b.config(state="normal", cursor="hand2")
            if not self.rounds:
                self.empty_label.pack(fill="x")
            for rd in self.rounds:
                rd.collapse.pack(fill="x", padx=8, pady=(6, 2))
        else:
            self._mode_single_btn.config(bg=COLORS["bg"], fg=COLORS["text_secondary"])
            self._mode_hanchan_btn.config(bg=COLORS["accent"], fg="#FFFFFF")
            self._hanchan_frame.pack(fill="both", expand=True, padx=0, pady=(4, 2))
            for b in self._toolbar_btns:
                b.config(state="disabled", cursor="arrow")
            self.empty_label.pack_forget()
            for rd in self.rounds:
                rd.collapse.pack_forget()

    def _fetch_tenhou_url(self):
        url = (self._hanchan_url.get() or "").strip()
        if not url:
            messagebox.showwarning("未输入URL", "请输入天凤牌谱 ID 或 URL")
            return
        self._hanchan_fetch_btn.config(state="disabled", text="...")
        self._set_status("正在获取天凤牌谱...")
        self.master.update_idletasks()
        try:
            import subprocess
            result = subprocess.run(
                ["node",
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), "tenhou", "tenhou-convert", "command.js"),
                 url],
                capture_output=True, encoding="utf-8", timeout=30)
            if result.returncode != 0:
                err = (result.stderr or "").strip() or "unknown error"
                messagebox.showerror("获取失败", f"tenhou-convert 执行失败:\n{err}")
                self._set_status("获取失败")
                return
            data = (result.stdout or "").strip()
            try:
                jd = json.loads(data)
                formatted = format_mahjong_json(jd)
            except json.JSONDecodeError:
                messagebox.showerror("格式错误", "返回数据不是有效的 JSON")
                self._set_status("获取失败")
                return
            self._hanchan_text.delete("1.0", tk.END)
            self._hanchan_text.insert("1.0", formatted)
            self._preview_hanchan()
            self._set_status("已获取天凤牌谱")
        except subprocess.TimeoutExpired:
            messagebox.showerror("超时", "获取天凤牌谱超时（30秒）")
            self._set_status("超时")
        except FileNotFoundError:
            messagebox.showerror("未找到 tenhou-convert",
                                 "请先安装:\ncd tenhou/tenhou-convert && npm install")
            self._set_status("tenhou-convert 未安装")
        except Exception as e:
            messagebox.showerror("获取失败", str(e))
            self._set_status("获取失败")
        finally:
            self._hanchan_fetch_btn.config(state="normal", text="获取")

    def _load_hanchan_json(self):
        path = filedialog.askopenfilename(
            title="选择半庄 JSON 文件", filetypes=[("JSON", "*.json")])
        if not path: return
        try:
            txt = Path(path).read_text(encoding="utf-8")
            try:
                jd = json.loads(txt)
                formatted = format_mahjong_json(jd)
            except json.JSONDecodeError:
                formatted = txt
            self._hanchan_text.delete("1.0", tk.END)
            self._hanchan_text.insert("1.0", formatted)
            self._preview_hanchan()
            self._set_status(f"已加载: {Path(path).name}")
        except Exception as e:
            messagebox.showerror("读取失败", str(e))

    def _preview_hanchan(self):
        raw = self._hanchan_text.get("1.0", tk.END).strip()
        self._hanchan_preview.delete(0, tk.END)
        if not raw: return
        try:
            data = json.loads(raw)
            log = data.get("log", [])
            names = data.get("name", [])
        except json.JSONDecodeError:
            self._hanchan_preview.insert(tk.END, "JSON 格式错误")
            self._hanchan_preview.config(fg=COLORS["danger"])
            return
        # Auto-fill main_title / main_date from hanchan JSON (always overwrite)
        try:
            title_list = data.get("title", ["", ""])
            if (isinstance(title_list, list) and len(title_list) > 0 and title_list[0]):
                self.main_title.delete(0, tk.END)
                self.main_title.insert(0, title_list[0])
            if (isinstance(title_list, list) and len(title_list) > 1 and title_list[1]):
                self.main_date.delete(0, tk.END)
                self.main_date.insert(0, title_list[1])
        except Exception: pass
        # Also format the text box content
        try:
            formatted = format_mahjong_json(data)
            self._hanchan_text.delete("1.0", tk.END)
            self._hanchan_text.insert("1.0", formatted)
        except Exception: pass
        self._hanchan_preview.config(fg=COLORS["text"])
        for i, rd in enumerate(log):
            try:
                ri = rd[0]
                rn = ri[0]
                if 0 <= rn <= 3: rname = f"东{rn+1}局"
                elif 4 <= rn <= 7: rname = f"南{rn-3}局"
                else: rname = f"东{rn+1}局"
                honba = ri[1] if len(ri) > 1 else 0
                if honba > 0: rname += f" {honba}本场"
                last = rd[-1]
                last_action = last[0] if isinstance(last, list) and len(last) > 0 and isinstance(last[0], str) else ""
                if last_action == "和了":
                    scores = last[1] if len(last) > 1 else []
                    details = last[2] if len(last) > 2 else []
                    winner_str = "?"
                    score_str = ""
                    if isinstance(details, list) and len(details) >= 2:
                        widx = details[0]
                        if isinstance(widx, int) and widx < len(names):
                            winner_str = names[widx]
                        if len(details) >= 4 and isinstance(details[3], str):
                            score_str = details[3][:20]
                    line = "  %-12s  赢家: %-12s  %s" % (rname, winner_str, score_str)
                elif last_action in ("流局", "九種九牌", "四風連打", "四槓散了", "三家和了"):
                    line = "  %-12s  %s" % (rname, last_action)
                else:
                    line = "  %-12s  流局" % rname
                self._hanchan_preview.insert(tk.END, line)
            except Exception:
                self._hanchan_preview.insert(tk.END, f"  第{i+1}局  (解析失败)")

    def _on_checkbox_change(self):
        if not self.gen_individual.get() and not self.gen_merged.get():
            self.gen_btn.config(state="disabled")
        else:
            self.gen_btn.config(state="normal")

    # ========== Scroll ==========
    def _bind_mousewheel(self):
        def _mw(event):
            # Priority: hanchan text > hanchan preview > rounds canvas
            w = event.widget
            # Check if mouse is over hanchan_text
            try:
                htw = self._hanchan_text
                hx, hy = htw.winfo_rootx(), htw.winfo_rooty()
                hw, hh = htw.winfo_width(), htw.winfo_height()
                if hx <= event.x_root <= hx + hw and hy <= event.y_root <= hy + hh:
                    htw.yview_scroll(int(-event.delta / 120), "units")
                    return "break"
            except Exception: pass
            # Check if mouse is over hanchan_preview
            try:
                hpw = self._hanchan_preview
                hpx, hpy = hpw.winfo_rootx(), hpw.winfo_rooty()
                hpw_w, hpw_h = hpw.winfo_width(), hpw.winfo_height()
                if hpx <= event.x_root <= hpx + hpw_w and hpy <= event.y_root <= hpy + hpw_h:
                    hpw.yview_scroll(int(-event.delta / 120), "units")
                    return "break"
            except Exception: pass
            # Fallback: rounds canvas
            x, y = self.rounds_canvas.winfo_pointerxy()
            wx = self.rounds_canvas.winfo_rootx()
            wy = self.rounds_canvas.winfo_rooty()
            if wx <= x <= wx + self.rounds_canvas.winfo_width() and \
               wy <= y <= wy + self.rounds_canvas.winfo_height():
                self.rounds_canvas.yview_scroll(int(-event.delta / 120), "units")
        self.master.bind_all("<MouseWheel>", _mw)

    def _on_scroll(self, *args):
        self.scrollbar.set(*args)
        if float(args[1]) >= 1.0:
            self.scrollbar.pack_forget()
        else:
            self.scrollbar.pack(side="right", fill="y")

    def _on_inner_configure(self, event):
        self.rounds_canvas.configure(scrollregion=self.rounds_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.rounds_canvas.itemconfig(self.canvas_window, width=event.width)

    # ========== Round management ==========
    def _round_cbs(self):
        return {"remove": self.remove_round, "move_up": self.move_round_up,
                "move_down": self.move_round_down, "changed": lambda: None,
                "title_sync": self._on_round_title_sync}

    def _on_round_title_sync(self, title_list):
        """When a round loads JSON, sync its title to global title fields if they are empty."""
        if title_list and not self.main_title.get().strip() and len(title_list) > 0 and title_list[0]:
            self.main_title.delete(0, tk.END)
            self.main_title.insert(0, title_list[0])
        if title_list and not self.main_date.get().strip() and len(title_list) > 1 and title_list[1]:
            self.main_date.delete(0, tk.END)
            self.main_date.insert(0, title_list[1])

    def add_round(self, json_text=None):
        if not self.rounds:
            self.empty_label.pack_forget()
        idx = len(self.rounds) + 1
        rd = RoundCard(self.inner_frame, idx, self._round_cbs())
        self.rounds.append(rd)
        rd.collapse.pack(fill="x", padx=8, pady=(6, 2))
        if json_text:
            rd.text.delete("1.0", tk.END)
            rd.text.insert("1.0", json_text)
            rd._validate_json()
        self._update_round_count()
        self._auto_scroll_bottom()

    def remove_round(self, rd):
        try: self.rounds.remove(rd)
        except ValueError: return
        self._renumber_rounds()
        if not self.rounds:
            self.empty_label.pack(fill="x")

    def move_round_up(self, rd):
        try: i = self.rounds.index(rd)
        except ValueError: return
        if i == 0: return
        self.rounds[i], self.rounds[i-1] = self.rounds[i-1], self.rounds[i]
        self._repack_renumber()

    def move_round_down(self, rd):
        try: i = self.rounds.index(rd)
        except ValueError: return
        if i >= len(self.rounds)-1: return
        self.rounds[i], self.rounds[i+1] = self.rounds[i+1], self.rounds[i]
        self._repack_renumber()

    def _repack_renumber(self):
        for rd in self.rounds: rd.collapse.pack_forget()
        for rd in self.rounds: rd.collapse.pack(fill="x", padx=8, pady=(6, 2))
        self._renumber_rounds()

    def _renumber_rounds(self):
        for i, rd in enumerate(self.rounds, 1): rd.set_index(i)
        self._update_round_count()

    def _update_round_count(self):
        self.round_count_label.config(text=f"({len(self.rounds)} 局)")

    def _auto_scroll_bottom(self):
        self.master.after(50, lambda: self.rounds_canvas.yview_moveto(1.0))

    def clear_all(self):
        if not self.rounds: return
        if not messagebox.askyesno("确认", "确定清空全部对局数据？"):
            return
        for rd in list(self.rounds): rd.destroy()
        self.rounds.clear()
        self.empty_label.pack(fill="x")
        self._update_round_count()

    def _expand_all(self):
        for rd in self.rounds:
            if rd.collapse.is_collapsed():
                rd.collapse._toggle()

    def _collapse_all(self):
        for rd in self.rounds:
            if not rd.collapse.is_collapsed():
                rd.collapse._toggle()

    def import_files(self):
        paths = filedialog.askopenfilenames(
            title="选择 JSON 文件", filetypes=[("JSON", "*.json")])
        if not paths: return
        for p in paths:
            try:
                txt = Path(p).read_text(encoding="utf-8")
                try:
                    jd = json.loads(txt)
                    formatted = format_mahjong_json(jd)
                except json.JSONDecodeError:
                    formatted = txt
                    jd = None
                self.add_round(json_text=formatted)
            except Exception as e:
                messagebox.showerror("读取错误", f"{Path(p).name}:\n{str(e)}")
        self._set_status(f"已导入 {len(paths)} 个文件")

    # ========== Project save/load ==========
    def save_project(self):
        path = filedialog.asksaveasfilename(
            title="保存项目", defaultextension=".mjproj",
            filetypes=[("麻将项目", "*.mjproj")])
        if not path: return
        data = {
            "main_title": self.main_title.get(),
            "main_date": self.main_date.get(),
            "east": self.east_entry.get(), "south": self.south_entry.get(),
            "west": self.west_entry.get(), "north": self.north_entry.get(),
            "order": self.order_entry.get(), "mapping": self.mapping_entry.get(),
            "rounds": []
        }
        for rd in self.rounds:
            data["rounds"].append({
                "json": rd.text.get("1.0", tk.END).strip(),
                "per_title": rd.per_title.get(),
                "per_date": rd.per_date.get(),
            })
        try:
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self._set_status(f"已保存: {Path(path).name} ({len(self.rounds)} 局)")
        except Exception as e:
            messagebox.showerror("保存错误", str(e))

    def load_project(self):
        path = filedialog.askopenfilename(
            title="加载项目", filetypes=[("麻将项目", "*.mjproj")])
        if not path: return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            messagebox.showerror("读取错误", str(e))
            return
        # Restore settings
        self.main_title.delete(0, tk.END)
        self.main_title.insert(0, data.get("main_title", ""))
        self.main_date.delete(0, tk.END)
        self.main_date.insert(0, data.get("main_date", ""))
        self.east_entry.delete(0, tk.END)
        self.east_entry.insert(0, data.get("east", ""))
        self.south_entry.delete(0, tk.END)
        self.south_entry.insert(0, data.get("south", ""))
        self.west_entry.delete(0, tk.END)
        self.west_entry.insert(0, data.get("west", ""))
        self.north_entry.delete(0, tk.END)
        self.north_entry.insert(0, data.get("north", ""))
        self.order_entry.delete(0, tk.END)
        self.order_entry.insert(0, data.get("order", ""))
        self.mapping_entry.delete(0, tk.END)
        self.mapping_entry.insert(0, data.get("mapping", ""))
        # Clear existing rounds
        for rd in list(self.rounds): rd.destroy()
        self.rounds.clear()
        self.empty_label.pack_forget()
        # Load rounds
        for rd_data in data.get("rounds", []):
            self.add_round(json_text=rd_data.get("json", ""))
            if self.rounds:
                last = self.rounds[-1]
                last.per_title.delete(0, tk.END)
                last.per_title.insert(0, rd_data.get("per_title", ""))
                last.per_date.delete(0, tk.END)
                last.per_date.insert(0, rd_data.get("per_date", ""))
        self._set_status(f"已加载: {Path(path).name} ({len(self.rounds)} 局)")

    # ========== Settings ==========
    def _restore_settings(self):
        s = self.settings
        if s.get("main_title"): self.main_title.insert(0, s["main_title"])
        if s.get("main_date"): self.main_date.insert(0, s["main_date"])
        self.east_entry.insert(0, s.get("east", ""))
        self.south_entry.insert(0, s.get("south", ""))
        self.west_entry.insert(0, s.get("west", ""))
        self.north_entry.insert(0, s.get("north", ""))

    def _persist_settings(self):
        self.settings.update({
            "main_title": self.main_title.get(), "main_date": self.main_date.get(),
            "east": self.east_entry.get(), "south": self.south_entry.get(),
            "west": self.west_entry.get(), "north": self.north_entry.get(),
        })
        save_settings(self.settings)

    # ========== Helpers ==========
    def _set_status(self, text):
        self.status_label.config(text=text)

    def parse_mapping(self, s):
        s = (s or "").strip()
        if not s: return {}
        mapping = {}
        for part in [p.strip() for p in s.replace(";", ",").split(",") if p.strip()]:
            if "=" in part:
                k, v = part.split("=", 1)
                mapping[k.strip()] = v.strip()
        return mapping

    def build_names_list(self):
        order_raw = (self.order_entry.get() or "").strip()
        mapping = self.parse_mapping(self.mapping_entry.get())
        if order_raw:
            small = order_raw.replace(",", " ").split()
            if len(small) == 1 and len(small[0]) == 4:
                tokens = list(small[0])
            elif len(small) == 4:
                tokens = small
            else:
                tokens = None
            if tokens:
                return [mapping.get(tok, tok) for tok in tokens]
        return [
            self.east_entry.get().strip() or "东家",
            self.south_entry.get().strip() or "南家",
            self.west_entry.get().strip() or "西家",
            self.north_entry.get().strip() or "北家",
        ]

    # ========== Generate ==========
    def generate_all(self):
        if self._gen_running: return

        out_dir = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.settings.get("last_output_dir", ""))
        if not out_dir: return
        self.settings["last_output_dir"] = out_dir
        self._persist_settings()

        gen_indiv = self.gen_individual.get()
        gen_merge = self.gen_merged.get()

        # ========== Single-round mode ==========
        if self._mode == "single":
            if not self.rounds:
                messagebox.showwarning("未添加对局", "请至少添加一局 JSON")
                return
            invalid = [i for i, rd in enumerate(self.rounds, 1) if not rd.validate()]
            if invalid:
                if not messagebox.askyesno("JSON 格式警告",
                                           f"第 {invalid} 局 JSON 格式有问题，是否继续？"):
                    return

            self._gen_running = True
            self.gen_btn.config(state="disabled", text="  ... 生成中 ...  ")
            self._set_status("正在生成...")
            main_title = (self.main_title.get() or "").strip()
            main_date = (self.main_date.get() or "").strip()
            names_list = self.build_names_list()
            total = len(self.rounds)
            self.progress["maximum"] = total
            self.progress["value"] = 0
            pdf_paths = []
            tmp_json_paths = []
            success = True

            for idx, rd in enumerate(self.rounds, 1):
                jd = rd.get_json_dict()
                if jd is None:
                    messagebox.showerror("JSON 格式错误", f"第 {idx} 局 JSON 格式错误或为空")
                    success = False
                    break
                per_title = (rd.per_title.get() or "").strip()
                per_date = (rd.per_date.get() or "").strip()
                jd["name"] = names_list
                if "title" not in jd or not isinstance(jd["title"], list):
                    jd["title"] = ["", ""]
                if main_title:
                    jd["title"][0] = main_title
                elif per_title:
                    jd["title"][0] = per_title
                if main_date:
                    jd["title"][1] = main_date
                elif per_date:
                    jd["title"][1] = per_date

                self._set_status(f"正在生成第 {idx}/{total} 局...")
                self.progress["value"] = idx
                self.master.update_idletasks()

                tmpf = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".json", mode="w", encoding="utf-8")
                json.dump(jd, tmpf, ensure_ascii=False, indent=2)
                tmpf.close()
                tmp_json_paths.append(tmpf.name)

                pdf_path = os.path.join(out_dir, f"round_{idx}.pdf")
                ok, err = generate_pdf_from_json(tmpf.name, pdf_path)
                if not ok:
                    messagebox.showerror("生成失败", f"第 {idx} 局生成失败：\n\n{err}")
                    success = False
                    break
                pdf_paths.append(pdf_path)

            if success and pdf_paths:
                if gen_merge:
                    self._set_status("正在合并 PDF...")
                    self.master.update_idletasks()
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_name = f"{main_title}_{ts}" if main_title else f"牌谱_{ts}"
                    merged_path = os.path.join(out_dir, f"{out_name}.pdf")
                    merger = PdfMerger()
                    try:
                        for p in pdf_paths: merger.append(p)
                        merger.write(merged_path)
                    finally:
                        merger.close()
                    self._set_status(f"完成！{len(pdf_paths)} 局 -> {Path(merged_path).name}")
                    messagebox.showinfo("完成",
                                        f"整合牌谱 PDF 已生成：\n\n{merged_path}\n\n共 {len(pdf_paths)} 局")
                else:
                    self._set_status(f"完成！已生成 {len(pdf_paths)} 个单局 PDF")

                if not gen_indiv:
                    for p in pdf_paths:
                        try: os.remove(p)
                        except: pass
            else:
                self._set_status("已取消或失败.")

            for t in tmp_json_paths:
                try: os.remove(t)
                except: pass

            self.progress["value"] = 0
            self._gen_running = False
            self.gen_btn.config(state="normal", text="    生成整合牌谱 PDF    ")

        # ========== Hanchan mode ==========
        else:
            raw = self._hanchan_text.get("1.0", tk.END).strip()
            if not raw:
                messagebox.showwarning("未输入数据", "请先粘贴或导入半庄 JSON")
                return
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                messagebox.showerror("JSON 格式错误", "半庄 JSON 格式错误，请检查")
                return

            tmpf = tempfile.NamedTemporaryFile(
                delete=False, suffix=".json", mode="w", encoding="utf-8")
            json.dump(data, tmpf, ensure_ascii=False, indent=2)
            tmpf.close()

            self._gen_running = True
            self.gen_btn.config(state="disabled", text="  ... 生成中 ...  ")
            self._set_status("正在解析半庄...")

            # Use GUI title/subtitle if set; otherwise fallback to JSON
            gui_title = (self.main_title.get() or "").strip()
            gui_date = (self.main_date.get() or "").strip()

            try:
                from mahjong_score_sheet import split_hanchan_rounds
                rounds = split_hanchan_rounds(tmpf.name)
                total = len(rounds)
                self.progress["maximum"] = total
                self.progress["value"] = 0

                from mahjong_score_sheet import parse_antoinput_file
                pdf_paths = []
                for i, rd in enumerate(rounds, 1):
                    self._set_status(f"正在生成第 {i}/{total} 局...")
                    self.progress["value"] = i
                    self.master.update_idletasks()

                    # Inject GUI title into each round JSON
                    if "title" not in rd or not isinstance(rd["title"], list):
                        rd["title"] = ["", ""]
                    if gui_title:
                        rd["title"][0] = gui_title
                    if gui_date:
                        rd["title"][1] = gui_date

                    t2 = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".json", mode="w", encoding="utf-8")
                    json.dump(rd, t2, ensure_ascii=False, indent=2)
                    t2.close()

                    pdf_path = os.path.join(out_dir, f"round_{i}.pdf")
                    try:
                        game = parse_antoinput_file(t2.name)
                        game.create_pdf_with_annotations(pdf_path)
                        pdf_paths.append(pdf_path)
                    except Exception as e:
                        import traceback
                        messagebox.showerror("生成失败", f"第 {i} 局生成失败：\n\n{traceback.format_exc()}")
                        try: os.remove(t2.name)
                        except: pass
                        break
                    finally:
                        try: os.remove(t2.name)
                        except: pass

                if pdf_paths:
                    if gen_merge:
                        self._set_status("正在合并 PDF...")
                        self.master.update_idletasks()
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        out_title = gui_title or data.get("title", ["牌谱", ""])[0] or "牌谱"
                        merged_path = os.path.join(out_dir, f"{out_title}_{ts}.pdf")
                        merger = PdfMerger()
                        try:
                            for p in pdf_paths: merger.append(p)
                            merger.write(merged_path)
                        finally:
                            merger.close()
                        self._set_status(f"完成！{len(pdf_paths)} 局 -> {Path(merged_path).name}")
                        messagebox.showinfo("完成",
                                            f"整合牌谱 PDF 已生成：\n\n{merged_path}\n\n共 {len(pdf_paths)} 局")
                    else:
                        self._set_status(f"完成！已生成 {len(pdf_paths)} 个单局 PDF")

                    if not gen_indiv:
                        for p in pdf_paths:
                            try: os.remove(p)
                            except: pass

            except Exception as e:
                import traceback
                messagebox.showerror("生成失败", traceback.format_exc())
                self._set_status("生成失败")
            finally:
                try: os.remove(tmpf.name)
                except: pass

            self.progress["value"] = 0
            self._gen_running = False
            self.gen_btn.config(state="normal", text="    生成整合牌谱 PDF    ")

    def _show_about(self):
        messagebox.showinfo(
            "关于",
            "麻将牌谱生成器 v4\n\n"
            "将麻将牌局数据自动排版\n"
            "生成精美的 A4 牌谱 PDF。\n\n"
            "快捷键: Ctrl+N 新增 | Ctrl+O 导入 | Ctrl+G 生成 | Ctrl+S 保存\n\n"
            "依赖: ReportLab / fpdf2 / pdfrw / PyPDF2")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
