import scoring_engine


def score_patches_original(check):
    patch_list = check.get("recent_patches", [])
    if patch_list:
        return scoring_engine.BASELINE_POINTS["os_and_patches"], "Recent patches found"
    return 0, "No recent patches found"


def test_defect_placeholder_scored_as_pass():
    check = {"recent_patches": ["No patch list available"]}
    points, detail = score_patches_original(check)
    assert points == 0, (
        "DEFECT REPRODUCED: the placeholder value 'No patch list available' "
        "was awarded full marks because the original condition only checked "
        "that the list was non-empty."
    )


def test_fix_placeholder_scored_as_fail():
    check = {"recent_patches": ["No patch list available"]}
    points, detail = scoring_engine.score_patches(check)
    assert points == 0
