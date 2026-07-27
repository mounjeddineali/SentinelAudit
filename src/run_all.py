import json
import subprocess
import sys


def run_module(name, script):
    print("=" * 60)
    print(f"STAGE: {name}")
    print("=" * 60)
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        return False
    return True


def show_pipeline_data():
    print("=" * 60)
    print("INTER-MODULE DATA FLOW")
    print("=" * 60)

    with open("scan_result.json", "r") as f:
        scan = json.load(f)
    with open("score_result.json", "r") as f:
        score = json.load(f)

    print("Scanner output passed to Scoring Engine:")
    for key, value in scan["checks"].items():
        status = value.get("status", "n/a")
        print(f"   {key}: {status}")

    print("\nScoring Engine output passed to Dashboard:")
    print(f"   hostname: {score['hostname']}")
    print(f"   total_score: {score['total_score']}")
    print(f"   status: {score['status']}")


def main():
    print("SentinelAudit - Full System Integration Run")
    print()

    if not run_module("1 of 2 - Read-Only Scanner", "sentinel_scanner.py"):
        print("Scanner failed. Stopping.")
        return

    if not run_module("2 of 2 - Rule-Based Scoring Engine", "scoring_engine.py"):
        print("Scoring engine failed. Stopping.")
        return

    show_pipeline_data()

    print()
    print("=" * 60)
    print("INTEGRATION COMPLETE")
    print("=" * 60)
    print("Both modules ran successfully and exchanged data.")
    print("Launch the dashboard with:  py -m streamlit run dashboard.py")


if __name__ == "__main__":
    main()
