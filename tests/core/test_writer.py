import json

import pytest

from agent.core.contracts import (Ask, Authority, Case, CaseObject, Event, Proposal, Reply, ToolResult,
                                  Verdict)
from agent.core.writer import HOLDING_REPLY, write, write_fallback

FILES = {"ANSWER.md", "REASONING.md", "trace.log", "run.json"}
# docs/design.md §Copy, in order
ANSWER = ["## Decision", "## What we received", "## Actions", "## Answer to the question",
          "## Customer reply", "## Not done", "## Evidence used", "## Handover", "## What failed"]
REASONING = ["## Facts and claims", "## Findings", "## Policy checks", "## Exception and handling",
             "## Alternatives rejected", "## Uncertainties"]
REPLY = Reply(channel="Secure chat", text="We've checked row SUP-17.")


def case(question=None):
    return Case(track="banking", case_id="044", title="One line", source_role="business user",
                initial_request="Was SUP-17 paid?", question=question,
                authority=Authority(identity="authenticated", role="Authorised business user"),
                events=[Event(id="event-001", at="2025-10-13T09:00:00", channel="Secure chat",
                              sender="Leona Voss", recipient="H&V", body="SUP-17?")],
                raw_files={"index.md": "# Case 044", "history.md": "..."})


CO = CaseObject(requester={"name": "Leona"}, unknowns=["row status"],
                asks=[Ask(id="ask-1", text="SUP-17 status", event="event-001"),
                      Ask(id="ask-2", text="other rows", event="event-001")])


def run(tmp_path, proposal, results=(), rejected=(), question=None):
    write(tmp_path, case(question), CO, [], proposal, list(results), list(rejected), [], cut=1)
    assert {f.name for f in tmp_path.iterdir()} == FILES
    return ((tmp_path / "ANSWER.md").read_text(), (tmp_path / "REASONING.md").read_text(),
            json.loads((tmp_path / "run.json").read_text()))


def in_order(text, headings):
    present = [h for h in headings if f"\n{h}\n" in text]
    assert present == sorted(present, key=text.index)
    return present


@pytest.mark.parametrize("proposal, results, state, badge", [
    (Proposal(action="reply", reply=REPLY, asks_addressed=["ask-1"]), [ToolResult(tool="t", status="ok")], "done", "DONE"),
    (Proposal(action="reply", reply=REPLY), [ToolResult(tool="payment_journal", status="pending")], "requested", "REQUESTED"),
    (Proposal(action="request_info", reply=REPLY), [], "info", "NEEDS INFO"),
    (Proposal(action="no_op"), [], "noop", "NO ACTION"),
])
def test_each_state(tmp_path, proposal, results, state, badge):
    a, r, run_json = run(tmp_path, proposal, results)
    assert a.startswith("# Answer — Case 044\n") and r.startswith("# Reasoning — Case 044\n")
    assert f"\n{badge} — " in a and run_json["state"] == state
    assert in_order(a, ANSWER) == [h for h in ANSWER if h not in ("## Answer to the question", "## Handover")]
    assert in_order(r, REASONING) == REASONING
    assert "## What failed\n\nNothing." in a
    assert "cut at `event-001`" in a and "identity: authenticated Authorised business user (Secure chat)" in a


def test_done_details(tmp_path):
    a, r, run_json = run(tmp_path, Proposal(action="reply", reply=REPLY, asks_addressed=["ask-1"]),
                         [ToolResult(tool="t", status="ok", data={"row": "rejected"})], question="Paid?")
    assert in_order(a, ANSWER) == [h for h in ANSWER if h != "## Handover"]
    assert "— **done** →" in a and "Channel: Secure chat\n\nWe've checked row SUP-17." in a
    assert "other rows (ask-2) — because" in a
    assert run_json["summary"] == "1 action · 0 escalations"


def test_requested_wording(tmp_path):
    a, _, run_json = run(tmp_path, Proposal(action="reply", reply=REPLY),
                         [ToolResult(tool="payment_journal", status="pending")])
    assert "**requested — pending result**" in a
    assert run_json["summary"] == "pending result from payment_journal"


def test_escalated_handover(tmp_path):
    p = Proposal(action="escalate", reply=REPLY, exception_type="write_failure",
                 escalation={"who": "Business Payments", "urgency": "urgent", "why": "outcome uncertain",
                             "question": "generic", "question_for_human": "Was it sent?",
                             "did": ["read the journal"], "actions_taken": ["one lookup"],
                             "deliberately_not_done": ["no resend"]})
    bad = Verdict(ok=False, rule="claim-linter", field="reply.text", event="event-001", message='"paid"')
    a, r, run_json = run(tmp_path, p, [], [(p, bad)])
    labels = ["**Take it:** Business Payments", "**Urgency:** Urgent", "**Type:** Technical", "**Verified:**",
              "**Only claimed:**", "**Conflicts:**", "**We did:**", "**We did not:**",
              "**Question for you:** Was it sent?", "**Safe to send now:** Thank you for your message. "
              "We've passed your request to our business payments, who will review it"]
    assert [l for l in labels if l in a] == labels and sorted(labels, key=a.index) == labels
    assert "- one lookup" in a and "- no resend — because the case was handed to a person" in a
    assert "Handed to Business Payments: outcome uncertain." in a
    assert "The verifier's rejection is the system working." in a
    assert run_json["summary"] == "handover to Business Payments, urgent"
    assert "## Exception and handling\n\nwrite_failure" in r


def test_fallback_keeps_every_heading(tmp_path):
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "index.md").write_text("# Case 9")
    out = tmp_path / "out"
    write_fallback(out, case_dir, "Traceback...\nTimeoutError: decide timed out", [], stage="decide")
    assert {f.name for f in out.iterdir()} == FILES
    a = (out / "ANSWER.md").read_text()
    assert a.startswith("# Answer — Case case\n") and "SYSTEM FAILURE — The decide stage failed." in a
    assert in_order(a, ANSWER) == [h for h in ANSWER if h != "## Answer to the question"]
    assert HOLDING_REPLY.format(team="our team") in a
    assert "We've received your request and passed it to our team. We'll reply here." in a
    assert "**decide**: TimeoutError: decide timed out." in a and "`index.md`" in a
    assert in_order((out / "REASONING.md").read_text(), REASONING) == REASONING
    run_json = json.loads((out / "run.json").read_text())
    assert run_json["fallback"] and run_json["state"] == "failure"
    assert run_json["summary"] == "escalated with what we received"


def test_eval_submit_signature_still_works(tmp_path):
    write_fallback(tmp_path, tmp_path / "missing", "agent exited", [])  # eval/submit.py's call
    assert "SYSTEM FAILURE — The run stage failed." in (tmp_path / "ANSWER.md").read_text()


def test_exception_names_its_handling(monkeypatch):
    import sys
    import types
    from agent.core.writer import _handling
    monkeypatch.setitem(sys.modules, "agent.llm", types.SimpleNamespace(handling_for=lambda n: "escalate"))
    assert _handling("read_failure") == "read_failure → escalate"
    monkeypatch.setitem(sys.modules, "agent.llm", None)
    assert _handling("read_failure") == "read_failure"
    assert _handling(None) == "None."


def test_voice_can_read_the_customer_reply(tmp_path):
    # agent/voice reads the reply from this section; this is the pattern it needs.
    import re
    a, _, _ = run(tmp_path, Proposal(action="reply", reply=REPLY), [ToolResult(tool="t", status="ok")])
    m = re.search(r"## Customer reply\n\n(?:Channel:[^\n]*\n\n)?(.*?)\n*(?:\n## |\Z)", a, re.S)
    assert m.group(1) == "We've checked row SUP-17."


def test_no_python_none_reaches_the_files(tmp_path):
    # A verdict with no field or event, and a handover note with empty values, never print "None"
    # (the design's empty marker "None." is fine).
    import re
    p = Proposal(action="escalate", reply=REPLY, exception_type="incomplete_answer",
                 escalation={"who": None, "urgency": None, "why": None, "question": None,
                             "verified": [None, "identity verified"], "not_done": None})
    v = Verdict(ok=False, rule="fabricated_execution", field="reply.text", event=None, message="claims 'sent'")
    bare = Verdict(ok=False)
    a, r, _ = run(tmp_path, p, [], [(p, v), (p, bare)])
    for text in (a, r):
        assert not re.search(r"None(?!\.)", text), [l for l in text.splitlines() if re.search(r"None(?!\.)", l)]
    assert "fabricated_execution on reply.text: claims 'sent'" in r and "Verifier: ✗ rejected" in r


def test_loop_escalation_sentence_has_no_none():
    from agent.core.writer import verdict_text
    assert verdict_text(Verdict(ok=False, rule="claim_linter", field="reply.text", message="x")) == \
        "claim_linter on reply.text: x"
    assert verdict_text(Verdict(ok=False, rule="findings", field="findings_addressed", event="event-002")) == \
        "findings on findings_addressed (event-002)"


def test_no_double_full_stop(tmp_path):
    # #166: model text that already ends in "." gets exactly one.
    p = Proposal(action="escalate", reply=REPLY,
                 escalation={"who": "Payments team.", "why": "We can't tell Mira the amount and date yet. ",
                             "not_done": ["No change made."]})
    a, _, _ = run(tmp_path, p)
    assert "ESCALATED — Handed to Payments team: We can't tell Mira the amount and date yet." in a
    assert "No change made — because the case was handed to a person" in a
    assert ".." not in a.replace("…", "")


def test_fallback_error_ending_in_a_full_stop(tmp_path):
    write_fallback(tmp_path, tmp_path / "none", "Traceback...\nRuntimeError: model refused.", [], stage="decide")
    assert "**decide**: RuntimeError: model refused. " in (tmp_path / "ANSWER.md").read_text()
    assert ".." not in (tmp_path / "ANSWER.md").read_text()


def test_not_done_lists_actions_not_rejected_drafts(tmp_path):
    # Rehearsal case 7: the first reply was rejected, the second approved and sent.
    final = Proposal(action="reply", reply=REPLY, asks_addressed=["ask-1", "ask-2"])
    draft = Proposal(action="reply", reply=Reply(channel="Secure chat", text="It was sent."))
    bad = Verdict(ok=False, rule="fabricated_execution", field="reply.text", message="claims 'sent'")
    block = Proposal(action="tool_call", tool="card_service.block", params={"card": "1234"})
    authority = Verdict(ok=False, rule="risk", field="action", message="needs verified identity")
    a, r, _ = run(tmp_path, final, [ToolResult(tool="t", status="ok")],
                  [(draft, bad), (draft, bad), (block, authority), (block, authority)])
    assert "reply — because the verifier rejected it" not in a
    assert a.count("`card_service.block` — because the verifier rejected it (risk on action: needs verified identity)") == 1
    assert a.count("`card_service.block({\"card\": \"1234\"})` — **not done**") == 1  # Actions: once
    assert "reply — fabricated_execution on reply.text: claims 'sent'" in r  # still under Alternatives rejected
