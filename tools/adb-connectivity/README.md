# ADB connectivity checks

Optional host-side diagnostics for `bluejay-kali_nethunter`. The Python runner
uses `adbutils` and calls a Node.js `@devicefarmer/adbkit` helper to verify both
libraries can communicate with the same Android devices.

These scripts perform a harmless shell echo only. They do not flash images,
install apps, reboot devices, or require root or an unlocked bootloader.
They do not verify Pixel 6a compatibility or whether flashing is safe.

## Requirements

- Python 3 with pip (`adbutils` 2.12.0 is pinned in `requirements.txt`).
- Node.js 22.12 or newer and npm.
- Android SDK Platform-Tools with `adb` on PATH.
- An Android device booted into Android, USB debugging enabled, and an
  authorized data connection. Fastboot mode is not supported by these checks.

The scripts can run on Windows or Linux when those dependencies and USB access
are available. Android Studio and Android SDK build tools are not required.
`uiautomator2` is not required or exercised.

## Install dependencies

Run all commands in this README from the repository root.

On Windows, install ADB and Node.js if needed:

```powershell
winget install --id Google.PlatformTools --exact
winget install --id OpenJS.NodeJS.LTS --exact
```

Open a new shell after installation so PATH changes take effect.
On Linux, install Platform-Tools, Python, and a supported Node.js release using
your distribution's instructions. Ensure the current user has USB access to the
device; configure the appropriate Android udev rules if required.

Check prerequisites:

```sh
adb version
python --version
node --version
npm --version
```

On systems where Python 3 is named `python3`, substitute `python3` for `python`.

Recommended: create an isolated Python environment.

```sh
python -m venv tools/adb-connectivity/.venv
```

Activate it in PowerShell:

```powershell
.\tools\adb-connectivity\.venv\Scripts\Activate.ps1
```

Or activate it in a Linux shell:

```sh
. tools/adb-connectivity/.venv/bin/activate
```

With the environment active, install dependencies:

```sh
python -m pip install -r tools/adb-connectivity/requirements.txt
npm --prefix tools/adb-connectivity ci
```

`npm ci` uses the committed lockfile and replaces this tool's `node_modules`
directory. It is not a separate package to install. Dependencies and Python
cache files are ignored by Git.

## Prepare a device

1. Enable Developer options (usually by tapping **Build number** seven times).
2. Enable **USB debugging**.
3. Connect a USB data cable, unlock the device, and accept its debugging prompt.
4. Confirm that `adb devices -l` lists the device with state `device`.

Only authorize trusted computers. Disable USB debugging when no longer needed.

## Run

```sh
python tools/adb-connectivity/test_connectivity.py
```

The runner:

- Starts the local ADB server.
- Connects both libraries to `127.0.0.1:5037`.
- Lists serial numbers and states for all detected devices.
- Checks `echo adb_connection_ok` through each library on every ready device.
- Compares server protocol versions and device serial/state sets.

The helper is resolved relative to the Python file, so the runner can also be
called by absolute path from another working directory. Keep both scripts
together.

### Results

- Exit `0`: At least one device was detected and all checks passed.
- Exit `1`: No devices, an unauthorized/offline device, a library error, failed
  shell access, or differing results.

Inspect the exit code with `$LASTEXITCODE` in PowerShell or `echo $?` in a Linux
shell immediately after running the test.

Both libraries must report shell verification for every device. Server protocol
`41` is distinct from the installed Platform-Tools version.

### Node.js helper only

```sh
adb start-server
node tools/adb-connectivity/check_node_adb.cjs
```

The helper prints JSON for the runner. It can exit `0` with an empty device list
or per-device failures recorded in JSON. Use the Python runner for automated
pass/fail decisions.

### Timeouts and CI

ADB startup allows 20 seconds, Python shell calls allow 10 seconds per device,
and the Node.js helper has a 60-second overall watchdog. The Python runner gives
the Node subprocess 65 seconds.

A CI runner needs the same dependencies and access to an authorized Android
device. A device-free hosted runner fails this hardware test by design. These
checks are not connected to automatic flashing or a CI workflow.

## Troubleshooting

- **Command missing:** Confirm Python, Node.js, and ADB are on PATH; reopen the
  shell after installing tools.
- **Python import error:** Activate the intended environment and rerun the pip
  requirements command with the same Python interpreter used for testing.
- **Node module missing:** Rerun `npm --prefix tools/adb-connectivity ci`.
- **No devices:** Check USB debugging, unlock the device, try another data cable
  or port, and run `adb devices -l`. Windows may need the manufacturer's official
  USB driver; Linux may need USB permissions/udev rules.
- **Unauthorized:** Accept the debugging prompt. Reconnect if necessary.
- **Different results:** Keep devices connected; state may have changed between
  the two library checks. Retry.
- **Offline or timeout:** Restart ADB and retry. This interrupts other ADB
  sessions on the host:

```sh
adb kill-server
adb start-server
python tools/adb-connectivity/test_connectivity.py
```

## Validation scope

The integrated scripts passed Python and Node.js syntax checks. A clean
`npm ci` completed with no reported vulnerabilities. Both libraries connected
to the local ADB server (protocol 41), detected `emulator-5554`, and passed
shell echo checks with matching device states.

This validates emulator connectivity, not physical Pixel 6a hardware or kernel
compatibility.

## Project notes: Rootless shared-storage access

**Status: resolved / closed locally (2026-11-15).**

### Symptoms and diagnosis

Launching Kali PRoot through `adb shell run-as com.termux` produced:

```text
proot warning: can't sanitize binding "/sdcard": Permission denied
```

Termux's read/write storage permissions were already granted, and
`~/storage/shared` and `~/storage/downloads` pointed to the expected Android
shared-storage paths. The failure was specific to the ADB `run-as` context,
which does not provide the same shared-storage access as a normal Termux
app session. Termux's maintainers document this limitation in
[termux-app issue 4052](https://github.com/termux/termux-app/issues/4052).

### Resolution

Launch NetHunter from the Termux app itself rather than using `run-as` for
shared-storage operations. No extra storage permissions, root access, launcher
changes, or SELinux changes were needed.

To verify access, run the following **inside Termux on the phone**, not in
PowerShell or an ADB shell:

```sh
nethunter -r 'python3 -c "import tempfile; f=tempfile.TemporaryFile(dir=\"/sdcard/Download\"); f.write(b\"storage-test\"); f.seek(0); assert f.read()==b\"storage-test\"; f.close(); print(\"PASS: Kali shared-storage read/write works\")"'
```

Confirmed output:

```text
PASS: Kali shared-storage read/write works
Exit code: 0
```

The exit code was captured by the test wrapper. The test created, wrote, read,
and automatically removed a temporary file in `/sdcard/Download`.
It passed on a physical Pixel 6a running Android 17, build `2026111301`,
with Termux 0.118.3 and Kali Rolling 2026.3 ARM64.

This confirms Rootless userspace shared-storage access only, not compatibility
with the project's Android 16 custom kernel or full NetHunter hardware features.
The warning may still occur if the same diagnostic is launched through ADB
`run-as`; that does not establish a failure in the normal app session.

No matching open GitHub issue was identified in the upstream repository during
the check. This local resolution does not close an upstream issue.
