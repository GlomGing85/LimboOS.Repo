#!/bin/bash
# ==============================================================================
# LimboOS Main Build Script — for GitHub Codespaces / Full Linux
# Creates bootable .img and .qcow2 disk image for Limbo PC Emulator
# ==============================================================================
# Usage:
#   sudo bash build_limboos.sh [--arch x86|x86_64] [--size 300]
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${SCRIPT_DIR}/output"
WORK_DIR="${SCRIPT_DIR}/work"
ROOTFS_DIR="${WORK_DIR}/rootfs"

ARCH="x86"
IMAGE_SIZE_MB=300

while [[ $# -gt 0 ]]; do
    case $1 in
        --arch) ARCH="$2"; shift 2 ;;
        --size) IMAGE_SIZE_MB="$2"; shift 2 ;;
        *) shift ;;
    esac
done

CYAN='\033[1;36m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; NC='\033[0m'

step() { echo -e "\n${YELLOW}[★] $1${NC}"; }
ok()   { echo -e "${GREEN}  [+] $1${NC}"; }
fail() { echo -e "${RED}  [!] $1${NC}"; exit 1; }

echo -e "${CYAN}"
echo " __    _       _          _____ _____ "
echo "|  |  |_|_____| |_ ___   |     |   __|"
echo "|  |__| |     | . | . |  |  |  |__   |"
echo "|_____|_|_|_|_|___|___|  |_____|_____|"
echo -e "${NC}"
echo -e "${GREEN}  LimboOS Build System v1.0 [Genesis]${NC}"
echo -e "${CYAN}  Arch: ${ARCH} | Size: ${IMAGE_SIZE_MB}MB${NC}"

# ── Preflight ─────────────────────────────────────────────────────────────────
step "Checking prerequisites..."
if [[ $EUID -ne 0 ]]; then fail "Run with sudo"; fi

for tool in debootstrap grub-mkrescue xorriso mtools qemu-img mkfs.ext4; do
    command -v "$tool" &>/dev/null || MISSING="$MISSING $tool"
done
if [[ -n "$MISSING" ]]; then
    echo -e "${YELLOW}  Install: apt-get install debootstrap grub-pc-bin grub-common xorriso mtools qemu-utils e2fsprogs${NC}"
    fail "Missing:$MISSING"
fi
ok "All prerequisites OK."

# ── Clean ─────────────────────────────────────────────────────────────────────
step "Cleaning..."
rm -rf "${WORK_DIR}"
mkdir -p "${BUILD_DIR}" "${WORK_DIR}" "${ROOTFS_DIR}"

# ── 1. Rootfs via debootstrap ─────────────────────────────────────────────────
step "Creating rootfs (Debian bookworm minbase)..."

debootstrap --arch=i386 --variant=minbase \
    --include=python3,python3-tk,busybox-static,kmod,procps,\
kbd,console-setup,xterm,x11-xserver-utils,libtk8.6,libtcl8.6 \
    bookworm "${ROOTFS_DIR}" http://deb.debian.org/debian/ \
    || fail "debootstrap failed. Check internet and arch."
ok "Rootfs base created."

# ── 2. Configure rootfs ──────────────────────────────────────────────────────
step "Configuring LimboOS..."

mkdir -p "${ROOTFS_DIR}"/{proc,sys,dev,tmp,run,mnt/media}
mkdir -p "${ROOTFS_DIR}/usr/lib/limboos"
mkdir -p "${ROOTFS_DIR}/var/lib/lpkg"
mkdir -p "${ROOTFS_DIR}/var/log/limboos"
mkdir -p "${ROOTFS_DIR}/etc/limboos"
mkdir -p "${ROOTFS_DIR}/opt/limboos/apps"
mkdir -p "${ROOTFS_DIR}/home/user"

cat > "${ROOTFS_DIR}/etc/limboos-release" << 'EOF'
NAME="LimboOS"
VERSION="1.0.0"
CODENAME="Genesis"
PRETTY_NAME="LimboOS Linux v1.0.0 (Genesis)"
ID=limboos
EOF

cp "${PROJECT_DIR}/system/version.json" "${ROOTFS_DIR}/etc/limboos/" 2>/dev/null || true
echo "limboos-linux" > "${ROOTFS_DIR}/etc/hostname"

cat > "${ROOTFS_DIR}/etc/hosts" << 'EOF'
127.0.0.1   localhost
127.0.1.1   limboos-linux
EOF

cat > "${ROOTFS_DIR}/etc/fstab" << 'EOF'
/dev/sda1   /       ext4    defaults,noatime    0 1
proc        /proc   proc    defaults            0 0
sysfs       /sys    sysfs   defaults            0 0
tmpfs       /tmp    tmpfs   defaults            0 0
EOF

cat > "${ROOTFS_DIR}/etc/inittab" << 'EOF'
::sysinit:/etc/init.d/rcS
::respawn:/sbin/getty -L tty1 0 vt100
::ctrlaltdel:/sbin/reboot
::shutdown:/bin/umount -a -r
EOF

mkdir -p "${ROOTFS_DIR}/etc/init.d"
cat > "${ROOTFS_DIR}/etc/init.d/rcS" << 'INITEOF'
#!/bin/sh
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev 2>/dev/null
mount -t tmpfs tmpfs /tmp
hostname -F /etc/hostname
echo "LimboOS Linux initialized."
INITEOF
chmod +x "${ROOTFS_DIR}/etc/init.d/rcS"

# ── 3. Install LimboOS components ─────────────────────────────────────────────
step "Installing LimboOS components..."

# Desktop
for f in limboos_desktop.py limboos_desktop_v2.py limboos_theme.py; do
    [[ -f "${PROJECT_DIR}/desktop/$f" ]] && cp "${PROJECT_DIR}/desktop/$f" "${ROOTFS_DIR}/usr/lib/limboos/"
done
[[ -f "${PROJECT_DIR}/desktop/limboos_autostart.sh" ]] && cp "${PROJECT_DIR}/desktop/limboos_autostart.sh" "${ROOTFS_DIR}/usr/bin/" && chmod +x "${ROOTFS_DIR}/usr/bin/limboos_autostart.sh"
ok "Desktop installed."

# lpkg
[[ -f "${PROJECT_DIR}/lpkg/lpkg.py" ]] && cp "${PROJECT_DIR}/lpkg/lpkg.py" "${ROOTFS_DIR}/usr/bin/lpkg" && chmod +x "${ROOTFS_DIR}/usr/bin/lpkg"
[[ -f "${PROJECT_DIR}/lpkg/repo_manifest.json" ]] && cp "${PROJECT_DIR}/lpkg/repo_manifest.json" "${ROOTFS_DIR}/var/lib/lpkg/"
ok "lpkg installed."

# OTA
[[ -f "${PROJECT_DIR}/system/ota_update.py" ]] && cp "${PROJECT_DIR}/system/ota_update.py" "${ROOTFS_DIR}/usr/bin/limboos-update" && chmod +x "${ROOTFS_DIR}/usr/bin/limboos-update"
ok "OTA system installed."

# Apps
for app_dir in "${PROJECT_DIR}/Apps"/*/; do
    [[ -d "$app_dir" ]] || continue
    app_name=$(basename "$app_dir")
    mkdir -p "${ROOTFS_DIR}/opt/limboos/apps/${app_name}"
    cp -r "${app_dir}"* "${ROOTFS_DIR}/opt/limboos/apps/${app_name}/" 2>/dev/null || true
done
ok "Built-in apps installed."

# ── 4. Kernel & Boot ─────────────────────────────────────────────────────────
step "Setting up boot files..."

mkdir -p "${ROOTFS_DIR}/boot/grub"

# Check for pre-downloaded kernel
if [[ -f "${SCRIPT_DIR}/vmlinuz" && -f "${SCRIPT_DIR}/initrd.img" ]]; then
    cp "${SCRIPT_DIR}/vmlinuz" "${ROOTFS_DIR}/boot/"
    cp "${SCRIPT_DIR}/initrd.img" "${ROOTFS_DIR}/boot/"
    ok "Kernel files copied from build/."
else
    echo -e "${YELLOW}  No kernel in build/. Run: bash download_kernel.sh${NC}"
    echo -e "${YELLOW}  Or place vmlinuz + initrd.img in build/ directory.${NC}"
    cat > "${ROOTFS_DIR}/boot/README.txt" << 'EOF'
LimboOS Boot Files Needed:
1. vmlinuz  — Linux kernel (download via download_kernel.sh)
2. initrd.img — initial ramdisk

Place both files in /boot/ before creating the disk image.
EOF
fi

cat > "${ROOTFS_DIR}/boot/grub/grub.cfg" << 'EOF'
set timeout=3
set default=0
menuentry "LimboOS Linux v1.0 (Genesis)" {
    linux /boot/vmlinuz root=/dev/sda1 rw quiet splash
    initrd /boot/initrd.img
}
menuentry "LimboOS (Recovery)" {
    linux /boot/vmlinuz root=/dev/sda1 rw single
    initrd /boot/initrd.img
}
EOF

# ── 5. Create disk image ─────────────────────────────────────────────────────
step "Creating disk image (${IMAGE_SIZE_MB} MB)..."

OUTPUT_IMG="${BUILD_DIR}/limboos-1.0.0-${ARCH}.img"
OUTPUT_QCOW2="${BUILD_DIR}/limboos-1.0.0-${ARCH}.qcow2"

qemu-img create -f raw "$OUTPUT_IMG" "${IMAGE_SIZE_MB}M"

# Partition
echo -e "o\nn\np\n1\n\n\na\n1\nw" | fdisk "$OUTPUT_IMG" 2>/dev/null || true

LOOP_DEV=$(losetup -f --show "$OUTPUT_IMG")
PART_DEV="${LOOP_DEV}p1"
[[ ! -e "$PART_DEV" ]] && PART_DEV="$LOOP_DEV"

mkfs.ext4 -F -L "LimboOS" "$PART_DEV"

MOUNT_DIR=$(mktemp -d)
mount "$PART_DEV" "$MOUNT_DIR"
cp -a "${ROOTFS_DIR}/." "$MOUNT_DIR/"

# Install GRUB
grub-install --target=i386-pc --boot-directory="${MOUNT_DIR}/boot" "$LOOP_DEV" 2>/dev/null || true
umount "$MOUNT_DIR"
losetup -d "$LOOP_DEV"

ok "Raw image created: $OUTPUT_IMG"

# ── 6. Convert to qcow2 ──────────────────────────────────────────────────────
step "Converting to qcow2..."
qemu-img convert -f raw -O qcow2 "$OUTPUT_IMG" "$OUTPUT_QCOW2"
ok "qcow2 image: $OUTPUT_QCOW2"

# ── 7. Checksums ─────────────────────────────────────────────────────────────
step "Generating checksums..."
cd "$BUILD_DIR"
for f in *.img *.qcow2; do
    [[ -f "$f" ]] || continue
    sha256sum "$f" > "${f}.sha256"
done

# ── Done! ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}============================================================================${NC}"
echo -e "${GREEN}  LimboOS Build Complete!${NC}"
echo -e "${CYAN}============================================================================${NC}"
echo ""
ls -lh "$BUILD_DIR/"
echo ""
echo "  Import into Limbo PC Emulator:"
echo "  - Architecture: x86 (or x86_64)"
echo "  - RAM: 512 MB"
echo "  - Hard Disk: limboos-1.0.0-x86.qcow2"
echo "  - Boot from: Hard Disk"
echo ""
