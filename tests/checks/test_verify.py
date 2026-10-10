import sys
import types
from datetime import datetime, timezone

from agent.checks import verify
from agent.core.contracts import (
    Ask,
    Authority,
    Case,
    CaseObject,
    Claim,
    Constraint,
    Event,
    Finding,
    Proposal,
    Reply,
    Requester,
    ToolResult,
    ToolSpec,
)


def _ev(n, body, channel="Secure chat", sender="Mara Ellison", recipient="H&V agent"):
    return Event(
        id=f"event-{n:03d}",
        at=datetime(2025, 7, 19, 9, 0, tzinfo=timezone.utc),
        channel=channel,
        sender=sender,
        recipient=recipient,
        body=body,
    )


def _case(events, question=None, identity="verified", role="Bank customer"):
    return Case(
        track="t",
        case_id="t",
        title="t",
        source_role="Bank customer",
        initial_request="help",
        events=list(events),
        question=question,
        authority=Authority(identity=identity, role=role),
    )


def _object(claims=(), asks=(), constraints=(), requester="Mara Ellison"):
    return CaseObject(
        requester=Requester(name=requester),
        claims=list(claims),
        asks=list(asks),
        unknowns=[],
        constraints=list(constraints),
    )


def _claim(value, subject="payment", predicate="detail", event="event-001"):
    return Claim(
        subject=subject,
        predicate=predicate,
        value=value,
        source_actor="Mara Ellison",
        channel="Secure chat",
        event=event,
    )


def _proposal(**kw):
    kw.setdefault("action", "reply")
    kw.setdefault("claims_relied_on", ["event-001"])
    return Proposal(**kw)


def _reply(text, channel="secure chat"):
    return Reply(channel=channel, text=text)


def _result(tool, status="ok", data=None, source_event=None):
    return ToolResult(tool=tool, params={}, status=status,
                      data=data or {}, source_event=source_event)


def _finding(n=1, kind="anomaly", check="identity", events=("event-001",)):
    return Finding(id=f"finding-{n}", kind=kind, check=check,
                   detail="detail", events=list(events))


def _spec(name, risk=1, roles=(), required_reads=()):
    return ToolSpec(name=name, risk=risk, roles=list(roles),
                    required_reads=list(required_reads))


def _catalogue(monkeypatch, specs):
    """Inject a stub agent.tools module holding the given {name: ToolSpec} catalogue."""
    monkeypatch.setitem(sys.modules, "agent.tools",
                        types.SimpleNamespace(CATALOGUE=dict(specs)))


# --- §4.6 acceptance: a valid reply proposal passes every rule ---

def test_valid_reply_ok():
    case = _case([_ev(1, "You sent £420.00 to Alder & Reed Workshop on 19 July 2025.")])
    obj = _object(claims=[
        _claim("sent £420.00 on 19 July 2025", subject="Alder & Reed Workshop"),
    ])
    results = [_result("transfer_journal", data={"status": "sent", "amount": "420.00"},
                       source_event="event-001")]
    proposal = _proposal(
        reply=_reply("You sent £420.00 to Alder & Reed Workshop on 19 July 2025."),
        claims_relied_on=["event-001", "tool:transfer_journal"],
    )
    assert verify(proposal, case, obj, [], results).ok


# --- rule: citation ---

def test_citation_ok():
    case = _case([_ev(1, "help")])
    results = [_result("transfer_journal")]
    proposal = _proposal(action="no_op",
                         claims_relied_on=["event-001", "tool:transfer_journal"])
    assert verify(proposal, case, _object(), [], results).ok


def test_citation_missing_event_rejected():
    case = _case([_ev(1, "help")])
    proposal = _proposal(action="no_op", claims_relied_on=["event-001", "event-099"])
    verdict = verify(proposal, case, _object(), [], [])
    assert not verdict.ok
    assert verdict.rule == "citation"
    assert verdict.field == "claims_relied_on"
    assert verdict.event == "event-099"


def test_citation_missing_tool_result_rejected():
    case = _case([_ev(1, "help")])
    proposal = _proposal(action="no_op", claims_relied_on=["tool:transfer_journal"])
    verdict = verify(proposal, case, _object(), [], [])
    assert not verdict.ok
    assert verdict.rule == "citation"
    assert verdict.field == "claims_relied_on"
    assert "tool:transfer_journal" in verdict.message


# --- rule: claim linter ---

def test_claim_linter_ok():
    case = _case([_ev(1, "what was the fee")])
    obj = _object(claims=[
        _claim("£50.00", subject="overdraft fee"),
        _claim("Mara Ellison", subject="requester", predicate="name"),
    ])
    proposal = _proposal(reply=_reply("The fee on the account of Mara Ellison is £50.00."))
    assert verify(proposal, case, obj, [], []).ok


def test_claim_linter_unseen_amount_rejected():
    case = _case([_ev(1, "help")])
    obj = _object(claims=[_claim("£420.00 transfer")])
    proposal = _proposal(reply=_reply("Your refund of £50.00 is on hold."))
    verdict = verify(proposal, case, obj, [], [])
    assert not verdict.ok
    assert verdict.rule == "claim_linter"
    assert verdict.field == "reply.text"
    assert "50.00" in verdict.message


def test_claim_linter_unseen_name_rejected():
    case = _case([_ev(1, "help")])
    obj = _object(claims=[_claim("£420.00 to Alder & Reed Workshop")])
    proposal = _proposal(reply=_reply("The payment to Elena Marlow is noted."))
    verdict = verify(proposal, case, obj, [], [])
    assert not verdict.ok
    assert verdict.rule == "claim_linter"
    assert verdict.field == "reply.text"
    assert "Elena Marlow" in verdict.message


def test_claim_linter_greeting_to_requester_ok():
    # "Dear Ms Shah" lints as "Ms Shah" against the requester's own name
    case = _case([_ev(1, "help")])
    obj = _object(requester="Ms Shah")
    proposal = _proposal(
        reply=_reply("Dear Ms Shah, please confirm which transfer you mean."))
    assert verify(proposal, case, obj, [], []).ok


def test_claim_linter_wrong_greeting_name_rejected():
    # a greeting to a name that is not the requester's still fails
    obj = _object(requester="Ms Shah")
    proposal = _proposal(reply=_reply("Dear Ms Nobody, please confirm."))
    verdict = verify(proposal, _case([_ev(1, "help")]), obj, [], [])
    assert not verdict.ok
    assert verdict.rule == "claim_linter"


def test_claim_linter_eval_false_positives_clean():
    # every false positive the real eval produced (#89 / #69 review)
    case = _case([_ev(1, "the transfer to Alder & Reed Workshop went out"),
                  _ev(2, "Please pass it to Ms Mercer in Payments.")])
    obj = _object(
        claims=[_claim("Northmere Studio Ltd"),
                _claim("Owen Bell's Payroll Approver"),
                _claim("batch-041.csv arrived")],
        requester="Ms Ellery",
    )
    results = [_result("transfer_journal", data={"status": "ok"})]
    for text in [
        "Hello Mara, please confirm which transfer you mean.",
        "Hi Mara, we are on it.",
        "Hello Rowan, we are on it.",
        "Hello Leona, we are on it.",
        "Hello Ms Mercer, we are on it.",
        "Dear Ms Ellery, please confirm which transfer you mean.",
        "I'm on it now.",
        "I've asked and will come back.",
        "I'll confirm once the journal answers.",
        "Once I have the reference I will reply.",
        "H&V. We are looking into it.",
        "H&V. Our team is on it.",
        "SENT. You will hear from us.",
        "PIN. That stays with you.",
        "Vale Bank holds the record.",
        "The Direct Debit stays untouched.",
        "The Profile page shows it.",
        "The supplier is Northmere Studio Ltd's account.",
        "Owen Bell's Payroll Approver was named.",
        "We have written to Alder Reed.",   # tokens from the event text alone
        "The file batch-041 is in the portal.",  # prefix of batch-041.csv
    ]:
        proposal = _proposal(reply=_reply(text))
        assert verify(proposal, case, obj, [], results).ok, text


def test_claim_linter_unseen_date_rejected():
    case = _case([_ev(1, "help")])
    obj = _object(claims=[_claim("statement covers 1 July 2025")])
    proposal = _proposal(reply=_reply("The figure covers the period to 19 July 2025."))
    verdict = verify(proposal, case, obj, [], [])
    assert not verdict.ok
    assert verdict.rule == "claim_linter"
    assert "19 July 2025" in verdict.message


# --- rule: no fabricated execution ---

def test_fabricated_execution_ok():
    case = _case([_ev(1, "did my payment go out")])
    obj = _object(claims=[_claim("£420.00 to Alder & Reed Workshop")])
    results = [_result("transfer_journal", data={"status": "sent"},
                       source_event="event-001")]
    proposal = _proposal(
        reply=_reply("Your payment of £420.00 to Alder & Reed Workshop was sent."),
        claims_relied_on=["event-001", "tool:transfer_journal"],
    )
    assert verify(proposal, case, obj, [], results).ok


def test_fabricated_execution_pending_result_rejected():
    # "requested — pending result" must never become "done" (§4.3)
    case = _case([_ev(1, "did my payment go out")])
    obj = _object(claims=[_claim("£420.00 to Alder & Reed Workshop")])
    results = [_result("transfer_journal", status="pending", data={"status": "pending"},
                       source_event="event-001")]
    proposal = _proposal(
        reply=_reply("Your payment of £420.00 to Alder & Reed Workshop was sent."),
        claims_relied_on=["event-001", "tool:transfer_journal"],
    )
    verdict = verify(proposal, case, obj, [], results)
    assert not verdict.ok
    assert verdict.rule == "fabricated_execution"
    assert verdict.field == "reply.text"
    assert verdict.event == "event-001"
    assert "sent" in verdict.message


def test_fabricated_execution_negated_ok():
    case = _case([_ev(1, "where is my payment")])
    proposal = _proposal(
        reply=_reply("We have not sent the payment; it is still pending.")
    )
    assert verify(proposal, case, _object(), [], []).ok


def test_fabricated_execution_future_and_passive_ok():
    # "we will send" / "is being processed" / "under review" promise, not done
    case = _case([_ev(1, "where is my payment")])
    proposal = _proposal(
        reply=_reply("We will send it shortly — it is being processed "
                     "and is under review.")
    )
    assert verify(proposal, case, _object(), [], []).ok


# --- rule: question answered ---

def test_question_answered_ok():
    case = _case([_ev(1, "help")], question="When was the fee applied?")
    proposal = _proposal(
        question_answer="On 19 July 2025.",
        reply=_reply("Please see your statement for the date."),
    )
    assert verify(proposal, case, _object(), [], []).ok


def test_question_unanswered_rejected():
    case = _case([_ev(1, "help")], question="When was the fee applied?")
    proposal = _proposal(reply=_reply("Please see your statement for the date."))
    verdict = verify(proposal, case, _object(), [], [])
    assert not verdict.ok
    assert verdict.rule == "question"
    assert verdict.field == "question_answer"


# --- rule: findings ---

def test_findings_addressed_ok():
    case = _case([_ev(1, "help")])
    findings = [_finding(1)]
    proposal = _proposal(findings_addressed=["finding-1"],
                         reply=_reply("Thanks, that is noted."))
    assert verify(proposal, case, _object(), findings, []).ok


def test_findings_unaddressed_rejected():
    case = _case([_ev(1, "help")])
    findings = [_finding(1)]
    proposal = _proposal(reply=_reply("Thanks, that is noted."))
    verdict = verify(proposal, case, _object(), findings, [])
    assert not verdict.ok
    assert verdict.rule == "findings"
    assert verdict.field == "findings_addressed"
    assert verdict.event == "event-001"


# --- rule: authority & risk ---

def test_tool_call_in_catalogue_ok(monkeypatch):
    _catalogue(monkeypatch, {
        "transfer_journal": _spec("transfer_journal", risk=1, roles=["Bank customer"]),
    })
    case = _case([_ev(1, "help")])
    proposal = _proposal(action="tool_call", tool="transfer_journal",
                         params={"reference": "SUP-17"})
    assert verify(proposal, case, _object(), [], []).ok


def test_tool_call_unknown_tool_rejected(monkeypatch):
    _catalogue(monkeypatch, {"transfer_journal": _spec("transfer_journal")})
    case = _case([_ev(1, "help")])
    proposal = _proposal(action="tool_call", tool="make_tea")
    verdict = verify(proposal, case, _object(), [], [])
    assert not verdict.ok
    assert verdict.rule == "catalogue"
    assert verdict.field == "tool"


def test_tool_call_empty_catalogue_rejected(monkeypatch):
    # an empty catalogue rejects every tool_call, whether or not agent.tools exists
    monkeypatch.setattr(sys.modules["agent.checks.verify"],
                        "_catalogue", lambda: {})
    case = _case([_ev(1, "help")])
    proposal = _proposal(action="tool_call", tool="transfer_journal")
    verdict = verify(proposal, case, _object(), [], [])
    assert not verdict.ok
    assert verdict.rule == "catalogue"
    assert verdict.field == "tool"


def test_authority_role_not_checked_on_read(monkeypatch):
    # lookups are risk 1 and need no role: an unseen sub-role may still read
    _catalogue(monkeypatch, {
        "business_service": _spec("business_service", risk=1,
                                  roles=["Authorised business user"]),
    })
    case = _case([_ev(1, "help")], role="authorised file uploader")
    proposal = _proposal(action="tool_call", tool="business_service",
                         params={"batch": "SUP-17"})
    assert verify(proposal, case, _object(), [], []).ok


def test_authority_role_rejected(monkeypatch):
    _catalogue(monkeypatch, {
        "business_service.release_batch": _spec(
            "business_service.release_batch", risk=3,
            roles=["Authorised business user"],
            required_reads=["business_service"]),
    })
    case = _case([_ev(1, "help")], role="authorised file uploader",
                 identity="verified")
    results = [_result("business_service")]
    proposal = _proposal(action="tool_call",
                         tool="business_service.release_batch",
                         params={"batch": "SUP-17"},
                         claims_relied_on=["event-001", "tool:business_service"])
    verdict = verify(proposal, case, _object(), [], results)
    assert not verdict.ok
    assert verdict.rule == "authority"
    assert verdict.field == "action"
    assert "authorised file uploader" in verdict.message


def test_risk3_verified_with_required_reads_ok(monkeypatch):
    _catalogue(monkeypatch, {
        "business_service.release_batch": _spec(
            "business_service.release_batch", risk=3,
            roles=["Authorised business user"], required_reads=["business_service"]),
    })
    case = _case([_ev(1, "help")], identity="verified", role="Authorised business user")
    results = [_result("business_service", data={"batch": "SUP-17"})]
    proposal = _proposal(action="tool_call", tool="business_service.release_batch",
                         params={"batch": "SUP-17"},
                         claims_relied_on=["event-001", "tool:business_service"])
    assert verify(proposal, case, _object(), [], results).ok


def test_risk3_unverified_identity_rejected(monkeypatch):
    _catalogue(monkeypatch, {
        "business_service.release_batch": _spec(
            "business_service.release_batch", risk=3,
            roles=["Authorised business user"], required_reads=["business_service"]),
    })
    case = _case([_ev(1, "help")], identity="authenticated",
                 role="Authorised business user")
    results = [_result("business_service")]
    proposal = _proposal(action="tool_call", tool="business_service.release_batch",
                         claims_relied_on=["event-001", "tool:business_service"])
    verdict = verify(proposal, case, _object(), [], results)
    assert not verdict.ok
    assert verdict.rule == "risk"
    assert verdict.field == "action"


def test_risk3_missing_required_reads_rejected(monkeypatch):
    _catalogue(monkeypatch, {
        "business_service.release_batch": _spec(
            "business_service.release_batch", risk=3,
            roles=["Authorised business user"], required_reads=["business_service"]),
    })
    case = _case([_ev(1, "help")], identity="verified", role="Authorised business user")
    proposal = _proposal(action="tool_call", tool="business_service.release_batch")
    verdict = verify(proposal, case, _object(), [], [])
    assert not verdict.ok
    assert verdict.rule == "risk"
    assert "business_service" in verdict.message


# --- rule: authority & risk — channel constraint ---

def test_channel_constraint_ok():
    case = _case([_ev(1, "help")])
    obj = _object(constraints=[
        Constraint(type="channel", rule="not by email", source="event-001"),
    ])
    proposal = _proposal(reply=_reply("Your statement is ready.", channel="secure chat"))
    assert verify(proposal, case, obj, [], []).ok


def test_channel_constraint_rejected():
    case = _case([_ev(1, "help")])
    obj = _object(constraints=[
        Constraint(type="channel", rule="not by email", source="event-001"),
    ])
    proposal = _proposal(reply=_reply("Your statement is ready.", channel="email"))
    verdict = verify(proposal, case, obj, [], [])
    assert not verdict.ok
    assert verdict.rule == "channel"
    assert verdict.field == "reply.channel"
    assert verdict.event == "event-001"


# --- rule: completion ---

def test_completion_ask_addressed_ok():
    case = _case([_ev(1, "help")])
    obj = _object(asks=[Ask(id="ask-1", text="confirm the amount", event="event-001")])
    proposal = _proposal(asks_addressed=["ask-1"],
                         reply=_reply("Thanks, that is noted."))
    assert verify(proposal, case, obj, [], []).ok


def test_completion_escalation_handles_asks_ok():
    case = _case([_ev(1, "help")])
    obj = _object(asks=[Ask(id="ask-1", text="confirm the amount", event="event-001")])
    proposal = _proposal(action="escalate",
                         escalation={"note": "cannot confirm the amount"})
    assert verify(proposal, case, obj, [], []).ok


def test_completion_unaddressed_ask_rejected():
    case = _case([_ev(1, "help")])
    obj = _object(asks=[Ask(id="ask-1", text="confirm the amount", event="event-001")])
    proposal = _proposal(reply=_reply("Thanks, that is noted."))
    verdict = verify(proposal, case, obj, [], [])
    assert not verdict.ok
    assert verdict.rule == "completion"
    assert verdict.field == "asks_addressed"
    assert verdict.event == "event-001"


# --- rule: material conflict ---

def test_conflict_resolved_by_ok_lookup_ok():
    case = _case([
        _ev(1, "The transfer was £420.00."),
        _ev(2, "The transfer was £430.00, not £420.00."),
    ])
    obj = _object(claims=[_claim("£420.00", subject="transfer")])
    findings = [_finding(1, kind="conflict", check="amounts",
                         events=("event-001", "event-002"))]
    results = [_result("transfer_journal", data={"amount": "420.00"},
                       source_event="event-001")]
    proposal = _proposal(findings_addressed=["finding-1"],
                         reply=_reply("The confirmed amount is £420.00."))
    assert verify(proposal, case, obj, findings, results).ok


def test_conflict_unresolved_reply_rejected():
    case = _case([
        _ev(1, "The transfer was £420.00."),
        _ev(2, "The transfer was £430.00, not £420.00."),
    ])
    obj = _object(claims=[_claim("£420.00", subject="transfer")])
    findings = [_finding(1, kind="conflict", check="amounts",
                         events=("event-001", "event-002"))]
    proposal = _proposal(findings_addressed=["finding-1"],
                         reply=_reply("The correct amount is £420.00."))
    verdict = verify(proposal, case, obj, findings, [])
    assert not verdict.ok
    assert verdict.rule == "conflict"
    assert verdict.field == "action"
    assert verdict.event == "event-001"


def test_conflict_unresolved_escalate_ok():
    case = _case([
        _ev(1, "The transfer was £420.00."),
        _ev(2, "The transfer was £430.00, not £420.00."),
    ])
    findings = [_finding(1, kind="conflict", check="amounts",
                         events=("event-001", "event-002"))]
    proposal = _proposal(action="escalate", findings_addressed=["finding-1"],
                         escalation={"note": "unresolved amount conflict"})
    assert verify(proposal, case, _object(), findings, []).ok


# --- rule: disclosure ---

def test_disclosure_ok():
    case = _case([_ev(1, "help")])
    proposal = _proposal(reply=_reply("Your new statement is available in the portal."))
    assert verify(proposal, case, _object(), [], []).ok


def test_disclosure_sort_code_rejected():
    case = _case([_ev(1, "help")])
    proposal = _proposal(reply=_reply("For reference, your sort code is 12-34-56."))
    verdict = verify(proposal, case, _object(), [], [])
    assert not verdict.ok
    assert verdict.rule == "disclosure"
    assert verdict.field == "reply.text"
    assert "12-34-56" in verdict.message


def test_disclosure_account_number_rejected():
    case = _case([_ev(1, "help")])
    proposal = _proposal(reply=_reply("For reference, account 12345678."))
    verdict = verify(proposal, case, _object(), [], [])
    assert not verdict.ok
    assert verdict.rule == "disclosure"
    assert verdict.field == "reply.text"
    assert "12345678" in verdict.message


def test_disclosure_device_id_rejected():
    case = _case([_ev(1, "help")])
    # the id is evidenced, so the claim linter passes — disclosure still forbids it
    obj = _object(claims=[_claim("session device dev-9F31AB")])
    proposal = _proposal(reply=_reply("Session device dev-9F31AB was flagged."))
    verdict = verify(proposal, case, obj, [], [])
    assert not verdict.ok
    assert verdict.rule == "disclosure"
    assert verdict.field == "reply.text"


# --- claim linter false positives (FLAG on #14: the real eval's top rejector) ---

def test_linter_greeting_plus_name_ok():
    case = _case([_ev(1, "help", sender="Mara Ellison")])
    for text in ["Hello Mara, which transfer do you mean?",
                 "Hi Mara, can you confirm the batch?",
                 "Dear Ms Ellison, please check the reference."]:
        proposal = _proposal(reply=_reply(text))
        assert verify(proposal, case, _object(), [], []).ok, text


def test_linter_pronoun_sentence_start_ok():
    case = _case([_ev(1, "help")])
    for text in ["I'm not sure which payment you mean.",
                 "I've looked and I'll come back shortly.",
                 "Once I have the reference I will act on it."]:
        proposal = _proposal(reply=_reply(text))
        assert verify(proposal, case, _object(), [], []).ok, text


def test_linter_capital_after_full_stop_ok():
    # a name span must never cross a sentence boundary
    case = _case([_ev(1, "help")])
    for text in ["Contact H&V. We will confirm on the portal.",
                 "Use your PIN. That is all we need.",
                 "It was logged as SENT. You can check in the morning."]:
        results = [_result("transfer_journal")] if "SENT" in text else []
        proposal = _proposal(reply=_reply(text))
        assert verify(proposal, case, _object(), [], results).ok, text


def test_linter_bank_and_product_words_ok():
    case = _case([_ev(1, "help", sender="Mara Ellison")])
    for text in ["Your Direct Debit is unchanged.",
                 "The Standing Order stays in place.",
                 "Check the Secure Portal for the update.",
                 "Your Profile shows the change.",
                 "Vale Bank will confirm shortly."]:
        proposal = _proposal(reply=_reply(text))
        assert verify(proposal, case, _object(), [], []).ok, text


def test_linter_possessive_name_in_case_ok():
    case = _case([_ev(1, "The batch for Northmere Studio Ltd needs the "
                         "Payroll Approver.", sender="Owen Bell")])
    for text in ["Northmere Studio Ltd's batch is awaiting approval.",
                 "Owen Bell's Payroll Approver can release it."]:
        proposal = _proposal(reply=_reply(text))
        assert verify(proposal, case, _object(), [], []).ok, text


def test_linter_name_tokenwise_in_case_text_ok():
    # a name whose tokens all appear in the case (not just in claims) is evidenced
    case = _case([_ev(1, "Please review the payroll file.",
                      sender="Owen Bell", recipient="H&V agent")])
    proposal = _proposal(reply=_reply("Owen Bell, which row do you mean?"))
    assert verify(proposal, case, _object(), [], []).ok


def test_linter_reference_prefix_of_case_ref_ok():
    case = _case([_ev(1, "I uploaded batch-041.csv this morning.")])
    proposal = _proposal(reply=_reply("I can see batch-041 in the queue."))
    assert verify(proposal, case, _object(), [], []).ok


def test_linter_reference_case_insensitive_ok():
    case = _case([_ev(1, "The row is SUP-17 in the batch.")])
    proposal = _proposal(reply=_reply("I can see sup-17 in the batch."))
    assert verify(proposal, case, _object(), [], []).ok


def test_linter_unseen_name_still_rejected():
    # the safety value stays: a name nowhere in the case is still refused
    case = _case([_ev(1, "help", sender="Mara Ellison")])
    proposal = _proposal(reply=_reply("The payment to Elena Marlow is noted."))
    verdict = verify(proposal, case, _object(), [], [])
    assert not verdict.ok
    assert verdict.rule == "claim_linter"
    assert "Elena Marlow" in verdict.message
