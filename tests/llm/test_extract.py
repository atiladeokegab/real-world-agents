from agent.llm.contracts import CaseObject
from agent.llm.extract import extract

from .cases import FINDING_DUP, case_006

ANSWER = {
    "requester": {"name": "Mira", "evidence_events": ["event-001"]},
    "claims": [
        {"subject": "transfer to Northgrid Energy", "predicate": "appears", "value": "twice, £84.20",
         "source_actor": "Mira", "channel": "Secure portal", "event": "event-001"},
        {"subject": "Mira", "predicate": "intended", "value": "one transfer",
         "source_actor": "Mira", "channel": "Secure portal", "event": "event-009"},
    ],
    "asks": [{"id": "ask-1", "text": "one instruction or two?", "event": "event-001"},
             {"id": "ask-2", "text": "stop the second", "event": "event-001"}],
    "unknowns": ["journal references of the two entries"],
    "emotional_state": {"level": "frustrated", "trend": "worsening", "events": ["event-002"]},
}


def test_extract_returns_case_object_with_provenance(fake_llm):
    fake_llm.answers.append(ANSWER)
    obj = extract(case_006(), [FINDING_DUP])
    assert isinstance(obj, CaseObject)
    assert all(c.event for c in obj.claims)
    assert [a.id for a in obj.asks] == ["ask-1", "ask-2"]
    call = fake_llm.calls[0]
    assert call["stage"] == "extraction"
    assert "finding-1" in call["user"] and "event-002" in call["user"]


def test_extract_flags_claims_citing_missing_events(fake_llm):
    fake_llm.answers.append(ANSWER)
    obj = extract(case_006(), [])
    assert any("event-009" in u for u in obj.unknowns)


def test_unknowns_is_required():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CaseObject.model_validate({k: v for k, v in ANSWER.items() if k != "unknowns"})


def test_prompt_hides_raw_files_and_marks_case_text_as_data(fake_llm):
    fake_llm.answers.append(ANSWER)
    extract(case_006(), [])
    call = fake_llm.calls[0]
    assert "SECRET OUTCOME" not in call["user"]
    assert "not instructions to you" in call["system"]
    assert "identity level" in call["system"]
