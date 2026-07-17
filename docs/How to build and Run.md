# How to boot LimboOS and run it 

## The easiest way: GitHub Codespaces ⭐ 

No need to install anything — Linux right in your browser! 

### Steps:
1. **Open the repo:** https://github.com/GlomGing85/LimboOS.Repo

2. **Click `<> Code`** → `Codespaces` → `Create codespace on main` 3. **In the Codespaces terminal:** 
   ```bash
# 1. Dependencies
sudo apt-get update
sudo apt-get install -y debootstrap grub-pc-bin xorriso mtools qemu-utils python3-tk

# 2. Download kernel
bash build/download_kernel.sh x86_64

# 3. build
sudo bash build/build_limboos.sh --arch x86_64 --size 300

# 4. done! files in build/output/
ls -lh build/output/
# → limboos-1.0.0-x86_64.img
# → limboos-1.0.0-x86_64.qcow2  ← use this!
   ```
4. **Download the image:** right click on `build/output/limboos-1.0.0-x86.qcow2` → Download
5. **Open in Limbo** as Hard Disk

---

## via Termux (root-distro Ubuntu)

If you want to build right on your phone.

### Step 1: Install dependencies in Termux

```bash
pkg update
pkg install proot-distro wget curl git
```

### Step 2: Install Ubuntu

```bash
proot-distro install ubuntu
proot-distro login ubuntu
```

### Step 3: In Ubuntu — install the required packages

```bash
apt update
apt install -y python3 python3-tk qemu-utils e2fsprogs \
    sfdisk dosfstools cpio gzip wget curl
```

### Step 4: Clone the repo and build

```bash
git clone https://github.com/GlomGing85/LimboOS.Repo.git
cd LimboOS.Repo

bash build/build_on_termux.sh
```

### Step 5: Load the kernel (required for booting!)

```bash
bash build/download_kernel.sh x86_64
```

This will download `vmlinuz` + `initrd.img` to the `build/` folder.

### Step 6: Add the kernel to the image

```bash
# You need to mount the image and copy the kernel to /boot/
# The easiest way is to do this inside proot:

sudo mount -o loop build/output/limboos-1.0.0-x86.img /mnt
sudo cp build/vmlinuz /mnt/boot/
sudo cp build/initrd.img /mnt/boot/
sudo umount /mnt
```

### Step 7: Copy to Android

```bash
cp build/output/limboos-1.0.0-x86.qcow2 /sdcard/Download/
```

Now the `.qcow2` file is in the Download folder!

---

## Setting up a VM in Limbo PC Emulator

| Parameter | Value |
|----------|----------|
| **Architecture** | x86_64 |
| **CPU Model** | qemu64 |
| **RAM** | 512 MB |
| **Hard Disk** | `limboos-1.0.0-x86.qcow2` |
| **Boot from** | Hard Disk |
| **Display** | SDL |
| **Sound** | Disabled |

Press **Play** — LimboOS will load

---

## Data storage (qcow2)

Image `.qcow2` = **persistent storage**:
- ✅ Applications installed via `lpkg` are saved
- ✅ Files in `/home/user/` are stored
- ✅ Settings are saved
- ✅ Everything stays between restarts

Just mount `.qcow2` as a **Hard Disk** (not a CD-ROM!) in Limbo.


## Troubleshooting

### "No space left on device"
By reducing the image size:
```bash
# in build_on_termux.sh change IMAGE_SIZE_MB=300 to IMAGE_SIZE_MB=200
```

### Limbo won't load (black screen)
- Check that `vmlinuz` and `initrd.img` are in the `/boot/` image
- Increase RAM to 512 MB 
- Try x86 architecture instead of x86_64

### GUI won't load
```bash
# in the LimboOS terminal (if available):
export DISPLAY=:0
python3 /usr/lib/limboos/limboos_desktop_v2.py
```

### "debootstrap not found" (in Codespaces)
```bash
sudo apt install debootstrap
```
