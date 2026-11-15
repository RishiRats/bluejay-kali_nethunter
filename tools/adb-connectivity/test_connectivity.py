"""Compare Python/Node ADB detection and test shell access without device writes.

Run from the repository root: python tools/adb-connectivity/test_connectivity.py
Exit codes: 0 = all devices pass; 1 = failure or no devices.
Requires adb on PATH, Python adbutils, and local @devicefarmer/adbkit.
"""

import json
from pathlib import Path
import subprocess
import sys


def python_check():
    from adbutils import AdbClient

    client = AdbClient(host="127.0.0.1", port=5037, socket_timeout=10)
    version = client.server_version()
    results = []
    for info in client.list():
        result = {"serial": info.serial, "state": info.state, "ok": False}
        if info.state == "device":
            try:
                response = client.device(serial=info.serial).shell(
                    "echo adb_connection_ok", timeout=10
                ).strip()
                if response != "adb_connection_ok":
                    raise RuntimeError(f"Unexpected shell response: {response!r}")
                result["ok"] = True
            except Exception as exc:
                result["error"] = str(exc)
        else:
            result["error"] = "Device is not authorized or ready."
        results.append(result)
    return {"serverVersion": version, "devices": results}


def node_check():
    helper = Path(__file__).resolve().with_name("check_node_adb.cjs")
    completed = subprocess.run(
        ["node", str(helper)],
        capture_output=True,
        text=True,
        timeout=65,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "Node.js helper failed.")
    return json.loads(completed.stdout)


def main():
    try:
        started = subprocess.run(
            ["adb", "start-server"], capture_output=True, text=True, timeout=20
        )
        if started.returncode:
            raise RuntimeError(started.stderr.strip() or "ADB server failed to start.")
    except Exception as exc:
        print(f"FAIL: Cannot start ADB: {exc}", file=sys.stderr)
        return 1

    reports = {}
    failed = False
    for name, check in (("Python adbutils", python_check), ("Node.js adbkit", node_check)):
        print(f"\n{name}:", flush=True)
        try:
            report = check()
            reports[name] = report
            print(f"  PASS: ADB server connected (protocol {report['serverVersion']}).")
            if not report["devices"]:
                print("  FAIL: No Android devices detected.")
                failed = True
            for device in report["devices"]:
                status = "PASS" if device["ok"] else "FAIL"
                print(f"  {status}: {device['serial']} | {device['state']}")
                if device["ok"]:
                    print("    Shell echo verified.")
                else:
                    failed = True
                    print(f"    {device.get('error', 'Unknown error')}")
                    if device["state"] == "unauthorized":
                        print("    Unlock the device and accept USB debugging authorization.")
        except Exception as exc:
            print(f"  FAIL: {exc}")
            failed = True

    if len(reports) == 2:
        python_report, node_report = reports.values()
        python_devices = {
            (item["serial"], item["state"]) for item in python_report["devices"]
        }
        node_devices = {
            (item["serial"], item["state"]) for item in node_report["devices"]
        }
        if (
            python_devices != node_devices
            or python_report["serverVersion"] != node_report["serverVersion"]
        ):
            print("\nFAIL: Libraries reported different servers or device states.")
            print(f"  Python: {sorted(python_devices)}")
            print(f"  Node.js: {sorted(node_devices)}")
            print("  Keep the device connected and retry.")
            failed = True
        elif python_devices:
            print("\nPASS: Both libraries detected identical devices and states.")

    if failed:
        print("\nFAILED: Connect an authorized device and resolve the errors above.")
    else:
        print("\nPASSED: Every device passed shell checks in Python and Node.js.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
