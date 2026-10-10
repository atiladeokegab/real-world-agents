import pytest

from agent.llm import handover
from agent.llm._contracts import CaseObject, Proposal, ToolResult
from agent.llm.exceptions import EXCEPTIONS, handling_for, normalise, sentiment_escalation

from .cases import FINDING_DUP, case_006


def obj(level="calm", trend="steady", asks=None, claims=None):
    return CaseObject(
        unknowns=["journal references of the two entries"],
        asks=asks or [{"id": "ask-1", "text": "one instruction or two?", "event": "event-001"}],
        claims=claims or [],
        emotional_state={"level": level, "trend": trend},
    )


def run(proposal, case_object=None, results=(), findings=()):
    return normalise(Proposal.model_validate(proposal), case_006(), case_object or obj(), list(findings), list(results))


WRITE = {"action": "tool_call", "tool": "transfer_journal", "params": {"action": "cancel", "ref": "T2"}}
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
        assert out.tool is None


def test_read_failure_retries_once_then_escalates():
    failed = ToolResult(tool="transfer_journal", status="timeout")
    assert run({**READ, "exception_type": "read_failure"}, results=[failed]).action == "tool_call"
    assert run({**READ, "exception_type": "read_failure"}, results=[failed, failed]).action == "escalate"


def test_tool_budget_forces_escalation():
    results = [ToolResult(tool="transfer_journal", status="ok")] * 6
    out = run(READ, results=results)
    assert out.action == "escalate" and any("budget" in u for u in out.uncertainties)


@pytest.mark.parametrize("state, expected", [
    (dict(level="calm"), None),
    (dict(level="frustrated", trend="steady"), None),
    (dict(level="frustrated", trend="worsening"), "frustration is worsening across events, unresolved"),
    (dict(level="distressed"), "customer is distressed"),
    (dict(level="vulnerable"), "customer is vulnerable"),
    (dict(asks=[{"id": "ask-1", "text": "I want to make a formal complaint"}]), "customer has made a complaint"),
])
def test_sentiment_rule(state, expected):
    assert sentiment_escalation(obj(**state)) == expected


def test_mild_frustration_is_solved_not_escalated():
    assert run(REPLY, obj(level="frustrated")).action == "reply"


def test_distress_escalates_early_as_emotional():
    out = run(REPLY, obj(level="vulnerable"))
    assert out.action == "escalate"
    assert out.escalation.type == "emotional" and out.escalation.urgency == "high"
    assert out.reply.text == out.escalation.holding_reply


def test_escalation_always_carries_the_full_handover_note():
    claims = [
        {"subject": "pending transfer", "predicate": "status", "value": "stopped", "source_actor": "Mira",
         "event": "event-001", "conflicts_with": [1]},
        {"subject": "pending transfer", "predicate": "status", "value": "pending", "source_actor": "H&V",
         "event": "event-002"},
    ]
    results = [ToolResult(tool="transfer_journal", params={"action": "lookup"}, status="pending")]
    out = run({"action": "escalate", "exception_type": "conflicting_records"},
              obj(claims=claims), results=results, findings=[FINDING_DUP])
    note = out.escalation
    assert note.team == "Payments operations"
    assert note.type == "technical"
    assert any("authenticated" in v for v in note.verified)
    assert any("event-001" in c for c in note.claimed)
    assert any("finding-1" in c for c in note.conflicts)
    assert any("event-001 conflicts with event-002" in c for c in note.conflicts)
    assert any("pending" in d for d in note.done)
    assert "no change made to the account" in note.not_done
    assert any("ask-1" in n for n in note.not_done)
    assert note.question.startswith("Please establish")
    assert note.holding_reply and "£" not in note.holding_reply
    md = handover.render(note)
    assert md.startswith("## Handover note") and "**Question for you:**" in md


def test_model_handover_fields_are_kept():
    out = run({"action": "escalate", "escalation": {"team": "Fraud team", "urgency": "urgent",
                                                    "question": "Is this payee known fraud?"}})
    assert out.escalation.team == "Fraud team"
    assert out.escalation.urgency == "urgent"
    assert out.escalation.question == "Is this payee known fraud?"
