# ============================================================
# SentinelAudit - Read-Only Windows Security Scanner
# Week 2 deliverable
#
# WHAT IT DOES (read-only, changes nothing):
#   1. Checks BitLocker (disk encryption) status
#   2. Checks Windows Firewall status
#   3. Checks OS version and recent security patches
#   4. Saves everything to scan_result.json
#
# HOW TO RUN (easiest way):
#   1. Save this file as  sentinel_scanner.py  (e.g., in Documents)
#   2. Open PowerShell (Start menu -> type "PowerShell" -> Enter)
#   3. Type:  cd Documents        (or wherever you saved it)
#   4. Type:  python sentinel_scanner.py
#
# NOTE: BitLocker status needs Administrator rights to read.
#   If you run without admin, the scanner still works and will
#   mark BitLocker as "requires_admin". To get the real value:
#   Start menu -> type "PowerShell" -> right-click ->
#   "Run as administrator" -> repeat steps 3 and 4.
# ============================================================

import json
import platform
import subprocess
from datetime import datetime, timezone


def run_command(command):
    """Run a Windows command and return its text output (read-only)."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            timeout=60,
        )
        return result.stdout + result.stderr
    except Exception as error:
        return f"ERROR: {error}"


def check_bitlocker():
    """Check BitLocker status of drive C: (needs admin to read)."""
    output = run_command("manage-bde -status C:")

    if "Protection On" in output:
        return {"status": "on", "detail": "BitLocker protection is ON for drive C:"}
    if "Protection Off" in output:
        return {"status": "off", "detail": "BitLocker protection is OFF for drive C:"}
    if "Access is denied" in output or "ERROR" in output.upper():
        return {
            "status": "requires_admin",
            "detail": "Could not read BitLocker status. Re-run PowerShell as Administrator.",
        }
    return {"status": "unknown", "detail": output.strip()[:200]}


def check_firewall():
    """Check Windows Firewall for all profiles (no admin needed)."""
    output = run_command("netsh advfirewall show allprofiles state")

    profiles_on = output.count("ON")
    profiles_off = output.count("OFF")

    if profiles_off == 0 and profiles_on > 0:
        return {"status": "on", "detail": f"All firewall profiles are ON ({profiles_on} profiles)."}
    if profiles_off > 0:
        return {"status": "partially_off", "detail": f"{profiles_off} firewall profile(s) are OFF."}
    return {"status": "unknown", "detail": output.strip()[:200]}


def check_os_patches():
    """Read OS version and the most recent installed updates (no admin needed)."""
    os_version = f"{platform.system()} {platform.release()} (build {platform.version()})"

    # Get the 5 most recent installed hotfixes via PowerShell
    ps_command = (
        'powershell -Command "Get-HotFix | Sort-Object InstalledOn -Descending '
        '| Select-Object -First 5 HotFixID, InstalledOn | Format-Table -HideTableHeaders"'
    )
    output = run_command(ps_command)

    patches = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("KB"):
            patches.append(line)

    return {
        "os_version": os_version,
        "recent_patches": patches if patches else ["No patch list available"],
        "detail": f"Found {len(patches)} recent update(s).",
    }


def main():
    print("=" * 60)
    print("SentinelAudit - Read-Only Security Scanner")
    print("This scan READS settings only. Nothing is changed.")
    print("=" * 60)

    print("\n[1/3] Checking BitLocker (disk encryption)...")
    bitlocker = check_bitlocker()
    print("      ->", bitlocker["detail"])

    print("\n[2/3] Checking Windows Firewall...")
    firewall = check_firewall()
    print("      ->", firewall["detail"])

    print("\n[3/3] Checking OS version and patches...")
    patches = check_os_patches()
    print("      ->", patches["os_version"])
    print("      ->", patches["detail"])

    # Build the final result
    scan_result = {
        "tool": "SentinelAudit Scanner",
        "scan_time_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "checks": {
            "disk_encryption": bitlocker,
            "firewall": firewall,
            "os_and_patches": patches,
        },
    }

    # Save to JSON (this file becomes the input for the Week 3 scoring engine)
    with open("scan_result.json", "w") as f:
        json.dump(scan_result, f, indent=2)

    print("\n" + "=" * 60)
    print("Scan complete. Results saved to: scan_result.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
