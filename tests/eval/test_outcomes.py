from eval.outcomes import LABELS, score_outcome


def test_ten_labelled_cases():
    assert len(LABELS) == 10


def test_outcome_scoring():
    ok = {"status": "ok", "write": True}
    assert score_outcome("005", "Your return request is registered.", [ok]) == []
    assert score_outcome("005", "Return request done, money is back.", [ok])  # forbidden claim
    assert score_outcome("001", "It was sent.", [ok])  # write not needed
    assert score_outcome("001", "It was sent.", [], escalated=True)
