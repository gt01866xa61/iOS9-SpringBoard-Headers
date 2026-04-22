#!/usr/bin/env python3
"""PDF 浮水印工具 - 拖曳 PDF 自動套用浮水印"""

import io
import json
import os
import re
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    raise SystemExit("請先安裝 tkinterdnd2：pip install tkinterdnd2")

try:
    import fitz
except ImportError:
    raise SystemExit("請先安裝 PyMuPDF：pip install PyMuPDF")

try:
    from PIL import Image
except ImportError:
    raise SystemExit("請先安裝 Pillow：pip install Pillow")


CONFIG_PATH = Path.home() / ".pdf_watermark_config.json"

def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


FONTS = {
    "Helvetica": "helv",
    "Helvetica Bold": "hebo",
    "Helvetica Oblique": "heit",
    "Helvetica Bold Oblique": "hebi",
    "Times New Roman": "tiro",
    "Times New Roman Bold": "tibo",
    "Times New Roman Italic": "tiit",
    "Times New Roman Bold Italic": "tibi",
    "Courier": "cour",
    "Courier Bold": "cobo",
    "Courier Oblique": "coit",
    "Courier Bold Oblique": "cobi",
}

POSITIONS = ["置中", "左上", "右上", "左下", "右下", "平鋪重複"]


def hex_to_rgb_float(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    return (r, g, b)


def resolve_output_path(pdf_path: str, suffix: str, folder: str | None = None) -> str:
    base = os.path.splitext(pdf_path)[0]
    if folder:
        filename = os.path.basename(base) + suffix + ".pdf"
        out = os.path.join(folder, filename)
    else:
        out = base + suffix + ".pdf"
    if os.path.exists(out):
        i = 2
        while True:
            candidate = (os.path.splitext(out)[0] + f"_{i}.pdf")
            if not os.path.exists(candidate):
                return candidate
            i += 1
    return out


def parse_page_spec(spec: str, total: int) -> list:
    result = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            result.update(range(max(1, a) - 1, min(total, b)))
        elif re.match(r"^\d+$", part):
            n = int(part)
            if 1 <= n <= total:
                result.add(n - 1)
    return sorted(result)


class WatermarkEngine:
    def __init__(self, pdf_path: str, params: dict):
        self.pdf_path = pdf_path
        self.params = params

    def apply(self) -> str:
        doc = fitz.open(self.pdf_path)
        pages = self._resolve_pages(doc)
        wtype = self.params["watermark_type"]
        for page_idx in pages:
            page = doc[page_idx]
            if wtype == "text":
                self._apply_text(page)
            else:
                self._apply_image(page)
        out = resolve_output_path(
            self.pdf_path,
            self.params["output_suffix"],
            self.params.get("output_folder"),
        )
        doc.save(out, garbage=4, deflate=True, clean=True)
        doc.close()
        return out

    def _resolve_pages(self, doc) -> list:
        total = len(doc)
        mode = self.params["page_range_mode"]
        if mode == "all":
            return list(range(total))
        if mode == "specific":
            return parse_page_spec(self.params["page_spec"], total)
        if mode == "range":
            a = max(1, self.params["page_from"]) - 1
            b = min(total, self.params["page_to"])
            return list(range(a, b))
        return list(range(total))

    def _apply_text(self, page):
        p = self.params
        text = p["text"]
        fontname = p["fontname"]
        fontsize = p["fontsize"]
        color = hex_to_rgb_float(p["color_hex"])
        opacity = p["opacity"] / 100.0
        rotation = p["rotation"]
        overlay = p["overlay"]

        font = fitz.Font(fontname=fontname)
        tw = fitz.TextWriter(page.rect)

        text_width = font.text_length(text, fontsize=fontsize)

        if p["position"] == "平鋪重複":
            step_x = page.rect.width / 3
            step_y = page.rect.height / 3
            for col in range(3):
                for row in range(3):
                    cx = col * step_x + step_x / 2
                    cy = row * step_y + step_y / 2
                    pos = fitz.Point(cx - text_width / 2, cy + fontsize * 0.3)
                    tw.append(pos, text, font=font, fontsize=fontsize)
            morph = self._make_morph(page.rect.width / 2, page.rect.height / 2, rotation)
            tw.write_text(page, color=color, opacity=opacity, morph=morph, overlay=overlay)
        else:
            pos = self._text_position(page, fontsize, text_width)
            cx = pos.x + text_width / 2
            cy = pos.y - fontsize * 0.3
            tw.append(pos, text, font=font, fontsize=fontsize)
            morph = self._make_morph(cx, cy, rotation)
            tw.write_text(page, color=color, opacity=opacity, morph=morph, overlay=overlay)

    def _make_morph(self, cx, cy, angle):
        if angle == 0:
            return None
        pivot = fitz.Point(cx, cy)
        mat = fitz.Matrix(1, 0, 0, 1, 0, 0).prerotate(angle)
        return (pivot, mat)

    def _text_position(self, page, fontsize, text_width=0) -> fitz.Point:
        w, h = page.rect.width, page.rect.height
        pad = 30
        pos_map = {
            "置中":  fitz.Point(w / 2 - text_width / 2, h / 2 + fontsize * 0.3),
            "左上":  fitz.Point(pad, pad + fontsize),
            "右上":  fitz.Point(w - pad - text_width, pad + fontsize),
            "左下":  fitz.Point(pad, h - pad),
            "右下":  fitz.Point(w - pad - text_width, h - pad),
        }
        return pos_map.get(self.params["position"], fitz.Point(w / 2 - text_width / 2, h / 2 + fontsize * 0.3))

    def _apply_image(self, page):
        p = self.params
        img_path = p["image_path"]
        scale = p["scale"] / 100.0
        opacity = p["opacity"] / 100.0
        rotation = p["rotation"]
        overlay = p["overlay"]

        img = Image.open(img_path).convert("RGBA")
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # apply opacity to alpha channel
        r, g, b, a = img.split()
        a = a.point(lambda x: int(x * opacity))
        img = Image.merge("RGBA", (r, g, b, a))

        if rotation != 0:
            img = img.rotate(-rotation, expand=True, resample=Image.BICUBIC)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        rect = self._image_rect(page, img.width, img.height)
        page.insert_image(rect, stream=buf.read(), overlay=overlay)

    def _image_rect(self, page, iw, ih) -> fitz.Rect:
        pw, ph = page.rect.width, page.rect.height
        pad = 20
        pos = self.params["position"]
        rects = {
            "置中":  fitz.Rect(pw/2 - iw/2, ph/2 - ih/2, pw/2 + iw/2, ph/2 + ih/2),
            "左上":  fitz.Rect(pad, pad, pad + iw, pad + ih),
            "右上":  fitz.Rect(pw - pad - iw, pad, pw - pad, pad + ih),
            "左下":  fitz.Rect(pad, ph - pad - ih, pad + iw, ph - pad),
            "右下":  fitz.Rect(pw - pad - iw, ph - pad - ih, pw - pad, ph - pad),
            "平鋪重複": fitz.Rect(pw/2 - iw/2, ph/2 - ih/2, pw/2 + iw/2, ph/2 + ih/2),
        }
        return rects.get(pos, rects["置中"])


class WatermarkDialog:
    def __init__(self, parent, pdf_path: str):
        self.parent = parent
        self.pdf_path = pdf_path
        self.result = None
        self._cfg = load_config()
        self._color_hex = self._cfg.get("text_color_hex", "#FF0000")

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"浮水印設定 — {os.path.basename(pdf_path)}")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        self._build_ui()
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build_ui(self):
        nb = ttk.Notebook(self.dialog)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self._text_tab = ttk.Frame(nb)
        self._image_tab = ttk.Frame(nb)
        nb.add(self._text_tab, text="文字浮水印")
        nb.add(self._image_tab, text="圖片浮水印")
        self._nb = nb

        self._build_text_tab()
        self._build_image_tab()
        self._build_common_section()
        self._build_buttons()
        # restore last used tab
        nb.select(self._cfg.get("last_tab", 0))

    # ---- Text tab ----

    def _build_text_tab(self):
        f = self._text_tab
        c = self._cfg
        self._text_var = tk.StringVar(value=c.get("text_text", "機密文件"))
        self._font_var = tk.StringVar(value=c.get("text_font", "Helvetica"))
        self._fontsize_var = tk.IntVar(value=c.get("text_fontsize", 60))
        self._text_opacity_var = tk.IntVar(value=c.get("text_opacity", 25))
        self._text_rotation_var = tk.IntVar(value=c.get("text_rotation", 45))
        self._text_position_var = tk.StringVar(value=c.get("text_position", "置中"))
        self._text_overlay_var = tk.BooleanVar(value=c.get("text_overlay", True))

        row = 0
        ttk.Label(f, text="浮水印文字：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        ttk.Entry(f, textvariable=self._text_var, width=30).grid(row=row, column=1, columnspan=2, sticky="ew", padx=10)

        row += 1
        ttk.Label(f, text="字型：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        ttk.Combobox(f, textvariable=self._font_var, values=list(FONTS.keys()), state="readonly", width=20).grid(row=row, column=1, sticky="w", padx=10)

        row += 1
        ttk.Label(f, text="字體大小：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        ttk.Spinbox(f, from_=8, to=300, textvariable=self._fontsize_var, width=8).grid(row=row, column=1, sticky="w", padx=10)

        row += 1
        ttk.Label(f, text="顏色：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        self._color_btn = tk.Label(f, bg=self._color_hex, width=6, relief="raised", cursor="hand2")
        self._color_btn.grid(row=row, column=1, sticky="w", padx=10)
        self._color_btn.bind("<Button-1>", self._pick_color)
        ttk.Label(f, text="（點擊選色）").grid(row=row, column=2, sticky="w")

        row += 1
        ttk.Label(f, text="透明度：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        self._make_scale_row(f, row, self._text_opacity_var, 0, 100, "%")

        row += 1
        ttk.Label(f, text="旋轉角度：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        self._make_scale_row(f, row, self._text_rotation_var, -180, 180, "°")

        row += 1
        ttk.Label(f, text="位置：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        ttk.Combobox(f, textvariable=self._text_position_var, values=POSITIONS, state="readonly", width=14).grid(row=row, column=1, sticky="w", padx=10)

        row += 1
        ttk.Label(f, text="圖層：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        layer_f = ttk.Frame(f)
        layer_f.grid(row=row, column=1, columnspan=2, sticky="w", padx=10)
        ttk.Radiobutton(layer_f, text="文字之上", variable=self._text_overlay_var, value=True).pack(side="left")
        ttk.Radiobutton(layer_f, text="文字之後", variable=self._text_overlay_var, value=False).pack(side="left", padx=8)

    # ---- Image tab ----

    def _build_image_tab(self):
        f = self._image_tab
        c = self._cfg
        self._image_path_var = tk.StringVar(value=c.get("image_path", ""))
        self._image_scale_var = tk.IntVar(value=c.get("image_scale", 30))
        self._image_opacity_var = tk.IntVar(value=c.get("image_opacity", 50))
        self._image_rotation_var = tk.IntVar(value=c.get("image_rotation", 0))
        self._image_position_var = tk.StringVar(value=c.get("image_position", "置中"))
        self._image_overlay_var = tk.BooleanVar(value=c.get("image_overlay", True))

        row = 0
        ttk.Label(f, text="圖片路徑：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        path_f = ttk.Frame(f)
        path_f.grid(row=row, column=1, columnspan=2, sticky="ew", padx=10)
        ttk.Entry(path_f, textvariable=self._image_path_var, width=24).pack(side="left")
        ttk.Button(path_f, text="瀏覽…", command=self._pick_image).pack(side="left", padx=4)

        row += 1
        ttk.Label(f, text="縮放比例：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        self._make_scale_row(f, row, self._image_scale_var, 5, 200, "%")

        row += 1
        ttk.Label(f, text="透明度：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        self._make_scale_row(f, row, self._image_opacity_var, 0, 100, "%")

        row += 1
        ttk.Label(f, text="旋轉角度：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        self._make_scale_row(f, row, self._image_rotation_var, -180, 180, "°")

        row += 1
        ttk.Label(f, text="位置：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        ttk.Combobox(f, textvariable=self._image_position_var, values=POSITIONS, state="readonly", width=14).grid(row=row, column=1, sticky="w", padx=10)

        row += 1
        ttk.Label(f, text="圖層：").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        layer_f = ttk.Frame(f)
        layer_f.grid(row=row, column=1, columnspan=2, sticky="w", padx=10)
        ttk.Radiobutton(layer_f, text="文字之上", variable=self._image_overlay_var, value=True).pack(side="left")
        ttk.Radiobutton(layer_f, text="文字之後", variable=self._image_overlay_var, value=False).pack(side="left", padx=8)

    # ---- Shared helper ----

    def _make_scale_row(self, parent, row, var, from_, to, unit):
        scale = ttk.Scale(parent, from_=from_, to=to, variable=var, orient="horizontal", length=150)

        def on_scale(*_):
            var.set(int(var.get()))

        scale.config(command=on_scale)
        scale.grid(row=row, column=1, sticky="w", padx=10)

        val_frame = ttk.Frame(parent)
        val_frame.grid(row=row, column=2, sticky="w")
        spin = ttk.Spinbox(val_frame, from_=from_, to=to, textvariable=var, width=5)
        spin.pack(side="left")
        ttk.Label(val_frame, text=unit).pack(side="left", padx=(2, 0))

    # ---- Common (page range + output) ----

    def _build_common_section(self):
        sep = ttk.Separator(self.dialog, orient="horizontal")
        sep.pack(fill="x", padx=10)

        frame = ttk.Frame(self.dialog)
        frame.pack(fill="x", padx=10, pady=6)

        c = self._cfg
        self._page_mode_var = tk.StringVar(value=c.get("page_range_mode", "all"))
        self._page_spec_var = tk.StringVar(value=c.get("page_spec", ""))
        self._page_from_var = tk.IntVar(value=c.get("page_from", 1))
        self._page_to_var = tk.IntVar(value=c.get("page_to", 1))

        ttk.Label(frame, text="頁面範圍：", font=("", 9, "bold")).grid(row=0, column=0, sticky="w", pady=2)

        rb_all = ttk.Radiobutton(frame, text="全部頁面", variable=self._page_mode_var,
                                  value="all", command=self._update_page_widgets)
        rb_all.grid(row=0, column=1, sticky="w")

        rb_spec = ttk.Radiobutton(frame, text="指定頁碼（如 1,3,5-8）：",
                                   variable=self._page_mode_var, value="specific",
                                   command=self._update_page_widgets)
        rb_spec.grid(row=1, column=1, sticky="w")
        self._spec_entry = ttk.Entry(frame, textvariable=self._page_spec_var, width=16, state="disabled")
        self._spec_entry.grid(row=1, column=2, sticky="w", padx=4)

        rb_range = ttk.Radiobutton(frame, text="頁碼範圍：",
                                    variable=self._page_mode_var, value="range",
                                    command=self._update_page_widgets)
        rb_range.grid(row=2, column=1, sticky="w")
        range_f = ttk.Frame(frame)
        range_f.grid(row=2, column=2, sticky="w", padx=4)
        ttk.Label(range_f, text="第").pack(side="left")
        self._from_spin = ttk.Spinbox(range_f, from_=1, to=9999, textvariable=self._page_from_var,
                                       width=5, state="disabled")
        self._from_spin.pack(side="left", padx=2)
        ttk.Label(range_f, text="頁 到 第").pack(side="left")
        self._to_spin = ttk.Spinbox(range_f, from_=1, to=9999, textvariable=self._page_to_var,
                                     width=5, state="disabled")
        self._to_spin.pack(side="left", padx=2)
        ttk.Label(range_f, text="頁").pack(side="left")

        sep2 = ttk.Separator(self.dialog, orient="horizontal")
        sep2.pack(fill="x", padx=10, pady=4)

        out_frame = ttk.Frame(self.dialog)
        out_frame.pack(fill="x", padx=10, pady=4)

        self._out_mode_var = tk.StringVar(value=c.get("output_mode", "same"))
        self._out_suffix_var = tk.StringVar(value=c.get("output_suffix", ""))
        self._out_folder_var = tk.StringVar(value=c.get("output_folder", ""))

        ttk.Label(out_frame, text="輸出方式：", font=("", 9, "bold")).grid(row=0, column=0, sticky="w")

        rb_same = ttk.Radiobutton(out_frame, text="原資料夾，後綴名：",
                                   variable=self._out_mode_var, value="same",
                                   command=self._update_out_widgets)
        rb_same.grid(row=0, column=1, sticky="w")
        self._suffix_entry = ttk.Entry(out_frame, textvariable=self._out_suffix_var, width=12)
        self._suffix_entry.grid(row=0, column=2, sticky="w", padx=4)
        ttk.Label(out_frame, text="（空白→_浮水印）", foreground="#888").grid(row=0, column=3, sticky="w")

        rb_folder = ttk.Radiobutton(out_frame, text="指定資料夾：",
                                     variable=self._out_mode_var, value="folder",
                                     command=self._update_out_widgets)
        rb_folder.grid(row=1, column=1, sticky="w")
        folder_f = ttk.Frame(out_frame)
        folder_f.grid(row=1, column=2, sticky="w", padx=4)
        self._folder_entry = ttk.Entry(folder_f, textvariable=self._out_folder_var, width=20, state="disabled")
        self._folder_entry.pack(side="left")
        self._folder_btn = ttk.Button(folder_f, text="瀏覽…", command=self._pick_folder, state="disabled")
        self._folder_btn.pack(side="left", padx=4)

        # apply saved states
        self._update_page_widgets()
        self._update_out_widgets()

    def _build_buttons(self):
        btn_f = ttk.Frame(self.dialog)
        btn_f.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_f, text="套用浮水印", command=self._on_apply).pack(side="right", padx=4)
        ttk.Button(btn_f, text="取消", command=self._on_cancel).pack(side="right")

    # ---- Widget state helpers ----

    def _update_page_widgets(self):
        mode = self._page_mode_var.get()
        self._spec_entry.config(state="normal" if mode == "specific" else "disabled")
        spin_state = "normal" if mode == "range" else "disabled"
        self._from_spin.config(state=spin_state)
        self._to_spin.config(state=spin_state)

    def _update_out_widgets(self):
        folder = self._out_mode_var.get() == "folder"
        self._suffix_entry.config(state="disabled" if folder else "normal")
        self._folder_entry.config(state="normal" if folder else "disabled")
        self._folder_btn.config(state="normal" if folder else "disabled")

    # ---- Pickers ----

    def _pick_color(self, _event=None):
        result = colorchooser.askcolor(color=self._color_hex, title="選擇浮水印顏色", parent=self.dialog)
        if result and result[1]:
            self._color_hex = result[1]
            self._color_btn.config(bg=self._color_hex)

    def _pick_image(self):
        path = filedialog.askopenfilename(
            title="選擇浮水印圖片",
            filetypes=[("圖片檔案", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"), ("所有檔案", "*.*")],
            parent=self.dialog,
        )
        if path:
            self._image_path_var.set(path)

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="選擇輸出資料夾", parent=self.dialog)
        if folder:
            self._out_folder_var.set(folder)

    # ---- Apply / Cancel ----

    def _on_apply(self):
        tab = self._nb.index(self._nb.select())
        wtype = "text" if tab == 0 else "image"

        if wtype == "text" and not self._text_var.get().strip():
            messagebox.showwarning("缺少內容", "請輸入浮水印文字。", parent=self.dialog)
            return

        if wtype == "image":
            img_path = self._image_path_var.get().strip()
            if not img_path or not os.path.isfile(img_path):
                messagebox.showwarning("缺少圖片", "請選擇有效的浮水印圖片。", parent=self.dialog)
                return

        out_mode = self._out_mode_var.get()
        if out_mode == "folder":
            folder = self._out_folder_var.get().strip()
            if not folder or not os.path.isdir(folder):
                messagebox.showwarning("資料夾無效", "請選擇有效的輸出資料夾。", parent=self.dialog)
                return

        save_config({
            "last_tab": self._nb.index(self._nb.select()),
            "text_text": self._text_var.get(),
            "text_font": self._font_var.get(),
            "text_fontsize": self._fontsize_var.get(),
            "text_color_hex": self._color_hex,
            "text_opacity": self._text_opacity_var.get(),
            "text_rotation": self._text_rotation_var.get(),
            "text_position": self._text_position_var.get(),
            "text_overlay": bool(self._text_overlay_var.get()),
            "image_path": self._image_path_var.get(),
            "image_scale": self._image_scale_var.get(),
            "image_opacity": self._image_opacity_var.get(),
            "image_rotation": self._image_rotation_var.get(),
            "image_position": self._image_position_var.get(),
            "image_overlay": bool(self._image_overlay_var.get()),
            "page_range_mode": self._page_mode_var.get(),
            "page_spec": self._page_spec_var.get(),
            "page_from": self._page_from_var.get(),
            "page_to": self._page_to_var.get(),
            "output_mode": self._out_mode_var.get(),
            "output_suffix": self._out_suffix_var.get(),
            "output_folder": self._out_folder_var.get(),
        })

        self.result = {
            "watermark_type": wtype,
            # text
            "text": self._text_var.get(),
            "fontname": FONTS.get(self._font_var.get(), "helv"),
            "fontsize": self._fontsize_var.get(),
            "color_hex": self._color_hex,
            "opacity": self._text_opacity_var.get() if wtype == "text" else self._image_opacity_var.get(),
            "rotation": self._text_rotation_var.get() if wtype == "text" else self._image_rotation_var.get(),
            "position": self._text_position_var.get() if wtype == "text" else self._image_position_var.get(),
            "overlay": self._text_overlay_var.get() if wtype == "text" else self._image_overlay_var.get(),
            # image
            "image_path": self._image_path_var.get(),
            "scale": self._image_scale_var.get(),
            # page range
            "page_range_mode": self._page_mode_var.get(),
            "page_spec": self._page_spec_var.get(),
            "page_from": self._page_from_var.get(),
            "page_to": self._page_to_var.get(),
            # output
            "output_suffix": self._out_suffix_var.get() or "_浮水印",
            "output_folder": self._out_folder_var.get() if out_mode == "folder" else None,
        }
        self.dialog.destroy()

    def _on_cancel(self):
        self.result = None
        self.dialog.destroy()

    def show(self) -> dict | None:
        self.dialog.wait_window()
        return self.result


class DropZoneApp:
    def __init__(self, root: TkinterDnD.Tk):
        self.root = root
        self.root.title("PDF 浮水印工具")
        self.root.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        self.root.configure(bg="#f5f5f5")

        outer = tk.Frame(self.root, bg="#f5f5f5", padx=20, pady=20)
        outer.pack(fill="both", expand=True)

        title = tk.Label(outer, text="PDF 浮水印工具", font=("", 16, "bold"), bg="#f5f5f5", fg="#333")
        title.pack(pady=(0, 10))

        # Drop zone
        drop_frame = tk.Frame(outer, bg="#e8f0fe", bd=2, relief="groove",
                               highlightbackground="#4a90e2", highlightthickness=2)
        drop_frame.pack(fill="both", expand=True)

        inner = tk.Frame(drop_frame, bg="#e8f0fe", padx=40, pady=40)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="📄", font=("", 48), bg="#e8f0fe").pack()
        tk.Label(inner, text="將 PDF 檔案拖曳至此", font=("", 13, "bold"),
                 bg="#e8f0fe", fg="#4a90e2").pack(pady=(8, 4))
        tk.Label(inner, text="或使用下方按鈕選擇檔案", font=("", 10),
                 bg="#e8f0fe", fg="#666").pack()

        ttk.Button(inner, text="瀏覽 PDF 檔案…", command=self._browse).pack(pady=14)

        # Register drag-and-drop for the whole drop area
        for widget in [drop_frame, inner] + inner.winfo_children():
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass

        self._status_var = tk.StringVar(value="等待 PDF 檔案...")
        self._status_lbl = tk.Label(outer, textvariable=self._status_var,
                                     font=("", 10), bg="#f5f5f5", fg="#555",
                                     wraplength=360, justify="center")
        self._status_lbl.pack(pady=(12, 0))

    def _on_drop(self, event):
        try:
            paths = self.root.tk.splitlist(event.data)
        except Exception:
            paths = [event.data.strip("{}")]

        pdf_paths = [p for p in paths if p.lower().endswith(".pdf") and os.path.isfile(p)]
        if not pdf_paths:
            self._set_status("請拖曳 PDF 格式的檔案。", "red")
            return
        self._process_files(pdf_paths)

    def _browse(self):
        paths = filedialog.askopenfilenames(
            title="選擇 PDF 檔案",
            filetypes=[("PDF 文件", "*.pdf"), ("所有檔案", "*.*")],
        )
        if paths:
            self._process_files(list(paths))

    def _process_files(self, paths: list):
        for pdf_path in paths:
            self._set_status(f"正在處理：{os.path.basename(pdf_path)}", "#333")
            self.root.update()

            dlg = WatermarkDialog(self.root, pdf_path)
            params = dlg.show()

            if params is None:
                self._set_status("已取消。", "#888")
                continue

            try:
                engine = WatermarkEngine(pdf_path, params)
                out_path = engine.apply()
                self._set_status(f"✓ 已儲存：{out_path}", "#2e7d32")
            except Exception as e:
                messagebox.showerror("處理失敗", f"無法套用浮水印：\n{e}")
                self._set_status("處理失敗，請查看錯誤訊息。", "red")

    def _set_status(self, msg: str, color: str = "#555"):
        self._status_var.set(msg)
        self._status_lbl.config(fg=color)
        self.root.update_idletasks()


def main():
    import sys

    pdf_paths = [p for p in sys.argv[1:] if p.lower().endswith(".pdf") and os.path.isfile(p)]

    if pdf_paths:
        # Desktop icon mode: PDF dropped onto the .py file icon
        # Use plain tk.Tk (no drag-drop window needed)
        root = tk.Tk()
        root.withdraw()
        for pdf_path in pdf_paths:
            dlg = WatermarkDialog(root, pdf_path)
            params = dlg.show()
            if params is None:
                continue
            try:
                engine = WatermarkEngine(pdf_path, params)
                out_path = engine.apply()
                messagebox.showinfo("完成", f"✓ 已儲存：\n{out_path}", parent=root)
            except Exception as e:
                messagebox.showerror("處理失敗", f"無法套用浮水印：\n{e}", parent=root)
        root.destroy()
        return

    # Normal window mode: show the drag-and-drop zone
    root = TkinterDnD.Tk()
    root.geometry("420x360")
    DropZoneApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
