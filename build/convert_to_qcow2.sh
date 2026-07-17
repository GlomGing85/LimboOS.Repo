#!/bin/bash
# ==============================================================================
# Convert raw disk image to qcow2 (smaller, persistent storage for Limbo)
# Usage: bash convert_to_qcow2.sh <input.img> [output.qcow2]
# ==============================================================================

set -euo pipefail

INPUT="${1:?Usage: convert_to_qcow2.sh <input.raw> [output.qcow2]}"
OUTPUT="${2:-${INPUT%.img}.qcow2}"

[[ -f "$INPUT" ]] || { echo "[!] File not found: $INPUT"; exit 1; }
command -v qemu-img &>/dev/null || { echo "[!] Install: apt install qemu-utils"; exit 1; }

echo "[*] Converting: $INPUT → $OUTPUT"
qemu-img convert -f raw -O qcow2 "$INPUT" "$OUTPUT"

echo "[+] Done!"
echo "    Input:  $(du -h "$INPUT" | cut -f1)"
echo "    Output: $(du -h "$OUTPUT" | cut -f1)"
echo ""
echo "    Import $OUTPUT into Limbo as Hard Disk."
