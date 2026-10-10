from eval.stages import first_failing_stage as f


def test_first_wrong_stage_wins():
    assert f({"error": "boom", "stage": "extraction"}, 2) == "extraction"
    assert f({"visible": 4}, 2) == "cut"
    assert f({"visible": 2, "expect": "amounts", "checks": []}, 2) == "findings"
    assert f({"visible": 2, "expect": "amounts", "checks": ["amounts"]}, 2) == "decision"
