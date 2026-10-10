from agent.llm import decide
from agent.llm.contracts import CaseObject, ToolResult, Verdict

from .cases import FINDING_DUP, case_006

CASE_OBJECT = CaseObject(
    requester={"name": "Mira"},
    unknowns=["journal references"],
    asks=[{"id": "ask-1", "text": "one instruction or two?", "event": "event-001"}],
)
NO_ASKS = CaseObject(requester={"name": "Mira"}, unknowns=[])
LOOKUP = {"action": "tool_call", "tool": "transfer_journal", "params": {"action": "lookup"},
          "asks_addressed": ["ask-1"], "findings_addressed": ["finding-1"]}


def test_decide_returns_one_proposal_with_exactly_once_rule(fake_llm):
    fake_llm.answers.append(LOOKUP)
    out = decide(case_006(), CASE_OBJECT, [FINDING_DUP], [])
    assert out.action == "tool_call" and out.tool == "transfer_journal"
    call = fake_llm.calls[0]
    assert call["stage"] == "decision"
    assert "Every action must happen exactly once." in call["system"]
    assert "Lookups are risk 1 and need no role" in call["system"]
    assert "uses exactly these keys and no others: who" in call["system"]
    assert "When action is escalate, set the exception_type" in call["system"]
    assert "asks_addressed lists every ask id" in call["system"]
    assert "We'll reply here once they've confirmed." in call["system"]
    assert '"credited", "refunded"' in call["system"]
    assert "ambiguous_reference" in call["system"] and "{exception_types}" not in call["system"]
    assert "finding-1" in call["user"] and "identity: authenticated" in call["user"]


def test_decide_can_choose_escalate_request_info_or_no_op(fake_llm):
    for action in ("escalate", "request_info", "no_op"):
        fake_llm.answers.append({"action": action})
        assert decide(case_006(), NO_ASKS, [], []).action == action


def test_question_is_passed_and_answered(fake_llm):
    fake_llm.answers.append({"action": "reply", "reply": {"channel": "Secure chat", "text": "We are checking."},
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
    fake_llm.answers.append({"action": "reply", "reply": {"channel": "Secure chat", "text": "Two separate instructions."}})
    results = [ToolResult(tool="transfer_journal", status="ok", data={"instructions": 2}, source_event="event-004")]
    decide(case_006(), CASE_OBJECT, [], results)
    assert '"instructions": 2' in fake_llm.calls[0]["user"] and "Tool calls used: 1 of 6." in fake_llm.calls[0]["user"]


def test_channel_constraints_and_reply_channel_rules_in_prompts():
    from agent.llm import prompts
    assert "Type channel only for a rule about which channel to reply or act on" in prompts.EXTRACTION_SYSTEM
    assert "is not authorisation" in prompts.EXTRACTION_SYSTEM
    assert "never an external message" in prompts.DECISION_SYSTEM


PENDING = [ToolResult(tool="mandate_journal", status="pending", data={"note": "status check requested"})]
PENDING_REPLY = {"action": "reply", "asks_addressed": ["ask-1"],
                 "reply": {"channel": "Secure chat", "text": "We've asked our payments team to check the mandate. "
                                                             "We'll reply here once they've confirmed."}}


def test_no_op_after_a_pending_lookup_is_retried_as_a_reply(fake_llm):
    fake_llm.answers += [{"action": "no_op", "asks_addressed": ["ask-1"]}, PENDING_REPLY]
    out = decide(case_006(), CASE_OBJECT, [], PENDING)
    assert out.action == "reply" and "once they've confirmed" in out.reply.text
    assert len(fake_llm.calls) == 2 and "rule: completion" in fake_llm.calls[1]["user"]


def test_no_op_twice_while_pending_escalates_with_a_holding_reply(fake_llm):
    fake_llm.answers += [{"action": "no_op"}, {"action": "no_op"}]
    out = decide(case_006(), CASE_OBJECT, [], PENDING)
    assert out.action == "escalate" and out.exception_type == "incomplete_answer"
    assert out.reply and out.reply.text and out.escalation


def test_no_op_on_a_status_ask_is_retried_even_without_a_lookup(fake_llm):
    status = {"action": "reply", "asks_addressed": ["ask-1"],
              "reply": {"channel": "Secure chat", "text": "Your mandate is shown as Active."}}
    fake_llm.answers += [{"action": "no_op", "question_answer": "No refund is due."}, status]
    done = [ToolResult(tool="mandate_journal", status="ok", data={"status": "Active"})]
    assert decide(case_006(), CASE_OBJECT, [], done).action == "reply"


def test_no_op_with_nothing_asked_is_kept(fake_llm):
    fake_llm.answers.append({"action": "no_op"})
    assert decide(case_006(), NO_ASKS, [], []).action == "no_op" and len(fake_llm.calls) == 1


def test_prompt_forbids_no_op_while_an_ask_is_unanswered(fake_llm):
    fake_llm.answers.append(LOOKUP)
    decide(case_006(), CASE_OBJECT, [], [])
    system = fake_llm.calls[0]["system"]
    assert "Never no_op while an ask is unanswered" in system
    assert 'A pending result is not a finished check: never write "checked"' in system


def test_prompt_acts_after_a_pending_read(fake_llm):
    fake_llm.answers.append(LOOKUP)
    decide(case_006(), CASE_OBJECT, [], [])
    assert "the required read came back pending, propose the matching action next" in fake_llm.calls[0]["system"]


NOT_FOUND = [ToolResult(tool="transfer_journal", status="not_found")]
TIMED_OUT = [ToolResult(tool="transfer_journal", status="timeout")] * 2
HONEST = {"action": "reply", "reply": {"channel": "Secure chat", "text": "We can't see a record of it yet."},
          "asks_addressed": ["ask-1"]}


def test_not_found_labelled_read_failure_is_retried_into_a_reply(fake_llm):
    fake_llm.answers += [{"action": "escalate", "exception_type": "read_failure"}, HONEST]
    out = decide(case_006(), CASE_OBJECT, [], NOT_FOUND)
    assert out.action == "reply" and len(fake_llm.calls) == 2
    assert "not_found is a normal answer, not a read_failure" in fake_llm.calls[1]["user"]


def test_timeout_still_escalates_as_read_failure(fake_llm):
    fake_llm.answers.append({"action": "escalate", "exception_type": "read_failure"})
    assert decide(case_006(), CASE_OBJECT, [], TIMED_OUT).action == "escalate" and len(fake_llm.calls) == 1


def test_prompt_says_not_found_is_not_a_read_failure(fake_llm):
    fake_llm.answers.append(LOOKUP)
    decide(case_006(), CASE_OBJECT, [], [])
    assert "A not_found result is a normal answer, not a read_failure" in fake_llm.calls[0]["system"]
