#!/bin/bash
# ==============================================================================
# Download Linux Kernel for LimboOS
# Downloads kernel + creates initrd for booting in Limbo PC Emulator
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARCH="${1:-x86_64}"

echo " __    _       _          _____ _____ "
echo "|  |  |_|_____| |_ ___   |     |   __|"
echo "|  |__| |     | . | . |  |  |  |__   |"
echo "|_____|_|_|_|_|___|___|  |_____|_____|"
echo ""
echo "  LimboOS Kernel Download"
echo "  Architecture: $ARCH"
echo ""

if [ "$ARCH" = "x86_64" ]; then
    KERNEL_URL="https://kernel.ubuntu.com/~kernel-ppa/mainline/v6.1.0/amd64/linux-image-unsigned-6.1.0-060100-generic_6.1.0-060100.202212111931_amd64.deb"
elif [ "$ARCH" = "x86" ]; then
    echo "[!] 32-bit kernel — use Debian package:"
    KERNEL_URL="http://ftp.debian.org/debian/pool/main/l/linux/linux-image-6.1.0-18-686-pae_6.1.76-1_i386.deb"
else
    echo "[!] Unknown arch: $ARCH (use x86 or x86_64)"
    exit 1
fi

echo "[*] Downloading kernel from:"
echo "    $KERNEL_URL"

cd "$SCRIPT_DIR"

# Download
if command -v wget &>/dev/null; then
    wget -q --show-progress "$KERNEL_URL" -O kernel.deb
elif command -v curl &>/dev/null; then
    curl -L "$KERNEL_URL" -o kernel.deb
else
    echo "[!] Install wget or curl"
    exit 1
fi

echo "[+] Downloaded."

# Extract
echo "[*] Extracting..."
if command -v dpkg &>/dev/null; then
    mkdir -p kernel_tmp
    dpkg -x kernel.deb kernel_tmp
elif command -v ar &>/dev/null; then
    mkdir -p kernel_tmp
    cd kernel_tmp
    ar x ../kernel.deb
    tar -xf data.tar.xz 2>/dev/null || tar -xf data.tar.gz 2>/dev/null || true
    cd ..
else
    echo "[!] Install dpkg: apt install dpkg"
    exit 1
fi

# Find vmlinuz
VMLINUZ=$(find kernel_tmp -name "vmlinuz*" -type f 2>/dev/null | head -1)
INITRD=$(find kernel_tmp -name "initrd*" -type f 2>/dev/null | head -1)

if [ -z "$VMLINUZ" ]; then
    # Try alternative paths
    VMLINUZ=$(find kernel_tmp -path "*/boot/vmlinuz*" -type f 2>/dev/null | head -1)
fi

if [ -z "$VMLINUZ" ]; then
    echo "[!] vmlinuz not found!"
    find kernel_tmp -type f -name "*.img" -o -name "vmlinuz*" -o -name "bzImage" 2>/dev/null
    echo "[!] Try building kernel from source or use a different package."
    exit 1
fi

cp "$VMLINUZ" "${SCRIPT_DIR}/vmlinuz"
echo "[+] vmlinuz → build/vmlinuz"

if [ -n "$INITRD" ]; then
    cp "$INITRD" "${SCRIPT_DIR}/initrd.img"
    echo "[+] initrd.img → build/initrd.img"
else
    echo "[*] Creating minimal initrd..."
    INITRD_DIR=$(mktemp -d)
    mkdir -p "${INITRD_DIR}/bin" "${INITRD_DIR}/proc" "${INITRD_DIR}/sys" "${INITRD_DIR}/root"

    cat > "${INITRD_DIR}/init" << 'INITEOF'
#!/bin/sh
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev 2>/dev/null
echo "LimboOS: mounting root..."
mount /dev/sda1 /root 2>/dev/null
if [ -d /root/usr ]; then
    exec switch_root /root /sbin/init
else
    echo "ERROR: root not found!"
    exec /bin/sh
fi
INITEOF
    chmod +x "${INITRD_DIR}/init"

    cd "$INITRD_DIR"
    find . | cpio -H newc -o 2>/dev/null | gzip > "${SCRIPT_DIR}/initrd.img"
    cd "$SCRIPT_DIR"
    rm -rf "$INITRD_DIR"
    echo "[+] Minimal initrd created."
fi

rm -f kernel.deb
rm -rf kernel_tmp

echo ""
echo "[+] Kernel ready:"
echo "    build/vmlinuz"
echo "    build/initrd.img"
echo ""
echo "[*] Now run: bash build_limboos.sh  OR  bash build_on_termux.sh"
echo ""
