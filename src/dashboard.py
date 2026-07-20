import json
from datetime import datetime, timezone

import streamlit as st

st.set_page_config(page_title="SentinelAudit Dashboard", page_icon="🛡️", layout="wide")


def load_json(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def status_color(status):
    if status == "Compliant":
        return "green"
    if status == "Needs Attention":
        return "orange"
    return "red"


st.title("🛡️ SentinelAudit — Compliance Dashboard")
st.caption("Automated Security & Compliance Framework for Remote Windows Workstations")

score_data = load_json("score_result.json")
scan_data = load_json("scan_result.json")

if score_data is None:
    st.error("score_result.json not found. Run sentinel_scanner.py and scoring_engine.py first, then refresh this page.")
    st.stop()

status = score_data["status"]
total = score_data["total_score"]
hostname = score_data.get("hostname", "unknown")
scored_time = score_data.get("scored_time_utc", "")

col1, col2, col3 = st.columns(3)
col1.metric("Workstation", hostname)
col2.metric("Compliance Score", f"{total}/100")
col3.metric("Status", status)

st.progress(total / 100)

color = status_color(status)
st.markdown(f"### Overall status: :{color}[{status}]")

st.divider()
st.subheader("Check Breakdown")

breakdown = score_data["breakdown"]
labels = {
    "disk_encryption": "Disk Encryption (BitLocker)",
    "firewall": "Windows Firewall",
    "os_and_patches": "OS Patch Level",
}

for key, info in breakdown.items():
    name = labels.get(key, key)
    points = info["points"]
    max_points = info["max"]
    detail = info["detail"]
    passed = points == max_points

    c1, c2, c3 = st.columns([3, 1, 4])
    c1.write(f"**{name}**")
    c2.write(f"{points}/{max_points}")
    if passed:
        c3.success(detail)
    else:
        c3.error(detail)

st.divider()

if scan_data is not None:
    st.subheader("Latest Scan Details")
    scan_time = scan_data.get("scan_time_utc", "unknown")
    st.write(f"Scan time (UTC): {scan_time}")
    patches = scan_data["checks"]["os_and_patches"].get("recent_patches", [])
    if patches:
        st.write("Recent updates installed:")
        for patch in patches:
            st.write(f"- {patch}")

st.caption(f"Scored at (UTC): {scored_time}")
st.caption("All timestamps standardized to UTC for cross-timezone consistency.")
