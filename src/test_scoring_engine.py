from scoring_engine import (
    score_disk_encryption,
    score_firewall,
    score_patches,
    get_status_label,
)


def test_disk_encryption_on():
    points, detail = score_disk_encryption({"status": "on"})
    assert points == 40
    assert "ON" in detail


def test_disk_encryption_off():
    points, detail = score_disk_encryption({"status": "off"})
    assert points == 0
    assert "OFF" in detail


def test_disk_encryption_requires_admin():
    points, detail = score_disk_encryption({"status": "requires_admin"})
    assert points == 0
    assert "Administrator" in detail


def test_firewall_on():
    points, detail = score_firewall({"status": "on"})
    assert points == 40


def test_firewall_partially_off():
    points, detail = score_firewall({"status": "partially_off"})
    assert points == 0


def test_patches_found():
    check = {"recent_patches": ["KB5094126 6/10/2026"]}
    points, detail = score_patches(check)
    assert points == 20


def test_patches_not_found():
    check = {"recent_patches": ["No patch list available"]}
    points, detail = score_patches(check)
    assert points == 0


def test_patches_empty_list():
    check = {"recent_patches": []}
    points, detail = score_patches(check)
    assert points == 0


def test_status_compliant():
    assert get_status_label(100) == "Compliant"
    assert get_status_label(90) == "Compliant"


def test_status_needs_attention():
    assert get_status_label(60) == "Needs Attention"
    assert get_status_label(89) == "Needs Attention"


def test_status_at_risk():
    assert get_status_label(59) == "At Risk"
    assert get_status_label(0) == "At Risk"


def test_full_score_calculation():
    total = 0
    p, _ = score_disk_encryption({"status": "off"})
    total += p
    p, _ = score_firewall({"status": "on"})
    total += p
    p, _ = score_patches({"recent_patches": ["KB5094126"]})
    total += p
    assert total == 60
    assert get_status_label(total) == "Needs Attention"
