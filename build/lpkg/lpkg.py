#!/usr/bin/env python3
# ==============================================================================
# LPKG v1.0 — LimboOS GitHub Package Manager
# "Наш власний pkg/apt через GitHub!"
# Custom Package Manager specifically engineered for LimboOS Linux.
# Downloads and installs standalone custom applications directly from
# GitHub/Mirrors into the LimboOS filesystem.
# ==============================================================================

import os
import sys
import json
import urllib.request
import urllib.error
import subprocess
import hashlib
import time

# ── Paths ─────────────────────────────────────────────────────────────────────
TARGET_BIN = os.path.expanduser("~/bin")
SYS_BIN = "/usr/bin" if os.access("/usr/bin", os.W_OK) else TARGET_BIN
LPKG_DATA = os.path.expanduser("~/bin/lpkg_repo.json")
LPKG_INSTALLED = os.path.expanduser("~/bin/limboos_installed_apps.json")
LPKG_CACHE = os.path.expanduser("~/.cache/lpkg")

os.makedirs(TARGET_BIN, exist_ok=True)
os.makedirs(LPKG_CACHE, exist_ok=True)

# ── Remote Repository URL ─────────────────────────────────────────────────────
REPO_MANIFEST_URL = "https://raw.githubusercontent.com/GlomGing85/LimboOS.Repo/main/lpkg/repo_manifest.json"

# ── Embedded Fallback Manifest ────────────────────────────────────────────────
EMBEDDED_MANIFEST = {
    "limbo-snake": {
        "name": "LimboOS Retro Snake Game",
        "description": "Classic ASCII Snake game optimized for 80x25 terminal grid and Limbo x86",
        "category": "Games",
        "version": "1.0.0",
        "author": "LimboOS Team",
        "code": '''#!/usr/bin/env python3
import curses, random, time
def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    sh, sw = stdscr.getmaxyx()
    w = curses.newwin(sh, sw, 0, 0)
    w.keypad(1)
    w.timeout(100)
    snk_x = sw//4; snk_y = sh//2
    snake = [[snk_y, snk_x], [snk_y, snk_x-1], [snk_y, snk_x-2]]
    food = [sh//2, sw//2]
    w.addch(food[0], food[1], curses.ACS_PI)
    key = curses.KEY_RIGHT
    score = 0
    while True:
        next_key = w.getch()
        key = key if next_key == -1 else next_key
        if key == 27: break
        new_head = [snake[0][0], snake[0][1]]
        if key == curses.KEY_DOWN: new_head[0] += 1
        if key == curses.KEY_UP: new_head[0] -= 1
        if key == curses.KEY_LEFT: new_head[1] -= 1
        if key == curses.KEY_RIGHT: new_head[1] += 1
        snake.insert(0, new_head)
        if snake[0] == food:
            score += 10
            food = None
            while food is None:
                nf = [random.randint(1, sh-2), random.randint(1, sw-2)]
                food = nf if nf not in snake else None
            w.addch(food[0], food[1], curses.ACS_PI)
        else:
            tail = snake.pop()
            w.addch(tail[0], tail[1], ' ')
        try: w.addch(snake[0][0], snake[0][1], curses.ACS_CKBOARD)
        except: break
        w.addstr(0, 2, f" [ LimboOS Snake | Score: {score} | ESC to Quit ] ")
if __name__ == "__main__": curses.wrapper(main)
'''
    },
    "limbo-matrix": {
        "name": "LimboOS Cyber Matrix Rain",
        "description": "ASCII green digital matrix rain screen saver for LimboOS terminal",
        "category": "Demos",
        "version": "1.0.0",
        "author": "LimboOS Team",
        "code": '''#!/usr/bin/env python3
import os, sys, time, random
C_GREEN = "\\033[1;32m"
C_WHITE = "\\033[1;37m"
C_RESET = "\\033[0m"
def main():
    cols = 80
    try: cols = os.get_terminal_size().columns
    except: pass
    drops = [0] * cols
    print(f"\\033[2J\\033[H", end="")
    try:
        while True:
            line = ""
            for i in range(cols):
                if random.random() < 0.08 or drops[i] > 0:
                    char = random.choice("0123456789ABCDEF@#$%&*+=-")
                    color = C_WHITE if random.random() < 0.1 else C_GREEN
                    line += f"{color}{char}{C_RESET}"
                    drops[i] = random.randint(1, 15) if drops[i] == 0 else drops[i] - 1
                else:
                    line += " "
            print(line)
            time.sleep(0.06)
    except KeyboardInterrupt:
        print(f"\\n{C_WHITE}[+] Exited LimboOS Matrix Rain.{C_RESET}")
if __name__ == "__main__": main()
'''
    },
    "limbo-clock": {
        "name": "LimboOS Big ASCII Digital Clock",
        "description": "Large digital ASCII clock display for terminal monitoring",
        "category": "Utilities",
        "version": "1.0.0",
        "author": "LimboOS Team",
        "code": '''#!/usr/bin/env python3
import time, os
C_TEAL = "\\033[1;36m"
C_RESET = "\\033[0m"
def main():
    try:
        while True:
            os.system("clear || cls")
            now = time.strftime("%H : %M : %S")
            date_str = time.strftime("%A, %d %B %Y")
            print(f"\\n\\n\\n{C_TEAL}")
            print("      ===== [ LimboOS System Digital Clock ] =====")
            print(f"\\n              [  {now}  ]")
            print(f"\\n                 {date_str}{C_RESET}\\n")
            print("           Press Ctrl+C to exit back to LimboOS Shell.")
            time.sleep(1)
    except KeyboardInterrupt: pass
if __name__ == "__main__": main()
'''
    },
    "limbo-sysstat": {
        "name": "LimboOS Advanced Hardware Diagnostic",
        "description": "Extended system hardware scanner and benchmark reporter",
        "category": "Diagnostics",
        "version": "1.0.0",
        "author": "LimboOS Team",
        "code": '''#!/usr/bin/env python3
import os, sys, platform
print("\\033[1;36m========================================================================\\033[0m")
print("           LimboOS Advanced Hardware Diagnostic Report v1.0             ")
print("\\033[1;36m========================================================================\\033[0m")
print(f" [★] System Platform  : {platform.system()} {platform.release()} ({platform.machine()})")
print(f" [★] Python Version   : {platform.python_version()}")
try:
    with open("/proc/cpuinfo") as f:
        for line in f:
            if "model name" in line:
                print(f" [★] CPU Model Name   : {line.split(':')[1].strip()}")
                break
except: pass
try:
    with open("/proc/meminfo") as f:
        for line in f[:4]:
            print(f" [★] {line.strip()}")
except: pass
print("\\033[1;36m========================================================================\\033[0m")
'''
    }
}


# ── Colors ────────────────────────────────────────────────────────────────────
C_CYAN = "\033[1;36m"
C_GREEN = "\033[1;32m"
C_YELLOW = "\033[1;33m"
C_RED = "\033[1;31m"
C_WHITE = "\033[1;37m"
C_DIM = "\033[0;36m"
C_RESET = "\033[0m"


# ── Banner ────────────────────────────────────────────────────────────────────
def print_banner():
    print(f"{C_CYAN} __    _       _          _____ _____ {C_RESET}")
    print(f"{C_CYAN}|  |  |_|_____| |_ ___   |     |   __|{C_RESET}   {C_WHITE}LPKG — LimboOS GitHub Package Manager{C_RESET}")
    print(f"{C_CYAN}|  |__| |     | . | . |  |  |  |__   |{C_RESET}   {C_GREEN}\"Наш власний pkg/apt в самій ОС!\"{C_RESET}")
    print(f"{C_CYAN}|_____|_|_|_|_|___|___|  |_____|_____|{C_RESET}")
    print(f"{C_CYAN}============================================================================{C_RESET}")


# ── Manifest Loading ──────────────────────────────────────────────────────────
def load_manifest():
    """Load manifest from local cache."""
    if os.path.exists(LPKG_DATA):
        try:
            with open(LPKG_DATA, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return EMBEDDED_MANIFEST.copy()


def load_installed():
    """Load installed packages registry."""
    if os.path.exists(LPKG_INSTALLED):
        try:
            with open(LPKG_INSTALLED, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_installed(data):
    """Save installed packages registry."""
    with open(LPKG_INSTALLED, "w") as f:
        json.dump(data, f, indent=2)


# ── Commands ──────────────────────────────────────────────────────────────────
def cmd_update():
    """Fetch latest repository manifest from GitHub."""
    print_banner()
    print(f"{C_YELLOW}[*] Fetching latest LimboOS repository index from GitHub...{C_RESET}")
    print(f"    URL: {REPO_MANIFEST_URL}")

    try:
        req = urllib.request.Request(REPO_MANIFEST_URL, headers={"User-Agent": "lpkg/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            with open(LPKG_DATA, "w") as f:
                json.dump(data, f, indent=2)
            print(f"{C_GREEN}[+] Repository index updated successfully! ({len(data)} packages available){C_RESET}")
            return
    except Exception as e:
        print(f"{C_YELLOW}[!] Could not fetch from GitHub: {e}{C_RESET}")
        print(f"{C_YELLOW}[*] Using embedded fallback manifest...{C_RESET}")

    # Fallback: save embedded manifest
    with open(LPKG_DATA, "w") as f:
        json.dump(EMBEDDED_MANIFEST, f, indent=2)
    print(f"{C_GREEN}[+] Repository index saved from embedded manifest. ({len(EMBEDDED_MANIFEST)} packages){C_RESET}")


def cmd_list():
    """List all available packages."""
    print_banner()
    manifest = load_manifest()
    installed = load_installed()
    print(f"{C_WHITE}Available LimboOS Packages via GitHub / lpkg:{C_RESET}\n")
    print(f"  {'Package':<18} {'Name':<35} {'Category':<14} {'Status'}")
    print(f"  {'─'*18} {'─'*35} {'─'*14} {'─'*10}")
    for pkg_id, info in sorted(manifest.items()):
        status = f"{C_GREEN}✅ installed{C_RESET}" if pkg_id in installed else f"{C_DIM}available{C_RESET}"
        print(f"  {C_GREEN}{pkg_id:<18}{C_RESET} {info.get('name', ''):<35} {info.get('category', ''):<14} {status}")
    print(f"\n  {C_DIM}Total: {len(manifest)} packages | Installed: {len(installed)}{C_RESET}")


def cmd_info(pkg_id):
    """Show detailed info about a package."""
    print_banner()
    manifest = load_manifest()
    installed = load_installed()

    if pkg_id not in manifest:
        print(f"{C_RED}[!] Package '{pkg_id}' not found in repository.{C_RESET}")
        print(f"    Run 'lpkg list' to see available packages.")
        sys.exit(1)

    info = manifest[pkg_id]
    is_installed = pkg_id in installed

    print(f"  {C_CYAN}Package   :{C_RESET} {pkg_id}")
    print(f"  {C_CYAN}Name      :{C_RESET} {info.get('name', 'N/A')}")
    print(f"  {C_CYAN}Version   :{C_RESET} {info.get('version', '1.0.0')}")
    print(f"  {C_CYAN}Category  :{C_RESET} {info.get('category', 'N/A')}")
    print(f"  {C_CYAN}Author    :{C_RESET} {info.get('author', 'LimboOS Team')}")
    print(f"  {C_CYAN}Status    :{C_RESET} {C_GREEN}✅ Installed{C_RESET}" if is_installed else f"  {C_CYAN}Status    :{C_RESET} {C_DIM}Not installed{C_RESET}")
    print(f"  {C_CYAN}Description:{C_RESET}")
    print(f"    {info.get('description', 'No description available.')}")


def cmd_install(pkg_id):
    """Download and install a package."""
    print_banner()
    manifest = load_manifest()
    installed = load_installed()

    if pkg_id not in manifest:
        print(f"{C_RED}[!] Package '{pkg_id}' not found in LimboOS repository.{C_RESET}")
        print(f"    Run 'lpkg list' to see available packages.")
        sys.exit(1)

    if pkg_id in installed:
        print(f"{C_YELLOW}[!] Package '{pkg_id}' is already installed.{C_RESET}")
        print(f"    Use 'lpkg remove {pkg_id}' to remove it first, or 'lpkg reinstall {pkg_id}'.")
        return

    info = manifest[pkg_id]
    print(f"{C_YELLOW}[*] Downloading and installing '{pkg_id}' ({info.get('name', '')})...{C_RESET}")

    # Check for remote download URL
    if "url" in info and info["url"]:
        print(f"    Fetching from: {info['url']}")
        try:
            req = urllib.request.Request(info["url"], headers={"User-Agent": "lpkg/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                code = resp.read().decode()
            print(f"    {C_GREEN}✓ Downloaded from remote{C_RESET}")
        except Exception as e:
            print(f"    {C_YELLOW}! Remote download failed: {e}{C_RESET}")
            print(f"    {C_YELLOW}* Using embedded package code...{C_RESET}")
            code = info.get("code", "")
    else:
        code = info.get("code", "")

    if not code:
        print(f"{C_RED}[!] No code available for package '{pkg_id}'.{C_RESET}")
        sys.exit(1)

    # Save to ~/bin
    target_file = os.path.join(TARGET_BIN, pkg_id)
    with open(target_file, "w") as f:
        f.write(code)
    os.chmod(target_file, 0o755)

    # Also save to /usr/bin if writable
    if SYS_BIN != TARGET_BIN and os.access(SYS_BIN, os.W_OK):
        sys_file = os.path.join(SYS_BIN, pkg_id)
        with open(sys_file, "w") as f:
            f.write(code)
        os.chmod(sys_file, 0o755)
        print(f"    Installed to: {target_file}")
        print(f"    System link:  {sys_file}")
    else:
        print(f"    Installed to: {target_file}")

    # Compute checksum
    sha = hashlib.sha256(code.encode()).hexdigest()[:16]
    print(f"    SHA256 (16):  {sha}")

    # Register in installed apps (for GUI integration)
    installed[pkg_id] = {
        "name": info.get("name", pkg_id),
        "version": info.get("version", "1.0.0"),
        "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cmd": f"xterm -geometry 85x25+60+60 -title '{info.get('name', pkg_id)}' -e bash -c '{target_file} ; read -p \"Press Enter...\" -r'",
        "sha256": sha
    }
    save_installed(installed)

    # Register in GUI start menu database
    gui_db = os.path.join(TARGET_BIN, "limboos_installed_apps.json")
    gui_apps = {}
    if os.path.exists(gui_db):
        try:
            with open(gui_db, "r") as f:
                gui_apps = json.load(f)
        except Exception:
            pass
    gui_apps[pkg_id] = {
        "name": info.get("name", pkg_id),
        "cmd": target_file
    }
    with open(gui_db, "w") as f:
        json.dump(gui_apps, f, indent=2)

    print(f"\n{C_GREEN}[+] Successfully installed '{pkg_id}' to {target_file}!{C_RESET}")
    print(f"{C_WHITE}[*] The package is now registered in your LimboOS Start Menu & App Store.{C_RESET}")


def cmd_remove(pkg_id):
    """Remove an installed package."""
    print_banner()
    installed = load_installed()

    if pkg_id not in installed:
        print(f"{C_RED}[!] Package '{pkg_id}' is not installed.{C_RESET}")
        sys.exit(1)

    # Remove binary
    target_file = os.path.join(TARGET_BIN, pkg_id)
    if os.path.exists(target_file):
        os.remove(target_file)
        print(f"    Removed: {target_file}")

    sys_file = os.path.join(SYS_BIN, pkg_id)
    if os.path.exists(sys_file) and sys_file != target_file:
        os.remove(sys_file)
        print(f"    Removed: {sys_file}")

    # Unregister from installed
    del installed[pkg_id]
    save_installed(installed)

    # Unregister from GUI
    gui_db = os.path.join(TARGET_BIN, "limboos_installed_apps.json")
    try:
        if os.path.exists(gui_db):
            with open(gui_db, "r") as f:
                gui_apps = json.load(f)
            if pkg_id in gui_apps:
                del gui_apps[pkg_id]
            with open(gui_db, "w") as f:
                json.dump(gui_apps, f, indent=2)
    except Exception:
        pass

    print(f"\n{C_GREEN}[+] Package '{pkg_id}' has been removed successfully.{C_RESET}")


def cmd_search(query):
    """Search packages by name/description/category."""
    print_banner()
    manifest = load_manifest()
    query_lower = query.lower()
    found = []

    for pkg_id, info in manifest.items():
        searchable = f"{pkg_id} {info.get('name', '')} {info.get('description', '')} {info.get('category', '')}".lower()
        if query_lower in searchable:
            found.append((pkg_id, info))

    if not found:
        print(f"{C_YELLOW}[!] No packages found matching '{query}'.{C_RESET}")
        return

    print(f"{C_WHITE}Search results for '{query}':{C_RESET}\n")
    for pkg_id, info in found:
        print(f"  {C_GREEN}{pkg_id:<18}{C_RESET} : {info.get('name', '')}")
        print(f"  {C_DIM}                 └─> {info.get('description', '')} [{info.get('category', '')}]{C_RESET}\n")
    print(f"  {C_DIM}Found: {len(found)} package(s){C_RESET}")


def cmd_installed():
    """List installed packages."""
    print_banner()
    installed = load_installed()

    if not installed:
        print(f"{C_YELLOW}[*] No packages installed via lpkg.{C_RESET}")
        return

    print(f"{C_WHITE}Installed packages:{C_RESET}\n")
    print(f"  {'Package':<18} {'Name':<35} {'Version':<10} {'Installed'}")
    print(f"  {'─'*18} {'─'*35} {'─'*10} {'─'*20}")
    for pkg_id, info in sorted(installed.items()):
        print(f"  {C_GREEN}{pkg_id:<18}{C_RESET} {info.get('name', ''):<35} {info.get('version', '1.0'):<10} {info.get('installed_at', 'N/A')}")
    print(f"\n  {C_DIM}Total installed: {len(installed)} package(s){C_RESET}")


def cmd_help():
    """Show help."""
    print_banner()
    print(f"""
{C_WHITE}Usage:{C_RESET} lpkg <command> [arguments]

{C_CYAN}Commands:{C_RESET}
  {C_GREEN}update{C_RESET}              Refresh repository index from GitHub
  {C_GREEN}list{C_RESET}                List all available packages
  {C_GREEN}install{C_RESET} <package>   Download & install a package
  {C_GREEN}remove{C_RESET} <package>    Remove an installed package
  {C_GREEN}search{C_RESET} <query>      Search packages by name/description
  {C_GREEN}info{C_RESET} <package>      Show detailed package information
  {C_GREEN}installed{C_RESET}           List installed packages
  {C_GREEN}help{C_RESET}                Show this help message

{C_CYAN}Examples:{C_RESET}
  lpkg update                          # Update package list
  lpkg list                            # See all available packages
  lpkg install limbo-snake             # Install the Snake game
  lpkg remove limbo-snake              # Remove the Snake game
  lpkg search game                     # Find game packages
  lpkg info limbo-matrix               # Show Matrix package details
""")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "update":
        cmd_update()
    elif cmd == "list":
        cmd_list()
    elif cmd == "install":
        if len(sys.argv) < 3:
            print(f"{C_RED}[!] Please specify a package name (e.g., 'lpkg install limbo-snake').{C_RESET}")
            sys.exit(1)
        cmd_install(sys.argv[2])
    elif cmd == "remove":
        if len(sys.argv) < 3:
            print(f"{C_RED}[!] Please specify a package name (e.g., 'lpkg remove limbo-snake').{C_RESET}")
            sys.exit(1)
        cmd_remove(sys.argv[2])
    elif cmd == "search":
        if len(sys.argv) < 3:
            print(f"{C_RED}[!] Please specify a search query.{C_RESET}")
            sys.exit(1)
        cmd_search(sys.argv[2])
    elif cmd == "info":
        if len(sys.argv) < 3:
            print(f"{C_RED}[!] Please specify a package name.{C_RESET}")
            sys.exit(1)
        cmd_info(sys.argv[2])
    elif cmd == "installed":
        cmd_installed()
    elif cmd == "help":
        cmd_help()
    else:
        print(f"{C_RED}[!] Unknown command '{cmd}'.{C_RESET}")
        print(f"    Run 'lpkg help' for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
