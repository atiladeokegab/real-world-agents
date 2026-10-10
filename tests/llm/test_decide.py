from agent.llm import decide
from agent.llm._contracts import CaseObject, ToolResult, Verdict

from .cases import FINDING_DUP, case_006

CASE_OBJECT = CaseObject(
    unknowns=["journal references"],
    asks=[{"id": "ask-1", "text": "one instruction or two?", "event": "event-001"}],
)
LOOKUP = {"action": "tool_call", "tool": "transfer_journal", "params": {"action": "lookup"},
          "asks_addressed": ["ask-1"], "findings_addressed": ["finding-1"]}


def test_decide_returns_one_proposal_with_exactly_once_rule(fake_llm):
    fake_llm.answers.append(LOOKUP)
    out = decide(case_006(), CASE_OBJECT, [FINDING_DUP], [])
    assert out.action == "tool_call" and out.tool == "transfer_journal"
    call = fake_llm.calls[0]
    assert call["stage"] == "decision"
    assert "Every action must happen exactly once." in call["system"]
    assert "ambiguous_reference" in call["system"] and "{exception_types}" not in call["system"]
    assert "finding-1" in call["user"] and "identity: authenticated" in call["user"]


def test_decide_can_choose_escalate_request_info_or_no_op(fake_llm):
    for action in ("escalate", "request_info", "no_op"):
        fake_llm.answers.append({"action": action})
        assert decide(case_006(), CASE_OBJECT, [], []).action == action


def test_question_is_passed_and_answered(fake_llm):
    fake_llm.answers.append({"action": "reply", "reply": {"text": "We are checking."},
                             "question_answer": "No, it should not be stopped yet."})
    out = decide(case_006(question="Should the pending payment be stopped?"), CASE_OBJECT, [], [])
    assert out.question_answer
    assert "<question>Should the pending payment be stopped?</question>" in fake_llm.calls[0]["user"]


def test_feedback_verdict_reaches_the_retry(fake_llm):
    fake_llm.answers.append(LOOKUP)
    verdict = Verdict(ok=False, rule="findings", field="findings_addressed", event="event-001",
                      message="finding-1 not addressed")
    decide(case_006(), CASE_OBJECT, [FINDING_DUP], [], feedback=verdict)
    user = fake_llm.calls[0]["user"]
    assert "rule: findings" in user and "field: findings_addressed" in user and "event: event-001" in user


def test_tool_results_so_far_are_shown(fake_llm):
    fake_llm.answers.append({"action": "reply", "reply": {"text": "Two separate instructions."}})
    results = [ToolResult(tool="transfer_journal", status="ok", data={"instructions": 2}, source_event="event-004")]
    decide(case_006(), CASE_OBJECT, [], results)
    assert '"instructions": 2' in fake_llm.calls[0]["user"] and "Tool calls used: 1 of 6." in fake_llm.calls[0]["user"]
