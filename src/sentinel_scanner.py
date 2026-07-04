import json
import platform
import subprocess
from datetime import datetime, timezone


def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True, timeout=60)
        return result.stdout + result.stderr
    except Exception as error:
        return f"ERROR: {error}"


def check_bitlocker():
    output = run_command("manage-bde -status C:")
    if "Protection On" in output:
        return {"status": "on", "detail": "BitLocker protection is ON for drive C:"}
    if "Protection Off" in output:
        return {"status": "off", "detail": "BitLocker protection is OFF for drive C:"}
    if "Access is denied" in output or "ERROR" in output.upper():
        return {"status": "requires_admin", "detail": "Could not read BitLocker status. Re-run PowerShell as Administrator."}
    return {"status": "unknown", "detail": output.strip()[:200]}


def check_firewall():
    output = run_command("netsh advfirewall show allprofiles state")
    profiles_on = output.count("ON")
    profiles_off = output.count("OFF")
    if profiles_off == 0 and profiles_on > 0:
        return {"status": "on", "detail": f"All firewall profiles are ON ({profiles_on} profiles)."}
    if profiles_off > 0:
        return {"status": "partially_off", "detail": f"{profiles_off} firewall profile(s) are OFF."}
    return {"status": "unknown", "detail": output.strip()[:200]}


def check_os_patches():
    os_version = f"{platform.system()} {platform.release()} (build {platform.version()})"
    ps_command = ('powershell -Command "Get-HotFix | Sort-Object InstalledOn -Descending '
                  '| Select-Object -First 5 HotFixID, InstalledOn | Format-Table -HideTableHeaders"')
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

    with open("scan_result.json", "w") as f:
        json.dump(scan_result, f, indent=2)

    print("\n" + "=" * 60)
    print("Scan complete. Results saved to: scan_result.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
