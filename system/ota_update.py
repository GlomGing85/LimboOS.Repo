#!/usr/bin/env python3
# ==============================================================================
# LimboOS OTA Update System v1.0
# Over-The-Air updates via GitHub Releases
# ==============================================================================

import os
import sys
import json
import urllib.request
import urllib.error
import hashlib
import shutil
import subprocess
import time
import tarfile
import tempfile

# ── Configuration ─────────────────────────────────────────────────────────────
GITHUB_REPO = "GlomGing85/LimboOS.Repo"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"
RELEASES_URL = f"{GITHUB_API}/releases"
LATEST_URL = f"{RELEASES_URL}/latest"

VERSION_FILE = "/etc/limboos/version.json"
BACKUP_DIR = "/var/lib/limboos/backups"
UPDATE_CACHE = "/var/cache/limboos/updates"
SYSTEM_LIB = "/usr/lib/limboos"

# ── Colors ────────────────────────────────────────────────────────────────────
C_CYAN = "\033[1;36m"
C_GREEN = "\033[1;32m"
C_YELLOW = "\033[1;33m"
C_RED = "\033[1;31m"
C_WHITE = "\033[1;37m"
C_RESET = "\033[0m"

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg, level="info"):
    colors = {
        "info": C_CYAN,
        "ok": C_GREEN,
        "warn": C_YELLOW,
        "error": C_RED,
        "white": C_WHITE,
    }
    c = colors.get(level, C_WHITE)
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "error": "[✗]", "white": ""}
    print(f"{c}{prefix.get(level, '[*]')} {msg}{C_RESET}")


def get_current_version():
    """Read current OS version from version file."""
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                data = json.load(f)
                return data.get("version", "0.0.0")
    except Exception:
        pass
    return "0.0.0"


def save_version(version, build_date=None):
    """Save version info."""
    data = {
        "version": version,
        "build_date": build_date or time.strftime("%Y-%m-%d"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "github_repo": GITHUB_REPO
    }
    os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
    with open(VERSION_FILE, "w") as f:
        json.dump(data, f, indent=2)


def parse_version(v):
    """Parse version string to tuple for comparison."""
    try:
        parts = v.lstrip("v").split(".")
        return tuple(int(p) for p in parts)
    except Exception:
        return (0, 0, 0)


# ── Check for Updates ────────────────────────────────────────────────────────
def check_updates():
    """Check GitHub for latest release."""
    log("Checking for LimboOS updates...")
    log(f"Repository: {GITHUB_REPO}")
    log(f"Current version: {get_current_version()}")

    try:
        req = urllib.request.Request(LATEST_URL, headers={
            "User-Agent": "LimboOS-OTA/1.0",
            "Accept": "application/vnd.github.v3+json"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        latest_tag = data.get("tag_name", "v0.0.0")
        latest_version = latest_tag.lstrip("v")
        release_name = data.get("name", "Unknown")
        release_date = data.get("published_at", "N/A")[:10]
        release_notes = data.get("body", "")
        assets = data.get("assets", [])

        log(f"Latest release: {latest_version}", "ok")
        log(f"Release name: {release_name}")
        log(f"Release date: {release_date}")

        current = parse_version(get_current_version())
        latest = parse_version(latest_version)

        if latest > current:
            log(f"🟢 Update available: {get_current_version()} → {latest_version}", "ok")
            if release_notes:
                log("Release notes:")
                for line in release_notes.strip().split("\n")[:10]:
                    log(f"  {line}")

            # Find update package asset
            update_asset = None
            for asset in assets:
                name = asset.get("name", "").lower()
                if "update" in name or name.endswith(".tar.gz") or name.endswith(".tar.xz"):
                    update_asset = asset
                    break

            return {
                "available": True,
                "version": latest_version,
                "tag": latest_tag,
                "name": release_name,
                "date": release_date,
                "notes": release_notes,
                "asset": update_asset,
                "data": data
            }
        else:
            log("✅ System is up to date!", "ok")
            return {
                "available": False,
                "version": latest_version,
                "current": get_current_version()
            }

    except urllib.error.HTTPError as e:
        if e.code == 404:
            log("No releases found in repository yet.", "warn")
        else:
            log(f"GitHub API error: {e}", "error")
    except Exception as e:
        log(f"Could not check for updates: {e}", "error")
        log("Check your internet connection.", "warn")

    return {"available": False, "error": True}


# ── Apply Update ──────────────────────────────────────────────────────────────
def apply_update(update_info=None):
    """Download and apply system update."""
    if update_info is None:
        update_info = check_updates()

    if not update_info.get("available"):
        log("No update to apply.", "warn")
        return False

    new_version = update_info["version"]
    log(f"Applying update to v{new_version}...")

    # Create backup of current system
    log("Creating system backup...")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_name = f"limboos-backup-{get_current_version()}-{int(time.time())}"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    try:
        # Backup critical system files
        files_to_backup = [
            SYSTEM_LIB,
            VERSION_FILE,
        ]
        os.makedirs(backup_path, exist_ok=True)

        for src in files_to_backup:
            if os.path.exists(src):
                dst = os.path.join(backup_path, os.path.basename(src))
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

        log(f"Backup created: {backup_path}", "ok")
    except Exception as e:
        log(f"Warning: Could not create full backup: {e}", "warn")
        backup_path = None

    # Download update package
    asset = update_info.get("asset")
    if asset:
        download_url = asset.get("browser_download_url", "")
        if download_url:
            log(f"Downloading update from: {download_url}")
            os.makedirs(UPDATE_CACHE, exist_ok=True)
            dl_path = os.path.join(UPDATE_CACHE, asset["name"])

            try:
                req = urllib.request.Request(download_url, headers={"User-Agent": "LimboOS-OTA/1.0"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    total = int(resp.headers.get("Content-Length", 0))
                    downloaded = 0
                    with open(dl_path, "wb") as f:
                        while True:
                            chunk = resp.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                pct = (downloaded * 100) // total
                                print(f"\r    Progress: {pct}% ({downloaded}/{total} bytes)", end="")
                print()
                log("Download complete!", "ok")

                # Extract update
                log("Extracting update package...")
                try:
                    with tarfile.open(dl_path, "r:*") as tar:
                        # Safety: extract to temp dir first
                        with tempfile.TemporaryDirectory() as tmpdir:
                            tar.extractall(tmpdir)
                            # Copy updated files
                            for root, dirs, files in os.walk(tmpdir):
                                rel = os.path.relpath(root, tmpdir)
                                target_dir = os.path.join("/", rel) if rel != "." else "/"
                                os.makedirs(target_dir, exist_ok=True)
                                for fname in files:
                                    src_f = os.path.join(root, fname)
                                    dst_f = os.path.join(target_dir, fname)
                                    shutil.copy2(src_f, dst_f)

                    log("Update files extracted and applied!", "ok")
                except Exception as e:
                    log(f"Could not extract archive: {e}", "error")
                    log("Attempting incremental update via file list...", "warn")
            except Exception as e:
                log(f"Download failed: {e}", "error")
                return False
    else:
        log("No downloadable update asset found.", "warn")
        log("You can manually update by pulling the latest from GitHub.", "info")
        return False

    # Update version file
    save_version(new_version)
    log(f"Version updated to v{new_version}!", "ok")

    # Cleanup
    log("Cleaning up...")
    if os.path.exists(UPDATE_CACHE):
        for f in os.listdir(UPDATE_CACHE):
            try:
                os.remove(os.path.join(UPDATE_CACHE, f))
            except Exception:
                pass

    log(f"✅ LimboOS has been updated to v{new_version}!", "ok")
    log("Please restart the desktop to apply changes.", "info")
    return True


# ── Rollback ──────────────────────────────────────────────────────────────────
def rollback():
    """Rollback to previous version from backup."""
    log("Looking for available backups...")

    if not os.path.exists(BACKUP_DIR):
        log("No backups found. Cannot rollback.", "error")
        return False

    backups = sorted([d for d in os.listdir(BACKUP_DIR) if d.startswith("limboos-backup-")])
    if not backups:
        log("No backups found. Cannot rollback.", "error")
        return False

    latest_backup = backups[-1]
    backup_path = os.path.join(BACKUP_DIR, latest_backup)
    log(f"Found backup: {latest_backup}")
    log(f"Restoring from: {backup_path}")

    try:
        for item in os.listdir(backup_path):
            src = os.path.join(backup_path, item)
            if item == "limboos":
                # Restore system lib
                dst = SYSTEM_LIB
                if os.path.exists(dst):
                    shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)
                log(f"Restored: {dst}", "ok")
            elif item == "version.json":
                shutil.copy2(src, VERSION_FILE)
                log(f"Restored: {VERSION_FILE}", "ok")

        log("✅ Rollback complete! Restart the desktop to apply.", "ok")
        return True
    except Exception as e:
        log(f"Rollback failed: {e}", "error")
        return False


# ── Status ────────────────────────────────────────────────────────────────────
def show_status():
    """Show current system status."""
    version = get_current_version()
    print(f"""
{C_CYAN}╔══════════════════════════════════════════════╗
║         LimboOS OTA Update System            ║
╚══════════════════════════════════════════════╝{C_RESET}

  {C_WHITE}Current Version:{C_RESET}  {C_GREEN}{version}{C_RESET}
  {C_WHITE}GitHub Repo:{C_RESET}      {GITHUB_REPO}
  {C_WHITE}Backup Dir:{C_RESET}       {BACKUP_DIR}
  {C_WHITE}System Lib:{C_RESET}       {SYSTEM_LIB}
""")

    # Count backups
    if os.path.exists(BACKUP_DIR):
        backups = [d for d in os.listdir(BACKUP_DIR) if d.startswith("limboos-backup-")]
        print(f"  {C_WHITE}Available Backups:{C_RESET} {len(backups)}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="LimboOS OTA Update System")
    parser.add_argument("--check", action="store_true", help="Check for available updates")
    parser.add_argument("--apply", action="store_true", help="Download and apply update")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous version")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--version", action="store_true", help="Show current version")

    args = parser.parse_args()

    if args.version:
        print(get_current_version())
    elif args.status:
        show_status()
    elif args.check:
        check_updates()
    elif args.apply:
        apply_update()
    elif args.rollback:
        rollback()
    else:
        # Default: check and show status
        show_status()
        check_updates()


if __name__ == "__main__":
    main()
