from pathlib import Path

import pytest

from agent.ingest import load_case

REPO = Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "examples"

ALL_CASES = sorted(p for p in EXAMPLES.iterdir() if p.is_dir() and p.name.isdigit())


def test_fifty_practice_cases_exist():
    assert len(ALL_CASES) == 50


@pytest.mark.parametrize("case_dir", ALL_CASES, ids=lambda p: p.name)
def test_parses_every_practice_case(case_dir):
    case = load_case(case_dir)

    assert case.case_id == case_dir.name
    assert case.track == "Banking & Financial Services"
    assert case.title
    assert case.source_role in {"Bank customer", "Authorised business user"}
    assert case.created is not None
    assert case.initial_request
    assert len(case.events) >= 3

    for n, event in enumerate(case.events, start=1):
        assert event.id == f"event-{n:03d}"
        assert event.at is not None
        assert event.channel
        assert event.sender
        assert event.recipient
        assert event.body

    assert set(case.raw_files) == {"index.md", "history.md"}


def test_case_001_fields():
    case = load_case(EXAMPLES / "001")

    assert case.title == "Was the one-off transfer sent?"
    assert case.source_role == "Bank customer"
    assert case.created.year == 2025 and case.created.month == 7
    assert "£420" in case.initial_request
    assert "Alder & Reed Workshop" in case.initial_request
    assert len(case.events) == 5
    assert case.events[1].channel == "Secure chat"
    assert case.events[1].sender == "Mara Ellison"


@pytest.mark.parametrize(
    "case_dir,identity",
    [
        ("005", "verified"),   # Verified call
        ("001", "authenticated"),  # Secure chat
        ("003", "authenticated"),  # Secure portal
        ("041", "authenticated"),  # Business portal
        ("020", "unverified"),  # External message
    ],
)
def test_authority_identity_from_channel(case_dir, identity):
    assert load_case(EXAMPLES / case_dir).authority.identity == identity


def test_authority_role_from_the_record():
    # "role from the record" (§4.1) — index.md's Source role, never the model.
    for case_dir in ("041", "047"):
        assert load_case(EXAMPLES / case_dir).authority.role == "Authorised business user"
    assert load_case(EXAMPLES / "001").authority.role == "Bank customer"


def test_authority_never_model_derived():
    # External message stays unverified even though the sender claims to be the customer.
    assert load_case(EXAMPLES / "028").authority.identity == "unverified"


def test_cut_hides_later_events_and_strips_answer_sections():
    case = load_case(EXAMPLES / "001", cut=2)

    assert [e.id for e in case.events] == ["event-001", "event-002"]

    index = case.raw_files["index.md"]
    for heading in ("## Overview", "## Next action at escalation", "## Outcome"):
        assert heading in index  # heading kept, body hidden
    assert "H&V's journal recorded the transfer as sent" not in index
    assert "Check the specific transfer's status" not in index

    assert "event-003" not in case.raw_files["history.md"]
    assert "SENT" not in case.raw_files["history.md"]


def test_no_cut_keeps_full_case():
    case = load_case(EXAMPLES / "001")
    assert len(case.events) == 5
    assert "H&V's journal recorded the transfer as sent" in case.raw_files["index.md"]


def test_question_stored_on_case():
    case = load_case(EXAMPLES / "001", question="Should this payment be released?")
    assert case.question == "Should this payment be released?"
    assert load_case(EXAMPLES / "001").question is None


def test_cut_allows_first_event_only():
    case = load_case(EXAMPLES / "001", cut=1)
    assert [e.id for e in case.events] == ["event-001"]
    # event-001 is bank -> customer, no inbound seen yet
    assert case.authority.identity == "unverified"
