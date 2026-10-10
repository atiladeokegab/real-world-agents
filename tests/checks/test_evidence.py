from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent.checks import find_evidence
from agent.core.contracts import Attachment, Case, Event
from agent.ingest import load_case

REPO = Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "examples"

ALL_CASES = sorted(p for p in EXAMPLES.iterdir() if p.is_dir() and p.name.isdigit())


def _ev(n, body, channel="Secure chat", sender="Mara Ellison", recipient="H&V agent", at=None):
    return Event(
        id=f"event-{n:03d}",
        at=at or datetime(2025, 7, 19, 9, 0, tzinfo=timezone.utc),
        channel=channel,
        sender=sender,
        recipient=recipient,
        body=body,
    )


def _case(events, attachments=(), created=None):
    return Case(
        track="t",
        case_id="t",
        title="t",
        source_role="Bank customer",
        created=created,
        initial_request="help",
        events=list(events),
        attachments=list(attachments),
    )


def _checks(findings):
    return {f.check for f in findings}


# --- the two cases named in the vertical's acceptance ---

def test_case_006_fires_duplicates():
    findings = find_evidence(load_case(EXAMPLES / "006"))
    dup = [f for f in findings if f.check == "duplicates"]
    assert dup and "event-001" in dup[0].events
    assert all(f.kind in {"conflict", "anomaly"} for f in findings)


def test_case_044_fires_status():
    findings = find_evidence(load_case(EXAMPLES / "044"))
    status = [f for f in findings if f.check == "status"]
    assert status
    assert "event-001" in status[0].events and "event-002" in status[0].events


def test_case_045_fires_identity_role_disclaimer():
    findings = find_evidence(load_case(EXAMPLES / "045"))
    assert "identity" in _checks(findings)


def test_every_finding_cites_events():
    for case_dir in ALL_CASES:
        for f in find_evidence(load_case(case_dir)):
            assert f.id.startswith("finding-")
            assert f.check in {"amounts", "identity", "time", "duplicates", "status", "limits"}
            assert f.events, f"{case_dir.name}: {f.check} finding cites no events"


def test_low_noise_across_practice_cases():
    total = sum(len(find_evidence(load_case(d))) for d in ALL_CASES)
    assert total <= 30  # find_evidence is conservative; a blow-up here means over-flagging


def test_clean_case_has_no_findings():
    assert find_evidence(load_case(EXAMPLES / "001")) == []


# --- amounts ---

def test_amounts_conflict_same_payee_two_amounts():
    case = _case([
        _ev(1, "You sent £420.00 to Alder & Reed Workshop yesterday."),
        _ev(2, "The transfer to Alder & Reed Workshop was £430.00, not £420.00."),
    ])
    f = [f for f in find_evidence(case) if f.check == "amounts"]
    assert f and f[0].kind == "conflict"
    assert set(f[0].events) == {"event-001", "event-002"}


def test_amounts_clean_same_amount_twice():
    case = _case([
        _ev(1, "You sent £420.00 to Alder & Reed Workshop yesterday."),
        _ev(2, "Confirmed: £420.00 to Alder & Reed Workshop."),
    ])
    assert "amounts" not in _checks(find_evidence(case))


def test_amounts_conflict_stated_total_vs_csv():
    case = _case(
        [_ev(1, "The batch total is £500.00, please confirm.")],
        attachments=[Attachment(name="batch.csv", kind="csv",
                                text="row,amount_gbp\n1,420.00\n2,385.00\n")],
    )
    f = [f for f in find_evidence(case) if f.check == "amounts"]
    assert f and f[0].kind == "conflict" and "event-001" in f[0].events


def test_amounts_clean_matching_total():
    case = _case(
        [_ev(1, "The batch total is £805.00, please confirm.")],
        attachments=[Attachment(name="batch.csv", kind="csv",
                                text="row,amount_gbp\n1,420.00\n2,385.00\n")],
    )
    assert "amounts" not in _checks(find_evidence(case))


# --- identity ---

def test_identity_attachment_holder_mismatch():
    case = _case(
        [_ev(1, "Please check my statement.")],
        attachments=[Attachment(name="s.txt", kind="text",
                                text="Account holder: Elena Marlow\nSome rows\n")],
    )
    f = [f for f in find_evidence(case) if f.check == "identity"]
    assert f and "event-001" in f[0].events


def test_identity_clean_same_holder():
    case = _case(
        [_ev(1, "Please check my statement.")],
        attachments=[Attachment(name="s.txt", kind="text",
                                text="Account holder: Mara Ellison\nSome rows\n")],
    )
    assert "identity" not in _checks(find_evidence(case))


def test_identity_role_disclaimer():
    case = _case([_ev(1, "Please add a signatory. I'm not the company administrator.")])
    assert "identity" in _checks(find_evidence(case))


def test_identity_third_party_and_customer():
    case = _case([
        _ev(1, "Refund please.", channel="External message", sender="Buyer"),
        _ev(2, "That message is not mine — I never asked for a refund."),
    ])
    f = [f for f in find_evidence(case) if f.check == "identity"]
    assert f and set(f[0].events) == {"event-001", "event-002"}


# --- time ---

def test_time_out_of_order_events():
    early = datetime(2025, 7, 19, 9, 0, tzinfo=timezone.utc)
    late = datetime(2025, 7, 19, 10, 0, tzinfo=timezone.utc)
    case = _case([_ev(1, "hi", at=late), _ev(2, "earlier?", at=early)])
    f = [f for f in find_evidence(case) if f.check == "time"]
    assert f and set(f[0].events) == {"event-001", "event-002"}


def test_time_clean_monotonic():
    case = _case([_ev(1, "hi"), _ev(2, "there")])
    assert "time" not in _checks(find_evidence(case))


def test_time_action_dated_in_the_future():
    case = _case([_ev(1, "The transfer was sent on 25 August 2025.")])
    assert "time" in _checks(find_evidence(case))


def test_time_scheduled_future_date_is_clean():
    case = _case([_ev(1, "Your standing order is next scheduled to run on 25 August 2025.")])
    assert "time" not in _checks(find_evidence(case))


def test_time_past_deadline():
    case = _case(
        [_ev(1, "The form was due 10 July 2025.")],
        created=datetime(2025, 7, 19, 9, 0, tzinfo=timezone.utc),
    )
    assert "time" in _checks(find_evidence(case))


# --- duplicates ---

def test_duplicates_two_similar_entries_wording():
    case = _case([_ev(1, "Your activity shows two similar transfer entries to North Quay Utilities for £84.20.")])
    f = [f for f in find_evidence(case) if f.check == "duplicates"]
    assert f and "event-001" in f[0].events


def test_duplicates_clean_single_transfer():
    case = _case([_ev(1, "Your transfer to North Quay Utilities for £84.20 was sent.")])
    assert "duplicates" not in _checks(find_evidence(case))


# --- status ---

def test_status_collection_vs_member():
    case = _case([
        _ev(1, 'Batch "supplier payments" — status: Processed.', channel="Business portal"),
        _ev(2, "I can't tell whether row SUP-17 was paid.", sender="Leona Voss"),
    ])
    f = [f for f in find_evidence(case) if f.check == "status"]
    assert f and set(f[0].events) == {"event-001", "event-002"}


def test_status_clean_batch_only():
    case = _case([_ev(1, 'Batch "supplier payments" — status: Processed.', channel="Business portal")])
    assert "status" not in _checks(find_evidence(case))


# --- limits ---

def test_limits_request_over_stated_limit():
    case = _case([
        _ev(1, "The company limit is £20,000 per outgoing payment.", sender="H&V agent", recipient="Mara Ellison"),
        _ev(2, "Please transfer £25,000 to the supplier today."),
    ])
    assert "limits" in _checks(find_evidence(case))


def test_limits_clean_within_limit():
    case = _case([
        _ev(1, "The company limit is £20,000 per outgoing payment.", sender="H&V agent", recipient="Mara Ellison"),
        _ev(2, "Please transfer £15,000 to the supplier today."),
    ])
    assert "limits" not in _checks(find_evidence(case))


def test_limits_cutoff_exceeded():
    day = datetime(2025, 7, 19, 14, 0, tzinfo=timezone.utc)
    late = datetime(2025, 7, 19, 16, 30, tzinfo=timezone.utc)
    case = _case([
        _ev(1, "Payments submitted after the 15:00 cut-off run tomorrow.", at=day),
        _ev(2, "Please send the supplier payment now.", at=late),
    ])
    assert "limits" in _checks(find_evidence(case))
