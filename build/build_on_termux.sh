#!/bin/bash
# ==============================================================================
# LimboOS Build Script for Termux / proot-distro Ubuntu
# Works inside proot-distro Ubuntu on Android (no root needed)
# Creates a filesystem image that can be booted in Limbo
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${SCRIPT_DIR}/output"
WORK_DIR="${SCRIPT_DIR}/work"

mkdir -p "$BUILD_DIR" "$WORK_DIR"

echo " __    _       _          _____ _____ "
echo "|  |  |_|_____| |_ ___   |     |   __|"
echo "|  |__| |     | . | . |  |  |  |__   |"
echo "|_____|_|_|_|_|___|___|  |_____|_____|"
echo ""
echo "  LimboOS Build (Termux/proot Edition)"
echo ""

IMAGE_SIZE_MB=300
ARCH="${1:-x86_64}"
OUTPUT_IMG="${BUILD_DIR}/limboos-1.0.0-${ARCH}.img"
OUTPUT_QCOW2="${BUILD_DIR}/limboos-1.0.0-${ARCH}.qcow2"

# ── Check tools ───────────────────────────────────────────────────────────────
for tool in qemu-img mkfs.ext4 python3; do
    command -v "$tool" &>/dev/null || { echo "[!] Missing: $tool — apt install qemu-utils e2fsprogs python3"; exit 1; }
done
echo "[+] All tools available."

# ── 1. Create disk image ─────────────────────────────────────────────────────
echo "[★] Creating disk image (${IMAGE_SIZE_MB} MB)..."
qemu-img create -f raw "$OUTPUT_IMG" "${IMAGE_SIZE_MB}M"

# Try loop device
LOOP_DEV=""
MOUNT_DIR=""

if command -v losetup &>/dev/null; then
    LOOP_DEV=$(losetup -f --show "$OUTPUT_IMG" 2>/dev/null) || LOOP_DEV=""
fi

if [ -n "$LOOP_DEV" ]; then
    echo "type=83, bootable" | sfdisk "$LOOP_DEV" 2>/dev/null || true
    PART_DEV="${LOOP_DEV}p1"
    [[ ! -e "$PART_DEV" ]] && PART_DEV="$LOOP_DEV"

    mkfs.ext4 -F -L "LimboOS" "$PART_DEV"
    MOUNT_DIR=$(mktemp -d)
    mount "$PART_DEV" "$MOUNT_DIR"
    echo "[+] Mounted at: $MOUNT_DIR"
else
    echo "[!] No loop device — using file-based approach"
    FS_IMG="${WORK_DIR}/rootfs.img"
    qemu-img create -f raw "$FS_IMG" "${IMAGE_SIZE_MB}M"
    mkfs.ext4 -F -L "LimboOS" "$FS_IMG"
    MOUNT_DIR=$(mktemp -d)
    if mount -o loop "$FS_IMG" "$MOUNT_DIR" 2>/dev/null; then
        echo "[+] Mounted at: $MOUNT_DIR"
    else
        echo "[!] Cannot mount — using directory mode"
        MOUNT_DIR="${WORK_DIR}/rootfs_dir"
        mkdir -p "$MOUNT_DIR"
    fi
fi

# ── 2. Populate rootfs ───────────────────────────────────────────────────────
echo "[★] Populating root filesystem..."
ROOTFS="$MOUNT_DIR"

mkdir -p "${ROOTFS}"/{bin,sbin,usr/bin,usr/sbin,usr/lib,lib}
mkdir -p "${ROOTFS}"/{proc,sys,dev,tmp,run,mnt}
mkdir -p "${ROOTFS}"/{etc,etc/init.d,etc/limboos}
mkdir -p "${ROOTFS}"/{home/user,var/lib/lpkg,var/log/limboos}
mkdir -p "${ROOTFS}"/opt/limboos/apps
mkdir -p "${ROOTFS}/usr/lib/limboos"
mkdir -p "${ROOTFS}/boot"

cat > "${ROOTFS}/etc/limboos-release" << 'EOF'
NAME="LimboOS"
VERSION="1.0.0"
CODENAME="Genesis"
PRETTY_NAME="LimboOS Linux v1.0.0"
ID=limboos
EOF

echo "limboos-linux" > "${ROOTFS}/etc/hostname"

cat > "${ROOTFS}/etc/hosts" << 'EOF'
127.0.0.1  localhost
127.0.1.1  limboos-linux
EOF

cat > "${ROOTFS}/etc/fstab" << 'EOF'
/dev/sda1  /   ext4  defaults,noatime  0 1
proc       /proc  proc  defaults  0 0
sysfs      /sys   sysfs defaults  0 0
tmpfs      /tmp   tmpfs defaults  0 0
EOF

cat > "${ROOTFS}/etc/inittab" << 'EOF'
::sysinit:/etc/init.d/rcS
::respawn:/sbin/getty -L tty1 0 vt100
::ctrlaltdel:/sbin/reboot
EOF

mkdir -p "${ROOTFS}/etc/init.d"
cat > "${ROOTFS}/etc/init.d/rcS" << 'EOF'
#!/bin/sh
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev 2>/dev/null
mount -t tmpfs tmpfs /tmp
hostname -F /etc/hostname
echo "LimboOS initialized."
EOF
chmod +x "${ROOTFS}/etc/init.d/rcS"

# ── 3. Install LimboOS files ─────────────────────────────────────────────────
echo "[★] Installing LimboOS components..."

for f in limboos_desktop.py limboos_desktop_v2.py limboos_theme.py; do
    [[ -f "${PROJECT_DIR}/desktop/$f" ]] && cp "${PROJECT_DIR}/desktop/$f" "${ROOTFS}/usr/lib/limboos/"
done
[[ -f "${PROJECT_DIR}/desktop/limboos_autostart.sh" ]] && cp "${PROJECT_DIR}/desktop/limboos_autostart.sh" "${ROOTFS}/usr/bin/" && chmod +x "${ROOTFS}/usr/bin/limboos_autostart.sh"

[[ -f "${PROJECT_DIR}/lpkg/lpkg.py" ]] && cp "${PROJECT_DIR}/lpkg/lpkg.py" "${ROOTFS}/usr/bin/lpkg" && chmod +x "${ROOTFS}/usr/bin/lpkg"
[[ -f "${PROJECT_DIR}/lpkg/repo_manifest.json" ]] && cp "${PROJECT_DIR}/lpkg/repo_manifest.json" "${ROOTFS}/var/lib/lpkg/"

[[ -f "${PROJECT_DIR}/system/ota_update.py" ]] && cp "${PROJECT_DIR}/system/ota_update.py" "${ROOTFS}/usr/bin/limboos-update" && chmod +x "${ROOTFS}/usr/bin/limboos-update"

for app_dir in "${PROJECT_DIR}/Apps"/*/; do
    [[ -d "$app_dir" ]] || continue
    app_name=$(basename "$app_dir")
    mkdir -p "${ROOTFS}/opt/limboos/apps/${app_name}"
    cp -r "${app_dir}"* "${ROOTFS}/opt/limboos/apps/${app_name}/" 2>/dev/null || true
done

ok() { echo "[+] $1"; }
ok "Components installed."

# ── 4. Boot files ─────────────────────────────────────────────────────────────
echo "[★] Setting up boot..."

mkdir -p "${ROOTFS}/boot/grub"

if [[ -f "${SCRIPT_DIR}/vmlinuz" && -f "${SCRIPT_DIR}/initrd.img" ]]; then
    cp "${SCRIPT_DIR}/vmlinuz" "${ROOTFS}/boot/"
    cp "${SCRIPT_DIR}/initrd.img" "${ROOTFS}/boot/"
    ok "Kernel files copied."
else
    echo "[!] No vmlinuz/initrd in build/ — run: bash download_kernel.sh"
    cat > "${ROOTFS}/boot/README.txt" << 'EOF'
Place vmlinuz and initrd.img here.
Run: bash build/download_kernel.sh x86_64
EOF
fi

cat > "${ROOTFS}/boot/grub/grub.cfg" << 'EOF'
set timeout=3
menuentry "LimboOS Linux v1.0" {
    linux /boot/vmlinuz root=/dev/sda1 rw quiet
    initrd /boot/initrd.img
}
menuentry "LimboOS (Recovery)" {
    linux /boot/vmlinuz root=/dev/sda1 rw single
    initrd /boot/initrd.img
}
EOF

# ── 5. Finalize ──────────────────────────────────────────────────────────────
echo "[★] Finalizing..."

if [ -n "${LOOP_DEV:-}" ]; then
    umount "$MOUNT_DIR" 2>/dev/null || true
    losetup -d "$LOOP_DEV" 2>/dev/null || true
else
    umount "$MOUNT_DIR" 2>/dev/null || true
fi
rmdir "$MOUNT_DIR" 2>/dev/null || true

# Convert to qcow2
echo "[*] Converting to qcow2..."
qemu-img convert -f raw -O qcow2 "$OUTPUT_IMG" "$OUTPUT_QCOW2"

cd "$BUILD_DIR"
sha256sum *.img *.qcow2 2>/dev/null > checksums.sha256 || true

echo ""
echo "============================================================================"
echo "  Build Complete!"
echo "============================================================================"
echo ""
ls -lh "$BUILD_DIR"
echo ""
echo "  Next: Copy .qcow2 to Android, open in Limbo as Hard Disk."
echo ""
