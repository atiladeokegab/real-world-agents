from eval.__main__ import score


def test_score_exact_match():
    rows = [{"case": "001", "action": "tool_call", "kind": "read"},
            {"case": "027", "action": "escalate", "kind": "none"}]
    m = score(rows)
    assert m["action_match"] == 0.5 and m["clean_escalation_rate"] == 0.5


def test_score_folder_from_run_files(tmp_path):
    import json

    from eval.__main__ import _score_folder, trace_steps

    log = ('== raw file: x ==\nhello\n\n== finding ==\n{"check": "amounts"}\n\n'
           '== proposal ==\n{"action": "escalate", "tool": null}\n\n== final ==\n{"action": "escalate"}\n')
    assert [s["step"] for s in trace_steps(log)] == ["finding", "proposal", "final"]
    (tmp_path / "trace.log").write_text(log)
    (tmp_path / "run.json").write_text(json.dumps({"escalated": True}))
    row = {}
    _score_folder(row, tmp_path)
    assert row["action"] == "escalate" and row["kind"] == "none" and row["checks"] == ["amounts"] and row["escalated"]
