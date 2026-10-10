from eval.__main__ import score


def test_score_exact_match():
    rows = [{"case": "001", "action": "tool_call", "kind": "read"},
            {"case": "027", "action": "escalate", "kind": "none"}]
    m = score(rows)
    assert m["action_match"] == 0.5 and m["clean_escalation_rate"] == 0.5
