import json
import statistics
import subprocess
import sys
import time
import tracemalloc

import scoring_engine

RUNS = 3


def measure_scanner():
    durations = []
    for i in range(RUNS):
        start = time.perf_counter()
        subprocess.run([sys.executable, "sentinel_scanner.py"], capture_output=True, text=True)
        elapsed = time.perf_counter() - start
        durations.append(elapsed)
        print(f"   run {i + 1}: {elapsed:.3f} s")
    return durations


def measure_scoring():
    durations = []
    with open("scan_result.json", "r") as f:
        scan = json.load(f)
    checks = scan["checks"]

    for i in range(RUNS):
        start = time.perf_counter()
        total = 0
        points, _ = scoring_engine.score_disk_encryption(checks["disk_encryption"])
        total += points
        points, _ = scoring_engine.score_firewall(checks["firewall"])
        total += points
        points, _ = scoring_engine.score_patches(checks["os_and_patches"])
        total += points
        scoring_engine.get_status_label(total)
        elapsed = (time.perf_counter() - start) * 1000
        durations.append(elapsed)
        print(f"   run {i + 1}: {elapsed:.4f} ms")
    return durations


def measure_memory():
    with open("scan_result.json", "r") as f:
        scan = json.load(f)
    checks = scan["checks"]

    tracemalloc.start()
    total = 0
    points, _ = scoring_engine.score_disk_encryption(checks["disk_encryption"])
    total += points
    points, _ = scoring_engine.score_firewall(checks["firewall"])
    total += points
    points, _ = scoring_engine.score_patches(checks["os_and_patches"])
    total += points
    scoring_engine.get_status_label(total)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024


def main():
    print("=" * 60)
    print("SentinelAudit - Performance Benchmark")
    print("=" * 60)

    print(f"\n[1/3] Scanner latency ({RUNS} runs)...")
    scanner_times = measure_scanner()
    scanner_avg = statistics.mean(scanner_times)

    print(f"\n[2/3] Scoring engine latency ({RUNS} runs)...")
    scoring_times = measure_scoring()
    scoring_avg = statistics.mean(scoring_times)

    print("\n[3/3] Scoring engine peak memory...")
    memory_kb = measure_memory()
    print(f"   peak: {memory_kb:.2f} KB")

    throughput = 60 / scanner_avg

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Scanner average latency:        {scanner_avg:.3f} s")
    print(f"Scoring engine average latency: {scoring_avg:.4f} ms")
    print(f"Scoring engine peak memory:     {memory_kb:.2f} KB")
    print(f"Estimated throughput:           {throughput:.1f} scans/minute")
    print("=" * 60)

    results = {
        "runs_per_test": RUNS,
        "scanner_latency_seconds": round(scanner_avg, 3),
        "scanner_latency_all_runs": [round(x, 3) for x in scanner_times],
        "scoring_latency_ms": round(scoring_avg, 4),
        "scoring_latency_all_runs": [round(x, 4) for x in scoring_times],
        "scoring_peak_memory_kb": round(memory_kb, 2),
        "throughput_scans_per_minute": round(throughput, 1),
    }

    with open("benchmark_result.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nSaved to: benchmark_result.json")


if __name__ == "__main__":
    main()
