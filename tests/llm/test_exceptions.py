import sys
import types

import pytest

from agent.llm import handover
from agent.llm.contracts import CaseObject, Proposal, ToolResult
from agent.llm.exceptions import EXCEPTIONS, handling_for, normalise, sentiment_escalation, tool_risk

from .cases import FINDING_DUP, case_006


def obj(level="calm", trend="steady", asks=None, claims=None):
    return CaseObject(
        requester={"name": "Mira"},
        unknowns=["journal references of the two entries"],
        asks=asks or [{"id": "ask-1", "text": "one instruction or two?", "event": "event-001"}],
        claims=claims or [],
        emotional_state={"level": level, "trend": trend},
    )


def run(proposal, case_object=None, results=(), findings=()):
    return normalise(Proposal.model_validate(proposal), case_006(), case_object or obj(), list(findings), list(results))


WRITE = {"action": "tool_call", "tool": "transfer_journal.return_request", "params": {"action": "cancel", "ref": "T2"}}
READ = {"action": "tool_call", "tool": "transfer_journal", "params": {"action": "lookup"}}
REPLY = {"action": "reply", "reply": {"channel": "Secure chat", "text": "It was sent."}}


def test_registry_has_the_ten_types_of_section_4_8():
    assert len(EXCEPTIONS) == 10
    assert handling_for("Ambiguous reference") == "request_info; never pick one"
    assert handling_for("made_up") == "unknown exception type: escalate"
    assert handling_for(None) is None


@pytest.mark.parametrize("name, proposal, expected", [
    ("ambiguous_request", REPLY, "request_info"),
    ("ambiguous_reference", WRITE, "request_info"),
    ("conflicting_records", WRITE, "escalate"),
    ("conflicting_records", READ, "tool_call"),
    ("missing_authority", WRITE, "request_info"),
    ("missing_authority", READ, "tool_call"),
    ("ambiguous_reference", READ, "tool_call"),
    ("read_failure", READ, "tool_call"),
    ("write_failure", REPLY, "escalate"),
    ("quiet_wrong_value", REPLY, "escalate"),
    ("role_violation", WRITE, "escalate"),
    ("role_violation", REPLY, "reply"),
    ("incomplete_answer", REPLY, "reply"),
    ("hidden_instructions", WRITE, "escalate"),
    ("hidden_instructions", REPLY, "reply"),
    ("something_new", REPLY, "escalate"),
])
def test_each_exception_type_maps_to_its_handling(name, proposal, expected):
    out = run({**proposal, "exception_type": name})
    assert out.action == expected
    if expected == "request_info":
        assert out.reply.text.startswith("To make sure we act on the right request")
        assert "uncert" not in out.reply.text and out.reply.text.endswith(".")
        assert out.tool is None


def test_tool_risk_counts_write_words_on_read_named_tools(monkeypatch):
    fake = types.SimpleNamespace(CATALOGUE={
        "transfer_journal": types.SimpleNamespace(risk=1),
        "transfer_journal.return_request": types.SimpleNamespace(risk=3),
    })
    monkeypatch.setitem(sys.modules, "agent.tools", fake)
    monkeypatch.setattr(sys.modules["agent"], "tools", fake, raising=False)
    assert tool_risk("transfer_journal", {"action": "lookup"}) == 1
    assert tool_risk("transfer_journal", {"action": "cancel"}) == 3
    assert tool_risk("transfer_journal.return_request", {}) == 3
    proposal = {"action": "tool_call", "tool": "transfer_journal",
                "params": {"action": "cancel", "ref": "T2"}, "exception_type": "conflicting_records"}
    assert run(proposal).action == "escalate"


def test_missing_authority_question_fits_an_authenticated_channel():
    out = run({**WRITE, "exception_type": "missing_authority"})
    assert "role this request needs" in out.reply.text and "verified call" not in out.reply.text


def test_read_failure_retries_once_then_escalates():
    failed = ToolResult(tool="transfer_journal", status="timeout")
    assert run({**READ, "exception_type": "read_failure"}, results=[failed]).action == "tool_call"
    assert run({**READ, "exception_type": "read_failure"}, results=[failed, failed]).action == "escalate"


def test_tool_budget_forces_escalation():
    results = [ToolResult(tool="transfer_journal", status="ok")] * 6
    out = run(READ, results=results)
    assert out.action == "escalate" and any("budget" in u for u in out.uncertainties)


@pytest.mark.parametrize("state, expected", [
    ({"level": "calm"}, None),
    ({"level": "frustrated", "trend": "steady"}, None),
    ({"level": "frustrated", "trend": "worsening"}, "frustration is worsening across events, unresolved"),
    ({"level": "distressed"}, "customer is distressed"),
    ({"level": "vulnerable"}, "customer is vulnerable"),
    ({"asks": [{"id": "ask-1", "text": "I want to make a formal complaint", "event": "event-002"}]}, "customer has made a complaint"),
])
def test_sentiment_rule(state, expected):
    assert sentiment_escalation(obj(**state)) == expected


def test_mild_frustration_is_solved_not_escalated():
    assert run(REPLY, obj(level="frustrated")).action == "reply"


def test_distress_escalates_early_as_emotional():
    out = run(REPLY, obj(level="vulnerable"))
    assert out.action == "escalate"
    assert out.escalation["type"] == "emotional" and out.escalation["urgency"] == "high"
    assert out.escalation["who"] == "Customer care (vulnerable customers)"
    assert "sentiment: customer is vulnerable" in out.escalation["why"]
    assert out.reply.text == out.escalation["holding_reply"]


def test_escalation_always_carries_the_full_handover_note():
    claims = [
        {"subject": "pending transfer", "predicate": "status", "value": "stopped", "source_actor": "Mira",
         "channel": "Secure chat", "event": "event-001", "conflicts_with": [1]},
        {"subject": "pending transfer", "predicate": "status", "value": "pending", "source_actor": "H&V",
         "channel": "Internal note", "event": "event-002"},
    ]
    results = [ToolResult(tool="transfer_journal", params={"action": "lookup"}, status="pending")]
    out = run({"action": "escalate", "exception_type": "conflicting_records"},
              obj(claims=claims), results=results, findings=[FINDING_DUP])
    note = out.escalation
    assert list(note) == ["who", "urgency", "type", "why", "verified", "claimed", "conflicts", "did",
                          "not_done", "question", "holding_reply"]
    assert note["who"] == "Payments operations"
    assert note["type"] == "technical"
    assert note["why"] == "conflicting_records"
    assert any("authenticated" in v for v in note["verified"])
    assert any("event-001" in c for c in note["claimed"])
    assert any("finding-1" in c for c in note["conflicts"])
    assert any("event-001 conflicts with event-002" in c for c in note["conflicts"])
    assert any("pending" in d for d in note["did"])
    assert "no change made to the account" in note["not_done"]
    assert any("ask-1" in n for n in note["not_done"])
    assert note["question"].startswith("Please establish")
    assert note["holding_reply"] and "£" not in note["holding_reply"]
    md = handover.render(note)
    assert md.startswith("## Handover note") and "**Question for you:**" in md


def test_model_handover_fields_are_kept():
    out = run({"action": "escalate", "escalation": {"team": "Fraud team", "urgency": "urgent",
                                                    "question": "Is this payee known fraud?"}})
    assert out.escalation["who"] == "Fraud team"
    assert out.escalation["urgency"] == "urgent"
    assert out.escalation["question"] == "Is this payee known fraud?"


def test_loop_style_title_case_exception_names_are_understood():
    out = run({**REPLY, "exception_type": "Write failure"})
    assert out.exception_type == "write_failure" and out.action == "escalate"
