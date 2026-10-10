from eval.outcomes import LABELS, score_outcome


def test_ten_labelled_cases():
    assert len(LABELS) == 10


def test_outcome_scoring():
    ok = {"status": "ok", "write": True}
    assert score_outcome("005", "Your return request is registered.", [ok]) == []
    assert score_outcome("005", "Return request done, money is back.", [ok])  # forbidden claim
    assert score_outcome("001", "It was sent.", [ok])  # write not needed
    assert score_outcome("001", "It was sent.", [], escalated=True)


def test_required_statements_avoid_design_banned_words():
    banned = ("paid", "received", "credited", "refunded", "resolved", "downloaded")  # docs/design.md Copy
    assert not [(c, r) for c, lab in LABELS.items() for r in lab["required"] if any(b in r for b in banned)]


def test_negated_forbidden_words_are_not_claims():
    ok = "It is shown as sent by H&V. We can't see whether the recipient's bank has received it, and if it hasn't arrived, tell us."
    assert score_outcome("001", ok, []) == []
    assert score_outcome("001", "It is sent and the bank received it.", [])  # a plain claim still fails
