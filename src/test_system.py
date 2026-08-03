import json
import os
import subprocess
import sys

import pytest

import scoring_engine

SCAN_FILE = "scan_result.json"
SCORE_FILE = "score_result.json"


def load(filename):
    with open(filename, "r") as f:
        return json.load(f)


class TestIntegration:

    def test_scanner_produces_scan_file(self):
        subprocess.run([sys.executable, "sentinel_scanner.py"], capture_output=True, text=True)
        assert os.path.exists(SCAN_FILE)

    def test_scan_file_has_required_structure(self):
        scan = load(SCAN_FILE)
        assert "checks" in scan
        assert "scan_time_utc" in scan
        assert "hostname" in scan
        for key in ["disk_encryption", "firewall", "os_and_patches"]:
            assert key in scan["checks"]

    def test_scoring_engine_consumes_scanner_output(self):
        result = subprocess.run([sys.executable, "scoring_engine.py"], capture_output=True, text=True)
        assert result.returncode == 0
        assert os.path.exists(SCORE_FILE)

    def test_score_file_matches_scan_hostname(self):
        scan = load(SCAN_FILE)
        score = load(SCORE_FILE)
        assert score["hostname"] == scan["hostname"]

    def test_dashboard_can_read_both_artifacts(self):
        scan = load(SCAN_FILE)
        score = load(SCORE_FILE)
        assert isinstance(score["total_score"], int)
        assert "breakdown" in score
        assert len(score["breakdown"]) == len(scan["checks"])


class TestSystem:

    def test_total_score_within_valid_range(self):
        score = load(SCORE_FILE)
        assert 0 <= score["total_score"] <= 100

    def test_status_is_recognised_label(self):
        score = load(SCORE_FILE)
        assert score["status"] in ["Compliant", "Needs Attention", "At Risk"]

    def test_breakdown_points_sum_to_total(self):
        score = load(SCORE_FILE)
        total = sum(item["points"] for item in score["breakdown"].values())
        assert total == score["total_score"]

    def test_status_matches_score_band(self):
        score = load(SCORE_FILE)
        expected = scoring_engine.get_status_label(score["total_score"])
        assert score["status"] == expected

    def test_timestamps_are_utc(self):
        scan = load(SCAN_FILE)
        score = load(SCORE_FILE)
        assert "+00:00" in scan["scan_time_utc"]
        assert "+00:00" in score["scored_time_utc"]

    def test_scanner_is_read_only(self):
        before = load(SCAN_FILE)["checks"]["firewall"]["status"]
        subprocess.run([sys.executable, "sentinel_scanner.py"], capture_output=True, text=True)
        after = load(SCAN_FILE)["checks"]["firewall"]["status"]
        assert before == after


class TestAcceptance:

    def test_fr1_scans_three_baseline_controls(self):
        scan = load(SCAN_FILE)
        assert len(scan["checks"]) == 3

    def test_fr3_produces_score_out_of_100(self):
        score = load(SCORE_FILE)
        maximum = sum(item["max"] for item in score["breakdown"].values())
        assert maximum == 100

    def test_fr4_flags_device_below_threshold(self):
        assert scoring_engine.get_status_label(59) == "At Risk"
        assert scoring_engine.get_status_label(60) != "At Risk"

    def test_fr6_every_check_has_readable_detail(self):
        score = load(SCORE_FILE)
        for item in score["breakdown"].values():
            assert isinstance(item["detail"], str)
            assert len(item["detail"]) > 0

    def test_nfr_reliability_repeated_scoring_is_consistent(self):
        first = load(SCORE_FILE)["total_score"]
        subprocess.run([sys.executable, "scoring_engine.py"], capture_output=True, text=True)
        second = load(SCORE_FILE)["total_score"]
        assert first == second


class TestNegative:

    def test_scoring_handles_missing_scan_file(self, tmp_path):
        result = subprocess.run(
            [sys.executable, os.path.join(os.getcwd(), "scoring_engine.py")],
            capture_output=True, text=True, cwd=tmp_path,
        )
        assert result.returncode == 0
        assert "not found" in result.stdout

    def test_unknown_status_scores_zero(self):
        points, _ = scoring_engine.score_disk_encryption({"status": "unknown"})
        assert points == 0

    def test_partially_off_firewall_scores_zero(self):
        points, _ = scoring_engine.score_firewall({"status": "partially_off"})
        assert points == 0
