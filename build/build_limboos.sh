#!/bin/bash
# LimboOS Build Script — Alpine-based (works in Codespaces)
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${SCRIPT_DIR}/output"
WORK_DIR="${SCRIPT_DIR}/work"
ROOTFS_DIR="${WORK_DIR}/rootfs"

ARCH="x86_64"
IMAGE_SIZE_MB=300

while [[ $# -gt 0 ]]; do
    case $1 in
        --arch) ARCH="$2"; shift 2 ;;
        --size) IMAGE_SIZE_MB="$2"; shift 2 ;;
        *) shift ;;
    esac
done

echo " __    _       _          _____ _____ "
echo "|  |  |_|_____| |_ ___   |     |   __|"
echo "|  |__| |     | . | . |  |  |  |__   |"
echo "|_____|_|_|_|_|___|___|  |_____|_____|"
echo ""
echo "  LimboOS Build — Alpine Edition"
echo "  Arch: ${ARCH} | Size: ${IMAGE_SIZE_MB}MB"
echo ""

# Check tools
for tool in qemu-img mkfs.ext4 python3 wget cpio gzip; do
    command -v "$tool" &>/dev/null || { echo "[!] Missing: $tool"; echo "    Install: apt install qemu-utils e2fsprogs python3 wget cpio gzip"; exit 1; }
done

# Clean
rm -rf "${WORK_DIR}"
mkdir -p "${BUILD_DIR}" "${WORK_DIR}" "${ROOTFS_DIR}"

# Download Alpine rootfs
echo "[1/7] Downloading Alpine rootfs..."
ALPINE_VER="3.19"
wget -q "https://dl-cdn.alpinelinux.org/alpine/v${ALPINE_VER}/releases/${ARCH}/alpine-minirootfs-${ALPINE_VER}.0-${ARCH}.tar.gz" -O "${WORK_DIR}/alpine.tar.gz"
tar -xzf "${WORK_DIR}/alpine.tar.gz" -C "${ROOTFS_DIR}"
rm "${WORK_DIR}/alpine.tar.gz"
echo "[+] Alpine rootfs extracted"

# Configure
echo "[2/7] Configuring LimboOS..."
mkdir -p "${ROOTFS_DIR}"/{etc/limboos,var/lib/lpkg,usr/lib/limboos,opt/limboos/apps,home/user}

cat > "${ROOTFS_DIR}/etc/limboos-release" << 'EOF'
NAME="LimboOS"
VERSION="1.0.0"
CODENAME="Genesis"
ID=limboos
EOF

echo "limboos-linux" > "${ROOTFS_DIR}/etc/hostname"

cat > "${ROOTFS_DIR}/etc/hosts" << 'EOF'
127.0.0.1  localhost
127.0.1.1  limboos-linux
EOF

cat > "${ROOTFS_DIR}/etc/fstab" << 'EOF'
/dev/sda1  /  ext4  defaults  0 1
proc  /proc  proc  defaults  0 0
EOF

cat > "${ROOTFS_DIR}/usr/bin/limboos-autostart.sh" << 'EOF'
#!/bin/sh
export DISPLAY=:0
export HOME=/home/user
python3 /usr/lib/limboos/limboos_desktop_v2.py
EOF
chmod +x "${ROOTFS_DIR}/usr/bin/limboos-autostart.sh"
echo "[+] Configured"

# Install LimboOS files
echo "[3/7] Installing LimboOS components..."
for f in limboos_desktop.py limboos_desktop_v2.py limboos_theme.py; do
    [[ -f "${PROJECT_DIR}/desktop/$f" ]] && cp "${PROJECT_DIR}/desktop/$f" "${ROOTFS_DIR}/usr/lib/limboos/"
done

[[ -f "${PROJECT_DIR}/lpkg/lpkg.py" ]] && cp "${PROJECT_DIR}/lpkg/lpkg.py" "${ROOTFS_DIR}/usr/bin/lpkg" && chmod +x "${ROOTFS_DIR}/usr/bin/lpkg"
[[ -f "${PROJECT_DIR}/lpkg/repo_manifest.json" ]] && cp "${PROJECT_DIR}/lpkg/repo_manifest.json" "${ROOTFS_DIR}/var/lib/lpkg/"

[[ -f "${PROJECT_DIR}/system/ota_update.py" ]] && cp "${PROJECT_DIR}/system/ota_update.py" "${ROOTFS_DIR}/usr/bin/limboos-update" && chmod +x "${ROOTFS_DIR}/usr/bin/limboos-update"

for app_dir in "${PROJECT_DIR}/Apps"/*/; do
    [[ -d "$app_dir" ]] || continue
    app_name=$(basename "$app_dir")
    mkdir -p "${ROOTFS_DIR}/opt/limboos/apps/${app_name}"
    cp -r "${app_dir}"* "${ROOTFS_DIR}/opt/limboos/apps/${app_name}/" 2>/dev/null || true
done
echo "[+] Components installed"

# Kernel
echo "[4/7] Setting up boot files..."
mkdir -p "${ROOTFS_DIR}/boot/grub"

if [[ -f "${SCRIPT_DIR}/vmlinuz" && -f "${SCRIPT_DIR}/initrd.img" ]]; then
    cp "${SCRIPT_DIR}/vmlinuz" "${ROOTFS_DIR}/boot/"
    cp "${SCRIPT_DIR}/initrd.img" "${ROOTFS_DIR}/boot/"
    echo "[+] Kernel copied"
else
    echo "[!] No kernel — run: bash download_kernel.sh"
fi

cat > "${ROOTFS_DIR}/boot/grub/grub.cfg" << 'EOF'
set timeout=3
menuentry "LimboOS Linux v1.0" {
    linux /boot/vmlinuz root=/dev/sda1 rw quiet
    initrd /boot/initrd.img
}
EOF

# Create disk image
echo "[5/7] Creating disk image..."
OUTPUT_IMG="${BUILD_DIR}/limboos-1.0.0-${ARCH}.img"
qemu-img create -f raw "$OUTPUT_IMG" "${IMAGE_SIZE_MB}M"

if command -v losetup &>/dev/null && command -v fdisk &>/dev/null; then
    echo -e "o\nn\np\n1\n\n\na\n1\nw" | fdisk "$OUTPUT_IMG" 2>/dev/null || true
    LOOP=$(losetup -f --show "$OUTPUT_IMG" 2>/dev/null) || LOOP=""
    
    if [[ -n "$LOOP" ]]; then
        PART="${LOOP}p1"
        [[ ! -e "$PART" ]] && PART="$LOOP"
        mkfs.ext4 -F -L "LimboOS" "$PART"
        MNT=$(mktemp -d)
        mount "$PART" "$MNT"
        cp -a "${ROOTFS_DIR}/." "$MNT/"
        umount "$MNT"
        losetup -d "$LOOP"
        echo "[+] Image with partitions"
    else
        mkfs.ext4 -F -L "LimboOS" "$OUTPUT_IMG"
        MNT=$(mktemp -d)
        mount -o loop "$OUTPUT_IMG" "$MNT" 2>/dev/null && cp -a "${ROOTFS_DIR}/." "$MNT/" && umount "$MNT"
        rmdir "$MNT"
        echo "[+] Simple image"
    fi
else
    cd "${ROOTFS_DIR}" && find . | cpio -H newc -o 2>/dev/null | gzip > "${BUILD_DIR}/initrd.img" && cd "$SCRIPT_DIR"
    echo "[+] Initrd created"
fi

# Convert to qcow2
echo "[6/7] Converting to qcow2..."
OUTPUT_QCOW2="${BUILD_DIR}/limboos-1.0.0-${ARCH}.qcow2"
qemu-img convert -f raw -O qcow2 "$OUTPUT_IMG" "$OUTPUT_QCOW2"

# Checksums
echo "[7/7] Checksums..."
cd "$BUILD_DIR"
sha256sum *.img *.qcow2 2>/dev/null > checksums.sha256 || true

echo ""
echo "================================================================"
echo "  Build Complete!"
echo "================================================================"
ls -lh "$BUILD_DIR/"
echo ""
echo "  Limbo settings: x86_64, RAM 512MB, Hard Disk: .qcow2"
echo ""
