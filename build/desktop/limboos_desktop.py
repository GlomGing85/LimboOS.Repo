#!/usr/bin/env python3
# ==============================================================================
# LimboOS Linux Custom Desktop Environment & GUI Shell v1.0
# Written from scratch in Python 3 (Tkinter / X11) as a 100% Custom GUI layer
# sitting directly on top of the Linux Kernel (vmlinuz / minimal rootfs).
# ==============================================================================

import os
import sys
import time
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


class LimboOSDesktop(tk.Tk):
    """Main LimboOS Desktop Environment - Custom GUI Shell."""

    def __init__(self):
        super().__init__()
        self.title("LimboOS Custom Linux Desktop v1.0")

        # Make fullscreen / borderless or fixed size for X11 kiosk mode
        self.geometry("1024x768+0+0")
        self.configure(bg="#008080")  # Classic Retro Cyber Teal Background

        # State variables
        self.open_windows = {}
        self.start_menu_open = False

        # Load installed apps registry
        self.installed_apps = self._load_installed_apps()

        # Setup GUI Layers
        self.create_desktop_background()
        self.create_top_bar()
        self.create_taskbar()
        self.create_desktop_icons()

        # Auto-launch System Diagnostics on startup
        self.after(500, self.open_app_sysinfo)

    # ==========================================================================
    # GUI Layer: Desktop Background
    # ==========================================================================
    def create_desktop_background(self):
        self.desktop_area = tk.Frame(self, bg="#008080")
        self.desktop_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        banner_txt = (
            " __    _       _          _____ _____ \n"
            "|  |  |_|_____| |_ ___   |     |   __|\n"
            "|  |__| |     | . | . |  |  |  |__   |\n"
            "|_____|_|_|_|_|___|___|  |_____|_____|\n\n"
            "LimboOS Custom Linux Build — Pure Kernel + Custom GUI Shell"
        )
        watermark = tk.Label(
            self.desktop_area, text=banner_txt,
            bg="#008080", fg="#00A0A0",
            font=("Monospace", 14, "bold"), justify=tk.CENTER
        )
        watermark.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    # ==========================================================================
    # GUI Layer: Top Bar (System Info)
    # ==========================================================================
    def create_top_bar(self):
        self.top_bar = tk.Frame(self, bg="#001830", height=26)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        self.top_bar.pack_propagate(False)

        title_lbl = tk.Label(
            self.top_bar,
            text=" [ LimboOS Linux v1.0 ]   Kernel: Pure Linux x86/x86_64   |   GUI: 100% Custom Built Shell ",
            bg="#001830", fg="#00FFFF", font=("Sans", 10, "bold")
        )
        title_lbl.pack(side=tk.LEFT, padx=10, pady=2)

        self.status_lbl = tk.Label(
            self.top_bar,
            text=" [ ONLINE | Limbo Emulation Core: Active ] ",
            bg="#001830", fg="#55FF55", font=("Sans", 9, "bold")
        )
        self.status_lbl.pack(side=tk.RIGHT, padx=10, pady=2)

    # ==========================================================================
    # GUI Layer: Taskbar (Bottom)
    # ==========================================================================
    def create_taskbar(self):
        self.taskbar = tk.Frame(self, bg="#1F2428", height=36, bd=2, relief=tk.RAISED)
        self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.taskbar.pack_propagate(False)

        # Start Button
        self.start_btn = tk.Button(
            self.taskbar, text=" ★ [ LimboOS Menu ] ",
            bg="#006699", fg="#FFFFFF",
            activebackground="#008080", activeforeground="#FFFFFF",
            font=("Sans", 10, "bold"), relief=tk.RAISED, bd=2,
            command=self.toggle_start_menu
        )
        self.start_btn.pack(side=tk.LEFT, padx=6, pady=4)

        # Window Tabs Frame
        self.tabs_frame = tk.Frame(self.taskbar, bg="#1F2428")
        self.tabs_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Clock & Memory Widget
        self.clock_lbl = tk.Label(
            self.taskbar, text="",
            bg="#1F2428", fg="#FFFFFF", font=("Monospace", 10, "bold")
        )
        self.clock_lbl.pack(side=tk.RIGHT, padx=10, pady=4)
        self.update_clock_and_mem()

    def update_clock_and_mem(self):
        now_str = time.strftime("%H:%M:%S | %a %d %b")

        # Read memory from /proc/meminfo if available
        mem_str = "RAM: ~48 MB"
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            tot = avail = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    tot = int(line.split()[1]) // 1024
                elif line.startswith("MemAvailable:"):
                    avail = int(line.split()[1]) // 1024
            if tot > 0:
                used = tot - avail
                mem_str = f"RAM: {used} MB / {tot} MB"
        except Exception:
            pass

        self.clock_lbl.configure(text=f" {mem_str}   |   {now_str} ")
        self.after(1000, self.update_clock_and_mem)

    # ==========================================================================
    # Desktop Icons
    # ==========================================================================
    def create_desktop_icons(self):
        icons = [
            ("★ System Diagnostics\n(ASCII Banner & Hardware)", self.open_app_sysinfo),
            ("📁 LimboOS File Explorer\n(Browse Linux RootFS)", self.open_app_files),
            ("🤖 LimboOS AI Assistant\n(Neural Chat Simulator)", self.open_app_chat),
            ("📝 Custom Retro AI-Pad\n(Text Editor & Notes)", self.open_app_notepad),
            ("⚡ Math & Benchmarks\n(FLOPS CPU Speed Test)", self.open_app_calc),
            ("💻 Terminal Shell\n(Pure Linux Command Line)", self.open_app_term),
            ("📦 LimboOS App Store\n(lpkg Store)", self.open_app_store),
        ]

        # Also add dynamically installed apps from lpkg
        for pkg_id, info in self.installed_apps.items():
            if pkg_id not in [ic[0].split("\n")[0] for ic in icons]:
                icons.append((
                    f"📦 {info.get('name', pkg_id)}\n(Installed via lpkg)",
                    lambda cmd=info.get('cmd', f'xterm -e {pkg_id}'): self._run_external(cmd)
                ))

        y_pos = 20
        for label_text, cmd in icons:
            icon_btn = tk.Button(
                self.desktop_area, text=label_text,
                bg="#006060", fg="#FFFFFF",
                activebackground="#00A0A0", activeforeground="#FFFFFF",
                font=("Sans", 9, "bold"), relief=tk.RAISED, bd=3, width=25, height=2,
                command=cmd
            )
            icon_btn.place(x=25, y=y_pos)
            y_pos += 65

    def _run_external(self, cmd):
        """Run an external command (installed app)."""
        try:
            subprocess.Popen(cmd, shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot launch app:\n{e}")

    def _load_installed_apps(self):
        """Load lpkg installed apps registry."""
        db_path = os.path.expanduser("~/bin/limboos_installed_apps.json")
        try:
            if os.path.exists(db_path):
                with open(db_path, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    # ==========================================================================
    # Start Menu
    # ==========================================================================
    def toggle_start_menu(self):
        if self.start_menu_open:
            self.close_start_menu()
        else:
            self.open_start_menu()

    def open_start_menu(self):
        self.start_menu_open = True
        self.start_menu = tk.Frame(self, bg="#101820", bd=3, relief=tk.RAISED, width=300)
        self.start_menu.place(x=5, y=self.winfo_height() - 36 - 340, width=300, height=340)
        self.start_menu.lift()

        header = tk.Label(
            self.start_menu, text=" LimboOS Custom Linux Menu ",
            bg="#004080", fg="#FFFFFF", font=("Sans", 11, "bold"), pady=6
        )
        header.pack(fill=tk.X)

        menu_items = [
            ("★ System Diagnostics (ASCII Banner)", self.open_app_sysinfo),
            ("📁 LimboOS File Explorer (RootFS)", self.open_app_files),
            ("🤖 LimboOS AI Chat Assistant", self.open_app_chat),
            ("📝 Retro AI-Pad Text Editor", self.open_app_notepad),
            ("⚡ Math Calculator & CPU Bench", self.open_app_calc),
            ("💻 Linux Terminal Shell", self.open_app_term),
            ("📦 LimboOS App Store (lpkg)", self.open_app_store),
            ("---", None),
            ("🔄 Check for Updates (OTA)", self.open_ota_check),
            ("⚙️ LimboOS Settings", self.open_settings),
            ("---", None),
            ("🔴 Shutdown / Exit LimboOS GUI", self.exit_gui),
        ]

        for text, cmd in menu_items:
            if text == "---":
                ttk.Separator(self.start_menu, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)
            else:
                btn = tk.Button(
                    self.start_menu, text=f"  {text}",
                    bg="#101820", fg="#FFFFFF",
                    activebackground="#008080", activeforeground="#FFFFFF",
                    font=("Sans", 9), anchor=tk.W, relief=tk.FLAT, bd=1,
                    command=lambda c=cmd: (self.close_start_menu(), c() if c else None)
                )
                btn.pack(fill=tk.X, padx=4, pady=1)

    def close_start_menu(self):
        if hasattr(self, 'start_menu') and self.start_menu:
            self.start_menu.destroy()
        self.start_menu_open = False

    # ==========================================================================
    # Custom Window Manager
    # ==========================================================================
    def create_custom_window(self, title, width=580, height=420):
        win = tk.Toplevel(self)
        win.title(title)
        x_off = 160 + len(self.open_windows) * 25
        y_off = 50 + len(self.open_windows) * 25
        win.geometry(f"{width}x{height}+{x_off}+{y_off}")
        win.configure(bg="#2D333B")
        win.transient(self)
        win.lift()

        win_id = id(win)
        self.open_windows[win_id] = win
        self.update_taskbar_tabs()

        def on_close():
            if win_id in self.open_windows:
                del self.open_windows[win_id]
            win.destroy()
            self.update_taskbar_tabs()

        win.protocol("WM_DELETE_WINDOW", on_close)
        return win

    def update_taskbar_tabs(self):
        for widget in self.tabs_frame.winfo_children():
            widget.destroy()
        for win_id, win in self.open_windows.items():
            try:
                title = win.title()
                if len(title) > 20:
                    title = title[:17] + "..."
                tab_btn = tk.Button(
                    self.tabs_frame, text=f"▪ {title}",
                    bg="#004080", fg="#FFFFFF",
                    font=("Sans", 8, "bold"), relief=tk.RAISED, bd=2,
                    command=lambda w=win: (w.deiconify(), w.lift())
                )
                tab_btn.pack(side=tk.LEFT, padx=3, pady=2)
            except Exception:
                pass

    # ==========================================================================
    # Application 1: System Diagnostics & ASCII Banner
    # ==========================================================================
    def open_app_sysinfo(self):
        win = self.create_custom_window("LimboOS System Diagnostics & ASCII Logo", 660, 480)

        top_frame = tk.Frame(win, bg="#001830", pady=10)
        top_frame.pack(fill=tk.X)

        ascii_txt = (
            " __    _       _          _____ _____ \n"
            "|  |  |_|_____| |_ ___   |     |   __|\n"
            "|  |__| |     | . | . |  |  |  |__   |\n"
            "|_____|_|_|_|_|___|___|  |_____|_____|"
        )
        lbl_ascii = tk.Label(
            top_frame, text=ascii_txt,
            bg="#001830", fg="#00FFFF",
            font=("Monospace", 14, "bold"), justify=tk.CENTER
        )
        lbl_ascii.pack()

        lbl_sub = tk.Label(
            top_frame,
            text="LimboOS Custom Linux Build — Pure Kernel + Custom GUI Shell",
            bg="#001830", fg="#FFFF00", font=("Sans", 10, "bold")
        )
        lbl_sub.pack(pady=4)

        info_frame = tk.Frame(win, bg="#2D333B", padx=15, pady=10)
        info_frame.pack(fill=tk.BOTH, expand=True)

        txt_box = scrolledtext.ScrolledText(
            info_frame, bg="#1A1D20", fg="#55FF55",
            font=("Monospace", 10), height=14
        )
        txt_box.pack(fill=tk.BOTH, expand=True)

        kernel = os.uname().release
        machine = os.uname().machine

        cpu_info = "Limbo Emulated x86/x86_64 CPU"
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu_info = line.split(":")[1].strip()
                        break
        except Exception:
            pass

        mem_info = "512 MB Base"
        try:
            with open("/proc/meminfo", "r") as f:
                tot = avail = 0
                for line in f:
                    if "MemTotal:" in line:
                        tot = int(line.split()[1]) // 1024
                    elif "MemAvailable:" in line:
                        avail = int(line.split()[1]) // 1024
                if tot > 0:
                    mem_info = f"{tot - avail} MB used / {tot} MB Total (Ultra-Lightweight!)"
        except Exception:
            pass

        report = (
            f" [★] OS Distribution : LimboOS Linux Custom Build v1.0\n"
            f" [★] Linux Kernel    : {kernel} ({machine})\n"
            f" [★] GUI Architecture: LimboOS Pure Python/Tkinter Custom Shell\n"
            f" [★] Host CPU Model  : {cpu_info}\n"
            f" [★] Memory Status   : {mem_info}\n"
            f" [★] Display Mode    : X11 Kiosk / Framebuffer Direct Rendering\n"
            f" [★] Custom GUI Features:\n"
            f"      - Built-in Window Manager & Custom Start Menu\n"
            f"      - Custom Graphical File Explorer (RootFS Access)\n"
            f"      - Neural AI Assistant Chat Simulator\n"
            f"      - Retro AI-Pad Text Editor Buffer\n"
            f"      - FLOPS CPU Speed Benchmarking Engine\n"
            f"      - lpkg Package Manager & App Store\n\n"
            f" === [ LimboOS Linux Core: Active & Running Smoothly ] ==="
        )
        txt_box.insert(tk.END, report)
        txt_box.configure(state=tk.DISABLED)

    # ==========================================================================
    # Application 2: LimboOS File Explorer
    # ==========================================================================
    def open_app_files(self):
        win = self.create_custom_window("LimboOS File Explorer (Linux RootFS)", 620, 440)

        top_frame = tk.Frame(win, bg="#1F2428", pady=6, padx=10)
        top_frame.pack(fill=tk.X)

        tk.Label(
            top_frame, text="Current Directory:",
            bg="#1F2428", fg="#FFFFFF", font=("Sans", 10, "bold")
        ).pack(side=tk.LEFT)

        default_path = "/home/user" if os.path.exists("/home/user") else "/"
        path_var = tk.StringVar(value=default_path)
        path_entry = tk.Entry(
            top_frame, textvariable=path_var,
            bg="#101418", fg="#00FFFF", font=("Monospace", 10)
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        list_frame = tk.Frame(win, bg="#2D333B", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        file_list = tk.Listbox(
            list_frame, bg="#1A1D20", fg="#FFFFFF",
            font=("Monospace", 10), selectbackground="#008080"
        )
        file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=file_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        file_list.configure(yscrollcommand=scrollbar.set)

        def load_dir(dpath):
            file_list.delete(0, tk.END)
            try:
                items = sorted(os.listdir(dpath))
                file_list.insert(tk.END, "📁 .. (Parent Directory)")
                for item in items:
                    full = os.path.join(dpath, item)
                    if os.path.isdir(full):
                        file_list.insert(tk.END, f"📁 {item}/")
                    else:
                        size = os.path.getsize(full) if os.path.isfile(full) else 0
                        file_list.insert(tk.END, f"📄 {item} ({size} bytes)")
            except Exception as e:
                file_list.insert(tk.END, f"[Error reading dir: {e}]")

        def on_select(event):
            selection = file_list.curselection()
            if not selection:
                return
            item_str = file_list.get(selection[0])
            cur_dir = path_var.get()

            if item_str.startswith("📁 .."):
                new_dir = os.path.dirname(cur_dir)
                if not new_dir:
                    new_dir = "/"
                path_var.set(new_dir)
                load_dir(new_dir)
            elif item_str.startswith("📁 "):
                dname = item_str[2:].rstrip("/")
                new_dir = os.path.join(cur_dir, dname)
                path_var.set(new_dir)
                load_dir(new_dir)
            elif item_str.startswith("📄 "):
                fname = item_str.split()[1]
                fpath = os.path.join(cur_dir, fname)
                self.open_file_in_notepad(fpath)

        file_list.bind("<Double-Button-1>", on_select)
        tk.Button(
            top_frame, text=" Go / Refresh ",
            bg="#006699", fg="#FFFFFF", font=("Sans", 9, "bold"),
            command=lambda: load_dir(path_var.get())
        ).pack(side=tk.RIGHT)

        load_dir(path_var.get())

    def open_file_in_notepad(self, filepath):
        self.open_app_notepad(filepath)

    # ==========================================================================
    # Application 3: LimboOS AI Assistant
    # ==========================================================================
    def open_app_chat(self):
        win = self.create_custom_window("LimboOS AI Assistant (Custom Neural Simulator)", 580, 420)

        chat_box = scrolledtext.ScrolledText(
            win, bg="#101418", fg="#FFFFFF", font=("Sans", 10), height=15
        )
        chat_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        chat_box.insert(
            tk.END,
            "🤖 [LimboOS Neural Assistant]: Greetings! I am your custom-built LimboOS AI Assistant, "
            "running directly inside our custom Linux GUI layer! Ask me anything.\n\n"
        )
        chat_box.configure(state=tk.DISABLED)

        btm_frame = tk.Frame(win, bg="#2D333B", padx=10, pady=8)
        btm_frame.pack(fill=tk.X)

        entry = tk.Entry(btm_frame, bg="#1F2428", fg="#00FFFF", font=("Sans", 10))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        def send_msg():
            txt = entry.get().strip()
            if not txt:
                return
            entry.delete(0, tk.END)

            chat_box.configure(state=tk.NORMAL)
            chat_box.insert(tk.END, f"👤 [You]: {txt}\n")

            lower = txt.lower()
            if "ascii" in lower or "лого" in lower or "банер" in lower:
                ans = "Our ASCII banner '__ _ _ _____ _____' is the true centerpiece of LimboOS across all three editions!"
            elif "linux" in lower or "ядро" in lower or "лінукс" in lower:
                ans = "We dropped generic managers and wrote this entire GUI layer in pure Python/X11 directly over the Linux kernel!"
            elif "limbo" in lower or "android" in lower or "телефон" in lower:
                ans = "Limbo PC Emulator x86 runs this custom Linux distribution lightning fast because we have zero desktop bloat!"
            elif "хто" in lower or "хто ти" in lower or "who" in lower:
                ans = "I am LimboOS Neural Core v1.0, engineered specifically to give ordinary enthusiasts an extraordinary custom OS!"
            elif "lpkg" in lower or "пакет" in lower or "package" in lower:
                ans = "lpkg is our custom package manager! It downloads apps directly from our GitHub repository. Try: lpkg list"
            elif "update" in lower or "оновлен" in lower:
                ans = "LimboOS supports OTA updates! Run 'limboos-update --check' or use the App Store to check for updates."
            else:
                ans = f"Processing query '{txt}'... Optimized real-time execution completed in 2 milliseconds on our custom kernel!"

            chat_box.insert(tk.END, f"🤖 [LimboOS Assistant]: {ans}\n\n")
            chat_box.see(tk.END)
            chat_box.configure(state=tk.DISABLED)

        entry.bind("<Return>", lambda e: send_msg())
        tk.Button(
            btm_frame, text=" Send ",
            bg="#008080", fg="#FFFFFF", font=("Sans", 9, "bold"),
            command=send_msg
        ).pack(side=tk.RIGHT, padx=5)

    # ==========================================================================
    # Application 4: LimboOS Retro AI-Pad (Notepad)
    # ==========================================================================
    def open_app_notepad(self, load_path=None):
        win = self.create_custom_window("LimboOS Retro AI-Pad Text Editor", 600, 430)

        top_bar = tk.Frame(win, bg="#1F2428", pady=4, padx=8)
        top_bar.pack(fill=tk.X)

        txt_editor = scrolledtext.ScrolledText(
            win, bg="#1A1D20", fg="#FFFF00",
            font=("Monospace", 10), insertbackground="#FFFFFF"
        )
        txt_editor.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        if load_path and os.path.exists(load_path):
            try:
                with open(load_path, "r", errors="ignore") as f:
                    txt_editor.insert(tk.END, f.read())
                win.title(f"Retro AI-Pad - [{os.path.basename(load_path)}]")
            except Exception as e:
                txt_editor.insert(tk.END, f"[Error loading file: {e}]")
        else:
            txt_editor.insert(
                tk.END,
                "# LimboOS Custom Notes\n# Type here or open files from LimboOS File Explorer!\n\n"
            )

        def save_file():
            save_path = load_path if load_path else "/home/user/limboos_notes.txt"
            try:
                with open(save_path, "w") as f:
                    f.write(txt_editor.get("1.0", tk.END))
                messagebox.showinfo("Saved", f"Successfully saved to:\n{save_path}", parent=win)
            except Exception as e:
                messagebox.showerror("Error", f"Could not save: {e}", parent=win)

        tk.Button(
            top_bar, text=" 💾 Save File ",
            bg="#008080", fg="#FFFFFF", font=("Sans", 9, "bold"),
            command=save_file
        ).pack(side=tk.LEFT, padx=4)
        tk.Button(
            top_bar, text=" 🧹 Clear ",
            bg="#800000", fg="#FFFFFF", font=("Sans", 9, "bold"),
            command=lambda: txt_editor.delete("1.0", tk.END)
        ).pack(side=tk.LEFT, padx=4)

    # ==========================================================================
    # Application 5: Calculator & Benchmark Engine
    # ==========================================================================
    def open_app_calc(self):
        win = self.create_custom_window("LimboOS Math & FLOPS Benchmark Engine", 500, 380)

        res_var = tk.StringVar(value="0")
        display = tk.Entry(
            win, textvariable=res_var,
            bg="#101418", fg="#00FFFF",
            font=("Monospace", 18, "bold"), justify=tk.RIGHT,
            bd=6, relief=tk.SUNKEN
        )
        display.pack(fill=tk.X, padx=15, pady=15)

        btns_frame = tk.Frame(win, bg="#2D333B")
        btns_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        def run_benchmark():
            res_var.set("Benchmarking...")
            win.update()
            t0 = time.time()
            s = 0.0
            for i in range(2000000):
                s += i * 1.0001
            dt = time.time() - t0
            mflops = (2.0 / dt) if dt > 0 else 999.0
            res_var.set(f"Speed: {mflops:.1f} MFLOPS (Limbo Core OK!)")

        tk.Button(
            btns_frame, text="⚡ RUN CPU SPEED BENCHMARK ⚡",
            bg="#008080", fg="#FFFFFF", font=("Sans", 11, "bold"),
            command=run_benchmark
        ).pack(fill=tk.X, pady=8)

        grid_f = tk.Frame(btns_frame, bg="#2D333B")
        grid_f.pack(fill=tk.BOTH, expand=True)

        buttons = [
            ('7', '8', '9', '/'),
            ('4', '5', '6', '*'),
            ('1', '2', '3', '-'),
            ('C', '0', '=', '+')
        ]

        def on_calc_click(char):
            cur = res_var.get()
            if char == 'C':
                res_var.set("0")
            elif char == '=':
                try:
                    res_var.set(str(eval(cur)))
                except Exception:
                    res_var.set("Error")
            else:
                if cur in ("0", "Error", "Benchmarking...") or "Speed:" in cur:
                    res_var.set(char)
                else:
                    res_var.set(cur + char)

        for r, row in enumerate(buttons):
            for c, char in enumerate(row):
                tk.Button(
                    grid_f, text=char,
                    bg="#1F2428", fg="#FFFFFF",
                    font=("Sans", 12, "bold"), width=6, height=1,
                    command=lambda ch=char: on_calc_click(ch)
                ).grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
                grid_f.columnconfigure(c, weight=1)
                grid_f.rowconfigure(r, weight=1)

    # ==========================================================================
    # Application 6: Linux Terminal Shell
    # ==========================================================================
    def open_app_term(self):
        win = self.create_custom_window("LimboOS Terminal Shell (Pure Linux Command Line)", 640, 420)

        txt_term = scrolledtext.ScrolledText(
            win, bg="#000000", fg="#00FF00", font=("Monospace", 10)
        )
        txt_term.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        txt_term.insert(tk.END, "limboos-linux:~$ uname -a\n" + subprocess.getoutput("uname -a") + "\n\n")
        txt_term.insert(tk.END, "limboos-linux:~$ ")

        btm_f = tk.Frame(win, bg="#2D333B", padx=8, pady=6)
        btm_f.pack(fill=tk.X)

        tk.Label(
            btm_f, text="Command:",
            bg="#2D333B", fg="#FFFFFF", font=("Sans", 10, "bold")
        ).pack(side=tk.LEFT)

        cmd_entry = tk.Entry(btm_f, bg="#101418", fg="#00FFFF", font=("Monospace", 10))
        cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        def run_cmd():
            c = cmd_entry.get().strip()
            if not c:
                return
            cmd_entry.delete(0, tk.END)
            txt_term.insert(tk.END, f"{c}\n")
            try:
                out = subprocess.getoutput(c)
                txt_term.insert(tk.END, out + "\n\nlimboos-linux:~$ ")
            except Exception as e:
                txt_term.insert(tk.END, f"Error: {e}\n\nlimboos-linux:~$ ")
            txt_term.see(tk.END)

        cmd_entry.bind("<Return>", lambda e: run_cmd())
        tk.Button(
            btm_f, text=" Execute ",
            bg="#006699", fg="#FFFFFF", font=("Sans", 9, "bold"),
            command=run_cmd
        ).pack(side=tk.RIGHT)

    # ==========================================================================
    # Application 7: LimboOS App Store (lpkg Store)
    # ==========================================================================
    def open_app_store(self):
        win = self.create_custom_window("LimboOS App Store (lpkg)", 680, 520)

        # Header
        header = tk.Frame(win, bg="#004080", pady=8)
        header.pack(fill=tk.X)
        tk.Label(
            header, text=" 📦 LimboOS App Store — Powered by lpkg ",
            bg="#004080", fg="#FFFFFF", font=("Sans", 13, "bold")
        ).pack()

        # Category filter
        filter_frame = tk.Frame(win, bg="#1F2428", padx=10, pady=6)
        filter_frame.pack(fill=tk.X)
        tk.Label(filter_frame, text="Category:", bg="#1F2428", fg="#FFFFFF", font=("Sans", 9, "bold")).pack(side=tk.LEFT)

        categories = ["All", "Games", "Demos", "Utilities", "Diagnostics", "System"]
        cat_var = tk.StringVar(value="All")
        for cat in categories:
            tk.Radiobutton(
                filter_frame, text=cat, variable=cat_var, value=cat,
                bg="#1F2428", fg="#00FFFF", activebackground="#008080",
                font=("Sans", 9), command=lambda: refresh_list()
            ).pack(side=tk.LEFT, padx=6)

        # Package list
        list_frame = tk.Frame(win, bg="#2D333B", padx=10, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        pkg_listbox = tk.Listbox(
            list_frame, bg="#1A1D20", fg="#FFFFFF",
            font=("Monospace", 10), selectbackground="#008080",
            activestyle="none"
        )
        pkg_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=pkg_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        pkg_listbox.configure(yscrollcommand=scrollbar.set)

        # Info panel
        info_frame = tk.Frame(win, bg="#2D333B", padx=10)
        info_frame.pack(fill=tk.X)

        info_label = tk.Label(
            info_frame, text="Select a package to see details...",
            bg="#2D333B", fg="#AAAAAA", font=("Sans", 9),
            anchor=tk.W, justify=tk.LEFT, wraplength=640
        )
        info_label.pack(fill=tk.X)

        # Actions
        action_frame = tk.Frame(win, bg="#1F2428", padx=10, pady=8)
        action_frame.pack(fill=tk.X)

        status_label = tk.Label(
            action_frame, text="Ready",
            bg="#1F2428", fg="#55FF55", font=("Sans", 9)
        )
        status_label.pack(side=tk.LEFT, padx=5)

        # Load manifest
        manifest = self._load_store_manifest()

        def refresh_list():
            pkg_listbox.delete(0, tk.END)
            cat = cat_var.get()
            for pkg_id, info in manifest.items():
                if cat == "All" or info.get("category") == cat:
                    status_icon = "✅" if self._is_installed(pkg_id) else "  "
                    pkg_listbox.insert(tk.END, f" {status_icon} {pkg_id:<18} {info['name']}")

        def on_select_pkg(event):
            sel = pkg_listbox.curselection()
            if not sel:
                return
            text = pkg_listbox.get(sel[0])
            pkg_id = text.split()[1] if len(text.split()) > 1 else ""
            if pkg_id in manifest:
                info = manifest[pkg_id]
                installed = "✅ Installed" if self._is_installed(pkg_id) else "❌ Not installed"
                info_label.configure(
                    text=f"  {info['name']} v{info.get('version', '1.0')} | {info.get('category', '')} | {installed}\n"
                         f"  {info.get('description', '')}",
                    fg="#FFFFFF"
                )

        def install_selected():
            sel = pkg_listbox.curselection()
            if not sel:
                return
            text = pkg_listbox.get(sel[0])
            pkg_id = text.split()[1] if len(text.split()) > 1 else ""
            if pkg_id and not self._is_installed(pkg_id):
                status_label.configure(text=f"Installing {pkg_id}...", fg="#FFFF00")
                win.update()
                try:
                    self._install_from_store(pkg_id, manifest.get(pkg_id, {}))
                    status_label.configure(text=f"✅ {pkg_id} installed successfully!", fg="#55FF55")
                    refresh_list()
                except Exception as e:
                    status_label.configure(text=f"❌ Error: {e}", fg="#FF5555")
            elif self._is_installed(pkg_id):
                status_label.configure(text=f"ℹ️ {pkg_id} is already installed", fg="#AAAAAA")

        def remove_selected():
            sel = pkg_listbox.curselection()
            if not sel:
                return
            text = pkg_listbox.get(sel[0])
            pkg_id = text.split()[1] if len(text.split()) > 1 else ""
            if pkg_id and self._is_installed(pkg_id):
                self._remove_from_store(pkg_id)
                status_label.configure(text=f"🗑️ {pkg_id} removed", fg="#FF5555")
                refresh_list()

        pkg_listbox.bind("<<ListboxSelect>>", on_select_pkg)

        tk.Button(
            action_frame, text=" 📥 Install ",
            bg="#008080", fg="#FFFFFF", font=("Sans", 10, "bold"),
            command=install_selected
        ).pack(side=tk.RIGHT, padx=4)

        tk.Button(
            action_frame, text=" 🗑️ Remove ",
            bg="#800000", fg="#FFFFFF", font=("Sans", 10, "bold"),
            command=remove_selected
        ).pack(side=tk.RIGHT, padx=4)

        tk.Button(
            action_frame, text=" 🔄 Refresh ",
            bg="#004080", fg="#FFFFFF", font=("Sans", 10, "bold"),
            command=lambda: (status_label.configure(text="Updating repo...", fg="#FFFF00"),
                             win.update(), refresh_list(),
                             status_label.configure(text="Ready", fg="#55FF55"))
        ).pack(side=tk.RIGHT, padx=4)

        refresh_list()

    def _load_store_manifest(self):
        """Load package manifest from lpkg repo."""
        paths = [
            os.path.expanduser("~/bin/lpkg_repo.json"),
            "/var/lib/lpkg/repo_manifest.json",
            "/var/lib/lpkg/lpkg_repo.json",
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, "r") as f:
                        return json.load(f)
                except Exception:
                    pass

        # Fallback: embedded manifest
        return {
            "limbo-snake": {
                "name": "LimboOS Retro Snake Game",
                "description": "Classic ASCII Snake game optimized for 80x25 terminal grid",
                "category": "Games",
                "version": "1.0.0"
            },
            "limbo-matrix": {
                "name": "LimboOS Cyber Matrix Rain",
                "description": "ASCII green digital matrix rain screen saver",
                "category": "Demos",
                "version": "1.0.0"
            },
            "limbo-clock": {
                "name": "LimboOS Big ASCII Digital Clock",
                "description": "Large digital ASCII clock display for terminal",
                "category": "Utilities",
                "version": "1.0.0"
            },
            "limbo-sysstat": {
                "name": "LimboOS Advanced Hardware Diagnostic",
                "description": "Extended system hardware scanner and benchmark reporter",
                "category": "Diagnostics",
                "version": "1.0.0"
            }
        }

    def _is_installed(self, pkg_id):
        """Check if a package is installed."""
        installed_db = os.path.expanduser("~/bin/limboos_installed_apps.json")
        try:
            if os.path.exists(installed_db):
                with open(installed_db, "r") as f:
                    data = json.load(f)
                return pkg_id in data
        except Exception:
            pass
        # Check if binary exists
        bin_path = os.path.expanduser(f"~/bin/{pkg_id}")
        return os.path.exists(bin_path)

    def _install_from_store(self, pkg_id, info):
        """Install a package from the store."""
        # Use lpkg install command
        result = subprocess.run(
            [sys.executable, "/usr/bin/lpkg", "install", pkg_id],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            # Fallback: direct install from manifest
            target = os.path.expanduser(f"~/bin/{pkg_id}")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if "code" in info:
                with open(target, "w") as f:
                    f.write(info["code"])
                os.chmod(target, 0o755)

                # Register in GUI
                gui_db = os.path.expanduser("~/bin/limboos_installed_apps.json")
                installed = {}
                if os.path.exists(gui_db):
                    with open(gui_db, "r") as f:
                        installed = json.load(f)
                installed[pkg_id] = {
                    "name": info.get("name", pkg_id),
                    "cmd": target
                }
                with open(gui_db, "w") as f:
                    json.dump(installed, f, indent=2)

    def _remove_from_store(self, pkg_id):
        """Remove an installed package."""
        bin_path = os.path.expanduser(f"~/bin/{pkg_id}")
        if os.path.exists(bin_path):
            os.remove(bin_path)
        gui_db = os.path.expanduser("~/bin/limboos_installed_apps.json")
        try:
            if os.path.exists(gui_db):
                with open(gui_db, "r") as f:
                    data = json.load(f)
                if pkg_id in data:
                    del data[pkg_id]
                with open(gui_db, "w") as f:
                    json.dump(data, f, indent=2)
        except Exception:
            pass

    # ==========================================================================
    # OTA Update Checker
    # ==========================================================================
    def open_ota_check(self):
        win = self.create_custom_window("LimboOS OTA Update Checker", 500, 350)

        header = tk.Frame(win, bg="#004080", pady=8)
        header.pack(fill=tk.X)
        tk.Label(
            header, text=" 🔄 LimboOS OTA Update System ",
            bg="#004080", fg="#FFFFFF", font=("Sans", 12, "bold")
        ).pack()

        info_frame = tk.Frame(win, bg="#2D333B", padx=20, pady=20)
        info_frame.pack(fill=tk.BOTH, expand=True)

        status_var = tk.StringVar(value="Checking for updates...")
        tk.Label(
            info_frame, textvariable=status_var,
            bg="#2D333B", fg="#FFFF00", font=("Sans", 11, "bold"),
            wraplength=440, justify=tk.CENTER
        ).pack(pady=20)

        log_box = scrolledtext.ScrolledText(
            info_frame, bg="#1A1D20", fg="#55FF55",
            font=("Monospace", 9), height=8
        )
        log_box.pack(fill=tk.BOTH, expand=True, pady=10)

        def check_updates():
            log_box.insert(tk.END, "[*] Connecting to GitHub API...\n")
            log_box.insert(tk.END, "[*] Repository: GlomGing85/LimboOS.Repo\n")
            log_box.see(tk.END)
            win.update()

            try:
                import urllib.request
                url = "https://api.github.com/repos/GlomGing85/LimboOS.Repo/releases/latest"
                req = urllib.request.Request(url, headers={"User-Agent": "LimboOS/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                    latest = data.get("tag_name", "unknown")
                    log_box.insert(tk.END, f"[+] Latest release: {latest}\n")
                    log_box.insert(tk.END, f"[+] Release name: {data.get('name', 'N/A')}\n")

                    # Read current version
                    current = "1.0.0"
                    try:
                        with open("/etc/limboos/version.json", "r") as f:
                            vdata = json.load(f)
                            current = vdata.get("version", current)
                    except Exception:
                        pass

                    log_box.insert(tk.END, f"[*] Current version: {current}\n")

                    if latest > current:
                        status_var.set(f"🟢 Update available: {latest}")
                        log_box.insert(tk.END, f"[!] Update available! Run 'limboos-update --apply'\n")
                    else:
                        status_var.set("✅ System is up to date!")
                        log_box.insert(tk.END, "[+] System is up to date.\n")
            except Exception as e:
                status_var.set("⚠️ Could not check for updates")
                log_box.insert(tk.END, f"[!] Error: {e}\n")
                log_box.insert(tk.END, "[*] Check your internet connection.\n")

            log_box.see(tk.END)

        tk.Button(
            info_frame, text=" 🔄 Check Now ",
            bg="#008080", fg="#FFFFFF", font=("Sans", 10, "bold"),
            command=check_updates
        ).pack(pady=10)

        # Auto-check on open
        win.after(500, check_updates)

    # ==========================================================================
    # Settings
    # ==========================================================================
    def open_settings(self):
        win = self.create_custom_window("LimboOS Settings", 480, 380)

        header = tk.Frame(win, bg="#004080", pady=8)
        header.pack(fill=tk.X)
        tk.Label(
            header, text=" ⚙️ LimboOS Settings ",
            bg="#004080", fg="#FFFFFF", font=("Sans", 12, "bold")
        ).pack()

        settings_frame = tk.Frame(win, bg="#2D333B", padx=20, pady=15)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # Version info
        tk.Label(
            settings_frame, text="LimboOS Linux v1.0 (Genesis)",
            bg="#2D333B", fg="#00FFFF", font=("Sans", 11, "bold")
        ).pack(anchor=tk.W, pady=4)

        tk.Label(
            settings_frame, text="Kernel: " + os.uname().release,
            bg="#2D333B", fg="#AAAAAA", font=("Sans", 9)
        ).pack(anchor=tk.W)

        tk.Label(
            settings_frame, text="Architecture: " + os.uname().machine,
            bg="#2D333B", fg="#AAAAAA", font=("Sans", 9)
        ).pack(anchor=tk.W)

        ttk.Separator(settings_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # GitHub link
        tk.Label(
            settings_frame, text="GitHub: github.com/GlomGing85/LimboOS.Repo",
            bg="#2D333B", fg="#55FF55", font=("Sans", 9)
        ).pack(anchor=tk.W)

        tk.Label(
            settings_frame, text="Package Manager: lpkg v1.0",
            bg="#2D333B", fg="#AAAAAA", font=("Sans", 9)
        ).pack(anchor=tk.W)

        ttk.Separator(settings_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # About
        tk.Label(
            settings_frame,
            text="LimboOS — custom Linux distribution for Limbo PC Emulator.\n"
                 "Built with pure Linux kernel + custom Python/Tkinter GUI shell.\n"
                 "Package management via GitHub-powered lpkg.",
            bg="#2D333B", fg="#888888", font=("Sans", 9),
            justify=tk.LEFT, wraplength=420
        ).pack(anchor=tk.W, pady=10)

    # ==========================================================================
    # Exit
    # ==========================================================================
    def exit_gui(self):
        if messagebox.askyesno("Exit LimboOS GUI", "Close custom Linux desktop and return to command prompt?"):
            self.destroy()
            sys.exit(0)


# ==============================================================================
# Main entry point
# ==============================================================================
if __name__ == "__main__":
    app = LimboOSDesktop()
    app.mainloop()
