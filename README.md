# bluejay-kali_nethunter

Kali NetHunter kernel for the **Google Pixel 6a (bluejay)** running **lineage-23.2-20260509-nightly-bluejay-signed.zip (Android 16)**.

- **Kernel:** `6.1.145-android14-11-maybe-dirty-NetHunter` (GKI 2.0)
- **Base:** LineageOS 23.2 kernel source (Kleaf/Bazel build system)
- **Tested on:** LineageOS 23.2 + Magisk 30.7

---

## Features

| Feature | Status |
|---|---|
| USB HID keyboard (`/dev/hidg0`) | ✅ Working |
| Rucky / NetHunter HID attacks | ✅ Working |
| External WiFi — Atheros AR9271 (`ath9k_htc`) | ✅ Built-in module, ⚠️ Need someone to check |
| External WiFi — Realtek RTL8xxxU (`rtl8xxxu`) | ✅ Built-in module, ⚠️ Need someone to check |
| chroot| ✅ Working |
| Metasploit | ✅ Working |
| All stock LineageOS functionality | ✅ Preserved |
and many more features are working

---

## Requirements

- Google Pixel 6a (`bluejay`)
- LineageOS 23.2 (Android 16) installed
- Unlocked bootloader
- `adb` and `fastboot` on your PC

---

## Files

| File | Description |
|---|---|
| `patched_boot.img` | NetHunter kernel boot image |
| `dtbo.img` | Device tree overlay |
| `vendor_dlkm.img` | Vendor kernel modules (ath9k, rtl8xxxu, etc.) |
| `bluejay-kali_nethunter-hid.zip` | Magisk module — enables `/dev/hidg0` on every boot |

---

## Build limitations

This repository distributes prebuilt kernel assets; it is not a complete kernel
source checkout. The tracked files include the kernel `Image`, DTBO, compiled
modules, and a Magisk module archive. The kernel source tree, complete Kleaf/Bazel
build configuration, and image-packaging workflow are not included.

- There is no kernel build target in this checkout. The Node.js package under
  `tools/adb-connectivity` also has no `build` script; it contains host-side tests.
- Building new kernel or flashable partition images requires the matching kernel
  sources, device configuration, toolchain, vendor/module inputs, and packaging
  instructions for the target ROM. Cloning this repository alone is insufficient.
- `devices.yml` is integration metadata for the external Kali NetHunter build
  scripts, not a standalone build system.
- `sixteen/bluejay-los/Image` is a raw kernel binary, not a replacement for
  `patched_boot.img`. Flashable release assets are available from the
  [upstream releases](https://github.com/RishiRats/bluejay-kali_nethunter/releases).
- The published kernel targets LineageOS 23.2 / Android 16. Android 17 or
  GrapheneOS compatibility is not established by ADB or Rootless userspace tests.

### Available local validation

After following the [ADB tool setup instructions](tools/adb-connectivity/README.md),
run these commands from the repository root:

```sh
npm --prefix tools/adb-connectivity ci
node --check tools/adb-connectivity/check_node_adb.cjs
python -m py_compile tools/adb-connectivity/test_connectivity.py
python tools/adb-connectivity/test_connectivity.py
```

These commands install the locked Node.js dependencies, check script syntax, and
verify ADB connectivity. They do not compile a kernel, generate flashable images,
or flash a device. The connectivity check requires at least one authorized
Android device or emulator.

**Build investigation: resolved / closed locally (2026-11-15).** Dependency
installation and syntax checks passed, and both ADB libraries verified shell
connectivity to a physical Pixel 6a and an emulator. No kernel build was performed
or claimed. This note does not close an upstream GitHub issue or pull request.

## ADB connectivity check (optional)

Before following the installation instructions, you can verify host-to-device ADB
communication with both Python and Node.js using
[`tools/adb-connectivity`](tools/adb-connectivity/README.md).
The checks do not flash images, reboot the device, or require root.

After installing the tool's dependencies as described in its README, run from the
repository root:

```sh
python tools/adb-connectivity/test_connectivity.py
```

A successful result confirms ADB shell connectivity only; it does not validate
the device model, ROM, bootloader, kernel, or readiness for flashing.

## Installation

> **Note:** The Pixel 6a uses dynamic partitions. The NetHunter installer zip **must** be flashed via Magisk (not TWRP). The NetHunter installer handles flashing the kernel automatically — no manual `fastboot flash boot` needed.

## Have Freash install of Lineage

### Step 1 — Flash WiFi kernel modules (optional)

`vendor_dlkm` is a logical partition and can only be written from fastbootd, not from within Android. Boot into fastboot mode (hold **Power + Volume Down**), then:

```bash
adb reboot fastboot
```

When the device shows the fastbootd menu:

```bash
fastboot flash vendor_dlkm vendor_dlkm.img
fastboot reboot bootloader
fastboot flash boot patched_boot.img 
fastboot flash dtbo dtbo.img
fastboot reboot
```

### Step 2 — Install Magisk

1. Download the latest **Magisk APK** from [github.com/topjohnwu/Magisk/releases](https://github.com/topjohnwu/Magisk/releases)
2. Open the **Magisk** app → tap **Install** → **Direct Install (Recommended)**
3. Tap **Reboot**

### Step 3 — Flash the HID Patch via Magisk

1. Copy `magisk-module/nethunter-hid-bluejay-fix.zip` to your device
2. Open **Magisk** → **Modules** → **Install from storage**
3. Select `bluejay-kali_nethunter-hid.zip`
4. Tap **Reboot**

### Step 4 — Install the NetHunter Suite

1. Copy `nethunter-20260514_044708-generic-arm64-no_kernel-kalifs_nano.zip` to your device from [Releases](../../releases) page
2. Open **Magisk** → **Modules** → **Install from storage**
3. Select `nethunter-20260514_044708-generic-arm64-no_kernel-kalifs_nano.zip`
4. Tap **Reboot**

---
Happy Hacking


## Authors

- **RishiRats** — [LinkedIn](https://www.linkedin.com/in/rishi-raturi/)
- **Claude** (Anthropic) — kernel build system fixes, HID gadget research & SIGSTOP/SIGCONT solution

## Credits

- [Kali NetHunter](https://www.kali.org/docs/nethunter/) project
- [LineageOS](https://lineageos.org/) kernel source
- [Magisk](https://github.com/topjohnwu/Magisk) by topjohnwu
