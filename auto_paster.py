# 📱 Auto-Paster - A powerful tool for sequential data pasting.
# Build Command: pyinstaller --noconsole --onefile auto_paster.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import threading
import time
import pyperclip
import uiautomation as auto
import sys
import ctypes

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

# ── Config ────────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "data.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

CATEGORIES = ["Phone", "Name", "Email", "Password"]
DEFAULT_HOTKEY = "ctrl+shift+space"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_data():
    default_data = {cat: [] for cat in CATEGORIES}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            
            # Migration: If old data is a list, move it to "Phone"
            if isinstance(data, list):
                migrated = []
                for item in data:
                    val = item.get("number") or item.get("value", "")
                    migrated.append({"value": val, "pasted": item.get("pasted", False)})
                default_data["Phone"] = migrated
                return default_data
            
            # If data is a dict, ensure all categories exist
            if isinstance(data, dict):
                # Compatibility check for old "number" vs new "value" key
                for cat in data:
                    if isinstance(data[cat], list):
                        for item in data[cat]:
                            if "number" in item and "value" not in item:
                                item["value"] = item.pop("number")
                
                for cat in CATEGORIES:
                    if cat not in data:
                        data[cat] = []
                return data
        except Exception:
            return default_data
    return default_data

def save_data(all_data):
    with open(DATA_FILE, "w") as f:
        json.dump(all_data, f, indent=2)

def load_settings():
    default = {"hotkey": DEFAULT_HOTKEY, "paste_mode": "paste"}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                # Ensure defaults for new settings
                if "paste_mode" not in data:
                    data["paste_mode"] = "paste"
                return data
        except:
            return default
    return default

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

# ── Design System ─────────────────────────────────────────────────────────────
BG_COLOR = "#050508"
CARD_COLOR = "#0f0f1a"
ACCENT_COLOR = "#00f2c3"
ACCENT_GLOW = "#1a3a35"
TEXT_COLOR = "#ffffff"
MUTED_COLOR = "#8b8b9e"
DANGER_COLOR = "#ff4757"
DANGER_GLOW = "#3d1418"

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_MONO = ("Consolas", 11)

# ── UI Components ─────────────────────────────────────────────────────────────
class AutoScrollbar(ttk.Scrollbar):
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.pack_forget()
        else:
            self.pack(side="right", fill="y")
        ttk.Scrollbar.set(self, lo, hi)

class HoverButton(tk.Button):
    def __init__(self, master, hover_bg=None, hover_fg=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_bg = self["bg"]
        self.default_fg = self["fg"]
        self.hover_bg = hover_bg or self.default_bg
        self.hover_fg = hover_fg or self.default_fg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.config(bg=self.hover_bg, fg=self.hover_fg)

    def _on_leave(self, e):
        self.config(bg=self.default_bg, fg=self.default_fg)

# ── Main App ──────────────────────────────────────────────────────────────────
class PhonePasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📱 Auto-Paster")
        self.root.geometry("720x950")
        self.root.resizable(True, True)
        self.root.configure(bg=BG_COLOR)

        self.all_data = load_data()
        self.settings = load_settings()
        
        self.current_category = self.settings.get("last_category", CATEGORIES[0])
        if self.current_category not in CATEGORIES:
            self.current_category = CATEGORIES[0]
            
        self.numbers = self.all_data[self.current_category]
        self.auto_detect = tk.BooleanVar(value=self.settings.get("auto_detect", False))
        
        self.hotkey = self.settings.get("hotkey", DEFAULT_HOTKEY)
        self.paste_mode = tk.StringVar(value=self.settings.get("paste_mode", "paste"))
        self.hotkey_registered = False
        self.paste_lock = threading.Lock()
        self.is_admin = is_admin()
        self.last_pasted_idx = None # Tracks last item for Undo
        self.show_password = False

        self._build_ui()
        self._refresh_list()
        self._register_hotkey()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI Build ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        BG = BG_COLOR
        CARD = CARD_COLOR
        ACCENT = ACCENT_COLOR
        TEXT = TEXT_COLOR
        MUTED = MUTED_COLOR
        DANGER = DANGER_COLOR

        # Header Container
        header_container = tk.Frame(self.root, bg=BG, pady=20)
        header_container.pack(fill="x", padx=25)

        # Logo and Title
        title_frame = tk.Frame(header_container, bg=BG)
        title_frame.pack(side="left")

        tk.Label(title_frame, text="⚡", font=("Segoe UI Emoji", 26),
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(title_frame, text="Auto-Paster",
                 font=FONT_TITLE, bg=BG, fg=TEXT).pack(side="left", padx=12)

        # Hotkey & Auto-Detect (Right Side)
        badge_container = tk.Frame(header_container, bg=BG)
        badge_container.pack(side="right")

        def toggle_auto():
            self.settings["auto_detect"] = self.auto_detect.get()
            save_settings(self.settings)
            status = "ON" if self.auto_detect.get() else "OFF"
            self._set_status(f"🔍 Auto-Detect: {status}")

        tk.Checkbutton(badge_container, text="Auto-Detect", variable=self.auto_detect,
                       command=toggle_auto, font=("Segoe UI", 8),
                       bg=BG, fg=MUTED, activebackground=BG,
                       activeforeground=ACCENT, selectcolor=BG,
                       relief="flat", bd=0, cursor="hand2").pack(side="left", padx=(0, 15))

        self.hotkey_badge = tk.Label(badge_container, text=f"⌨  {self.hotkey.upper()}",
                                     font=("Consolas", 10, "bold"), bg="#1a1a2e", fg=ACCENT,
                                     padx=12, pady=6, cursor="hand2",
                                     highlightthickness=1, highlightbackground=ACCENT)
        self.hotkey_badge.pack(side="right")
        self.hotkey_badge.bind("<Button-1>", lambda e: self._change_hotkey())

        # Admin Status Indicator
        if not self.is_admin:
            admin_lbl = tk.Label(badge_container, text="⚠ No Admin", font=("Segoe UI", 8, "bold"),
                                bg=BG, fg=DANGER)
            admin_lbl.pack(side="right", padx=(0, 10))
            admin_lbl.bind("<Button-1>", lambda e: messagebox.showwarning("Admin Required", 
                "Running without Administrator privileges may prevent pasting in emulators and some system apps."))

        # Category Pill Selector
        selector_container = tk.Frame(self.root, bg=BG)
        selector_container.pack(fill="x", padx=25, pady=(0, 20))
        
        self.cat_var = tk.StringVar(value=self.current_category)
        self.cat_buttons = {}

        pill_frame = tk.Frame(selector_container, bg="#12121f", padx=4, pady=4)
        pill_frame.pack(side="left")

        for cat in CATEGORIES:
            btn = tk.Radiobutton(pill_frame, text=cat, variable=self.cat_var, value=cat,
                               command=self._on_category_change,
                               font=("Segoe UI", 9, "bold"),
                               bg="#12121f", fg=MUTED, selectcolor="#12121f",
                               activebackground="#12121f", activeforeground=ACCENT,
                               indicatoron=False, borderwidth=0,
                               padx=18, pady=8, cursor="hand2")
            btn.pack(side="left")
            self.cat_buttons[cat] = btn
        
        # Paste Mode Selector (Next to categories)
        mode_frame = tk.Frame(selector_container, bg="#12121f", padx=4, pady=4)
        mode_frame.pack(side="right")

        def on_mode_change():
            self.settings["paste_mode"] = self.paste_mode.get()
            save_settings(self.settings)
            self._set_status(f"⚙ Mode: {self.paste_mode.get().title()}")

        for mode_val, mode_label in [("paste", "📋 Paste"), ("type", "⌨ Type")]:
            rb = tk.Radiobutton(mode_frame, text=mode_label, variable=self.paste_mode, 
                               value=mode_val, command=on_mode_change,
                               font=("Segoe UI", 8, "bold"), bg="#12121f", fg=MUTED,
                               selectcolor="#1c1c2e", activebackground="#12121f",
                               activeforeground=ACCENT, indicatoron=False, 
                               borderwidth=0, padx=12, pady=6, cursor="hand2")
            rb.pack(side="left")

        self._update_pill_visuals()

        # Stats bar
        stats_frame = tk.Frame(self.root, bg=BG)
        stats_frame.pack(fill="x", padx=25, pady=(0, 15))

        def create_stat_card(parent, label, color):
            f = tk.Frame(parent, bg=CARD, padx=15, pady=10, highlightthickness=1, highlightbackground="#1e1e2d")
            f.pack(side="left", fill="x", expand=True, padx=(0, 10) if label != "Remaining" else 0)
            tk.Label(f, text=label, font=("Segoe UI", 8, "bold"), bg=CARD, fg=MUTED).pack(anchor="w")
            val_lbl = tk.Label(f, text="0", font=("Segoe UI", 14, "bold"), bg=CARD, fg=color)
            val_lbl.pack(anchor="w")
            return val_lbl

        self.stat_total_val = create_stat_card(stats_frame, "Total Items", TEXT)
        self.stat_done_val = create_stat_card(stats_frame, "Pasted", ACCENT)
        self.stat_remaining_val = create_stat_card(stats_frame, "Remaining", "#ffb86c")

        # Progress bar
        progress_container = tk.Frame(self.root, bg=BG)
        progress_container.pack(fill="x", padx=25, pady=(0, 20))

        self.progress_var = tk.DoubleVar()
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Neon.Horizontal.TProgressbar",
                        background=ACCENT, troughcolor="#12121f",
                        bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT,
                        thickness=6)
        self.progress = ttk.Progressbar(progress_container, variable=self.progress_var,
                                        style="Neon.Horizontal.TProgressbar",
                                        maximum=100)
        self.progress.pack(fill="x")

        # Custom Scrollbar Style
        style.configure("Modern.Vertical.TScrollbar",
                        background="#1e1e2d",
                        troughcolor="#0a0a0f",
                        bordercolor="#0a0a0f",
                        arrowcolor=ACCENT,
                        gripcount=0,
                        thickness=10)
        style.map("Modern.Vertical.TScrollbar",
                  background=[("active", ACCENT), ("pressed", ACCENT)])

        # Input row
        input_container = tk.Frame(self.root, bg=BG)
        input_container.pack(fill="x", padx=25, pady=(0, 15))

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(input_container, textvariable=self.entry_var,
                              font=FONT_MONO, bg="#12121f", fg=TEXT,
                              insertbackground=ACCENT, relief="flat",
                              bd=0, highlightthickness=1,
                              highlightbackground="#1e1e2d",
                              highlightcolor=ACCENT)
        self.entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self._add_item())

        add_btn = HoverButton(input_container, text="＋", font=("Segoe UI", 14, "bold"),
                             bg=ACCENT, fg=BG, relief="flat", cursor="hand2",
                             hover_bg=TEXT, hover_fg=BG,
                             width=4, pady=0, command=self._add_item)
        add_btn.pack(side="left")

        self.bulk_btn = HoverButton(input_container, text="📋 Bulk", font=FONT_BOLD,
                              bg="#1e1e2d", fg=TEXT, relief="flat", cursor="hand2",
                              hover_bg="#2a2a3d", hover_fg=ACCENT,
                              padx=15, pady=8, command=self._bulk_add)
        self.bulk_btn.pack(side="left", padx=(8, 0))

        # List frame
        list_container = tk.Frame(self.root, bg=BG)
        list_container.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        canvas_container = tk.Frame(list_container, bg=CARD, highlightthickness=1, highlightbackground="#1e1e2d")
        canvas_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_container, bg=CARD, highlightthickness=0)
        self.scrollbar = AutoScrollbar(canvas_container, orient="vertical", 
                                 command=canvas.yview, style="Modern.Vertical.TScrollbar")
        self.list_frame = tk.Frame(canvas, bg=CARD)

        def _on_canvas_configure(e):
            # Dynamic width adjustment
            canvas.itemconfig(canvas_win, width=e.width)

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas_win = canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        canvas.bind("<Configure>", _on_canvas_configure)
        self.list_frame.bind("<Configure>", _on_frame_configure)
        canvas.configure(yscrollcommand=self.scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas = canvas

        # Bottom buttons
        footer_frame = tk.Frame(self.root, bg=BG)
        footer_frame.pack(fill="x", padx=25, pady=(0, 20))

        reset_btn = HoverButton(footer_frame, text="↺  Reset Progress", font=FONT_MAIN,
                               bg="#1a1a2e", fg=TEXT, relief="flat", cursor="hand2",
                               hover_bg="#252545", hover_fg=ACCENT,
                               padx=15, pady=8, command=self._reset_all)
        reset_btn.pack(side="left")

        clear_btn = HoverButton(footer_frame, text="🗑  Clear List", font=FONT_MAIN,
                               bg="#241216", fg=DANGER, relief="flat", cursor="hand2",
                               hover_bg=DANGER, hover_fg=TEXT_COLOR,
                               padx=15, pady=8, command=self._clear_all)
        clear_btn.pack(side="left", padx=(10, 0))

        undo_btn = HoverButton(footer_frame, text="↶  Undo Paste", font=FONT_MAIN,
                               bg="#1a1a2e", fg=ACCENT, relief="flat", cursor="hand2",
                               hover_bg="#252545", hover_fg=TEXT_COLOR,
                               padx=15, pady=8, command=self._undo_paste)
        undo_btn.pack(side="right")

        # Status bar
        self.status_var = tk.StringVar(value="Ready — Press hotkey anywhere to paste next item")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var,
                                   font=("Segoe UI", 9), bg="#030305", fg=MUTED,
                                   anchor="w", pady=8, padx=25)
        self.status_bar.pack(fill="x")

    def _update_pill_visuals(self):
        ACCENT = ACCENT_COLOR
        MUTED = MUTED_COLOR
        curr = self.cat_var.get()
        for cat, btn in self.cat_buttons.items():
            if cat == curr:
                btn.config(fg=ACCENT, font=("Segoe UI", 9, "bold"))
            else:
                btn.config(fg=MUTED, font=("Segoe UI", 9))

    def _on_category_change(self):
        self.current_category = self.cat_var.get()
        self.numbers = self.all_data[self.current_category]
        self.settings["last_category"] = self.current_category
        save_settings(self.settings)
        self._update_pill_visuals()
        
        if self.current_category == "Password":
            self.bulk_btn.pack_forget()
        else:
            self.bulk_btn.pack(side="left", padx=(8, 0))
            
        self._refresh_list()
        self._set_status(f"📂 Switched to {self.current_category}")

    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        BG = CARD_COLOR
        ACCENT = ACCENT_COLOR
        TEXT = TEXT_COLOR
        MUTED = MUTED_COLOR
        PASTED_BG = "#0d2018"
        PASTED_FG = "#2a7a5a"

        if not self.numbers:
            # Statically center the placeholder in the canvas so it doesn't scroll
            if not hasattr(self, 'placeholder') or not self.placeholder.winfo_exists():
                self.placeholder = tk.Label(self.canvas, 
                          text=f"No {self.current_category.lower()}s yet.\nAdd {self.current_category.lower()}s above ☝",
                          font=("Segoe UI", 11), bg=CARD_COLOR, fg=MUTED,
                          justify="center")
            self.placeholder.place(relx=0.5, rely=0.4, anchor="center")
        else:
            if hasattr(self, 'placeholder') and self.placeholder.winfo_exists():
                self.placeholder.place_forget()
            
            # Sort: Unpasted items at top (False < True), preserve original order within groups
            sorted_items = sorted(enumerate(self.numbers), 
                                key=lambda x: (x[1].get("pasted", False), x[0]))
            for j, (i, item) in enumerate(sorted_items):
                is_pasted = item.get("pasted", False)
                row_bg = PASTED_BG if is_pasted else BG
                fg = PASTED_FG if is_pasted else TEXT

                row = tk.Frame(self.list_frame, bg=row_bg, pady=4)
                row.pack(fill="x", padx=10, pady=2)
                
                def on_row_enter(e, r=row, p=is_pasted):
                    if not p: r.config(bg="#1a1a2e")
                def on_row_leave(e, r=row, p=is_pasted):
                    if not p: r.config(bg=BG)
                
                row.bind("<Enter>", on_row_enter)
                row.bind("<Leave>", on_row_leave)

                idx_lbl = tk.Label(row, text=f"{j+1:>3}.", font=("Consolas", 10),
                                  bg=row_bg, fg=MUTED, width=4)
                if self.current_category == "Password":
                    idx_lbl.pack_forget()
                else:
                    idx_lbl.pack(side="left", padx=(8, 0))

                display_val = item["value"]
                if self.current_category == "Password" and not self.show_password:
                    display_val = "•" * max(8, len(item["value"]))

                val_lbl = tk.Label(row, text=display_val, font=FONT_BOLD,
                                  bg=row_bg, fg=fg, anchor="w")
                val_lbl.pack(side="left", padx=12, pady=10, fill="x", expand=True)

                if self.current_category == "Password":
                    def toggle_visibility(e):
                        self.show_password = not self.show_password
                        self._refresh_list()
                    eye_icon = "👁" if not self.show_password else "🙈"
                    eye_lbl = tk.Label(row, text=eye_icon, font=("Segoe UI Emoji", 12),
                                       bg=row_bg, fg=MUTED, cursor="hand2")
                    eye_lbl.pack(side="left", padx=10)
                    eye_lbl.bind("<Button-1>", toggle_visibility)

                    tk.Label(row, text="🔁 Reusable", font=("Segoe UI", 8, "bold"),
                             bg=ACCENT_GLOW, fg=ACCENT, padx=8, pady=2).pack(side="right", padx=10)
                else:
                    if is_pasted:
                        tk.Label(row, text="✓ pasted", font=("Segoe UI", 8, "bold"),
                                 bg=PASTED_BG, fg=ACCENT, padx=8, pady=2).pack(side="right", padx=10)
                    else:
                        next_idx = self._next_index()
                        if next_idx == i:
                            tk.Label(row, text="NEXT", font=("Segoe UI", 8, "bold"),
                                     bg=ACCENT_GLOW, fg=ACCENT, padx=8, pady=2).pack(side="right", padx=10)

                tk.Button(row, text="✕", font=("Segoe UI", 9),
                          bg=row_bg, fg="#555566", relief="flat",
                          activebackground=row_bg, activeforeground=DANGER_COLOR,
                          cursor="hand2", padx=6,
                          command=lambda idx=i: self._delete_item(idx)).pack(side="right", padx=5)

        self._update_stats()
        self.canvas.after(10, lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def _on_mousewheel(self, event):
        widget = event.widget
        curr = widget
        is_child = False
        try:
            while curr:
                if curr == self.canvas:
                    is_child = True
                    break
                curr = curr.master
        except Exception:
            pass

        if is_child:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _update_stats(self):
        if self.current_category == "Password":
            self.stat_total_val.config(text="1" if self.numbers else "0")
            self.stat_done_val.config(text="∞")
            self.stat_remaining_val.config(text="∞")
            self.progress_var.set(100 if self.numbers else 0)
            return

        total = len(self.numbers)
        done = sum(1 for n in self.numbers if n.get("pasted"))
        remaining = total - done

        self.stat_total_val.config(text=str(total))
        self.stat_done_val.config(text=str(done))
        self.stat_remaining_val.config(text=str(remaining))

        pct = (done / total * 100) if total > 0 else 0
        self.progress_var.set(pct)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _next_index(self):
        for i, item in enumerate(self.numbers):
            if not item.get("pasted", False):
                return i
        return None

    def _add_item(self):
        val = self.entry_var.get().strip()
        if not val:
            return
        if self.current_category == "Password":
            self.numbers.clear()
        self.numbers.append({"value": val, "pasted": False})
        save_data(self.all_data)
        self.entry_var.set("")
        self._refresh_list()

    def _bulk_add(self):
        win = tk.Toplevel(self.root)
        win.title(f"Bulk Add {self.current_category}s")
        win.geometry("550x700")
        win.configure(bg=BG_COLOR)
        win.grab_set()

        # Header
        header = tk.Frame(win, bg=BG_COLOR, pady=20)
        header.pack(fill="x")
        
        tk.Label(header, text=f"📥 Bulk Add {self.current_category}s",
                 font=FONT_TITLE, bg=BG_COLOR, fg=TEXT_COLOR).pack()
        tk.Label(header, text="Enter one item per line",
                 font=("Segoe UI", 9), bg=BG_COLOR, fg=MUTED_COLOR).pack()

        # Container for text area and scrollbar
        text_container = tk.Frame(win, bg="#121220", padx=2, pady=2,
                                highlightthickness=1, highlightbackground="#1e1e2d")
        text_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Text area
        txt = tk.Text(text_container, font=FONT_MONO, bg="#121220", fg=TEXT_COLOR,
                      insertbackground=ACCENT_COLOR, relief="flat", bd=0,
                      padx=10, pady=10, height=12) # Reduced height
        
        sb = AutoScrollbar(text_container, orient="vertical", 
                          command=txt.yview, style="Modern.Vertical.TScrollbar")
        txt.configure(yscrollcommand=sb.set)
        
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        # Bottom Button Container
        footer = tk.Frame(win, bg=BG_COLOR, pady=20)
        footer.pack(fill="x", side="bottom")

        def do_add():
            lines = txt.get("1.0", "end").strip().splitlines()
            added = 0
            for line in lines:
                line = line.strip()
                if line:
                    self.numbers.append({"value": line, "pasted": False})
                    added += 1
            save_data(self.all_data)
            self._refresh_list()
            win.destroy()
            self._set_status(f"✓ Added {added} {self.current_category.lower()}s")

        # Buttons (Ordered so Add is on top of Cancel)
        cancel_btn = HoverButton(footer, text="Cancel", font=("Segoe UI", 9),
                                bg="#1e1e2d", fg=MUTED_COLOR, relief="flat", cursor="hand2",
                                hover_bg=DANGER_COLOR, hover_fg=TEXT_COLOR,
                                padx=20, pady=8, command=win.destroy)
        cancel_btn.pack(side="bottom", fill="x", padx=25, pady=(15, 0))

        add_btn = HoverButton(footer, text=f"Add to List", 
                             font=("Segoe UI", 11, "bold"),
                             bg=ACCENT_COLOR, fg=BG_COLOR, relief="flat", cursor="hand2",
                             hover_bg=TEXT_COLOR, hover_fg=BG_COLOR,
                             padx=40, pady=12, command=do_add)
        add_btn.pack(side="bottom", fill="x", padx=25)

    def _delete_item(self, idx):
        self.numbers.pop(idx)
        save_data(self.all_data)
        self._refresh_list()

    def _reset_all(self):
        for item in self.numbers:
            item["pasted"] = False
        save_data(self.all_data)
        self._refresh_list()
        self._set_status(f"↺ All {self.current_category.lower()}s reset")

    def _undo_paste(self):
        if self.last_pasted_idx is None:
            self._set_status("⚠ Nothing to undo")
            return
        
        idx = self.last_pasted_idx
        if 0 <= idx < len(self.numbers):
            item = self.numbers[idx]
            if item.get("pasted"):
                item["pasted"] = False
                save_data(self.all_data)
                self.last_pasted_idx = None
                self._refresh_list()
                self._update_stats()
                self._set_status(f"↶ Undo: '{item['value'][:15]}...' is now NEXT")
                return
        
        self._set_status("⚠ Could not undo (item moved or deleted)")
        self.last_pasted_idx = None

    def _clear_all(self):
        if messagebox.askyesno("Clear All", f"Delete all {self.current_category.lower()}s?"):
            self.numbers.clear()
            self.all_data[self.current_category] = [] # Ensure it's empty
            save_data(self.all_data)
            self._refresh_list()

    def _set_status(self, msg):
        self.status_var.set(msg)
        self.root.after(3000, lambda: self.status_var.set(
            "Ready — Press hotkey anywhere to paste next item"))

    # ── Paste Logic ───────────────────────────────────────────────────────────
    def _detect_context(self):
        """Attempts to detect the current input field type globally."""
        if not self.auto_detect.get(): return None
        try:
            focused = auto.GetFocusedControl()
            if not focused: 
                self.root.after(0, lambda: self._set_status("🔍 No focused field detected"))
                return None
            
            name = str(focused.Name).lower()
            auto_id = str(focused.AutomationId).lower()
            cls_name = str(focused.ClassName).lower()
            full_text = f"{name} {auto_id} {cls_name}"
            
            if any(k in full_text for k in ["mail", "email", "e-mail", "address"]): return "Email"
            if any(k in full_text for k in ["phone", "number", "tel", "mobile", "cell", "contact", "digit"]): return "Phone"
            if any(k in full_text for k in ["name", "user", "id", "first", "last", "profile"]): return "Name"
            if any(k in full_text for k in ["pass", "pwd", "password", "pin", "secret"]): return "Password"
            
            found_msg = f"🔍 Found: {name[:12]}... (No category match)"
            self.root.after(0, lambda: self._set_status(found_msg))
        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"🔍 Error: {e}"))
        return None

    def _do_paste(self):
        # COM must be initialized in each thread for uiautomation to work
        with auto.UIAutomationInitializerInThread():
            # Determine category (Manual or Auto-Detect)
            target_category = self.current_category
            detected = self._detect_context()
        
        if detected:
            target_category = detected
            # Temporarily switch visual focus if possible
            # We use a separate local context for this paste
            self.root.after(0, lambda: self._set_status(f"🔍 Auto-detected: {detected}"))

        # Re-fetch data for the resolved category
        current_list = self.all_data.get(target_category, [])
        if not current_list:
            if detected:
                self._set_status(f"⚠ Detected {detected} but list is empty")
            return

        # Find first unpasted item in THAT specific category
        idx = -1
        if target_category == "Password":
            if current_list:
                idx = 0
        else:
            for i, item in enumerate(current_list):
                if not item.get("pasted", False):
                    idx = i
                    break

        if idx == -1:
            self._set_status(f"✓ All {target_category} items pasted")
            return

        number = current_list[idx]["value"]

        # ── Focus Safety Check ──────────────────────────────────────────
        # If the focused window is our app, abort to prevent accidental counts
        try:
            focused = auto.GetFocusedControl()
            if focused:
                top_window = focused.GetTopLevelWindow()
                if top_window and top_window.Name == "📱 Auto-Paster":
                    self.root.after(0, lambda: self._set_status("⚠ Aborted: Cannot paste inside Auto-Paster"))
                    return
        except Exception:
            pass
        
        # Determine Output Mode
        mode = self.paste_mode.get()
        
        # Execute Output Action
        success = True
        try:
            if mode == "type":
                time.sleep(0.1)
                keyboard.write(number, delay=0.01)
            else:
                pyperclip.copy(number)
                time.sleep(0.05)
                keyboard.release('shift')
                keyboard.release('alt')
                keyboard.press('ctrl')
                keyboard.press('v')
                time.sleep(0.05)
                keyboard.release('v')
                keyboard.release('ctrl')
        except Exception as e:
            success = False
            self.root.after(0, lambda err=e: self._set_status(f"⚠ Error: {err}"))

        if success:
            # ✅ Success: Mark as pasted and update stats
            if target_category != "Password":
                current_list[idx]["pasted"] = True
                self.last_pasted_idx = idx
                save_data(self.all_data)
            
            self.root.after(0, self._refresh_list)
            self.root.after(0, self._update_stats)
            self.root.after(0, lambda: self._set_status(
                f"✓ {'Typed' if mode == 'type' else 'Pasted'} ({target_category}): {'***' if target_category == 'Password' else number[:15]}..."))

    # ── Hotkey ────────────────────────────────────────────────────────────────
    def _register_hotkey(self):
        if not KEYBOARD_AVAILABLE:
            messagebox.showwarning("Warning", "Keyboard library not installed. Global hotkeys will not work.")
            return
        try:
            if self.hotkey_registered:
                keyboard.unhook_all()
            
            keyboard.add_hotkey(self.hotkey, lambda: threading.Thread(
                target=self._do_paste, daemon=True).start())
            self.hotkey_registered = True
        except Exception as e:
            error_msg = f"⚠ Hotkey Error: {e}"
            self._set_status(error_msg)
            messagebox.showerror("Hotkey Error", f"Could not register '{self.hotkey.upper()}'.\nError: {e}\n\nPlease try running the CMD as Administrator.")

    def _change_hotkey(self):
        win = tk.Toplevel(self.root)
        win.title("Record Shortcut")
        win.geometry("440x380")
        win.configure(bg=BG_COLOR)
        win.grab_set()

        header = tk.Frame(win, bg=BG_COLOR, pady=25)
        header.pack(fill="x")
        
        tk.Label(header, text="⌨ Record Shortcut",
                 font=FONT_TITLE, bg=BG_COLOR, fg=TEXT_COLOR).pack()
        
        desc_lbl = tk.Label(win, text="Press the combination you want to use\n(e.g., Ctrl + Shift + V)",
                 font=("Segoe UI", 9), bg=BG_COLOR, fg=MUTED_COLOR)
        desc_lbl.pack(pady=(0, 20))

        # Visual Key Display
        key_display_frame = tk.Frame(win, bg="#121220", padx=20, pady=30,
                                   highlightthickness=1, highlightbackground=ACCENT_COLOR)
        key_display_frame.pack(fill="x", padx=40)

        recording_var = tk.StringVar(value="...")
        key_lbl = tk.Label(key_display_frame, textvariable=recording_var, 
                          font=("Consolas", 18, "bold"), bg="#121220", fg=ACCENT_COLOR)
        key_lbl.pack()

        status_lbl = tk.Label(win, text="Listening for keys...", font=("Segoe UI", 9, "italic"),
                             bg=BG_COLOR, fg=ACCENT_COLOR)
        status_lbl.pack(pady=15)

        recording = True
        current_keys = set()

        def update_ui():
            if not recording: return
            if not KEYBOARD_AVAILABLE: return
            
            # Using keyboard library to get current pressed keys
            try:
                # We catch the current combination
                import keyboard as k
                # This is a bit of a hacky way but works well for UI
                # We want to see what is currently pressed
                keys = []
                for action in ['ctrl', 'shift', 'alt', 'windows']:
                    if k.is_pressed(action):
                        keys.append(action.title())
                
                # Check for other keys
                # This is just for visual feedback
                recording_var.set(" + ".join(keys) if keys else "Waiting...")
            except:
                pass
            
            if recording:
                win.after(50, update_ui)

        def on_key_recorded(event):
            nonlocal recording
            if not recording: return
            
            try:
                # Read the full hotkey string
                new_hotkey = k.get_hotkey_name()
                if new_hotkey and len(new_hotkey) > 1:
                    recording = False
                    self.hotkey = new_hotkey.lower()
                    self.settings["hotkey"] = self.hotkey
                    save_settings(self.settings)
                    self.hotkey_badge.config(text=f"⌨  {self.hotkey.upper()}")
                    self._register_hotkey()
                    self._set_status(f"✓ Shortcut updated: {self.hotkey.upper()}")
                    
                    # Final visual feedback before closing
                    recording_var.set(self.hotkey.upper())
                    status_lbl.config(text="Saved successfully!", fg="#00ff00")
                    win.after(800, win.destroy)
            except:
                pass

        if KEYBOARD_AVAILABLE:
            import keyboard as k
            # We use a one-time hook to capture the next hotkey
            # keyboard.read_hotkey() blocks, so we'll use a thread or hook logic
            
            def track():
                shortcut = k.read_hotkey(suppress=False)
                if shortcut:
                    self.root.after(0, lambda s=shortcut: finish_recording(s))

            def finish_recording(shortcut):
                nonlocal recording
                recording = False
                self.hotkey = shortcut.lower()
                self.settings["hotkey"] = self.hotkey
                save_settings(self.settings)
                self.hotkey_badge.config(text=f"⌨  {self.hotkey.upper()}")
                self._register_hotkey()
                self._set_status(f"✓ Shortcut updated: {self.hotkey.upper()}")
                
                recording_var.set(self.hotkey.upper())
                status_lbl.config(text="Saved successfully!", fg="#00ff00")
                win.after(800, win.destroy)

            threading.Thread(target=track, daemon=True).start()
            update_ui()
        else:
            recording_var.set("ERROR")
            status_lbl.config(text="Keyboard library not found", fg=DANGER_COLOR)

        cancel_btn = HoverButton(win, text="Cancel", font=("Segoe UI", 9),
                                bg="#1e1e2d", fg=MUTED_COLOR, relief="flat", cursor="hand2",
                                hover_bg=DANGER_COLOR, hover_fg=TEXT_COLOR,
                                padx=20, pady=8, command=win.destroy)
        cancel_btn.pack(side="bottom", pady=20)

    def _on_close(self):
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.remove_all_hotkeys()
            except Exception:
                pass
        self.root.destroy()

# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = PhonePasterApp(root)
    root.mainloop()
