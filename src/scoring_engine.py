import json
from datetime import datetime, timezone

BASELINE_POINTS = {
    "disk_encryption": 40,
    "firewall": 40,
    "os_and_patches": 20,
}


def load_scan_result(filename="scan_result.json"):
    with open(filename, "r") as f:
        return json.load(f)


def score_disk_encryption(check):
    if check["status"] == "on":
        return BASELINE_POINTS["disk_encryption"], "BitLocker is ON"
    if check["status"] == "requires_admin":
        return 0, "Could not verify BitLocker (run scanner as Administrator)"
    return 0, "BitLocker is OFF"


def score_firewall(check):
    if check["status"] == "on":
        return BASELINE_POINTS["firewall"], "All firewall profiles are ON"
    return 0, "One or more firewall profiles are OFF"


def score_patches(check):
    patch_list = check.get("recent_patches", [])
    if patch_list and patch_list[0] != "No patch list available":
        return BASELINE_POINTS["os_and_patches"], "Recent patches found"
    return 0, "No recent patches found"


def get_status_label(score):
    if score >= 90:
        return "Compliant"
    if score >= 60:
        return "Needs Attention"
    return "At Risk"


def main():
    print("=" * 60)
    print("SentinelAudit - Rule-Based Compliance Scoring Engine")
    print("=" * 60)

    try:
        scan = load_scan_result()
    except FileNotFoundError:
        print("\nERROR: scan_result.json not found in this folder.")
        print("Run sentinel_scanner.py first, then run this again.")
        return

    checks = scan["checks"]

    total_score = 0
    breakdown = {}

    points, detail = score_disk_encryption(checks["disk_encryption"])
    total_score += points
    breakdown["disk_encryption"] = {"points": points, "max": BASELINE_POINTS["disk_encryption"], "detail": detail}
    print(f"\nDisk Encryption: {points}/{BASELINE_POINTS['disk_encryption']}  -> {detail}")

    points, detail = score_firewall(checks["firewall"])
    total_score += points
    breakdown["firewall"] = {"points": points, "max": BASELINE_POINTS["firewall"], "detail": detail}
    print(f"Firewall:        {points}/{BASELINE_POINTS['firewall']}  -> {detail}")

    points, detail = score_patches(checks["os_and_patches"])
    total_score += points
    breakdown["os_and_patches"] = {"points": points, "max": BASELINE_POINTS["os_and_patches"], "detail": detail}
    print(f"OS Patches:      {points}/{BASELINE_POINTS['os_and_patches']}  -> {detail}")

    status = get_status_label(total_score)

    print("\n" + "=" * 60)
    print(f"TOTAL SCORE: {total_score}/100  ->  {status}")
    print("=" * 60)

    result = {
        "tool": "SentinelAudit Scoring Engine",
        "scored_time_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": scan.get("hostname", "unknown"),
        "total_score": total_score,
        "status": status,
        "breakdown": breakdown,
    }

    with open("score_result.json", "w") as f:
        json.dump(result, f, indent=2)

    print("\nSaved to: score_result.json")


if __name__ == "__main__":
    main()
