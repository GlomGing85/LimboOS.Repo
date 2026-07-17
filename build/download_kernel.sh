#!/bin/bash
# ==============================================================================
# Download Linux Kernel for LimboOS (Alpine-based)
# Downloads Alpine linux-lts kernel package
# ==============================================================================

set -eo pipefail

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

ALPINE_VERSION="3.19"
KERNEL_PKG="linux-lts"

if [ "$ARCH" = "x86_64" ]; then
    KERNEL_URL="https://dl-cdn.alpinelinux.org/alpine/v${ALPINE_VERSION}/main/${ARCH}/${KERNEL_PKG}-6.6.10-r0.apk"
elif [ "$ARCH" = "x86" ]; then
    KERNEL_URL="https://dl-cdn.alpinelinux.org/alpine/v${ALPINE_VERSION}/main/${ARCH}/${KERNEL_PKG}-6.6.10-r0.apk"
else
    echo "[!] Unknown arch: $ARCH (use x86 or x86_64)"
    exit 1
fi

echo "[*] Downloading kernel from:"
echo "    $KERNEL_URL"

cd "$SCRIPT_DIR"

# Download
if command -v wget &>/dev/null; then
    wget -q --show-progress "$KERNEL_URL" -O kernel.apk
elif command -v curl &>/dev/null; then
    curl -L "$KERNEL_URL" -o kernel.apk
else
    echo "[!] Install wget or curl"
    exit 1
fi

if [[ ! -s kernel.apk ]]; then
    echo "[!] Download failed"
    exit 1
fi

echo "[+] Downloaded: $(du -h kernel.apk | cut -f1)"

# Extract APK (it's just a tar.gz)
echo "[*] Extracting kernel..."
mkdir -p kernel_tmp

if tar -xzf kernel.apk -C kernel_tmp 2>/dev/null; then
    echo "[+] Extracted with tar -z"
elif tar -xf kernel.apk -C kernel_tmp 2>/dev/null; then
    echo "[+] Extracted with tar"
else
    echo "[!] Extraction failed"
    rm -f kernel.apk
    exit 1
fi

# Find vmlinuz
VMLINUZ=$(find kernel_tmp -name "vmlinuz*" -type f 2>/dev/null | head -1)
INITRD=$(find kernel_tmp -name "initrd*" -type f 2>/dev/null | head -1)

if [[ -z "$VMLINUZ" ]]; then
    echo "[!] vmlinuz not found!"
    echo "[*] Available files:"
    find kernel_tmp -type f | head -20
    rm -rf kernel.apk kernel_tmp
    exit 1
fi

cp "$VMLINUZ" "${SCRIPT_DIR}/vmlinuz"
echo "[+] vmlinuz → build/vmlinuz ($(ls -lh "${SCRIPT_DIR}/vmlinuz" | awk '{print $5}'))"

if [[ -n "$INITRD" ]]; then
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
mount -t tmpfs tmpfs /tmp

echo "LimboOS: mounting root..."
mount /dev/sda1 /root 2>/dev/null

if [ -d /root/usr ]; then
    echo "LimboOS: switching to root filesystem..."
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
    echo "[+] Minimal initrd created"
fi

rm -f kernel.apk
rm -rf kernel_tmp

echo ""
echo "[+] Kernel ready:"
echo "    build/vmlinuz"
echo "    build/initrd.img"
echo ""
echo "[*] Now run: bash build_limboos.sh"
echo ""
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
