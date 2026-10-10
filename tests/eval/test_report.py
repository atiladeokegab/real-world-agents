from eval.report import write_report

ROW = {"case": "001", "ok": True, "action": "tool_call", "secs": 2.0, "stage": None}
M = {"action_match": 0.5, "kind_match": 0.5, "tool_match": None, "clean_escalation_rate": 0.0}


def test_report_from_fake_results(tmp_path):
    rows = [ROW, {**ROW, "case": "002", "ok": False, "stage": "findings", "secs": 4.0}]
    jr = [{"case": "013", "action": "escalate"}]
    write_report(tmp_path / "r.md", rows, M, det=0.8, jp=1.0, jr=jr, judged=[True], sha="abc1234", model="m-1")
    t = (tmp_path / "r.md").read_text()
    assert "`abc1234`" in t and "Mean seconds per case | 3.0" in t
    assert "- findings: 1" in t and "Tool match | not run" in t
    assert "ANSWERS/001/ANSWER.md" in t and "case 013 (judgement case)" in t and "case 002" in t
