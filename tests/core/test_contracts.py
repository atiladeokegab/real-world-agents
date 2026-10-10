from datetime import datetime, timezone

import pytest

from agent.core.contracts import (
    Ask, Attachment, Authority, Case, CaseObject, Claim, Event, Finding, Proposal,
    Reply, Requester, ToolResult, ToolSpec, Verdict,
)

AT = datetime(2026, 10, 10, 9, 0, tzinfo=timezone.utc)
EVENT = Event(id="event-001", at=AT, channel="Secure chat", sender="customer",
              recipient="bank", body="Please cancel the duplicate transfer.")

SAMPLES = [
    Authority(identity="authenticated", role="customer"),
    EVENT,
    Attachment(name="rows.csv", kind="csv", text="payee,amount\nACME,100.00"),
    Case(track="Banking & Financial Services", case_id="006", title="Duplicate transfer",
         source_role="customer", created=AT, initial_request="cancel one",
         events=[EVENT], authority=Authority(identity="verified"),
         raw_files={"index.md": "# 006"}, question="Should it be returned?"),
    Finding(id="finding-1", kind="conflict", check="duplicates",
            detail="two transfers, same payee, amount and day", events=["event-001"]),
    CaseObject(requester=Requester(name="A. Customer", evidence_events=["event-001"]),
               claims=[Claim(subject="transfer", predicate="amount", value="100.00",
                             source_actor="customer", channel="Secure chat",
                             event="event-001", conflicts_with=[])],
               asks=[Ask(id="ask-1", text="cancel the duplicate", event="event-001")],
               unknowns=["which of the two transfers"]),
    Proposal(action="reply", reply=Reply(channel="Secure chat", text="Action requested."),
             asks_addressed=["ask-1"], claims_relied_on=["event-001"],
             findings_addressed=["finding-1"]),
    ToolSpec(name="transfer_journal", inputs={"reference": "str"}, roles=["customer"], risk=1),
    ToolResult(tool="transfer_journal", params={"reference": "T1"}, status="pending"),
    Verdict(ok=False, rule="findings", field="findings_addressed", event="event-001",
            message="finding-1 not addressed"),
]


@pytest.mark.parametrize("model", SAMPLES, ids=lambda m: type(m).__name__)
def test_json_round_trip(model):
    assert type(model).model_validate_json(model.model_dump_json()) == model
