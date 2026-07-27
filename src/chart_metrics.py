import json

import matplotlib.pyplot as plt

with open("benchmark_result.json", "r") as f:
    data = json.load(f)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

runs = data["scanner_latency_all_runs"]
labels = [f"Run {i + 1}" for i in range(len(runs))]
bars = ax1.bar(labels, runs, color="#2E75B6", edgecolor="black", linewidth=0.7)
ax1.axhline(data["scanner_latency_seconds"], color="#C00000", linestyle="--", linewidth=1.5,
            label=f"Average: {data['scanner_latency_seconds']} s")
ax1.set_ylabel("Latency (seconds)")
ax1.set_title("Scanner Latency per Run", fontweight="bold")
ax1.legend()
ax1.grid(axis="y", linestyle="--", alpha=0.4)
for bar, value in zip(bars, runs):
    ax1.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.2f}",
             ha="center", va="bottom", fontsize=9)

metrics = ["Scanner\nlatency (s)", "Scoring\nlatency (ms)", "Peak memory\n(KB)"]
values = [data["scanner_latency_seconds"], data["scoring_latency_ms"], data["scoring_peak_memory_kb"]]
colors = ["#2E75B6", "#548235", "#7030A0"]
bars2 = ax2.bar(metrics, values, color=colors, edgecolor="black", linewidth=0.7)
ax2.set_yscale("log")
ax2.set_ylabel("Value (log scale)")
ax2.set_title("Performance Metrics Summary", fontweight="bold")
ax2.grid(axis="y", linestyle="--", alpha=0.4)
for bar, value in zip(bars2, values):
    ax2.text(bar.get_x() + bar.get_width() / 2, value, f"{value}",
             ha="center", va="bottom", fontsize=9)

plt.suptitle("SentinelAudit - System Performance Evaluation", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("performance_chart.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.show()
print("Saved: performance_chart.png")
