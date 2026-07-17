#!/usr/bin/env python3
# ==============================================================================
# LimboOS Desktop Environment v2.0 — Final Concept Edition
# Matching the "Limbo•OS" concept screenshots:
#   - Blue desktop with diagonal "LIMBO•OS" watermark
#   - App icons: gradient squares (grey→blue) with app name below
#   - Taskbar: [■ Start Menu] [open app icons A, B...] [clock + date]
#   - Windows: grey body + gradient titlebar + yellow X button
# ==============================================================================

import os
import sys
import time
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox


# ── Theme (matching concept) ──────────────────────────────────────────────────
COLOR_BG = "#00AADD"
COLOR_WATERMARK = "#0088BB"
COLOR_TASKBAR = "#B0B0B0"
COLOR_WINDOW_BG = "#A0A0A0"
COLOR_TITLEBAR_START = "#888888"
COLOR_TITLEBAR_END = "#0000CC"
COLOR_ICON_BG_START = "#303030"
COLOR_ICON_BG_END = "#0000CC"
COLOR_ICON_TEXT = "#FFFFFF"
COLOR_BTN_X = "#FFFF00"
COLOR_START_BTN = "#303030"
COLOR_MENU_BG = "#909090"

FONT_MONO = "Courier"
FONT_SANS = "Arial"

# ── Built-in apps (each has: letter, name, icon_color, function) ──────────────
BUILTIN_APPS = [
    {"id": "snake",    "letter": "S", "name": "Snake",       "desc": "Retro Snake Game"},
    {"id": "matrix",   "letter": "M", "name": "Matrix",      "desc": "Cyber Matrix Rain"},
    {"id": "clock",    "letter": "C", "name": "Clock",       "desc": "ASCII Digital Clock"},
    {"id": "sysstat",  "letter": "D", "name": "Diagnostics", "desc": "Hardware Diagnostic"},
    {"id": "files",    "letter": "F", "name": "Files",       "desc": "File Explorer"},
    {"id": "terminal", "letter": "T", "name": "Terminal",    "desc": "Linux Shell"},
    {"id": "notepad",  "letter": "N", "name": "Notepad",     "desc": "Text Editor"},
    {"id": "calc",     "letter": "K", "name": "Calculator",  "desc": "Math & Benchmark"},
    {"id": "chat",     "letter": "A", "name": "AI Chat",     "desc": "Neural Assistant"},
    {"id": "store",    "letter": "P", "name": "App Store",   "desc": "lpkg Store"},
    {"id": "settings", "letter": "G", "name": "Settings",    "desc": "System Settings"},
    {"id": "update",   "letter": "U", "name": "Updates",     "desc": "OTA Update Check"},
]


def interpolate(c1, c2, t):
    """Interpolate between two hex colors."""
    c1 = tuple(int(c1[i:i+2], 16) for i in (1, 3, 5))
    c2 = tuple(int(c2[i:i+2], 16) for i in (1, 3, 5))
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Window ────────────────────────────────────────────────────────────────────
class LimboWindow:
    """Floating window: grey body + gradient titlebar + yellow X."""

    _z_counter = 0

    def __init__(self, desktop, title, width=380, height=260):
        self.desktop = desktop
        self.c = desktop.canvas
        self.title = title
        self.w = width
        self.h = height
        LimboWindow._z_counter += 1
        self.z = LimboWindow._z_counter

        # Position with cascade
        idx = len(desktop.windows)
        self.x = 60 + idx * 22
        self.y = 40 + idx * 16
        self.tag = f"w{self.z}"

        self._draw()
        desktop.windows.append(self)
        desktop._refresh_taskbar()

    # ── Draw window ───────────────────────────────────────────────────────────
    def _draw(self):
        c, x, y, w, h, z, tag = self.c, self.x, self.y, self.w, self.h, self.z, self.tag

        # Shadow
        c.create_rectangle(x+4, y+4, x+w+4, y+h+4, fill="#00000022", tag=tag)

        # Body (grey)
        c.create_rectangle(x, y, x+w, y+h, fill=COLOR_WINDOW_BG, outline="#666666", width=1, tag=tag)

        # Titlebar gradient
        th = 26
        for i in range(th):
            t = i / max(th - 1, 1)
            c.create_line(x, y + i, x + w, y + i,
                          fill=interpolate(COLOR_TITLEBAR_START, COLOR_TITLEBAR_END, t), tag=tag)

        # Title text
        c.create_text(x + 8, y + th // 2 + 1, text=self.title,
                      fill="white", font=(FONT_MONO, 10, "bold"), anchor="w", tag=tag)

        # Yellow X button
        bx, by = x + w - 20, y + 4
        c.create_rectangle(bx, by, bx + 16, by + 18, fill=COLOR_BTN_X, outline="#CC9900", tag=tag)
        c.create_text(bx + 8, by + 10, text="X", fill="black", font=(FONT_MONO, 9, "bold"), tag=tag)
        c.tag_bind(tag, "<Button-1>", self._on_click)

        # Content area coords
        self.cx = x + 10
        self.cy = y + th + 8
        self.cw = w - 20
        self.ch = h - th - 16

    def _on_click(self, event):
        cx = self.c.canvasx(event.x)
        cy = self.c.canvasy(event.y)
        bx = self.x + self.w - 20
        by = self.y + 4
        if bx <= cx <= bx + 16 and by <= cy <= by + 18:
            self.close()
            return
        # Drag titlebar
        if self.y <= cy <= self.y + 26:
            self._dragging = True
            self._drag_off = (cx - self.x, cy - self.y)
            self._bring_front()
            return
        self._bring_front()

    def _bring_front(self):
        LimboWindow._z_counter += 1
        self.z = LimboWindow._z_counter
        self.tag = f"w{self.z}"
        # Re-tag all items (simple approach: redraw)
        # In practice we'd re-tag, but for simplicity we just re-order via lift
        # Tkinter canvas doesn't have great z-order per-tag, so we use a workaround:
        # We'll just keep the tag and accept overlapping order

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.c.move(self.tag, dx, dy)

    def add_text_area(self, text):
        """Scrollable text inside window."""
        frame = tk.Frame(self.c, bg=COLOR_WINDOW_BG)
        tw = scrolledtext.ScrolledText(
            frame, bg="#999999", fg="#333333",
            font=(FONT_MONO, 10), wrap=tk.WORD,
            width=self.cw // 7, height=self.ch // 16,
            bd=0, relief=tk.FLAT
        )
        tw.pack(fill=tk.BOTH, expand=True)
        tw.insert(tk.END, text)
        tw.configure(state=tk.DISABLED)
        self.c.create_window(
            self.cx, self.cy, window=frame,
            anchor="nw", width=self.cw, height=self.ch, tag=self.tag
        )

    def add_lines(self, lines):
        """Draw simple text lines inside window."""
        for i, line in enumerate(lines):
            self.c.create_text(
                self.cx + 10, self.cy + 15 + i * 22,
                text=line, fill="#555555",
                font=(FONT_MONO, 14), anchor="nw", tag=self.tag
            )

    def close(self):
        self.c.delete(self.tag)
        if self in self.desktop.windows:
            self.desktop.windows.remove(self)
        self.desktop._refresh_taskbar()


# ── Desktop ───────────────────────────────────────────────────────────────────
class LimboOSDesktop(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("LimboOS")
        self.W, self.H = 800, 600
        self.geometry(f"{self.W}x{self.H}+0+0")
        self.resizable(False, False)
        self.configure(bg="#000000")

        self.windows = []
        self.open_apps = []      # list of (app_dict, window)
        self.menu_open = False
        self.icon_size = 64
        self.icon_spacing_x = 90
        self.icon_spacing_y = 95
        self.icon_start_x = 50
        self.icon_start_y = 30

        # Main canvas (desktop area, above taskbar)
        self.canvas = tk.Canvas(self, width=self.W, height=self.H - 32,
                                highlightthickness=0, bg=COLOR_BG)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Build UI
        self._draw_watermark()
        self._draw_app_icons()
        self._draw_taskbar()
        self._update_clock()

        # Canvas drag binding for windows
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self._dragging_window = None

    # ── Watermark ─────────────────────────────────────────────────────────────
    def _draw_watermark(self):
        c = self.canvas
        c.create_rectangle(0, 0, self.W, self.H - 32, fill=COLOR_BG, outline="")
        text = "LIMBO•OS"
        for row in range(-3, 10):
            for col in range(-2, 8):
                x = col * 210 + 100 + (row % 2) * 105
                y = row * 70 + 120
                c.create_text(x, y, text=text,
                              fill=COLOR_WATERMARK,
                              font=(FONT_SANS, 26, "bold"),
                              angle=-25)

    # ── App Icons Grid ────────────────────────────────────────────────────────
    def _draw_app_icons(self):
        """Draw app icons: gradient squares with letter + name below."""
        c = self.canvas
        cols = 7  # 7 icons per row
        self._icon_rects = {}

        for i, app in enumerate(BUILTIN_APPS):
            row = i // cols
            col = i % cols
            x = self.icon_start_x + col * self.icon_spacing_x
            y = self.icon_start_y + row * self.icon_spacing_y
            s = self.icon_size

            # Gradient square
            for j in range(s):
                t = j / max(s - 1, 1)
                c.create_line(x, y + j, x + s, y + j,
                              fill=interpolate(COLOR_ICON_BG_START, COLOR_ICON_BG_END, t))

            # Border
            c.create_rectangle(x, y, x + s, y + s, outline="#000055", width=1)

            # Letter in center
            c.create_text(x + s // 2, y + s // 2 - 4,
                          text=app["letter"],
                          fill=COLOR_ICON_TEXT, font=(FONT_MONO, 24, "bold"))

            # App name below icon
            c.create_text(x + s // 2, y + s + 12,
                          text=app["name"],
                          fill="white", font=(FONT_SANS, 9))

            # Clickable area
            area_tag = f"icon_{app['id']}"
            c.create_rectangle(x - 5, y - 5, x + s + 5, y + s + 20,
                               fill="", outline="", tag=area_tag)
            c.tag_bind(area_tag, "<Button-1>", lambda e, a=app: self._launch_app(a))
            self._icon_rects[app["id"]] = (x, y, s)

    def _launch_app(self, app):
        """Open app window."""
        win = LimboWindow(self, app["name"], width=380, height=260)

        # Generate content based on app id
        content = self._get_app_content(app["id"])
        win.add_lines(content)

        self.open_apps.append((app, win))
        self._refresh_taskbar()

    def _get_app_content(self, app_id):
        """Return text lines for each app window."""
        contents = {
            "snake":    ["APP CONTENT...", "APP CONTENT...", "APP CONTENT...",
                         "", "(Snake game would run here)"],
            "matrix":   ["APP CONTENT...", "APP CONTENT...", "APP CONTENT...",
                         "", "(Matrix rain effect)"],
            "clock":    ["APP CONTENT...", "APP CONTENT...", "APP CONTENT...",
                         "", "(ASCII clock display)"],
            "sysstat":  ["APP CONTENT...", "APP CONTENT...", "APP CONTENT...",
                         "", "(Hardware diagnostics)"],
            "files":    ["LimboOS File Explorer", "", "/home/user",
                         "├── .bashrc", "├── notes.txt", "├── bin/",
                         "", "[Disk: /dev/sda1 qcow2]"],
            "terminal": ["limboos:~$ uname -a",
                         "Linux limboos 6.1.0 x86_64",
                         "", "limboos:~$ lpkg list",
                         "  snake    Retro Snake Game",
                         "  matrix   Cyber Matrix Rain",
                         "  clock    ASCII Clock",
                         "", "limboos:~$ _"],
            "notepad":  ["# LimboOS Notes", "", "Type here...",
                         "", "[File saved to /home/user/]"],
            "calc":     ["=== Calculator ===", "", "0",
                         "", "[7] [8] [9] [/]",
                         "[4] [5] [6] [*]",
                         "[1] [2] [3] [-]",
                         "[C] [0] [=] [+]"],
            "chat":     ["🤖 LimboOS AI Assistant", "",
                         "Ask me anything!",
                         "", "You: ___",
                         "[Send]"],
            "store":    ["=== lpkg App Store ===", "",
                         "Available:",
                         "  ✅ snake   v1.0  Games",
                         "  ✅ matrix  v1.0  Demos",
                         "  ✅ clock   v1.0  Utils",
                         "", "lpkg install <name>"],
            "settings": ["LimboOS Settings", "",
                         "Version: 1.0.0 (Genesis)",
                         "Kernel: Linux 6.1 LTS",
                         "GUI: Concept v2.0",
                         "Disk: qcow2 persistent",
                         "PM: lpkg v1.0"],
            "update":   ["Checking for updates...", "",
                         "Repo: GlomGing85/LimboOS.Repo",
                         "Current: v1.0.0",
                         "Latest:  v1.0.0",
                         "", "✅ System is up to date!"],
        }
        return contents.get(app_id, ["APP CONTENT...", "APP CONTENT...", "APP CONTENT..."])

    # ─ Taskbar ───────────────────────────────────────────────────────────────
    def _draw_taskbar(self):
        c = self.canvas
        ty = self.H - 32

        # Background
        c.create_rectangle(0, ty, self.W, self.H, fill=COLOR_TASKBAR, outline="")
        c.create_line(0, ty, self.W, ty, fill="#888888")

        # Start button (■ black square)
        self.start_btn_tag = "start_btn"
        c.create_rectangle(10, ty + 4, 34, ty + 28,
                           fill=COLOR_START_BTN, outline="#606060", width=1,
                           tag=self.start_btn_tag)
        c.tag_bind(self.start_btn_tag, "<Button-1>", self._toggle_menu)

        # Open apps area (starts after start button)
        self._taskbar_apps_x = 42

        # Clock area (right side)
        self.clock_id = c.create_text(self.W - 50, ty + 14,
                                       text="", fill="black",
                                       font=(FONT_MONO, 10, "bold"))
        self.date_id = c.create_text(self.W - 50, ty + 26,
                                      text="", fill="black",
                                      font=(FONT_MONO, 8))

    def _refresh_taskbar(self):
        """Update open app icons on taskbar."""
        c = self.canvas
        c.delete("tb_app")
        x = self._taskbar_apps_x
        ty = self.H - 32

        for app, win in self.open_apps:
            s = 22
            c.create_rectangle(x, ty + 5, x + s, ty + 27,
                               fill="#707070", outline="#505050", width=1,
                               tag="tb_app")
            c.create_text(x + s // 2, ty + 16,
                          text=app["letter"],
                          fill="white", font=(FONT_MONO, 11, "bold"),
                          tag="tb_app")
            c.tag_bind("tb_app", "<Button-1>",
                       lambda e, w=win: self._focus_or_close(w))
            x += s + 4

    def _focus_or_close(self, win):
        """Click on taskbar app: right-click close, left-click focus."""
        # For simplicity: just bring to front (close handled by X button)
        pass

    def _update_clock(self):
        now = time.localtime()
        t = f"{now.tm_hour:02d}:{now.tm_min:02d}"
        d = f"{now.tm_mday:02d}.{now.tm_mon:02d}.{now.tm_year % 100:02d}"
        self.canvas.itemconfig(self.clock_id, text=t)
        self.canvas.itemconfig(self.date_id, text=d)
        self.after(1000, self._update_clock)

    # ─ Start Menu (■ button) ────────────────────────────────────────────────
    def _toggle_menu(self, event=None):
        if self.menu_open:
            self._close_menu()
        else:
            self._open_menu()

    def _open_menu(self):
        self.menu_open = True
        c = self.canvas
        mw, mh = 200, 220
        mx, my = 10, self.H - 32 - mh - 4

        # Menu background
        c.create_rectangle(mx, my, mx + mw, my + mh,
                           fill=COLOR_MENU_BG, outline="#606060", width=2, tag="menu")

        # Title
        c.create_text(mx + mw // 2, my + 18,
                      text="LimboOS Menu",
                      fill="white", font=(FONT_MONO, 11, "bold"), tag="menu")

        # Separator
        c.create_line(mx + 5, my + 30, mx + mw - 5, my + 30,
                      fill="#707070", tag="menu")

        # Menu items
        items = [
            ("📁 File Explorer", self._launch_by_id("files")),
            (" Terminal", self._launch_by_id("terminal")),
            ("📝 Notepad", self._launch_by_id("notepad")),
            (" App Store (lpkg)", self._launch_by_id("store")),
            ("⚙️ Settings", self._launch_by_id("settings")),
            (" Check Updates", self._launch_by_id("update")),
            ("───", None),
            ("🔴 Exit LimboOS", self._exit),
        ]

        for i, (text, cmd) in enumerate(items):
            y = my + 42 + i * 22
            if text == "───":
                c.create_line(mx + 10, y, mx + mw - 10, y, fill="#707070", tag="menu")
                continue
            item_tag = f"menu_item_{i}"
            c.create_rectangle(mx + 5, y - 10, mx + mw - 5, y + 8,
                               fill="#808080", outline="", tag=item_tag)
            c.create_text(mx + 15, y, text=text,
                          fill="white", font=(FONT_SANS, 9), anchor="w", tag=item_tag)
            if cmd:
                c.tag_bind(item_tag, "<Button-1>",
                           lambda e, c=cmd: (self._close_menu(), c()))

    def _close_menu(self):
        self.menu_open = False
        self.canvas.delete("menu")
        # Delete individual item tags
        for i in range(20):
            self.canvas.delete(f"menu_item_{i}")

    def _launch_by_id(self, app_id):
        """Return a function that launches the app by id."""
        def _launch():
            for app in BUILTIN_APPS:
                if app["id"] == app_id:
                    self._launch_app(app)
                    return
        return _launch

    def _exit(self):
        if messagebox.askyesno("Exit", "Exit LimboOS Desktop?"):
            self.destroy()
            sys.exit(0)

    # ── Window dragging ───────────────────────────────────────────────────────
    def _on_drag(self, event):
        if self._dragging_window:
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            dx = cx - self._dragging_window.x - self._drag_off[0]
            dy = cy - self._dragging_window.y - self._drag_off[1]
            self._dragging_window.move(dx, dy)
            self._drag_off = (cx - self._dragging_window.x, cy - self._dragging_window.y)

    def _on_drag_end(self, event):
        self._dragging_window = None


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = LimboOSDesktop()
    app.mainloop()
